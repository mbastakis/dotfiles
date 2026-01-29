// Hook for watching plist directory for changes

import { useState, useEffect, useCallback } from "react"
import { watch } from "fs"
import { getLaunchAgentsSrcPath } from "../lib/plist"

interface UsePlistWatcherResult {
  isWatching: boolean
  lastChange: number | null
}

export function usePlistWatcher(
  onFileChange: () => void
): UsePlistWatcherResult {
  const [isWatching, setIsWatching] = useState(false)
  const [lastChange, setLastChange] = useState<number | null>(null)

  useEffect(() => {
    const plistDir = getLaunchAgentsSrcPath()
    let debounceTimeout: ReturnType<typeof setTimeout> | null = null

    try {
      const watcher = watch(plistDir, (eventType, filename) => {
        if (filename?.endsWith(".plist")) {
          if (debounceTimeout) {
            clearTimeout(debounceTimeout)
          }
          debounceTimeout = setTimeout(() => {
            setLastChange(Date.now())
            onFileChange()
          }, 100)
        }
      })

      setIsWatching(true)

      return () => {
        watcher.close()
        if (debounceTimeout) {
          clearTimeout(debounceTimeout)
        }
        setIsWatching(false)
      }
    } catch {
      setIsWatching(false)
    }
  }, [onFileChange])

  return { isWatching, lastChange }
}
