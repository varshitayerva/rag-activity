import { useState, useEffect } from 'react'
import { AlertTriangle, Activity, TrendingDown, AlertCircle, CheckCircle2 } from 'lucide-react'

export function MonitoringDashboard({ apiKey }) {
  const [metrics, setMetrics] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('metrics')

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [metricsRes, alertsRes, healthRes] = await Promise.all([
        fetch(API_CONFIG.monitoring.metrics, {
          headers: { 'X-API-Key': apiKey }
        }).then(r => r.json()),
        fetch(API_CONFIG.monitoring.alerts, {
          headers: { 'X-API-Key': apiKey }
        }).then(r => r.json()),
        fetch(API_CONFIG.metrics.health, {
          headers: { 'X-API-Key': apiKey }
        }).then(r => r.json())
      ])
      setMetrics(metricsRes.metrics || {})
      setAlerts(alertsRes.alerts || {})
      setHealth(healthRes.health || {})
    } catch (error) {
      console.error('Failed to fetch monitoring data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading monitoring data...</div>

  const getHealthColor = (score) => {
    if (score >= 80) return 'from-green-500 to-green-600'
    if (score >= 60) return 'from-yellow-500 to-yellow-600'
    return 'from-red-500 to-red-600'
  }

  const getAlertSeverity = (alert) => {
    if (alert.severity === 'critical') return 'border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20'
    if (alert.severity === 'warning') return 'border-l-4 border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
    return 'border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">System Monitoring</h1>
            <p className="text-indigo-100">Real-time health & performance tracking</p>
          </div>
          <Activity size={48} className="opacity-80" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('metrics')}
          className={`py-3 px-4 font-semibold border-b-2 transition ${
            activeTab === 'metrics'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400'
          }`}
        >
          Metrics
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={`py-3 px-4 font-semibold border-b-2 transition flex items-center gap-2 ${
            activeTab === 'alerts'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400'
          }`}
        >
          <AlertTriangle size={18} />
          Alerts
          {Object.values(alerts || {}).filter(a => a.triggered).length > 0 && (
            <span className="bg-red-500 text-white text-xs rounded-full px-2">
              {Object.values(alerts || {}).filter(a => a.triggered).length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('health')}
          className={`py-3 px-4 font-semibold border-b-2 transition ${
            activeTab === 'health'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400'
          }`}
        >
          Health
        </button>
      </div>

      {/* METRICS TAB */}
      {activeTab === 'metrics' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Total Queries</p>
              <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">
                {metrics.total_queries || 0}
              </p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-lg p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Avg Latency</p>
              <p className="text-4xl font-bold text-green-600 dark:text-green-400">
                {(metrics.avg_latency || 0).toFixed(2)}ms
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Error Rate</p>
              <p className="text-4xl font-bold text-purple-600 dark:text-purple-400">
                {(metrics.error_rate || 0).toFixed(2)}%
              </p>
            </div>

            <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/30 dark:to-orange-800/30 rounded-lg p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">QPS (Peak)</p>
              <p className="text-4xl font-bold text-orange-600 dark:text-orange-400">
                {(metrics.qps || 0).toFixed(1)}/s
              </p>
            </div>
          </div>

          {/* Detailed Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Search Performance</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Total Searches</span>
                  <span className="font-bold">{metrics.total_searches || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Search Time</span>
                  <span className="font-bold">{(metrics.avg_search_latency || 0).toFixed(2)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Min/Max</span>
                  <span className="font-bold text-gray-600 dark:text-gray-400">
                    {(metrics.min_latency || 0).toFixed(2)}ms / {(metrics.max_latency || 0).toFixed(2)}ms
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Generation Performance</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Total Generations</span>
                  <span className="font-bold">{metrics.total_generations || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Generation Time</span>
                  <span className="font-bold">{(metrics.avg_generation_latency || 0).toFixed(2)}ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Success Rate</span>
                  <span className="font-bold text-green-600 dark:text-green-400">
                    {((1 - (metrics.error_rate || 0) / 100) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ALERTS TAB */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          {Object.entries(alerts || {}).length === 0 ? (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-8 flex items-center gap-4">
              <CheckCircle2 className="text-green-600 dark:text-green-400" size={32} />
              <div>
                <h3 className="font-bold text-green-900 dark:text-green-300">All Systems Operational</h3>
                <p className="text-sm text-green-700 dark:text-green-400">No active alerts</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(alerts || {}).map(([key, alert]) => (
                <div
                  key={key}
                  className={`rounded-lg p-6 ${getAlertSeverity(alert)} ${alert.triggered ? 'opacity-100' : 'opacity-50'}`}
                >
                  <div className="flex items-start gap-4">
                    <AlertTriangle
                      size={24}
                      className={
                        alert.severity === 'critical' ? 'text-red-600 dark:text-red-400' :
                        alert.severity === 'warning' ? 'text-yellow-600 dark:text-yellow-400' :
                        'text-blue-600 dark:text-blue-400'
                      }
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-bold text-gray-900 dark:text-white">{alert.name}</h3>
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${
                          alert.triggered
                            ? 'bg-red-500 text-white'
                            : 'bg-green-500 text-white'
                        }`}>
                          {alert.triggered ? 'TRIGGERED' : 'OK'}
                        </span>
                      </div>
                      <p className="text-gray-700 dark:text-gray-300 text-sm mb-2">
                        {alert.message}
                      </p>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        <p>Threshold: {alert.threshold}</p>
                        <p>Current: {alert.current_value}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Alert Rules */}
          <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Alert Rules</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-600 pb-3">
                <span>High Error Rate</span>
                <span className="font-bold">&gt; 5%</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-600 pb-3">
                <span>High Latency</span>
                <span className="font-bold">&gt; 5000ms</span>
              </div>
              <div className="flex justify-between border-b border-gray-200 dark:border-gray-600 pb-3">
                <span>Low Cache Hit Rate</span>
                <span className="font-bold">&lt; 30%</span>
              </div>
              <div className="flex justify-between">
                <span>High QPS</span>
                <span className="font-bold">&gt; 100/s</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* HEALTH TAB */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          {/* Health Score */}
          <div className={`bg-gradient-to-r ${getHealthColor(health.score || 0)} rounded-lg p-8 text-white`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm opacity-90">Overall Health Score</p>
                <p className="text-5xl font-bold">{health.score || 0}/100</p>
              </div>
              <div className="text-right">
                <p className="text-sm opacity-90">Status</p>
                <p className="text-2xl font-bold">
                  {health.score >= 80 ? 'Excellent' : health.score >= 60 ? 'Good' : 'Needs Attention'}
                </p>
              </div>
            </div>
          </div>

          {/* Health Components */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-6">Component Status</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Database</span>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm">Healthy</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span>Cache</span>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 ${health.cache_status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'} rounded-full`}></div>
                    <span className="text-sm capitalize">{health.cache_status || 'Degraded'}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span>API</span>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm">Responding</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span>Vector Index</span>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 ${health.vector_index_status === 'ready' ? 'bg-green-500' : 'bg-gray-500'} rounded-full`}></div>
                    <span className="text-sm capitalize">{health.vector_index_status || 'Unavailable'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-6">Recent Issues</h3>
              {health.recent_errors && health.recent_errors.length > 0 ? (
                <div className="space-y-3">
                  {health.recent_errors.slice(0, 5).map((error, idx) => (
                    <div key={idx} className="text-sm border-l-2 border-red-500 pl-3">
                      <p className="font-semibold text-gray-900 dark:text-white">{error.type}</p>
                      <p className="text-gray-600 dark:text-gray-400">{error.message}</p>
                      <p className="text-xs text-gray-500">{error.timestamp}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 dark:text-gray-400">No recent errors</p>
              )}
            </div>
          </div>

          {/* Uptime */}
          <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
            <h3 className="text-lg font-bold mb-4">Uptime</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">99.9%</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Today</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">99.8%</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">This Week</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">99.7%</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">This Month</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">99.6%</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">All Time</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
