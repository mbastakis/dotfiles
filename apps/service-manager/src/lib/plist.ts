// Config parsing and plist generation utilities

import { readdir, readFile, exists, writeFile } from "fs/promises"
import { homedir } from "os"
import { join } from "path"
import { parse as parseToml, stringify as stringifyToml } from "smol-toml"
import type { Service, ServiceConfig, ParseConfigResult } from "./types"

/**
 * Escape special XML characters and control characters to prevent malformed plist generation
 */
function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;")
    .replace(/\r/g, "&#13;")
    .replace(/\n/g, "&#10;")
    .replace(/\t/g, "&#9;")
}

// Config and destination directories
const CONFIG_DIR = join(homedir(), ".config/service-manager")
const LAUNCHAGENTS_DEST = join(homedir(), "Library/LaunchAgents")

/**
 * Get the path to the service-manager config directory
 */
export function getConfigDir(): string {
  return CONFIG_DIR
}

/**
 * Get the path to the installed LaunchAgents directory
 */
export function getLaunchAgentsDestPath(): string {
  return LAUNCHAGENTS_DEST
}

/**
 * List all TOML config files in the config directory
 */
export async function listConfigFiles(): Promise<string[]> {
  try {
    if (!(await exists(CONFIG_DIR))) {
      return []
    }
    const files = await readdir(CONFIG_DIR)
    return files
      .filter((f) => f.endsWith(".toml"))
      .map((f) => join(CONFIG_DIR, f))
  } catch {
    return []
  }
}

/**
 * Expand ~ to home directory in paths
 */
export function expandPath(value: string): string {
  if (value.startsWith("~")) {
    return join(homedir(), value.slice(1))
  }
  return value
}

/**
 * Parse a TOML config file and return ServiceConfig with detailed errors
 */
export function parseConfigWithError(
  content: string,
  filename: string
): ParseConfigResult {
  try {
    const data = parseToml(content)

    // Validate required fields with specific error messages
    if (typeof data.enabled !== "boolean") {
      return { success: false, error: `${filename}: missing or invalid 'enabled' field (must be true/false)` }
    }

    const service = data.service as ServiceConfig["service"] | undefined
    if (!service) {
      return { success: false, error: `${filename}: missing [service] section` }
    }

    if (!service.label || typeof service.label !== "string") {
      return { success: false, error: `${filename}: missing or invalid 'service.label'` }
    }

    if (!Array.isArray(service.program)) {
      return { success: false, error: `${filename}: 'service.program' must be an array` }
    }

    if (service.program.length === 0) {
      return { success: false, error: `${filename}: 'service.program' cannot be empty` }
    }

    if (!service.program.every((p) => typeof p === "string")) {
      return { success: false, error: `${filename}: all 'service.program' elements must be strings` }
    }

    return {
      success: true,
      config: {
        enabled: data.enabled as boolean,
        service: {
          label: service.label,
          program: service.program,
          run_at_load: service.run_at_load,
          keep_alive: service.keep_alive,
          working_directory: service.working_directory,
          environment: service.environment,
        },
        logs: data.logs as ServiceConfig["logs"],
      },
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown parse error"
    return { success: false, error: `${filename}: ${message}` }
  }
}

/**
 * Parse a TOML config file and return ServiceConfig (null on error)
 */
export async function parseConfig(path: string): Promise<ServiceConfig | null> {
  try {
    const content = await readFile(path, "utf-8")
    const filename = path.split("/").pop() || path
    const result = parseConfigWithError(content, filename)
    return result.success ? result.config : null
  } catch {
    return null
  }
}

/**
 * Parse a TOML config file with detailed error reporting
 */
export async function parseConfigDetailed(path: string): Promise<ParseConfigResult> {
  try {
    const content = await readFile(path, "utf-8")
    const filename = path.split("/").pop() || path
    return parseConfigWithError(content, filename)
  } catch (err) {
    const filename = path.split("/").pop() || path
    const message = err instanceof Error ? err.message : "Failed to read file"
    return { success: false, error: `${filename}: ${message}` }
  }
}

/**
 * Get the installed path for a service label
 */
export function getInstalledPath(label: string): string {
  return join(LAUNCHAGENTS_DEST, `${label}.plist`)
}

/**
 * Parse a config file and return a partial Service object
 */
export async function parseConfigToService(
  configPath: string
): Promise<Omit<Service, "status" | "pid" | "exitCode"> | null> {
  const config = await parseConfig(configPath)
  if (!config) {
    return null
  }

  const { service, logs, enabled } = config

  return {
    label: service.label,
    configPath,
    installedPath: getInstalledPath(service.label),
    enabled,
    program: service.program,
    runAtLoad: service.run_at_load ?? false,
    keepAlive: service.keep_alive ?? false,
    stdoutPath: logs?.stdout ? expandPath(logs.stdout) : undefined,
    stderrPath: logs?.stderr ? expandPath(logs.stderr) : undefined,
    workingDirectory: service.working_directory
      ? expandPath(service.working_directory)
      : undefined,
    environmentVariables: service.environment,
  }
}

/**
 * Generate a shell command that logs a startup timestamp then exec's the real program
 * Also redirects stderr to stdout so all logs appear in one file
 * Truncates the log file on startup to prevent unbounded growth
 */
function generateStartupWrapper(program: string[], stdoutPath?: string): string[] {
  if (!stdoutPath) {
    // No log file, just run the program directly
    return program
  }
  
  const expandedStdout = expandPath(stdoutPath)
  const expandedProgram = program.map(expandPath)
  const escapedProgram = expandedProgram.map((arg) => `'${arg.replace(/'/g, "'\\''")}'`).join(" ")
  
  // Shell command that truncates log, writes timestamp, then exec's the real program with stderr redirected to stdout
  const shellCmd = `echo "=== Service started at $(date '+%Y-%m-%d %H:%M:%S') ===" > "${expandedStdout}" && exec ${escapedProgram} 2>&1`
  
  return ["/bin/sh", "-c", shellCmd]
}

/**
 * Generate plist XML from a ServiceConfig
 */
export function generatePlist(config: ServiceConfig): string {
  const { service, logs } = config
  const home = homedir()
  
  // Wrap the program to add startup timestamp logging
  const wrappedProgram = generateStartupWrapper(service.program, logs?.stdout)
  
  let xml = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${escapeXml(service.label)}</string>

    <key>ProgramArguments</key>
    <array>
${wrappedProgram.map((arg) => `        <string>${escapeXml(arg)}</string>`).join("\n")}
    </array>
`

  // Environment variables (expand ~ in values)
  const userEnv: Record<string, string> = {}
  if (service.environment) {
    for (const [key, value] of Object.entries(service.environment)) {
      userEnv[key] = expandPath(value)
    }
  }
  
  const env: Record<string, string> = {
    HOME: home,
    PATH: "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
    ...userEnv,
  }
  
  xml += `
    <key>EnvironmentVariables</key>
    <dict>
${Object.entries(env)
  .map(
    ([key, value]) =>
      `        <key>${escapeXml(key)}</key>
        <string>${escapeXml(value)}</string>`
  )
  .join("\n")}
    </dict>
`

  // Run at load
  if (service.run_at_load) {
    xml += `
    <key>RunAtLoad</key>
    <true/>
`
  }

  // Keep alive
  if (service.keep_alive) {
    xml += `
    <key>KeepAlive</key>
    <true/>
`
  }

  // Log paths
  if (logs?.stdout) {
    xml += `
    <key>StandardOutPath</key>
    <string>${escapeXml(expandPath(logs.stdout))}</string>
`
  }

  if (logs?.stderr) {
    xml += `
    <key>StandardErrorPath</key>
    <string>${escapeXml(expandPath(logs.stderr))}</string>
`
  }

  // Working directory
  if (service.working_directory) {
    xml += `
    <key>WorkingDirectory</key>
    <string>${escapeXml(expandPath(service.working_directory))}</string>
`
  }

  xml += `</dict>
</plist>
`

  return xml
}

/**
 * Update the enabled state in a TOML config file
 */
export async function updateConfigEnabled(
  configPath: string,
  enabled: boolean
): Promise<boolean> {
  try {
    const content = await readFile(configPath, "utf-8")
    const data = parseToml(content)

    // Check if enabled field exists and is a boolean
    if (typeof data.enabled !== "boolean") {
      return false
    }

    // Update and write back using TOML serializer
    data.enabled = enabled
    const newContent = stringifyToml(data)
    await writeFile(configPath, newContent, "utf-8")
    return true
  } catch {
    return false
  }
}
