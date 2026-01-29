// Entry point for nix-manager TUI

import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"
import { App } from "./App"
import { runCliList, runCliDiff, printHelp } from "./lib/cli"

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
