// DetailPanel component for showing package details

import type { PackageInfo, Package } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"

interface DetailPanelProps {
  visible: boolean
  pkg: Package | null
  info: PackageInfo | null
  loading: boolean
}

export function DetailPanel({ visible, pkg, info, loading }: DetailPanelProps) {
  if (!visible || !pkg) return null

  return (
    <box
      border
      borderStyle="rounded"
      borderColor={colors.surface1}
      backgroundColor={colors.surface0}
      padding={2}
      width={40}
      flexDirection="column"
      gap={1}
    >
      <text>
        <span fg={colors.blue}>
          <strong>Package: </strong>
        </span>
        <span fg={colors.text}>{pkg.name}</span>
      </text>

      {loading ? (
        <text fg={colors.yellow}>Loading info...</text>
      ) : (
        <>
          {info?.version && (
            <text>
              <span fg={colors.blue}>
                <strong>Version: </strong>
              </span>
              <span fg={colors.text}>{info.version}</span>
            </text>
          )}

          <text>
            <span fg={colors.blue}>
              <strong>Status: </strong>
            </span>
            <span fg={getStatusColor(pkg.status)}>
              {getStatusText(pkg.status)}
            </span>
          </text>

          {info?.description && (
            <box marginTop={1}>
              <text>
                <span fg={colors.blue}>
                  <strong>Desc: </strong>
                </span>
                <span fg={colors.subtext0}>
                  {truncateText(info.description, 100)}
                </span>
              </text>
            </box>
          )}

          {info?.homepage && (
            <box marginTop={1}>
              <text>
                <span fg={colors.blue}>
                  <strong>URL: </strong>
                </span>
                <span fg={colors.teal}>{info.homepage}</span>
              </text>
            </box>
          )}
        </>
      )}

      <box marginTop={2}>
        <text fg={colors.subtext0}>
          <em>Press Esc to close</em>
        </text>
      </box>
    </box>
  )
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

function getStatusText(status: Package["status"]): string {
  switch (status) {
    case "synced":
      return "✓ Synced with flake.nix"
    case "extra":
      return "+ Installed but not in flake"
    case "missing":
      return "! In flake but not installed"
  }
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + "..."
}
