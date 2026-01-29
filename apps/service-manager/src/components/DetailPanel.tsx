// DetailPanel component for showing service details

import type { Service } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"
import { truncateText, truncatePath } from "@dotfiles/shared/utils"
import { PropertyRow, Panel, StatusIndicator } from "@dotfiles/shared/components"

interface DetailPanelProps {
  visible: boolean
  service: Service | null
}

export function DetailPanel({ visible, service }: DetailPanelProps) {
  if (!visible || !service) return null

  return (
    <Panel width={45}>
      <PropertyRow label="Service" value={service.label} />

      <PropertyRow
        label="Enabled"
        value={
          <span fg={service.enabled ? colors.green : colors.yellow}>
            {service.enabled ? "Yes" : "No"}
          </span>
        }
      />

      <PropertyRow
        label="Status"
        value={<ServiceStatus status={service.status} />}
      />

      {service.pid && (
        <PropertyRow label="PID" value={String(service.pid)} />
      )}

      {service.exitCode !== undefined && (
        <PropertyRow
          label="Exit Code"
          value={
            <span fg={service.exitCode === 0 ? colors.green : colors.red}>
              {service.exitCode}
            </span>
          }
        />
      )}

      <box marginTop={1}>
        <PropertyRow label="Command" value="" />
      </box>
      <text fg={colors.subtext0}>
        {truncateText(service.program.join(" "), 40)}
      </text>

      <box marginTop={1} flexDirection="row" gap={2}>
        <PropertyRow
          label="RunAtLoad"
          value={
            <span fg={service.runAtLoad ? colors.green : colors.subtext0}>
              {service.runAtLoad ? "Yes" : "No"}
            </span>
          }
        />
        <PropertyRow
          label="KeepAlive"
          value={
            <span fg={service.keepAlive ? colors.green : colors.subtext0}>
              {service.keepAlive ? "Yes" : "No"}
            </span>
          }
        />
      </box>

      {service.stdoutPath && (
        <box marginTop={1}>
          <PropertyRow
            label="Stdout"
            value={truncatePath(service.stdoutPath, 35)}
            valueColor={colors.teal}
          />
        </box>
      )}

      {service.stderrPath && (
        <PropertyRow
          label="Stderr"
          value={truncatePath(service.stderrPath, 35)}
          valueColor={colors.teal}
        />
      )}

      <box marginTop={1}>
        <PropertyRow
          label="Config"
          value={truncatePath(service.configPath, 35)}
          valueColor={colors.lavender}
        />
      </box>

      <box marginTop={2}>
        <text fg={colors.subtext0}>
          <em>Press Esc to close</em>
        </text>
      </box>
    </Panel>
  )
}

function ServiceStatus({ status }: { status: Service["status"] }) {
  switch (status) {
    case "running":
      return <StatusIndicator color={colors.green} icon="●" text="Running" />
    case "stopped":
      return <StatusIndicator color={colors.red} icon="○" text="Stopped" />
    case "not_installed":
      return <StatusIndicator color={colors.yellow} icon="◌" text="Not Installed" />
  }
}
