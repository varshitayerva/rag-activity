import { useState, useEffect } from 'react'
import { User, Mail, Building2, Shield, LogIn, Copy, Check, Edit2, Save, X } from 'lucide-react'

export function UserProfile({ apiKey = 'sk-demo-key-12345' }) {
  const [profile, setProfile] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const [profileRes, statsRes] = await Promise.all([
          fetch('http://localhost:8003/api/user/profile', {
            headers: { 'X-API-Key': apiKey }
          }).then(r => r.json()),
          fetch('http://localhost:8003/api/user/stats', {
            headers: { 'X-API-Key': apiKey }
          }).then(r => r.json())
        ])
        setProfile(profileRes.user)
        setStats(statsRes.stats)
        setEditData(profileRes.user || {})
      } catch (error) {
        console.error('Failed to fetch profile:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [apiKey])

  const handleEdit = () => {
    setIsEditing(true)
    setEditData({ ...profile })
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const response = await fetch('http://localhost:8003/api/user/profile', {
        method: 'PUT',
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editData)
      })
      if (response.ok) {
        const result = await response.json()
        setProfile(result.user)
        setIsEditing(false)
      }
    } catch (error) {
      console.error('Failed to save profile:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditData({ ...profile })
  }

  const handleInputChange = (field, value) => {
    setEditData(prev => ({ ...prev, [field]: value }))
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(apiKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) return <div className="text-center py-8">Loading profile...</div>
  if (!profile) return <div className="text-center py-8 text-red-500">Failed to load profile</div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
              <User size={32} />
            </div>
            <div>
              <h1 className="text-3xl font-bold">
                {isEditing ? (
                  <input
                    type="text"
                    value={editData.username || ''}
                    onChange={(e) => handleInputChange('username', e.target.value)}
                    className="bg-white/20 border-2 border-white/40 rounded px-2 py-1 text-white placeholder-white/60"
                  />
                ) : (
                  profile.username
                )}
              </h1>
              <p className="text-blue-100">
                {isEditing ? (
                  <input
                    type="text"
                    value={editData.department || ''}
                    onChange={(e) => handleInputChange('department', e.target.value)}
                    className="bg-white/20 border-2 border-white/40 rounded px-2 py-1 text-white placeholder-white/60 text-sm"
                    placeholder="Department"
                  />
                ) : (
                  profile.department || 'No department'
                )}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={isEditing ? handleSave : handleEdit}
              disabled={saving}
              className="flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white font-bold py-2 px-4 rounded-lg transition disabled:opacity-50"
            >
              {isEditing ? (
                <>
                  <Save size={18} />
                  {saving ? 'Saving...' : 'Save'}
                </>
              ) : (
                <>
                  <Edit2 size={18} />
                  Edit
                </>
              )}
            </button>
            {isEditing && (
              <button
                onClick={handleCancel}
                className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white font-bold py-2 px-4 rounded-lg transition"
              >
                <X size={18} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Profile Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Account Information</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Email</label>
              {isEditing ? (
                <input
                  type="email"
                  value={editData.email || ''}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              ) : (
                <div className="flex items-center gap-2 mt-1">
                  <Mail size={18} className="text-blue-500" />
                  <span className="text-gray-900 dark:text-white">{profile.email}</span>
                </div>
              )}
            </div>

            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Role</label>
              <div className="flex items-center gap-2 mt-1">
                <Shield size={18} className={profile.role === 'admin' ? 'text-red-500' : 'text-green-500'} />
                <span className="text-gray-900 dark:text-white capitalize">{profile.role}</span>
              </div>
            </div>

            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Department</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editData.department || ''}
                  onChange={(e) => handleInputChange('department', e.target.value)}
                  className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              ) : (
                <div className="flex items-center gap-2 mt-1">
                  <Building2 size={18} className="text-purple-500" />
                  <span className="text-gray-900 dark:text-white">{profile.department || 'N/A'}</span>
                </div>
              )}
            </div>

            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Member Since</label>
              <p className="text-gray-900 dark:text-white mt-1">
                {new Date(profile.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* API Key */}
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">API Key</h2>
          <div className="bg-gray-100 dark:bg-gray-600 rounded-lg p-4 mb-4">
            <code className="text-sm text-gray-700 dark:text-gray-300 break-all">{apiKey}</code>
          </div>
          <button
            onClick={copyToClipboard}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition"
          >
            {copied ? (
              <>
                <Check size={18} />
                Copied!
              </>
            ) : (
              <>
                <Copy size={18} />
                Copy API Key
              </>
            )}
          </button>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-3">
            Use this key for API requests in the X-API-Key header
          </p>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Searches</p>
          <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.search_count}</p>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Generations</p>
          <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.generation_count}</p>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Total Queries</p>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">{stats.total_queries}</p>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/30 dark:to-orange-800/30 rounded-lg p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Last Login</p>
          <p className="text-lg font-bold text-orange-600 dark:text-orange-400">
            {stats.last_login ? new Date(stats.last_login).toLocaleDateString() : 'Never'}
          </p>
        </div>
      </div>
    </div>
  )
}
