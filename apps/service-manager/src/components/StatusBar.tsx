// StatusBar component with keyboard hints

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
        {mode === "normal" && (
          <text fg={colors.subtext0}>
            <span fg={colors.blue}>j/k</span>:Nav{"  "}
            <span fg={colors.blue}>s</span>:Start{"  "}
            <span fg={colors.blue}>x</span>:Stop{"  "}
            <span fg={colors.blue}>r</span>:Restart{"  "}
            <span fg={colors.blue}>i</span>:Install{"  "}
            <span fg={colors.blue}>l</span>:Logs{"  "}
            <span fg={colors.blue}>d</span>:Details{"  "}
            <span fg={colors.blue}>R</span>:Refresh{"  "}
            <span fg={colors.blue}>q</span>:Quit
          </text>
        )}
        {mode === "detail" && (
          <text fg={colors.subtext0}>
            <span fg={colors.blue}>Esc/h</span>:Back{"  "}
            <span fg={colors.blue}>s</span>:Start{"  "}
            <span fg={colors.blue}>x</span>:Stop{"  "}
            <span fg={colors.blue}>r</span>:Restart{"  "}
            <span fg={colors.blue}>l</span>:Logs
          </text>
        )}
        {mode === "logs" && (
          <text fg={colors.subtext0}>
            <span fg={colors.blue}>j/k</span>:Scroll{"  "}
            <span fg={colors.blue}>g</span>:Top{"  "}
            <span fg={colors.blue}>G</span>:Bottom{"  "}
            <span fg={colors.blue}>r</span>:Refresh{"  "}
            <span fg={colors.blue}>Esc/q</span>:Back
          </text>
        )}
      </box>
    </box>
  )
}
