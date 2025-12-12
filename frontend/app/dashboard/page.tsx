'use client'

import dynamic from 'next/dynamic'
import { useState, useEffect } from 'react'
import ChartsComponent from '@/components/ChartsComponent'
import RiskCardsComponent from '@/components/RiskCardsComponent'
import AlertsPanelComponent from '@/components/AlertsPanelComponent'
import ImpactTableComponent from '@/components/ImpactTableComponent'
import BacktestingControlsComponent from '@/components/BacktestingControlsComponent'

// Dynamically import HeatmapComponent to avoid SSR issues with Cesium
const HeatmapComponent = dynamic(() => import('@/components/HeatmapComponent'), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full bg-astro-dark/50 rounded-lg flex items-center justify-center">
      <p className="text-gray-400">Loading 3D Earth Globe...</p>
    </div>
  )
})

export default function Dashboard() {
  const [currentTime, setCurrentTime] = useState<string>('')
  const [systemMode, setSystemMode] = useState<'live' | 'backtest'>('live')

  useEffect(() => {
    const updateTime = () => {
      setCurrentTime(new Date().toISOString().slice(0, 19) + 'Z')
    }
    
    updateTime()
    const interval = setInterval(updateTime, 1000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Space Weather Dashboard</h2>
          <p className="text-gray-400 mt-1">Real-time monitoring and impact forecasting</p>
        </div>
        <div className="mt-4 sm:mt-0">
          <div className="bg-astro-blue/20 px-4 py-2 rounded-lg border border-astro-cyan/30">
            <p className="text-sm text-gray-300">UTC Time</p>
            <p className="text-lg font-mono text-astro-cyan">{currentTime}</p>
          </div>
        </div>
      </div>

      {/* Grid Layout for Dashboard Components */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Visualizations */}
        <div className="lg:col-span-2 space-y-6">
          {/* Global Impact Heatmap */}
          <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6 animate-fade-in">
            <h3 className="text-xl font-semibold text-astro-cyan mb-4">Global Impact Heatmap</h3>
            <div className="h-64 sm:h-80">
              <HeatmapComponent 
                className="h-full w-full"
                onRegionSelect={(region) => {
                  console.log('Selected region:', region)
                }}
              />
            </div>
          </div>

          {/* Charts Component */}
          <ChartsComponent 
            className="animate-slide-up"
            onThresholdCrossing={(type, value, threshold) => {
              console.log(`Threshold crossing detected: ${type} = ${value} (threshold: ${threshold})`)
            }}
          />
        </div>

        {/* Right Column - Risk Cards and Alerts */}
        <div className="space-y-6">
          {/* Risk Cards */}
          <RiskCardsComponent 
            className="animate-fade-in"
            onRiskChange={(sectorId, newRisk) => {
              console.log(`Risk updated for ${sectorId}:`, newRisk)
            }}
          />

          {/* Alerts Panel */}
          <AlertsPanelComponent 
            className="animate-slide-up"
            onAlertDismiss={(alertId) => {
              console.log(`Alert dismissed: ${alertId}`)
            }}
            enableAudio={true}
          />
        </div>
      </div>

      {/* Bottom Section - Impact Table */}
      <ImpactTableComponent 
        className="animate-fade-in"
        onPredictionSelect={(prediction) => {
          console.log('Selected prediction:', prediction)
        }}
      />

      {/* Backtesting Controls */}
      <BacktestingControlsComponent 
        className="animate-fade-in"
        onModeChange={(mode) => {
          setSystemMode(mode)
          console.log('System mode changed to:', mode)
        }}
        onPlaybackStateChange={(state) => {
          console.log('Playback state changed to:', state)
        }}
        onSpeedChange={(speed) => {
          console.log('Playback speed changed to:', speed)
        }}
      />
    </div>
  )
}