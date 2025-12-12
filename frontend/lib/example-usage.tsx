/**
 * Example Usage of API Client for Backend Communication
 * 
 * This file demonstrates how to use the implemented API client
 * and WebSocket client in React components.
 */

'use client'

import React, { useEffect, useState } from 'react'
import { useCurrentData, usePredictions } from '@/hooks/useApiData'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useAppContext } from '@/contexts/AppContext'

// Example component showing how to fetch current space weather data
export function CurrentDataExample() {
  const { data, loading, error, refetch } = useCurrentData(30000) // Refresh every 30 seconds

  if (loading) return <div>Loading current space weather data...</div>
  if (error) return <div>Error: {error}</div>
  if (!data) return <div>No data available</div>

  return (
    <div className="space-weather-data">
      <h3>Current Space Weather</h3>
      <div>Solar Wind Speed: {data.solar_wind_speed} km/s</div>
      <div>Bz Field: {data.bz_field} nT</div>
      <div>Kp Index: {data.kp_index}</div>
      <div>Proton Flux: {data.proton_flux}</div>
      <div>Last Updated: {data.timestamp}</div>
      <button onClick={refetch}>Refresh Data</button>
    </div>
  )
}

// Example component showing how to get predictions
export function PredictionsExample() {
  const [inputData, setInputData] = useState({
    solar_wind_speed: 400,
    bz_field: -5,
    kp_index: 3
  })

  const { data: predictions, loading, error } = usePredictions(inputData)

  const handleInputChange = (field: string, value: number) => {
    setInputData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="predictions-example">
      <h3>Impact Predictions</h3>
      
      {/* Input Controls */}
      <div className="input-controls">
        <label>
          Solar Wind Speed (km/s):
          <input
            type="number"
            value={inputData.solar_wind_speed}
            onChange={(e) => handleInputChange('solar_wind_speed', Number(e.target.value))}
          />
        </label>
        <label>
          Bz Field (nT):
          <input
            type="number"
            value={inputData.bz_field}
            onChange={(e) => handleInputChange('bz_field', Number(e.target.value))}
          />
        </label>
        <label>
          Kp Index:
          <input
            type="number"
            value={inputData.kp_index}
            onChange={(e) => handleInputChange('kp_index', Number(e.target.value))}
          />
        </label>
      </div>

      {/* Predictions Display */}
      {loading && <div>Calculating predictions...</div>}
      {error && <div>Error: {error}</div>}
      {predictions && (
        <div className="predictions-results">
          <div>Aviation HF Blackout: {predictions.aviation_hf_blackout_prob}%</div>
          <div>Aviation Polar Risk: {predictions.aviation_polar_risk}</div>
          <div>Telecom Degradation: {predictions.telecom_signal_degradation}%</div>
          <div>GPS Drift: {predictions.gps_drift_cm} cm</div>
          <div>Power Grid GIC Risk: {predictions.power_grid_gic_risk}/10</div>
          <div>Satellite Drag Risk: {predictions.satellite_drag_risk}/10</div>
          <div>Composite Score: {predictions.composite_score}/100</div>
        </div>
      )}
    </div>
  )
}

// Example component showing WebSocket real-time updates
export function RealTimeUpdatesExample() {
  const { isConnected, connectionStatus, lastMessage, connect, disconnect } = useWebSocket()
  const [messages, setMessages] = useState<any[]>([])

  useEffect(() => {
    if (lastMessage) {
      setMessages(prev => [lastMessage, ...prev.slice(0, 9)]) // Keep last 10 messages
    }
  }, [lastMessage])

  return (
    <div className="realtime-updates">
      <h3>Real-time Updates</h3>
      
      <div className="connection-status">
        Status: <span className={isConnected ? 'connected' : 'disconnected'}>
          {connectionStatus}
        </span>
        <button onClick={isConnected ? disconnect : connect}>
          {isConnected ? 'Disconnect' : 'Connect'}
        </button>
      </div>

      <div className="message-log">
        <h4>Recent Messages:</h4>
        {messages.length === 0 ? (
          <div>No messages received yet</div>
        ) : (
          <ul>
            {messages.map((msg, index) => (
              <li key={index}>
                <strong>{msg.type}</strong>: {JSON.stringify(msg.data)} 
                <small>({msg.timestamp})</small>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

// Example component using the App Context for state management
export function StateManagementExample() {
  const { state, dispatch } = useAppContext()

  const addAlert = () => {
    const alert = {
      id: Date.now().toString(),
      type: 'flash' as const,
      severity: 'high' as const,
      title: 'X-Class Solar Flare Detected',
      message: 'High-energy solar flare detected. Radio blackouts expected.',
      timestamp: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours
      sectors: ['aviation', 'telecom']
    }
    dispatch({ type: 'ADD_ALERT', payload: alert })
  }

  const toggleBacktest = () => {
    dispatch({ type: 'TOGGLE_BACKTEST_MODE', payload: '2024-05-10' })
  }

  return (
    <div className="state-management-example">
      <h3>State Management</h3>
      
      <div className="current-state">
        <div>Connection Status: {state.connectionStatus}</div>
        <div>Backtest Mode: {state.isBacktestMode ? 'ON' : 'OFF'}</div>
        <div>Active Alerts: {state.alerts.length}</div>
        <div>Theme: {state.theme}</div>
      </div>

      <div className="actions">
        <button onClick={addAlert}>Add Test Alert</button>
        <button onClick={toggleBacktest}>Toggle Backtest Mode</button>
        <button onClick={() => dispatch({ type: 'SET_THEME', payload: state.theme === 'dark' ? 'light' : 'dark' })}>
          Toggle Theme
        </button>
      </div>

      {state.alerts.length > 0 && (
        <div className="alerts-list">
          <h4>Active Alerts:</h4>
          {state.alerts.map(alert => (
            <div key={alert.id} className={`alert alert-${alert.severity}`}>
              <strong>{alert.title}</strong>
              <p>{alert.message}</p>
              <small>Expires: {alert.expiresAt}</small>
              <button onClick={() => dispatch({ type: 'REMOVE_ALERT', payload: alert.id })}>
                Dismiss
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Complete example showing all features together
export function CompleteAPIExample() {
  return (
    <div className="complete-api-example">
      <h2>AstroSense API Client Examples</h2>
      
      <div className="examples-grid">
        <CurrentDataExample />
        <PredictionsExample />
        <RealTimeUpdatesExample />
        <StateManagementExample />
      </div>
    </div>
  )
}