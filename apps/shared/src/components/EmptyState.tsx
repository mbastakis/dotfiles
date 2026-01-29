// EmptyState component - placeholder for empty lists

import { colors } from "../theme"

interface EmptyStateProps {
  message: string
  hint?: string
}

export function EmptyState({ message, hint }: EmptyStateProps) {
  return (
    <box
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      paddingY={4}
      gap={1}
    >
      <text fg={colors.subtext0}>{message}</text>
      {hint && (
        <text fg={colors.surface2}>
          <em>{hint}</em>
        </text>
      )}
    </box>
  )
}
