// Main App component with mode management and keyboard shortcuts

import { useState, useCallback, useMemo } from "react"
import { useKeyboard, useRenderer } from "@opentui/react"
import { Header } from "./components/Header"
import { ServiceList } from "./components/ServiceList"
import { StatusBar } from "./components/StatusBar"
import { DetailPanel } from "./components/DetailPanel"
import { LogViewer } from "./components/LogViewer"
import { useServices } from "./hooks/useServices"
import { useServiceStatus } from "./hooks/useServiceStatus"
import { useLogTail } from "./hooks/useLogTail"
import { usePlistWatcher } from "./hooks/usePlistWatcher"
import {
  startService,
  stopService,
  restartService,
  installPlist,
} from "./lib/launchctl"
import type { Service, ServiceStatus } from "./lib/types"
import { colors } from "@dotfiles/shared/theme"

type AppMode = "normal" | "detail" | "logs"

export function App() {
  const renderer = useRenderer()

  // State
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [mode, setMode] = useState<AppMode>("normal")
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  // Services data
  const { services, loading, refresh } = useServices()

  // Status polling - updates service statuses in place
  const handleStatusUpdate = useCallback(
    (
      updates: Map<
        string,
        { status: ServiceStatus; pid?: number; exitCode?: number }
      >
    ) => {
      // This is handled by the refresh cycle
    },
    []
  )

  useServiceStatus(services, handleStatusUpdate, 3000)

  // Watch for plist file changes
  const { isWatching } = usePlistWatcher(refresh)

  // Current service
  const currentService = services[selectedIndex] || null

  // Log tailing
  const {
    lines: logLines,
    loading: logLoading,
    error: logError,
    scrollOffset,
    setScrollOffset,
    refresh: refreshLog,
  } = useLogTail(currentService?.stdoutPath, mode === "logs")

  // Show temporary status message
  const showMessage = useCallback((msg: string) => {
    setStatusMessage(msg)
    setTimeout(() => setStatusMessage(null), 2000)
  }, [])

  // Service actions
  const handleStart = useCallback(async () => {
    if (!currentService) return
    if (currentService.status === "not_installed") {
      showMessage("Service not installed. Press 'i' to install first.")
      return
    }
    setActionLoading(true)
    const success = await startService(currentService.label)
    setActionLoading(false)
    showMessage(success ? `Started ${currentService.label}` : "Start failed")
    await refresh()
  }, [currentService, refresh, showMessage])

  const handleStop = useCallback(async () => {
    if (!currentService) return
    if (currentService.status === "not_installed") {
      showMessage("Service not installed")
      return
    }
    setActionLoading(true)
    const success = await stopService(currentService.label)
    setActionLoading(false)
    showMessage(success ? `Stopped ${currentService.label}` : "Stop failed")
    await refresh()
  }, [currentService, refresh, showMessage])

  const handleRestart = useCallback(async () => {
    if (!currentService) return
    if (currentService.status === "not_installed") {
      showMessage("Service not installed. Press 'i' to install first.")
      return
    }
    setActionLoading(true)
    showMessage(`Restarting ${currentService.label}...`)
    const success = await restartService(currentService.label)
    setActionLoading(false)
    showMessage(success ? `Restarted ${currentService.label}` : "Restart failed")
    await refresh()
  }, [currentService, refresh, showMessage])

  const handleInstall = useCallback(async () => {
    if (!currentService) return
    setActionLoading(true)
    const success = await installPlist(
      currentService.plistPath,
      currentService.label
    )
    setActionLoading(false)
    if (success) {
      showMessage(`Installed ${currentService.label}`)
      await refresh()
    } else {
      showMessage("Install failed")
    }
  }, [currentService, refresh, showMessage])

  // Handle keyboard input
  useKeyboard((key) => {
    // Global shortcuts
    if (key.ctrl && key.name === "c") {
      renderer.destroy()
      return
    }

    // Mode: logs
    if (mode === "logs") {
      switch (key.name) {
        case "escape":
        case "q":
          setMode("normal")
          break
        case "j":
        case "down":
          setScrollOffset((o) => Math.min(logLines.length - 10, o + 1))
          break
        case "k":
        case "up":
          setScrollOffset((o) => Math.max(0, o - 1))
          break
        case "g":
          setScrollOffset(0)
          break
        case "G":
          setScrollOffset(Math.max(0, logLines.length - 20))
          break
        case "r":
          refreshLog()
          break
      }
      return
    }

    // Mode: detail
    if (mode === "detail") {
      switch (key.name) {
        case "escape":
        case "h":
          setMode("normal")
          break
        case "s":
          handleStart()
          break
        case "x":
          handleStop()
          break
        case "r":
          handleRestart()
          break
        case "l":
          if (currentService?.stdoutPath) {
            setMode("logs")
          } else {
            showMessage("No log file configured")
          }
          break
      }
      return
    }

    // Mode: normal
    switch (key.name) {
      case "q":
        renderer.destroy()
        break

      case "j":
      case "down":
        setSelectedIndex((i) => Math.min(services.length - 1, i + 1))
        break

      case "k":
      case "up":
        setSelectedIndex((i) => Math.max(0, i - 1))
        break

      case "s":
        handleStart()
        break

      case "x":
        handleStop()
        break

      case "r":
        handleRestart()
        break

      case "i":
        handleInstall()
        break

      case "l":
      case "enter":
        if (currentService?.stdoutPath) {
          setMode("logs")
        } else {
          showMessage("No log file configured for this service")
        }
        break

      case "d":
        setMode("detail")
        break

      case "R":
        refresh()
        showMessage("Refreshed services")
        break

      case "g":
        setSelectedIndex(0)
        break

      case "G":
        setSelectedIndex(Math.max(0, services.length - 1))
        break
    }
  })

  const isLoading = loading || actionLoading

  // Full-screen log view
  if (mode === "logs") {
    return (
      <box
        flexDirection="column"
        backgroundColor={colors.base}
        width="100%"
        height="100%"
      >
        <LogViewer
          visible={true}
          service={currentService}
          lines={logLines}
          scrollOffset={scrollOffset}
          loading={logLoading}
          error={logError}
          logType="stdout"
        />
        <StatusBar
          currentService={currentService}
          isLoading={isLoading}
          mode={mode}
        />
      </box>
    )
  }

  return (
    <box
      flexDirection="column"
      backgroundColor={colors.base}
      width="100%"
      height="100%"
    >
      <Header services={services} isWatching={isWatching} />

      {statusMessage && (
        <box paddingX={2} paddingY={1} backgroundColor={colors.surface0}>
          <text fg={colors.yellow}>{statusMessage}</text>
        </box>
      )}

      <box flexDirection="row" flexGrow={1}>
        <box flexGrow={1} flexDirection="column">
          <ServiceList
            services={services}
            selectedIndex={selectedIndex}
            onSelect={setSelectedIndex}
            focused={mode === "normal"}
          />
        </box>

        <DetailPanel visible={mode === "detail"} service={currentService} />
      </box>

      <StatusBar
        currentService={currentService}
        isLoading={isLoading}
        mode={mode}
      />
    </box>
  )
}
