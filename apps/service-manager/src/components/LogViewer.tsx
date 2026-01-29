// LogViewer component for showing service logs

import type { Service } from "../lib/types"
import { colors } from "@dotfiles/shared/theme"
import { truncateLine, truncatePath } from "@dotfiles/shared/utils"

interface LogViewerProps {
  visible: boolean
  service: Service | null
  lines: string[]
  scrollOffset: number
  loading: boolean
  error: string | null
  logType: "stdout" | "stderr"
}

export function LogViewer({
  visible,
  service,
  lines,
  scrollOffset,
  loading,
  error,
  logType,
}: LogViewerProps) {
  if (!visible || !service) return null

  const visibleHeight = 20
  const visibleLines = lines.slice(scrollOffset, scrollOffset + visibleHeight)
  const showScrollUp = scrollOffset > 0
  const showScrollDown = scrollOffset + visibleHeight < lines.length

  const logPath =
    logType === "stdout" ? service.stdoutPath : service.stderrPath

  return (
    <box
      border
      borderStyle="rounded"
      borderColor={colors.surface1}
      backgroundColor={colors.base}
      padding={1}
      flexDirection="column"
      flexGrow={1}
    >
      {/* Header */}
      <box
        borderBottom
        borderColor={colors.surface1}
        paddingX={1}
        paddingBottom={1}
        flexDirection="row"
        justifyContent="space-between"
      >
        <text>
          <span fg={colors.mauve}>
            <strong>
              {logType === "stdout" ? "Output Log" : "Error Log"}
            </strong>
          </span>
          <span fg={colors.subtext0}> - {service.label}</span>
        </text>
        <text fg={colors.subtext0}>
          {lines.length > 0
            ? `${scrollOffset + 1}-${Math.min(scrollOffset + visibleHeight, lines.length)}/${lines.length}`
            : "0/0"}
        </text>
      </box>

      {/* Log content */}
      <box flexGrow={1} flexDirection="column" paddingTop={1}>
        {loading ? (
          <box justifyContent="center" alignItems="center" flexGrow={1}>
            <text fg={colors.yellow}>Loading log...</text>
          </box>
        ) : error ? (
          <box justifyContent="center" alignItems="center" flexGrow={1}>
            <text fg={colors.red}>{error}</text>
          </box>
        ) : lines.length === 0 ? (
          <box justifyContent="center" alignItems="center" flexGrow={1}>
            <text fg={colors.subtext0}>
              <em>Log file is empty or doesn't exist yet</em>
            </text>
            {logPath && (
              <text fg={colors.subtext0}>
                <em>Path: {truncatePath(logPath, 50)}</em>
              </text>
            )}
          </box>
        ) : (
          <>
            {showScrollUp && (
              <text fg={colors.subtext0}>
                <em>↑ More above...</em>
              </text>
            )}
            {visibleLines.map((line, index) => (
              <text key={scrollOffset + index} fg={colors.text}>
                {truncateLine(line, 120)}
              </text>
            ))}
            {showScrollDown && (
              <text fg={colors.subtext0}>
                <em>↓ More below...</em>
              </text>
            )}
          </>
        )}
      </box>

      {/* Path info */}
      {logPath && (
        <box borderTop borderColor={colors.surface1} paddingTop={1} paddingX={1}>
          <text fg={colors.subtext0}>
            <span fg={colors.blue}>Path: </span>
            <span fg={colors.teal}>{truncatePath(logPath, 60)}</span>
          </text>
        </box>
      )}
    </box>
  )
}
