// LaunchAgent control functions

import { homedir } from "os"
import { mkdir, unlink } from "fs/promises"
import { join, dirname } from "path"
import { exists } from "fs/promises"
import type { ServiceStatus, ServiceConfig } from "./types"
import {
  getInstalledPath,
  getLaunchAgentsDestPath,
  listConfigFiles,
  parseConfig,
  parseConfigDetailed,
  generatePlist,
  expandPath,
} from "./plist"

/**
 * Get the current user's GUI domain for launchctl
 */
async function getGuiDomain(): Promise<string> {
  const proc = Bun.spawn(["id", "-u"], { stdout: "pipe" })
  const uid = (await new Response(proc.stdout).text()).trim()
  await proc.exited
  return `gui/${uid}`
}

interface ServiceStatusInfo {
  status: ServiceStatus
  pid?: number
  exitCode?: number
}

/**
 * Get the status of a service by its label
 */
export async function getServiceStatus(
  label: string
): Promise<ServiceStatusInfo> {
  // First check if the plist is installed
  const installedPath = getInstalledPath(label)
  const installed = await exists(installedPath)

  if (!installed) {
    return { status: "not_installed" }
  }

  // Check if service is loaded and get its status
  const proc = Bun.spawn(["launchctl", "list"], { stdout: "pipe" })
  const output = await new Response(proc.stdout).text()
  await proc.exited

  // Parse launchctl list output
  // Format: PID\tStatus\tLabel
  const lines = output.trim().split("\n")
  for (const line of lines) {
    const parts = line.split("\t")
    if (parts.length >= 3 && parts[2] === label) {
      const pidStr = parts[0]
      const exitCodeStr = parts[1]

      if (pidStr !== "-" && pidStr !== "") {
        return {
          status: "running",
          pid: parseInt(pidStr, 10),
          exitCode: exitCodeStr !== "-" ? parseInt(exitCodeStr, 10) : undefined,
        }
      } else {
        return {
          status: "stopped",
          exitCode: exitCodeStr !== "-" ? parseInt(exitCodeStr, 10) : undefined,
        }
      }
    }
  }

  // Service is installed but not in launchctl list (not loaded)
  return { status: "stopped" }
}

/**
 * Start a service (bootstrap it)
 */
export async function startService(label: string): Promise<boolean> {
  const installedPath = getInstalledPath(label)
  const installed = await exists(installedPath)

  if (!installed) {
    return false
  }

  const domain = await getGuiDomain()

  // First try to bootout in case it's in a weird state
  const bootoutProc = Bun.spawn(
    ["launchctl", "bootout", `${domain}/${label}`],
    {
      stdout: "ignore",
      stderr: "ignore",
    }
  )
  await bootoutProc.exited

  // Small delay
  await Bun.sleep(200)

  // Bootstrap the service
  const proc = Bun.spawn(["launchctl", "bootstrap", domain, installedPath], {
    stdout: "pipe",
    stderr: "pipe",
  })

  await proc.exited

  // Retry checking status for slow-starting services
  const maxRetries = 15
  const retryDelay = 300 // ms

  for (let i = 0; i < maxRetries; i++) {
    const status = await getServiceStatus(label)
    if (status.status === "running") {
      return true
    }
    // One-shot service that completed successfully
    if (status.status === "stopped" && status.exitCode === 0) {
      return true
    }
    // Service crashed - exit early instead of waiting full timeout
    if (status.status === "stopped" && status.exitCode !== undefined && status.exitCode !== 0) {
      return false
    }
    // Don't sleep after last attempt
    if (i < maxRetries - 1) {
      await Bun.sleep(retryDelay)
    }
  }

  return false
}

/**
 * Stop a service (bootout)
 */
export async function stopService(label: string): Promise<boolean> {
  const domain = await getGuiDomain()

  const proc = Bun.spawn(["launchctl", "bootout", `${domain}/${label}`], {
    stdout: "pipe",
    stderr: "pipe",
  })

  await proc.exited

  // Success if exit code is 0 or service wasn't running
  return proc.exitCode === 0 || proc.exitCode === 3
}

/**
 * Restart a service (stop + start)
 */
export async function restartService(label: string): Promise<boolean> {
  await stopService(label)
  await Bun.sleep(500)
  return startService(label)
}

/**
 * Install a service from its config - generates plist and installs it
 */
export async function installService(configPath: string): Promise<boolean> {
  try {
    const config = await parseConfig(configPath)
    if (!config) {
      return false
    }

    // Ensure LaunchAgents directory exists
    const destDir = getLaunchAgentsDestPath()
    await mkdir(destDir, { recursive: true })

    // Ensure log directories exist
    if (config.logs?.stdout) {
      const logDir = dirname(expandPath(config.logs.stdout))
      await mkdir(logDir, { recursive: true })
    }
    if (config.logs?.stderr) {
      const logDir = dirname(expandPath(config.logs.stderr))
      await mkdir(logDir, { recursive: true })
    }

    // Generate and write plist
    const plistContent = generatePlist(config)
    const destPath = getInstalledPath(config.service.label)
    await Bun.write(destPath, plistContent)

    return true
  } catch {
    return false
  }
}

/**
 * Uninstall a plist (stop service and remove file)
 */
export async function uninstallService(label: string): Promise<boolean> {
  try {
    // First stop the service
    await stopService(label)
    await Bun.sleep(200)

    // Remove the plist file
    const destPath = getInstalledPath(label)
    const file = Bun.file(destPath)
    if (await file.exists()) {
      await unlink(destPath)
    }

    return true
  } catch {
    return false
  }
}

export interface SyncResult {
  label: string
  action: "installed" | "reinstalled" | "uninstalled" | "unchanged" | "error"
  error?: string
}

/**
 * Sync all services from config files
 * - If enabled: install plist and bootstrap
 * - If disabled: bootout and uninstall
 */
export async function syncServices(): Promise<SyncResult[]> {
  const results: SyncResult[] = []
  const configFiles = await listConfigFiles()

  for (const configPath of configFiles) {
    const filename = configPath.split("/").pop() || configPath
    const parseResult = await parseConfigDetailed(configPath)
    
    if (!parseResult.success) {
      results.push({
        label: filename,
        action: "error",
        error: parseResult.error,
      })
      continue
    }

    const config = parseResult.config
    const label = config.service.label
    const installedPath = getInstalledPath(label)
    const isInstalled = await exists(installedPath)

    try {
      if (config.enabled) {
        // If reinstalling, uninstall first to ensure clean state
        if (isInstalled) {
          await uninstallService(label)
          await Bun.sleep(200)
        }

        // Install and start
        const installed = await installService(configPath)
        if (!installed) {
          results.push({ label, action: "error", error: "Failed to install" })
          continue
        }

        const started = await startService(label)
        if (!started) {
          results.push({
            label,
            action: "error",
            error: "Installed but failed to start",
          })
          continue
        }

        results.push({
          label,
          action: isInstalled ? "reinstalled" : "installed",
        })
      } else {
        // Disable and uninstall if currently installed
        if (isInstalled) {
          const uninstalled = await uninstallService(label)
          if (uninstalled) {
            results.push({ label, action: "uninstalled" })
          } else {
            results.push({ label, action: "error", error: "Failed to uninstall" })
          }
        } else {
          results.push({ label, action: "unchanged" })
        }
      }
    } catch (err) {
      results.push({
        label,
        action: "error",
        error: err instanceof Error ? err.message : "Unknown error",
      })
    }
  }

  return results
}

/**
 * Tail the last N lines of a log file
 */
export async function tailLog(
  logPath: string,
  lines: number = 50
): Promise<string[]> {
  try {
    const file = Bun.file(logPath)
    if (!(await file.exists())) {
      return []
    }

    const content = await file.text()
    const allLines = content.split("\n")
    return allLines.slice(-lines).filter((line) => line.length > 0)
  } catch {
    return []
  }
}
