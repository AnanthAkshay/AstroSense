import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

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
      <body className={`${inter.className} bg-astro-dark text-white`}>
        {children}
      </body>
    </html>
  )
}
