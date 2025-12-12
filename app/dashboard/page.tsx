'use client'

import { useState, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import LoginForm from '../../components/LoginForm'
import UserInfo from '../../components/UserInfo'

// Dynamically import Highcharts to avoid SSR issues
const HighchartsReact = dynamic(
  () => import('highcharts-react-official'),
  { ssr: false }
)

export default function Dashboard() {
  const [currentTime, setCurrentTime] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [solarWindData, setSolarWindData] = useState<Array<[number, number]>>([])
  const [bzFieldData, setBzFieldData] = useState<Array<[number, number]>>([])
  const [user, setUser] = useState<any>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [highcharts, setHighcharts] = useState<any>(null)
  const chartRef = useRef<any>(null)

  // Load Highcharts on client side (lazy load - only when needed)
  useEffect(() => {
    if (typeof window !== 'undefined' && !highcharts) {
      // Load Highcharts only when user scrolls to charts or after initial render
      const timer = setTimeout(() => {
        import('highcharts').then((Highcharts) => {
          setHighcharts(Highcharts.default)
        }).catch((err) => {
          console.error('Failed to load Highcharts:', err)
        })
      }, 500) // Delay more to let page fully render
      return () => clearTimeout(timer)
    }
  }, [highcharts])

  useEffect(() => {
    // Set auth loading to false immediately - check auth in background
    setAuthLoading(false)
    
    // Check authentication status (non-blocking)
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
        // Silent fail - user can still use the page
        console.error('Auth check failed:', err)
      }
    }
    
    // Run auth check without blocking
    checkAuth()
    
    const updateTime = () => {
      setCurrentTime(new Date().toISOString().slice(0, 19) + 'Z')
    }
    
    updateTime()
    const interval = setInterval(updateTime, 1000)
    
    // Generate sample data for charts (optimized - fewer data points, no random)
    const generateSolarWindData = () => {
      const data: Array<[number, number]> = []
      const now = Date.now()
      // Reduced to 24 points for better performance
      for (let i = 0; i < 24; i++) {
        const time = now - (24 - i) * 60 * 60 * 1000
        // Deterministic values (no Math.random for performance)
        const baseValue = 350 + Math.sin(i * 0.5) * 80
        const variation = Math.sin(i * 0.7) * 50
        const value = Math.max(200, Math.min(600, baseValue + variation))
        data.push([time, Number(value.toFixed(1))])
      }
      return data
    }

    const generateBzFieldData = () => {
      const data: Array<[number, number]> = []
      const now = Date.now()
      // Reduced to 24 points for better performance
      for (let i = 0; i < 24; i++) {
        const time = now - (24 - i) * 60 * 60 * 1000
        // Deterministic values (no Math.random for performance)
        const baseValue = Math.sin(i * 0.6) * 12
        const variation = Math.cos(i * 0.8) * 8
        const value = Math.max(-30, Math.min(30, baseValue + variation))
        data.push([time, Number(value.toFixed(1))])
      }
      return data
    }

    // Generate data once and set immediately
    const windData = generateSolarWindData()
    const fieldData = generateBzFieldData()
    setSolarWindData(windData)
    setBzFieldData(fieldData)
    
    // Set loading to false immediately so page renders
    setIsLoading(false)
    
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
            <h3 className="text-xl font-semibold text-astro-cyan mb-4">Solar Wind Speed & Magnetic Field</h3>
            <div className="space-y-6">
              {/* Solar Wind Speed Chart */}
              <div className="bg-gray-800/30 rounded-lg p-5 border border-gray-700/50">
                {isLoading ? (
                  <div className="h-64 flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                      <p className="text-gray-400">Loading solar wind data...</p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <span className="text-sm font-medium text-gray-300">Wind Speed</span>
                        <span className="text-xs text-gray-500 ml-2">(km/s)</span>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="text-xs text-gray-500">Current</div>
                          <span className="text-xl font-mono font-bold text-astro-cyan">
                            {solarWindData[solarWindData.length - 1]?.[1]?.toFixed(1) || '425.3'}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-gray-500">Average</div>
                          <span className="text-sm font-mono text-gray-400">
                            {(solarWindData.reduce((sum, [, val]) => sum + val, 0) / solarWindData.length).toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="h-64">
                      {highcharts ? (
                        <HighchartsReact
                          highcharts={highcharts}
                          options={{
                            chart: {
                              type: 'spline',
                              backgroundColor: 'transparent',
                              height: 250,
                              zoomType: 'x',
                              animation: false
                            },
                            title: { text: null },
                            credits: { enabled: false },
                            legend: { enabled: false },
                            xAxis: {
                              type: 'datetime',
                              gridLineColor: '#374151',
                              gridLineWidth: 1,
                              lineColor: '#06b6d4',
                              lineWidth: 1,
                              tickColor: '#06b6d4',
                              labels: { 
                                style: { color: '#9ca3af', fontSize: '11px' },
                                format: '{value:%H:%M}'
                              },
                              title: {
                                text: 'Time (UTC)',
                                style: { color: '#9ca3af', fontSize: '12px' }
                              }
                            },
                            yAxis: {
                              title: { 
                                text: 'Wind Speed (km/s)',
                                style: { color: '#9ca3af', fontSize: '12px' }
                              },
                              gridLineColor: '#374151',
                              lineColor: '#06b6d4',
                              tickColor: '#06b6d4',
                              labels: { style: { color: '#9ca3af', fontSize: '11px' } },
                              plotLines: [{
                                color: '#ef4444',
                                width: 2,
                                value: 500,
                                dashStyle: 'Dash',
                                zIndex: 5,
                                label: {
                                  text: 'Critical: 500 km/s',
                                  align: 'right',
                                  style: { color: '#ef4444', fontSize: '10px', fontWeight: 'bold' }
                                }
                              }, {
                                color: '#f59e0b',
                                width: 1,
                                value: 400,
                                dashStyle: 'Dot',
                                zIndex: 4,
                                label: {
                                  text: 'Warning: 400 km/s',
                                  align: 'right',
                                  style: { color: '#f59e0b', fontSize: '9px' }
                                }
                              }]
                            },
                            tooltip: {
                              backgroundColor: 'rgba(15, 23, 42, 0.95)',
                              borderColor: '#06b6d4',
                              borderRadius: 8,
                              borderWidth: 2,
                              style: { color: '#ffffff', fontSize: '12px' },
                              shared: false,
                              formatter: function() {
                                return `<div style="padding: 4px;">
                                  <b style="color: #06b6d4;">${new Date(this.x!).toLocaleString()}</b><br/>
                                  <span style="color: #06b6d4;">Wind Speed: <b>${this.y?.toFixed(2)} km/s</b></span>
                                </div>`
                              }
                            },
                            plotOptions: {
                              spline: {
                                marker: { 
                                  enabled: false,
                                  states: { hover: { enabled: true, radius: 5 } }
                                },
                                lineWidth: 3,
                                animation: false,
                                threshold: null,
                                turboThreshold: 1000
                              }
                            },
                            series: [{
                              name: 'Solar Wind Speed',
                              data: solarWindData,
                              color: '#06b6d4',
                              fillColor: {
                                linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
                                stops: [
                                  [0, 'rgba(6, 182, 212, 0.3)'],
                                  [1, 'rgba(6, 182, 212, 0.05)']
                                ]
                              },
                              fillOpacity: 0.4,
                              zones: [{
                                value: 400,
                                color: '#06b6d4'
                              }, {
                                value: 500,
                                color: '#f59e0b'
                              }, {
                                color: '#ef4444'
                              }]
                            }]
                          }}
                        />
                      ) : (
                        <div className="h-full flex items-center justify-center">
                          <div className="text-center">
                            <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                            <p className="text-gray-400 text-sm">Loading chart...</p>
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="flex justify-between items-center mt-3 text-xs text-gray-500">
                      <span>Data range: Last 24 hours</span>
                      <span>Last updated: {currentTime}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Magnetic Field Chart */}
              <div className="bg-gray-800/30 rounded-lg p-5 border border-gray-700/50">
                {isLoading ? (
                  <div className="h-64 flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                      <p className="text-gray-400">Loading magnetic field data...</p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <span className="text-sm font-medium text-gray-300">Bz Magnetic Field</span>
                        <span className="text-xs text-gray-500 ml-2">(nT)</span>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="text-xs text-gray-500">Current</div>
                          <span className={`text-xl font-mono font-bold ${
                            (bzFieldData[bzFieldData.length - 1]?.[1] || 0) < -10 
                              ? 'text-red-400' 
                              : (bzFieldData[bzFieldData.length - 1]?.[1] || 0) < 0 
                                ? 'text-yellow-400' 
                                : 'text-green-400'
                          }`}>
                            {bzFieldData[bzFieldData.length - 1]?.[1]?.toFixed(2) || '-2.10'}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-gray-500">Status</div>
                          <span className={`text-sm font-semibold ${
                            (bzFieldData[bzFieldData.length - 1]?.[1] || 0) < -10 
                              ? 'text-red-400' 
                              : 'text-green-400'
                          }`}>
                            {(bzFieldData[bzFieldData.length - 1]?.[1] || 0) < -10 ? '⚠ Critical' : '✓ Normal'}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="h-64">
                      {highcharts ? (
                        <HighchartsReact
                          highcharts={highcharts}
                          options={{
                            chart: {
                              type: 'spline',
                              backgroundColor: 'transparent',
                              height: 250,
                              zoomType: 'x',
                              animation: false
                            },
                            title: { text: null },
                            credits: { enabled: false },
                            legend: { enabled: false },
                            xAxis: {
                              type: 'datetime',
                              gridLineColor: '#374151',
                              gridLineWidth: 1,
                              lineColor: '#10b981',
                            lineWidth: 1,
                            tickColor: '#10b981',
                            labels: { 
                              style: { color: '#9ca3af', fontSize: '11px' },
                              format: '{value:%H:%M}'
                            },
                            title: {
                              text: 'Time (UTC)',
                              style: { color: '#9ca3af', fontSize: '12px' }
                            }
                          },
                          yAxis: {
                            title: { 
                              text: 'Bz Field (nT)',
                              style: { color: '#9ca3af', fontSize: '12px' }
                            },
                            gridLineColor: '#374151',
                            lineColor: '#10b981',
                            tickColor: '#10b981',
                            labels: { style: { color: '#9ca3af', fontSize: '11px' } },
                            plotLines: [{
                              color: '#ef4444',
                              width: 2,
                              value: -10,
                              dashStyle: 'Dash',
                              zIndex: 5,
                              label: {
                                text: 'Critical: -10 nT',
                                align: 'right',
                                style: { color: '#ef4444', fontSize: '10px', fontWeight: 'bold' }
                              }
                            }, {
                              color: '#6b7280',
                              width: 1,
                              value: 0,
                              zIndex: 4,
                              label: {
                                text: '0 nT (Neutral)',
                                align: 'right',
                                style: { color: '#6b7280', fontSize: '9px' }
                              }
                            }]
                          },
                          tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            borderColor: '#10b981',
                            borderRadius: 8,
                            borderWidth: 2,
                            style: { color: '#ffffff', fontSize: '12px' },
                            shared: false,
                            formatter: function() {
                              const value = this.y as number
                              const status = value < -10 ? '🔴 Critical' : value < 0 ? '🟡 Negative' : '🟢 Positive'
                              return `<div style="padding: 4px;">
                                <b style="color: #10b981;">${new Date(this.x!).toLocaleString()}</b><br/>
                                <span style="color: #10b981;">Bz Field: <b>${value.toFixed(2)} nT</b></span><br/>
                                <span style="color: #9ca3af; font-size: 10px;">Status: ${status}</span>
                              </div>`
                            }
                          },
                          plotOptions: {
                            spline: {
                              marker: { 
                                enabled: false,
                                states: { hover: { enabled: true, radius: 5 } }
                              },
                              lineWidth: 3,
                              animation: false,
                              threshold: null,
                              turboThreshold: 1000
                            }
                          },
                          series: [{
                            name: 'Bz Magnetic Field',
                            data: bzFieldData,
                            color: '#10b981',
                            fillColor: {
                              linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
                              stops: [
                                [0, 'rgba(16, 185, 129, 0.3)'],
                                [1, 'rgba(16, 185, 129, 0.05)']
                              ]
                            },
                            fillOpacity: 0.4,
                            negativeColor: '#ef4444',
                            zones: [{
                              value: -10,
                              color: '#ef4444'
                            }, {
                              value: 0,
                              color: '#10b981'
                            }, {
                              color: '#10b981'
                            }]
                          }]
                        }}
                        />
                      ) : (
                        <div className="h-full flex items-center justify-center">
                          <div className="text-center">
                            <div className="w-8 h-8 border-2 border-astro-cyan border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                            <p className="text-gray-400 text-sm">Loading chart...</p>
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="flex justify-between items-center mt-3 text-xs text-gray-500">
                      <span>Data range: Last 24 hours</span>
                      <span className={`font-semibold ${
                        (bzFieldData[bzFieldData.length - 1]?.[1] || 0) < -10 
                          ? 'text-red-400' 
                          : 'text-green-400'
                      }`}>
                        Status: {(bzFieldData[bzFieldData.length - 1]?.[1] || 0) < -10 ? 'Critical - Geomagnetic Storm Risk' : 'Normal Conditions'}
                      </span>
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
                    {highcharts && (
                      <HighchartsReact
                        highcharts={highcharts}
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
                    )}
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
                {highcharts && (
                  <HighchartsReact
                    highcharts={highcharts}
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
                )}
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