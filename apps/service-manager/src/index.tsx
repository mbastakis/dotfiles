// Entry point for service-manager TUI and CLI

import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"
import { App } from "./App"
import { syncServices } from "./lib/launchctl"
import { getConfigDir } from "./lib/plist"

// Colors for CLI output
const GREEN = "\x1b[32m"
const RED = "\x1b[31m"
const YELLOW = "\x1b[33m"
const NC = "\x1b[0m" // No color

async function runSync(): Promise<void> {
  console.log(`Syncing services from ${getConfigDir()}...`)
  
  const results = await syncServices()
  
  if (results.length === 0) {
    console.log(`${YELLOW}No config files found${NC}`)
    return
  }

  let hasErrors = false
  
  for (const result of results) {
    switch (result.action) {
      case "installed":
        console.log(`${GREEN}[+]${NC} ${result.label}: installed and started`)
        break
      case "reinstalled":
        console.log(`${GREEN}[~]${NC} ${result.label}: reinstalled and started`)
        break
      case "uninstalled":
        console.log(`${YELLOW}[-]${NC} ${result.label}: stopped and uninstalled`)
        break
      case "unchanged":
        console.log(`${GREEN}[=]${NC} ${result.label}: up to date`)
        break
      case "error":
        console.log(`${RED}[!]${NC} ${result.label}: ${result.error}`)
        hasErrors = true
        break
    }
  }
  
  if (hasErrors) {
    process.exit(1)
  }
}

async function runTui(): Promise<void> {
  const renderer = await createCliRenderer({
    exitOnCtrlC: false, // Handle Ctrl+C in our keyboard handler
  })

  createRoot(renderer).render(<App />)
}

async function main() {
  const args = process.argv.slice(2)
  
  // CLI mode
  if (args[0] === "sync") {
    await runSync()
    process.exit(0)
  }
  
  if (args[0] === "--help" || args[0] === "-h") {
    console.log(`service-manager - Manage macOS LaunchAgent services

Usage:
  svc              Launch interactive TUI
  svc sync         Sync all services from config files
  svc --help       Show this help message

Config files are read from ~/.config/service-manager/*.toml
`)
    process.exit(0)
  }
  
  // TUI mode (default)
  await runTui()
}

main().catch((err) => {
  console.error("Failed to start service-manager:", err)
  process.exit(1)
})
