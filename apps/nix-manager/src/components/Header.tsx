// Header component with title and tab selection

import type { PackageType } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"

interface HeaderProps {
  activeTab: PackageType
  onTabChange: (tab: PackageType) => void
}

export function Header({
  activeTab,
  onTabChange,
}: HeaderProps) {
  const tabs: { id: PackageType; label: string }[] = [
    { id: "brews", label: "Brews" },
    { id: "casks", label: "Casks" },
    { id: "masApps", label: "Mac Apps" },
    { id: "nixpkgs", label: "Nix Pkgs" },
  ]

  return (
    <box flexDirection="column">
      <box justifyContent="center" paddingTop={1} paddingBottom={1}>
        <text>
          <span fg={colors.mauve}>
            <strong>Nix Package Manager</strong>
          </span>
        </text>
      </box>
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
        <box flexDirection="row" gap={2}>
          {tabs.map((tab) => (
            <text
              key={tab.id}
              fg={activeTab === tab.id ? colors.blue : colors.subtext0}
              bg={activeTab === tab.id ? colors.surface1 : "transparent"}
            >
              {activeTab === tab.id ? `[ ${tab.label} ]` : `  ${tab.label}  `}
            </text>
          ))}
        </box>
      </box>
    </box>
  )
}
