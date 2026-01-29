// StatusIndicator component - colored status with icon

import { colors } from "../theme"

type PresetStatus = "success" | "warning" | "error" | "info" | "neutral"

interface PresetStatusProps {
  status: PresetStatus
  text: string
  icon?: string
}

interface CustomStatusProps {
  text: string
  color: string
  icon: string
}

type StatusIndicatorProps = PresetStatusProps | CustomStatusProps

const STATUS_CONFIG: Record<PresetStatus, { color: string; icon: string }> = {
  success: { color: colors.green, icon: "●" },
  warning: { color: colors.yellow, icon: "◐" },
  error: { color: colors.red, icon: "○" },
  info: { color: colors.blue, icon: "●" },
  neutral: { color: colors.subtext0, icon: "◌" },
}

function isPresetProps(props: StatusIndicatorProps): props is PresetStatusProps {
  return "status" in props
}

export function StatusIndicator(props: StatusIndicatorProps) {
  if (isPresetProps(props)) {
    const config = STATUS_CONFIG[props.status]
    const displayIcon = props.icon ?? config.icon
    return (
      <text fg={config.color}>
        {displayIcon} {props.text}
      </text>
    )
  }

  // Custom color/icon
  return (
    <text fg={props.color}>
      {props.icon} {props.text}
    </text>
  )
}
