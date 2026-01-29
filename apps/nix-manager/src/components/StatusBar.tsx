// StatusBar component with summary and keyboard shortcuts

import type { Package, PackageType } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"

type SortMode = "name" | "status-asc" | "status-desc"

interface StatusBarProps {
  packages: Package[]
  packageType: PackageType
  selectedCount: number
  isWatching: boolean
  isLoading: boolean
  sortMode: SortMode
}

export function StatusBar({
  packages,
  packageType,
  selectedCount,
  isWatching,
  isLoading,
  sortMode,
}: StatusBarProps) {
  const total = packages.length
  const synced = packages.filter((p) => p.status === "synced").length
  const extra = packages.filter((p) => p.status === "extra").length
  const missing = packages.filter((p) => p.status === "missing").length

  const typeLabel =
    packageType === "brews"
      ? "brews"
      : packageType === "casks"
        ? "casks"
        : packageType === "masApps"
          ? "mac apps"
          : "nix pkgs"

  return (
    <box flexDirection="column">
      <box
        border
        borderStyle="rounded"
        borderColor={colors.surface1}
        paddingLeft={2}
        paddingRight={2}
        paddingTop={1}
        paddingBottom={1}
        flexDirection="row"
        justifyContent="space-between"
      >
        <text fg={colors.subtext0}>
          {selectedCount > 0 && (
            <span fg={colors.blue}>{selectedCount} selected │ </span>
          )}
          <span>
            {total} {typeLabel}
          </span>
          {synced > 0 && <span fg={colors.green}> ({synced} in nix</span>}
          {extra > 0 && <span fg={colors.yellow}>, {extra} extra</span>}
          {missing > 0 && <span fg={colors.red}>, {missing} missing</span>}
          {(synced > 0 || extra > 0 || missing > 0) && <span fg={colors.subtext0}>)</span>}
        </text>
        <text fg={colors.subtext0}>
          {isLoading ? (
            <span fg={colors.yellow}>Loading...</span>
          ) : isWatching ? (
            <span fg={colors.green}>● Watching</span>
          ) : (
            <span fg={colors.red}>○ Not watching</span>
          )}
        </text>
      </box>
      <box backgroundColor={colors.mantle} paddingLeft={2} paddingRight={2} paddingTop={1} paddingBottom={1}>
        <text fg={colors.subtext0}>
          <span>Sort: </span>
          <span fg={colors.blue}>{sortMode === "name" ? "Name" : sortMode === "status-asc" ? "Status ↑" : "Status ↓"}</span>
          <span> │ </span>
          <span fg={colors.subtext0}>Press </span>
          <span fg={colors.yellow}>?</span>
          <span fg={colors.subtext0}> for help</span>
        </text>
      </box>
    </box>
  )
}
