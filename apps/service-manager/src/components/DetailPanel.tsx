// DetailPanel component for showing service details

import type { Service } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"
import { truncateText, truncatePath } from "@dotfiles/shared/utils"

interface DetailPanelProps {
  visible: boolean
  service: Service | null
}

export function DetailPanel({ visible, service }: DetailPanelProps) {
  if (!visible || !service) return null

  return (
    <box
      border
      borderStyle="rounded"
      borderColor={colors.surface1}
      backgroundColor={colors.surface0}
      padding={2}
      width={45}
      flexDirection="column"
      gap={1}
    >
      <text>
        <span fg={colors.blue}>
          <strong>Service: </strong>
        </span>
        <span fg={colors.text}>{service.label}</span>
      </text>

      <text>
        <span fg={colors.blue}>
          <strong>Status: </strong>
        </span>
        <span fg={getStatusColor(service.status)}>
          {getStatusText(service)}
        </span>
      </text>

      {service.pid && (
        <text>
          <span fg={colors.blue}>
            <strong>PID: </strong>
          </span>
          <span fg={colors.text}>{service.pid}</span>
        </text>
      )}

      {service.exitCode !== undefined && (
        <text>
          <span fg={colors.blue}>
            <strong>Exit Code: </strong>
          </span>
          <span fg={service.exitCode === 0 ? colors.green : colors.red}>
            {service.exitCode}
          </span>
        </text>
      )}

      <box marginTop={1}>
        <text>
          <span fg={colors.blue}>
            <strong>Command: </strong>
          </span>
        </text>
      </box>
      <text fg={colors.subtext0}>
        {truncateText(service.program.join(" "), 40)}
      </text>

      <box marginTop={1} flexDirection="row" gap={2}>
        <text>
          <span fg={colors.blue}>RunAtLoad: </span>
          <span fg={service.runAtLoad ? colors.green : colors.subtext0}>
            {service.runAtLoad ? "Yes" : "No"}
          </span>
        </text>
        <text>
          <span fg={colors.blue}>KeepAlive: </span>
          <span fg={service.keepAlive ? colors.green : colors.subtext0}>
            {service.keepAlive ? "Yes" : "No"}
          </span>
        </text>
      </box>

      {service.stdoutPath && (
        <box marginTop={1}>
          <text>
            <span fg={colors.blue}>
              <strong>Stdout: </strong>
            </span>
            <span fg={colors.teal}>
              {truncatePath(service.stdoutPath, 35)}
            </span>
          </text>
        </box>
      )}

      {service.stderrPath && (
        <text>
          <span fg={colors.blue}>
            <strong>Stderr: </strong>
          </span>
          <span fg={colors.teal}>{truncatePath(service.stderrPath, 35)}</span>
        </text>
      )}

      <box marginTop={2}>
        <text fg={colors.subtext0}>
          <em>Press Esc to close</em>
        </text>
      </box>
    </box>
  )
}

function getStatusColor(status: Service["status"]): string {
  switch (status) {
    case "running":
      return colors.green
    case "stopped":
      return colors.red
    case "not_installed":
      return colors.yellow
  }
}

function getStatusText(service: Service): string {
  switch (service.status) {
    case "running":
      return "● Running"
    case "stopped":
      return "○ Stopped"
    case "not_installed":
      return "◌ Not Installed"
  }
}
