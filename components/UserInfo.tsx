'use client'

import { useState } from 'react'

interface User {
  id: number
  email: string
  created_at: string
  last_login: string
}

interface UserInfoProps {
  user: User
  onLogout: () => void
}

export default function UserInfo({ user, onLogout }: UserInfoProps) {
  const [loading, setLoading] = useState(false)

  const handleLogout = async () => {
    setLoading(true)
    
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
      
      onLogout()
    } catch (err) {
      console.error('Logout failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="bg-astro-blue/10 rounded-lg border border-astro-cyan/20 p-4 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-astro-cyan/20 rounded-full flex items-center justify-center">
            <span className="text-astro-cyan text-sm font-semibold">
              {user.email.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <div className="text-white font-medium">{user.email}</div>
            <div className="text-xs text-gray-400">
              Last login: {formatDate(user.last_login)}
            </div>
          </div>
        </div>
        
        <button
          onClick={handleLogout}
          disabled={loading}
          className="bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium py-1.5 px-3 rounded-lg transition-all duration-300 disabled:opacity-50"
        >
          {loading ? (
            <div className="flex items-center">
              <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mr-1"></div>
              Logging out...
            </div>
          ) : (
            'Logout'
          )}
        </button>
      </div>
    </div>
  )
}