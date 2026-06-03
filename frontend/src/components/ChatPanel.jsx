import { useState } from 'react'
import { apiClient } from '../utils/api'
import { Send, Zap, AlertCircle } from 'lucide-react'

export function ChatPanel({ onSourcesUpdate, filters = {} }) {
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
      // Generate answer with sources using Groq
      const generatedResult = await apiClient.generate(userQuery, 10, filters)
      const chunks = generatedResult.sources || []
      const answer = generatedResult.answer || 'No answer generated'

      // Notify parent of retrieved sources
      onSourcesUpdate?.(chunks)

      // Display the LLM-generated answer
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: answer, sources: chunks }
      ])
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
    <div className="flex flex-col h-full bg-gradient-to-br from-white to-blue-50/30 dark:from-gray-800 dark:to-gray-900 rounded-2xl shadow-2xl border-2 border-blue-200 dark:border-blue-800/40 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b-2 border-blue-200 dark:border-blue-800 bg-gradient-to-r from-blue-600 via-blue-700 to-purple-800 dark:from-blue-900 dark:via-purple-900 dark:to-slate-950">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <div className="p-1.5 bg-white/20 rounded-lg">
            <Zap size={20} className="text-yellow-300" />
          </div>
          Chat
        </h2>
        <p className="text-blue-100 text-xs mt-1 font-medium">🔍 Semantic search</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-7 space-y-5">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-sm">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                <Zap size={40} className="text-white" />
              </div>
              <h3 className="text-2xl font-black text-gray-900 dark:text-white mb-3">
                Welcome! 👋
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
                Start by typing a question about your documents, or try one of the suggestions below
              </p>

              {/* Quick Suggestions */}
              <div className="space-y-3">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 uppercase font-bold tracking-wider">✨ Quick Examples:</p>
                {[
                  'What is Kubernetes?',
                  'How do I restart a pod?',
                  'What is Docker?',
                  'Python best practices'
                ].map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setQuery(suggestion)
                      setTimeout(() => {
                        const form = document.querySelector('form')
                        if (form) {
                          form.dispatchEvent(new Event('submit', { bubbles: true }))
                        }
                      }, 0)
                    }}
                    className="block w-full px-5 py-3 text-sm text-left font-medium text-blue-700 dark:text-blue-300 bg-gradient-to-r from-blue-100 to-blue-50 dark:from-blue-900/30 dark:to-blue-800/20 hover:from-blue-200 hover:to-blue-100 dark:hover:from-blue-900/50 dark:hover:to-blue-800/40 rounded-xl transition-all duration-300 border-2 border-blue-200 dark:border-blue-700/50 hover:shadow-md"
                  >
                    💡 {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in gap-3`}
          >
            <div
              className={`max-w-xl px-5 py-4 rounded-2xl font-medium ${
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-br-none shadow-xl hover:shadow-2xl transition-shadow'
                  : msg.error
                  ? 'bg-gradient-to-br from-red-100 to-red-50 dark:from-red-900/30 dark:to-red-800/20 text-red-900 dark:text-red-400 rounded-bl-none border-2 border-red-300 dark:border-red-700'
                  : 'bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-700/50 dark:to-gray-800/50 text-gray-900 dark:text-gray-100 rounded-bl-none border-2 border-gray-300 dark:border-gray-600'
              }`}
            >
              {msg.error && (
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={18} className="flex-shrink-0" />
                  <span className="font-bold text-sm">⚠️ Error</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.tokens && (
                <p className="text-xs mt-3 opacity-75 pt-2 border-t border-white/20">🪙 {msg.tokens} tokens</p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start animate-fade-in gap-3">
            <div className="bg-gradient-to-r from-blue-100 to-blue-50 dark:from-blue-900/30 dark:to-blue-800/20 px-6 py-4 rounded-2xl rounded-bl-none border-2 border-blue-300 dark:border-blue-700/50 shadow-md">
              <div className="flex gap-3 items-center">
                <div className="flex gap-2">
                  <div className="w-3 h-3 bg-gradient-to-r from-blue-600 to-blue-700 rounded-full animate-bounce"></div>
                  <div className="w-3 h-3 bg-gradient-to-r from-blue-600 to-blue-700 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-3 h-3 bg-gradient-to-r from-blue-600 to-blue-700 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
                <p className="text-sm font-semibold text-blue-700 dark:text-blue-300">Generating answer...</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-6 border-t-2 border-blue-200 dark:border-blue-800 bg-gradient-to-r from-white to-blue-50 dark:from-gray-800 dark:to-gray-900">
        <div className="flex gap-3 items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="🔍 Ask anything about your documents..."
            disabled={loading}
            className="flex-1 px-5 py-3 rounded-full bg-white dark:bg-gray-700/50 border-2 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 disabled:opacity-60 transition-all duration-300"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-7 py-3 rounded-full bg-gradient-to-r from-blue-600 via-blue-700 to-purple-700 hover:from-blue-700 hover:via-blue-800 hover:to-purple-800 text-white font-bold hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center gap-2 shadow-xl transform hover:scale-105"
          >
            <Send size={20} />
            <span className="hidden sm:inline">Search</span>
          </button>
        </div>
      </form>
    </div>
  )
}
