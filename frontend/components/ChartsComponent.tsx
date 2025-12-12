'use client'

import { useEffect, useState, useRef } from 'react'
import Highcharts from 'highcharts'
import HighchartsReact from 'highcharts-react-official'
import { useRealtimeData } from '@/hooks/useRealtimeData'
import { useLiveDataRefresh } from '@/hooks/useLiveDataRefresh'
import ConnectionStatus from './ui/ConnectionStatus'
import { animateValue, easingFunctions } from '@/lib/animation-utils'

interface DataPoint {
  timestamp: number
  value: number
}

interface ChartsComponentProps {
  solarWindData?: DataPoint[]
  bzFieldData?: DataPoint[]
  className?: string
  onThresholdCrossing?: (type: 'solar_wind' | 'bz_field', value: number, threshold: number) => void
}

// Thresholds for critical events
const SOLAR_WIND_THRESHOLD = 500 // km/s
const BZ_FIELD_THRESHOLD = -10 // nT (negative Bz is concerning)

// Generate sample data for demonstration
const generateSampleData = (hours: number = 24, interval: number = 5): DataPoint[] => {
  const data: DataPoint[] = []
  const now = Date.now()
  const pointCount = (hours * 60) / interval // 5-minute intervals
  
  for (let i = 0; i < pointCount; i++) {
    const timestamp = now - (pointCount - i) * interval * 60 * 1000
    data.push({ timestamp, value: 0 })
  }
  
  return data
}

const generateSolarWindData = (): DataPoint[] => {
  return generateSampleData().map((point, index) => ({
    ...point,
    value: 300 + Math.sin(index * 0.1) * 100 + Math.random() * 150 + 
           (index > 200 ? Math.sin((index - 200) * 0.05) * 200 : 0) // Add some variation
  }))
}

const generateBzFieldData = (): DataPoint[] => {
  return generateSampleData().map((point, index) => ({
    ...point,
    value: Math.sin(index * 0.08) * 15 + Math.random() * 10 - 5 +
           (index > 150 && index < 200 ? -20 : 0) // Add a negative Bz event
  }))
}

export default function ChartsComponent({
  solarWindData = generateSolarWindData(),
  bzFieldData = generateBzFieldData(),
  className = '',
  onThresholdCrossing
}: ChartsComponentProps) {
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [currentSolarWindData, setCurrentSolarWindData] = useState<DataPoint[]>(solarWindData)
  const [currentBzFieldData, setCurrentBzFieldData] = useState<DataPoint[]>(bzFieldData)
  const [isUpdating, setIsUpdating] = useState(false)
  const solarWindRef = useRef<HighchartsReact.RefObject>(null)
  const bzFieldRef = useRef<HighchartsReact.RefObject>(null)

  // Real-time data integration
  const { 
    isConnected, 
    connectionStatus, 
    currentData, 
    lastUpdate: realtimeLastUpdate 
  } = useRealtimeData({
    onDataUpdate: (update) => {
      // Queue the update for smooth processing
      queueUpdate(update, 'normal')
    }
  })

  // Live data refresh system
  const {
    isUpdating: isRefreshing,
    isUserInteracting,
    queueUpdate,
    getQueueStatus
  } = useLiveDataRefresh({
    animationDuration: 300, // Smooth transitions (200-400ms as per requirements)
    updateQueueDelay: 1000,
    onUpdateStart: () => {
      setIsUpdating(true)
    },
    onUpdateComplete: () => {
      setIsUpdating(false)
    }
  })

  // Handle real-time data updates with smooth animations
  const handleRealtimeUpdate = (update: any) => {
    if (!update.current_data) return
    
    setLastUpdate(new Date())
    
    const newDataPoint = {
      timestamp: Date.now(),
      value: 0
    }
    
    // Update solar wind data with smooth animation
    if (update.current_data.solar_wind_speed !== undefined) {
      const solarWindPoint = {
        ...newDataPoint,
        value: update.current_data.solar_wind_speed
      }
      
      setCurrentSolarWindData(prevData => {
        const newData = [...prevData, solarWindPoint]
        // Keep only last 24 hours of data (288 points at 5-minute intervals)
        const trimmedData = newData.slice(-288)
        
        // Animate the new data point smoothly
        if (solarWindRef.current?.chart) {
          const chart = solarWindRef.current.chart
          const series = chart.series[0]
          
          // Add point with animation
          series.addPoint([solarWindPoint.timestamp, solarWindPoint.value], true, trimmedData.length > 288)
        }
        
        return trimmedData
      })
    }
    
    // Update Bz field data with smooth animation
    if (update.current_data.bz_field !== undefined) {
      const bzFieldPoint = {
        ...newDataPoint,
        value: update.current_data.bz_field
      }
      
      setCurrentBzFieldData(prevData => {
        const newData = [...prevData, bzFieldPoint]
        // Keep only last 24 hours of data (288 points at 5-minute intervals)
        const trimmedData = newData.slice(-288)
        
        // Animate the new data point smoothly
        if (bzFieldRef.current?.chart) {
          const chart = bzFieldRef.current.chart
          const series = chart.series[0]
          
          // Add point with animation
          series.addPoint([bzFieldPoint.timestamp, bzFieldPoint.value], true, trimmedData.length > 288)
        }
        
        return trimmedData
      })
    }
  }

  // Check for threshold crossings
  useEffect(() => {
    const latestSolarWind = currentSolarWindData[currentSolarWindData.length - 1]
    const latestBzField = currentBzFieldData[currentBzFieldData.length - 1]

    if (latestSolarWind && latestSolarWind.value > SOLAR_WIND_THRESHOLD) {
      onThresholdCrossing?.('solar_wind', latestSolarWind.value, SOLAR_WIND_THRESHOLD)
    }

    if (latestBzField && latestBzField.value < BZ_FIELD_THRESHOLD) {
      onThresholdCrossing?.('bz_field', latestBzField.value, BZ_FIELD_THRESHOLD)
    }
  }, [currentSolarWindData, currentBzFieldData, onThresholdCrossing])

  // Process queued updates
  useEffect(() => {
    const queueStatus = getQueueStatus()
    if (queueStatus.nextUpdate && !isUserInteracting && !isRefreshing) {
      handleRealtimeUpdate(queueStatus.nextUpdate.data)
    }
  }, [getQueueStatus, isUserInteracting, isRefreshing])

  // Update charts when real-time data changes
  useEffect(() => {
    if (currentData) {
      // Queue update for smooth processing
      queueUpdate({ current_data: currentData }, 'normal')
    }
  }, [currentData, queueUpdate])

  // Animate chart updates smoothly
  useEffect(() => {
    if (isRefreshing) {
      // Trigger smooth chart animations
      if (solarWindRef.current?.chart) {
        const chart = solarWindRef.current.chart
        chart.redraw(true) // Animate redraw
      }
      if (bzFieldRef.current?.chart) {
        const chart = bzFieldRef.current.chart
        chart.redraw(true) // Animate redraw
      }
    }
  }, [isRefreshing])

  // Pause updates during user interactions
  useEffect(() => {
    if (isUserInteracting) {
      // Temporarily pause chart animations during user interactions
      if (solarWindRef.current?.chart) {
        solarWindRef.current.chart.update({ chart: { animation: false } })
      }
      if (bzFieldRef.current?.chart) {
        bzFieldRef.current.chart.update({ chart: { animation: false } })
      }
    } else {
      // Resume animations when user stops interacting
      if (solarWindRef.current?.chart) {
        solarWindRef.current.chart.update({ chart: { animation: true } })
      }
      if (bzFieldRef.current?.chart) {
        bzFieldRef.current.chart.update({ chart: { animation: true } })
      }
    }
  }, [isUserInteracting])

  // Common chart configuration
  const getBaseChartConfig = () => ({
    chart: {
      type: 'line',
      backgroundColor: 'transparent',
      height: 200,
      animation: {
        duration: 300
      }
    },
    title: {
      text: undefined
    },
    credits: {
      enabled: false
    },
    legend: {
      enabled: false
    },
    xAxis: {
      type: 'datetime' as const,
      gridLineColor: '#1e3a8a',
      lineColor: '#06b6d4',
      tickColor: '#06b6d4',
      labels: {
        style: {
          color: '#9ca3af'
        }
      }
    },
    yAxis: {
      gridLineColor: '#1e3a8a',
      lineColor: '#06b6d4',
      tickColor: '#06b6d4',
      labels: {
        style: {
          color: '#9ca3af'
        }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(30, 58, 138, 0.9)',
      borderColor: '#06b6d4',
      style: {
        color: '#ffffff'
      }
    },
    plotOptions: {
      line: {
        marker: {
          enabled: false,
          states: {
            hover: {
              enabled: true,
              radius: 4
            }
          }
        },
        lineWidth: 2,
        animation: {
          duration: 200
        }
      }
    }
  })

  // Solar Wind Speed Chart Configuration
  const solarWindConfig: Highcharts.Options = {
    ...getBaseChartConfig(),
    yAxis: {
      ...getBaseChartConfig().yAxis,
      title: {
        text: 'Speed (km/s)',
        style: {
          color: '#06b6d4'
        }
      },
      plotLines: [{
        color: '#ef4444',
        width: 2,
        value: SOLAR_WIND_THRESHOLD,
        dashStyle: 'Dash',
        label: {
          text: `Critical: ${SOLAR_WIND_THRESHOLD} km/s`,
          style: {
            color: '#ef4444'
          }
        }
      }]
    },
    series: [{
      type: 'line',
      name: 'Solar Wind Speed',
      data: currentSolarWindData.map(point => [point.timestamp, point.value]),
      color: '#3b82f6',
      zones: [{
        value: SOLAR_WIND_THRESHOLD,
        color: '#3b82f6'
      }, {
        color: '#ef4444'
      }]
    }]
  }

  // Bz Magnetic Field Chart Configuration
  const bzFieldConfig: Highcharts.Options = {
    ...getBaseChartConfig(),
    yAxis: {
      ...getBaseChartConfig().yAxis,
      title: {
        text: 'Bz Field (nT)',
        style: {
          color: '#06b6d4'
        }
      },
      plotLines: [{
        color: '#ef4444',
        width: 2,
        value: BZ_FIELD_THRESHOLD,
        dashStyle: 'Dash',
        label: {
          text: `Critical: ${BZ_FIELD_THRESHOLD} nT`,
          style: {
            color: '#ef4444'
          }
        }
      }, {
        color: '#6b7280',
        width: 1,
        value: 0,
        label: {
          text: '0 nT',
          style: {
            color: '#6b7280'
          }
        }
      }]
    },
    series: [{
      type: 'line',
      name: 'Bz Magnetic Field',
      data: currentBzFieldData.map(point => [point.timestamp, point.value]),
      color: '#06b6d4',
      zones: [{
        value: BZ_FIELD_THRESHOLD,
        color: '#ef4444'
      }, {
        color: '#06b6d4'
      }]
    }]
  }

  // Get current values for display
  const currentSolarWindValue = currentSolarWindData[currentSolarWindData.length - 1]?.value || 0
  const currentBzFieldValue = currentBzFieldData[currentBzFieldData.length - 1]?.value || 0

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Solar Wind Speed Chart */}
      <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-astro-cyan">Solar Wind Speed</h3>
            <p className="text-sm text-gray-400">24-hour trend with 5-minute resolution</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-mono text-white">
              {currentSolarWindValue.toFixed(1)} <span className="text-sm text-gray-400">km/s</span>
            </div>
            <div className={`text-sm font-medium ${
              currentSolarWindValue > SOLAR_WIND_THRESHOLD ? 'text-red-400' : 'text-green-400'
            }`}>
              {currentSolarWindValue > SOLAR_WIND_THRESHOLD ? 'CRITICAL' : 'NORMAL'}
            </div>
          </div>
        </div>
        
        <div className="h-48">
          <HighchartsReact
            ref={solarWindRef}
            highcharts={Highcharts}
            options={solarWindConfig}
          />
        </div>
      </div>

      {/* Bz Magnetic Field Chart */}
      <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-astro-cyan">Bz Magnetic Field</h3>
            <p className="text-sm text-gray-400">Interplanetary magnetic field north-south component</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-mono text-white">
              {currentBzFieldValue > 0 ? '+' : ''}{currentBzFieldValue.toFixed(1)} <span className="text-sm text-gray-400">nT</span>
            </div>
            <div className={`text-sm font-medium ${
              currentBzFieldValue < BZ_FIELD_THRESHOLD ? 'text-red-400' : 'text-green-400'
            }`}>
              {currentBzFieldValue < BZ_FIELD_THRESHOLD ? 'CRITICAL' : 'NORMAL'}
            </div>
          </div>
        </div>
        
        <div className="h-48">
          <HighchartsReact
            ref={bzFieldRef}
            highcharts={Highcharts}
            options={bzFieldConfig}
          />
        </div>
      </div>

      {/* Chart Status */}
      <div className="flex items-center justify-between text-sm text-gray-400">
        <div className="flex items-center space-x-4">
          <ConnectionStatus 
            status={connectionStatus} 
            lastUpdate={realtimeLastUpdate}
            showText={false}
          />
          <span className={isConnected ? 'text-green-400' : 'text-gray-400'}>
            {isConnected ? 'Live Data' : 'Offline'}
          </span>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-0.5 bg-red-400"></div>
            <span>Critical Thresholds</span>
          </div>
        </div>
        <div>
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}