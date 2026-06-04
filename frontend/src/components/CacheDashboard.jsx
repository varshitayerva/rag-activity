import { useState, useEffect } from 'react'
import { BarChart3, Zap, RefreshCw, Trash2 } from 'lucide-react'

export function CacheDashboard({ apiKey = 'sk-demo-key-12345' }) {
  const [cacheStats, setCacheStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchCacheStats()
    const interval = setInterval(fetchCacheStats, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchCacheStats = async () => {
    try {
      const response = await fetch('http://localhost:8003/api/cache/stats', {
        headers: { 'X-API-Key': apiKey }
      })
      const data = await response.json()
      setCacheStats(data.stats)
    } catch (error) {
      console.error('Failed to fetch cache stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClearCache = async () => {
    setClearing(true)
    setMessage('')
    try {
      const response = await fetch('http://localhost:8003/api/cache/clear', {
        method: 'POST',
        headers: { 'X-API-Key': apiKey }
      })
      const data = await response.json()
      if (response.ok) {
        setMessage('✅ Cache cleared successfully!')
        fetchCacheStats()
      } else {
        setMessage('❌ Failed to clear cache')
      }
    } catch (error) {
      setMessage('❌ Error clearing cache')
    } finally {
      setClearing(false)
      setTimeout(() => setMessage(''), 3000)
    }
  }

  if (loading) return <div className="text-center py-8">Loading cache statistics...</div>
  if (!cacheStats) return <div className="text-center py-8 text-red-500">Failed to load cache stats</div>

  const hitRate = cacheStats.total_requests > 0
    ? (cacheStats.cache_hits / cacheStats.total_requests * 100).toFixed(1)
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Cache Performance</h1>
            <p className="text-cyan-100">Hybrid Redis + In-Memory Caching</p>
          </div>
          <BarChart3 size={48} className="opacity-80" />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Hit Rate</p>
          <p className="text-4xl font-bold text-green-600 dark:text-green-400">{hitRate}%</p>
          <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">Excellent performance</p>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Total Hits</p>
          <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">{cacheStats.cache_hits}</p>
          <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">Cached responses</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Total Misses</p>
          <p className="text-4xl font-bold text-purple-600 dark:text-purple-400">{cacheStats.cache_misses}</p>
          <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">Cache misses</p>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/30 dark:to-orange-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Memory Used</p>
          <p className="text-4xl font-bold text-orange-600 dark:text-orange-400">
            {(cacheStats.memory_used_mb || 0).toFixed(2)}MB
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">Current usage</p>
        </div>
      </div>

      {/* Cache Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <h3 className="text-lg font-bold mb-6">Search Results Cache</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">Items Cached</span>
              <span className="font-bold text-blue-600 dark:text-blue-400">{cacheStats.search_cache_size || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">Hit Rate</span>
              <span className="font-bold">{cacheStats.search_cache_hit_rate || 0}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">TTL</span>
              <span className="font-bold text-gray-600 dark:text-gray-400">1 Hour</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full"
                style={{width: `${cacheStats.search_cache_hit_rate || 0}%`}}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <h3 className="text-lg font-bold mb-6">Generation Cache</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">Items Cached</span>
              <span className="font-bold text-purple-600 dark:text-purple-400">{cacheStats.generation_cache_size || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">Hit Rate</span>
              <span className="font-bold">{cacheStats.generation_cache_hit_rate || 0}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">TTL</span>
              <span className="font-bold text-gray-600 dark:text-gray-400">2 Hours</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full"
                style={{width: `${cacheStats.generation_cache_hit_rate || 0}%`}}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Request Statistics */}
      <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
        <h3 className="text-lg font-bold mb-6">Request Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Total Requests</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{cacheStats.total_requests}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Cache Evictions</p>
            <p className="text-3xl font-bold text-red-600 dark:text-red-400">{cacheStats.cache_evictions || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Memory Efficiency</p>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {(((cacheStats.cache_hits / (cacheStats.cache_hits + cacheStats.cache_misses)) || 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Cache Details */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-bold mb-4">Cache Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600 dark:text-gray-400">Backend</p>
            <p className="font-semibold text-gray-900 dark:text-white">Redis + In-Memory Fallback</p>
          </div>
          <div>
            <p className="text-gray-600 dark:text-gray-400">Search TTL</p>
            <p className="font-semibold text-gray-900 dark:text-white">3,600 seconds (1 hour)</p>
          </div>
          <div>
            <p className="text-gray-600 dark:text-gray-400">Generation TTL</p>
            <p className="font-semibold text-gray-900 dark:text-white">7,200 seconds (2 hours)</p>
          </div>
          <div>
            <p className="text-gray-600 dark:text-gray-400">Eviction Policy</p>
            <p className="font-semibold text-gray-900 dark:text-white">LRU (Least Recently Used)</p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-4">
        {message && (
          <div className={`p-4 rounded-lg ${message.includes('✅') ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'}`}>
            {message}
          </div>
        )}

        <button
          onClick={handleClearCache}
          disabled={clearing}
          className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition"
        >
          <Trash2 size={20} />
          {clearing ? 'Clearing Cache...' : 'Clear All Cache'}
        </button>

        <button
          onClick={fetchCacheStats}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition"
        >
          <RefreshCw size={20} />
          Refresh Statistics
        </button>
      </div>
    </div>
  )
}
