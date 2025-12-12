import { renderHook, act } from '@testing-library/react'
import { useCurrentData, usePredictions, useBacktest } from '@/hooks/useApiData'
import { useWebSocket } from '@/hooks/useWebSocket'
import { apiClient } from '@/lib/api-client'
import { wsClient } from '@/lib/websocket-client'

// Mock the API client
jest.mock('@/lib/api-client')
jest.mock('@/lib/websocket-client')

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>
const mockWsClient = wsClient as jest.Mocked<typeof wsClient>

describe('API Data Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('useCurrentData', () => {
    it('should fetch current data on mount', async () => {
      const mockData = {
        timestamp: '2024-01-01T00:00:00Z',
        solar_wind_speed: 400,
        bz_field: -5,
        kp_index: 3,
        proton_flux: 1.5,
        source: 'NOAA'
      }

      mockApiClient.fetchCurrentData.mockResolvedValue({
        data: mockData,
        success: true,
        timestamp: '2024-01-01T00:00:00Z'
      })

      const { result } = renderHook(() => useCurrentData(5000))

      expect(result.current.loading).toBe(true)
      expect(result.current.data).toBe(null)

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      expect(mockApiClient.fetchCurrentData).toHaveBeenCalled()
      expect(result.current.loading).toBe(false)
      expect(result.current.data).toEqual(mockData)
      expect(result.current.error).toBe(null)
    })

    it('should handle API errors', async () => {
      mockApiClient.fetchCurrentData.mockResolvedValue({
        data: null as any,
        success: false,
        error: 'Network error',
        timestamp: '2024-01-01T00:00:00Z'
      })

      const { result } = renderHook(() => useCurrentData())

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      expect(result.current.loading).toBe(false)
      expect(result.current.data).toBe(null)
      expect(result.current.error).toBe('Network error')
    })

    it('should refresh data at specified intervals', async () => {
      mockApiClient.fetchCurrentData.mockResolvedValue({
        data: {
          timestamp: '2024-01-01T00:00:00Z',
          solar_wind_speed: 400,
          bz_field: -5,
          kp_index: 3,
          proton_flux: 1.5,
          source: 'NOAA'
        },
        success: true,
        timestamp: '2024-01-01T00:00:00Z'
      })

      renderHook(() => useCurrentData(5000))

      // Initial call
      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      expect(mockApiClient.fetchCurrentData).toHaveBeenCalledTimes(1)

      // Should call again after interval
      await act(async () => {
        jest.advanceTimersByTime(5000)
      })

      expect(mockApiClient.fetchCurrentData).toHaveBeenCalledTimes(2)
    })
  })

  describe('usePredictions', () => {
    it('should fetch predictions when input data is provided', async () => {
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

      mockApiClient.predictImpact.mockResolvedValue({
        data: mockPredictions,
        success: true,
        timestamp: '2024-01-01T00:00:00Z'
      })

      const { result } = renderHook(() => usePredictions(inputData))

      expect(result.current.loading).toBe(true)

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      expect(mockApiClient.predictImpact).toHaveBeenCalledWith(inputData)
      expect(result.current.loading).toBe(false)
      expect(result.current.data).toEqual(mockPredictions)
    })

    it('should not fetch predictions without input data', () => {
      const { result } = renderHook(() => usePredictions())

      expect(result.current.loading).toBe(false)
      expect(mockApiClient.predictImpact).not.toHaveBeenCalled()
    })
  })

  describe('useBacktest', () => {
    it('should run backtest for specified date', async () => {
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
        timeline: []
      }

      mockApiClient.runBacktest.mockResolvedValue({
        data: mockBacktestData,
        success: true,
        timestamp: '2024-01-01T00:00:00Z'
      })

      const { result } = renderHook(() => useBacktest())

      await act(async () => {
        await result.current.runBacktest(eventDate)
      })

      expect(mockApiClient.runBacktest).toHaveBeenCalledWith(eventDate)
      expect(result.current.data).toEqual(mockBacktestData)
      expect(result.current.loading).toBe(false)
    })
  })
})

describe('WebSocket Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useWebSocket', () => {
    it('should connect automatically when autoConnect is true', () => {
      mockWsClient.connect.mockResolvedValue()
      mockWsClient.getStatus.mockReturnValue('connected')

      const { result } = renderHook(() => useWebSocket(true))

      expect(mockWsClient.connect).toHaveBeenCalled()
      expect(mockWsClient.on).toHaveBeenCalledWith('connection', expect.any(Function))
      expect(mockWsClient.on).toHaveBeenCalledWith('message', expect.any(Function))
    })

    it('should not connect automatically when autoConnect is false', () => {
      mockWsClient.getStatus.mockReturnValue('disconnected')

      renderHook(() => useWebSocket(false))

      expect(mockWsClient.connect).not.toHaveBeenCalled()
    })

    it('should provide connection status', () => {
      const { result } = renderHook(() => useWebSocket(false))

      // Initially should be disconnected
      expect(result.current.connectionStatus).toBe('disconnected')
      expect(result.current.isConnected).toBe(false)

      // Simulate connection event by calling the handler that was registered
      const connectionHandler = mockWsClient.on.mock.calls.find(
        call => call[0] === 'connection'
      )?.[1]

      if (connectionHandler) {
        act(() => {
          connectionHandler({
            type: 'connection',
            data: { status: 'connected' },
            timestamp: '2024-01-01T00:00:00Z'
          })
        })

        expect(result.current.connectionStatus).toBe('connected')
        expect(result.current.isConnected).toBe(true)
      }
    })

    it('should provide send message function', () => {
      mockWsClient.send.mockReturnValue(true)

      const { result } = renderHook(() => useWebSocket(false))

      const testMessage = { type: 'test', data: 'hello' }
      const sent = result.current.sendMessage(testMessage)

      expect(sent).toBe(true)
      expect(mockWsClient.send).toHaveBeenCalledWith(testMessage)
    })

    it('should clean up on unmount', () => {
      const { unmount } = renderHook(() => useWebSocket(false))

      unmount()

      expect(mockWsClient.off).toHaveBeenCalledWith('connection', expect.any(Function))
      expect(mockWsClient.off).toHaveBeenCalledWith('message', expect.any(Function))
    })
  })
})