'use client'

import { useEffect, useRef, useState } from 'react'
import { Viewer, Entity, PolygonGraphics, Globe, Scene, Camera, CesiumComponentRef } from 'resium'
import { 
  Cartesian3, 
  Color, 
  PolygonHierarchy, 
  Material,
  Viewer as CesiumViewer,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  defined,
  Math as CesiumMath
} from 'cesium'
import { useRealtimeData } from '@/hooks/useRealtimeData'
import { useLiveDataRefresh } from '@/hooks/useLiveDataRefresh'
import ConnectionStatus from './ui/ConnectionStatus'
import { animateValue, easingFunctions } from '@/lib/animation-utils'

interface RegionData {
  id: string
  name: string
  coordinates: number[][]
  riskLevel: 'low' | 'moderate' | 'high' | 'critical'
  metrics: {
    geomagneticLatitude: number
    kpIndex: number
    impactSeverity: number
    affectedSectors: string[]
  }
}

interface HeatmapComponentProps {
  data?: RegionData[]
  onRegionSelect?: (region: RegionData | null) => void
  className?: string
}

// Sample geomagnetic latitude regions for demonstration
const defaultRegions: RegionData[] = [
  {
    id: 'arctic',
    name: 'Arctic Region',
    coordinates: [
      [-180, 70], [-90, 70], [0, 70], [90, 70], [180, 70],
      [180, 85], [-180, 85]
    ],
    riskLevel: 'high',
    metrics: {
      geomagneticLatitude: 75,
      kpIndex: 7.2,
      impactSeverity: 8.5,
      affectedSectors: ['Aviation', 'GPS', 'Telecommunications']
    }
  },
  {
    id: 'northern_mid',
    name: 'Northern Mid-Latitudes',
    coordinates: [
      [-180, 45], [-90, 45], [0, 45], [90, 45], [180, 45],
      [180, 70], [-180, 70]
    ],
    riskLevel: 'moderate',
    metrics: {
      geomagneticLatitude: 55,
      kpIndex: 4.8,
      impactSeverity: 5.2,
      affectedSectors: ['Power Grid', 'Satellites']
    }
  },
  {
    id: 'equatorial',
    name: 'Equatorial Region',
    coordinates: [
      [-180, -30], [-90, -30], [0, -30], [90, -30], [180, -30],
      [180, 30], [-180, 30]
    ],
    riskLevel: 'low',
    metrics: {
      geomagneticLatitude: 15,
      kpIndex: 2.1,
      impactSeverity: 1.8,
      affectedSectors: ['Satellites']
    }
  },
  {
    id: 'southern_mid',
    name: 'Southern Mid-Latitudes',
    coordinates: [
      [-180, -70], [-90, -70], [0, -70], [90, -70], [180, -70],
      [180, -45], [-180, -45]
    ],
    riskLevel: 'moderate',
    metrics: {
      geomagneticLatitude: -55,
      kpIndex: 4.5,
      impactSeverity: 4.9,
      affectedSectors: ['GPS', 'Telecommunications']
    }
  },
  {
    id: 'antarctic',
    name: 'Antarctic Region',
    coordinates: [
      [-180, -85], [-90, -85], [0, -85], [90, -85], [180, -85],
      [180, -70], [-180, -70]
    ],
    riskLevel: 'critical',
    metrics: {
      geomagneticLatitude: -75,
      kpIndex: 8.1,
      impactSeverity: 9.2,
      affectedSectors: ['Aviation', 'GPS', 'Power Grid', 'Satellites']
    }
  }
]

export default function HeatmapComponent({ 
  data = defaultRegions, 
  onRegionSelect,
  className = '' 
}: HeatmapComponentProps) {
  const viewerRef = useRef<CesiumViewer | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<RegionData | null>(null)
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date())
  const [regionData, setRegionData] = useState<RegionData[]>(data)
  const [isUpdating, setIsUpdating] = useState(false)

  // Real-time data integration
  const { 
    isConnected, 
    connectionStatus, 
    currentData, 
    predictions, 
    lastUpdate 
  } = useRealtimeData({
    onDataUpdate: (update) => {
      // Queue the update instead of applying immediately
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
    animationDuration: 2000, // 2 seconds as per requirements (Requirement 9.5)
    updateQueueDelay: 1000,
    onUpdateStart: () => {
      setIsUpdating(true)
    },
    onUpdateComplete: () => {
      setIsUpdating(false)
    }
  })

  // Color mapping for risk levels
  const getRiskColor = (riskLevel: string): Color => {
    switch (riskLevel) {
      case 'low':
        return Color.fromCssColorString('#22c55e').withAlpha(0.6) // Green
      case 'moderate':
        return Color.fromCssColorString('#eab308').withAlpha(0.6) // Yellow
      case 'high':
        return Color.fromCssColorString('#f97316').withAlpha(0.6) // Orange
      case 'critical':
        return Color.fromCssColorString('#ef4444').withAlpha(0.6) // Red
      default:
        return Color.fromCssColorString('#6b7280').withAlpha(0.6) // Gray
    }
  }

  // Handle region selection
  const handleRegionClick = (region: RegionData) => {
    setSelectedRegion(region)
    onRegionSelect?.(region)
  }

  // Set up click handler for region selection
  useEffect(() => {
    if (!viewerRef.current) return

    const handler = new ScreenSpaceEventHandler(viewerRef.current.scene.canvas)
    
    handler.setInputAction((event: any) => {
      const pickedObject = viewerRef.current?.scene.pick(event.position)
      
      if (defined(pickedObject) && defined(pickedObject.id)) {
        const entityId = pickedObject.id.id
        const region = regionData.find(r => r.id === entityId)
        if (region) {
          handleRegionClick(region)
        }
      } else {
        setSelectedRegion(null)
        onRegionSelect?.(null)
      }
    }, ScreenSpaceEventType.LEFT_CLICK)

    return () => {
      handler.destroy()
    }
  }, [regionData, onRegionSelect])

  // Handle real-time data updates with smooth animations
  const handleRealtimeUpdate = (update: any) => {
    setLastUpdateTime(new Date())
    
    // Update region data based on real-time predictions
    if (update.predictions) {
      const updatedRegions = regionData.map(region => {
        const newRegion = { ...region }
        
        // Update risk levels based on composite score and sector predictions
        const compositeScore = update.composite_score || 0
        
        // Adjust risk levels based on geomagnetic latitude and current conditions
        if (Math.abs(region.metrics.geomagneticLatitude) > 60) {
          // Polar regions - more sensitive to space weather
          newRegion.riskLevel = compositeScore > 70 ? 'critical' :
                               compositeScore > 50 ? 'high' :
                               compositeScore > 30 ? 'moderate' : 'low'
        } else if (Math.abs(region.metrics.geomagneticLatitude) > 30) {
          // Mid-latitudes
          newRegion.riskLevel = compositeScore > 80 ? 'critical' :
                               compositeScore > 60 ? 'high' :
                               compositeScore > 40 ? 'moderate' : 'low'
        } else {
          // Equatorial regions - less affected
          newRegion.riskLevel = compositeScore > 90 ? 'critical' :
                               compositeScore > 75 ? 'high' :
                               compositeScore > 50 ? 'moderate' : 'low'
        }
        
        // Animate metric changes smoothly
        if (currentData) {
          const oldKpIndex = newRegion.metrics.kpIndex
          const newKpIndex = currentData.kp_index
          const oldImpactSeverity = newRegion.metrics.impactSeverity
          const newImpactSeverity = Math.min(10, compositeScore / 10)
          
          // Animate Kp index change
          if (oldKpIndex !== newKpIndex) {
            animateValue(
              oldKpIndex,
              newKpIndex,
              1000, // 1 second animation
              easingFunctions.easeOutQuad,
              (value) => {
                newRegion.metrics.kpIndex = value
              }
            )
          } else {
            newRegion.metrics.kpIndex = newKpIndex
          }
          
          // Animate impact severity change
          if (oldImpactSeverity !== newImpactSeverity) {
            animateValue(
              oldImpactSeverity,
              newImpactSeverity,
              1000, // 1 second animation
              easingFunctions.easeOutQuad,
              (value) => {
                newRegion.metrics.impactSeverity = value
              }
            )
          } else {
            newRegion.metrics.impactSeverity = newImpactSeverity
          }
        }
        
        return newRegion
      })
      
      // Apply updates smoothly without jarring transitions
      setRegionData(updatedRegions)
    }
  }

  // Process queued updates
  useEffect(() => {
    const queueStatus = getQueueStatus()
    if (queueStatus.nextUpdate && !isUserInteracting && !isRefreshing) {
      handleRealtimeUpdate(queueStatus.nextUpdate.data)
    }
  }, [getQueueStatus, isUserInteracting, isRefreshing])

  // Update region data when data prop changes
  useEffect(() => {
    setRegionData(data)
  }, [data])

  // Update region data when real-time data changes
  useEffect(() => {
    if (currentData || predictions) {
      // Queue update instead of immediate processing
      queueUpdate({ 
        predictions, 
        composite_score: predictions?.composite_score || 0 
      }, 'normal')
    }
  }, [currentData, predictions, queueUpdate])

  // Configure viewer settings
  const handleViewerReady = (ref: CesiumComponentRef<CesiumViewer> | null) => {
    if (ref?.cesiumElement) {
      const viewer = ref.cesiumElement
      viewerRef.current = viewer
    
      // Set initial camera position
      viewer.camera.setView({
        destination: Cartesian3.fromDegrees(0, 30, 15000000),
        orientation: {
          heading: 0,
          pitch: CesiumMath.toRadians(-45),
          roll: 0
        }
      })

      // Configure globe appearance
      viewer.scene.globe.enableLighting = true
      viewer.scene.globe.atmosphereHueShift = 0.1
      viewer.scene.globe.atmosphereSaturationShift = 0.1
    }
  }

  return (
    <div className={`relative ${className}`}>
      {/* Cesium Viewer */}
      <div className="h-full w-full rounded-lg overflow-hidden">
        <Viewer
          full
          ref={handleViewerReady}
          timeline={false}
          animation={false}
          homeButton={false}
          sceneModePicker={false}
          baseLayerPicker={false}
          navigationHelpButton={false}
          geocoder={false}
          fullscreenButton={false}
          vrButton={false}
          infoBox={false}
          selectionIndicator={false}
        >
          <Globe enableLighting />
          <Scene />
          <Camera />
          
          {/* Render regions as polygons */}
          {regionData.map((region) => (
            <Entity
              key={region.id}
              id={region.id}
              name={region.name}
            >
              <PolygonGraphics
                hierarchy={new PolygonHierarchy(
                  region.coordinates.map(coord => 
                    Cartesian3.fromDegrees(coord[0], coord[1])
                  )
                )}
                material={getRiskColor(region.riskLevel)}
                outline={true}
                outlineColor={Color.WHITE.withAlpha(0.8)}
                height={0}
                extrudedHeight={region.metrics.impactSeverity * 100000}
              />
            </Entity>
          ))}
        </Viewer>
      </div>

      {/* Region Details Panel */}
      {selectedRegion && (
        <div className="absolute top-4 right-4 bg-astro-blue/90 backdrop-blur-sm rounded-lg border border-astro-cyan/30 p-4 max-w-xs animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-lg font-semibold text-astro-cyan">{selectedRegion.name}</h4>
            <button
              onClick={() => {
                setSelectedRegion(null)
                onRegionSelect?.(null)
              }}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ×
            </button>
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-300">Risk Level:</span>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                selectedRegion.riskLevel === 'low' ? 'bg-green-900/50 text-green-300' :
                selectedRegion.riskLevel === 'moderate' ? 'bg-yellow-900/50 text-yellow-300' :
                selectedRegion.riskLevel === 'high' ? 'bg-orange-900/50 text-orange-300' :
                'bg-red-900/50 text-red-300'
              }`}>
                {selectedRegion.riskLevel.toUpperCase()}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-300">Geomagnetic Lat:</span>
              <span className="text-white font-mono">{selectedRegion.metrics.geomagneticLatitude}°</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-300">Kp-Index:</span>
              <span className="text-white font-mono">{selectedRegion.metrics.kpIndex}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-300">Impact Severity:</span>
              <span className="text-white font-mono">{selectedRegion.metrics.impactSeverity}/10</span>
            </div>
            
            <div className="mt-3">
              <span className="text-gray-300 text-xs">Affected Sectors:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {selectedRegion.metrics.affectedSectors.map((sector) => (
                  <span
                    key={sector}
                    className="px-2 py-1 bg-astro-dark/50 text-astro-cyan text-xs rounded"
                  >
                    {sector}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Connection Status and Update Indicator */}
      <div className="absolute bottom-4 left-4 bg-astro-blue/90 backdrop-blur-sm rounded-lg border border-astro-cyan/30 px-3 py-2">
        <div className="space-y-2">
          <ConnectionStatus 
            status={connectionStatus} 
            lastUpdate={lastUpdate}
            showText={true}
          />
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              isRefreshing ? 'bg-yellow-400 animate-pulse' : 
              isUserInteracting ? 'bg-blue-400 animate-bounce' :
              isConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
            }`}></div>
            <span className="text-xs text-gray-300">
              Last updated: {lastUpdateTime.toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="absolute top-4 left-4 bg-astro-blue/90 backdrop-blur-sm rounded-lg border border-astro-cyan/30 p-3">
        <div className="text-xs text-gray-300 mb-2">Controls:</div>
        <div className="text-xs text-gray-400 space-y-1">
          <div>• Left click: Select region</div>
          <div>• Mouse wheel: Zoom</div>
          <div>• Left drag: Rotate</div>
          <div>• Right drag: Pan</div>
        </div>
      </div>
    </div>
  )
}