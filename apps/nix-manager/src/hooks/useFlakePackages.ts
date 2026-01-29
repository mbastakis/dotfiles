// Hook for parsing and managing flake.nix packages

import { useState, useEffect, useCallback } from "react"
import {
  readFlake,
  extractBrews,
  extractCasks,
  extractMasApps,
  extractNixPackages,
  addPackage,
  removePackage,
} from "../lib/flake"
import type { PackageType, MasApp } from "../lib/types"

interface UseFlakePackagesResult {
  brews: string[]
  casks: string[]
  masApps: MasApp[]
  nixpkgs: string[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  add: (name: string, type: PackageType, masAppId?: number) => Promise<void>
  remove: (name: string, type: PackageType) => Promise<void>
}

export function useFlakePackages(): UseFlakePackagesResult {
  const [brews, setBrews] = useState<string[]>([])
  const [casks, setCasks] = useState<string[]>([])
  const [masApps, setMasApps] = useState<MasApp[]>([])
  const [nixpkgs, setNixpkgs] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const content = await readFlake()
      setBrews(extractBrews(content))
      setCasks(extractCasks(content))
      setMasApps(extractMasApps(content))
      setNixpkgs(extractNixPackages(content))
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error("Failed to parse flake.nix")
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const add = useCallback(
    async (name: string, type: PackageType, masAppId?: number) => {
      try {
        await addPackage(name, type, undefined, masAppId)
        await refresh()
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error("Failed to add package")
        )
      }
    },
    [refresh]
  )

  const remove = useCallback(
    async (name: string, type: PackageType) => {
      try {
        await removePackage(name, type)
        await refresh()
      } catch (err) {
        setError(
          err instanceof Error ? err : new Error("Failed to remove package")
        )
      }
    },
    [refresh]
  )

  return { brews, casks, masApps, nixpkgs, loading, error, refresh, add, remove }
}
