// StatusIndicator component - colored status with icon

import { colors } from "../theme"

type StatusType = "success" | "warning" | "error" | "info" | "neutral"

interface StatusIndicatorProps {
  status: StatusType
  text: string
  icon?: string
}

const STATUS_CONFIG: Record<StatusType, { color: string; icon: string }> = {
  success: { color: colors.green, icon: "●" },
  warning: { color: colors.yellow, icon: "◐" },
  error: { color: colors.red, icon: "○" },
  info: { color: colors.blue, icon: "●" },
  neutral: { color: colors.subtext0, icon: "◌" },
}

export function StatusIndicator({ status, text, icon }: StatusIndicatorProps) {
  const config = STATUS_CONFIG[status]
  const displayIcon = icon ?? config.icon

  return (
    <text fg={config.color}>
      {displayIcon} {text}
    </text>
  )
}
