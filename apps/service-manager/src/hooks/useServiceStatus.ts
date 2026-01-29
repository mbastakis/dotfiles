// Hook for polling service status updates

import { useState, useEffect, useRef } from "react"
import type { Service, ServiceStatus } from "../lib/types"
import { getServiceStatus } from "../lib/launchctl"

interface UseServiceStatusResult {
  updateStatus: (
    services: Service[]
  ) => Promise<Map<string, { status: ServiceStatus; pid?: number; exitCode?: number }>>
}

export function useServiceStatus(
  services: Service[],
  onStatusUpdate: (
    updates: Map<string, { status: ServiceStatus; pid?: number; exitCode?: number }>
  ) => void,
  pollInterval: number = 3000
): UseServiceStatusResult {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const updateStatus = async (
    servicesToCheck: Service[]
  ): Promise<Map<string, { status: ServiceStatus; pid?: number; exitCode?: number }>> => {
    const updates = new Map<
      string,
      { status: ServiceStatus; pid?: number; exitCode?: number }
    >()

    for (const service of servicesToCheck) {
      const statusInfo = await getServiceStatus(service.label)
      updates.set(service.label, statusInfo)
    }

    return updates
  }

  useEffect(() => {
    if (services.length === 0) return

    const poll = async () => {
      const updates = await updateStatus(services)
      onStatusUpdate(updates)
    }

    // Initial poll
    poll()

    // Set up interval
    intervalRef.current = setInterval(poll, pollInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [services.map((s) => s.label).join(","), pollInterval])

  return { updateStatus }
}
