// StatusBar component with service info and status

import type { Service } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"

interface StatusBarProps {
  currentService: Service | null
  isLoading: boolean
  mode: "normal" | "detail" | "logs"
}

export function StatusBar({ currentService, isLoading, mode }: StatusBarProps) {
  return (
    <box flexDirection="column">
      <box
        border
        borderStyle="single"
        borderColor={colors.surface1}
        paddingX={2}
        paddingY={1}
        flexDirection="row"
        justifyContent="space-between"
      >
        <text fg={colors.subtext0}>
          {currentService ? (
            <>
              <span fg={colors.blue}>{currentService.label}</span>
              {currentService.program.length > 0 && (
                <span fg={colors.subtext0}>
                  {" → "}
                  {currentService.program[0]}
                </span>
              )}
            </>
          ) : (
            <span>No service selected</span>
          )}
        </text>
        <text fg={colors.subtext0}>
          {isLoading ? (
            <span fg={colors.yellow}>Loading...</span>
          ) : (
            <span fg={colors.green}>Ready</span>
          )}
        </text>
      </box>
      <box backgroundColor={colors.mantle} paddingX={2} paddingY={1}>
        <text fg={colors.subtext0}>
          Press <span fg={colors.yellow}>?</span> for help
          {mode !== "normal" && (
            <>
              {" │ "}
              <span fg={colors.blue}>Esc</span> to go back
            </>
          )}
        </text>
      </box>
    </box>
  )
}
