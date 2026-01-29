// Plist parsing utilities

import { readdir, readFile, exists } from "fs/promises"
import { homedir } from "os"
import { join, basename } from "path"
import type { PlistData, Service } from "./types"

// Try common dotfiles locations
function findDotfilesDir(): string {
  const candidates = [
    join(homedir(), "dotfiles"),
    join(homedir(), "dev/dotfiles"),
    join(homedir(), ".dotfiles"),
  ]
  
  for (const candidate of candidates) {
    try {
      const fs = require("fs")
      if (fs.existsSync(join(candidate, "dot-launchagents"))) {
        return candidate
      }
    } catch {}
  }
  
  // Fallback - resolve from this script's location
  const scriptDir = import.meta.dir
  // service-manager/src/lib/plist.ts -> go up to dotfiles
  return join(scriptDir, "../../../../..")
}

const DOTFILES_DIR = findDotfilesDir()
const LAUNCHAGENTS_SRC = join(DOTFILES_DIR, "dot-launchagents")
const LAUNCHAGENTS_DEST = join(homedir(), "Library/LaunchAgents")

/**
 * Get the path to the dotfiles LaunchAgents directory
 */
export function getLaunchAgentsSrcPath(): string {
  return LAUNCHAGENTS_SRC
}

/**
 * Get the path to the installed LaunchAgents directory
 */
export function getLaunchAgentsDestPath(): string {
  return LAUNCHAGENTS_DEST
}

/**
 * List all plist files in the dotfiles LaunchAgents directory
 */
export async function listPlistFiles(): Promise<string[]> {
  try {
    const files = await readdir(LAUNCHAGENTS_SRC)
    return files
      .filter((f) => f.endsWith(".plist"))
      .map((f) => join(LAUNCHAGENTS_SRC, f))
  } catch {
    return []
  }
}

/**
 * Parse a plist file using plutil and return parsed data
 */
export async function parsePlist(path: string): Promise<PlistData | null> {
  try {
    // Use plutil to convert plist to JSON
    const proc = Bun.spawn(["plutil", "-convert", "json", "-o", "-", path], {
      stdout: "pipe",
      stderr: "pipe",
    })

    const output = await new Response(proc.stdout).text()
    await proc.exited

    if (proc.exitCode !== 0) {
      return null
    }

    const data = JSON.parse(output) as PlistData
    return data
  } catch {
    return null
  }
}

/**
 * Replace __HOME__ placeholder with actual home directory
 */
export function replaceHomePlaceholder(value: string): string {
  return value.replace(/__HOME__/g, homedir())
}

/**
 * Check if a plist is installed in ~/Library/LaunchAgents
 */
export async function isPlistInstalled(label: string): Promise<boolean> {
  const installedPath = join(LAUNCHAGENTS_DEST, `${label}.plist`)
  return exists(installedPath)
}

/**
 * Get the installed path for a service label
 */
export function getInstalledPath(label: string): string {
  return join(LAUNCHAGENTS_DEST, `${label}.plist`)
}

/**
 * Parse a plist file and return a partial Service object
 */
export async function parsePlistToService(
  plistPath: string
): Promise<Omit<Service, "status" | "pid" | "exitCode"> | null> {
  const data = await parsePlist(plistPath)
  if (!data || !data.Label) {
    return null
  }

  const label = data.Label

  return {
    label,
    plistPath,
    installedPath: getInstalledPath(label),
    program: data.ProgramArguments || [],
    runAtLoad: data.RunAtLoad ?? false,
    keepAlive: data.KeepAlive ?? false,
    stdoutPath: data.StandardOutPath
      ? replaceHomePlaceholder(data.StandardOutPath)
      : undefined,
    stderrPath: data.StandardErrorPath
      ? replaceHomePlaceholder(data.StandardErrorPath)
      : undefined,
    workingDirectory: data.WorkingDirectory
      ? replaceHomePlaceholder(data.WorkingDirectory)
      : undefined,
    environmentVariables: data.EnvironmentVariables
      ? Object.fromEntries(
          Object.entries(data.EnvironmentVariables).map(([k, v]) => [
            k,
            replaceHomePlaceholder(v),
          ])
        )
      : undefined,
  }
}
