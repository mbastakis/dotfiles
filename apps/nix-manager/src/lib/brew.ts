// Homebrew command execution utilities

import { $ } from "bun"
import type { MasApp } from "./types"

/**
 * Get list of installed Homebrew formulae
 */
export async function getInstalledBrews(): Promise<string[]> {
  try {
    const result = await $`brew list --formula -1`.text()
    return result
      .trim()
      .split("\n")
      .filter((line) => line.length > 0)
      .sort()
  } catch {
    return []
  }
}

/**
 * Get list of installed Homebrew casks
 */
export async function getInstalledCasks(): Promise<string[]> {
  try {
    const result = await $`brew list --cask -1`.text()
    return result
      .trim()
      .split("\n")
      .filter((line) => line.length > 0)
      .sort()
  } catch {
    return []
  }
}

/**
 * Get list of installed Mac App Store apps via mas
 * Returns array of { name, id } objects
 */
export async function getInstalledMasApps(): Promise<MasApp[]> {
  try {
    const result = await $`mas list`.text()
    const apps: MasApp[] = []
    // Output format: "123456789 App Name (1.2.3)"
    const lines = result.trim().split("\n").filter((line) => line.length > 0)
    for (const line of lines) {
      const match = line.match(/^(\d+)\s+(.+?)\s+\(/)
      if (match) {
        apps.push({ id: parseInt(match[1], 10), name: match[2] })
      }
    }
    return apps.sort((a, b) => a.name.localeCompare(b.name))
  } catch {
    return []
  }
}

/**
 * Get detailed info for a brew package
 */
export async function getBrewInfo(name: string): Promise<{
  name: string
  version?: string
  description?: string
  homepage?: string
} | null> {
  try {
    const result = await $`brew info --json=v2 ${name}`.json()
    const formula = result.formulae?.[0] || result.casks?.[0]
    if (!formula) return null

    return {
      name: formula.name || formula.token || name,
      version: formula.versions?.stable || formula.version,
      description: formula.desc || formula.description,
      homepage: formula.homepage,
    }
  } catch {
    return null
  }
}
