import { useState, useEffect } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { UploadPanel } from './components/UploadPanel'
import { FilterBar } from './components/FilterBar'
import { SourceCard } from './components/SourceCard'
import { MetricsBar } from './components/MetricsBar'
import { ArchitectureDiagram } from './components/ArchitectureDiagram'
import { Search, Upload, Zap, Moon, Sun, Menu, X } from 'lucide-react'

function App() {
  const [view, setView] = useState('chat')
  const [retrievedSources, setRetrievedSources] = useState([])
  const [filters, setFilters] = useState({ department: '', category: '', dateFrom: '', dateTo: '' })
  const [darkMode, setDarkMode] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [documentCount, setDocumentCount] = useState(3)

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

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
    { id: 'architecture', label: 'Architecture', icon: Zap },
  ]

  return (
    <div className={`h-screen flex flex-col ${darkMode ? 'dark' : ''}`}>
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 dark:from-blue-900 dark:to-blue-950 text-white p-4 shadow-lg border-b border-blue-700">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <Zap className="text-blue-600" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
                AI Search Copilot
              </h1>
              <p className="text-blue-100 text-xs">Semantic RAG with Real Embeddings</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition"
              title="Toggle dark mode"
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition lg:hidden"
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden bg-gray-50 dark:bg-gray-900">
        {/* Sidebar */}
        {sidebarOpen && (
          <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 shadow-sm p-6 overflow-y-auto">
            <nav className="space-y-3">
              {navItems.map(item => {
                const Icon = item.icon
                return (
                  <button
                    key={item.id}
                    onClick={() => setView(item.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition ${
                      view === item.id
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon size={20} />
                    {item.label}
                  </button>
                )
              })}
            </nav>

            {/* Stats */}
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700 space-y-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Documents</p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{documentCount}</p>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Status</p>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <p className="text-sm font-semibold text-green-600 dark:text-green-400">Online</p>
                </div>
              </div>
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
                    <ChatPanel onSourcesUpdate={handleSourcesUpdate} />
                  </div>

                  {/* Right Sidebar - Retrieved Sources */}
                  <div className="w-96 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
                    <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          Retrieved Sources
                        </h3>
                        <span className="ml-auto bg-blue-600 text-white text-xs px-2 py-1 rounded-full font-semibold">
                          {retrievedSources.length}
                        </span>
                      </div>
                    </div>

                    {retrievedSources.length === 0 ? (
                      <div className="flex-1 flex items-center justify-center p-6">
                        <div className="text-center">
                          <Search size={40} className="text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                          <p className="text-gray-500 dark:text-gray-400 text-sm">
                            Search to see sources
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 overflow-y-auto p-4 space-y-3">
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
                        15
                      </div>
                      <p className="text-gray-600 dark:text-gray-400">Chunks Ready to Search</p>
                    </div>
                  </div>

                  <UploadPanel onUploadSuccess={handleUploadSuccess} />
                </div>
              </div>
            )}

            {view === 'architecture' && (
              <div className="h-full overflow-y-auto p-8 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
                <div className="max-w-6xl mx-auto">
                  <div className="mb-8">
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                      System Architecture
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400">
                      RAG System with Real Embeddings & Semantic Search
                    </p>
                  </div>
                  <ArchitectureDiagram />
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
