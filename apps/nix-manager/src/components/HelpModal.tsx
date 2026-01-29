// HelpModal component for showing keyboard shortcuts

import { colors } from "@dotfiles/shared/theme"
import { Panel } from "@dotfiles/shared/components"

interface HelpModalProps {
  visible: boolean
}

const shortcuts = [
  { key: "j/k", desc: "Navigate up/down" },
  { key: "Enter/l", desc: "View package details" },
  { key: "Space", desc: "Select/deselect package" },
  { key: "Tab", desc: "Switch tab (Brews/Casks/Nix)" },
  { key: "/", desc: "Search packages" },
  { key: "s", desc: "Toggle sort (name/status)" },
  { key: "a", desc: "Add package to flake.nix" },
  { key: "d", desc: "Delete package from flake.nix" },
  { key: "r", desc: "Refresh package list" },
  { key: "Esc", desc: "Clear filter/selection" },
  { key: "?", desc: "Show this help" },
  { key: "q", desc: "Quit" },
]

export function HelpModal({ visible }: HelpModalProps) {
  if (!visible) return null

  return (
    <box
      position="absolute"
      top={0}
      left={0}
      right={0}
      bottom={0}
      justifyContent="center"
      alignItems="center"
      backgroundColor={colors.crust}
    >
      <Panel width={45} borderColor={colors.blue}>
        <box justifyContent="center" paddingBottom={1}>
          <text fg={colors.mauve}>
            <strong>Keyboard Shortcuts</strong>
          </text>
        </box>

        {shortcuts.map(({ key, desc }) => (
          <box key={key} flexDirection="row">
            <text fg={colors.blue} width={12}>
              {key}
            </text>
            <text fg={colors.text}>{desc}</text>
          </box>
        ))}

        <box justifyContent="center" paddingTop={2}>
          <text fg={colors.subtext0}>
            Press <span fg={colors.yellow}>?</span> or{" "}
            <span fg={colors.yellow}>Esc</span> to close
          </text>
        </box>
      </Panel>
    </box>
  )
}
