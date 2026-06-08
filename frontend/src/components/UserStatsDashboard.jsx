import { useState, useEffect } from 'react'
import { User, Search, Zap, Calendar, TrendingUp } from 'lucide-react'
import { API_CONFIG } from '../config/api'

export function UserStatsDashboard({ apiKey = '' }) {
  const [userStats, setUserStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUserStats = async () => {
      try {
        const [profileResponse, statsResponse] = await Promise.all([
          fetch(API_CONFIG.auth.profile, {
            headers: { 'X-API-Key': apiKey }
          }),
          fetch(API_CONFIG.user.stats, {
            headers: { 'X-API-Key': apiKey }
          })
        ])

        let profileData = {}
        let statsData = {}

        if (profileResponse.ok) {
          const data = await profileResponse.json()
          profileData = data.user || data
        }

        if (statsResponse.ok) {
          const data = await statsResponse.json()
          statsData = data.stats || data
        }

        setUserStats({
          username: profileData.username || 'Unknown',
          role: profileData.role || 'user',
          department: profileData.department || 'N/A',
          email: profileData.email || 'N/A',
          created_at: profileData.created_at,
          last_login: profileData.last_login,
          search_count: statsData.search_count || 0,
          generation_count: statsData.generation_count || 0,
          total_queries: statsData.total_queries || 0
        })
      } catch (error) {
        console.error('Failed to fetch user stats:', error)
        setUserStats({
          username: 'Error',
          role: 'user',
          department: 'N/A',
          email: 'N/A',
          created_at: null,
          last_login: null,
          search_count: 0,
          generation_count: 0,
          total_queries: 0
        })
      } finally {
        setLoading(false)
      }
    }

    if (apiKey) {
      fetchUserStats()
      const interval = setInterval(fetchUserStats, 30000)
      return () => clearInterval(interval)
    }
  }, [apiKey])

  if (loading) return <div className="text-center py-8 text-gray-600 dark:text-gray-400">Loading user stats...</div>

  if (!userStats || (userStats.username === 'Error' && !apiKey)) return (
    <div className="text-center py-12 text-gray-600 dark:text-gray-400">
      <p className="mb-2">Unable to load user statistics</p>
      <p className="text-sm">Please make sure you are logged in with a valid API key</p>
    </div>
  )

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
            {userStats.created_at
              ? new Date(userStats.created_at).toLocaleDateString()
              : 'N/A'
            }
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
          <p className="text-6xl font-bold text-blue-600 dark:text-blue-400">{userStats.search_count || 0}</p>
          <div className="mt-4 bg-blue-100 dark:bg-blue-900/30 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">Semantic searches performed</p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Generations</h3>
            <Zap className="text-purple-500" size={32} />
          </div>
          <p className="text-6xl font-bold text-purple-600 dark:text-purple-400">{userStats.generation_count || 0}</p>
          <div className="mt-4 bg-purple-100 dark:bg-purple-900/30 rounded-lg p-3">
            <p className="text-sm text-purple-700 dark:text-purple-300">LLM answers generated</p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Total Queries</h3>
            <TrendingUp className="text-green-500" size={32} />
          </div>
          <p className="text-6xl font-bold text-green-600 dark:text-green-400">{userStats.total_queries || 0}</p>
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
                {(userStats.total_queries && userStats.total_queries > 0) ? Math.round(((userStats.search_count || 0) / userStats.total_queries) * 100) : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full"
                style={{width: `${(userStats.total_queries && userStats.total_queries > 0) ? ((userStats.search_count || 0) / userStats.total_queries) * 100 : 0}%`}}
              ></div>
            </div>
          </div>

          {/* Generation Activity */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <span className="text-gray-700 dark:text-gray-300 font-semibold">Generation Activity</span>
              <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {(userStats.total_queries && userStats.total_queries > 0) ? Math.round(((userStats.generation_count || 0) / userStats.total_queries) * 100) : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-purple-500 to-purple-600 h-3 rounded-full"
                style={{width: `${(userStats.total_queries && userStats.total_queries > 0) ? ((userStats.generation_count || 0) / userStats.total_queries) * 100 : 0}%`}}
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
