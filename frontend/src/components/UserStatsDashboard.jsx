import { useState, useEffect } from 'react'
import { User, Search, Zap, Calendar, TrendingUp } from 'lucide-react'

export function UserStatsDashboard() {
  const [userStats, setUserStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUserStats = async () => {
      try {
        const response = await fetch('http://localhost:8002/api/user/stats', {
          headers: { 'X-API-Key': 'sk-demo-key-12345' }
        })
        const data = await response.json()
        setUserStats(data.stats)
      } catch (error) {
        console.error('Failed to fetch user stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchUserStats()
    const interval = setInterval(fetchUserStats, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return <div className="text-center py-8">Loading user stats...</div>

  if (!userStats) return <div className="text-center py-8 text-red-500">Failed to load user stats</div>

  return (
    <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 min-h-screen">
      <h1 className="text-4xl font-bold mb-8 text-gray-900 dark:text-white">
        My Statistics
      </h1>

      {/* User Info Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Username</h3>
            <User className="text-blue-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{userStats.username}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Role: {userStats.role}</p>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Department</h3>
            <Zap className="text-purple-500" size={24} />
          </div>
          <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{userStats.department || 'N/A'}</p>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Member Since</h3>
            <Calendar className="text-green-500" size={24} />
          </div>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {new Date(userStats.member_since).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Activity Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Total Searches</h3>
            <Search className="text-blue-500" size={32} />
          </div>
          <p className="text-6xl font-bold text-blue-600 dark:text-blue-400">{userStats.search_count}</p>
          <div className="mt-4 bg-blue-100 dark:bg-blue-900/30 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">Semantic searches performed</p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Generations</h3>
            <Zap className="text-purple-500" size={32} />
          </div>
          <p className="text-6xl font-bold text-purple-600 dark:text-purple-400">{userStats.generation_count}</p>
          <div className="mt-4 bg-purple-100 dark:bg-purple-900/30 rounded-lg p-3">
            <p className="text-sm text-purple-700 dark:text-purple-300">LLM answers generated</p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Total Queries</h3>
            <TrendingUp className="text-green-500" size={32} />
          </div>
          <p className="text-6xl font-bold text-green-600 dark:text-green-400">{userStats.total_queries}</p>
          <div className="mt-4 bg-green-100 dark:bg-green-900/30 rounded-lg p-3">
            <p className="text-sm text-green-700 dark:text-green-300">Combined searches & generations</p>
          </div>
        </div>
      </div>

      {/* Activity Breakdown */}
      <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-8 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Activity Breakdown</h2>

        <div className="space-y-6">
          {/* Search Activity */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-gray-700 dark:text-gray-300 font-semibold">Search Activity</span>
              <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {userStats.total_queries > 0 ? Math.round((userStats.search_count / userStats.total_queries) * 100) : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full"
                style={{width: `${userStats.total_queries > 0 ? (userStats.search_count / userStats.total_queries) * 100 : 0}%`}}
              ></div>
            </div>
          </div>

          {/* Generation Activity */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-gray-700 dark:text-gray-300 font-semibold">Generation Activity</span>
              <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {userStats.total_queries > 0 ? Math.round((userStats.generation_count / userStats.total_queries) * 100) : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-purple-500 to-purple-600 h-3 rounded-full"
                style={{width: `${userStats.total_queries > 0 ? (userStats.generation_count / userStats.total_queries) * 100 : 0}%`}}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Last Login */}
      <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-3">Last Login</h3>
        <p className="text-gray-600 dark:text-gray-400">
          {userStats.last_login
            ? new Date(userStats.last_login).toLocaleString()
            : 'No login recorded'
          }
        </p>
      </div>
    </div>
  )
}
