import { useState } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { UploadPanel } from './components/UploadPanel'
import { FilterBar } from './components/FilterBar'
import { SourceCard } from './components/SourceCard'
import { MetricsBar } from './components/MetricsBar'
import { ArchitectureDiagram } from './components/ArchitectureDiagram'

function App() {
  const [view, setView] = useState('chat')
  const [retrievedSources, setRetrievedSources] = useState([])
  const [filters, setFilters] = useState({ department: '', category: '', dateFrom: '', dateTo: '' })

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
    console.log('Filters changed:', newFilters)
    // TODO: Re-run search with new filters in Phase 2 enhancement
  }

  const handleSourcesUpdate = (sources) => {
    setRetrievedSources(sources)
  }

  const handleUploadSuccess = (result) => {
    console.log('Document uploaded successfully:', result)
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      <header className="bg-blue-600 text-white p-4 shadow">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Technical Support Copilot</h1>
            <p className="text-blue-100 text-sm">Powered by RAG with semantic search</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setView('chat')}
              className={`px-4 py-2 rounded ${
                view === 'chat'
                  ? 'bg-blue-700'
                  : 'bg-blue-500 hover:bg-blue-700'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setView('docs')}
              className={`px-4 py-2 rounded ${
                view === 'docs'
                  ? 'bg-blue-700'
                  : 'bg-blue-500 hover:bg-blue-700'
              }`}
            >
              Upload Docs
            </button>
            <button
              onClick={() => setView('architecture')}
              className={`px-4 py-2 rounded ${
                view === 'architecture'
                  ? 'bg-blue-700'
                  : 'bg-blue-500 hover:bg-blue-700'
              }`}
            >
              Architecture
            </button>
          </div>
        </div>
      </header>

      <MetricsBar />

      <main className="flex-1 overflow-hidden">
        {view === 'chat' && (
          <div className="h-full flex flex-col">
            <FilterBar onFilterChange={handleFilterChange} />
            <div className="flex-1 flex gap-4 overflow-hidden p-4">
              <div className="flex-1 flex flex-col min-w-0">
                <ChatPanel onSourcesUpdate={handleSourcesUpdate} />
              </div>

              <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">
                    Retrieved Sources ({retrievedSources.length})
                  </h3>
                  {retrievedSources.length === 0 ? (
                    <p className="text-gray-500 text-sm">
                      Run a search to see sources
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {retrievedSources.map((source, idx) => (
                        <SourceCard key={idx} source={source} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {view === 'docs' && (
          <div className="h-full overflow-y-auto p-4">
            <div className="max-w-2xl mx-auto">
              <UploadPanel onUploadSuccess={handleUploadSuccess} />
              <div className="mt-6">
                <h3 className="font-semibold text-gray-900 mb-3">Sample Documents</h3>
                <p className="text-gray-600 text-sm">
                  Waiting for M1 ingestion pipeline. Will display indexed documents here.
                </p>
              </div>
            </div>
          </div>
        )}

        {view === 'architecture' && (
          <div className="h-full overflow-y-auto p-4">
            <div className="max-w-4xl mx-auto">
              <ArchitectureDiagram />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
