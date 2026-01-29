// Hook for tailing log files

import { useState, useEffect, useRef, useCallback } from "react"
import { watch } from "fs"
import { exists } from "fs/promises"
import { tailLog } from "../lib/launchctl"

interface UseLogTailResult {
  lines: string[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  scrollOffset: number
  setScrollOffset: (offset: number) => void
  totalLines: number
}

const MAX_LINES = 500

export function useLogTail(
  logPath: string | undefined,
  active: boolean = true
): UseLogTailResult {
  const [lines, setLines] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scrollOffset, setScrollOffset] = useState(0)
  const watcherRef = useRef<ReturnType<typeof watch> | null>(null)

  const loadLog = useCallback(async () => {
    if (!logPath) {
      setLines([])
      setError(null)
      return
    }

    setLoading(true)
    try {
      const fileExists = await exists(logPath)
      if (!fileExists) {
        setLines([])
        setError("Log file does not exist yet")
        setLoading(false)
        return
      }

      const logLines = await tailLog(logPath, MAX_LINES)
      setLines(logLines)
      setError(null)

      // Auto-scroll to bottom on new content
      if (logLines.length > 0) {
        setScrollOffset(Math.max(0, logLines.length - 20))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to read log")
      setLines([])
    } finally {
      setLoading(false)
    }
  }, [logPath])

  // Watch for file changes
  useEffect(() => {
    if (!active || !logPath) {
      if (watcherRef.current) {
        watcherRef.current.close()
        watcherRef.current = null
      }
      return
    }

    // Initial load
    loadLog()

    // Set up file watcher
    let debounceTimeout: ReturnType<typeof setTimeout> | null = null

    const setupWatcher = async () => {
      try {
        const fileExists = await exists(logPath)
        if (!fileExists) return

        watcherRef.current = watch(logPath, (eventType) => {
          if (eventType === "change") {
            if (debounceTimeout) clearTimeout(debounceTimeout)
            debounceTimeout = setTimeout(loadLog, 100)
          }
        })
      } catch {
        // File doesn't exist yet, that's ok
      }
    }

    setupWatcher()

    return () => {
      if (watcherRef.current) {
        watcherRef.current.close()
        watcherRef.current = null
      }
      if (debounceTimeout) {
        clearTimeout(debounceTimeout)
      }
    }
  }, [logPath, active, loadLog])

  return {
    lines,
    loading,
    error,
    refresh: loadLog,
    scrollOffset,
    setScrollOffset,
    totalLines: lines.length,
  }
}
