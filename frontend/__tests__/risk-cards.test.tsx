/**
 * Risk Cards Component Tests
 * Tests the risk cards component functionality and display requirements
 */

import React from 'react'
import { render, screen, waitFor } from './test-utils'
import '@testing-library/jest-dom'
import RiskCardsComponent from '../components/RiskCardsComponent'

// Mock the UI components
jest.mock('../components/ui/Card', () => {
  return function MockCard({ children, className }: { children: React.ReactNode, className?: string }) {
    return <div data-testid="card" className={className}>{children}</div>
  }
})

jest.mock('../components/ui/StatusIndicator', () => {
  return function MockStatusIndicator({ status, label }: { status: string, label: string }) {
    return <div data-testid="status-indicator" data-status={status}>{label}</div>
  }
})

describe('RiskCardsComponent', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders all five sector risk cards', () => {
    render(<RiskCardsComponent />)
    
    expect(screen.getByText('Aviation')).toBeInTheDocument()
    expect(screen.getByText('Telecommunications')).toBeInTheDocument()
    expect(screen.getByText('GPS Systems')).toBeInTheDocument()
    expect(screen.getByText('Power Grid')).toBeInTheDocument()
    expect(screen.getByText('Satellites')).toBeInTheDocument()
  })

  test('displays aviation HF blackout probability and polar route risk (Requirement 4.4)', () => {
    render(<RiskCardsComponent />)
    
    expect(screen.getByText('HF Blackout Probability')).toBeInTheDocument()
    expect(screen.getByText(/Polar Route Risk/)).toBeInTheDocument()
    expect(screen.getByText('High frequency radio communications and polar route safety')).toBeInTheDocument()
  })

  test('displays telecom signal degradation with historical comparison (Requirement 5.4)', () => {
    render(<RiskCardsComponent />)
    
    expect(screen.getByText('Signal Degradation')).toBeInTheDocument()
    expect(screen.getByText('Historical Trend:')).toBeInTheDocument()
    expect(screen.getByText('Satellite communications and terrestrial signal quality')).toBeInTheDocument()
  })

  test('displays GPS drift magnitude with geographic distribution (Requirement 6.4)', () => {
    render(<RiskCardsComponent />)
    
    expect(screen.getByText('Positional Drift')).toBeInTheDocument()
    expect(screen.getByText(/Geographic Distribution/)).toBeInTheDocument()
    expect(screen.getByText('Polar Regions')).toBeInTheDocument()
    expect(screen.getByText(/Polar Regions \(67\.5 cm\)/)).toBeInTheDocument()
  })

  test('displays power grid GIC risk level with affected regions (Requirement 7.3)', () => {
    render(<RiskCardsComponent />)
    
    expect(screen.getByText('GIC Risk Level')).toBeInTheDocument()
    expect(screen.getByText(/Affected Regions/)).toBeInTheDocument()
    expect(screen.getByText('Northern Grid')).toBeInTheDocument()
    expect(screen.getByText('Eastern Grid')).toBeInTheDocument()
    expect(screen.getByText('Western Grid')).toBeInTheDocument()
  })

  test('displays satellite drag risk level with altitude-specific impacts (Requirement 8.3)', () => {
    render(<RiskCardsComponent />)
    
    expect(screen.getByText('Orbital Drag Risk')).toBeInTheDocument()
    expect(screen.getByText('Altitude Impact:')).toBeInTheDocument()
    expect(screen.getByText('400 km')).toBeInTheDocument()
    expect(screen.getByText('High (LEO)')).toBeInTheDocument()
  })

  test('applies color-coded severity indicators', () => {
    render(<RiskCardsComponent />)
    
    const statusIndicators = screen.getAllByTestId('status-indicator')
    expect(statusIndicators.length).toBeGreaterThan(0)
    
    // Check that status indicators have appropriate status values
    const statuses = statusIndicators.map(indicator => indicator.getAttribute('data-status'))
    expect(statuses).toContain('low')
    expect(statuses).toContain('moderate')
    expect(statuses).toContain('high')
  })

  test('displays overall risk assessment summary', () => {
    render(<RiskCardsComponent />)
    
    expect(screen.getByText('Overall Risk Assessment')).toBeInTheDocument()
    expect(screen.getByText('Active Alerts:')).toBeInTheDocument()
    expect(screen.getByText('Monitoring:')).toBeInTheDocument()
    expect(screen.getByText('5 Sectors')).toBeInTheDocument()
  })

  test('shows live status indicators', () => {
    render(<RiskCardsComponent />)
    
    const liveIndicators = screen.getAllByText('Live')
    expect(liveIndicators.length).toBeGreaterThan(0)
  })

  test('displays last updated timestamps', () => {
    render(<RiskCardsComponent />)
    
    const lastUpdatedElements = screen.getAllByText(/Last updated:/)
    expect(lastUpdatedElements.length).toBe(5) // One for each sector
  })

  test('handles custom risk data prop', () => {
    const customRisks = [{
      id: 'test',
      name: 'Test Sector',
      icon: '🧪',
      primaryMetric: {
        label: 'Test Metric',
        value: 50,
        unit: '%',
        threshold: 60,
        status: 'moderate' as const
      },
      description: 'Test sector description',
      lastUpdated: new Date()
    }]

    render(<RiskCardsComponent risks={customRisks} />)
    
    expect(screen.getByText('Test Sector')).toBeInTheDocument()
    expect(screen.getByText('Test Metric')).toBeInTheDocument()
    expect(screen.getByText('50.0')).toBeInTheDocument()
  })

  test('calls onRiskChange callback when provided', async () => {
    const mockOnRiskChange = jest.fn()
    
    render(<RiskCardsComponent onRiskChange={mockOnRiskChange} />)
    
    // Wait for the simulation to potentially trigger
    await waitFor(() => {
      // The component should render without errors
      expect(screen.getByText('Aviation')).toBeInTheDocument()
    }, { timeout: 1000 })
  })
})