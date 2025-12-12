// API Client for AstroSense Backend Communication
// Implements fetch wrappers for REST endpoints with error handling and caching

export interface SpaceWeatherData {
  timestamp: string
  solar_wind_speed: number
  bz_field: number
  kp_index: number
  proton_flux: number
  source: string
}

export interface SectorPredictions {
  aviation_hf_blackout_prob: number
  aviation_polar_risk: number
  telecom_signal_degradation: number
  gps_drift_cm: number
  power_grid_gic_risk: number
  satellite_drag_risk: number
  composite_score: number
  timestamp: string
  model_version: string
}

export interface BacktestData {
  event_name: string
  event_date: string
  predicted_impacts: SectorPredictions
  actual_impacts: SectorPredictions
  accuracy_metrics: Record<string, number>
  timeline: Array<[string, any]>
}

export interface ApiResponse<T> {
  data: T
  success: boolean
  error?: string
  timestamp: string
}

class ApiClient {
  private baseUrl: string
  private cache: Map<string, { data: any; timestamp: number; ttl: number }>
  private defaultCacheTtl: number = 60000 // 60 seconds

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl
    this.cache = new Map()
  }

  // Generic fetch wrapper with error handling and caching
  private async fetchWithCache<T>(
    endpoint: string,
    options: RequestInit = {},
    cacheTtl: number = this.defaultCacheTtl
  ): Promise<ApiResponse<T>> {
    const cacheKey = `${endpoint}:${JSON.stringify(options)}`
    
    // Check cache first
    const cached = this.cache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      const result: ApiResponse<T> = {
        data,
        success: true,
        timestamp: new Date().toISOString(),
      }

      // Cache successful responses
      this.cache.set(cacheKey, {
        data: result,
        timestamp: Date.now(),
        ttl: cacheTtl,
      })

      return result
    } catch (error) {
      console.error(`API Error for ${endpoint}:`, error)
      return {
        data: null as T,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      }
    }
  }

  // Predict impact endpoint
  async predictImpact(inputData: Partial<SpaceWeatherData>): Promise<ApiResponse<SectorPredictions>> {
    return this.fetchWithCache<SectorPredictions>('/api/predict-impact', {
      method: 'POST',
      body: JSON.stringify(inputData),
    }, 30000) // 30 second cache for predictions
  }

  // Fetch current space weather data
  async fetchCurrentData(): Promise<ApiResponse<SpaceWeatherData>> {
    return this.fetchWithCache<SpaceWeatherData>('/api/fetch-data', {
      method: 'GET',
    }, 10000) // 10 second cache for current data
  }

  // Backtest historical events
  async runBacktest(eventDate: string): Promise<ApiResponse<BacktestData>> {
    return this.fetchWithCache<BacktestData>('/api/backtest', {
      method: 'POST',
      body: JSON.stringify({ event_date: eventDate }),
    }, 300000) // 5 minute cache for backtest data
  }

  // Clear cache (useful for forced refresh)
  clearCache(): void {
    this.cache.clear()
  }

  // Get cache stats for debugging
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    }
  }
}

// Singleton instance
export const apiClient = new ApiClient()