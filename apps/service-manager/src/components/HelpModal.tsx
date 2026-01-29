// HelpModal component for showing keyboard shortcuts

import { colors } from "@dotfiles/shared/theme"
import { Panel } from "@dotfiles/shared/components"

interface HelpModalProps {
  visible: boolean
  mode: "normal" | "detail" | "logs"
}

const normalShortcuts = [
  { key: "j/k", desc: "Navigate up/down" },
  { key: "g/G", desc: "Go to first/last" },
  { key: "s", desc: "Start service" },
  { key: "x", desc: "Stop service" },
  { key: "r", desc: "Restart service" },
  { key: "i", desc: "Install service" },
  { key: "e", desc: "Toggle enabled" },
  { key: "l/Enter", desc: "View logs" },
  { key: "d", desc: "View details" },
  { key: "R", desc: "Refresh services" },
  { key: "?", desc: "Show this help" },
  { key: "q", desc: "Quit" },
]

const detailShortcuts = [
  { key: "s", desc: "Start service" },
  { key: "x", desc: "Stop service" },
  { key: "r", desc: "Restart service" },
  { key: "e", desc: "Toggle enabled" },
  { key: "l", desc: "View logs" },
  { key: "Esc/h", desc: "Go back" },
]

const logShortcuts = [
  { key: "j/k", desc: "Scroll up/down" },
  { key: "g", desc: "Go to top" },
  { key: "G", desc: "Go to bottom" },
  { key: "r", desc: "Refresh log" },
  { key: "Esc/q", desc: "Go back" },
]

export function HelpModal({ visible, mode }: HelpModalProps) {
  if (!visible) return null

  const shortcuts =
    mode === "logs" ? logShortcuts : mode === "detail" ? detailShortcuts : normalShortcuts

  const title =
    mode === "logs"
      ? "Log Viewer Shortcuts"
      : mode === "detail"
        ? "Detail View Shortcuts"
        : "Keyboard Shortcuts"

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
            <strong>{title}</strong>
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
