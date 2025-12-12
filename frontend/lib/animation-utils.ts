// Animation utilities for smooth data transitions
// Implements easing functions and transition helpers for live data updates

export type EasingFunction = (t: number) => number

// Easing functions for smooth animations
export const easingFunctions = {
  linear: (t: number) => t,
  easeInQuad: (t: number) => t * t,
  easeOutQuad: (t: number) => t * (2 - t),
  easeInOutQuad: (t: number) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
  easeInCubic: (t: number) => t * t * t,
  easeOutCubic: (t: number) => (--t) * t * t + 1,
  easeInOutCubic: (t: number) => t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
  easeOutElastic: (t: number) => {
    const c4 = (2 * Math.PI) / 3
    return t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1
  }
}

// Animate a numeric value from start to end
export function animateValue(
  start: number,
  end: number,
  duration: number,
  easing: EasingFunction = easingFunctions.easeOutQuad,
  onUpdate: (value: number) => void,
  onComplete?: () => void
): () => void {
  const startTime = performance.now()
  let animationId: number

  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    const easedProgress = easing(progress)
    const currentValue = start + (end - start) * easedProgress
    
    onUpdate(currentValue)
    
    if (progress < 1) {
      animationId = requestAnimationFrame(animate)
    } else {
      onComplete?.()
    }
  }
  
  animationId = requestAnimationFrame(animate)
  
  // Return cancel function
  return () => {
    if (animationId) {
      cancelAnimationFrame(animationId)
    }
  }
}

// Animate multiple values simultaneously
export function animateMultipleValues(
  values: Array<{ start: number; end: number; onUpdate: (value: number) => void }>,
  duration: number,
  easing: EasingFunction = easingFunctions.easeOutQuad,
  onComplete?: () => void
): () => void {
  const startTime = performance.now()
  let animationId: number

  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    const easedProgress = easing(progress)
    
    values.forEach(({ start, end, onUpdate }) => {
      const currentValue = start + (end - start) * easedProgress
      onUpdate(currentValue)
    })
    
    if (progress < 1) {
      animationId = requestAnimationFrame(animate)
    } else {
      onComplete?.()
    }
  }
  
  animationId = requestAnimationFrame(animate)
  
  return () => {
    if (animationId) {
      cancelAnimationFrame(animationId)
    }
  }
}

// Stagger animations for multiple elements
export function staggerAnimation(
  elements: Array<() => void>,
  staggerDelay: number = 100
): () => void {
  const timeouts: NodeJS.Timeout[] = []
  
  elements.forEach((animate, index) => {
    const timeout = setTimeout(() => {
      animate()
    }, index * staggerDelay)
    
    timeouts.push(timeout)
  })
  
  return () => {
    timeouts.forEach(timeout => clearTimeout(timeout))
  }
}

// Smooth color transitions
export function interpolateColor(
  startColor: string,
  endColor: string,
  progress: number
): string {
  // Convert hex colors to RGB
  const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 }
  }
  
  const start = hexToRgb(startColor)
  const end = hexToRgb(endColor)
  
  const r = Math.round(start.r + (end.r - start.r) * progress)
  const g = Math.round(start.g + (end.g - start.g) * progress)
  const b = Math.round(start.b + (end.b - start.b) * progress)
  
  return `rgb(${r}, ${g}, ${b})`
}

// Create a spring animation for bouncy effects
export function createSpringAnimation(
  tension: number = 120,
  friction: number = 14,
  mass: number = 1
): EasingFunction {
  return (t: number) => {
    const w = Math.sqrt(tension / mass)
    const zeta = friction / (2 * Math.sqrt(tension * mass))
    
    if (zeta < 1) {
      // Underdamped
      const wd = w * Math.sqrt(1 - zeta * zeta)
      return 1 - Math.exp(-zeta * w * t) * Math.cos(wd * t)
    } else {
      // Overdamped or critically damped
      return 1 - Math.exp(-w * t)
    }
  }
}

// Pulse animation for highlighting updates
export function createPulseEffect(
  element: HTMLElement,
  duration: number = 300,
  intensity: number = 0.2
): () => void {
  const originalOpacity = element.style.opacity || '1'
  const targetOpacity = (parseFloat(originalOpacity) + intensity).toString()
  
  return animateValue(
    parseFloat(originalOpacity),
    parseFloat(targetOpacity),
    duration / 2,
    easingFunctions.easeOutQuad,
    (value) => {
      element.style.opacity = value.toString()
    },
    () => {
      // Animate back to original
      animateValue(
        parseFloat(targetOpacity),
        parseFloat(originalOpacity),
        duration / 2,
        easingFunctions.easeInQuad,
        (value) => {
          element.style.opacity = value.toString()
        }
      )
    }
  )
}

// Scale animation for card updates
export function createScaleEffect(
  element: HTMLElement,
  duration: number = 300,
  maxScale: number = 1.05
): () => void {
  const originalTransform = element.style.transform || 'scale(1)'
  
  return animateValue(
    1,
    maxScale,
    duration / 2,
    easingFunctions.easeOutQuad,
    (value) => {
      element.style.transform = `scale(${value})`
    },
    () => {
      // Animate back to original
      animateValue(
        maxScale,
        1,
        duration / 2,
        easingFunctions.easeInQuad,
        (value) => {
          element.style.transform = `scale(${value})`
        },
        () => {
          element.style.transform = originalTransform
        }
      )
    }
  )
}

// Smooth number transitions for counters
export function animateCounter(
  element: HTMLElement,
  start: number,
  end: number,
  duration: number = 1000,
  decimals: number = 0,
  suffix: string = ''
): () => void {
  return animateValue(
    start,
    end,
    duration,
    easingFunctions.easeOutCubic,
    (value) => {
      element.textContent = value.toFixed(decimals) + suffix
    }
  )
}

// Fade transition for content updates
export function fadeTransition(
  element: HTMLElement,
  newContent: string | HTMLElement,
  duration: number = 300
): Promise<void> {
  return new Promise((resolve) => {
    // Fade out
    animateValue(
      1,
      0,
      duration / 2,
      easingFunctions.easeInQuad,
      (value) => {
        element.style.opacity = value.toString()
      },
      () => {
        // Update content
        if (typeof newContent === 'string') {
          element.textContent = newContent
        } else {
          element.innerHTML = ''
          element.appendChild(newContent)
        }
        
        // Fade in
        animateValue(
          0,
          1,
          duration / 2,
          easingFunctions.easeOutQuad,
          (value) => {
            element.style.opacity = value.toString()
          },
          () => {
            resolve()
          }
        )
      }
    )
  })
}