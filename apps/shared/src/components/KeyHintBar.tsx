// KeyHintBar component - row of keyboard hints with consistent styling

import { colors } from "../theme"
import { KeyHint } from "./KeyHint"

interface KeyHintBarProps {
  hints: Array<{ key: string; action: string }>
  separator?: string
}

export function KeyHintBar({ hints, separator = "  " }: KeyHintBarProps) {
  return (
    <box backgroundColor={colors.mantle} paddingX={2} paddingY={1}>
      <text fg={colors.subtext0}>
        {hints.map((hint, index) => (
          <span key={hint.key}>
            <span fg={colors.blue}>{hint.key}</span>
            <span>:{hint.action}</span>
            {index < hints.length - 1 && separator}
          </span>
        ))}
      </text>
    </box>
  )
}
