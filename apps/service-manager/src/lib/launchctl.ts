// LaunchAgent control functions

import { homedir } from "os"
import { readFile, copyFile, mkdir } from "fs/promises"
import { join } from "path"
import { exists } from "fs/promises"
import type { ServiceStatus } from "./types"
import { getInstalledPath, getLaunchAgentsDestPath } from "./plist"

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

  // Check if it's running now
  const status = await getServiceStatus(label)
  return status.status === "running" || status.status === "stopped"
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
 * Install a plist from dotfiles to ~/Library/LaunchAgents
 * Replaces __HOME__ placeholder with actual home directory
 */
export async function installPlist(
  sourcePath: string,
  label: string
): Promise<boolean> {
  try {
    // Ensure LaunchAgents directory exists
    const destDir = getLaunchAgentsDestPath()
    await mkdir(destDir, { recursive: true })

    // Read source plist
    const content = await readFile(sourcePath, "utf-8")

    // Replace __HOME__ placeholder
    const home = homedir()
    const processedContent = content.replace(/__HOME__/g, home)

    // Write to destination
    const destPath = getInstalledPath(label)
    await Bun.write(destPath, processedContent)

    return true
  } catch {
    return false
  }
}

/**
 * Uninstall a plist (stop service and remove file)
 */
export async function uninstallPlist(label: string): Promise<boolean> {
  try {
    // First stop the service
    await stopService(label)
    await Bun.sleep(200)

    // Remove the plist file
    const destPath = getInstalledPath(label)
    const file = Bun.file(destPath)
    if (await file.exists()) {
      await Bun.write(destPath, "") // Clear file
      const proc = Bun.spawn(["rm", destPath], { stdout: "ignore" })
      await proc.exited
    }

    return true
  } catch {
    return false
  }
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
