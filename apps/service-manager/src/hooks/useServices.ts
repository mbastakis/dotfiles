// Hook for discovering and loading services from config files

import { useState, useEffect, useCallback } from "react"
import type { Service } from "../lib/types"
import { listConfigFiles, parseConfigToService } from "../lib/plist"
import { getServiceStatus } from "../lib/launchctl"

interface UseServicesResult {
  services: Service[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

export function useServices(): UseServicesResult {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadServices = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const configPaths = await listConfigFiles()

      if (configPaths.length === 0) {
        setServices([])
        setLoading(false)
        return
      }

      const loadedServices: Service[] = []

      for (const configPath of configPaths) {
        const partialService = await parseConfigToService(configPath)
        if (!partialService) continue

        // Get current status
        const statusInfo = await getServiceStatus(partialService.label)

        loadedServices.push({
          ...partialService,
          status: statusInfo.status,
          pid: statusInfo.pid,
          exitCode: statusInfo.exitCode,
        })
      }

      // Sort by label
      loadedServices.sort((a, b) => a.label.localeCompare(b.label))
      setServices(loadedServices)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load services")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadServices()
  }, [loadServices])

  return {
    services,
    loading,
    error,
    refresh: loadServices,
  }
}
