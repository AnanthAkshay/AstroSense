'use client'

import { useState, useEffect } from 'react'
import Card from './ui/Card'
import StatusIndicator from './ui/StatusIndicator'

interface ImpactPrediction {
  id: string
  sector: string
  impactType: string
  severity: 'low' | 'moderate' | 'high' | 'critical'
  value: string
  timeWindow: {
    start: Date
    end: Date
    description: string
  }
  geographicDistribution: {
    regions: string[]
    primaryRegion: string
    coverage: 'local' | 'regional' | 'global'
  }
  confidence: number
  mitigation: string[]
  lastUpdated: Date
}

interface ImpactTableComponentProps {
  predictions?: ImpactPrediction[]
  className?: string
  onPredictionSelect?: (prediction: ImpactPrediction) => void
}

// Sample impact predictions for demonstration
const defaultPredictions: ImpactPrediction[] = [
  {
    id: 'aviation-001',
    sector: 'Aviation',
    impactType: 'HF Radio Blackout',
    severity: 'low',
    value: '15% probability',
    timeWindow: {
      start: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
      end: new Date(Date.now() + 8 * 60 * 60 * 1000), // 8 hours from now
      description: 'Next 6 hours'
    },
    geographicDistribution: {
      regions: ['North America', 'Northern Europe'],
      primaryRegion: 'Arctic',
      coverage: 'regional'
    },
    confidence: 85,
    mitigation: [
      'Use backup VHF communications',
      'Avoid polar routes above 70°N',
      'Monitor SWPC alerts continuously'
    ],
    lastUpdated: new Date()
  },
  {
    id: 'aviation-002',
    sector: 'Aviation',
    impactType: 'Polar Route Risk',
    severity: 'moderate',
    value: 'Elevated risk',
    timeWindow: {
      start: new Date(Date.now() + 12 * 60 * 60 * 1000), // 12 hours from now
      end: new Date(Date.now() + 36 * 60 * 60 * 1000), // 36 hours from now
      description: '12-36 hours'
    },
    geographicDistribution: {
      regions: ['Arctic Ocean', 'Northern Canada', 'Northern Siberia'],
      primaryRegion: 'Arctic',
      coverage: 'regional'
    },
    confidence: 72,
    mitigation: [
      'Reroute flights below 65°N latitude',
      'Increase fuel reserves for alternate routes',
      'Brief crews on radiation exposure protocols'
    ],
    lastUpdated: new Date()
  },
  {
    id: 'telecom-001',
    sector: 'Telecommunications',
    impactType: 'Signal Degradation',
    severity: 'moderate',
    value: '35% degradation',
    timeWindow: {
      start: new Date(Date.now() + 6 * 60 * 60 * 1000), // 6 hours from now
      end: new Date(Date.now() + 18 * 60 * 60 * 1000), // 18 hours from now
      description: '6-18 hours'
    },
    geographicDistribution: {
      regions: ['Northern Europe', 'Scandinavia', 'Northern Russia'],
      primaryRegion: 'Northern Europe',
      coverage: 'regional'
    },
    confidence: 68,
    mitigation: [
      'Activate backup satellite links',
      'Increase error correction protocols',
      'Notify customers of potential service impacts'
    ],
    lastUpdated: new Date()
  },
  {
    id: 'gps-001',
    sector: 'GPS Systems',
    impactType: 'Positional Drift',
    severity: 'low',
    value: '45 cm drift',
    timeWindow: {
      start: new Date(Date.now() + 4 * 60 * 60 * 1000), // 4 hours from now
      end: new Date(Date.now() + 12 * 60 * 60 * 1000), // 12 hours from now
      description: '4-12 hours'
    },
    geographicDistribution: {
      regions: ['Global'],
      primaryRegion: 'Equatorial',
      coverage: 'global'
    },
    confidence: 91,
    mitigation: [
      'Use WAAS/EGNOS augmentation systems',
      'Increase position update frequency',
      'Cross-reference with inertial navigation'
    ],
    lastUpdated: new Date()
  },
  {
    id: 'power-001',
    sector: 'Power Grid',
    impactType: 'GIC Risk',
    severity: 'high',
    value: 'Level 8/10',
    timeWindow: {
      start: new Date(Date.now() + 14 * 60 * 60 * 1000), // 14 hours from now
      end: new Date(Date.now() + 26 * 60 * 60 * 1000), // 26 hours from now
      description: '14-26 hours'
    },
    geographicDistribution: {
      regions: ['Northern US', 'Southern Canada', 'Northern Europe'],
      primaryRegion: 'Northern US',
      coverage: 'regional'
    },
    confidence: 76,
    mitigation: [
      'Prepare transformer protection systems',
      'Reduce grid loading where possible',
      'Monitor GIC levels continuously',
      'Have repair crews on standby'
    ],
    lastUpdated: new Date()
  },
  {
    id: 'satellite-001',
    sector: 'Satellites',
    impactType: 'Orbital Drag',
    severity: 'moderate',
    value: 'Level 6/10',
    timeWindow: {
      start: new Date(Date.now() + 8 * 60 * 60 * 1000), // 8 hours from now
      end: new Date(Date.now() + 32 * 60 * 60 * 1000), // 32 hours from now
      description: '8-32 hours'
    },
    geographicDistribution: {
      regions: ['LEO Orbits (200-800 km)'],
      primaryRegion: 'Global LEO',
      coverage: 'global'
    },
    confidence: 83,
    mitigation: [
      'Plan orbit adjustment maneuvers',
      'Monitor atmospheric density models',
      'Prioritize critical mission satellites',
      'Prepare collision avoidance protocols'
    ],
    lastUpdated: new Date()
  }
]

export default function ImpactTableComponent({
  predictions = defaultPredictions,
  className = '',
  onPredictionSelect
}: ImpactTableComponentProps) {
  const [currentPredictions, setCurrentPredictions] = useState<ImpactPrediction[]>(predictions)
  const [selectedPrediction, setSelectedPrediction] = useState<ImpactPrediction | null>(null)
  const [sortBy, setSortBy] = useState<'sector' | 'severity' | 'timeWindow'>('severity')
  const [filterSector, setFilterSector] = useState<string>('all')

  // Get unique sectors for filtering
  const sectors = ['all', ...Array.from(new Set(currentPredictions.map(p => p.sector)))]

  // Sort predictions
  const sortedPredictions = [...currentPredictions].sort((a, b) => {
    switch (sortBy) {
      case 'sector':
        return a.sector.localeCompare(b.sector)
      case 'severity':
        const severityOrder = { critical: 4, high: 3, moderate: 2, low: 1 }
        return severityOrder[b.severity] - severityOrder[a.severity]
      case 'timeWindow':
        return a.timeWindow.start.getTime() - b.timeWindow.start.getTime()
      default:
        return 0
    }
  })

  // Filter predictions
  const filteredPredictions = sortedPredictions.filter(p => 
    filterSector === 'all' || p.sector === filterSector
  )

  // Handle row selection
  const handleRowClick = (prediction: ImpactPrediction) => {
    setSelectedPrediction(prediction)
    onPredictionSelect?.(prediction)
  }

  // Get severity styling
  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-400 bg-red-900/20'
      case 'high':
        return 'text-orange-400 bg-orange-900/20'
      case 'moderate':
        return 'text-yellow-400 bg-yellow-900/20'
      case 'low':
        return 'text-green-400 bg-green-900/20'
      default:
        return 'text-gray-400 bg-gray-900/20'
    }
  }

  // Get coverage icon
  const getCoverageIcon = (coverage: string) => {
    switch (coverage) {
      case 'global':
        return '🌍'
      case 'regional':
        return '🗺️'
      case 'local':
        return '📍'
      default:
        return '❓'
    }
  }

  // Format time window
  const formatTimeWindow = (timeWindow: { start: Date; end: Date; description: string }) => {
    const now = new Date()
    const hoursToStart = Math.round((timeWindow.start.getTime() - now.getTime()) / (1000 * 60 * 60))
    
    if (hoursToStart <= 0) {
      return 'Active now'
    } else if (hoursToStart < 24) {
      return `In ${hoursToStart}h`
    } else {
      const days = Math.round(hoursToStart / 24)
      return `In ${days}d`
    }
  }

  // Simulate prediction updates
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentPredictions(prevPredictions =>
        prevPredictions.map(prediction => ({
          ...prediction,
          lastUpdated: new Date()
        }))
      )
    }, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <h3 className="text-xl font-semibold text-astro-cyan">
          Impact Predictions ({filteredPredictions.length})
        </h3>
        
        <div className="flex items-center space-x-4">
          {/* Sector Filter */}
          <select
            value={filterSector}
            onChange={(e) => setFilterSector(e.target.value)}
            className="bg-astro-blue/20 border border-astro-cyan/30 rounded-lg px-3 py-1 text-sm text-white"
          >
            {sectors.map(sector => (
              <option key={sector} value={sector} className="bg-astro-dark">
                {sector === 'all' ? 'All Sectors' : sector}
              </option>
            ))}
          </select>
          
          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'sector' | 'severity' | 'timeWindow')}
            className="bg-astro-blue/20 border border-astro-cyan/30 rounded-lg px-3 py-1 text-sm text-white"
          >
            <option value="severity" className="bg-astro-dark">Sort by Severity</option>
            <option value="sector" className="bg-astro-dark">Sort by Sector</option>
            <option value="timeWindow" className="bg-astro-dark">Sort by Time</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-astro-cyan/20">
                <th className="text-left py-3 px-4 text-gray-300 font-medium">Sector</th>
                <th className="text-left py-3 px-4 text-gray-300 font-medium hidden sm:table-cell">Impact Type</th>
                <th className="text-left py-3 px-4 text-gray-300 font-medium">Severity</th>
                <th className="text-left py-3 px-4 text-gray-300 font-medium hidden md:table-cell">Time Window</th>
                <th className="text-left py-3 px-4 text-gray-300 font-medium hidden lg:table-cell">Geographic</th>
                <th className="text-left py-3 px-4 text-gray-300 font-medium hidden xl:table-cell">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {filteredPredictions.map((prediction) => (
                <tr
                  key={prediction.id}
                  onClick={() => handleRowClick(prediction)}
                  className={`border-b border-astro-cyan/10 hover:bg-astro-blue/10 cursor-pointer transition-colors ${
                    selectedPrediction?.id === prediction.id ? 'bg-astro-blue/20' : ''
                  }`}
                >
                  <td className="py-3 px-4">
                    <div className="font-medium text-white">{prediction.sector}</div>
                    <div className="text-xs text-gray-400 sm:hidden">{prediction.impactType}</div>
                  </td>
                  <td className="py-3 px-4 text-gray-300 hidden sm:table-cell">
                    {prediction.impactType}
                  </td>
                  <td className="py-3 px-4">
                    <StatusIndicator
                      status={prediction.severity}
                      label={prediction.value}
                    />
                  </td>
                  <td className="py-3 px-4 text-gray-300 hidden md:table-cell">
                    <div>{formatTimeWindow(prediction.timeWindow)}</div>
                    <div className="text-xs text-gray-400">{prediction.timeWindow.description}</div>
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell">
                    <div className="flex items-center space-x-2">
                      <span>{getCoverageIcon(prediction.geographicDistribution.coverage)}</span>
                      <div>
                        <div className="text-gray-300">{prediction.geographicDistribution.primaryRegion}</div>
                        <div className="text-xs text-gray-400 capitalize">{prediction.geographicDistribution.coverage}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 hidden xl:table-cell">
                    <div className={`text-sm font-medium ${
                      prediction.confidence >= 80 ? 'text-green-400' :
                      prediction.confidence >= 60 ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {prediction.confidence}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Selected Prediction Details */}
      {selectedPrediction && (
        <Card className="bg-astro-blue/20 border-astro-cyan/40 animate-fade-in">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h4 className="text-lg font-semibold text-white">
                {selectedPrediction.sector} - {selectedPrediction.impactType}
              </h4>
              <p className="text-sm text-gray-400">
                Last updated: {selectedPrediction.lastUpdated.toLocaleTimeString()}
              </p>
            </div>
            <button
              onClick={() => setSelectedPrediction(null)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Impact Details */}
            <div className="space-y-4">
              <div>
                <h5 className="text-sm font-medium text-astro-cyan mb-2">Impact Details</h5>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Severity:</span>
                    <StatusIndicator
                      status={selectedPrediction.severity}
                      label={selectedPrediction.severity.toUpperCase()}
                    />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Value:</span>
                    <span className="text-white font-mono">{selectedPrediction.value}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Confidence:</span>
                    <span className={`font-medium ${
                      selectedPrediction.confidence >= 80 ? 'text-green-400' :
                      selectedPrediction.confidence >= 60 ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {selectedPrediction.confidence}%
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h5 className="text-sm font-medium text-astro-cyan mb-2">Time Window</h5>
                <div className="bg-astro-dark/50 rounded-lg p-3 text-sm">
                  <div className="text-white">{selectedPrediction.timeWindow.description}</div>
                  <div className="text-gray-400 text-xs mt-1">
                    {selectedPrediction.timeWindow.start.toLocaleString()} - {selectedPrediction.timeWindow.end.toLocaleString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Geographic and Mitigation */}
            <div className="space-y-4">
              <div>
                <h5 className="text-sm font-medium text-astro-cyan mb-2">Geographic Distribution</h5>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <span>{getCoverageIcon(selectedPrediction.geographicDistribution.coverage)}</span>
                    <span className="text-white capitalize">{selectedPrediction.geographicDistribution.coverage} Coverage</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Primary Region: </span>
                    <span className="text-white">{selectedPrediction.geographicDistribution.primaryRegion}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Affected Regions:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedPrediction.geographicDistribution.regions.map((region) => (
                        <span
                          key={region}
                          className="px-2 py-1 bg-astro-dark/50 text-astro-cyan text-xs rounded"
                        >
                          {region}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h5 className="text-sm font-medium text-astro-cyan mb-2">Mitigation Recommendations</h5>
                <ul className="text-sm text-gray-300 space-y-1">
                  {selectedPrediction.mitigation.map((action, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-astro-cyan mt-1">•</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {['critical', 'high', 'moderate', 'low'].map(severity => {
          const count = filteredPredictions.filter(p => p.severity === severity).length
          return (
            <div key={severity} className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-3 text-center">
              <div className={`text-2xl font-bold ${getSeverityStyles(severity).split(' ')[0]}`}>
                {count}
              </div>
              <div className="text-sm text-gray-400 capitalize">{severity} Risk</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}