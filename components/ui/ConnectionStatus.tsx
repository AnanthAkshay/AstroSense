'use client'

import { useEffect, useState } from 'react'

interface ConnectionStatusProps {
  status: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastUpdate?: Date
  className?: string
  showText?: boolean
}

export default function ConnectionStatus({ 
  status, 
  lastUpdate, 
  className = '', 
  showText = true 
}: ConnectionStatusProps) {
  const [timeSinceUpdate, setTimeSinceUpdate] = useState<string>('')

  // Update time since last update
  useEffect(() => {
    if (!lastUpdate) return

    const updateTimer = () => {
      const now = new Date()
      const diff = now.getTime() - lastUpdate.getTime()
      const seconds = Math.floor(diff / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)

      if (hours > 0) {
        setTimeSinceUpdate(`${hours}h ${minutes % 60}m ago`)
      } else if (minutes > 0) {
        setTimeSinceUpdate(`${minutes}m ${seconds % 60}s ago`)
      } else {
        setTimeSinceUpdate(`${seconds}s ago`)
      }
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)
    return () => clearInterval(interval)
  }, [lastUpdate])

  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-400',
          text: 'Connected',
          icon: '🟢',
          animate: 'animate-pulse'
        }
      case 'connecting':
        return {
          color: 'bg-yellow-400',
          text: 'Connecting...',
          icon: '🟡',
          animate: 'animate-bounce'
        }
      case 'disconnected':
        return {
          color: 'bg-gray-400',
          text: 'Disconnected',
          icon: '⚪',
          animate: ''
        }
      case 'error':
        return {
          color: 'bg-red-400',
          text: 'Connection Error',
          icon: '🔴',
          animate: 'animate-pulse'
        }
      default:
        return {
          color: 'bg-gray-400',
          text: 'Unknown',
          icon: '⚪',
          animate: ''
        }
    }
  }

  const config = getStatusConfig()

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`w-2 h-2 rounded-full ${config.color} ${config.animate}`}></div>
      {showText && (
        <div className="text-sm">
          <span className="text-gray-300">{config.text}</span>
          {lastUpdate && status === 'connected' && (
            <span className="text-gray-500 ml-2">
              • Updated {timeSinceUpdate}
            </span>
          )}
        </div>
      )}
    </div>
  )
}