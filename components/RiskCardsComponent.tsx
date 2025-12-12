'use client'

import { useState, useEffect } from 'react'
import Card from './ui/Card'
import StatusIndicator from './ui/StatusIndicator'
import { useRealtimeData } from '@/hooks/useRealtimeData'
import { useLiveDataRefresh } from '@/hooks/useLiveDataRefresh'
import ConnectionStatus from './ui/ConnectionStatus'
import { animateValue, easingFunctions, createScaleEffect } from '@/lib/animation-utils'

interface SectorRisk {
  id: string
  name: string
  icon: string
  primaryMetric: {
    label: string
    value: number
    unit: string
    threshold: number
    status: 'low' | 'moderate' | 'high' | 'critical'
  }
  secondaryMetric?: {
    label: string
    value: number | string
    unit?: string
  }
  geographicInfo?: {
    label: string
    regions: string[]
    mostAffected?: string
  }
  historicalComparison?: {
    trend: 'increasing' | 'decreasing' | 'stable'
    previousValue: number
    changePercent: number
  }
  altitudeInfo?: {
    altitude: number
    impactLevel: string
  }
  description: string
  lastUpdated: Date
}

interface RiskCardsComponentProps {
  risks?: SectorRisk[]
  className?: string
  onRiskChange?: (sectorId: string, newRisk: SectorRisk) => void
}

// Default risk data for demonstration - matches backend sector predictor outputs
const defaultRisks: SectorRisk[] = [
  {
    id: 'aviation',
    name: 'Aviation',
    icon: '✈️',
    primaryMetric: {
      label: 'HF Blackout Probability',
      value: 15,
      unit: '%',
      threshold: 70,
      status: 'low'
    },
    secondaryMetric: {
      label: 'Polar Route Risk',
      value: 25,
      unit: '%'
    },
    description: 'High frequency radio communications and polar route safety',
    lastUpdated: new Date()
  },
  {
    id: 'telecom',
    name: 'Telecommunications',
    icon: '📡',
    primaryMetric: {
      label: 'Signal Degradation',
      value: 35,
      unit: '%',
      threshold: 30,
      status: 'moderate'
    },
    secondaryMetric: {
      label: 'Impact Duration',
      value: '4-6',
      unit: 'hours'
    },
    historicalComparison: {
      trend: 'increasing',
      previousValue: 28,
      changePercent: 25
    },
    description: 'Satellite communications and terrestrial signal quality',
    lastUpdated: new Date()
  },
  {
    id: 'gps',
    name: 'GPS Systems',
    icon: '🛰️',
    primaryMetric: {
      label: 'Positional Drift',
      value: 45,
      unit: 'cm',
      threshold: 50,
      status: 'low'
    },
    secondaryMetric: {
      label: 'Accuracy Warning',
      value: 'None',
      unit: ''
    },
    geographicInfo: {
      label: 'Geographic Distribution',
      regions: ['Polar Regions', 'High Latitudes', 'Mid Latitudes', 'Low Latitudes'],
      mostAffected: 'Polar Regions (67.5 cm)'
    },
    description: 'Global positioning accuracy and ionospheric interference',
    lastUpdated: new Date()
  },
  {
    id: 'power_grid',
    name: 'Power Grid',
    icon: '⚡',
    primaryMetric: {
      label: 'GIC Risk Level',
      value: 8,
      unit: '/10',
      threshold: 7,
      status: 'high'
    },
    secondaryMetric: {
      label: 'Warning Window',
      value: '6',
      unit: 'hours'
    },
    geographicInfo: {
      label: 'Affected Regions',
      regions: ['Northern Grid', 'Eastern Grid', 'Western Grid'],
      mostAffected: 'Northern Grid (High Conductivity)'
    },
    description: 'Geomagnetically induced currents and transformer protection',
    lastUpdated: new Date()
  },
  {
    id: 'satellites',
    name: 'Satellites',
    icon: '🛸',
    primaryMetric: {
      label: 'Orbital Drag Risk',
      value: 6,
      unit: '/10',
      threshold: 6,
      status: 'moderate'
    },
    secondaryMetric: {
      label: 'Advance Notice',
      value: '24',
      unit: 'hours'
    },
    altitudeInfo: {
      altitude: 400,
      impactLevel: 'High (LEO)'
    },
    description: 'Atmospheric drag and orbital decay risk assessment',
    lastUpdated: new Date()
  }
]

export default function RiskCardsComponent({
  risks = defaultRisks,
  className = '',
  onRiskChange
}: RiskCardsComponentProps) {
  const [currentRisks, setCurrentRisks] = useState<SectorRisk[]>(risks)
  const [animatingCards, setAnimatingCards] = useState<Set<string>>(new Set())

  // Real-time data integration
  const { 
    isConnected, 
    connectionStatus, 
    predictions, 
    lastUpdate 
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
    animationDuration: 300, // Smooth card animations
    updateQueueDelay: 1000,
    onUpdateStart: () => {
      // Cards will handle their own animation states
    },
    onUpdateComplete: () => {
      // Animation complete
    }
  })

  // Convert backend sector predictions to SectorRisk format
  const convertBackendData = (sectorPredictions: any): SectorRisk[] => {
    const convertedRisks: SectorRisk[] = []

    // Aviation sector
    if (sectorPredictions.aviation) {
      const aviation = sectorPredictions.aviation
      convertedRisks.push({
        id: 'aviation',
        name: 'Aviation',
        icon: '✈️',
        primaryMetric: {
          label: 'HF Blackout Probability',
          value: aviation.hf_blackout_probability || 0,
          unit: '%',
          threshold: 70,
          status: getStatusFromValue(aviation.hf_blackout_probability || 0, 70, 'aviation')
        },
        secondaryMetric: {
          label: 'Polar Route Risk',
          value: aviation.polar_route_risk || 0,
          unit: '%'
        },
        description: 'High frequency radio communications and polar route safety',
        lastUpdated: new Date()
      })
    }

    // Telecom sector
    if (sectorPredictions.telecom) {
      const telecom = sectorPredictions.telecom
      convertedRisks.push({
        id: 'telecom',
        name: 'Telecommunications',
        icon: '📡',
        primaryMetric: {
          label: 'Signal Degradation',
          value: telecom.signal_degradation_percent || 0,
          unit: '%',
          threshold: 30,
          status: getStatusFromValue(telecom.signal_degradation_percent || 0, 30, 'telecom')
        },
        secondaryMetric: {
          label: 'Classification',
          value: telecom.classification || 'low',
          unit: ''
        },
        historicalComparison: {
          trend: 'stable', // Would need historical data from backend
          previousValue: telecom.signal_degradation_percent || 0,
          changePercent: 0
        },
        description: 'Satellite communications and terrestrial signal quality',
        lastUpdated: new Date()
      })
    }

    // GPS sector
    if (sectorPredictions.gps) {
      const gps = sectorPredictions.gps
      const geoDist = gps.geographic_distribution
      convertedRisks.push({
        id: 'gps',
        name: 'GPS Systems',
        icon: '🛰️',
        primaryMetric: {
          label: 'Positional Drift',
          value: gps.positional_drift_cm || 0,
          unit: 'cm',
          threshold: 50,
          status: getStatusFromValue(gps.positional_drift_cm || 0, 50, 'gps')
        },
        secondaryMetric: {
          label: 'Classification',
          value: gps.classification || 'low',
          unit: ''
        },
        geographicInfo: geoDist ? {
          label: 'Geographic Distribution',
          regions: Object.keys(geoDist.regions || {}),
          mostAffected: `${geoDist.greatest_impact_region} (${geoDist.greatest_impact_drift?.toFixed(1)} cm)`
        } : undefined,
        description: 'Global positioning accuracy and ionospheric interference',
        lastUpdated: new Date()
      })
    }

    // Power Grid sector
    if (sectorPredictions.power_grid) {
      const powerGrid = sectorPredictions.power_grid
      convertedRisks.push({
        id: 'power_grid',
        name: 'Power Grid',
        icon: '⚡',
        primaryMetric: {
          label: 'GIC Risk Level',
          value: powerGrid.gic_risk_level || 1,
          unit: '/10',
          threshold: 7,
          status: getStatusFromValue(powerGrid.gic_risk_level || 1, 7, 'power_grid')
        },
        secondaryMetric: {
          label: 'Classification',
          value: powerGrid.classification || 'low',
          unit: ''
        },
        geographicInfo: {
          label: 'Affected Regions',
          regions: ['Northern Grid', 'Eastern Grid', 'Western Grid'],
          mostAffected: 'Northern Grid (High Conductivity)' // Would come from backend
        },
        description: 'Geomagnetically induced currents and transformer protection',
        lastUpdated: new Date()
      })
    }

    // Satellite sector
    if (sectorPredictions.satellites) {
      const satellites = sectorPredictions.satellites
      convertedRisks.push({
        id: 'satellites',
        name: 'Satellites',
        icon: '🛸',
        primaryMetric: {
          label: 'Orbital Drag Risk',
          value: satellites.orbital_drag_risk || 1,
          unit: '/10',
          threshold: 6,
          status: getStatusFromValue(satellites.orbital_drag_risk || 1, 6, 'satellites')
        },
        secondaryMetric: {
          label: 'Classification',
          value: satellites.classification || 'low',
          unit: ''
        },
        altitudeInfo: {
          altitude: satellites.altitude_km || 400,
          impactLevel: satellites.orbital_drag_risk >= 8 ? 'Critical (LEO)' :
                      satellites.orbital_drag_risk >= 6 ? 'High (LEO)' :
                      satellites.orbital_drag_risk >= 4 ? 'Moderate (LEO)' :
                      'Low (LEO)'
        },
        description: 'Atmospheric drag and orbital decay risk assessment',
        lastUpdated: new Date()
      })
    }

    return convertedRisks
  }

  // Handle real-time data updates with smooth animations
  const handleRealtimeUpdate = (update: any) => {
    if (!update.predictions) return

    const updatedRisks = convertBackendData(update.predictions)
    
    // Animate cards that have changed with smooth value transitions
    updatedRisks.forEach(newRisk => {
      const oldRisk = currentRisks.find(r => r.id === newRisk.id)
      if (oldRisk && oldRisk.primaryMetric.value !== newRisk.primaryMetric.value) {
        // Animate the value change smoothly
        const startValue = oldRisk.primaryMetric.value
        const endValue = newRisk.primaryMetric.value
        
        setAnimatingCards(prev => new Set(prev).add(newRisk.id))
        
        // Animate the numeric value transition
        animateValue(
          startValue,
          endValue,
          800, // 800ms smooth transition
          easingFunctions.easeOutCubic,
          (currentValue) => {
            setCurrentRisks(prevRisks => 
              prevRisks.map(risk => 
                risk.id === newRisk.id 
                  ? { ...risk, primaryMetric: { ...risk.primaryMetric, value: currentValue } }
                  : risk
              )
            )
          },
          () => {
            // Animation complete
            setAnimatingCards(prev => {
              const newSet = new Set(prev)
              newSet.delete(newRisk.id)
              return newSet
            })
          }
        )
      }
    })
    
    // Update risks that haven't changed
    setCurrentRisks(prevRisks => 
      prevRisks.map(oldRisk => {
        const newRisk = updatedRisks.find(r => r.id === oldRisk.id)
        if (newRisk && oldRisk.primaryMetric.value === newRisk.primaryMetric.value) {
          return newRisk // Update other properties but keep same value
        }
        return oldRisk
      })
    )
  }

  // Process queued updates
  useEffect(() => {
    const queueStatus = getQueueStatus()
    if (queueStatus.nextUpdate && !isUserInteracting && !isRefreshing) {
      handleRealtimeUpdate(queueStatus.nextUpdate.data)
    }
  }, [getQueueStatus, isUserInteracting, isRefreshing])

  // Update risks when real-time predictions change
  useEffect(() => {
    if (predictions) {
      // Queue update for smooth processing
      queueUpdate({ predictions }, 'normal')
    }
  }, [predictions, queueUpdate])

  // Simulate risk level changes for demonstration (fallback when no real-time data)
  useEffect(() => {
    if (isConnected) return // Don't simulate when connected to real data
    
    const interval = setInterval(() => {
      setCurrentRisks(prevRisks => 
        prevRisks.map(risk => {
          // Randomly update some metrics
          if (Math.random() < 0.3) { // 30% chance to update each risk
            const updatedRisk = { ...risk }
            
            // Simulate metric changes based on sector type
            const previousValue = risk.primaryMetric.value
            switch (risk.id) {
              case 'aviation':
                updatedRisk.primaryMetric = {
                  ...risk.primaryMetric,
                  value: Math.max(0, Math.min(100, risk.primaryMetric.value + (Math.random() - 0.5) * 10))
                }
                // Update polar route risk
                if (updatedRisk.secondaryMetric) {
                  updatedRisk.secondaryMetric = {
                    ...updatedRisk.secondaryMetric,
                    value: Math.max(0, Math.min(100, (updatedRisk.secondaryMetric.value as number) + (Math.random() - 0.5) * 8))
                  }
                }
                break
              case 'telecom':
                updatedRisk.primaryMetric = {
                  ...risk.primaryMetric,
                  value: Math.max(0, Math.min(100, risk.primaryMetric.value + (Math.random() - 0.5) * 15))
                }
                // Update historical comparison
                if (updatedRisk.historicalComparison) {
                  const change = updatedRisk.primaryMetric.value - previousValue
                  updatedRisk.historicalComparison = {
                    ...updatedRisk.historicalComparison,
                    previousValue: previousValue,
                    changePercent: Math.round((change / previousValue) * 100),
                    trend: change > 2 ? 'increasing' : change < -2 ? 'decreasing' : 'stable'
                  }
                }
                break
              case 'gps':
                updatedRisk.primaryMetric = {
                  ...risk.primaryMetric,
                  value: Math.max(0, Math.min(500, risk.primaryMetric.value + (Math.random() - 0.5) * 20))
                }
                // Update geographic distribution
                if (updatedRisk.geographicInfo) {
                  const baseDrift = updatedRisk.primaryMetric.value
                  const polarDrift = baseDrift * 1.5
                  updatedRisk.geographicInfo = {
                    ...updatedRisk.geographicInfo,
                    mostAffected: `Polar Regions (${polarDrift.toFixed(1)} cm)`
                  }
                }
                break
              case 'power_grid':
                updatedRisk.primaryMetric = {
                  ...risk.primaryMetric,
                  value: Math.max(1, Math.min(10, Math.round(risk.primaryMetric.value + (Math.random() - 0.5) * 2)))
                }
                // Update affected regions based on risk level
                if (updatedRisk.geographicInfo) {
                  const riskLevel = updatedRisk.primaryMetric.value
                  const mostAffected = riskLevel >= 8 ? 'Northern Grid (High Conductivity)' :
                                     riskLevel >= 6 ? 'Eastern Grid (Moderate Risk)' :
                                     'Western Grid (Low Risk)'
                  updatedRisk.geographicInfo = {
                    ...updatedRisk.geographicInfo,
                    mostAffected
                  }
                }
                break
              case 'satellites':
                updatedRisk.primaryMetric = {
                  ...risk.primaryMetric,
                  value: Math.max(1, Math.min(10, Math.round(risk.primaryMetric.value + (Math.random() - 0.5) * 2)))
                }
                // Update altitude impact
                if (updatedRisk.altitudeInfo) {
                  const riskLevel = updatedRisk.primaryMetric.value
                  const impactLevel = riskLevel >= 8 ? 'Critical (LEO)' :
                                    riskLevel >= 6 ? 'High (LEO)' :
                                    riskLevel >= 4 ? 'Moderate (LEO)' :
                                    'Low (LEO)'
                  updatedRisk.altitudeInfo = {
                    ...updatedRisk.altitudeInfo,
                    impactLevel
                  }
                }
                break
            }

            // Update status based on new value
            updatedRisk.primaryMetric.status = getStatusFromValue(
              updatedRisk.primaryMetric.value,
              updatedRisk.primaryMetric.threshold,
              risk.id
            )
            
            updatedRisk.lastUpdated = new Date()
            
            // Trigger animation
            setAnimatingCards(prev => new Set(prev).add(risk.id))
            setTimeout(() => {
              setAnimatingCards(prev => {
                const newSet = new Set(prev)
                newSet.delete(risk.id)
                return newSet
              })
            }, 300)

            onRiskChange?.(risk.id, updatedRisk)
            return updatedRisk
          }
          return risk
        })
      )
    }, 8000) // Update every 8 seconds

    return () => clearInterval(interval)
  }, [onRiskChange, isConnected])

  // Determine status based on value and threshold
  const getStatusFromValue = (value: number, threshold: number, sectorId: string): 'low' | 'moderate' | 'high' | 'critical' => {
    if (sectorId === 'gps') {
      // GPS uses different thresholds (50cm moderate, 200cm critical)
      if (value < 50) return 'low'
      if (value < 200) return 'moderate'
      return 'critical'
    } else if (sectorId === 'power_grid' || sectorId === 'satellites') {
      // Scale-based metrics (1-10)
      if (value < threshold) return 'low'
      if (value < threshold + 2) return 'moderate'
      if (value < threshold + 3) return 'high'
      return 'critical'
    } else {
      // Percentage-based metrics
      if (value < threshold * 0.5) return 'low'
      if (value < threshold) return 'moderate'
      if (value < threshold * 1.5) return 'high'
      return 'critical'
    }
  }

  // Get trend indicator
  const getTrendIcon = (risk: SectorRisk) => {
    const timeSinceUpdate = Date.now() - risk.lastUpdated.getTime()
    if (timeSinceUpdate < 10000) { // Updated in last 10 seconds
      return <span className="text-green-400 text-xs">↗️</span>
    }
    return null
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {currentRisks.map((risk) => (
        <Card
          key={risk.id}
          className={`transition-all duration-300 ${
            animatingCards.has(risk.id) ? 'scale-105 shadow-lg shadow-astro-cyan/20' : ''
          }`}
          animate={animatingCards.has(risk.id)}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-2xl">{risk.icon}</div>
              <div>
                <h4 className="text-lg font-semibold text-white">{risk.name}</h4>
                <p className="text-sm text-gray-400">{risk.description}</p>
              </div>
            </div>
            {getTrendIcon(risk)}
          </div>

          <div className="mt-4 space-y-3">
            {/* Primary Metric */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-300">{risk.primaryMetric.label}</p>
                <div className="flex items-baseline space-x-2">
                  <span className="text-2xl font-mono text-white">
                    {typeof risk.primaryMetric.value === 'number' 
                      ? risk.primaryMetric.value.toFixed(risk.id === 'gps' ? 0 : 1)
                      : risk.primaryMetric.value
                    }
                  </span>
                  <span className="text-sm text-gray-400">{risk.primaryMetric.unit}</span>
                </div>
              </div>
              <StatusIndicator
                status={risk.primaryMetric.status}
                label={risk.primaryMetric.status.toUpperCase()}
              />
            </div>

            {/* Secondary Metric */}
            {risk.secondaryMetric && (
              <div className="flex items-center justify-between pt-2 border-t border-astro-cyan/10">
                <span className="text-sm text-gray-300">{risk.secondaryMetric.label}:</span>
                <span className="text-sm text-white font-medium">
                  {risk.secondaryMetric.value} {risk.secondaryMetric.unit}
                </span>
              </div>
            )}

            {/* Historical Comparison (Requirement 5.4) */}
            {risk.historicalComparison && (
              <div className="pt-2 border-t border-astro-cyan/10">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Historical Trend:</span>
                  <div className="flex items-center space-x-2">
                    <span className={`text-sm font-medium ${
                      risk.historicalComparison.trend === 'increasing' ? 'text-red-400' :
                      risk.historicalComparison.trend === 'decreasing' ? 'text-green-400' :
                      'text-yellow-400'
                    }`}>
                      {risk.historicalComparison.trend === 'increasing' ? '↗' :
                       risk.historicalComparison.trend === 'decreasing' ? '↘' : '→'}
                      {risk.historicalComparison.changePercent > 0 ? '+' : ''}{risk.historicalComparison.changePercent}%
                    </span>
                    <span className="text-xs text-gray-400">
                      (was {risk.historicalComparison.previousValue}{risk.primaryMetric.unit})
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Geographic Information (Requirements 6.4, 7.3) */}
            {risk.geographicInfo && (
              <div className="pt-2 border-t border-astro-cyan/10">
                <div className="space-y-1">
                  <span className="text-sm text-gray-300">{risk.geographicInfo.label}:</span>
                  <div className="flex flex-wrap gap-1">
                    {risk.geographicInfo.regions.map((region, index) => (
                      <span
                        key={index}
                        className={`text-xs px-2 py-1 rounded ${
                          risk.geographicInfo?.mostAffected?.includes(region) 
                            ? 'bg-red-900/30 text-red-300 border border-red-500/30'
                            : 'bg-astro-blue/20 text-gray-300 border border-astro-cyan/20'
                        }`}
                      >
                        {region}
                      </span>
                    ))}
                  </div>
                  {risk.geographicInfo.mostAffected && (
                    <div className="text-xs text-gray-400 mt-1">
                      Most affected: {risk.geographicInfo.mostAffected}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Altitude Information (Requirement 8.3) */}
            {risk.altitudeInfo && (
              <div className="pt-2 border-t border-astro-cyan/10">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Altitude Impact:</span>
                  <div className="text-right">
                    <div className="text-sm text-white font-medium">
                      {risk.altitudeInfo.altitude} km
                    </div>
                    <div className="text-xs text-gray-400">
                      {risk.altitudeInfo.impactLevel}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Progress Bar for Threshold Visualization */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Risk Level</span>
                <span>Threshold: {risk.primaryMetric.threshold}{risk.primaryMetric.unit}</span>
              </div>
              <div className="w-full bg-astro-dark/50 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    risk.primaryMetric.status === 'low' ? 'bg-green-500' :
                    risk.primaryMetric.status === 'moderate' ? 'bg-yellow-500' :
                    risk.primaryMetric.status === 'high' ? 'bg-orange-500' :
                    'bg-red-500'
                  }`}
                  style={{
                    width: `${Math.min(100, (risk.primaryMetric.value / (risk.primaryMetric.threshold * 2)) * 100)}%`
                  }}
                />
              </div>
            </div>

            {/* Last Updated */}
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Last updated: {risk.lastUpdated.toLocaleTimeString()}</span>
              <div className="flex items-center space-x-1">
                <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
                <span>Live</span>
              </div>
            </div>
          </div>
        </Card>
      ))}

      {/* Summary Card */}
      <Card className="bg-astro-blue/20 border-astro-cyan/40">
        <div className="text-center">
          <h4 className="text-lg font-semibold text-astro-cyan mb-2">Overall Risk Assessment</h4>
          <div className="grid grid-cols-2 gap-4 text-sm mb-3">
            <div>
              <span className="text-gray-300">Active Alerts:</span>
              <span className="ml-2 text-white font-medium">
                {currentRisks.filter(r => r.primaryMetric.status === 'high' || r.primaryMetric.status === 'critical').length}
              </span>
            </div>
            <div>
              <span className="text-gray-300">Monitoring:</span>
              <span className="ml-2 text-white font-medium">{currentRisks.length} Sectors</span>
            </div>
          </div>
          <div className="flex justify-center">
            <ConnectionStatus 
              status={connectionStatus} 
              lastUpdate={lastUpdate}
              showText={true}
            />
          </div>
        </div>
      </Card>
    </div>
  )
}