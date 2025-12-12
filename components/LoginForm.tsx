'use client'

import { useState } from 'react'

interface LoginFormProps {
  onLogin: (user: any) => void
}

export default function LoginForm({ onLogin }: LoginFormProps) {
  const [step, setStep] = useState<'email' | 'otp'>('email')
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [resendCount, setResendCount] = useState(0)

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setMessage('')

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (data.success) {
        setMessage(data.message)
        setStep('otp')
      } else {
        setError(data.message)
      }
    } catch (err) {
      setError('Failed to send OTP. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, otp }),
      })

      const data = await response.json()

      if (data.success) {
        // Pass user object if available, otherwise create one from email
        const userData = data.user || {
          email: data.email || email,
          id: Date.now(), // Temporary ID
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString()
        }
        onLogin(userData)
      } else {
        setError(data.message)
        setOtp('') // Clear wrong OTP
      }
    } catch (err) {
      setError('Failed to verify code. Please try again.')
      setOtp('')
    } finally {
      setLoading(false)
    }
  }

  const handleResendOTP = async () => {
    if (resendCount >= 2) {
      setError('Maximum resend limit reached. Please start over.')
      return
    }

    setLoading(true)
    setError('')
    setMessage('')

    try {
      const response = await fetch('/api/auth/resend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (data.success) {
        setMessage(data.message)
        setResendCount(prev => prev + 1)
      } else {
        setError(data.message)
      }
    } catch (err) {
      setError('Failed to resend code. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleBackToEmail = () => {
    setStep('email')
    setOtp('')
    setMessage('')
    setError('')
    setResendCount(0)
  }

  return (
    <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-astro-cyan">
          {step === 'email' ? 'Login to AstroSense' : 'Enter Verification Code'}
        </h3>
        <div className="text-xs text-gray-400">
          🔐 Secure Email Authentication
        </div>
      </div>

      {step === 'email' ? (
        <form onSubmit={handleEmailSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm text-gray-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800/50 border border-astro-cyan/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-astro-cyan focus:ring-1 focus:ring-astro-cyan"
              placeholder="Enter your email address"
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg p-3">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !email}
            className="w-full bg-astro-blue hover:bg-astro-accent text-white font-semibold py-2 px-4 rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Sending Code...
              </div>
            ) : (
              'Send Login Code'
            )}
          </button>

          <p className="text-xs text-gray-400 text-center">
            We'll send a 6-digit code to your email for secure login
          </p>
        </form>
      ) : (
        <form onSubmit={handleOTPSubmit} className="space-y-4">
          <div>
            <label htmlFor="otp" className="block text-sm text-gray-300 mb-2">
              Verification Code
            </label>
            <input
              type="text"
              id="otp"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              className="w-full px-3 py-2 bg-gray-800/50 border border-astro-cyan/30 rounded-lg text-white text-center text-lg font-mono tracking-widest focus:outline-none focus:border-astro-cyan focus:ring-1 focus:ring-astro-cyan"
              placeholder="000000"
              maxLength={6}
              required
              disabled={loading}
            />
          </div>

          {message && (
            <div className="text-green-400 text-sm bg-green-400/10 border border-green-400/20 rounded-lg p-3">
              {message}
            </div>
          )}

          {error && (
            <div className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 rounded-lg p-3">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <button
              type="submit"
              disabled={loading || otp.length !== 6}
              className="w-full bg-astro-blue hover:bg-astro-accent text-white font-semibold py-2 px-4 rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Verifying...
                </div>
              ) : (
                'Verify & Login'
              )}
            </button>
            
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={handleBackToEmail}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-all duration-300"
                disabled={loading}
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleResendOTP}
                disabled={loading || resendCount >= 2}
                className="flex-1 bg-yellow-600 hover:bg-yellow-500 text-white font-medium py-2 px-4 rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : `Resend Code ${resendCount >= 2 ? '(Max)' : `(${resendCount}/2)`}`}
              </button>
            </div>
          </div>

          <p className="text-xs text-gray-400 text-center">
            Code expires in 5 minutes • Check your email for the 6-digit code
          </p>
        </form>
      )}
    </div>
  )
}