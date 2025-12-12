'use client'

import { useState, useEffect, useRef } from 'react'
import Card from './ui/Card'
import { useRealtimeData } from '@/hooks/useRealtimeData'
import ConnectionStatus from './ui/ConnectionStatus'

interface Alert {
  id: string
  type: 'flash' | 'forecast'
  severity: 'low' | 'moderate' | 'high' | 'critical'
  title: string
  description: string
  timestamp: Date
  expiresAt?: Date
  confidence?: number
  affectedSectors: string[]
  countdownTarget?: Date
  mitigation?: string[]
}

interface AlertsPanelComponentProps {
  alerts?: Alert[]
  className?: string
  onAlertDismiss?: (alertId: string) => void
  enableAudio?: boolean
}

// Sample alerts for demonstration
const defaultAlerts: Alert[] = [
  {
    id: 'flash-001',
    type: 'flash',
    severity: 'critical',
    title: 'X-Class Solar Flare Detected',
    description: 'X2.1 solar flare detected at 14:23 UTC. Immediate HF radio blackout expected.',
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    expiresAt: new Date(Date.now() + 115 * 60 * 1000), // Expires in 115 minutes (2 hours total)
    confidence: 95,
    affectedSectors: ['Aviation', 'Telecommunications', 'GPS'],
    mitigation: [
      'Switch to backup communication systems',
      'Avoid polar flight routes',
      'Monitor GPS accuracy closely'
    ]
  },
  {
    id: 'forecast-001',
    type: 'forecast',
    severity: 'high',
    title: 'CME Impact Forecast',
    description: 'High-speed CME expected to arrive in 18-24 hours. Severe geomagnetic storm likely.',
    timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
    countdownTarget: new Date(Date.now() + 20 * 60 * 60 * 1000), // 20 hours from now
    confidence: 78,
    affectedSectors: ['Power Grid', 'Satellites', 'GPS', 'Telecommunications'],
    mitigation: [
      'Prepare power grid protective measures',
      'Consider satellite orbit adjustments',
      'Alert critical infrastructure operators'
    ]
  },
  {
    id: 'forecast-002',
    type: 'forecast',
    severity: 'moderate',
    title: 'Elevated Kp-Index Expected',
    description: 'Moderate geomagnetic activity forecast for next 6 hours.',
    timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
    countdownTarget: new Date(Date.now() + 4 * 60 * 60 * 1000), // 4 hours from now
    confidence: 65,
    affectedSectors: ['GPS', 'Satellites'],
    mitigation: [
      'Monitor GPS accuracy in polar regions',
      'Track satellite drag coefficients'
    ]
  }
]

export default function AlertsPanelComponent({
  alerts = defaultAlerts,
  className = '',
  onAlertDismiss,
  enableAudio = true
}: AlertsPanelComponentProps) {
  const [currentAlerts, setCurrentAlerts] = useState<Alert[]>(alerts)
  const [alertHistory, setAlertHistory] = useState<Alert[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [audioEnabled, setAudioEnabled] = useState(enableAudio)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const lastAlertCount = useRef(alerts.length)

  // Real-time data integration
  const { 
    isConnected, 
    connectionStatus, 
    alerts: realtimeAlerts, 
    lastUpdate 
  } = useRealtimeData({
    onAlert: (alert) => {
      handleNewAlert(alert)
    }
  })

  // Handle new real-time alerts
  const handleNewAlert = (alert: any) => {
    const newAlert: Alert = {
      id: alert.id || Date.now().toString(),
      type: alert.type || 'forecast',
      severity: alert.severity || 'moderate',
      title: alert.title,
      description: alert.message || alert.description,
      timestamp: new Date(alert.timestamp || Date.now()),
      expiresAt: alert.expiresAt ? new Date(alert.expiresAt) : new Date(Date.now() + 2 * 60 * 60 * 1000),
      confidence: alert.confidence,
      affectedSectors: alert.sectors || [],
      countdownTarget: alert.countdownTarget ? new Date(alert.countdownTarget) : undefined,
      mitigation: alert.mitigation
    }
    
    setCurrentAlerts(prevAlerts => {
      // Check if alert already exists
      const exists = prevAlerts.some(existing => existing.id === newAlert.id)
      if (exists) return prevAlerts
      
      return [newAlert, ...prevAlerts]
    })
  }

  // Update alerts from real-time data
  useEffect(() => {
    if (realtimeAlerts && realtimeAlerts.length > 0) {
      const formattedAlerts = realtimeAlerts.map(alert => ({
        id: alert.id,
        type: alert.type as 'flash' | 'forecast',
        severity: alert.severity,
        title: alert.title,
        description: alert.message,
        timestamp: new Date(alert.timestamp),
        expiresAt: new Date(alert.expiresAt),
        affectedSectors: alert.sectors,
        confidence: undefined,
        countdownTarget: undefined,
        mitigation: undefined
      }))
      
      setCurrentAlerts(formattedAlerts)
    }
  }, [realtimeAlerts])

  // Sort alerts by severity and timestamp
  const sortAlerts = (alertList: Alert[]) => {
    const severityOrder = { critical: 4, high: 3, moderate: 2, low: 1 }
    return [...alertList].sort((a, b) => {
      const severityDiff = severityOrder[b.severity] - severityOrder[a.severity]
      if (severityDiff !== 0) return severityDiff
      return b.timestamp.getTime() - a.timestamp.getTime()
    })
  }

  // Play audio notification for new alerts
  useEffect(() => {
    if (audioEnabled && currentAlerts.length > lastAlertCount.current) {
      // New alert detected
      const newAlerts = currentAlerts.slice(0, currentAlerts.length - lastAlertCount.current)
      const hasCritical = newAlerts.some(alert => alert.severity === 'critical')
      
      if (hasCritical) {
        // Play critical alert sound (simulated)
        console.log('🚨 CRITICAL ALERT AUDIO NOTIFICATION')
      } else {
        // Play normal alert sound (simulated)
        console.log('🔔 Alert notification')
      }
    }
    lastAlertCount.current = currentAlerts.length
  }, [currentAlerts.length, audioEnabled])

  // Handle alert expiration
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      setCurrentAlerts(prevAlerts => {
        const activeAlerts: Alert[] = []
        const expiredAlerts: Alert[] = []

        prevAlerts.forEach(alert => {
          if (alert.expiresAt && now > alert.expiresAt) {
            expiredAlerts.push(alert)
          } else {
            activeAlerts.push(alert)
          }
        })

        // Move expired alerts to history
        if (expiredAlerts.length > 0) {
          setAlertHistory(prevHistory => [...expiredAlerts, ...prevHistory].slice(0, 20)) // Keep last 20
        }

        return activeAlerts
      })
    }, 1000) // Check every second

    return () => clearInterval(interval)
  }, [])

  // Calculate countdown time
  const getCountdownText = (target: Date): string => {
    const now = new Date()
    const diff = target.getTime() - now.getTime()
    
    if (diff <= 0) return 'Arrived'
    
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    } else {
      return `${seconds}s`
    }
  }

  // Get severity styling
  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-900/30 border-red-500/50 text-red-300'
      case 'high':
        return 'bg-orange-900/30 border-orange-500/50 text-orange-300'
      case 'moderate':
        return 'bg-yellow-900/30 border-yellow-500/50 text-yellow-300'
      case 'low':
        return 'bg-blue-900/30 border-blue-500/50 text-blue-300'
      default:
        return 'bg-gray-900/30 border-gray-500/50 text-gray-300'
    }
  }

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return '🚨'
      case 'high':
        return '⚠️'
      case 'moderate':
        return '🟡'
      case 'low':
        return 'ℹ️'
      default:
        return '📢'
    }
  }

  const sortedAlerts = sortAlerts(currentAlerts)

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h3 className="text-xl font-semibold text-astro-cyan">
            Active Alerts ({sortedAlerts.length})
          </h3>
          <ConnectionStatus 
            status={connectionStatus} 
            lastUpdate={lastUpdate}
            showText={false}
          />
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`p-2 rounded-lg transition-colors ${
              audioEnabled 
                ? 'bg-astro-blue/30 text-astro-cyan' 
                : 'bg-gray-700/30 text-gray-400'
            }`}
            title={audioEnabled ? 'Disable audio alerts' : 'Enable audio alerts'}
          >
            {audioEnabled ? '🔊' : '🔇'}
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="p-2 bg-astro-blue/30 text-astro-cyan rounded-lg hover:bg-astro-blue/50 transition-colors"
            title="Toggle alert history"
          >
            📋
          </button>
        </div>
      </div>

      {/* Active Alerts */}
      <div className="space-y-3">
        {sortedAlerts.length === 0 ? (
          <Card className="text-center py-8">
            <div className="text-4xl mb-2">✅</div>
            <p className="text-gray-400">No active alerts</p>
            <p className="text-sm text-gray-500 mt-1">All systems operating normally</p>
          </Card>
        ) : (
          sortedAlerts.map((alert) => (
            <Card
              key={alert.id}
              className={`${getSeverityStyles(alert.severity)} animate-fade-in`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="text-2xl mt-1">
                    {getSeverityIcon(alert.severity)}
                    {alert.type === 'flash' && (
                      <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse absolute -top-1 -right-1"></div>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-semibold text-white">{alert.title}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        alert.type === 'flash' 
                          ? 'bg-red-900/50 text-red-300' 
                          : 'bg-blue-900/50 text-blue-300'
                      }`}>
                        {alert.type?.toUpperCase() || 'UNKNOWN'}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-300 mb-3">{alert.description}</p>
                    
                    {/* Countdown Timer */}
                    {alert.countdownTarget && (
                      <div className="bg-astro-dark/50 rounded-lg p-3 mb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-400">Time to Impact:</span>
                          <span className="text-lg font-mono text-white">
                            {getCountdownText(alert.countdownTarget)}
                          </span>
                        </div>
                      </div>
                    )}
                    
                    {/* Confidence Level */}
                    {alert.confidence !== undefined && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-400">Confidence:</span>
                          <span className={`font-medium ${
                            alert.confidence >= 80 ? 'text-green-400' :
                            alert.confidence >= 60 ? 'text-yellow-400' :
                            'text-red-400'
                          }`}>
                            {alert.confidence}%
                          </span>
                        </div>
                        {alert.confidence < 70 && (
                          <div className="text-xs text-yellow-400 flex items-center space-x-1">
                            <span>⚠️</span>
                            <span>Low confidence - uncertainty in forecast</span>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Affected Sectors */}
                    <div className="mb-3">
                      <span className="text-xs text-gray-400">Affected Sectors:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {alert.affectedSectors.map((sector, index) => (
                          <span
                            key={`${alert.id}-sector-${index}`}
                            className="px-2 py-1 bg-astro-dark/50 text-astro-cyan text-xs rounded"
                          >
                            {sector}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {/* Mitigation Recommendations */}
                    {alert.mitigation && alert.mitigation.length > 0 && (
                      <div className="bg-astro-dark/30 rounded-lg p-3">
                        <div className="text-xs text-gray-400 mb-2">Recommended Actions:</div>
                        <ul className="text-xs text-gray-300 space-y-1">
                          {alert.mitigation.map((action, index) => (
                            <li key={index} className="flex items-start space-x-2">
                              <span className="text-astro-cyan">•</span>
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {/* Timestamp */}
                    <div className="flex items-center justify-between text-xs text-gray-500 mt-3">
                      <span>Issued: {alert.timestamp.toLocaleTimeString()}</span>
                      {alert.expiresAt && (
                        <span>Expires: {alert.expiresAt.toLocaleTimeString()}</span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Dismiss Button */}
                {onAlertDismiss && (
                  <button
                    onClick={() => onAlertDismiss(alert.id)}
                    className="text-gray-400 hover:text-white transition-colors ml-2"
                    title="Dismiss alert"
                  >
                    ×
                  </button>
                )}
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Alert History */}
      {showHistory && (
        <Card className="bg-astro-dark/50">
          <h4 className="text-lg font-semibold text-astro-cyan mb-3">
            Alert History ({alertHistory.length})
          </h4>
          {alertHistory.length === 0 ? (
            <p className="text-gray-400 text-center py-4">No recent alerts</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {alertHistory.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-2 bg-astro-blue/10 rounded border-l-4 border-gray-500"
                >
                  <div>
                    <div className="text-sm text-white">{alert.title}</div>
                    <div className="text-xs text-gray-400">
                      {alert.timestamp.toLocaleString()}
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 px-2 py-1 bg-gray-700/50 rounded">
                    EXPIRED
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}