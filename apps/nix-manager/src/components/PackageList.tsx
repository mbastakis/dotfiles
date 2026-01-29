// PackageList component with custom list rendering

import { useTerminalDimensions } from "@opentui/react"
import type { Package } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"
import { EmptyState } from "@dotfiles/shared/components"

interface PackageListProps {
  packages: Package[]
  selectedIndex: number
  onSelect: (index: number) => void
  focused: boolean
}

// Calculate list height based on terminal size
// Header: title (3 lines) + tabs (5 lines with border/padding) = 8 lines
// StatusBar: summary (5 lines with border/padding) + hints (3 lines) = 8 lines
const CHROME_HEIGHT = 16

// Fixed column widths
const NAME_WIDTH = 30
const STATUS_WIDTH = 12

export function PackageList({
  packages,
  selectedIndex,
  onSelect,
  focused,
}: PackageListProps) {
  const { height: termHeight, width: termWidth } = useTerminalDimensions()
  const listHeight = Math.max(5, termHeight - CHROME_HEIGHT)

  if (packages.length === 0) {
    return (
      <box padding={2} justifyContent="center" alignItems="center" flexGrow={1}>
        <EmptyState message="No packages found" hint="Try switching tabs" />
      </box>
    )
  }

  // Reserve 1 line for position indicator
  const itemsHeight = listHeight - 1
  const visibleCount = itemsHeight
  const halfVisible = Math.floor(visibleCount / 2)
  let startIndex = Math.max(0, selectedIndex - halfVisible)
  const endIndex = Math.min(packages.length, startIndex + visibleCount)
  
  // Adjust start if we're near the end
  if (endIndex - startIndex < visibleCount) {
    startIndex = Math.max(0, endIndex - visibleCount)
  }
  
  const visiblePackages = packages.slice(startIndex, endIndex)

  return (
    <box flexDirection="column" height={listHeight} overflow="hidden">
      <box flexDirection="column" height={itemsHeight} overflow="hidden">
        {visiblePackages.map((pkg, i) => {
          const actualIndex = startIndex + i
          const isSelected = actualIndex === selectedIndex
          const statusColor = getStatusColor(pkg.status)
          const checkbox = pkg.selected ? "[✓]" : "[ ]"
          const statusText = `${getStatusIcon(pkg.status)} ${getStatusLabel(pkg.status)}`
          
          return (
            <box
              key={`${pkg.name}-${actualIndex}`}
              backgroundColor={isSelected ? colors.surface1 : "transparent"}
              flexDirection="row"
              width={termWidth}
              height={1}
            >
              <box width={5} paddingLeft={1}>
                <text fg={isSelected ? colors.text : colors.subtext0}>{checkbox}</text>
              </box>
              <box width={NAME_WIDTH}>
                <text fg={isSelected ? colors.text : colors.subtext0}>{pkg.name}</text>
              </box>
              <box width={STATUS_WIDTH}>
                <text fg={statusColor}>{statusText}</text>
              </box>
            </box>
          )
        })}
      </box>
      {/* Position indicator - always show */}
      <box paddingLeft={2} height={1}>
        <text fg={colors.subtext0}>
          {startIndex > 0 ? "↑" : " "} {selectedIndex + 1}/{packages.length} {endIndex < packages.length ? "↓" : " "}
        </text>
      </box>
    </box>
  )
}

function getStatusIcon(status: Package["status"]): string {
  switch (status) {
    case "synced":
      return "✓"
    case "extra":
      return "+"
    case "missing":
      return "!"
  }
}

function getStatusLabel(status: Package["status"]): string {
  switch (status) {
    case "synced":
      return "in nix"
    case "extra":
      return "extra"
    case "missing":
      return "missing"
  }
}

function getStatusColor(status: Package["status"]): string {
  switch (status) {
    case "synced":
      return colors.green
    case "extra":
      return colors.yellow
    case "missing":
      return colors.red
  }
}