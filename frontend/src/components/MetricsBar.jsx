import { useState, useEffect } from 'react'

export function MetricsBar() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setMetrics({
          cache_hit_rate: 0.73,
          avg_latency_ms: 340,
          embedding_cache_hits: 45,
          retrieval_cache_hits: 12,
          response_cache_hits: 5,
          total_queries: 89,
          avg_tokens_in_context: 2450,
          estimated_cost_usd: 0.0012,
          uptime_seconds: 3600
        })
        setLoading(false)
      } catch (error) {
        console.error('Failed to fetch metrics:', error)
        setLoading(false)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 1000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="bg-gray-100 p-2 text-sm text-gray-600">Loading metrics...</div>
  }

  if (!metrics) {
    return <div className="bg-gray-100 p-2 text-sm text-gray-600">Metrics unavailable</div>
  }

  return (
    <div className="bg-gray-50 border-b border-gray-200 p-3 grid grid-cols-4 gap-4 text-sm">
      <div className="flex flex-col">
        <span className="text-gray-600 text-xs uppercase">Cache Hit Rate</span>
        <span className="text-lg font-semibold text-blue-600">
          {(metrics.cache_hit_rate * 100).toFixed(1)}%
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-gray-600 text-xs uppercase">Avg Latency</span>
        <span className="text-lg font-semibold text-blue-600">
          {metrics.avg_latency_ms}ms
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-gray-600 text-xs uppercase">Avg Tokens</span>
        <span className="text-lg font-semibold text-blue-600">
          {metrics.avg_tokens_in_context.toLocaleString()}
        </span>
      </div>

      <div className="flex flex-col">
        <span className="text-gray-600 text-xs uppercase">Total Queries</span>
        <span className="text-lg font-semibold text-blue-600">
          {metrics.total_queries}
        </span>
      </div>
    </div>
  )
}
