import { apiClient } from '@/lib/api-client'

// Mock fetch for testing
global.fetch = jest.fn()

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    apiClient.clearCache()
  })

  describe('fetchCurrentData', () => {
    it('should fetch current space weather data successfully', async () => {
      const mockData = {
        timestamp: '2024-01-01T00:00:00Z',
        solar_wind_speed: 400,
        bz_field: -5,
        kp_index: 3,
        proton_flux: 1.5,
        source: 'NOAA'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.fetchCurrentData()

      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockData)
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/fetch-data'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    it('should handle API errors gracefully', async () => {
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      })

      const result = await apiClient.fetchCurrentData()

      expect(result.success).toBe(false)
      expect(result.error).toContain('HTTP 500')
    })

    it('should cache responses for the specified TTL', async () => {
      const mockData = {
        timestamp: '2024-01-01T00:00:00Z',
        solar_wind_speed: 400,
        bz_field: -5,
        kp_index: 3,
        proton_flux: 1.5,
        source: 'NOAA'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      // First call
      await apiClient.fetchCurrentData()
      
      // Second call should use cache
      await apiClient.fetchCurrentData()

      expect(fetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('predictImpact', () => {
    it('should send prediction request with input data', async () => {
      const inputData = {
        solar_wind_speed: 500,
        bz_field: -10,
        kp_index: 5
      }

      const mockPredictions = {
        aviation_hf_blackout_prob: 75,
        aviation_polar_risk: 60,
        telecom_signal_degradation: 45,
        gps_drift_cm: 120,
        power_grid_gic_risk: 7,
        satellite_drag_risk: 6,
        composite_score: 68,
        timestamp: '2024-01-01T00:00:00Z',
        model_version: 'v1.0'
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockPredictions,
      })

      const result = await apiClient.predictImpact(inputData)

      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockPredictions)
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/predict-impact'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(inputData),
        })
      )
    })
  })

  describe('runBacktest', () => {
    it('should initiate backtest for specified date', async () => {
      const eventDate = '2024-05-10'
      const mockBacktestData = {
        event_name: 'May 2024 Geomagnetic Storm',
        event_date: '2024-05-10T00:00:00Z',
        predicted_impacts: {
          aviation_hf_blackout_prob: 80,
          aviation_polar_risk: 70,
          telecom_signal_degradation: 55,
          gps_drift_cm: 150,
          power_grid_gic_risk: 8,
          satellite_drag_risk: 7,
          composite_score: 75,
          timestamp: '2024-05-10T00:00:00Z',
          model_version: 'v1.0'
        },
        actual_impacts: {
          aviation_hf_blackout_prob: 85,
          aviation_polar_risk: 75,
          telecom_signal_degradation: 60,
          gps_drift_cm: 140,
          power_grid_gic_risk: 9,
          satellite_drag_risk: 8,
          composite_score: 80,
          timestamp: '2024-05-10T00:00:00Z',
          model_version: 'actual'
        },
        accuracy_metrics: {
          mae: 5.2,
          rmse: 7.8,
          r2: 0.92
        },
        timeline: [
          ['2024-05-10T00:00:00Z', { event: 'CME detected' }],
          ['2024-05-10T12:00:00Z', { event: 'Impact begins' }]
        ]
      }

      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBacktestData,
      })

      const result = await apiClient.runBacktest(eventDate)

      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockBacktestData)
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/backtest'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ event_date: eventDate }),
        })
      )
    })
  })

  describe('cache management', () => {
    it('should clear cache when requested', () => {
      apiClient.clearCache()
      const stats = apiClient.getCacheStats()
      expect(stats.size).toBe(0)
      expect(stats.keys).toEqual([])
    })

    it('should provide cache statistics', async () => {
      const mockData = { test: 'data' }
      ;(fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      await apiClient.fetchCurrentData()
      const stats = apiClient.getCacheStats()
      
      expect(stats.size).toBeGreaterThan(0)
      expect(stats.keys.length).toBeGreaterThan(0)
    })
  })
})