import { useState, useEffect } from 'react'
import { apiClient } from '../utils/api'

export function StatusIndicator() {
  const [isOnline, setIsOnline] = useState(true)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    // Check health immediately
    const checkHealth = async () => {
      setChecking(true)
      const online = await apiClient.checkHealth()
      setIsOnline(online)
      setChecking(false)
    }

    checkHealth()

    // Check health every 5 seconds
    const interval = setInterval(checkHealth, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className={`rounded-2xl p-5 shadow-lg border-2 transition-all duration-300 ${
      isOnline
        ? 'bg-gradient-to-br from-green-100 to-green-50 dark:from-green-900/30 dark:to-green-800/20 border-green-300 dark:border-green-700'
        : 'bg-gradient-to-br from-red-100 to-red-50 dark:from-red-900/30 dark:to-red-800/20 border-red-300 dark:border-red-700'
    }`}>
      <p className="text-xs text-gray-700 dark:text-gray-300 mb-3 font-bold uppercase tracking-wider">📊 Status</p>
      <div className="flex items-center gap-3">
        <div
          className={`w-4 h-4 rounded-full ${
            isOnline ? 'bg-gradient-to-br from-green-400 to-green-600' : 'bg-gradient-to-br from-red-400 to-red-600'
          } ${!checking ? 'animate-pulse shadow-lg' : 'shadow-md'}`}
        />
        <p className={`text-sm font-bold ${
          isOnline
            ? 'text-green-700 dark:text-green-400'
            : 'text-red-700 dark:text-red-400'
        }`}>
          {isOnline ? '🟢 Online' : '🔴 Offline'}
        </p>
      </div>
    </div>
  )
}
