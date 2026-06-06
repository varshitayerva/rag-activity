import { useState, useEffect } from 'react'
import { Users, Trash2, Shield, CheckCircle, AlertCircle, UserPlus, Lock } from 'lucide-react'
import { API_CONFIG } from '../config/api'

export function AdminDashboard({ apiKey }) {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    if (apiKey) {
      fetchUsers()
      const interval = setInterval(fetchUsers, 10000)
      return () => clearInterval(interval)
    }
  }, [apiKey])

  const fetchUsers = async () => {
    try {
      const res = await fetch(API_CONFIG.admin.users, {
        headers: { 'X-API-Key': apiKey }
      })

      if (res.ok) {
        const data = await res.json()
        setUsers(data.users || [])
      } else {
        console.error('Failed to fetch users:', res.status)
        setUsers([])
      }
    } catch (error) {
      console.error('Failed to fetch users:', error)
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  const filteredUsers = users.filter(user => {
    if (filter === 'active') return user.recently_active
    if (filter === 'inactive') return !user.recently_active
    return true
  })

  const stats = {
    total_users: users.length,
    active_users: users.filter(u => u.recently_active).length,
    inactive_users: users.filter(u => !u.recently_active).length
  }

  if (loading) return <div className="text-center py-8 text-gray-400">Loading users...</div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-orange-600 rounded-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">User Management</h1>
            <p className="text-red-100">Manage system users and permissions</p>
          </div>
          <Users size={48} className="opacity-80" />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Total Users</p>
          <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">
            {stats.total_users}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Registered accounts</p>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Active Users</p>
          <p className="text-4xl font-bold text-green-600 dark:text-green-400">
            {stats.active_users}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Logged in users</p>
        </div>

        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Inactive Users</p>
          <p className="text-4xl font-bold text-orange-600 dark:text-orange-400">
            {stats.inactive_users}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Disabled accounts</p>
        </div>
      </div>

      {/* Filter & Search */}
      <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-semibold transition ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white'
            }`}
          >
            All Users
          </button>
          <button
            onClick={() => setFilter('active')}
            className={`px-4 py-2 rounded-lg font-semibold transition ${
              filter === 'active'
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setFilter('inactive')}
            className={`px-4 py-2 rounded-lg font-semibold transition ${
              filter === 'inactive'
                ? 'bg-orange-600 text-white'
                : 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white'
            }`}
          >
            Inactive
          </button>
        </div>

        {/* Users Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-300 dark:border-gray-600">
                <th className="px-4 py-3 text-gray-700 dark:text-gray-300 font-semibold">Username</th>
                <th className="px-4 py-3 text-gray-700 dark:text-gray-300 font-semibold">Email</th>
                <th className="px-4 py-3 text-gray-700 dark:text-gray-300 font-semibold">Department</th>
                <th className="px-4 py-3 text-gray-700 dark:text-gray-300 font-semibold">Status</th>
                <th className="px-4 py-3 text-gray-700 dark:text-gray-300 font-semibold">Joined</th>
                <th className="px-4 py-3 text-gray-700 dark:text-gray-300 font-semibold">Last Login</th>
                <th className="px-4 py-3 text-gray-700 dark:text-gray-300 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600/50 transition"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                          {user.username[0].toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {user.username}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{user.email}</td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {user.department || 'N/A'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {user.recently_active ? (
                          <>
                            <CheckCircle size={18} className="text-green-500" />
                            <span className="text-green-600 dark:text-green-400 text-sm font-semibold">
                              Active (last 24h)
                            </span>
                          </>
                        ) : (
                          <>
                            <AlertCircle size={18} className="text-orange-500" />
                            <span className="text-orange-600 dark:text-orange-400 text-sm font-semibold">
                              Inactive
                            </span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300 text-sm">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300 text-sm">
                      {user.last_login
                        ? new Date(user.last_login).toLocaleDateString()
                        : 'Never'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          title={user.is_active ? 'Disable user' : 'Enable user'}
                          className="p-2 hover:bg-orange-100 dark:hover:bg-orange-900/30 rounded transition text-orange-600 dark:text-orange-400"
                        >
                          <Lock size={18} />
                        </button>
                        <button
                          title="Delete user"
                          className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition text-red-600 dark:text-red-400"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* System Controls */}
      <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">System Controls</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button className="flex items-center gap-3 p-4 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg transition">
            <Shield className="text-blue-600 dark:text-blue-400" size={24} />
            <div className="text-left">
              <p className="font-semibold text-gray-900 dark:text-white">Reset API Keys</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Invalidate all user API keys</p>
            </div>
          </button>

          <button className="flex items-center gap-3 p-4 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg transition">
            <UserPlus className="text-green-600 dark:text-green-400" size={24} />
            <div className="text-left">
              <p className="font-semibold text-gray-900 dark:text-white">Clear Cache</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Clear all system caches</p>
            </div>
          </button>

          <button className="flex items-center gap-3 p-4 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg transition">
            <AlertCircle className="text-orange-600 dark:text-orange-400" size={24} />
            <div className="text-left">
              <p className="font-semibold text-gray-900 dark:text-white">System Settings</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Configure system parameters</p>
            </div>
          </button>

          <button className="flex items-center gap-3 p-4 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg transition">
            <Lock className="text-red-600 dark:text-red-400" size={24} />
            <div className="text-left">
              <p className="font-semibold text-gray-900 dark:text-white">Maintenance Mode</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Enable system maintenance</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}
