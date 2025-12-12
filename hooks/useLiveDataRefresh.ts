'use client'

import { useCallback, useRef, useState, useEffect } from 'react'

interface LiveDataRefreshOptions {
  animationDuration?: number
  updateQueueDelay?: number
  maxQueueSize?: number
  onUpdateStart?: () => void
  onUpdateComplete?: () => void
  onUserInteractionDetected?: () => void
}

interface QueuedUpdate {
  id: string
  data: any
  timestamp: number
  priority: 'low' | 'normal' | 'high'
}

export function useLiveDataRefresh(options: LiveDataRefreshOptions = {}) {
  const {
    animationDuration = 300,
    updateQueueDelay = 1000,
    maxQueueSize = 10,
    onUpdateStart,
    onUpdateComplete,
    onUserInteractionDetected
  } = options

  const [isUpdating, setIsUpdating] = useState(false)
  const [isUserInteracting, setIsUserInteracting] = useState(false)
  const [queuedUpdates, setQueuedUpdates] = useState<QueuedUpdate[]>([])
  
  const updateQueueRef = useRef<QueuedUpdate[]>([])
  const userInteractionTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const updateTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  // Track user interactions
  const handleUserInteraction = useCallback(() => {
    setIsUserInteracting(true)
    onUserInteractionDetected?.()
    
    // Clear existing timeout
    if (userInteractionTimeoutRef.current) {
      clearTimeout(userInteractionTimeoutRef.current)
    }
    
    // Set timeout to end user interaction state
    userInteractionTimeoutRef.current = setTimeout(() => {
      setIsUserInteracting(false)
      processQueuedUpdates()
    }, updateQueueDelay)
  }, [updateQueueDelay, onUserInteractionDetected])

  // Add event listeners for user interactions
  useEffect(() => {
    const events = ['mousedown', 'mousemove', 'wheel', 'touchstart', 'touchmove', 'keydown']
    
    events.forEach(event => {
      document.addEventListener(event, handleUserInteraction, { passive: true })
    })
    
    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleUserInteraction)
      })
    }
  }, [handleUserInteraction])

  // Process queued updates
  const processQueuedUpdates = useCallback(() => {
    if (updateQueueRef.current.length === 0 || isUserInteracting || isUpdating) {
      return
    }

    // Sort by priority and timestamp
    const sortedUpdates = [...updateQueueRef.current].sort((a, b) => {
      const priorityOrder = { high: 3, normal: 2, low: 1 }
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority]
      if (priorityDiff !== 0) return priorityDiff
      return a.timestamp - b.timestamp
    })

    // Process the highest priority update
    const nextUpdate = sortedUpdates[0]
    if (nextUpdate) {
      executeUpdate(nextUpdate)
      updateQueueRef.current = updateQueueRef.current.filter(u => u.id !== nextUpdate.id)
      setQueuedUpdates([...updateQueueRef.current])
    }
  }, [isUserInteracting, isUpdating])

  // Execute a single update with smooth animation
  const executeUpdate = useCallback((update: QueuedUpdate) => {
    setIsUpdating(true)
    onUpdateStart?.()

    // Use requestAnimationFrame for smooth animations
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }

    animationFrameRef.current = requestAnimationFrame(() => {
      // Trigger the actual update
      // This would be handled by the component using this hook
      
      // Complete the update after animation duration
      setTimeout(() => {
        setIsUpdating(false)
        onUpdateComplete?.()
        
        // Process next update if available
        setTimeout(() => {
          processQueuedUpdates()
        }, 50) // Small delay between updates
      }, animationDuration)
    })
  }, [animationDuration, onUpdateStart, onUpdateComplete, processQueuedUpdates])

  // Queue an update
  const queueUpdate = useCallback((data: any, priority: 'low' | 'normal' | 'high' = 'normal') => {
    const update: QueuedUpdate = {
      id: `${Date.now()}-${Math.random()}`,
      data,
      timestamp: Date.now(),
      priority
    }

    // Add to queue if not at max capacity
    if (updateQueueRef.current.length < maxQueueSize) {
      updateQueueRef.current.push(update)
      setQueuedUpdates([...updateQueueRef.current])
    } else {
      // Replace lowest priority update if queue is full
      const lowestPriorityIndex = updateQueueRef.current.findIndex(u => u.priority === 'low')
      if (lowestPriorityIndex !== -1 && priority !== 'low') {
        updateQueueRef.current[lowestPriorityIndex] = update
        setQueuedUpdates([...updateQueueRef.current])
      }
    }

    // Process immediately if not user interacting (with small delay for testing)
    if (!isUserInteracting && !isUpdating) {
      setTimeout(() => {
        processQueuedUpdates()
      }, 10) // Small delay to allow tests to check queue state
    }
  }, [maxQueueSize, isUserInteracting, isUpdating, processQueuedUpdates])

  // Force update (bypasses queue)
  const forceUpdate = useCallback((data: any) => {
    const update: QueuedUpdate = {
      id: `force-${Date.now()}`,
      data,
      timestamp: Date.now(),
      priority: 'high'
    }
    
    executeUpdate(update)
  }, [executeUpdate])

  // Clear queue
  const clearQueue = useCallback(() => {
    updateQueueRef.current = []
    setQueuedUpdates([])
  }, [])

  // Get queue status
  const getQueueStatus = useCallback(() => {
    return {
      size: updateQueueRef.current.length,
      isProcessing: isUpdating,
      isUserInteracting,
      nextUpdate: updateQueueRef.current[0] || null
    }
  }, [isUpdating, isUserInteracting])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (userInteractionTimeoutRef.current) {
        clearTimeout(userInteractionTimeoutRef.current)
      }
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current)
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [])

  return {
    // State
    isUpdating,
    isUserInteracting,
    queuedUpdates,
    
    // Actions
    queueUpdate,
    forceUpdate,
    clearQueue,
    
    // Status
    getQueueStatus,
    
    // Manual interaction control
    setUserInteracting: setIsUserInteracting
  }
}