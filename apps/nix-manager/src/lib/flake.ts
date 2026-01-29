// Flake.nix parsing and modification utilities

import { readFile, writeFile } from "fs/promises"
import { homedir } from "os"
import { join } from "path"

const DEFAULT_FLAKE_PATH = join(
  homedir(),
  "dev/dotfiles/dot-config/nix-darwin/flake.nix"
)

/**
 * Extract homebrew.brews from flake.nix
 */
export function extractBrews(content: string): string[] {
  const match = content.match(/homebrew\.brews\s*=\s*\[([\s\S]*?)\];/)
  if (!match) return []

  const packages: string[] = []
  const regex = /"([^"]+)"/g
  let m
  while ((m = regex.exec(match[1])) !== null) {
    packages.push(m[1])
  }
  return packages.sort((a, b) => {
    // Sort by the package name (last segment for tap packages)
    const aName = a.split("/").pop() || a
    const bName = b.split("/").pop() || b
    return aName.localeCompare(bName)
  })
}

/**
 * Extract homebrew.casks from flake.nix
 */
export function extractCasks(content: string): string[] {
  const match = content.match(/homebrew\.casks\s*=\s*\[([\s\S]*?)\];/)
  if (!match) return []

  const packages: string[] = []
  const regex = /"([^"]+)"/g
  let m
  while ((m = regex.exec(match[1])) !== null) {
    packages.push(m[1])
  }
  return packages.sort()
}

/**
 * Extract homebrew.masApps from flake.nix
 * Returns array of { name, id } objects
 */
export function extractMasApps(
  content: string
): { name: string; id: number }[] {
  const match = content.match(/homebrew\.masApps\s*=\s*\{([\s\S]*?)\};/)
  if (!match) return []

  const apps: { name: string; id: number }[] = []
  // Match "App Name" = 123456; pattern
  const regex = /"([^"]+)"\s*=\s*(\d+);/g
  let m
  while ((m = regex.exec(match[1])) !== null) {
    apps.push({ name: m[1], id: parseInt(m[2], 10) })
  }
  return apps.sort((a, b) => a.name.localeCompare(b.name))
}

/**
 * Extract environment.systemPackages (nix packages) from flake.nix
 */
export function extractNixPackages(content: string): string[] {
  const match = content.match(
    /environment\.systemPackages\s*=\s*\[([\s\S]*?)\];/
  )
  if (!match) return []

  const packages: string[] = []
  // Match both pkgs.name and pkgs."name"
  const regex = /pkgs\.(?:"([^"]+)"|([a-zA-Z0-9_-]+))/g
  let m
  while ((m = regex.exec(match[1])) !== null) {
    packages.push(m[1] || m[2])
  }
  return packages.sort()
}

/**
 * Read flake.nix content
 */
export async function readFlake(path?: string): Promise<string> {
  const flakePath = path || DEFAULT_FLAKE_PATH
  return readFile(flakePath, "utf-8")
}

/**
 * Get the flake path
 */
export function getFlakePath(): string {
  return DEFAULT_FLAKE_PATH
}

/**
 * Add a package to a list in flake.nix
 */
export async function addPackage(
  packageName: string,
  listType: "brews" | "casks" | "masApps" | "nixpkgs",
  flakePath?: string,
  masAppId?: number
): Promise<void> {
  const path = flakePath || DEFAULT_FLAKE_PATH
  let content = await readFile(path, "utf-8")

  if (listType === "brews") {
    content = addToBrews(content, packageName)
  } else if (listType === "casks") {
    content = addToCasks(content, packageName)
  } else if (listType === "masApps") {
    if (masAppId === undefined) {
      throw new Error("masAppId is required for masApps")
    }
    content = addToMasApps(content, packageName, masAppId)
  } else {
    content = addToNixPackages(content, packageName)
  }

  await writeFile(path, content)
}

/**
 * Remove a package from a list in flake.nix
 */
export async function removePackage(
  packageName: string,
  listType: "brews" | "casks" | "masApps" | "nixpkgs",
  flakePath?: string
): Promise<void> {
  const path = flakePath || DEFAULT_FLAKE_PATH
  let content = await readFile(path, "utf-8")

  if (listType === "brews") {
    content = removeFromBrews(content, packageName)
  } else if (listType === "casks") {
    content = removeFromCasks(content, packageName)
  } else if (listType === "masApps") {
    content = removeFromMasApps(content, packageName)
  } else {
    content = removeFromNixPackages(content, packageName)
  }

  await writeFile(path, content)
}

function addToBrews(content: string, packageName: string): string {
  const regex = /(homebrew\.brews\s*=\s*\[)([\s\S]*?)(\];)/
  const match = content.match(regex)
  if (!match) return content

  const existingPackages = extractBrews(content)
  if (existingPackages.includes(packageName)) return content

  const allPackages = [...existingPackages, packageName].sort((a, b) => {
    const aName = a.split("/").pop() || a
    const bName = b.split("/").pop() || b
    return aName.localeCompare(bName)
  })

  const newList = allPackages.map((p) => `        "${p}"`).join("\n")
  return content.replace(regex, `$1\n${newList}\n      $3`)
}

function addToCasks(content: string, packageName: string): string {
  const regex = /(homebrew\.casks\s*=\s*\[)([\s\S]*?)(\];)/
  const match = content.match(regex)
  if (!match) return content

  const existingPackages = extractCasks(content)
  if (existingPackages.includes(packageName)) return content

  const allPackages = [...existingPackages, packageName].sort()
  const newList = allPackages.map((p) => `        "${p}"`).join("\n")
  return content.replace(regex, `$1\n${newList}\n      $3`)
}

function addToNixPackages(content: string, packageName: string): string {
  const regex = /(environment\.systemPackages\s*=\s*\[)([\s\S]*?)(\];)/
  const match = content.match(regex)
  if (!match) return content

  const existingPackages = extractNixPackages(content)
  if (existingPackages.includes(packageName)) return content

  const allPackages = [...existingPackages, packageName].sort()
  const newList = allPackages.map((p) => `        pkgs.${p}`).join("\n")
  return content.replace(regex, `$1\n${newList}\n      $3`)
}

function removeFromBrews(content: string, packageName: string): string {
  // Handle both exact match and tap-prefixed packages
  const escapedName = packageName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  // Remove the line containing the package (handles any indentation)
  const lineRegex = new RegExp(`\\s*"${escapedName}"\\n?`, "g")
  return content.replace(lineRegex, "\n        ")
}

function removeFromCasks(content: string, packageName: string): string {
  const escapedName = packageName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  const lineRegex = new RegExp(`\\s*"${escapedName}"\\n?`, "g")
  return content.replace(lineRegex, "\n        ")
}

function removeFromNixPackages(content: string, packageName: string): string {
  const escapedName = packageName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  // Match pkgs.name or pkgs."name"
  const lineRegex = new RegExp(
    `\\s*pkgs\\.(?:"${escapedName}"|${escapedName})\\n?`,
    "g"
  )
  return content.replace(lineRegex, "\n        ")
}

function addToMasApps(
  content: string,
  appName: string,
  appId: number
): string {
  const regex = /(homebrew\.masApps\s*=\s*\{)([\s\S]*?)(\};)/
  const match = content.match(regex)
  if (!match) return content

  const existingApps = extractMasApps(content)
  if (existingApps.some((app) => app.name === appName)) return content

  const allApps = [...existingApps, { name: appName, id: appId }].sort((a, b) =>
    a.name.localeCompare(b.name)
  )

  const newList = allApps.map((a) => `        "${a.name}" = ${a.id};`).join("\n")
  return content.replace(regex, `$1\n${newList}\n      $3`)
}

function removeFromMasApps(content: string, appName: string): string {
  const escapedName = appName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  // Match "App Name" = 123456; pattern
  const lineRegex = new RegExp(`\\s*"${escapedName}"\\s*=\\s*\\d+;\\n?`, "g")
  return content.replace(lineRegex, "\n        ")
}
