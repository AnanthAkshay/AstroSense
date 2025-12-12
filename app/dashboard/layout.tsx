import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Dashboard - AstroSense',
  description: 'Real-time space weather monitoring dashboard',
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-astro-dark">
      {/* Header */}
      <header className="bg-astro-dark/90 backdrop-blur-sm border-b border-astro-cyan/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-astro-cyan">AstroSense</h1>
              <span className="text-sm text-gray-400 hidden sm:block">
                Space Weather Intelligence
              </span>
            </div>
            
            {/* Status indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-300 hidden sm:block">Live</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>
    </div>
  )
}