// KeyHint component - single keyboard shortcut hint

import { colors } from "../theme"

interface KeyHintProps {
  keyName: string
  action: string
}

export function KeyHint({ keyName, action }: KeyHintProps) {
  return (
    <text>
      <span fg={colors.blue}>{keyName}</span>
      <span fg={colors.subtext0}>:{action}</span>
    </text>
  )
}
