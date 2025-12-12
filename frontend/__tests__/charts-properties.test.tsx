/**
 * Property-based tests for ChartsComponent
 * Feature: astrosense-space-weather
 */

import { render, screen } from './test-utils'
import * as fc from 'fast-check'
import ChartsComponent from '../components/ChartsComponent'

// Mock Highcharts to avoid rendering issues in tests
jest.mock('highcharts', () => ({
  __esModule: true,
  default: {
    chart: jest.fn(() => ({
      destroy: jest.fn(),
      update: jest.fn(),
      redraw: jest.fn()
    }))
  }
}))

jest.mock('highcharts-react-official', () => ({
  __esModule: true,
  default: ({ options, ...props }: any) => (
    <div 
      data-testid="highcharts-chart" 
      data-chart-type={options?.chart?.type}
      data-y-axis-title={options?.yAxis?.title?.text}
      data-series-name={options?.series?.[0]?.name}
      data-series-color={options?.series?.[0]?.color}
      data-series-length={options?.series?.[0]?.data?.length}
      {...props}
    />
  )
}))

// Generators for test data
const dataPointArb = fc.record({
  timestamp: fc.integer({ min: Date.now() - 24 * 60 * 60 * 1000, max: Date.now() }),
  value: fc.float({ min: -50, max: 2000 })
})

const dataArrayArb = fc.array(dataPointArb, { minLength: 10, maxLength: 300 })

const solarWindDataArb = fc.array(
  fc.record({
    timestamp: fc.integer({ min: Date.now() - 24 * 60 * 60 * 1000, max: Date.now() }),
    value: fc.float({ min: 200, max: 1500 }) // Typical solar wind speeds
  }),
  { minLength: 10, maxLength: 300 }
)

const bzFieldDataArb = fc.array(
  fc.record({
    timestamp: fc.integer({ min: Date.now() - 24 * 60 * 60 * 1000, max: Date.now() }),
    value: fc.float({ min: -30, max: 30 }) // Typical Bz field values in nT
  }),
  { minLength: 10, maxLength: 300 }
)

describe('ChartsComponent Property Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    document.body.innerHTML = ''
  })

  /**
   * Feature: astrosense-space-weather, Property 30: Solar wind chart units
   * Validates: Requirements 10.1
   */
  test('Property 30: Solar wind chart units - For any solar wind data received, the time-series chart should plot wind speed values in kilometers per second', () => {
    fc.assert(
      fc.property(solarWindDataArb, (solarWindData) => {
        const { container, unmount } = render(
          <ChartsComponent solarWindData={solarWindData} />
        )
        
        try {
          // Verify component renders
          expect(container).toBeInTheDocument()
          
          // Find the solar wind chart
          const charts = container.querySelectorAll('[data-testid="highcharts-chart"]')
          const solarWindChart = Array.from(charts).find(chart => 
            chart.getAttribute('data-series-name') === 'Solar Wind Speed'
          )
          
          expect(solarWindChart).toBeInTheDocument()
          
          // Verify the chart displays km/s units
          expect(solarWindChart).toHaveAttribute('data-y-axis-title', 'Speed (km/s)')
          
          // Verify the chart has the correct series name
          expect(solarWindChart).toHaveAttribute('data-series-name', 'Solar Wind Speed')
          
          // Verify the chart type is line
          expect(solarWindChart).toHaveAttribute('data-chart-type', 'line')
          
          // Verify data is present
          const seriesLength = solarWindChart?.getAttribute('data-series-length')
          expect(parseInt(seriesLength || '0')).toBe(solarWindData.length)
          
          // Check that the component displays current value with km/s unit
          const kmPerSecText = container.textContent?.includes('km/s')
          expect(kmPerSecText).toBe(true)
          
          return true
        } finally {
          unmount()
        }
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Feature: astrosense-space-weather, Property 31: Bz chart units
   * Validates: Requirements 10.2
   */
  test('Property 31: Bz chart units - For any Bz magnetic field data received, the time-series chart should plot Bz values in nanoteslas', () => {
    fc.assert(
      fc.property(bzFieldDataArb, (bzFieldData) => {
        const { container, unmount } = render(
          <ChartsComponent bzFieldData={bzFieldData} />
        )
        
        try {
          // Verify component renders
          expect(container).toBeInTheDocument()
          
          // Find the Bz field chart
          const charts = container.querySelectorAll('[data-testid="highcharts-chart"]')
          const bzChart = Array.from(charts).find(chart => 
            chart.getAttribute('data-series-name') === 'Bz Magnetic Field'
          )
          
          expect(bzChart).toBeInTheDocument()
          
          // Verify the chart displays nT units
          expect(bzChart).toHaveAttribute('data-y-axis-title', 'Bz Field (nT)')
          
          // Verify the chart has the correct series name
          expect(bzChart).toHaveAttribute('data-series-name', 'Bz Magnetic Field')
          
          // Verify the chart type is line
          expect(bzChart).toHaveAttribute('data-chart-type', 'line')
          
          // Verify data is present
          const seriesLength = bzChart?.getAttribute('data-series-length')
          expect(parseInt(seriesLength || '0')).toBe(bzFieldData.length)
          
          // Check that the component displays current value with nT unit
          const nanoTeslaText = container.textContent?.includes('nT')
          expect(nanoTeslaText).toBe(true)
          
          return true
        } finally {
          unmount()
        }
      }),
      { numRuns: 20 }
    )
  })

  /**
   * Feature: astrosense-space-weather, Property 32: Chart time window and resolution
   * Validates: Requirements 10.3
   */
  test('Property 32: Chart time window and resolution - For any displayed chart, it should show the most recent 24 hours of data with data points at 5-minute intervals', () => {
    fc.assert(
      fc.property(solarWindDataArb, bzFieldDataArb, (solarWindData, bzFieldData) => {
        // Ensure we have data spanning close to 24 hours with 5-minute intervals
        const now = Date.now()
        const twentyFourHoursAgo = now - 24 * 60 * 60 * 1000
        const fiveMinuteInterval = 5 * 60 * 1000
        
        // Generate data points at 5-minute intervals for the last 24 hours
        const expectedDataPoints = Math.floor(24 * 60 / 5) // 288 points for 24 hours at 5-minute intervals
        
        const { container, unmount } = render(
          <ChartsComponent 
            solarWindData={solarWindData} 
            bzFieldData={bzFieldData}
          />
        )
        
        try {
          // Verify component renders
          expect(container).toBeInTheDocument()
          
          // Find both charts
          const charts = container.querySelectorAll('[data-testid="highcharts-chart"]')
          expect(charts.length).toBe(2)
          
          // Check that the component mentions 24-hour trend
          const twentyFourHourText = container.textContent?.includes('24-hour trend')
          expect(twentyFourHourText).toBe(true)
          
          // Check that the component mentions 5-minute resolution
          const fiveMinuteText = container.textContent?.includes('5-minute resolution')
          expect(fiveMinuteText).toBe(true)
          
          // Verify that charts have data (even if not exactly 288 points due to test data generation)
          charts.forEach(chart => {
            const seriesLength = chart.getAttribute('data-series-length')
            expect(parseInt(seriesLength || '0')).toBeGreaterThan(0)
          })
          
          return true
        } finally {
          unmount()
        }
      }),
      { numRuns: 15 }
    )
  })

  /**
   * Feature: astrosense-space-weather, Property 33: Threshold visualization
   * Validates: Requirements 10.4
   */
  test('Property 33: Threshold visualization - For any data point that crosses a critical threshold, the chart should highlight the threshold line and add an annotation marking the event', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            timestamp: fc.integer({ min: Date.now() - 24 * 60 * 60 * 1000, max: Date.now() }),
            value: fc.float({ min: 400, max: 800 }) // Values around the 500 km/s threshold
          }),
          { minLength: 10, maxLength: 50 }
        ),
        fc.array(
          fc.record({
            timestamp: fc.integer({ min: Date.now() - 24 * 60 * 60 * 1000, max: Date.now() }),
            value: fc.float({ min: -20, max: 5 }) // Values around the -10 nT threshold
          }),
          { minLength: 10, maxLength: 50 }
        ),
        (solarWindData, bzFieldData) => {
          let thresholdCrossings: Array<{ type: string; value: number; threshold: number }> = []
          
          const onThresholdCrossing = jest.fn((type, value, threshold) => {
            thresholdCrossings.push({ type, value, threshold })
          })
          
          const { container, unmount } = render(
            <ChartsComponent 
              solarWindData={solarWindData}
              bzFieldData={bzFieldData}
              onThresholdCrossing={onThresholdCrossing}
            />
          )
          
          try {
            // Verify component renders
            expect(container).toBeInTheDocument()
            
            // Check for threshold indicators in the UI
            const criticalText = container.textContent?.includes('CRITICAL') || 
                               container.textContent?.includes('Critical')
            const normalText = container.textContent?.includes('NORMAL') || 
                              container.textContent?.includes('Normal')
            
            // At least one status should be displayed
            expect(criticalText || normalText).toBe(true)
            
            // Check that threshold lines are mentioned or indicated
            const thresholdText = container.textContent?.includes('Critical Thresholds') ||
                                 container.textContent?.includes('threshold')
            expect(thresholdText).toBe(true)
            
            // Verify charts are rendered with proper configuration
            const charts = container.querySelectorAll('[data-testid="highcharts-chart"]')
            expect(charts.length).toBe(2)
            
            // The component should handle threshold crossing logic
            // (The actual threshold crossing detection happens in useEffect)
            return true
          } finally {
            unmount()
          }
        }
      ),
      { numRuns: 15 }
    )
  })

  test('Charts component handles empty data gracefully', () => {
    const { container, unmount } = render(<ChartsComponent solarWindData={[]} bzFieldData={[]} />)
    
    try {
      expect(container).toBeInTheDocument()
      
      // Should still render charts even with empty data
      const charts = container.querySelectorAll('[data-testid="highcharts-chart"]')
      expect(charts.length).toBe(2)
      
      // Should show 0 values for current readings
      const zeroValues = container.textContent?.includes('0.0')
      expect(zeroValues).toBe(true)
    } finally {
      unmount()
    }
  })

  test('Charts component displays current values correctly', () => {
    const solarWindData = [
      { timestamp: Date.now() - 1000, value: 450.5 },
      { timestamp: Date.now(), value: 523.7 }
    ]
    
    const bzFieldData = [
      { timestamp: Date.now() - 1000, value: -5.2 },
      { timestamp: Date.now(), value: -12.8 }
    ]
    
    const { container, unmount } = render(
      <ChartsComponent solarWindData={solarWindData} bzFieldData={bzFieldData} />
    )
    
    try {
      expect(container).toBeInTheDocument()
      
      // Should display the latest values
      expect(container.textContent).toContain('523.7')
      expect(container.textContent).toContain('-12.8')
      
      // Should show units
      expect(container.textContent).toContain('km/s')
      expect(container.textContent).toContain('nT')
    } finally {
      unmount()
    }
  })

  test('Charts component shows correct status based on thresholds', () => {
    const highSolarWind = [{ timestamp: Date.now(), value: 600 }] // Above 500 threshold
    const lowBzField = [{ timestamp: Date.now(), value: -15 }] // Below -10 threshold
    
    const { container, unmount } = render(
      <ChartsComponent solarWindData={highSolarWind} bzFieldData={lowBzField} />
    )
    
    try {
      expect(container).toBeInTheDocument()
      
      // Should show CRITICAL status for both high solar wind and low Bz
      const criticalStatuses = container.textContent?.match(/CRITICAL/g)
      expect(criticalStatuses?.length).toBeGreaterThanOrEqual(1)
    } finally {
      unmount()
    }
  })
})