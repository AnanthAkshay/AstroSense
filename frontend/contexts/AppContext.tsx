'use client'

import React, { createContext, useContext, useReducer, ReactNode } from 'react'
import { SpaceWeatherData, SectorPredictions } from '@/lib/api-client'

// State interface
export interface AppState {
  currentData: SpaceWeatherData | null
  predictions: SectorPredictions | null
  alerts: Alert[]
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  isBacktestMode: boolean
  backtestDate: string | null
  theme: 'dark' | 'light'
  notifications: Notification[]
}

export interface Alert {
  id: string
  type: 'flash' | 'forecast' | 'warning'
  severity: 'low' | 'moderate' | 'high' | 'critical'
  title: string
  message: string
  timestamp: string
  expiresAt: string
  sectors: string[]
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  autoHide?: boolean
}

// Action types
export type AppAction =
  | { type: 'SET_CURRENT_DATA'; payload: SpaceWeatherData }
  | { type: 'SET_PREDICTIONS'; payload: SectorPredictions }
  | { type: 'ADD_ALERT'; payload: Alert }
  | { type: 'REMOVE_ALERT'; payload: string }
  | { type: 'SET_CONNECTION_STATUS'; payload: AppState['connectionStatus'] }
  | { type: 'TOGGLE_BACKTEST_MODE'; payload?: string }
  | { type: 'SET_THEME'; payload: 'dark' | 'light' }
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_EXPIRED_ALERTS' }

// Initial state
const initialState: AppState = {
  currentData: null,
  predictions: null,
  alerts: [],
  connectionStatus: 'disconnected',
  isBacktestMode: false,
  backtestDate: null,
  theme: 'dark',
  notifications: [],
}

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_CURRENT_DATA':
      return {
        ...state,
        currentData: action.payload,
      }

    case 'SET_PREDICTIONS':
      return {
        ...state,
        predictions: action.payload,
      }

    case 'ADD_ALERT':
      return {
        ...state,
        alerts: [action.payload, ...state.alerts].slice(0, 50), // Keep max 50 alerts
      }

    case 'REMOVE_ALERT':
      return {
        ...state,
        alerts: state.alerts.filter(alert => alert.id !== action.payload),
      }

    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        connectionStatus: action.payload,
      }

    case 'TOGGLE_BACKTEST_MODE':
      return {
        ...state,
        isBacktestMode: !state.isBacktestMode,
        backtestDate: action.payload || null,
      }

    case 'SET_THEME':
      return {
        ...state,
        theme: action.payload,
      }

    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [action.payload, ...state.notifications].slice(0, 10), // Keep max 10 notifications
      }

    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(notif => notif.id !== action.payload),
      }

    case 'CLEAR_EXPIRED_ALERTS':
      const now = new Date().toISOString()
      return {
        ...state,
        alerts: state.alerts.filter(alert => alert.expiresAt > now),
      }

    default:
      return state
  }
}

// Context
const AppContext = createContext<{
  state: AppState
  dispatch: React.Dispatch<AppAction>
} | null>(null)

// Provider component
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState)

  // Auto-clear expired alerts every minute
  React.useEffect(() => {
    const interval = setInterval(() => {
      dispatch({ type: 'CLEAR_EXPIRED_ALERTS' })
    }, 60000)

    return () => clearInterval(interval)
  }, [])

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

// Hook to use the context
export function useAppContext() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider')
  }
  return context
}

// Helper hooks for specific state slices
export function useCurrentData() {
  const { state } = useAppContext()
  return state.currentData
}

export function usePredictionsData() {
  const { state } = useAppContext()
  return state.predictions
}

export function useAlerts() {
  const { state } = useAppContext()
  return state.alerts
}

export function useConnectionStatus() {
  const { state } = useAppContext()
  return state.connectionStatus
}

export function useBacktestMode() {
  const { state, dispatch } = useAppContext()
  
  const toggleBacktest = (date?: string) => {
    dispatch({ type: 'TOGGLE_BACKTEST_MODE', payload: date })
  }

  return {
    isBacktestMode: state.isBacktestMode,
    backtestDate: state.backtestDate,
    toggleBacktest,
  }
}

export function useNotifications() {
  const { state, dispatch } = useAppContext()
  
  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
    }
    dispatch({ type: 'ADD_NOTIFICATION', payload: newNotification })
    
    // Auto-hide after 5 seconds if autoHide is true
    if (notification.autoHide !== false) {
      setTimeout(() => {
        dispatch({ type: 'REMOVE_NOTIFICATION', payload: newNotification.id })
      }, 5000)
    }
  }

  const removeNotification = (id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id })
  }

  return {
    notifications: state.notifications,
    addNotification,
    removeNotification,
  }
}