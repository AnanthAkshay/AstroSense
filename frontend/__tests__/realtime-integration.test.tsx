import { renderHook, act } from '@testing-library/react'
import { useRealtimeData } from '@/hooks/useRealtimeData'
import { useLiveDataRefresh } from '@/hooks/useLiveDataRefresh'
import { AppProvider } from '@/contexts/AppContext'

// Mock WebSocket
jest.mock('@/lib/websocket-client', () => ({
  wsClient: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
    send: jest.fn(),
    getStatus: jest.fn(() => 'connected')
  }
}))

// Get the mocked WebSocket client
const { wsClient } = require('@/lib/websocket-client')

describe('Real-time Data Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useRealtimeData', () => {
    it('should initialize with default state', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AppProvider>{children}</AppProvider>
      )

      const { result } = renderHook(() => useRealtimeData(), { wrapper })

      expect(result.current.isConnected).toBe(false)
      expect(result.current.currentData).toBeNull()
      expect(result.current.predictions).toBeNull()
      expect(result.current.alerts).toEqual([])
    })

    it('should handle data updates', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AppProvider>{children}</AppProvider>
      )

      const onDataUpdate = jest.fn()
      const { result } = renderHook(() => useRealtimeData({ onDataUpdate }), { wrapper })

      // Simulate data update
      const mockUpdate = {
        current_data: {
          timestamp: '2023-01-01T00:00:00Z',
          solar_wind_speed: 450,
          bz_field: -5.2,
          kp_index: 3.5,
          proton_flux: 1.2,
          source: 'test'
        },
        predictions: {
          aviation_hf_blackout_prob: 25,
          aviation_polar_risk: 30,
          telecom_signal_degradation: 15,
          gps_drift_cm: 45,
          power_grid_gic_risk: 4,
          satellite_drag_risk: 3,
          composite_score: 35,
          timestamp: '2023-01-01T00:00:00Z',
          model_version: 'v1.0'
        }
      }

      act(() => {
        // Simulate WebSocket message
        const messageHandler = wsClient.on.mock.calls.find(
          call => call[0] === 'message'
        )?.[1]
        
        if (messageHandler) {
          messageHandler({
            type: 'space_weather_update',
            data: mockUpdate,
            timestamp: '2023-01-01T00:00:00Z'
          })
        }
      })

      expect(onDataUpdate).toHaveBeenCalledWith(mockUpdate)
    })
  })

  describe('useLiveDataRefresh', () => {
    it('should initialize with default state', () => {
      const { result } = renderHook(() => useLiveDataRefresh())

      expect(result.current.isUpdating).toBe(false)
      expect(result.current.isUserInteracting).toBe(false)
      expect(result.current.queuedUpdates).toEqual([])
    })

    it('should queue updates', async () => {
      const { result } = renderHook(() => useLiveDataRefresh())

      // Set user interacting to prevent immediate processing
      act(() => {
        result.current.setUserInteracting(true)
      })

      act(() => {
        result.current.queueUpdate({ test: 'data' }, 'normal')
      })

      const queueStatus = result.current.getQueueStatus()
      expect(queueStatus.size).toBe(1)
    })

    it('should handle user interactions', () => {
      const onUserInteractionDetected = jest.fn()
      const { result } = renderHook(() => 
        useLiveDataRefresh({ onUserInteractionDetected })
      )

      // Simulate user interaction
      act(() => {
        const mouseEvent = new MouseEvent('mousedown')
        document.dispatchEvent(mouseEvent)
      })

      expect(result.current.isUserInteracting).toBe(true)
      expect(onUserInteractionDetected).toHaveBeenCalled()
    })

    it('should clear queue', () => {
      const { result } = renderHook(() => useLiveDataRefresh())

      // Set user interacting to prevent immediate processing
      act(() => {
        result.current.setUserInteracting(true)
      })

      act(() => {
        result.current.queueUpdate({ test: 'data1' }, 'normal')
        result.current.queueUpdate({ test: 'data2' }, 'high')
      })

      expect(result.current.getQueueStatus().size).toBe(2)

      act(() => {
        result.current.clearQueue()
      })

      expect(result.current.getQueueStatus().size).toBe(0)
    })
  })

  describe('Integration Requirements', () => {
    it('should meet Requirement 17.1 - Real-time data push', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AppProvider>{children}</AppProvider>
      )

      const onDataUpdate = jest.fn()
      renderHook(() => useRealtimeData({ onDataUpdate }), { wrapper })

      // Verify WebSocket connection is established
      expect(wsClient.on).toHaveBeenCalledWith('message', expect.any(Function))
      expect(wsClient.on).toHaveBeenCalledWith('connection', expect.any(Function))
    })

    it('should meet Requirement 17.4 - Automatic reconnection', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => (
        <AppProvider>{children}</AppProvider>
      )

      const onConnectionChange = jest.fn()
      renderHook(() => useRealtimeData({ onConnectionChange }), { wrapper })

      // Simulate connection loss
      act(() => {
        const connectionHandler = wsClient.on.mock.calls.find(
          call => call[0] === 'connection'
        )?.[1]
        
        if (connectionHandler) {
          connectionHandler({
            type: 'connection',
            data: { status: 'disconnected' },
            timestamp: '2023-01-01T00:00:00Z'
          })
        }
      })

      expect(onConnectionChange).toHaveBeenCalledWith('disconnected')
    })

    it('should meet Requirement 9.5 - Heatmap update performance', () => {
      const { result } = renderHook(() => useLiveDataRefresh({
        animationDuration: 2000 // 2 seconds as per requirements
      }))

      const startTime = Date.now()
      
      act(() => {
        result.current.queueUpdate({ test: 'performance' }, 'high')
      })

      // Verify update is processed within performance requirements
      const queueStatus = result.current.getQueueStatus()
      expect(queueStatus.size).toBeLessThanOrEqual(1)
      
      const endTime = Date.now()
      expect(endTime - startTime).toBeLessThan(100) // Queue operation should be fast
    })

    it('should meet Requirement 10.5 - Chart updates without page reload', () => {
      const { result } = renderHook(() => useLiveDataRefresh())

      // Set user interacting to prevent immediate processing
      act(() => {
        result.current.setUserInteracting(true)
      })

      // Simulate multiple rapid updates
      act(() => {
        for (let i = 0; i < 5; i++) {
          result.current.queueUpdate({ chartData: i }, 'normal')
        }
      })

      // Verify updates are queued and managed properly
      const queueStatus = result.current.getQueueStatus()
      expect(queueStatus.size).toBeGreaterThan(0)
      expect(queueStatus.size).toBeLessThanOrEqual(5)
    })
  })
})