// Entry point for service-manager TUI

import { createCliRenderer } from "@opentui/core"
import { createRoot } from "@opentui/react"
import { App } from "./App"

async function main() {
  const renderer = await createCliRenderer({
    exitOnCtrlC: false, // Handle Ctrl+C in our keyboard handler
  })

  createRoot(renderer).render(<App />)
}

main().catch((err) => {
  console.error("Failed to start service-manager:", err)
  process.exit(1)
})
