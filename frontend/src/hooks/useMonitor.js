import { useState, useEffect, useCallback } from 'react'
import { monitorApi } from '../utils/api'

export function useMonitor() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchStatus = useCallback(async () => {
    try {
      const data = await monitorApi.status()
      setStatus(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    // Auto-refresh every 10 seconds
    const id = setInterval(fetchStatus, 10000)
    return () => clearInterval(id)
  }, [fetchStatus])

  const startMonitoring = async () => {
    const data = await monitorApi.start()
    setStatus((prev) => ({ ...prev, is_monitoring: data.is_monitoring }))
    return data
  }

  const stopMonitoring = async () => {
    const data = await monitorApi.stop()
    setStatus((prev) => ({ ...prev, is_monitoring: data.is_monitoring }))
    return data
  }

  return { status, loading, error, fetchStatus, startMonitoring, stopMonitoring }
}
