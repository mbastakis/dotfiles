// CLI output functions for non-interactive mode

import { getInstalledBrews, getInstalledCasks } from "./brew"
import {
  readFlake,
  extractBrews,
  extractCasks,
  extractNixPackages,
} from "./flake"
import type { PackageStatus } from "./types"

// ANSI color codes matching Catppuccin Mocha
const ansi = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  green: "\x1b[38;2;166;227;161m", // #a6e3a1
  yellow: "\x1b[38;2;249;226;175m", // #f9e2af
  red: "\x1b[38;2;243;139;168m", // #f38ba8
  blue: "\x1b[38;2;137;180;250m", // #89b4fa
  mauve: "\x1b[38;2;203;166;247m", // #cba6f7
  subtext: "\x1b[38;2;166;173;200m", // #a6adc8
}

interface PackageEntry {
  name: string
  fullName: string
  status: PackageStatus
}

async function getPackageData(): Promise<{
  brews: PackageEntry[]
  casks: PackageEntry[]
  nixpkgs: PackageEntry[]
}> {
  const [installedBrews, installedCasks, flakeContent] = await Promise.all([
    getInstalledBrews(),
    getInstalledCasks(),
    readFlake(),
  ])

  const flakeBrews = extractBrews(flakeContent)
  const flakeCasks = extractCasks(flakeContent)
  const flakeNixpkgs = extractNixPackages(flakeContent)

  // Process brews
  const installedBrewSet = new Set(installedBrews)
  const flakeBrewSet = new Set(flakeBrews.map((b) => b.split("/").pop() || b))
  const flakeBrewFullNames = new Map(
    flakeBrews.map((b) => [b.split("/").pop() || b, b])
  )

  const brews: PackageEntry[] = []

  for (const name of installedBrews) {
    brews.push({
      name,
      fullName: flakeBrewFullNames.get(name) || name,
      status: flakeBrewSet.has(name) ? "synced" : "extra",
    })
  }

  for (const fullName of flakeBrews) {
    const name = fullName.split("/").pop() || fullName
    if (!installedBrewSet.has(name)) {
      brews.push({
        name,
        fullName,
        status: "missing",
      })
    }
  }

  // Process casks
  const installedCaskSet = new Set(installedCasks)
  const flakeCaskSet = new Set(flakeCasks)

  const casks: PackageEntry[] = []

  for (const name of installedCasks) {
    casks.push({
      name,
      fullName: name,
      status: flakeCaskSet.has(name) ? "synced" : "extra",
    })
  }

  for (const name of flakeCasks) {
    if (!installedCaskSet.has(name)) {
      casks.push({
        name,
        fullName: name,
        status: "missing",
      })
    }
  }

  // Process nixpkgs (always synced since we just read from flake)
  const nixpkgs: PackageEntry[] = flakeNixpkgs.map((name) => ({
    name,
    fullName: name,
    status: "synced" as PackageStatus,
  }))

  // Sort all by name
  brews.sort((a, b) => a.name.localeCompare(b.name))
  casks.sort((a, b) => a.name.localeCompare(b.name))
  nixpkgs.sort((a, b) => a.name.localeCompare(b.name))

  return { brews, casks, nixpkgs }
}

function getStatusColor(status: PackageStatus): string {
  switch (status) {
    case "synced":
      return ansi.green
    case "extra":
      return ansi.yellow
    case "missing":
      return ansi.red
  }
}

function getStatusIcon(status: PackageStatus): string {
  switch (status) {
    case "synced":
      return "✓"
    case "extra":
      return "+"
    case "missing":
      return "!"
  }
}

function getStatusLabel(status: PackageStatus): string {
  switch (status) {
    case "synced":
      return "synced"
    case "extra":
      return "extra"
    case "missing":
      return "missing"
  }
}

function printPackageList(
  packages: PackageEntry[],
  title: string,
  diffOnly: boolean
) {
  const filtered = diffOnly
    ? packages.filter((p) => p.status !== "synced")
    : packages

  if (filtered.length === 0 && diffOnly) {
    return
  }

  console.log(`\n${ansi.mauve}${ansi.bold}${title}${ansi.reset}`)
  console.log(`${ansi.subtext}${"─".repeat(50)}${ansi.reset}`)

  if (filtered.length === 0) {
    console.log(`${ansi.subtext}  No packages${ansi.reset}`)
    return
  }

  for (const pkg of filtered) {
    const color = getStatusColor(pkg.status)
    const icon = getStatusIcon(pkg.status)
    const label = getStatusLabel(pkg.status)
    const name = pkg.name.padEnd(30)

    console.log(`${color}  ${icon} ${name} ${ansi.dim}${label}${ansi.reset}`)
  }
}

function printSummary(
  brews: PackageEntry[],
  casks: PackageEntry[],
  nixpkgs: PackageEntry[]
) {
  const brewExtra = brews.filter((p) => p.status === "extra").length
  const brewMissing = brews.filter((p) => p.status === "missing").length
  const caskExtra = casks.filter((p) => p.status === "extra").length
  const caskMissing = casks.filter((p) => p.status === "missing").length

  console.log(`\n${ansi.blue}${ansi.bold}Summary${ansi.reset}`)
  console.log(`${ansi.subtext}${"─".repeat(50)}${ansi.reset}`)

  const totalExtra = brewExtra + caskExtra
  const totalMissing = brewMissing + caskMissing

  if (totalExtra === 0 && totalMissing === 0) {
    console.log(`${ansi.green}  ✓ All packages synced!${ansi.reset}`)
  } else {
    if (totalExtra > 0) {
      console.log(
        `${ansi.yellow}  + ${totalExtra} extra package(s) (installed but not in flake)${ansi.reset}`
      )
    }
    if (totalMissing > 0) {
      console.log(
        `${ansi.red}  ! ${totalMissing} missing package(s) (in flake but not installed)${ansi.reset}`
      )
    }
  }

  console.log(
    `\n${ansi.subtext}  Brews: ${brews.length} | Casks: ${casks.length} | Nix: ${nixpkgs.length}${ansi.reset}`
  )
}

export async function runCliList(): Promise<void> {
  console.log(`${ansi.mauve}${ansi.bold}Nix Package Manager${ansi.reset}`)

  const { brews, casks, nixpkgs } = await getPackageData()

  printPackageList(brews, "Homebrew Formulae", false)
  printPackageList(casks, "Homebrew Casks", false)
  printPackageList(nixpkgs, "Nix Packages", false)
  printSummary(brews, casks, nixpkgs)
}

export async function runCliDiff(): Promise<void> {
  console.log(`${ansi.mauve}${ansi.bold}Nix Package Manager - Differences${ansi.reset}`)

  const { brews, casks, nixpkgs } = await getPackageData()

  const brewDiffs = brews.filter((p) => p.status !== "synced")
  const caskDiffs = casks.filter((p) => p.status !== "synced")

  if (brewDiffs.length === 0 && caskDiffs.length === 0) {
    console.log(`\n${ansi.green}  ✓ All packages are synced!${ansi.reset}`)
    return
  }

  printPackageList(brews, "Homebrew Formulae", true)
  printPackageList(casks, "Homebrew Casks", true)
  printSummary(brews, casks, nixpkgs)
}

export function printHelp(): void {
  console.log(`${ansi.mauve}${ansi.bold}nix-manager${ansi.reset} - TUI for managing Homebrew packages vs Nix flake

${ansi.blue}Usage:${ansi.reset}
  nix-manager           Start interactive TUI
  nix-manager --list    List all packages with status
  nix-manager --diff    Show only extra/missing packages
  nix-manager --help    Show this help message

${ansi.blue}Status indicators:${ansi.reset}
  ${ansi.green}✓ synced${ansi.reset}   Package in flake and installed
  ${ansi.yellow}+ extra${ansi.reset}    Installed but not in flake
  ${ansi.red}! missing${ansi.reset}  In flake but not installed

${ansi.blue}TUI Keyboard shortcuts:${ansi.reset}
  j/k         Navigate up/down
  Tab         Switch between Brews/Casks/Nix tabs
  Space       Select package
  a           Add selected to flake
  d           Remove selected from flake
  /           Search/filter packages
  r           Refresh package lists
  Enter/l     View package details
  Esc         Clear filter/selection
  q           Quit
`)
}
