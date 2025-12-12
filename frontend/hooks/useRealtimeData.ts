'use client'

import { useEffect, useCallback, useRef } from 'react'
import { useWebSocket } from './useWebSocket'
import { useAppContext } from '@/contexts/AppContext'
import { SpaceWeatherData, SectorPredictions } from '@/lib/api-client'

interface RealtimeDataUpdate {
  type: 'space_weather_update' | 'prediction_update' | 'alert' | 'system_status'
  data: any
  timestamp: string
}

interface SpaceWeatherUpdate {
  current_data: SpaceWeatherData
  predictions: SectorPredictions
  composite_score: number
  alerts?: Array<{
    id: string
    type: 'flash' | 'forecast'
    severity: 'low' | 'moderate' | 'high' | 'critical'
    title: string
    description: string
    affected_sectors: string[]
    confidence?: number
    expires_at?: string
    mitigation_recommendations?: string[]
  }>
}

interface UseRealtimeDataOptions {
  autoConnect?: boolean
  onDataUpdate?: (data: SpaceWeatherUpdate) => void
  onAlert?: (alert: any) => void
  onConnectionChange?: (status: string) => void
}

export function useRealtimeData(options: UseRealtimeDataOptions = {}) {
  const { 
    autoConnect = true, 
    onDataUpdate, 
    onAlert, 
    onConnectionChange 
  } = options
  
  const { state, dispatch } = useAppContext()
  const { 
    isConnected, 
    isConnecting, 
    connectionStatus, 
    lastMessage, 
    error, 
    connect, 
    disconnect 
  } = useWebSocket(autoConnect)
  
  const lastUpdateRef = useRef<Date>(new Date())
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Handle connection status changes
  useEffect(() => {
    dispatch({ type: 'SET_CONNECTION_STATUS', payload: connectionStatus })
    onConnectionChange?.(connectionStatus)
    
    // Handle connection loss with automatic reconnection
    if (connectionStatus === 'disconnected' || connectionStatus === 'error') {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      
      // Attempt reconnection after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        if (!isConnected && !isConnecting) {
          console.log('Attempting WebSocket reconnection...')
          connect().catch(err => {
            console.error('Reconnection failed:', err)
          })
        }
      }, 5000)
    } else if (connectionStatus === 'connected') {
      // Clear reconnection timeout on successful connection
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }
  }, [connectionStatus, isConnected, isConnecting, connect, dispatch, onConnectionChange])

  // Process incoming WebSocket messages
  const processMessage = useCallback((message: any) => {
    if (!message || !message.type) return

    const update: RealtimeDataUpdate = {
      type: message.type,
      data: message.data,
      timestamp: message.timestamp || new Date().toISOString()
    }

    switch (update.type) {
      case 'space_weather_update':
        handleSpaceWeatherUpdate(update.data)
        break
        
      case 'prediction_update':
        handlePredictionUpdate(update.data)
        break
        
      case 'alert':
        handleAlertUpdate(update.data)
        break
        
      case 'system_status':
        handleSystemStatusUpdate(update.data)
        break
        
      default:
        console.log('Unknown message type:', update.type)
    }
    
    lastUpdateRef.current = new Date()
  }, [dispatch, onDataUpdate, onAlert])

  // Handle space weather data updates
  const handleSpaceWeatherUpdate = useCallback((data: SpaceWeatherUpdate) => {
    // Update current space weather data
    if (data.current_data) {
      dispatch({ type: 'SET_CURRENT_DATA', payload: data.current_data })
    }
    
    // Update predictions
    if (data.predictions) {
      dispatch({ type: 'SET_PREDICTIONS', payload: data.predictions })
    }
    
    // Handle new alerts
    if (data.alerts && data.alerts.length > 0) {
      data.alerts.forEach(alert => {
        const formattedAlert = {
          id: alert.id,
          type: alert.type as 'flash' | 'forecast' | 'warning',
          severity: alert.severity,
          title: alert.title,
          message: alert.description,
          timestamp: new Date().toISOString(),
          expiresAt: alert.expires_at || new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours default
          sectors: alert.affected_sectors
        }
        
        dispatch({ type: 'ADD_ALERT', payload: formattedAlert })
        onAlert?.(formattedAlert)
      })
    }
    
    onDataUpdate?.(data)
  }, [dispatch, onDataUpdate, onAlert])

  // Handle prediction-only updates
  const handlePredictionUpdate = useCallback((data: SectorPredictions) => {
    dispatch({ type: 'SET_PREDICTIONS', payload: data })
  }, [dispatch])

  // Handle alert updates
  const handleAlertUpdate = useCallback((alertData: any) => {
    const formattedAlert = {
      id: alertData.id || Date.now().toString(),
      type: alertData.type as 'flash' | 'forecast' | 'warning',
      severity: alertData.severity,
      title: alertData.title,
      message: alertData.description || alertData.message,
      timestamp: alertData.timestamp || new Date().toISOString(),
      expiresAt: alertData.expires_at || new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      sectors: alertData.affected_sectors || []
    }
    
    dispatch({ type: 'ADD_ALERT', payload: formattedAlert })
    onAlert?.(formattedAlert)
  }, [dispatch, onAlert])

  // Handle system status updates
  const handleSystemStatusUpdate = useCallback((statusData: any) => {
    console.log('System status update:', statusData)
    // Could dispatch system status updates to context if needed
  }, [])

  // Process messages when they arrive
  useEffect(() => {
    if (lastMessage) {
      processMessage(lastMessage)
    }
  }, [lastMessage, processMessage])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  // Manual connection control
  const handleConnect = useCallback(async () => {
    try {
      await connect()
    } catch (err) {
      console.error('Manual connection failed:', err)
    }
  }, [connect])

  const handleDisconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    disconnect()
  }, [disconnect])

  return {
    // Connection state
    isConnected,
    isConnecting,
    connectionStatus,
    error,
    lastUpdate: lastUpdateRef.current,
    
    // Connection control
    connect: handleConnect,
    disconnect: handleDisconnect,
    
    // Data state from context
    currentData: state.currentData,
    predictions: state.predictions,
    alerts: state.alerts,
  }
}