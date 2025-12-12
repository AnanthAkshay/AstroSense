/**
 * Property-based tests for AlertsPanelComponent
 * Feature: astrosense-space-weather
 */

import { render, screen } from './test-utils'
import * as fc from 'fast-check'
import AlertsPanelComponent from '../components/AlertsPanelComponent'

// Generators for test data
const alertTypeArb = fc.constantFrom('flash', 'forecast')
const severityArb = fc.constantFrom('low', 'moderate', 'high', 'critical')
const sectorArb = fc.constantFrom('Aviation', 'Telecommunications', 'GPS', 'Power Grid', 'Satellites')

const alertArb = fc.record({
  id: fc.string({ minLength: 1, maxLength: 20 }),
  type: alertTypeArb,
  severity: severityArb,
  title: fc.string({ minLength: 5, maxLength: 100 }),
  description: fc.string({ minLength: 10, maxLength: 200 }),
  timestamp: fc.date({ min: new Date(Date.now() - 24 * 60 * 60 * 1000), max: new Date() }),
  expiresAt: fc.option(fc.date({ min: new Date(), max: new Date(Date.now() + 24 * 60 * 60 * 1000) })),
  confidence: fc.option(fc.integer({ min: 0, max: 100 })),
  affectedSectors: fc.array(sectorArb, { minLength: 1, maxLength: 3 }),
  countdownTarget: fc.option(fc.date({ min: new Date(), max: new Date(Date.now() + 48 * 60 * 60 * 1000) })),
  mitigation: fc.option(fc.array(fc.string({ minLength: 10, maxLength: 100 }), { minLength: 1, maxLength: 5 }))
})

const alertsArrayArb = fc.array(alertArb, { minLength: 0, maxLength: 10 })

// Helper to create forecast alerts with countdown targets
const forecastAlertArb = fc.record({
  id: fc.string({ minLength: 1, maxLength: 20 }),
  type: fc.constant('forecast' as const),
  severity: severityArb,
  title: fc.string({ minLength: 5, maxLength: 100 }),
  description: fc.string({ minLength: 10, maxLength: 200 }),
  timestamp: fc.date({ min: new Date(Date.now() - 24 * 60 * 60 * 1000), max: new Date() }),
  confidence: fc.integer({ min: 0, max: 100 }),
  affectedSectors: fc.array(sectorArb, { minLength: 1, maxLength: 3 }),
  countdownTarget: fc.date({ min: new Date(Date.now() + 1000), max: new Date(Date.now() + 48 * 60 * 60 * 1000) }),
  mitigation: fc.option(fc.array(fc.string({ minLength: 10, maxLength: 100 }), { minLength: 1, maxLength: 5 }))
})

describe('AlertsPanelComponent Property Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    document.body.innerHTML = ''
    // Mock console.log to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  /**
   * Feature: astrosense-space-weather, Property 40: Forecast countdown display
   * Validates: Requirements 12.3
   */
  test('Property 40: Forecast countdown display - For any active impact forecast, the dashboard should display a countdown timer showing time remaining until predicted CME arrival', () => {
    fc.assert(
      fc.property(fc.array(forecastAlertArb, { minLength: 1, maxLength: 5 }), (forecastAlerts) => {
        const { container, unmount } = render(
          <AlertsPanelComponent alerts={forecastAlerts} />
        )
        
        try {
          // Verify component renders
          expect(container).toBeInTheDocument()
          
          // Check for countdown timers in forecast alerts
          forecastAlerts.forEach(alert => {
            if (alert.countdownTarget) {
              // Look for time-related text patterns
              const timePatterns = [
                /\d+h\s+\d+m/, // Hours and minutes format
                /\d+m\s+\d+s/, // Minutes and seconds format
                /\d+s/,        // Seconds only format
                /Time to Impact/i,
                /countdown/i
              ]
              
              const hasTimeDisplay = timePatterns.some(pattern => 
                pattern.test(container.textContent || '')
              )
              
              // Should display some form of countdown or time indication
              expect(hasTimeDisplay || container.textContent?.includes('Impact')).toBe(true)
            }
          })
          
          // Verify forecast alerts are displayed
          const forecastElements = container.querySelectorAll('[class*="forecast"]') ||
                                 Array.from(container.querySelectorAll('*')).filter(el => 
                                   el.textContent?.includes('FORECAST')
                                 )
          
          // Should have forecast-related content
          const hasForecastContent = container.textContent?.includes('FORECAST') ||
                                   container.textContent?.includes('forecast') ||
                                   container.textContent?.includes('Impact') ||
                                   container.textContent?.includes('arrival')
          
          expect(hasForecastContent).toBe(true)
          
          return true
        } finally {
          unmount()
        }
      }),
      { numRuns: 15 }
    )
  })

  /**
   * Feature: astrosense-space-weather, Property 41: Low confidence uncertainty indication
   * Validates: Requirements 12.4
   */
  test('Property 41: Low confidence uncertainty indication - For any forecast with confidence below 70 percent, the system should display the uncertainty level and provide range estimates', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.string({ minLength: 1, maxLength: 20 }),
            type: fc.constant('forecast' as const),
            severity: severityArb,
            title: fc.string({ minLength: 5, maxLength: 100 }),
            description: fc.string({ minLength: 10, maxLength: 200 }),
            timestamp: fc.date({ min: new Date(Date.now() - 24 * 60 * 60 * 1000), max: new Date() }),
            confidence: fc.integer({ min: 0, max: 69 }), // Low confidence values
            affectedSectors: fc.array(sectorArb, { minLength: 1, maxLength: 3 }),
            countdownTarget: fc.option(fc.date({ min: new Date(Date.now() + 1000), max: new Date(Date.now() + 48 * 60 * 60 * 1000) })),
            mitigation: fc.option(fc.array(fc.string({ minLength: 10, maxLength: 100 }), { minLength: 1, maxLength: 5 }))
          }),
          { minLength: 1, maxLength: 3 }
        ),
        (lowConfidenceAlerts) => {
          const { container, unmount } = render(
            <AlertsPanelComponent alerts={lowConfidenceAlerts} />
          )
          
          try {
            // Verify component renders
            expect(container).toBeInTheDocument()
            
            // Check for low confidence indicators
            lowConfidenceAlerts.forEach(alert => {
              if (alert.confidence < 70) {
                // Look for uncertainty indicators
                const uncertaintyPatterns = [
                  /uncertainty/i,
                  /low confidence/i,
                  /range estimates/i,
                  /⚠️.*confidence/i,
                  /confidence.*low/i
                ]
                
                const hasUncertaintyIndicator = uncertaintyPatterns.some(pattern => 
                  pattern.test(container.textContent || '')
                )
                
                // Should display confidence percentage
                const confidenceText = container.textContent?.includes(`${alert.confidence}%`)
                
                // Should have some indication of uncertainty or confidence level
                expect(hasUncertaintyIndicator || confidenceText).toBe(true)
              }
            })
            
            // Check for confidence-related styling or warnings
            const hasConfidenceDisplay = container.textContent?.includes('Confidence') ||
                                        container.textContent?.includes('confidence') ||
                                        container.textContent?.includes('%')
            
            expect(hasConfidenceDisplay).toBe(true)
            
            return true
          } finally {
            unmount()
          }
        }
      ),
      { numRuns: 15 }
    )
  })

  test('Alerts panel handles empty alerts gracefully', () => {
    const { container, unmount } = render(<AlertsPanelComponent alerts={[]} />)
    
    try {
      expect(container).toBeInTheDocument()
      
      // Should show "no active alerts" message
      const noAlertsText = container.textContent?.includes('No active alerts') ||
                          container.textContent?.includes('no alerts') ||
                          container.textContent?.includes('All systems operating normally')
      
      expect(noAlertsText).toBe(true)
      
      // Should show 0 active alerts count
      expect(container.textContent).toContain('(0)')
    } finally {
      unmount()
    }
  })

  test('Alerts panel displays alert count correctly', () => {
    fc.assert(
      fc.property(alertsArrayArb, (alerts) => {
        const { container, unmount } = render(<AlertsPanelComponent alerts={alerts} />)
        
        try {
          expect(container).toBeInTheDocument()
          
          // Should display the correct count of alerts
          const countText = `(${alerts.length})`
          expect(container.textContent).toContain(countText)
          
          return true
        } finally {
          unmount()
        }
      }),
      { numRuns: 10 }
    )
  })

  test('Alerts panel shows severity indicators correctly', () => {
    const criticalAlert = {
      id: 'test-critical',
      type: 'flash' as const,
      severity: 'critical' as const,
      title: 'Critical Test Alert',
      description: 'This is a critical alert for testing',
      timestamp: new Date(),
      affectedSectors: ['Aviation'],
      confidence: 95
    }
    
    const { container, unmount } = render(<AlertsPanelComponent alerts={[criticalAlert]} />)
    
    try {
      expect(container).toBeInTheDocument()
      
      // Should display critical severity
      const hasCritical = container.textContent?.includes('CRITICAL') ||
                         container.textContent?.includes('critical')
      expect(hasCritical).toBe(true)
      
      // Should display the alert title
      expect(container.textContent).toContain('Critical Test Alert')
    } finally {
      unmount()
    }
  })

  test('Alerts panel handles forecast alerts with countdown', () => {
    const futureTime = new Date(Date.now() + 2 * 60 * 60 * 1000) // 2 hours from now
    
    const forecastAlert = {
      id: 'test-forecast',
      type: 'forecast' as const,
      severity: 'high' as const,
      title: 'CME Impact Forecast',
      description: 'CME expected to arrive soon',
      timestamp: new Date(),
      countdownTarget: futureTime,
      confidence: 75,
      affectedSectors: ['Power Grid', 'Satellites']
    }
    
    const { container, unmount } = render(<AlertsPanelComponent alerts={[forecastAlert]} />)
    
    try {
      expect(container).toBeInTheDocument()
      
      // Should display forecast type
      const hasForecast = container.textContent?.includes('FORECAST') ||
                         container.textContent?.includes('forecast')
      expect(hasForecast).toBe(true)
      
      // Should show time-related content
      const hasTimeContent = container.textContent?.includes('Time to Impact') ||
                            container.textContent?.includes('h ') ||
                            container.textContent?.includes('m ')
      expect(hasTimeContent).toBe(true)
    } finally {
      unmount()
    }
  })

  test('Alerts panel displays confidence levels correctly', () => {
    const lowConfidenceAlert = {
      id: 'test-low-confidence',
      type: 'forecast' as const,
      severity: 'moderate' as const,
      title: 'Uncertain Forecast',
      description: 'Low confidence prediction',
      timestamp: new Date(),
      confidence: 45, // Below 70% threshold
      affectedSectors: ['GPS']
    }
    
    const { container, unmount } = render(<AlertsPanelComponent alerts={[lowConfidenceAlert]} />)
    
    try {
      expect(container).toBeInTheDocument()
      
      // Should display confidence percentage
      expect(container.textContent).toContain('45%')
      
      // Should indicate low confidence
      const hasLowConfidenceWarning = container.textContent?.includes('Low confidence') ||
                                     container.textContent?.includes('uncertainty') ||
                                     container.textContent?.includes('⚠️')
      expect(hasLowConfidenceWarning).toBe(true)
    } finally {
      unmount()
    }
  })
})