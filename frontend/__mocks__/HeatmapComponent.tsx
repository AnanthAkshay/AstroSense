// Mock HeatmapComponent for testing
import React from 'react'

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

const MockHeatmapComponent: React.FC<HeatmapComponentProps> = ({ 
  className = '', 
  onRegionSelect 
}) => {
  return (
    <div 
      className={`mock-heatmap bg-gray-800 rounded-lg flex items-center justify-center ${className}`}
      data-testid="heatmap-component"
      onClick={() => {
        // Simulate region selection
        const mockRegion: RegionData = {
          id: 'test-region',
          name: 'Test Region',
          coordinates: [[0, 0], [1, 1]],
          riskLevel: 'moderate',
          metrics: {
            geomagneticLatitude: 45,
            kpIndex: 3.5,
            impactSeverity: 5.0,
            affectedSectors: ['GPS', 'Aviation']
          }
        }
        onRegionSelect?.(mockRegion)
      }}
    >
      <div className="text-center">
        <div className="text-2xl mb-2">🌍</div>
        <p className="text-gray-400">Mock 3D Earth Globe</p>
        <p className="text-xs text-gray-500 mt-1">Click to select region</p>
      </div>
    </div>
  )
}

export default MockHeatmapComponent