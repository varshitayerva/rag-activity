import { useState, useEffect } from 'react'
import { BarChart3, Zap, RefreshCw, Trash2, TrendingUp, Activity, Clock } from 'lucide-react'
import { API_CONFIG } from '../config/api'

export function CacheDashboard({ apiKey }) {
  const [cacheStats, setCacheStats] = useState(null)
  const [queryPerformance, setQueryPerformance] = useState({})
  const [loading, setLoading] = useState(true)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(5000)
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)

  useEffect(() => {
    fetchCacheStats()
    if (!autoRefresh) return

    const interval = setInterval(fetchCacheStats, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])

  const fetchCacheStats = async () => {
    try {
      const [statsResponse, perfResponse] = await Promise.all([
        fetch(API_CONFIG.cache.stats, {
          headers: { 'X-API-Key': apiKey }
        }),
        fetch(API_CONFIG.cache.queryPerformance, {
          headers: { 'X-API-Key': apiKey }
        })
      ])

      const statsData = await statsResponse.json()
      setCacheStats(statsData.stats)

      if (perfResponse.ok) {
        const perfData = await perfResponse.json()
        setQueryPerformance(perfData.query_performance || {})
      }

      // Track history for trends with latency metrics
      setHistory(prev => {
        const stats = statsData.stats
        const newHistory = [...prev, {
          timestamp: new Date().toLocaleTimeString(),
          hitRate: stats.hit_rate || 0,
          hits: stats.cache_hits || 0,
          misses: stats.cache_misses || 0,
          latency: stats.avg_latency_ms || 0,
          latencySaved: stats.latency_saved_ms || 0
        }]
        // Keep last 20 entries
        return newHistory.slice(-20)
      })
    } catch (error) {
      console.error('Failed to fetch cache stats:', error)
      setMessage('❌ Failed to fetch cache stats')
    } finally {
      setLoading(false)
    }
  }

  const handleClearCache = async () => {
    setClearing(true)
    setMessage('')
    try {
      const response = await fetch(API_CONFIG.cache.clear, {
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

  const hitRate = cacheStats
    ? (cacheStats.cache_hits / (cacheStats.cache_hits + cacheStats.cache_misses) * 100).toFixed(1)
    : 0

  const hitRateTrend = history.length > 1
    ? history[history.length - 1].hitRate - history[0].hitRate
    : 0

  const getHitRateColor = (rate) => {
    if (rate >= 70) return 'text-green-600 dark:text-green-400'
    if (rate >= 50) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getStatusBadge = (rate) => {
    if (rate >= 70) return '🟢 Excellent'
    if (rate >= 50) return '🟡 Good'
    return '🔴 Needs Optimization'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg p-8 text-white">
        <div className="flex items-center justify-between mb-6">
          <div className="flex-1">
            <h1 className="text-3xl font-bold">Cache Performance</h1>
            <p className="text-cyan-100">Real-time Monitoring & Analytics</p>
          </div>
          <BarChart3 size={48} className="opacity-80" />
        </div>

        {/* Auto-Refresh Controls */}
        <div className="bg-cyan-700 bg-opacity-50 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4 rounded"
              />
              <span className="text-sm">Auto Refresh {autoRefresh ? '🔵' : '⚪'}</span>
            </label>

            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              disabled={!autoRefresh}
              className="px-3 py-1 rounded text-sm text-gray-900 disabled:opacity-50"
            >
              <option value={1000}>1 second</option>
              <option value={5000}>5 seconds</option>
              <option value={10000}>10 seconds</option>
              <option value={30000}>30 seconds</option>
            </select>
          </div>

          <button
            onClick={() => setShowHistory(!showHistory)}
            className="text-sm bg-cyan-600 hover:bg-cyan-700 px-3 py-1 rounded transition"
          >
            {showHistory ? '📊 Hide' : '📊 Show'} History
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-lg p-6 border-2 border-green-200 dark:border-green-700">
          <div className="flex items-start justify-between mb-2">
            <p className="text-sm text-gray-600 dark:text-gray-400">Hit Rate</p>
            <TrendingUp size={16} className={hitRateTrend >= 0 ? 'text-green-600' : 'text-red-600'} />
          </div>
          <p className={`text-4xl font-bold mb-2 ${getHitRateColor(hitRate)}`}>{hitRate}%</p>
          <p className="text-xs text-gray-600 dark:text-gray-500">{getStatusBadge(hitRate)}</p>
          {history.length > 1 && (
            <p className="text-xs text-gray-500 mt-2">
              Trend: {hitRateTrend > 0 ? '📈' : '📉'} {Math.abs(hitRateTrend).toFixed(1)}%
            </p>
          )}
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-6 border-2 border-blue-200 dark:border-blue-700">
          <div className="flex items-start justify-between mb-2">
            <p className="text-sm text-gray-600 dark:text-gray-400">Avg Latency</p>
            <Activity size={16} className="text-blue-600" />
          </div>
          <p className="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">{(cacheStats.avg_latency_ms || 0).toFixed(0)}ms</p>
          <p className="text-xs text-gray-600 dark:text-gray-500">Current response time</p>
          <div className="mt-2 text-xs text-blue-600 dark:text-blue-400">
            📊 {cacheStats.total_requests} total queries
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-6 border-2 border-purple-200 dark:border-purple-700">
          <div className="flex items-start justify-between mb-2">
            <p className="text-sm text-gray-600 dark:text-gray-400">Time Saved</p>
            <Clock size={16} className="text-purple-600" />
          </div>
          <p className="text-4xl font-bold text-purple-600 dark:text-purple-400 mb-2">{(cacheStats.latency_saved_ms || 0).toFixed(0)}ms</p>
          <p className="text-xs text-gray-600 dark:text-gray-500">Per cached request</p>
          <div className="mt-2 text-xs text-purple-600 dark:text-purple-400">
            ⚡ {(cacheStats.latency_reduction_percent || 0).toFixed(0)}% faster on repeat
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/30 dark:to-orange-800/30 rounded-lg p-6 border-2 border-orange-200 dark:border-orange-700">
          <div className="flex items-start justify-between mb-2">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Requests</p>
            <Zap size={16} className="text-orange-600" />
          </div>
          <p className="text-4xl font-bold text-orange-600 dark:text-orange-400 mb-2">
            {cacheStats.cache_hits + cacheStats.cache_misses}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-500">Hits + Misses</p>
          <div className="mt-2 text-xs text-orange-600 dark:text-orange-400">
            ✅ {cacheStats.cache_hits} hits | ❌ {cacheStats.cache_misses} misses
          </div>
        </div>
      </div>

      {/* Live History Chart */}
      {showHistory && history.length > 0 && (
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6 space-y-6">
          <div>
            <h3 className="text-lg font-bold mb-4">📈 Hit Rate Trend (Last {history.length} measurements)</h3>
            <div className="space-y-3">
              {history.map((entry, idx) => (
                <div key={idx} className="flex items-center gap-4">
                  <span className="text-xs text-gray-600 dark:text-gray-400 min-w-20">{entry.timestamp}</span>
                  <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-6 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-green-400 to-green-600 h-full flex items-center justify-center transition-all"
                      style={{width: `${entry.hitRate}%`}}
                    >
                      {entry.hitRate > 10 && (
                        <span className="text-xs font-bold text-white">{entry.hitRate.toFixed(0)}%</span>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-gray-600 dark:text-gray-400 min-w-12">({entry.hits}h/{entry.misses}m)</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-bold mb-4">⚡ Latency Trend (Last {history.length} measurements)</h3>
            <div className="space-y-3">
              {history.map((entry, idx) => (
                <div key={idx} className="flex items-center gap-4">
                  <span className="text-xs text-gray-600 dark:text-gray-400 min-w-20">{entry.timestamp}</span>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600 dark:text-gray-400">Response:</span>
                      <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded h-4 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-blue-400 to-blue-600 h-full"
                          style={{width: `${Math.min(100, (entry.latency / 50))}%`}}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 min-w-16 text-right">{entry.latency.toFixed(1)}ms</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-600 dark:text-gray-400">Saved:</span>
                      <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded h-4 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-purple-400 to-purple-600 h-full"
                          style={{width: `${Math.min(100, (entry.latencySaved / 2000))}%`}}
                        ></div>
                      </div>
                      <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 min-w-16 text-right">{entry.latencySaved.toFixed(0)}ms</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Cache Breakdown - Layer Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold">🔴 Embedding Cache (Layer 1)</h3>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
              {cacheStats.embedding_cache_hits || 0} hits
            </span>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">Hit Rate</span>
              <span className={`font-bold text-lg ${getHitRateColor((cacheStats.embedding_cache_hits / (cacheStats.embedding_cache_hits + cacheStats.embedding_cache_misses + 1)) * 100)}`}>
                {((cacheStats.embedding_cache_hits / (cacheStats.embedding_cache_hits + cacheStats.embedding_cache_misses + 1)) * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-700 dark:text-gray-300">Hits / Misses</span>
              <span className="text-gray-600 dark:text-gray-400">{cacheStats.embedding_cache_hits || 0} / {cacheStats.embedding_cache_misses || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">TTL</span>
              <span className="font-bold text-gray-600 dark:text-gray-400">24 hours</span>
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded p-3 mt-2">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Caches query embeddings to avoid redundant API calls. Saves ~100ms per hit.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold">🔵 Retrieval Cache (Layer 2)</h3>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
              {cacheStats.search_cache_size || 0} items
            </span>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">Hit Rate</span>
              <span className={`font-bold text-lg ${getHitRateColor(cacheStats.search_cache_hit_rate || 0)}`}>
                {(cacheStats.search_cache_hit_rate || 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-700 dark:text-gray-300">Hits / Misses</span>
              <span className="text-gray-600 dark:text-gray-400">{cacheStats.retrieval_cache_hits || 0} / {cacheStats.retrieval_cache_misses || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">TTL</span>
              <span className="font-bold text-gray-600 dark:text-gray-400">4 hours</span>
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded p-3 mt-2">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Caches hybrid search results. Saves ~350ms per hit.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6 hover:shadow-lg transition">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold">🟣 Response Cache (Layer 3)</h3>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
              {cacheStats.generation_cache_size || 0} items
            </span>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">Hit Rate</span>
              <span className={`font-bold text-lg ${getHitRateColor(cacheStats.generation_cache_hit_rate || 0)}`}>
                {(cacheStats.generation_cache_hit_rate || 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-700 dark:text-gray-300">Hits / Misses</span>
              <span className="text-gray-600 dark:text-gray-400">{cacheStats.response_cache_hits || 0} / {cacheStats.response_cache_misses || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700 dark:text-gray-300">TTL</span>
              <span className="font-bold text-gray-600 dark:text-gray-400">2 hours</span>
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded p-3 mt-2">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Caches LLM responses. Saves ~1800ms per hit.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Latency Timeline for Each Query */}
      {Object.keys(queryPerformance).length > 0 && (
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <h3 className="text-2xl font-bold mb-2">⏱️ Query Latency Timeline</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">First execution is slower, repeated queries are faster (cached):</p>

          <div className="space-y-6">
            {Object.entries(queryPerformance).slice(0, 5).map(([query, metrics]) => (
              <div key={query} className="border-l-4 border-blue-500 pl-4">
                <p className="font-semibold text-gray-900 dark:text-white mb-3">"{query}"</p>

                <div className="space-y-2">
                  {metrics.all_latencies.map((latency, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="min-w-20">
                        <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                          Execution {idx + 1}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-8 overflow-hidden flex items-center">
                          <div
                            className={`h-full flex items-center justify-center text-white text-xs font-bold transition-all ${
                              idx === 0 ? 'bg-red-500' : 'bg-green-500'
                            }`}
                            style={{width: `${Math.max(5, (latency / Math.max(...metrics.all_latencies)) * 100)}%`}}
                          >
                            {latency > 50 && `${latency}ms`}
                          </div>
                        </div>
                      </div>
                      <div className="min-w-16 text-right">
                        <span className="font-bold text-gray-900 dark:text-white">{latency}ms</span>
                      </div>
                    </div>
                  ))}
                </div>

                {metrics.executions > 1 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      ⚡ <strong>{metrics.improvement_percent}% faster</strong> on repeated searches ({metrics.time_saved_ms}ms saved)
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {Object.keys(queryPerformance).length > 5 && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-6">
              ... and {Object.keys(queryPerformance).length - 5} more queries
            </p>
          )}
        </div>
      )}

      {/* Request Statistics */}
      <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
        <h3 className="text-lg font-bold mb-6">📊 Performance Metrics & Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Total Requests</p>
            <p className="text-4xl font-bold text-gray-900 dark:text-white">{cacheStats.total_requests}</p>
            <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">All-time requests processed</p>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">❄️ Cold Cache Latency</p>
            <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">{(cacheStats.cold_latency_ms || 500).toFixed(0)}ms</p>
            <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">First execution (no cache)</p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">🔥 Warm Cache Latency</p>
            <p className="text-4xl font-bold text-green-600 dark:text-green-400">{(cacheStats.warm_latency_ms || 0).toFixed(0)}ms</p>
            <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">Cached execution</p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Time Saved Per Request</p>
            <p className="text-4xl font-bold text-purple-600 dark:text-purple-400">{(cacheStats.latency_saved_ms || 0).toFixed(0)}ms</p>
            <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">By using cache</p>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/30 dark:to-orange-800/30 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Speed Improvement</p>
            <p className="text-4xl font-bold text-orange-600 dark:text-orange-400">{(cacheStats.latency_reduction_percent || 0).toFixed(0)}%</p>
            <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">Faster with caching enabled</p>
          </div>

          <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 rounded-lg p-4">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Uptime</p>
            <p className="text-4xl font-bold text-red-600 dark:text-red-400">{Math.floor((cacheStats.uptime_seconds || 0) / 60)}m</p>
            <p className="text-xs text-gray-600 dark:text-gray-500 mt-2">System runtime</p>
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
          <div className={`p-4 rounded-lg animate-fade-in ${message.includes('✅') ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 border border-green-300 dark:border-green-700' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 border border-red-300 dark:border-red-700'}`}>
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={handleClearCache}
            disabled={clearing}
            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition transform hover:scale-105 active:scale-95"
          >
            <Trash2 size={20} />
            {clearing ? 'Clearing...' : 'Clear Cache'}
          </button>

          <button
            onClick={fetchCacheStats}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition transform hover:scale-105 active:scale-95"
          >
            <RefreshCw size={20} className={autoRefresh ? 'animate-spin' : ''} />
            Refresh Now
          </button>
        </div>

        {/* Cache Health Indicator */}
        <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl">
              {hitRate >= 70 ? '✨' : hitRate >= 50 ? '⚡' : '🔧'}
            </span>
            <div>
              <p className="font-bold text-gray-900 dark:text-white">Cache Health</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {hitRate >= 70 ? 'Excellent - Keep it up!' : hitRate >= 50 ? 'Good - Room for improvement' : 'Fair - Add more cache hits'}
              </p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-gray-700 dark:text-gray-300">
              <span className="font-semibold">Next actions:</span>
              {hitRate < 50 && <p>• Run more similar queries to boost hit rate</p>}
              {hitRate < 70 && <p>• Check if cache TTL matches query frequency</p>}
              {(cacheStats.cache_evictions || 0) > 10 && <p>• Many evictions detected - consider increasing cache size</p>}
              {hitRate >= 70 && <p>• ✅ Cache is performing optimally!</p>}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-in-out;
        }
      `}</style>
    </div>
  )
}
