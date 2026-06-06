import { useState, useEffect } from 'react'
import { apiClient } from '../utils/api'

export function MetricsBar() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await apiClient.getMetrics()
        setMetrics(data)
        setLoading(false)
      } catch (error) {
        console.error('Failed to fetch metrics:', error)
        setLoading(false)
      }
    }

    fetchMetrics()
    // Update metrics every 15 seconds
    const interval = setInterval(fetchMetrics, 15000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="bg-gray-100 p-2 text-sm text-gray-600">Loading metrics...</div>
  }

  if (!metrics) {
    return <div className="bg-gray-100 p-2 text-sm text-gray-600">Metrics unavailable</div>
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-purple-900/50 border-b-2 border-blue-200 dark:border-purple-700/50 p-5 grid grid-cols-4 gap-5 text-sm backdrop-blur-sm">
      <div className="flex flex-col bg-white dark:bg-gray-700/40 rounded-xl p-4 shadow-md hover:shadow-lg transition-shadow duration-300 border border-blue-100 dark:border-blue-800/30">
        <span className="text-gray-500 dark:text-gray-400 text-xs uppercase font-bold tracking-wider mb-2">⚡ Cache Hit</span>
        <span className="text-3xl font-black bg-gradient-to-r from-blue-600 to-blue-700 bg-clip-text text-transparent">
          {(metrics.cache_hit_rate * 100).toFixed(1)}%
        </span>
        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mt-2">
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 h-1.5 rounded-full" style={{width: `${(metrics.cache_hit_rate * 100)}%`}}></div>
        </div>
      </div>

      <div className="flex flex-col bg-white dark:bg-gray-700/40 rounded-xl p-4 shadow-md hover:shadow-lg transition-shadow duration-300 border border-purple-100 dark:border-purple-800/30">
        <span className="text-gray-500 dark:text-gray-400 text-xs uppercase font-bold tracking-wider mb-2">⏱️ Latency</span>
        <span className="text-3xl font-black bg-gradient-to-r from-purple-600 to-purple-700 bg-clip-text text-transparent">
          {metrics.avg_latency_ms.toFixed(0)}ms
        </span>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">avg response time</p>
      </div>

      <div className="flex flex-col bg-white dark:bg-gray-700/40 rounded-xl p-4 shadow-md hover:shadow-lg transition-shadow duration-300 border border-green-100 dark:border-green-800/30">
        <span className="text-gray-500 dark:text-gray-400 text-xs uppercase font-bold tracking-wider mb-2">🪙 Tokens</span>
        <span className="text-3xl font-black bg-gradient-to-r from-green-600 to-green-700 bg-clip-text text-transparent">
          {Math.round(metrics.avg_tokens_in_context).toLocaleString()}
        </span>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">per search</p>
      </div>

      <div className="flex flex-col bg-white dark:bg-gray-700/40 rounded-xl p-4 shadow-md hover:shadow-lg transition-shadow duration-300 border border-orange-100 dark:border-orange-800/30">
        <span className="text-gray-500 dark:text-gray-400 text-xs uppercase font-bold tracking-wider mb-2">📊 Queries</span>
        <span className="text-3xl font-black bg-gradient-to-r from-orange-600 to-orange-700 bg-clip-text text-transparent">
          {metrics.total_queries}
        </span>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">searches performed</p>
      </div>
    </div>
  )
}
