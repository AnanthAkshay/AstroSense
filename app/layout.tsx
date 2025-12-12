import type { Metadata } from 'next'
import './globals.css'
import { AppProvider } from '@/contexts/AppContext'

export const metadata: Metadata = {
  title: 'AstroSense - Space Weather Forecasting',
  description: 'Real-time space weather impact forecasting and risk intelligence system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans bg-astro-dark text-white">
        <AppProvider>
          {children}
        </AppProvider>
      </body>
    </html>
  )
}
