// Hook for polling service status updates

import { useEffect, useRef } from "react"
import type { Service } from "../lib/types"
import { getServiceStatus } from "../lib/launchctl"

export function useServiceStatus(
  services: Service[],
  onStatusChange: () => void,
  pollInterval: number = 3000
): void {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastStatusRef = useRef<Map<string, string>>(new Map())

  useEffect(() => {
    if (services.length === 0) return

    const poll = async () => {
      let hasChanges = false

      for (const service of services) {
        const statusInfo = await getServiceStatus(service.label)
        const lastStatus = lastStatusRef.current.get(service.label)
        
        if (lastStatus !== statusInfo.status) {
          hasChanges = true
          lastStatusRef.current.set(service.label, statusInfo.status)
        }
      }

      if (hasChanges) {
        onStatusChange()
      }
    }

    // Initialize last known statuses
    for (const service of services) {
      lastStatusRef.current.set(service.label, service.status)
    }

    // Set up interval (don't poll immediately, we already have initial state)
    intervalRef.current = setInterval(poll, pollInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [services.map((s) => s.label).join(","), pollInterval, onStatusChange])
}
