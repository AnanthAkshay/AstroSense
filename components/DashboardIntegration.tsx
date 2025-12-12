'use client'

import { useEffect, useState } from 'react'
import { useRealtimeData } from '@/hooks/useRealtimeData'
import { useLiveDataRefresh } from '@/hooks/useLiveDataRefresh'
import { useAppContext } from '@/contexts/AppContext'
import HeatmapComponent from './HeatmapComponent'
import ChartsComponent from './ChartsComponent'
import RiskCardsComponent from './RiskCardsComponent'
import AlertsPanelComponent from './AlertsPanelComponent'
import ConnectionStatus from './ui/ConnectionStatus'

interface DashboardIntegrationProps {
  className?: string
}

export default function DashboardIntegration({ className = '' }: DashboardIntegrationProps) {
  const { state, dispatch } = useAppContext()
  const [globalUpdateCount, setGlobalUpdateCount] = useState(0)
  const [lastGlobalUpdate, setLastGlobalUpdate] = useState<Date>(new Date())

  // Global real-time data management
  const { 
    isConnected, 
    connectionStatus, 
    currentData, 
    predictions, 
    alerts,
    lastUpdate,
    connect,
    disconnect
  } = useRealtimeData({
    autoConnect: true,
    onDataUpdate: (update) => {
      handleGlobalDataUpdate(update)
    },
    onAlert: (alert) => {
      handleGlobalAlert(alert)
    },
    onConnectionChange: (status) => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: status as any })
    }
  })

  // Global live data refresh coordination
  const {
    isUpdating: isGloballyUpdating,
    isUserInteracting: isGlobalUserInteracting,
    queueUpdate: queueGlobalUpdate,
    getQueueStatus: getGlobalQueueStatus
  } = useLiveDataRefresh({
    animationDuration: 500,
    updateQueueDelay: 1500,
    maxQueueSize: 20,
    onUpdateStart: () => {
      setGlobalUpdateCount(prev => prev + 1)
    },
    onUpdateComplete: () => {
      setLastGlobalUpdate(new Date())
    }
  })

  // Handle global data updates
  const handleGlobalDataUpdate = (update: any) => {
    // Update app context
    if (update.current_data) {
      dispatch({ type: 'SET_CURRENT_DATA', payload: update.current_data })
    }
    
    if (update.predictions) {
      dispatch({ type: 'SET_PREDICTIONS', payload: update.predictions })
    }
    
    // Queue global update for coordinated component updates
    queueGlobalUpdate(update, 'normal')
  }

  // Handle global alerts
  const handleGlobalAlert = (alert: any) => {
    const formattedAlert = {
      id: alert.id || Date.now().toString(),
      type: alert.type || 'warning' as 'flash' | 'forecast' | 'warning',
      severity: alert.severity || 'moderate',
      title: alert.title,
      message: alert.message || alert.description,
      timestamp: alert.timestamp || new Date().toISOString(),
      expiresAt: alert.expiresAt || new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
      sectors: alert.sectors || []
    }
    
    dispatch({ type: 'ADD_ALERT', payload: formattedAlert })
  }

  // Handle threshold crossings from charts
  const handleThresholdCrossing = (type: 'solar_wind' | 'bz_field', value: number, threshold: number) => {
    const alertId = `threshold-${type}-${Date.now()}`
    const alert = {
      id: alertId,
      type: 'warning' as 'flash' | 'forecast' | 'warning',
      severity: 'high' as 'low' | 'moderate' | 'high' | 'critical',
      title: `${type === 'solar_wind' ? 'Solar Wind' : 'Bz Field'} Threshold Exceeded`,
      message: `${type === 'solar_wind' ? 'Solar wind speed' : 'Bz magnetic field'} has crossed critical threshold: ${value.toFixed(1)} ${type === 'solar_wind' ? 'km/s' : 'nT'}`,
      timestamp: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30 minutes
      sectors: type === 'solar_wind' ? ['Aviation', 'Satellites'] : ['GPS', 'Power Grid']
    }
    
    dispatch({ type: 'ADD_ALERT', payload: alert })
  }

  // Handle region selection from heatmap
  const handleRegionSelect = (region: any) => {
    if (region) {
      // Could dispatch region selection to context for other components to use
      console.log('Region selected:', region.name)
    }
  }

  // Handle alert dismissal
  const handleAlertDismiss = (alertId: string) => {
    dispatch({ type: 'REMOVE_ALERT', payload: alertId })
  }

  // Handle risk changes from cards
  const handleRiskChange = (sectorId: string, newRisk: any) => {
    // Could dispatch risk changes to context for global state management
    console.log('Risk changed for sector:', sectorId, newRisk)
  }

  // Connection management
  const handleReconnect = () => {
    connect()
  }

  const handleDisconnect = () => {
    disconnect()
  }

  // Auto-clear expired alerts
  useEffect(() => {
    const interval = setInterval(() => {
      dispatch({ type: 'CLEAR_EXPIRED_ALERTS' })
    }, 60000) // Every minute

    return () => clearInterval(interval)
  }, [dispatch])

  // Global update coordination
  useEffect(() => {
    const queueStatus = getGlobalQueueStatus()
    if (queueStatus.size > 0 && !isGlobalUserInteracting) {
      // Coordinate updates across all components
      console.log(`Processing ${queueStatus.size} queued updates`)
    }
  }, [getGlobalQueueStatus, isGlobalUserInteracting])

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Global Connection Status */}
      <div className="flex items-center justify-between bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-astro-cyan">AstroSense Dashboard</h2>
          <ConnectionStatus 
            status={connectionStatus} 
            lastUpdate={lastUpdate}
            showText={true}
          />
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-400">
            Updates: {globalUpdateCount}
          </div>
          
          {!isConnected && (
            <button
              onClick={handleReconnect}
              className="px-3 py-1 bg-astro-cyan/20 text-astro-cyan rounded hover:bg-astro-cyan/30 transition-colors text-sm"
            >
              Reconnect
            </button>
          )}
          
          {isConnected && (
            <button
              onClick={handleDisconnect}
              className="px-3 py-1 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-colors text-sm"
            >
              Disconnect
            </button>
          )}
        </div>
      </div>

      {/* Global Update Indicator */}
      {isGloballyUpdating && (
        <div className="fixed top-4 right-4 z-50 bg-astro-blue/90 backdrop-blur-sm rounded-lg border border-astro-cyan/30 px-4 py-2">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-white">Updating dashboard...</span>
          </div>
        </div>
      )}

      {/* User Interaction Indicator */}
      {isGlobalUserInteracting && (
        <div className="fixed top-16 right-4 z-50 bg-blue-500/90 backdrop-blur-sm rounded-lg border border-blue-400/30 px-4 py-2">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce"></div>
            <span className="text-sm text-white">Updates paused during interaction</span>
          </div>
        </div>
      )}

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Heatmap */}
        <div className="lg:col-span-2">
          <div className="bg-astro-blue/5 rounded-lg border border-astro-cyan/10 p-4">
            <h3 className="text-lg font-semibold text-astro-cyan mb-4">Global Risk Heatmap</h3>
            <div className="h-96">
              <HeatmapComponent
                onRegionSelect={handleRegionSelect}
                className="h-full"
              />
            </div>
          </div>
        </div>

        {/* Right Column - Risk Cards and Alerts */}
        <div className="space-y-6">
          <div className="bg-astro-blue/5 rounded-lg border border-astro-cyan/10 p-4">
            <h3 className="text-lg font-semibold text-astro-cyan mb-4">Sector Risk Assessment</h3>
            <RiskCardsComponent
              onRiskChange={handleRiskChange}
            />
          </div>

          <div className="bg-astro-blue/5 rounded-lg border border-astro-cyan/10 p-4">
            <AlertsPanelComponent
              alerts={state.alerts.map(alert => ({
                ...alert,
                description: alert.message,
                affectedSectors: alert.sectors
              }))}
              onAlertDismiss={handleAlertDismiss}
              enableAudio={true}
            />
          </div>
        </div>
      </div>

      {/* Bottom Row - Charts */}
      <div className="bg-astro-blue/5 rounded-lg border border-astro-cyan/10 p-4">
        <h3 className="text-lg font-semibold text-astro-cyan mb-4">Real-time Space Weather Data</h3>
        <ChartsComponent
          onThresholdCrossing={handleThresholdCrossing}
        />
      </div>

      {/* Debug Information (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="bg-gray-900/50 rounded-lg border border-gray-700 p-4 text-xs text-gray-400">
          <h4 className="text-sm font-semibold mb-2">Debug Information</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div>Connection: {connectionStatus}</div>
              <div>Global Updates: {globalUpdateCount}</div>
              <div>User Interacting: {isGlobalUserInteracting ? 'Yes' : 'No'}</div>
              <div>Queue Size: {getGlobalQueueStatus().size}</div>
            </div>
            <div>
              <div>Current Data: {currentData ? 'Available' : 'None'}</div>
              <div>Predictions: {predictions ? 'Available' : 'None'}</div>
              <div>Active Alerts: {state.alerts.length}</div>
              <div>Last Update: {lastGlobalUpdate.toLocaleTimeString()}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}