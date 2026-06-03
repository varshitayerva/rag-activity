import { useState } from 'react'
import { apiClient } from '../utils/api'

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
      const chunks = searchResults.chunks || []

      // Notify parent of retrieved sources
      onSourcesUpdate?.(chunks)

      // Then stream the response
      let fullResponse = ''
      let sources = []

      for await (const event of apiClient.generateStreaming(userQuery, chunks)) {
        if (event.type === 'metadata') {
          sources = event.sources
        } else if (event.type === 'token') {
          fullResponse += event.content
          // Update message in real-time
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last?.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                { role: 'assistant', content: fullResponse, sources }
              ]
            }
            return prev
          })
        } else if (event.type === 'done') {
          // Final update with token counts
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last?.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                {
                  role: 'assistant',
                  content: fullResponse,
                  sources,
                  tokens: event.input_tokens ? `${event.input_tokens} → ${event.output_tokens}` : null
                }
              ]
            }
            return prev
          })
        }
      }
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
    <div className="flex flex-col h-full border-r border-gray-200">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">Welcome to Technical Support Copilot</p>
            <p className="text-sm mt-2">Ask a question to get started</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : msg.error
                  ? 'bg-red-100 text-red-900'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 text-xs opacity-70">
                  📎 {msg.sources.length} source{msg.sources.length !== 1 ? 's' : ''}
                </div>
              )}
              {msg.tokens && (
                <div className="mt-1 text-xs opacity-70">
                  🔢 {msg.tokens} tokens
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 p-3 rounded-lg">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
}
