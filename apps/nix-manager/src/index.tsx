// Entry point for nix-manager TUI

import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"
import { App } from "./App"
import { runCliList, runCliDiff, runCliAdd, runCliRemove, printHelp } from "./lib/cli"
import type { PackageType } from "./lib/types"

/**
 * Parse CLI arguments for add/remove commands
 * Returns { action, type, name, masId } or null if not a subcommand
 */
function parseSubcommand(args: string[]): {
  action: "add" | "remove"
  type: PackageType
  name: string
  masId?: number
} | null {
  const action = args[0]
  if (action !== "add" && action !== "remove") {
    return null
  }

  const restArgs = args.slice(1)
  let type: PackageType = "brews" // default
  let name: string | undefined
  let masId: number | undefined

  // Parse flags and extract package name
  for (let i = 0; i < restArgs.length; i++) {
    const arg = restArgs[i]

    if (arg === "--cask") {
      type = "casks"
    } else if (arg === "--mas") {
      type = "masApps"
    } else if (arg === "--nix") {
      type = "nixpkgs"
    } else if (!arg.startsWith("-")) {
      // This is a positional argument
      if (name === undefined) {
        name = arg
      } else if (type === "masApps" && masId === undefined) {
        // Second positional for mas apps is the ID
        const parsed = parseInt(arg, 10)
        if (isNaN(parsed)) {
          console.error(`Error: Invalid App Store ID "${arg}"`)
          process.exit(1)
        }
        masId = parsed
      }
    }
  }

  if (!name) {
    console.error(`Error: Package name is required for ${action}`)
    printHelp()
    process.exit(1)
  }

  return { action, type, name, masId }
}

async function main() {
  const args = process.argv.slice(2)

  // Handle CLI mode flags
  if (args.includes("--help") || args.includes("-h")) {
    printHelp()
    return
  }

  if (args.includes("--list") || args.includes("-l")) {
    await runCliList()
    return
  }

  if (args.includes("--diff") || args.includes("-d")) {
    await runCliDiff()
    return
  }

  // Handle add/remove subcommands
  const subcommand = parseSubcommand(args)
  if (subcommand) {
    const success =
      subcommand.action === "add"
        ? await runCliAdd(subcommand.type, subcommand.name, subcommand.masId)
        : await runCliRemove(subcommand.type, subcommand.name)

    process.exit(success ? 0 : 1)
  }

  // Default: start TUI
  const renderer = await createCliRenderer({
    exitOnCtrlC: false, // Handle Ctrl+C in our keyboard handler
  })

  createRoot(renderer).render(<App />)
}

main().catch((err) => {
  console.error("Failed to start nix-manager:", err)
  process.exit(1)
})
