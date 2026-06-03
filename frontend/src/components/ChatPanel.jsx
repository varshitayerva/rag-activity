import { useState } from 'react'
import { apiClient } from '../utils/api'
import { Send, Zap, AlertCircle } from 'lucide-react'

export function ChatPanel({ onSourcesUpdate }) {
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || loading) return

    const userQuery = query
    setQuery('')
    setMessages(prev => [...prev, { role: 'user', content: userQuery }])
    setLoading(true)

    try {
      // First, search for relevant chunks
      const searchResults = await apiClient.search(userQuery)
      const chunks = searchResults.results || []

      // Notify parent of retrieved sources
      onSourcesUpdate?.(chunks)

      // Add AI response
      let fullResponse = 'Searching your knowledge base...'
      setMessages(prev => [...prev, { role: 'assistant', content: fullResponse, sources: chunks }])

      // For now, just show search results
      // In phase 2, this will use streaming generation with Groq
      const responseText = `Found ${chunks.length} relevant results for your query.\n\nTop matches:\n${chunks.slice(0, 3).map(c => `• ${c.text?.substring(0, 100)}...`).join('\n')}`

      setMessages(prev => {
        const last = prev[prev.length - 1]
        if (last?.role === 'assistant') {
          return [
            ...prev.slice(0, -1),
            { role: 'assistant', content: responseText, sources: chunks }
          ]
        }
        return prev
      })
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        error: true
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Zap size={24} className="text-blue-600" />
          AI Chat
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Ask questions about your documents using semantic search
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap size={32} className="text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Welcome to AI Search
              </h3>
              <p className="text-gray-600 dark:text-gray-400 max-w-xs">
                Ask questions about Kubernetes, Docker, Python, or any of your indexed documents
              </p>

              {/* Quick Suggestions */}
              <div className="mt-6 space-y-2">
                <p className="text-xs text-gray-500 dark:text-gray-500 mb-3">Try asking:</p>
                {[
                  'What is Kubernetes?',
                  'How do I restart a pod?',
                  'Docker networking guide',
                  'Python best practices'
                ].map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuery(suggestion)
                      document.querySelector('form')?.dispatchEvent(
                        new Event('submit', { bubbles: true })
                      )
                    }}
                    className="block w-full px-4 py-2 text-sm text-left text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
          >
            <div
              className={`max-w-md px-4 py-3 rounded-2xl ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-br-none shadow-lg'
                  : msg.error
                  ? 'bg-red-100 dark:bg-red-900/20 text-red-900 dark:text-red-400 rounded-bl-none border border-red-300 dark:border-red-800'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-none border border-gray-200 dark:border-gray-600'
              }`}
            >
              {msg.error && (
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={16} />
                  <span className="font-semibold text-sm">Error</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.tokens && (
                <p className="text-xs mt-2 opacity-75">Tokens: {msg.tokens}</p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-gray-100 dark:bg-gray-700 px-4 py-3 rounded-2xl rounded-bl-none">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about your documents..."
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 rounded-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center gap-2 shadow-lg"
          >
            <Send size={18} />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </form>
    </div>
  )
}
