// Hook for fetching installed Homebrew packages

import { useState, useEffect, useCallback } from "react"
import { getInstalledBrews, getInstalledCasks, getInstalledMasApps } from "../lib/brew"
import type { MasApp } from "../lib/types"

interface UseBrewPackagesResult {
  brews: string[]
  casks: string[]
  masApps: MasApp[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

export function useBrewPackages(): UseBrewPackagesResult {
  const [brews, setBrews] = useState<string[]>([])
  const [casks, setCasks] = useState<string[]>([])
  const [masApps, setMasApps] = useState<MasApp[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [brewList, caskList, masList] = await Promise.all([
        getInstalledBrews(),
        getInstalledCasks(),
        getInstalledMasApps(),
      ])
      setBrews(brewList)
      setCasks(caskList)
      setMasApps(masList)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch packages"))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { brews, casks, masApps, loading, error, refresh }
}
