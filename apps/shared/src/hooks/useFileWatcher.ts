// Generic file/directory watcher hook

import { useState, useEffect } from "react"
import { watch } from "fs"

interface UseFileWatcherOptions {
  /** Path to watch (file or directory) */
  path: string
  /** Optional file filter function for directory watching */
  filter?: (filename: string) => boolean
  /** Debounce delay in ms (default: 100) */
  debounceMs?: number
}

interface UseFileWatcherResult {
  isWatching: boolean
  lastChange: number | null
}

export function useFileWatcher(
  options: UseFileWatcherOptions,
  onFileChange: () => void
): UseFileWatcherResult {
  const { path, filter, debounceMs = 100 } = options
  const [isWatching, setIsWatching] = useState(false)
  const [lastChange, setLastChange] = useState<number | null>(null)

  useEffect(() => {
    let debounceTimeout: ReturnType<typeof setTimeout> | null = null

    try {
      const watcher = watch(path, (eventType, filename) => {
        // Skip if filter provided and doesn't match
        if (filter && filename && !filter(filename)) {
          return
        }

        // Only trigger on change events, not rename
        if (eventType === "change" || (eventType === "rename" && filename)) {
          if (debounceTimeout) {
            clearTimeout(debounceTimeout)
          }
          debounceTimeout = setTimeout(() => {
            setLastChange(Date.now())
            onFileChange()
          }, debounceMs)
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
  }, [path, filter, debounceMs, onFileChange])

  return { isWatching, lastChange }
}
