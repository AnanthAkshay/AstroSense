'use client'

import { useState, useEffect, useCallback } from 'react'
import { apiClient, SpaceWeatherData, SectorPredictions, BacktestData, ApiResponse } from '@/lib/api-client'

export interface UseApiDataReturn<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  lastUpdated: string | null
}

// Hook for fetching current space weather data
export function useCurrentData(refreshInterval: number = 30000): UseApiDataReturn<SpaceWeatherData> {
  const [data, setData] = useState<SpaceWeatherData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.fetchCurrentData()
      
      if (response.success) {
        setData(response.data)
        setLastUpdated(response.timestamp)
      } else {
        setError(response.error || 'Failed to fetch data')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    
    const interval = setInterval(fetchData, refreshInterval)
    return () => clearInterval(interval)
  }, [fetchData, refreshInterval])

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    lastUpdated,
  }
}

// Hook for fetching predictions
export function usePredictions(inputData?: Partial<SpaceWeatherData>): UseApiDataReturn<SectorPredictions> {
  const [data, setData] = useState<SectorPredictions | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const fetchPredictions = useCallback(async () => {
    if (!inputData) return

    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.predictImpact(inputData)
      
      if (response.success) {
        setData(response.data)
        setLastUpdated(response.timestamp)
      } else {
        setError(response.error || 'Failed to fetch predictions')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [inputData])

  useEffect(() => {
    if (inputData) {
      fetchPredictions()
    }
  }, [fetchPredictions])

  return {
    data,
    loading,
    error,
    refetch: fetchPredictions,
    lastUpdated,
  }
}

// Hook for backtesting
export function useBacktest(): UseApiDataReturn<BacktestData> & {
  runBacktest: (eventDate: string) => Promise<void>
} {
  const [data, setData] = useState<BacktestData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const runBacktest = useCallback(async (eventDate: string) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiClient.runBacktest(eventDate)
      
      if (response.success) {
        setData(response.data)
        setLastUpdated(response.timestamp)
      } else {
        setError(response.error || 'Failed to run backtest')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [])

  const refetch = useCallback(async () => {
    // For backtest, we need the event date to refetch
    // This would typically be stored in state or passed as parameter
    console.warn('Backtest refetch requires event date parameter')
  }, [])

  return {
    data,
    loading,
    error,
    refetch,
    lastUpdated,
    runBacktest,
  }
}

// Generic hook for any API call
export function useApiCall<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  dependencies: any[] = [],
  autoFetch: boolean = true
): UseApiDataReturn<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(autoFetch)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await apiCall()
      
      if (response.success) {
        setData(response.data)
        setLastUpdated(response.timestamp)
      } else {
        setError(response.error || 'API call failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [apiCall])

  useEffect(() => {
    if (autoFetch) {
      fetchData()
    }
  }, [fetchData, autoFetch, ...dependencies])

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    lastUpdated,
  }
}