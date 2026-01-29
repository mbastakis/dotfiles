// DetailPanel component for showing package details

import type { PackageInfo, Package } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"
import { truncateText } from "@dotfiles/shared/utils"
import { PropertyRow, Panel, StatusIndicator } from "@dotfiles/shared/components"

interface DetailPanelProps {
  visible: boolean
  pkg: Package | null
  info: PackageInfo | null
  loading: boolean
}

export function DetailPanel({ visible, pkg, info, loading }: DetailPanelProps) {
  if (!visible || !pkg) return null

  return (
    <Panel width={40}>
      <PropertyRow label="Package" value={pkg.name} />

      {loading ? (
        <text fg={colors.yellow}>Loading info...</text>
      ) : (
        <>
          {info?.version && (
            <PropertyRow label="Version" value={info.version} />
          )}

          <PropertyRow
            label="Status"
            value={<PackageStatus status={pkg.status} />}
          />

          {info?.description && (
            <box marginTop={1}>
              <PropertyRow
                label="Desc"
                value={truncateText(info.description, 100)}
                valueColor={colors.subtext0}
              />
            </box>
          )}

          {info?.homepage && (
            <box marginTop={1}>
              <PropertyRow
                label="URL"
                value={info.homepage}
                valueColor={colors.teal}
              />
            </box>
          )}
        </>
      )}

      <box marginTop={2}>
        <text fg={colors.subtext0}>
          <em>Press Esc to close</em>
        </text>
      </box>
    </Panel>
  )
}

function PackageStatus({ status }: { status: Package["status"] }) {
  switch (status) {
    case "synced":
      return <StatusIndicator color={colors.green} icon="✓" text="Synced with flake.nix" />
    case "extra":
      return <StatusIndicator color={colors.yellow} icon="+" text="Installed but not in flake" />
    case "missing":
      return <StatusIndicator color={colors.red} icon="!" text="In flake but not installed" />
  }
}
