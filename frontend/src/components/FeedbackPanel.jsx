import { useState, useEffect } from 'react'
import { ThumbsUp, ThumbsDown, BarChart3, AlertCircle } from 'lucide-react'
import { API_CONFIG } from '../config/api'

export function FeedbackPanel({ apiKey, lastSearch = null }) {
  const [activeTab, setActiveTab] = useState('submit')
  const [query, setQuery] = useState(lastSearch?.query || '')
  const [answer, setAnswer] = useState(lastSearch?.answer || '')
  const [confidenceScore, setConfidenceScore] = useState(lastSearch?.confidence_score || null)
  const [rating, setRating] = useState(null)
  const [feedbackText, setFeedbackText] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [analytics, setAnalytics] = useState(null)
  const [lowConfidenceQueries, setLowConfidenceQueries] = useState([])

  useEffect(() => {
    if (activeTab === 'analytics') {
      fetchAnalytics()
    }
  }, [activeTab])

  useEffect(() => {
    if (lastSearch) {
      setQuery(lastSearch.query || '')
      setAnswer(lastSearch.answer || '')
      setConfidenceScore(lastSearch.confidence_score || null)
    }
  }, [lastSearch])

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/admin/feedback-analytics?days=30', {
        headers: { 'X-API-Key': apiKey }
      })
      const data = await response.json()
      setAnalytics(data.data)

      const lowConfResponse = await fetch(API_CONFIG.feedback.lowConfidence, {
        headers: { 'X-API-Key': apiKey }
      })
      const lowConfData = await lowConfResponse.json()
      setLowConfidenceQueries(lowConfData.queries || [])
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    }
  }

  const handleRating = async (ratingValue) => {
    setRating(ratingValue)
    setLoading(true)
    setMessage('')

    try {
      const formData = new FormData()
      formData.append('query', query)
      formData.append('answer', answer)
      formData.append('rating', ratingValue)
      formData.append('feedback_text', feedbackText || '')
      formData.append('confidence_score', confidenceScore || 0.5)

      const response = await fetch(API_CONFIG.feedback.submit, {
        method: 'POST',
        headers: { 'X-API-Key': apiKey },
        body: formData
      })

      const data = await response.json()
      if (response.ok) {
        setMessage(`Thank you for your ${ratingValue === 1 ? '👍' : '👎'} feedback!`)
        setTimeout(() => {
          setMessage('')
          setRating(null)
        }, 2000)
      } else {
        setMessage('Error submitting feedback')
      }
    } catch (error) {
      setMessage('Error submitting feedback')
    } finally {
      setLoading(false)
    }
  }

  const getConfidenceBadge = (score) => {
    if (!score && score !== 0) return null
    const percentage = Math.round(score * 100)
    if (score >= 0.7) {
      return (
        <div className="inline-flex items-center gap-2 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 px-3 py-1 rounded-full text-sm font-semibold">
          <span className="w-2 h-2 bg-green-600 rounded-full"></span>
          High ({percentage}%)
        </div>
      )
    } else if (score >= 0.4) {
      return (
        <div className="inline-flex items-center gap-2 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 px-3 py-1 rounded-full text-sm font-semibold">
          <span className="w-2 h-2 bg-yellow-600 rounded-full"></span>
          Medium ({percentage}%)
        </div>
      )
    } else {
      return (
        <div className="inline-flex items-center gap-2 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 px-3 py-1 rounded-full text-sm font-semibold">
          <span className="w-2 h-2 bg-red-600 rounded-full"></span>
          Low ({percentage}%)
        </div>
      )
    }
  }

  return (
    <div className="w-full">
      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('submit')}
          className={`py-3 px-4 font-semibold border-b-2 transition ${
            activeTab === 'submit'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Rate This Answer
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`py-3 px-4 font-semibold border-b-2 transition ${
            activeTab === 'analytics'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          <BarChart3 className="inline-block mr-2" size={18} />
          Analytics
        </button>
      </div>

      {/* Submit Tab */}
      {activeTab === 'submit' && (
        <div className="space-y-6">
          {/* Confidence Score Display */}
          {confidenceScore !== null && (
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Answer Confidence</p>
              {getConfidenceBadge(confidenceScore)}
              {confidenceScore < 0.4 && (
                <div className="mt-3 flex gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
                  <AlertCircle size={18} className="text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-yellow-800 dark:text-yellow-300">
                    This answer has limited source matches. Please verify before using.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Query & Answer Preview */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Your Query
              </label>
              <p className="text-gray-900 dark:text-white bg-gray-100 dark:bg-gray-700 p-3 rounded">
                {query || 'No query'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Answer
              </label>
              <p className="text-gray-900 dark:text-white bg-gray-100 dark:bg-gray-700 p-3 rounded max-h-32 overflow-y-auto">
                {answer || 'No answer'}
              </p>
            </div>
          </div>

          {/* Feedback Text */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Your Feedback (optional)
            </label>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Help us improve. What could be better?"
              rows="3"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            ></textarea>
          </div>

          {/* Rating Buttons */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
              Was this answer helpful?
            </label>
            <div className="flex gap-4">
              <button
                onClick={() => handleRating(1)}
                disabled={loading}
                className={`flex-1 py-4 px-6 rounded-lg font-semibold flex items-center justify-center gap-2 transition ${
                  rating === 1
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-green-100 dark:hover:bg-green-900/30'
                }`}
              >
                <ThumbsUp size={20} />
                Yes, helpful
              </button>
              <button
                onClick={() => handleRating(-1)}
                disabled={loading}
                className={`flex-1 py-4 px-6 rounded-lg font-semibold flex items-center justify-center gap-2 transition ${
                  rating === -1
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-red-100 dark:hover:bg-red-900/30'
                }`}
              >
                <ThumbsDown size={20} />
                Not helpful
              </button>
            </div>
          </div>

          {message && (
            <div className="p-4 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
              {message}
            </div>
          )}
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {analytics && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-4">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Total Feedback</p>
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                    {analytics.stats?.total_feedback || 0}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-lg p-4">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Thumbs Up</p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
                    {analytics.stats?.thumbs_up || 0}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 rounded-lg p-4">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Thumbs Down</p>
                  <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                    {analytics.stats?.thumbs_down || 0}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-4">
                  <p className="text-xs text-gray-600 dark:text-gray-400">Avg Confidence</p>
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                    {analytics.stats?.avg_confidence ? Math.round(analytics.stats.avg_confidence * 100) : 'N/A'}%
                  </p>
                </div>
              </div>

              {/* Low Confidence Queries */}
              {lowConfidenceQueries.length > 0 && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-yellow-900 dark:text-yellow-300 mb-4 flex items-center gap-2">
                    <AlertCircle size={20} />
                    Queries Needing Review
                  </h3>
                  <div className="space-y-3">
                    {lowConfidenceQueries.slice(0, 5).map((q, idx) => (
                      <div key={idx} className="bg-white dark:bg-gray-800 rounded p-3">
                        <p className="font-semibold text-gray-900 dark:text-white">{q.query}</p>
                        <div className="flex gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                          <span>Occurrences: {q.occurrences}</span>
                          <span>Avg Confidence: {Math.round(q.avg_confidence * 100)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-white dark:bg-gray-700 rounded-lg p-6 border border-gray-200 dark:border-gray-600">
                <h3 className="text-lg font-bold mb-4">Feedback Summary</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700 dark:text-gray-300">Positive Rate</span>
                    <span className="font-bold text-green-600 dark:text-green-400">
                      {analytics.stats?.total_feedback ?
                        Math.round((analytics.stats.thumbs_up / analytics.stats.total_feedback) * 100) : 0}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700 dark:text-gray-300">Negative Rate</span>
                    <span className="font-bold text-red-600 dark:text-red-400">
                      {analytics.stats?.total_feedback ?
                        Math.round((analytics.stats.thumbs_down / analytics.stats.total_feedback) * 100) : 0}%
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
