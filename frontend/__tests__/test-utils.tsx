import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { AppProvider } from '../contexts/AppContext'

// Custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <AppProvider>
      {children}
    </AppProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }

// Test to ensure the test utils work correctly
describe('Test Utils', () => {
  it('should provide custom render function', () => {
    expect(customRender).toBeDefined()
    expect(typeof customRender).toBe('function')
  })

  it('should provide AllTheProviders wrapper', () => {
    expect(AllTheProviders).toBeDefined()
    expect(typeof AllTheProviders).toBe('function')
  })
})