import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="max-w-2xl mx-auto text-center">
        <h1 className="text-5xl font-bold mb-6 text-astro-cyan animate-fade-in">
          AstroSense
        </h1>
        <p className="text-xl text-gray-300 mb-8 animate-slide-up">
          Space Weather Impact Forecasting & Risk Intelligence System
        </p>
        
        <div className="space-y-4 animate-fade-in">
          <Link 
            href="/dashboard"
            className="inline-block bg-astro-blue hover:bg-astro-accent text-white font-semibold py-3 px-8 rounded-lg transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-astro-cyan/20"
          >
            Enter Dashboard
          </Link>
          
          <div className="mt-8 p-6 bg-astro-blue/20 rounded-lg border border-astro-cyan/30">
            <p className="text-gray-400 text-sm">
              Real-time monitoring • Impact forecasting • Alert management
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
