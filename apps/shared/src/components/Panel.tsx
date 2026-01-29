// Panel component - bordered container with consistent styling

import { colors } from "../theme"

interface PanelProps {
  children: React.ReactNode
  title?: string
  width?: number | string
  height?: number | string
  borderColor?: string
  backgroundColor?: string
  padding?: number
}

export function Panel({
  children,
  title,
  width,
  height,
  borderColor = colors.surface1,
  backgroundColor = colors.surface0,
  padding = 2,
}: PanelProps) {
  return (
    <box
      border
      borderStyle="rounded"
      borderColor={borderColor}
      backgroundColor={backgroundColor}
      padding={padding}
      width={width}
      height={height}
      flexDirection="column"
      gap={1}
    >
      {title && (
        <text fg={colors.blue}>
          <strong>{title}</strong>
        </text>
      )}
      {children}
    </box>
  )
}
