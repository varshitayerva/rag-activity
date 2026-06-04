import { useState, useEffect } from 'react'
import { BarChart3, Users, AlertCircle, Zap, TrendingUp } from 'lucide-react'

export function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [feedbackStats, setFeedbackStats] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, feedbackRes, healthRes] = await Promise.all([
          fetch('http://localhost:8007/api/metrics').then(r => r.json()),
          fetch('http://localhost:8007/api/feedback/stats').then(r => r.json()),
          fetch('http://localhost:8007/api/health/detailed').then(r => r.json()),
        ])
        setStats(statsRes)
        setFeedbackStats(feedbackRes)
        setHealth(healthRes)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return <div className="text-center py-8">Loading dashboard...</div>

  const healthScore = health?.health?.health_score || 0
  const healthColor = healthScore >= 80 ? 'text-green-500' : healthScore >= 60 ? 'text-yellow-500' : 'text-red-500'

  return (
    <div className="p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white min-h-screen">
      <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
        Admin Dashboard
      </h1>

      {/* Health Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-2">System Health</p>
              <p className={`text-4xl font-bold ${healthColor}`}>{healthScore}</p>
              <p className="text-xs text-gray-400 mt-1">{health?.health?.status}</p>
            </div>
            <TrendingUp className={`w-10 h-10 ${healthColor}`} />
          </div>
        </div>

        <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-2">Total Queries</p>
              <p className="text-4xl font-bold text-blue-400">{stats?.total_queries || 0}</p>
            </div>
            <Zap className="w-10 h-10 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-2">Avg Latency</p>
              <p className="text-4xl font-bold text-purple-400">{stats?.avg_latency_ms?.toFixed(0) || 0}ms</p>
            </div>
            <BarChart3 className="w-10 h-10 text-purple-400" />
          </div>
        </div>

        <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-2">Active Alerts</p>
              <p className="text-4xl font-bold text-red-400">{health?.alerts?.active_count || 0}</p>
            </div>
            <AlertCircle className="w-10 h-10 text-red-400" />
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Cache Performance */}
        <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Zap className="text-yellow-400" />
            Cache Performance
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-300">Hit Rate</span>
              <span className="text-green-400 font-bold">{(stats?.cache_hit_rate * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{width: `${stats?.cache_hit_rate * 100}%`}}></div>
            </div>
            <div className="flex justify-between text-sm text-gray-400 mt-4">
              <span>Hits: {stats?.embedding_cache_hits || 0}</span>
              <span>Misses: {stats?.embedding_cache_misses || 0}</span>
            </div>
          </div>
        </div>

        {/* Feedback Quality */}
        <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Users className="text-blue-400" />
            Feedback Quality
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-300">Avg Rating</span>
              <span className="text-blue-400 font-bold">{feedbackStats?.stats?.avg_rating || 0}/5</span>
            </div>
            <div className="w-full bg-gray-600 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full" style={{width: `${(feedbackStats?.stats?.avg_rating / 5) * 100}%`}}></div>
            </div>
            <div className="flex justify-between text-sm text-gray-400 mt-4">
              <span>Total: {feedbackStats?.stats?.total_feedback || 0}</span>
              <span>Quality: {feedbackStats?.stats?.quality_score || 'N/A'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {health?.alerts?.triggered_alerts && health.alerts.triggered_alerts.length > 0 && (
        <div className="bg-red-900/30 border border-red-600 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4 text-red-400">🚨 Active Alerts</h2>
          <div className="space-y-2">
            {health.alerts.triggered_alerts.map((alert, idx) => (
              <div key={idx} className="flex items-center justify-between bg-gray-700/50 p-3 rounded">
                <span className="text-gray-200">{alert.name}</span>
                <span className="text-red-400 text-sm">{alert.metric}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rating Distribution */}
      {feedbackStats?.stats?.distribution && (
        <div className="bg-gray-700/50 rounded-lg p-6 border border-gray-600">
          <h2 className="text-xl font-bold mb-6">Rating Distribution</h2>
          <div className="flex items-end gap-4 h-40">
            {[5, 4, 3, 2, 1].map(rating => (
              <div key={rating} className="flex-1 flex flex-col items-center">
                <div className="w-full bg-gradient-to-t from-blue-500 to-purple-500 rounded-t"
                     style={{height: `${(feedbackStats.stats.distribution[rating] / Math.max(1, ...Object.values(feedbackStats.stats.distribution))) * 100}px`}}>
                </div>
                <p className="text-sm text-gray-400 mt-2">{rating}⭐ ({feedbackStats.stats.distribution[rating]})</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
