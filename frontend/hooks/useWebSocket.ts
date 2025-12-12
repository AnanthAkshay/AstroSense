'use client'

import { useEffect, useState, useCallback } from 'react'
import { wsClient, WebSocketMessage, WebSocketEventHandler } from '@/lib/websocket-client'

export interface UseWebSocketReturn {
  isConnected: boolean
  isConnecting: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastMessage: WebSocketMessage | null
  error: string | null
  connect: () => Promise<void>
  disconnect: () => void
  sendMessage: (message: any) => boolean
}

export function useWebSocket(autoConnect: boolean = true): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Handle connection status changes
  const handleConnectionChange = useCallback((message: WebSocketMessage) => {
    const { status, error: connectionError } = message.data
    
    setConnectionStatus(status)
    setIsConnected(status === 'connected')
    setIsConnecting(status === 'connecting')
    
    if (connectionError) {
      setError(connectionError.message || 'Connection error')
    } else if (status === 'connected') {
      setError(null)
    }
  }, [])

  // Handle incoming messages
  const handleMessage = useCallback((message: WebSocketMessage) => {
    setLastMessage(message)
  }, [])

  // Connect function
  const connect = useCallback(async () => {
    try {
      setIsConnecting(true)
      setError(null)
      await wsClient.connect()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
      setIsConnecting(false)
    }
  }, [])

  // Disconnect function
  const disconnect = useCallback(() => {
    wsClient.disconnect()
    setIsConnected(false)
    setIsConnecting(false)
    setConnectionStatus('disconnected')
  }, [])

  // Send message function
  const sendMessage = useCallback((message: any) => {
    return wsClient.send(message)
  }, [])

  useEffect(() => {
    // Set up event listeners
    wsClient.on('connection', handleConnectionChange)
    wsClient.on('message', handleMessage)

    // Auto-connect if requested
    if (autoConnect) {
      connect()
    }

    // Cleanup on unmount
    return () => {
      wsClient.off('connection', handleConnectionChange)
      wsClient.off('message', handleMessage)
      if (!autoConnect) {
        disconnect()
      }
    }
  }, [autoConnect, connect, disconnect, handleConnectionChange, handleMessage])

  return {
    isConnected,
    isConnecting,
    connectionStatus,
    lastMessage,
    error,
    connect,
    disconnect,
    sendMessage,
  }
}