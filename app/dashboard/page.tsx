'use client'

import { useState, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import LoginForm from '../../components/LoginForm'
import UserInfo from '../../components/UserInfo'

// Dynamically import Highcharts to avoid SSR issues
const Highcharts = dynamic(() => import('highcharts'), { ssr: false })
const HighchartsReact = dynamic(() => import('highcharts-react-official'), { ssr: false })

export default function Dashboard() {
  const [currentTime, setCurrentTime] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [solarWindData, setSolarWindData] = useState<Array<[number, number]>>([])
  const [bzFieldData, setBzFieldData] = useState<Array<[number, number]>>([])
  const [user, setUser] = useState<any>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const chartRef = useRef<any>(null)

  useEffect(() => {
    // Check authentication status
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/status', {
          credentials: 'include',
        })
        const data = await response.json()
        
        if (data.authenticated) {
          setUser(data.user)
        }
      } catch (err) {
        console.error('Auth check failed:', err)
      } finally {
        setAuthLoading(false)
      }
    }
    
    checkAuth()
    
    const updateTime = () => {
      setCurrentTime(new Date().toISOString().slice(0, 19) + 'Z')
    }
    
    updateTime()
    const interval = setInterval(updateTime, 1000)
    
    // Generate sample data for charts
    const generateSolarWindData = () => {
      const data: Array<[number, number]> = []
      const now = Date.now()
      for (let i = 0; i < 24; i++) {
        const time = now - (24 - i) * 60 * 60 * 1000 // Last 24 hours
        const value = 300 + Math.sin(i * 0.5) * 100 + Math.random() * 150
        data.push([time, value])
      }
      return data
    }

    const generateBzFieldData = () => {
      const data: Array<[number, number]> = []
      const now = Date.now()
      for (let i = 0; i < 24; i++) {
        const time = now - (24 - i) * 60 * 60 * 1000 // Last 24 hours
        const value = Math.sin(i * 0.3) * 15 + Math.random() * 10 - 5
        data.push([time, value])
      }
      return data
    }

    // Initialize chart data
    setSolarWindData(generateSolarWindData())
    setBzFieldData(generateBzFieldData())
    
    // Simulate loading time
    setTimeout(() => setIsLoading(false), 2000)
    
    return () => clearInterval(interval)
  }, [])

  const handleLogin = (userData: any) => {
    setUser(userData)
  }

  const handleLogout = () => {
    setUser(null)
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      {/* Authentication Section */}
      {!user ? (
        <LoginForm onLogin={handleLogin} />
      ) : (
        <UserInfo user={user} onLogout={handleLogout} />
      )}

      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
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
              {isLoading ? (
                <div className="h-full bg-gray-800/50 rounded flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-12 h-12 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-400">Loading 3D Earth Globe...</p>
                    <p className="text-xs text-gray-500 mt-2">Initializing Cesium engine</p>
                  </div>
                </div>
              ) : (
                <div className="h-full bg-gray-800/50 rounded flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-gradient-to-br from-astro-blue to-astro-cyan rounded-full mx-auto mb-4 flex items-center justify-center shadow-lg">
                      <span className="text-2xl">🌍</span>
                    </div>
                    <p className="text-astro-cyan font-semibold">Interactive 3D Earth Globe</p>
                    <p className="text-xs text-gray-400 mt-2">Click to explore global space weather impacts</p>
                    <div className="mt-4 px-4 py-2 bg-astro-blue/30 rounded-lg border border-astro-cyan/20">
                      <p className="text-xs text-gray-300">🌐 Global Coverage • 🛰️ Real-time Data • ⚡ Impact Analysis</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Charts Component */}
          <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6 animate-slide-up">
            <h3 className="text-xl font-semibold text-astro-cyan mb-4">Solar Wind & Magnetic Field</h3>
            <div className="space-y-4">
              {/* Solar Wind Chart */}
              <div className="bg-gray-800/30 rounded-lg p-4">
                {isLoading ? (
                  <div className="h-48 flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                      <p className="text-gray-400">Loading solar wind data...</p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-400">Solar Wind Speed</span>
                      <span className="text-lg font-mono text-astro-cyan">
                        {solarWindData[solarWindData.length - 1]?.[1]?.toFixed(1) || '425.3'} km/s
                      </span>
                    </div>
                    <div className="h-40">
                      <HighchartsReact
                        highcharts={Highcharts}
                        options={{
                          chart: {
                            type: 'line',
                            backgroundColor: 'transparent',
                            height: 160,
                            animation: { duration: 300 }
                          },
                          title: { text: null },
                          credits: { enabled: false },
                          legend: { enabled: false },
                          xAxis: {
                            type: 'datetime',
                            gridLineColor: '#1e3a8a',
                            lineColor: '#06b6d4',
                            tickColor: '#06b6d4',
                            labels: { style: { color: '#9ca3af' } }
                          },
                          yAxis: {
                            title: { text: null },
                            gridLineColor: '#1e3a8a',
                            lineColor: '#06b6d4',
                            tickColor: '#06b6d4',
                            labels: { style: { color: '#9ca3af' } },
                            plotLines: [{
                              color: '#ef4444',
                              width: 2,
                              value: 500,
                              dashStyle: 'Dash',
                              label: {
                                text: 'Critical: 500 km/s',
                                style: { color: '#ef4444', fontSize: '10px' }
                              }
                            }]
                          },
                          tooltip: {
                            backgroundColor: 'rgba(30, 58, 138, 0.9)',
                            borderColor: '#06b6d4',
                            style: { color: '#ffffff' },
                            formatter: function() {
                              return `<b>${new Date(this.x!).toLocaleTimeString()}</b><br/>Solar Wind: ${this.y} km/s`
                            }
                          },
                          plotOptions: {
                            line: {
                              marker: { enabled: false },
                              lineWidth: 2,
                              animation: { duration: 200 }
                            }
                          },
                          series: [{
                            name: 'Solar Wind Speed',
                            data: solarWindData,
                            color: '#06b6d4',
                            zones: [{
                              value: 500,
                              color: '#06b6d4'
                            }, {
                              color: '#ef4444'
                            }]
                          }]
                        }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-2">Last updated: {currentTime}</div>
                  </div>
                )}
              </div>

              {/* Magnetic Field Chart */}
              <div className="bg-gray-800/30 rounded-lg p-4">
                {isLoading ? (
                  <div className="h-48 flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                      <p className="text-gray-400">Loading magnetic field data...</p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-400">Bz Magnetic Field</span>
                      <span className="text-lg font-mono text-astro-cyan">
                        {bzFieldData[bzFieldData.length - 1]?.[1]?.toFixed(1) || '-2.1'} nT
                      </span>
                    </div>
                    <div className="h-40">
                      <HighchartsReact
                        highcharts={Highcharts}
                        options={{
                          chart: {
                            type: 'line',
                            backgroundColor: 'transparent',
                            height: 160,
                            animation: { duration: 300 }
                          },
                          title: { text: null },
                          credits: { enabled: false },
                          legend: { enabled: false },
                          xAxis: {
                            type: 'datetime',
                            gridLineColor: '#1e3a8a',
                            lineColor: '#06b6d4',
                            tickColor: '#06b6d4',
                            labels: { style: { color: '#9ca3af' } }
                          },
                          yAxis: {
                            title: { text: null },
                            gridLineColor: '#1e3a8a',
                            lineColor: '#06b6d4',
                            tickColor: '#06b6d4',
                            labels: { style: { color: '#9ca3af' } },
                            plotLines: [{
                              color: '#ef4444',
                              width: 2,
                              value: -10,
                              dashStyle: 'Dash',
                              label: {
                                text: 'Critical: -10 nT',
                                style: { color: '#ef4444', fontSize: '10px' }
                              }
                            }, {
                              color: '#6b7280',
                              width: 1,
                              value: 0,
                              label: {
                                text: '0 nT',
                                style: { color: '#6b7280', fontSize: '10px' }
                              }
                            }]
                          },
                          tooltip: {
                            backgroundColor: 'rgba(30, 58, 138, 0.9)',
                            borderColor: '#06b6d4',
                            style: { color: '#ffffff' },
                            formatter: function() {
                              return `<b>${new Date(this.x!).toLocaleTimeString()}</b><br/>Bz Field: ${this.y} nT`
                            }
                          },
                          plotOptions: {
                            line: {
                              marker: { enabled: false },
                              lineWidth: 2,
                              animation: { duration: 200 }
                            }
                          },
                          series: [{
                            name: 'Bz Magnetic Field',
                            data: bzFieldData,
                            color: '#10b981',
                            zones: [{
                              value: -10,
                              color: '#ef4444'
                            }, {
                              color: '#10b981'
                            }]
                          }]
                        }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-2">
                      Status: {bzFieldData[bzFieldData.length - 1]?.[1] < -10 ? 'Critical' : 'Normal'}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Risk Cards and Alerts */}
        <div className="space-y-6">
          {/* Risk Cards */}
          <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6 animate-fade-in">
            <h3 className="text-xl font-semibold text-astro-cyan mb-4">Sector Risk Assessment</h3>
            {isLoading ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-gray-400">Loading risk assessment...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Overall Risk Gauge */}
                <div className="bg-gray-800/30 rounded-lg p-4">
                  <div className="text-center mb-2">
                    <span className="text-sm text-gray-400">Overall Risk Level</span>
                  </div>
                  <div className="h-32">
                    <HighchartsReact
                      highcharts={Highcharts}
                      options={{
                        chart: {
                          type: 'gauge',
                          backgroundColor: 'transparent',
                          height: 120
                        },
                        title: { text: null },
                        credits: { enabled: false },
                        pane: {
                          startAngle: -90,
                          endAngle: 90,
                          background: [{
                            backgroundColor: '#1f2937',
                            borderWidth: 0,
                            outerRadius: '109%'
                          }]
                        },
                        yAxis: {
                          min: 0,
                          max: 100,
                          tickPixelInterval: 30,
                          tickWidth: 2,
                          tickPosition: 'inside',
                          tickLength: 20,
                          tickColor: '#06b6d4',
                          labels: {
                            step: 2,
                            rotation: 'auto',
                            style: { color: '#9ca3af', fontSize: '10px' }
                          },
                          title: { text: null },
                          plotBands: [{
                            from: 0,
                            to: 30,
                            color: '#10b981'
                          }, {
                            from: 30,
                            to: 70,
                            color: '#f59e0b'
                          }, {
                            from: 70,
                            to: 100,
                            color: '#ef4444'
                          }]
                        },
                        series: [{
                          name: 'Risk Level',
                          data: [25],
                          tooltip: { valueSuffix: '%' },
                          dataLabels: {
                            format: '{y}%',
                            borderWidth: 0,
                            color: '#06b6d4',
                            style: { fontSize: '14px', fontWeight: 'bold' }
                          },
                          dial: {
                            radius: '80%',
                            backgroundColor: '#06b6d4',
                            baseWidth: 12,
                            baseLength: '0%',
                            rearLength: '0%'
                          },
                          pivot: {
                            backgroundColor: '#06b6d4',
                            radius: 6
                          }
                        }]
                      }}
                    />
                  </div>
                </div>

                {/* Sector Risk Cards */}
                <div className="space-y-2">
                  {[
                    { name: 'Aviation', risk: 'LOW', value: 15, color: 'text-green-400' },
                    { name: 'Telecommunications', risk: 'LOW', value: 20, color: 'text-green-400' },
                    { name: 'GPS/GNSS', risk: 'MODERATE', value: 45, color: 'text-yellow-400' },
                    { name: 'Power Grid', risk: 'LOW', value: 10, color: 'text-green-400' },
                    { name: 'Satellites', risk: 'LOW', value: 25, color: 'text-green-400' }
                  ].map((sector) => (
                    <div key={sector.name} className="bg-gray-800/30 p-3 rounded hover:bg-gray-700/30 transition-colors">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-white text-sm">{sector.name}</span>
                        <span className={`${sector.color} text-xs font-semibold`}>{sector.risk}</span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-500 ${
                            sector.value < 30 ? 'bg-green-400' : 
                            sector.value < 70 ? 'bg-yellow-400' : 'bg-red-400'
                          }`}
                          style={{ width: `${sector.value}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{sector.value}% risk level</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Alerts Panel */}
          <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6 animate-slide-up">
            <h3 className="text-xl font-semibold text-astro-cyan mb-4">Active Alerts</h3>
            {isLoading ? (
              <div className="text-center py-8">
                <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                <p className="text-gray-400">Loading alerts...</p>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-12 h-12 bg-green-500/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-green-400 text-xl">✓</span>
                </div>
                <p className="text-gray-400">No active alerts</p>
                <p className="text-xs text-gray-500 mt-2">All systems operating normally</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Section - Impact Predictions */}
      <div className="mt-6 bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6 animate-fade-in">
        <h3 className="text-xl font-semibold text-astro-cyan mb-4">Impact Predictions & Analysis</h3>
        {isLoading ? (
          <div className="text-center py-8">
            <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-gray-400">Loading predictions...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Event Probability Chart */}
            <div className="bg-gray-800/30 rounded-lg p-4">
              <h4 className="text-lg font-semibold text-astro-cyan mb-3">Event Probabilities (Next 24h)</h4>
              <div className="h-64">
                <HighchartsReact
                  highcharts={Highcharts}
                  options={{
                    chart: {
                      type: 'pie',
                      backgroundColor: 'transparent',
                      height: 250
                    },
                    title: { text: null },
                    credits: { enabled: false },
                    tooltip: {
                      backgroundColor: 'rgba(30, 58, 138, 0.9)',
                      borderColor: '#06b6d4',
                      style: { color: '#ffffff' },
                      pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
                    },
                    accessibility: { point: { valueSuffix: '%' } },
                    plotOptions: {
                      pie: {
                        allowPointSelect: true,
                        cursor: 'pointer',
                        dataLabels: {
                          enabled: true,
                          format: '<b>{point.name}</b>: {point.percentage:.1f} %',
                          style: { color: '#ffffff', fontSize: '11px' }
                        },
                        showInLegend: true
                      }
                    },
                    legend: {
                      align: 'right',
                      verticalAlign: 'middle',
                      layout: 'vertical',
                      itemStyle: { color: '#9ca3af', fontSize: '11px' }
                    },
                    series: [{
                      name: 'Probability',
                      colorByPoint: true,
                      data: [{
                        name: 'Solar Flare',
                        y: 15,
                        color: '#f59e0b'
                      }, {
                        name: 'Geomagnetic Storm',
                        y: 8,
                        color: '#ef4444'
                      }, {
                        name: 'Radio Blackout',
                        y: 5,
                        color: '#8b5cf6'
                      }, {
                        name: 'Normal Conditions',
                        y: 72,
                        color: '#10b981'
                      }]
                    }]
                  }}
                />
              </div>
            </div>

            {/* Predictions Table */}
            <div className="bg-gray-800/30 rounded-lg p-4">
              <h4 className="text-lg font-semibold text-astro-cyan mb-3">Upcoming Events</h4>
              <div className="space-y-3">
                {[
                  { time: '12:30 UTC', event: 'Solar Flare', probability: 15, impact: 'Low', color: 'text-yellow-400' },
                  { time: '18:45 UTC', event: 'Geomagnetic Storm', probability: 8, impact: 'Low', color: 'text-orange-400' },
                  { time: '22:15 UTC', event: 'Radio Blackout', probability: 5, impact: 'Minimal', color: 'text-purple-400' }
                ].map((prediction, index) => (
                  <div key={index} className="bg-gray-700/50 rounded-lg p-3 hover:bg-gray-700/70 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-white font-medium">{prediction.event}</div>
                        <div className="text-xs text-gray-400">{prediction.time}</div>
                      </div>
                      <div className="text-right">
                        <div className={`${prediction.color} font-semibold`}>{prediction.probability}%</div>
                        <div className="text-xs text-gray-400">{prediction.impact} Impact</div>
                      </div>
                    </div>
                    <div className="w-full bg-gray-600 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-500 ${
                          prediction.probability < 10 ? 'bg-green-400' : 
                          prediction.probability < 20 ? 'bg-yellow-400' : 'bg-red-400'
                        }`}
                        style={{ width: `${prediction.probability}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 p-3 bg-astro-blue/20 rounded-lg border border-astro-cyan/30">
                <div className="text-xs text-gray-300">
                  <span className="text-astro-cyan font-semibold">📊 Analysis:</span> Current space weather conditions show low to moderate activity levels with minimal impact expected across all sectors.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}