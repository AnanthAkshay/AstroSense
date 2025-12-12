'use client'

import { useState, useEffect } from 'react'

export default function SimpleDashboard() {
  const [currentTime, setCurrentTime] = useState<string>('')

  useEffect(() => {
    const updateTime = () => {
      setCurrentTime(new Date().toISOString().slice(0, 19) + 'Z')
    }
    
    updateTime()
    const interval = setInterval(updateTime, 1000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen p-8">
      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white">Space Weather Dashboard</h2>
          <p className="text-gray-400 mt-1">Real-time monitoring and impact forecasting</p>
        </div>
        <div className="mt-4 sm:mt-0">
          <div className="bg-blue-900/20 px-4 py-2 rounded-lg border border-cyan-500/30">
            <p className="text-sm text-gray-300">UTC Time</p>
            <p className="text-lg font-mono text-cyan-400">{currentTime}</p>
          </div>
        </div>
      </div>

      {/* Simple Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Placeholder for 3D Globe */}
          <div className="bg-blue-900/10 rounded-lg border border-cyan-500/20 p-6">
            <h3 className="text-xl font-semibold text-cyan-400 mb-4">Global Impact Heatmap</h3>
            <div className="h-64 sm:h-80 bg-gray-800/50 rounded flex items-center justify-center">
              <p className="text-gray-400">3D Earth Globe (Loading...)</p>
            </div>
          </div>

          {/* Placeholder for Charts */}
          <div className="bg-blue-900/10 rounded-lg border border-cyan-500/20 p-6">
            <h3 className="text-xl font-semibold text-cyan-400 mb-4">Solar Wind & Magnetic Field</h3>
            <div className="space-y-4">
              <div className="h-48 bg-gray-800/50 rounded flex items-center justify-center">
                <p className="text-gray-400">Solar Wind Speed Chart</p>
              </div>
              <div className="h-48 bg-gray-800/50 rounded flex items-center justify-center">
                <p className="text-gray-400">Bz Magnetic Field Chart</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Risk Cards */}
          <div className="bg-blue-900/10 rounded-lg border border-cyan-500/20 p-6">
            <h3 className="text-xl font-semibold text-cyan-400 mb-4">Sector Risk Assessment</h3>
            <div className="space-y-3">
              {['Aviation', 'Telecommunications', 'GPS/GNSS', 'Power Grid', 'Satellites'].map((sector) => (
                <div key={sector} className="bg-gray-800/50 p-3 rounded">
                  <div className="flex justify-between items-center">
                    <span className="text-white">{sector}</span>
                    <span className="text-green-400">LOW</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Alerts Panel */}
          <div className="bg-blue-900/10 rounded-lg border border-cyan-500/20 p-6">
            <h3 className="text-xl font-semibold text-cyan-400 mb-4">Active Alerts</h3>
            <div className="text-center py-8">
              <p className="text-gray-400">No active alerts</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="mt-6 bg-blue-900/10 rounded-lg border border-cyan-500/20 p-6">
        <h3 className="text-xl font-semibold text-cyan-400 mb-4">Impact Predictions</h3>
        <div className="text-center py-8">
          <p className="text-gray-400">Impact prediction table will appear here</p>
        </div>
      </div>
    </div>
  )
}