// Main App component with mode management and keyboard shortcuts

import { useState, useCallback } from "react"
import { useKeyboard, useRenderer } from "@opentui/react"
import { Header } from "./components/Header"
import { ServiceList } from "./components/ServiceList"
import { StatusBar } from "./components/StatusBar"
import { DetailPanel } from "./components/DetailPanel"
import { LogViewer } from "./components/LogViewer"
import { HelpModal } from "./components/HelpModal"
import { useServices } from "./hooks/useServices"
import { useServiceStatus } from "./hooks/useServiceStatus"
import { useLogTail } from "./hooks/useLogTail"
import { usePlistWatcher } from "./hooks/usePlistWatcher"
import {
  startService,
  stopService,
  restartService,
  uninstallService,
} from "./lib/launchctl"
import { updateConfigEnabled } from "./lib/plist"
import type { Service } from "./lib/types"
import { colors } from "@dotfiles/shared/theme"

type AppMode = "normal" | "detail" | "logs" | "help"

export function App() {
  const renderer = useRenderer()

  // State
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [mode, setMode] = useState<AppMode>("normal")
  const [helpFromMode, setHelpFromMode] = useState<"normal" | "detail" | "logs">("normal")
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  // Services data
  const { services, loading, refresh } = useServices()

  // Status polling - refreshes when status changes detected
  useServiceStatus(services, refresh, 3000)

  // Watch for config file changes
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
    if (!currentService || actionLoading) return
    if (currentService.status === "not_installed") {
      showMessage("Service not installed. Enable it first with 'e'.")
      return
    }
    setActionLoading(true)
    const success = await startService(currentService.label)
    setActionLoading(false)
    showMessage(success ? `Started ${currentService.label}` : "Start failed")
    await refresh()
  }, [currentService, actionLoading, refresh, showMessage])

  const handleStop = useCallback(async () => {
    if (!currentService || actionLoading) return
    if (currentService.status === "not_installed") {
      showMessage("Service not installed")
      return
    }
    setActionLoading(true)
    const success = await stopService(currentService.label)
    setActionLoading(false)
    showMessage(success ? `Stopped ${currentService.label}` : "Stop failed")
    await refresh()
  }, [currentService, actionLoading, refresh, showMessage])

  const handleRestart = useCallback(async () => {
    if (!currentService || actionLoading) return
    if (currentService.status === "not_installed") {
      showMessage("Service not installed. Enable it first with 'e'.")
      return
    }
    setActionLoading(true)
    showMessage(`Restarting ${currentService.label}...`)
    const success = await restartService(currentService.label)
    setActionLoading(false)
    showMessage(success ? `Restarted ${currentService.label}` : "Restart failed")
    await refresh()
  }, [currentService, actionLoading, refresh, showMessage])

  const handleToggleEnabled = useCallback(async () => {
    if (!currentService || actionLoading) return
    setActionLoading(true)
    
    const newEnabled = !currentService.enabled
    const success = await updateConfigEnabled(currentService.configPath, newEnabled)
    
    if (success) {
      if (newEnabled) {
        // Enable: install and start
        const { installService } = await import("./lib/launchctl")
        const installed = await installService(currentService.configPath)
        if (!installed) {
          showMessage(`Config updated but failed to install ${currentService.label}`)
        } else {
          const started = await startService(currentService.label)
          showMessage(started 
            ? `Enabled ${currentService.label}` 
            : `Enabled ${currentService.label} (failed to start)`)
        }
      } else {
        // Disable: stop and uninstall
        const uninstalled = await uninstallService(currentService.label)
        showMessage(uninstalled 
          ? `Disabled ${currentService.label}` 
          : `Config updated but failed to uninstall ${currentService.label}`)
      }
    } else {
      showMessage("Failed to update config")
    }
    
    setActionLoading(false)
    await refresh()
  }, [currentService, actionLoading, refresh, showMessage])

  // Handle keyboard input
  useKeyboard((key) => {
    // Global shortcuts
    if (key.ctrl && key.name === "c") {
      renderer.destroy()
      return
    }

    // Help mode - any key closes it
    if (mode === "help") {
      if (key.name === "escape" || key.name === "?" || key.name === "enter") {
        setMode(helpFromMode)
      }
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
          if (logLines.length === 0) break
          setScrollOffset((o) => Math.max(0, Math.min(logLines.length - 10, o + 1)))
          break
        case "k":
        case "up":
          if (logLines.length === 0) break
          setScrollOffset((o) => Math.max(0, o - 1))
          break
        case "g":
          setScrollOffset(0)
          break
        case "G":
          if (logLines.length === 0) break
          setScrollOffset(Math.max(0, logLines.length - 20))
          break
        case "r":
          refreshLog()
          break
        case "?":
          setHelpFromMode("logs")
          setMode("help")
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
        case "e":
          handleToggleEnabled()
          break
        case "l":
        case "enter":
          if (currentService?.stdoutPath) {
            setMode("logs")
          } else {
            showMessage("No log file configured")
          }
          break
        case "?":
          setHelpFromMode("detail")
          setMode("help")
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
        if (services.length === 0) break
        setSelectedIndex((i) => Math.min(services.length - 1, i + 1))
        break

      case "k":
      case "up":
        if (services.length === 0) break
        setSelectedIndex((i) => Math.max(0, i - 1))
        break

      case "s":
        handleStart()
        break

      case "x":
        handleStop()
        break

      case "r":
        if (key.shift) {
          refresh()
          showMessage("Refreshed services")
        } else {
          handleRestart()
        }
        break

      case "e":
        handleToggleEnabled()
        break

      case "l":
      case "enter":
        if (!currentService) {
          showMessage("No service selected")
        } else if (currentService.stdoutPath) {
          setMode("logs")
        } else {
          showMessage("No log file configured for this service")
        }
        break

      case "d":
        setMode("detail")
        break

      case "g":
        if (services.length === 0) break
        if (key.shift) {
          setSelectedIndex(Math.max(0, services.length - 1))
        } else {
          setSelectedIndex(0)
        }
        break

      case "?":
        setHelpFromMode("normal")
        setMode("help")
        break
    }
  })

  const isLoading = loading || actionLoading

  // StatusBar mode (never "help")
  const statusBarMode = mode === "help" ? helpFromMode : mode

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
          mode={statusBarMode}
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
            focused={mode === "normal" || mode === "help"}
          />
        </box>

        <DetailPanel visible={mode === "detail"} service={currentService} />
      </box>

      <StatusBar
        currentService={currentService}
        isLoading={isLoading}
        mode={statusBarMode}
      />

      <HelpModal visible={mode === "help"} mode={helpFromMode} />
    </box>
  )
}
