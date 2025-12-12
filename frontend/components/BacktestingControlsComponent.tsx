'use client'

import { useState, useEffect, useRef } from 'react'
import Card from './ui/Card'

interface BacktestEvent {
  timestamp: Date
  eventType: 'flare' | 'cme' | 'storm' | 'measurement'
  description: string
  predicted?: {
    aviation: number
    telecom: number
    gps: number
    powerGrid: number
    satellites: number
  }
  actual?: {
    aviation: number
    telecom: number
    gps: number
    powerGrid: number
    satellites: number
  }
}

interface AccuracyMetrics {
  overall: number
  bySection: {
    aviation: number
    telecom: number
    gps: number
    powerGrid: number
    satellites: number
  }
  meanAbsoluteError: number
  rootMeanSquareError: number
}

interface BacktestingControlsComponentProps {
  events?: BacktestEvent[]
  className?: string
  onModeChange?: (mode: 'live' | 'backtest') => void
  onPlaybackStateChange?: (state: 'playing' | 'paused' | 'stopped') => void
  onSpeedChange?: (speed: number) => void
}

// Sample May 2024 geomagnetic storm events
const may2024Events: BacktestEvent[] = [
  {
    timestamp: new Date('2024-05-10T16:00:00Z'),
    eventType: 'flare',
    description: 'X5.8 solar flare detected from AR3664',
    predicted: { aviation: 85, telecom: 60, gps: 45, powerGrid: 30, satellites: 55 },
    actual: { aviation: 90, telecom: 65, gps: 50, powerGrid: 35, satellites: 60 }
  },
  {
    timestamp: new Date('2024-05-10T18:30:00Z'),
    eventType: 'cme',
    description: 'Fast CME launched, speed ~1800 km/s',
    predicted: { aviation: 70, telecom: 80, gps: 85, powerGrid: 90, satellites: 75 },
    actual: { aviation: 75, telecom: 85, gps: 90, powerGrid: 95, satellites: 80 }
  },
  {
    timestamp: new Date('2024-05-11T02:15:00Z'),
    eventType: 'storm',
    description: 'Geomagnetic storm onset, Kp=8',
    predicted: { aviation: 95, telecom: 85, gps: 90, powerGrid: 95, satellites: 85 },
    actual: { aviation: 92, telecom: 88, gps: 95, powerGrid: 98, satellites: 90 }
  },
  {
    timestamp: new Date('2024-05-11T06:45:00Z'),
    eventType: 'measurement',
    description: 'Peak storm intensity, Dst=-412 nT',
    predicted: { aviation: 98, telecom: 90, gps: 95, powerGrid: 98, satellites: 92 },
    actual: { aviation: 95, telecom: 92, gps: 98, powerGrid: 100, satellites: 95 }
  },
  {
    timestamp: new Date('2024-05-11T14:20:00Z'),
    eventType: 'storm',
    description: 'Storm recovery phase begins',
    predicted: { aviation: 60, telecom: 55, gps: 65, powerGrid: 70, satellites: 60 },
    actual: { aviation: 65, telecom: 60, gps: 70, powerGrid: 75, satellites: 65 }
  },
  {
    timestamp: new Date('2024-05-12T08:00:00Z'),
    eventType: 'measurement',
    description: 'Return to quiet conditions',
    predicted: { aviation: 20, telecom: 15, gps: 25, powerGrid: 30, satellites: 25 },
    actual: { aviation: 25, telecom: 20, gps: 30, powerGrid: 35, satellites: 30 }
  }
]

export default function BacktestingControlsComponent({
  events = may2024Events,
  className = '',
  onModeChange,
  onPlaybackStateChange,
  onSpeedChange
}: BacktestingControlsComponentProps) {
  const [mode, setMode] = useState<'live' | 'backtest'>('live')
  const [playbackState, setPlaybackState] = useState<'playing' | 'paused' | 'stopped'>('stopped')
  const [currentEventIndex, setCurrentEventIndex] = useState(0)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [showAccuracy, setShowAccuracy] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Calculate accuracy metrics
  const calculateAccuracyMetrics = (): AccuracyMetrics => {
    const completedEvents = events.slice(0, currentEventIndex + 1).filter(e => e.predicted && e.actual)
    
    if (completedEvents.length === 0) {
      return {
        overall: 0,
        bySection: { aviation: 0, telecom: 0, gps: 0, powerGrid: 0, satellites: 0 },
        meanAbsoluteError: 0,
        rootMeanSquareError: 0
      }
    }

    const sectors = ['aviation', 'telecom', 'gps', 'powerGrid', 'satellites'] as const
    const sectorAccuracies: Record<string, number> = {}
    let totalError = 0
    let totalSquaredError = 0
    let totalPredictions = 0

    sectors.forEach(sector => {
      let sectorError = 0
      let sectorCount = 0

      completedEvents.forEach(event => {
        if (event.predicted && event.actual) {
          const predicted = event.predicted[sector]
          const actual = event.actual[sector]
          const error = Math.abs(predicted - actual)
          
          sectorError += error
          totalError += error
          totalSquaredError += error * error
          sectorCount++
          totalPredictions++
        }
      })

      sectorAccuracies[sector] = sectorCount > 0 ? 100 - (sectorError / sectorCount) : 0
    })

    const meanAbsoluteError = totalPredictions > 0 ? totalError / totalPredictions : 0
    const rootMeanSquareError = totalPredictions > 0 ? Math.sqrt(totalSquaredError / totalPredictions) : 0
    const overall = Object.values(sectorAccuracies).reduce((sum, acc) => sum + acc, 0) / sectors.length

    return {
      overall,
      bySection: sectorAccuracies as AccuracyMetrics['bySection'],
      meanAbsoluteError,
      rootMeanSquareError
    }
  }

  // Handle mode switching
  const handleModeSwitch = (newMode: 'live' | 'backtest') => {
    if (newMode === 'live') {
      setPlaybackState('stopped')
      setCurrentEventIndex(0)
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
    setMode(newMode)
    onModeChange?.(newMode)
  }

  // Handle playback controls
  const handlePlay = () => {
    if (currentEventIndex >= events.length - 1) {
      setCurrentEventIndex(0)
    }
    setPlaybackState('playing')
    onPlaybackStateChange?.('playing')
  }

  const handlePause = () => {
    setPlaybackState('paused')
    onPlaybackStateChange?.('paused')
  }

  const handleStop = () => {
    setPlaybackState('stopped')
    setCurrentEventIndex(0)
    onPlaybackStateChange?.('stopped')
  }

  const handleSpeedChange = (newSpeed: number) => {
    setPlaybackSpeed(newSpeed)
    onSpeedChange?.(newSpeed)
  }

  // Playback logic
  useEffect(() => {
    if (mode === 'backtest' && playbackState === 'playing') {
      const baseInterval = 2000 // 2 seconds base interval
      const interval = baseInterval / playbackSpeed

      intervalRef.current = setInterval(() => {
        setCurrentEventIndex(prevIndex => {
          if (prevIndex >= events.length - 1) {
            setPlaybackState('stopped')
            onPlaybackStateChange?.('stopped')
            return prevIndex
          }
          return prevIndex + 1
        })
      }, interval)

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [mode, playbackState, playbackSpeed, events.length, onPlaybackStateChange])

  const currentEvent = events[currentEventIndex]
  const accuracyMetrics = calculateAccuracyMetrics()
  const progress = events.length > 0 ? ((currentEventIndex + 1) / events.length) * 100 : 0

  // Get event type styling
  const getEventTypeStyles = (eventType: string) => {
    switch (eventType) {
      case 'flare':
        return 'bg-red-900/30 text-red-300 border-red-500/50'
      case 'cme':
        return 'bg-orange-900/30 text-orange-300 border-orange-500/50'
      case 'storm':
        return 'bg-purple-900/30 text-purple-300 border-purple-500/50'
      case 'measurement':
        return 'bg-blue-900/30 text-blue-300 border-blue-500/50'
      default:
        return 'bg-gray-900/30 text-gray-300 border-gray-500/50'
    }
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Mode Switcher */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-astro-cyan">System Mode</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleModeSwitch('live')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                mode === 'live'
                  ? 'bg-green-600 text-white'
                  : 'bg-astro-blue/30 text-gray-300 hover:bg-astro-blue/50'
              }`}
            >
              🔴 Live Mode
            </button>
            <button
              onClick={() => handleModeSwitch('backtest')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                mode === 'backtest'
                  ? 'bg-astro-cyan text-astro-dark'
                  : 'bg-astro-blue/30 text-gray-300 hover:bg-astro-blue/50'
              }`}
            >
              📊 Backtest Mode
            </button>
          </div>
        </div>

        {mode === 'live' && (
          <div className="text-center py-4">
            <div className="text-green-400 text-lg font-medium mb-2">Live Data Mode Active</div>
            <p className="text-gray-400 text-sm">Displaying real-time space weather data and predictions</p>
          </div>
        )}
      </Card>

      {/* Backtesting Controls */}
      {mode === 'backtest' && (
        <>
          {/* Playback Controls */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-white">May 2024 Geomagnetic Storm Replay</h4>
              <div className="text-sm text-gray-400">
                Event {currentEventIndex + 1} of {events.length}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-400 mb-1">
                <span>Progress</span>
                <span>{progress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-astro-dark/50 rounded-full h-2">
                <div
                  className="bg-astro-cyan h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Control Buttons */}
            <div className="flex items-center justify-center space-x-4 mb-4">
              <button
                onClick={handlePlay}
                disabled={playbackState === 'playing'}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                ▶️ Play
              </button>
              <button
                onClick={handlePause}
                disabled={playbackState !== 'playing'}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                ⏸️ Pause
              </button>
              <button
                onClick={handleStop}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                ⏹️ Stop
              </button>
            </div>

            {/* Speed Control */}
            <div className="flex items-center justify-center space-x-4">
              <span className="text-sm text-gray-400">Speed:</span>
              {[0.5, 1, 2, 4].map(speed => (
                <button
                  key={speed}
                  onClick={() => handleSpeedChange(speed)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    playbackSpeed === speed
                      ? 'bg-astro-cyan text-astro-dark'
                      : 'bg-astro-blue/30 text-gray-300 hover:bg-astro-blue/50'
                  }`}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </Card>

          {/* Current Event Display */}
          {currentEvent && (
            <Card className={`${getEventTypeStyles(currentEvent.eventType)} animate-fade-in`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-lg font-semibold text-white">
                    {currentEvent.eventType.toUpperCase()} Event
                  </h4>
                  <p className="text-sm text-gray-300">{currentEvent.timestamp.toLocaleString()}</p>
                </div>
                <span className="px-2 py-1 bg-astro-dark/50 text-astro-cyan text-xs rounded">
                  {currentEventIndex + 1}/{events.length}
                </span>
              </div>

              <p className="text-white mb-4">{currentEvent.description}</p>

              {/* Predictions vs Actual Comparison */}
              {currentEvent.predicted && currentEvent.actual && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="text-sm font-medium text-astro-cyan mb-2">Predicted Impact</h5>
                    <div className="space-y-1 text-sm">
                      {Object.entries(currentEvent.predicted).map(([sector, value]) => (
                        <div key={sector} className="flex justify-between">
                          <span className="text-gray-300 capitalize">{sector}:</span>
                          <span className="text-white font-mono">{value}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-sm font-medium text-astro-cyan mb-2">Actual Impact</h5>
                    <div className="space-y-1 text-sm">
                      {Object.entries(currentEvent.actual).map(([sector, value]) => (
                        <div key={sector} className="flex justify-between">
                          <span className="text-gray-300 capitalize">{sector}:</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-white font-mono">{value}%</span>
                            <span className={`text-xs ${
                              Math.abs(value - currentEvent.predicted![sector as keyof typeof currentEvent.predicted]) <= 5
                                ? 'text-green-400'
                                : Math.abs(value - currentEvent.predicted![sector as keyof typeof currentEvent.predicted]) <= 10
                                ? 'text-yellow-400'
                                : 'text-red-400'
                            }`}>
                              ({value > currentEvent.predicted![sector as keyof typeof currentEvent.predicted] ? '+' : ''}
                              {value - currentEvent.predicted![sector as keyof typeof currentEvent.predicted]})
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Accuracy Metrics */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-white">Accuracy Report</h4>
              <button
                onClick={() => setShowAccuracy(!showAccuracy)}
                className="text-astro-cyan hover:text-white transition-colors"
              >
                {showAccuracy ? '📊 Hide Details' : '📈 Show Details'}
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-astro-cyan">
                  {accuracyMetrics.overall.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-400">Overall Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">
                  {accuracyMetrics.meanAbsoluteError.toFixed(1)}
                </div>
                <div className="text-sm text-gray-400">Mean Abs Error</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">
                  {accuracyMetrics.rootMeanSquareError.toFixed(1)}
                </div>
                <div className="text-sm text-gray-400">RMS Error</div>
              </div>
            </div>

            {showAccuracy && (
              <div className="space-y-2">
                <h5 className="text-sm font-medium text-astro-cyan">Accuracy by Sector</h5>
                {Object.entries(accuracyMetrics.bySection).map(([sector, accuracy]) => (
                  <div key={sector} className="flex items-center justify-between">
                    <span className="text-gray-300 capitalize">{sector}:</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-astro-dark/50 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            accuracy >= 90 ? 'bg-green-500' :
                            accuracy >= 80 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${accuracy}%` }}
                        />
                      </div>
                      <span className="text-white font-mono text-sm w-12">
                        {accuracy.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  )
}