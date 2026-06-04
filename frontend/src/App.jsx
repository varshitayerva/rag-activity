import { useState, useEffect } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { UploadPanel } from './components/UploadPanel'
import { FilterBar } from './components/FilterBar'
import { SourceCard } from './components/SourceCard'
import { MetricsBar } from './components/MetricsBar'
import { StatusIndicator } from './components/StatusIndicator'
import { UserProfile } from './components/UserProfile'
import { FeedbackPanel } from './components/FeedbackPanel'
import { CacheDashboard } from './components/CacheDashboard'
import { MonitoringDashboard } from './components/MonitoringDashboard'
import { AdminDashboard } from './components/AdminDashboard'
import { UserStatsDashboard } from './components/UserStatsDashboard'
import { apiClient } from './utils/api'
import { Search, Upload, Moon, Sun, Menu, X, User, MessageSquare, Zap, Activity, BarChart3, LineChart, LogOut, Lock, Copy, Check, Eye, EyeOff, AlertCircle } from 'lucide-react'

function App() {
  const [view, setView] = useState('chat')
  const [retrievedSources, setRetrievedSources] = useState([])
  const [filters, setFilters] = useState({ department: '', category: '', dateFrom: '', dateTo: '' })
  const [darkMode, setDarkMode] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [documentCount, setDocumentCount] = useState(0)
  const [chunkCount, setChunkCount] = useState(0)
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey') || '')
  const [showLoginModal, setShowLoginModal] = useState(!apiKey)
  const [loginError, setLoginError] = useState('')
  const [tempApiKey, setTempApiKey] = useState('')
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [userEmail, setUserEmail] = useState(localStorage.getItem('userEmail') || '')
  const [showPassword, setShowPassword] = useState(false)
  const [copied, setCopied] = useState(false)
  const [showApiInfo, setShowApiInfo] = useState(false)

  const handleLogin = async (e) => {
    e.preventDefault()
    setIsLoggingIn(true)
    setLoginError('')
    try {
      const response = await fetch('http://localhost:8003/api/user/profile', {
        headers: { 'X-API-Key': tempApiKey }
      })
      if (response.ok) {
        const data = await response.json()
        setApiKey(tempApiKey)
        setUserEmail(data.user.email)
        localStorage.setItem('apiKey', tempApiKey)
        localStorage.setItem('userEmail', data.user.email)
        setShowLoginModal(false)
        setTempApiKey('')
      } else {
        setLoginError('Invalid API key')
      }
    } catch (error) {
      setLoginError('Failed to authenticate. Make sure backend is running.')
    } finally {
      setIsLoggingIn(false)
    }
  }

  const handleLogout = () => {
    setApiKey('')
    setUserEmail('')
    localStorage.removeItem('apiKey')
    localStorage.removeItem('userEmail')
    setShowLoginModal(true)
  }

  useEffect(() => {
    if (!apiKey) return
    const fetchCounts = async () => {
      try {
        const docs = await apiClient.getDocuments()
        setDocumentCount(docs.documents.length)
      } catch (error) {
        console.error('Failed to fetch documents:', error)
      }
    }
    fetchCounts()
    const interval = setInterval(fetchCounts, 10000)
    return () => clearInterval(interval)
  }, [apiKey])

  useEffect(() => {
    const fetchChunks = async () => {
      try {
        const response = await fetch('http://localhost:8003/api/documents')
        if (response.ok) {
          const data = await response.json()
          let totalChunks = 0
          for (const doc of data.documents) {
            const chunksRes = await fetch(`http://localhost:8003/api/documents/${doc.id}/chunks`)
            if (chunksRes.ok) {
              const chunksData = await chunksRes.json()
              totalChunks += chunksData.count
            }
          }
          setChunkCount(totalChunks)
        }
      } catch (error) {
        console.error('Failed to fetch chunks:', error)
      }
    }
    fetchChunks()
  }, [documentCount])

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
  }

  const handleSourcesUpdate = (sources) => {
    setRetrievedSources(sources)
  }

  const handleUploadSuccess = (result) => {
    setDocumentCount(documentCount + 1)
  }

  const navItems = [
    { id: 'chat', label: 'Chat', icon: Search },
    { id: 'docs', label: 'Documents', icon: Upload },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'feedback', label: 'Feedback', icon: MessageSquare },
    { id: 'cache', label: 'Cache', icon: Zap },
    { id: 'monitoring', label: 'Monitoring', icon: Activity },
    { id: 'admin', label: 'Admin', icon: BarChart3 },
    { id: 'stats', label: 'My Stats', icon: LineChart },
  ]

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (showLoginModal) {
    return (
      <div className={`h-screen flex items-center justify-center ${darkMode ? 'dark' : ''} bg-gradient-to-br from-blue-600 via-blue-700 to-purple-800 dark:from-blue-900 dark:via-purple-900 dark:to-slate-950 overflow-auto`}>
        <div className="w-full max-w-md mx-4 my-8">
          {/* Main Login Card */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 border border-gray-200 dark:border-gray-700">
            {/* Logo */}
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-3xl flex items-center justify-center shadow-xl transform hover:scale-110 transition-transform duration-300">
                <Lock size={40} className="text-white" />
              </div>
            </div>

            {/* Header */}
            <h1 className="text-4xl font-black text-gray-900 dark:text-white text-center mb-2">AI Search Copilot</h1>
            <p className="text-gray-600 dark:text-gray-400 text-center mb-8 font-medium">Sign in with your API key</p>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-5">
              {/* API Key Input */}
              <div>
                <label className="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2">API Key</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={tempApiKey}
                    onChange={(e) => setTempApiKey(e.target.value)}
                    placeholder="sk-demo-key-12345"
                    className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-300"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              {/* Demo Key Info */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-600 p-4 rounded-lg">
                <p className="text-xs font-bold text-blue-900 dark:text-blue-300 mb-2">💡 Demo API Key:</p>
                <div className="flex items-center justify-between gap-2">
                  <code className="text-sm text-blue-800 dark:text-blue-200 font-mono font-bold flex-1 break-all">
                    sk-demo-key-12345
                  </code>
                  <button
                    type="button"
                    onClick={() => {
                      setTempApiKey('sk-demo-key-12345')
                      copyToClipboard('sk-demo-key-12345')
                    }}
                    className="flex-shrink-0 p-2 hover:bg-blue-100 dark:hover:bg-blue-800/40 rounded-lg transition-colors"
                  >
                    <Copy size={18} className="text-blue-600 dark:text-blue-400" />
                  </button>
                </div>
              </div>

              {/* Error Message */}
              {loginError && (
                <div className="p-4 bg-red-100 dark:bg-red-900/30 border-2 border-red-400 dark:border-red-600 rounded-xl text-red-700 dark:text-red-300 text-sm font-medium flex items-start gap-3">
                  <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
                  <span>{loginError}</span>
                </div>
              )}

              {/* Sign In Button */}
              <button
                type="submit"
                disabled={isLoggingIn || !tempApiKey}
                className="w-full bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-700 hover:via-purple-700 hover:to-pink-700 text-white font-bold py-3.5 px-4 rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                {isLoggingIn ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white border-r-transparent rounded-full animate-spin"></div>
                    Signing in...
                  </span>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            {/* API Info Section */}
            <button
              type="button"
              onClick={() => setShowApiInfo(!showApiInfo)}
              className="w-full mt-6 text-gray-600 dark:text-gray-400 text-sm font-medium py-2 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              {showApiInfo ? '▼ Hide' : '▶ Show'} API Information
            </button>

            {showApiInfo && (
              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/30 rounded-xl border border-gray-200 dark:border-gray-700 space-y-3">
                <div>
                  <p className="text-xs font-bold text-gray-600 dark:text-gray-400 mb-1">🔑 Generate API Key</p>
                  <button
                    type="button"
                    onClick={() => copyToClipboard('sk-' + Math.random().toString(36).slice(2, 15))}
                    className="text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg font-medium transition-colors"
                  >
                    Generate New Key
                  </button>
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  <p className="font-bold mb-1">📚 Documentation:</p>
                  <p>API keys are required for all authenticated requests. Keep them secure and never share them publicly.</p>
                </div>
              </div>
            )}
          </div>

          {/* Footer Info */}
          <div className="text-center mt-6 text-gray-200 text-xs">
            <p>🔒 Your data is encrypted and secure</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`h-screen flex flex-col ${darkMode ? 'dark' : ''}`}>
      {/* Header */}
      <header className="bg-gradient-to-br from-blue-600 via-blue-700 to-purple-800 dark:from-blue-900 dark:via-purple-900 dark:to-slate-950 text-white p-6 shadow-2xl border-b border-blue-500/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-200 to-blue-400 rounded-xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform duration-300">
              <Search className="text-blue-700" size={28} />
            </div>
            <div>
              <h1 className="text-3xl font-black bg-gradient-to-r from-white via-blue-100 to-purple-200 bg-clip-text text-transparent">
                AI Search Copilot
              </h1>
              <p className="text-blue-200 text-sm font-medium tracking-wide">Semantic RAG with Real-time Intelligence 🚀</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-blue-100">{userEmail || 'Demo User'}</p>
              <p className="text-xs text-blue-200">Logged in</p>
            </div>
            <div className="flex items-center gap-2 bg-white/10 backdrop-blur-md rounded-full p-1 border border-white/20">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2.5 rounded-full hover:bg-white/20 transition-all duration-300 transform hover:scale-110"
                title="Toggle dark mode"
              >
                {darkMode ? <Sun size={22} className="text-yellow-300" /> : <Moon size={22} className="text-blue-200" />}
              </button>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2.5 rounded-full hover:bg-white/20 transition-all duration-300 lg:hidden"
              >
                {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
              </button>
              <button
                onClick={handleLogout}
                className="p-2.5 rounded-full hover:bg-white/20 transition-all duration-300"
                title="Logout"
              >
                <LogOut size={22} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden bg-gray-50 dark:bg-gray-900">
        {/* Sidebar */}
        {sidebarOpen && (
          <aside className="w-72 bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 border-r border-gray-300 dark:border-gray-700 shadow-xl p-8 overflow-y-auto">
            <nav className="space-y-3">
              {navItems.map(item => {
                const Icon = item.icon
                return (
                  <button
                    key={item.id}
                    onClick={() => setView(item.id)}
                    className={`w-full flex items-center gap-3 px-5 py-3.5 rounded-xl font-semibold transition-all duration-300 transform ${
                      view === item.id
                        ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg scale-105 border border-blue-500'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700/50 hover:shadow-md border border-transparent'
                    }`}
                  >
                    <Icon size={22} />
                    <span>{item.label}</span>
                  </button>
                )
              })}
            </nav>

            {/* Stats */}
            <div className="mt-10 pt-8 border-t-2 border-gray-300 dark:border-gray-700 space-y-4">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-700 dark:to-blue-800 rounded-2xl p-5 shadow-lg text-white transform hover:scale-105 transition-transform duration-300">
                <p className="text-xs text-blue-100 font-semibold mb-2 uppercase tracking-wider">📚 Documents</p>
                <p className="text-4xl font-black">{documentCount}</p>
                <p className="text-xs text-blue-100 mt-2">Ready to search</p>
              </div>
              <StatusIndicator />
            </div>
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-hidden flex flex-col">
          {/* Metrics Bar */}
          <MetricsBar />

          {/* Content Area */}
          <div className="flex-1 overflow-hidden">
            {view === 'chat' && (
              <div className="h-full flex flex-col">
                <FilterBar onFilterChange={handleFilterChange} />
                <div className="flex-1 flex gap-4 overflow-hidden p-4">
                  <div className="flex-1 flex flex-col min-w-0">
                    <ChatPanel onSourcesUpdate={handleSourcesUpdate} filters={filters} />
                  </div>

                  {/* Right Sidebar - Retrieved Sources */}
                  <div className="w-2/5 bg-gradient-to-br from-white to-blue-50 dark:from-gray-800 dark:to-gray-900 rounded-2xl shadow-2xl border-2 border-blue-200 dark:border-blue-800 flex flex-col overflow-hidden">
                    <div className="p-5 border-b-2 border-blue-200 dark:border-blue-800 bg-gradient-to-r from-blue-600 via-blue-700 to-purple-800 dark:from-blue-900 dark:via-purple-900 dark:to-slate-950">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                        <h3 className="font-bold text-white text-lg">
                          Sources
                        </h3>
                        <span className="ml-auto bg-white/20 backdrop-blur-sm text-white text-sm px-3 py-1.5 rounded-full font-bold border border-white/30">
                          {retrievedSources.length}
                        </span>
                      </div>
                    </div>

                    {retrievedSources.length === 0 ? (
                      <div className="flex-1 flex items-center justify-center p-8">
                        <div className="text-center">
                          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                            <Search size={32} className="text-white" />
                          </div>
                          <p className="text-gray-600 dark:text-gray-400 text-sm font-semibold">
                            Start searching to see sources
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 overflow-y-auto p-5 space-y-4">
                        {retrievedSources.map((source, idx) => (
                          <SourceCard key={idx} source={source} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {view === 'docs' && (
              <div className="h-full overflow-y-auto p-8">
                <div className="max-w-3xl mx-auto">
                  <div className="mb-8">
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                      Document Management
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400">
                      Upload and manage your knowledge base documents
                    </p>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mb-8">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-sm">
                      <div className="text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                        {documentCount}
                      </div>
                      <p className="text-gray-600 dark:text-gray-400">Documents Indexed</p>
                    </div>
                    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700 shadow-sm">
                      <div className="text-4xl font-bold text-green-600 dark:text-green-400 mb-2">
                        {chunkCount}
                      </div>
                      <p className="text-gray-600 dark:text-gray-400">Chunks Ready to Search</p>
                    </div>
                  </div>

                  <UploadPanel onUploadSuccess={handleUploadSuccess} />
                </div>
              </div>
            )}

            {view === 'profile' && (
              <div className="h-full overflow-y-auto p-8">
                <div className="max-w-4xl mx-auto">
                  <UserProfile apiKey={apiKey} />
                </div>
              </div>
            )}

            {view === 'feedback' && (
              <div className="h-full overflow-y-auto p-8">
                <div className="max-w-3xl mx-auto">
                  <FeedbackPanel apiKey={apiKey} />
                </div>
              </div>
            )}

            {view === 'cache' && (
              <div className="h-full overflow-y-auto p-8">
                <div className="max-w-4xl mx-auto">
                  <CacheDashboard apiKey={apiKey} />
                </div>
              </div>
            )}

            {view === 'monitoring' && (
              <div className="h-full overflow-y-auto p-8">
                <div className="max-w-6xl mx-auto">
                  <MonitoringDashboard apiKey={apiKey} />
                </div>
              </div>
            )}

            {view === 'admin' && (
              <div className="h-full overflow-y-auto p-8">
                <div className="max-w-6xl mx-auto">
                  <AdminDashboard />
                </div>
              </div>
            )}

            {view === 'stats' && (
              <div className="h-full overflow-y-auto">
                <UserStatsDashboard />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
