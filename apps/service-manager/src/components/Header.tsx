// Header component with title and service count

import type { Service } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"

interface HeaderProps {
  services: Service[]
  isWatching: boolean
}

export function Header({ services, isWatching }: HeaderProps) {
  const running = services.filter((s) => s.status === "running").length
  const stopped = services.filter((s) => s.status === "stopped").length
  const notInstalled = services.filter(
    (s) => s.status === "not_installed"
  ).length

  return (
    <box flexDirection="column">
      <box justifyContent="center" paddingY={1}>
        <text>
          <span fg={colors.mauve}>
            <strong>LaunchAgent Service Manager</strong>
          </span>
        </text>
      </box>
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
          <span fg={colors.green}>{running} running</span>
          {" | "}
          <span fg={colors.red}>{stopped} stopped</span>
          {notInstalled > 0 && (
            <>
              {" | "}
              <span fg={colors.yellow}>{notInstalled} not installed</span>
            </>
          )}
        </text>
        <text fg={colors.subtext0}>
          {isWatching ? (
            <span fg={colors.green}>● Watching plists</span>
          ) : (
            <span fg={colors.red}>○ Not watching</span>
          )}
        </text>
      </box>
    </box>
  )
}
