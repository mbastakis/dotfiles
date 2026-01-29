// ServiceList component with select-based navigation

import type { Service } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"

interface ServiceListProps {
  services: Service[]
  selectedIndex: number
  onSelect: (index: number) => void
  focused: boolean
}

export function ServiceList({
  services,
  selectedIndex,
  onSelect,
  focused,
}: ServiceListProps) {
  if (services.length === 0) {
    return (
      <box
        padding={2}
        justifyContent="center"
        alignItems="center"
        flexGrow={1}
      >
        <text fg={colors.subtext0}>
          <em>No LaunchAgent plists found in ~/dotfiles/dot-launchagents/</em>
        </text>
      </box>
    )
  }

  return (
    <box flexDirection="column" flexGrow={1}>
      <select
        options={services.map((svc) => ({
          name: formatServiceLine(svc),
          value: svc.label,
        }))}
        selectedIndex={selectedIndex}
        onChange={(index) => onSelect(index)}
        focused={focused}
        height={15}
        selectedBackgroundColor={colors.surface1}
        selectedTextColor={colors.text}
        highlightBackgroundColor={colors.surface0}
      />
    </box>
  )
}

function formatServiceLine(svc: Service): string {
  const statusIcon = getStatusIcon(svc.status)
  const statusText = getStatusText(svc)

  // Pad the label to align status
  const paddedLabel = svc.label.padEnd(30)

  return `${statusIcon} ${paddedLabel} ${statusText}`
}

function getStatusIcon(status: Service["status"]): string {
  switch (status) {
    case "running":
      return "●"
    case "stopped":
      return "○"
    case "not_installed":
      return "◌"
  }
}

function getStatusText(svc: Service): string {
  switch (svc.status) {
    case "running":
      return svc.pid ? `Running (PID ${svc.pid})` : "Running"
    case "stopped":
      return svc.exitCode !== undefined
        ? `Stopped (exit ${svc.exitCode})`
        : "Stopped"
    case "not_installed":
      return "Not Installed"
  }
}
