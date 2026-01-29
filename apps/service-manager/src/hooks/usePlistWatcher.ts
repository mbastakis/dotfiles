// Hook for watching config directory for changes

import { useState, useEffect, useCallback } from "react"
import { watch } from "fs"
import { getConfigDir } from "../lib/plist"

interface UseConfigWatcherResult {
  isWatching: boolean
  lastChange: number | null
}

export function usePlistWatcher(
  onFileChange: () => void
): UseConfigWatcherResult {
  const [isWatching, setIsWatching] = useState(false)
  const [lastChange, setLastChange] = useState<number | null>(null)

  useEffect(() => {
    const configDir = getConfigDir()
    let debounceTimeout: ReturnType<typeof setTimeout> | null = null

    try {
      const watcher = watch(configDir, (eventType, filename) => {
        if (filename?.endsWith(".toml")) {
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
