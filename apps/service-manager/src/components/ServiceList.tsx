// ServiceList component with select-based navigation

import type { Service } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"
import { EmptyState } from "@dotfiles/shared/components"

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
      <box padding={2} justifyContent="center" alignItems="center" flexGrow={1}>
        <EmptyState
          message="No service configs found"
          hint="Add .toml files to ~/.config/service-manager/"
        />
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
  const enabledIcon = svc.enabled ? "✓" : "○"
  const statusIcon = getStatusIcon(svc.status)
  const statusText = getStatusText(svc)

  // Pad the label to align status
  const paddedLabel = svc.label.padEnd(28)

  return `${enabledIcon} ${statusIcon} ${paddedLabel} ${statusText}`
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
