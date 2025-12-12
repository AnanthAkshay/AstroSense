# AstroSense Frontend API Client

This directory contains the complete API client implementation for backend communication in the AstroSense space weather application.

## Overview

The API client provides:
- **REST API wrappers** for all backend endpoints
- **WebSocket client** for real-time streaming
- **Error handling and reconnection** logic
- **Data caching and state management** utilities

## Files

### Core API Client (`api-client.ts`)
- Implements fetch wrappers for REST endpoints
- Provides response caching with configurable TTL
- Handles errors gracefully with proper error reporting
- Supports all required endpoints:
  - `POST /api/predict-impact` - Get sector-specific predictions
  - `GET /api/fetch-data` - Retrieve current space weather data
  - `POST /api/backtest` - Run historical event replay

### WebSocket Client (`websocket-client.ts`)
- Manages WebSocket connections for real-time updates
- Implements automatic reconnection with exponential backoff
- Provides event-based message handling
- Includes connection timeout and heartbeat functionality
- Supports multiple event listeners per message type

### React Hooks (`../hooks/`)
- `useApiData.ts` - Hooks for API data fetching with loading states
- `useWebSocket.ts` - Hook for WebSocket connection management

### State Management (`../contexts/`)
- `AppContext.tsx` - Global application state management
- Handles alerts, notifications, connection status, and backtest mode

## Usage Examples

### Basic API Calls

```typescript
import { apiClient } from '@/lib/api-client'

// Fetch current space weather data
const response = await apiClient.fetchCurrentData()
if (response.success) {
  console.log('Current data:', response.data)
}

// Get predictions
const predictions = await apiClient.predictImpact({
  solar_wind_speed: 500,
  bz_field: -10,
  kp_index: 5
})

// Run backtest
const backtest = await apiClient.runBacktest('2024-05-10')
```

### WebSocket Real-time Updates

```typescript
import { wsClient } from '@/lib/websocket-client'

// Connect to WebSocket
await wsClient.connect()

// Listen for space weather updates
wsClient.on('space_weather_update', (message) => {
  console.log('New data:', message.data)
})

// Listen for alerts
wsClient.on('alert', (message) => {
  console.log('Alert:', message.data)
})
```

### React Hooks

```typescript
import { useCurrentData, usePredictions } from '@/hooks/useApiData'
import { useWebSocket } from '@/hooks/useWebSocket'

function MyComponent() {
  // Auto-refreshing current data
  const { data, loading, error } = useCurrentData(30000) // 30 second refresh
  
  // WebSocket connection
  const { isConnected, lastMessage } = useWebSocket()
  
  // Predictions based on input
  const { data: predictions } = usePredictions(inputData)
  
  return (
    <div>
      {loading ? 'Loading...' : JSON.stringify(data)}
      <div>WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</div>
    </div>
  )
}
```

### State Management

```typescript
import { useAppContext } from '@/contexts/AppContext'

function AlertsComponent() {
  const { state, dispatch } = useAppContext()
  
  const addAlert = () => {
    dispatch({
      type: 'ADD_ALERT',
      payload: {
        id: Date.now().toString(),
        type: 'flash',
        severity: 'high',
        title: 'Solar Flare Detected',
        message: 'X-class flare detected',
        timestamp: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
        sectors: ['aviation']
      }
    })
  }
  
  return (
    <div>
      <button onClick={addAlert}>Add Alert</button>
      {state.alerts.map(alert => (
        <div key={alert.id}>{alert.title}</div>
      ))}
    </div>
  )
}
```

## Configuration

The API client uses environment variables for configuration:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/stream
NEXT_PUBLIC_API_TIMEOUT=30000
NEXT_PUBLIC_CACHE_TTL=60000
NEXT_PUBLIC_WS_RECONNECT_ATTEMPTS=10
```

## Features

### Error Handling
- Automatic retry logic for failed requests
- Graceful degradation on network errors
- Proper error reporting with context
- Connection timeout handling

### Caching
- Response caching with configurable TTL
- Different cache durations per endpoint:
  - Current data: 10 seconds
  - Predictions: 30 seconds
  - Backtest: 5 minutes
- Cache management utilities (clear, stats)

### Real-time Updates
- WebSocket connection with auto-reconnect
- Exponential backoff for reconnection attempts
- Heartbeat to maintain connection
- Event-based message handling
- Connection status monitoring

### State Management
- Centralized application state
- Alert and notification management
- Connection status tracking
- Backtest mode support
- Theme management

## Requirements Validation

This implementation satisfies the following requirements:

**Requirement 15.1**: ✅ REST API endpoints
- Implements fetch wrappers for all required endpoints
- Returns JSON responses with proper error handling
- Includes CORS headers and rate limiting support

**Requirement 17.1**: ✅ Real-time streaming
- WebSocket client for real-time updates
- Automatic reconnection with exponential backoff
- Event-based message handling
- Connection establishment within 2 seconds

## Testing

The implementation includes comprehensive tests:
- Unit tests for API client functionality
- Integration tests for WebSocket behavior
- Mock implementations for testing
- Error scenario coverage
- State management validation

Run tests with:
```bash
npm test -- --watchAll=false api-integration
```

## Architecture

The API client follows a layered architecture:

1. **Transport Layer**: HTTP fetch and WebSocket connections
2. **Client Layer**: API client and WebSocket client classes
3. **Hook Layer**: React hooks for component integration
4. **State Layer**: Context providers for global state
5. **Component Layer**: React components using the hooks

This separation ensures clean abstractions and testability while providing a simple interface for React components.