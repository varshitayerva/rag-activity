import { useState, useEffect } from 'react'
import { ThumbsUp, ThumbsDown, AlertCircle, CheckCircle, List, ChevronDown, ChevronUp, BarChart3 } from 'lucide-react'
import { API_CONFIG } from '../config/api'

export function FeedbackPanel({ apiKey, lastSearch = null, userRole = 'user' }) {
  // User view states
  const [query, setQuery] = useState(lastSearch?.query || '')
  const [answer, setAnswer] = useState(lastSearch?.answer || '')
  const [confidenceScore, setConfidenceScore] = useState(lastSearch?.confidence_score || null)
  const [rating, setRating] = useState(null)
  const [feedbackText, setFeedbackText] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  // Admin view states
  const [adminActiveTab, setAdminActiveTab] = useState('feedback-list')
  const [feedbackList, setFeedbackList] = useState([])
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const [expandedFeedback, setExpandedFeedback] = useState(null)
  const [feedbackPage, setFeedbackPage] = useState(0)
  const [totalFeedback, setTotalFeedback] = useState(0)
  const [analytics, setAnalytics] = useState(null)
  const [lowConfidenceQueries, setLowConfidenceQueries] = useState([])

  useEffect(() => {
    if (userRole === 'admin') {
      if (adminActiveTab === 'feedback-list') {
        fetchFeedbackList()
      } else if (adminActiveTab === 'analytics') {
        fetchAnalytics()
      }
    }
  }, [adminActiveTab, feedbackPage, userRole])

  useEffect(() => {
    if (lastSearch) {
      setQuery(lastSearch.query || '')
      setAnswer(lastSearch.answer || '')
      setConfidenceScore(lastSearch.confidence_score || null)
    }
  }, [lastSearch])

  const fetchAnalytics = async () => {
    try {
      console.log('=== FETCHING ANALYTICS ===')
      const url = `${API_CONFIG.baseURL}/api/admin/feedback-analytics?days=30`
      console.log('API URL:', url)

      const response = await fetch(url, {
        headers: { 'X-API-Key': apiKey }
      })

      console.log('Response status:', response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Analytics fetch failed:', response.status, errorText)
        setAnalytics(null)
        return
      }

      const data = await response.json()
      console.log('===== FULL RESPONSE =====')
      console.log('data:', data)
      console.log('data.data:', data.data)
      console.log('data.data.stats:', data.data?.stats)
      console.log('=== END RESPONSE ===')

      // Set analytics with the stats object
      if (data && data.data && data.data.stats) {
        console.log('✓ CASE 1: Setting analytics with stats:', data.data.stats)
        const analyticsObj = {
          stats: data.data.stats,
          low_rated_queries: data.data.low_rated_queries || [],
          period_days: data.data.period_days || 30
        }
        console.log('Analytics object being set:', analyticsObj)
        setAnalytics(analyticsObj)
      } else if (data && data.stats) {
        // Fallback: maybe stats is directly in response
        console.log('✓ CASE 2: Setting analytics from direct stats:', data.stats)
        const analyticsObj = {
          stats: data.stats,
          low_rated_queries: data.low_rated_queries || [],
          period_days: data.period_days || 30
        }
        console.log('Analytics object being set:', analyticsObj)
        setAnalytics(analyticsObj)
      } else {
        console.warn('✗ CASE 3: No analytics data found. Response structure:', data)
        console.warn('Available keys in data:', Object.keys(data))
        console.warn('Available keys in data.data:', data.data ? Object.keys(data.data) : 'N/A')
        setAnalytics(null)
      }

      // Fetch low confidence queries separately
      console.log('Fetching low confidence queries...')
      const lowConfResponse = await fetch(`${API_CONFIG.baseURL}/api/admin/low-confidence-queries?threshold=0.4&limit=20`, {
        headers: { 'X-API-Key': apiKey }
      })
      if (!lowConfResponse.ok) {
        console.error('Low confidence queries fetch failed:', lowConfResponse.status)
        setLowConfidenceQueries([])
        return
      }
      const lowConfData = await lowConfResponse.json()
      console.log('Low confidence response:', lowConfData)
      console.log('Setting low confidence queries:', lowConfData.queries)
      setLowConfidenceQueries(lowConfData.queries || [])
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
      setAnalytics(null)
    }
  }

  const fetchFeedbackList = async () => {
    setFeedbackLoading(true)
    try {
      const limit = 20
      const offset = feedbackPage * limit
      const url = `${API_CONFIG.baseURL}/api/admin/all-feedback?limit=${limit}&offset=${offset}&days=30`
      console.log('Fetching feedback from:', url)

      const response = await fetch(url, {
        headers: { 'X-API-Key': apiKey }
      })

      console.log('Feedback list response status:', response.status)

      if (!response.ok) {
        console.error('Feedback list fetch failed:', response.status)
        const errorText = await response.text()
        console.error('Error response:', errorText)
        return
      }

      const data = await response.json()
      console.log('Feedback list response data:', data)

      if (data.data) {
        console.log('Setting feedback list:', data.data.feedback)
        console.log('Setting total feedback:', data.data.total)
        setFeedbackList(data.data.feedback || [])
        setTotalFeedback(data.data.total || 0)
      }
    } catch (error) {
      console.error('Failed to fetch feedback list:', error)
    } finally {
      setFeedbackLoading(false)
    }
  }

  const getRatingBadge = (rating) => {
    if (rating === 1) {
      return <span className="inline-flex items-center gap-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 px-3 py-1 rounded-full text-sm font-semibold">👍 Helpful</span>
    } else if (rating === -1) {
      return <span className="inline-flex items-center gap-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 px-3 py-1 rounded-full text-sm font-semibold">👎 Not Helpful</span>
    } else {
      return <span className="inline-flex items-center gap-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 px-3 py-1 rounded-full text-sm font-semibold">➖ Neutral</span>
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
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

      console.log('Submitting feedback:', {
        endpoint: API_CONFIG.feedback.submit,
        query: query,
        rating: ratingValue,
        confidence_score: confidenceScore || 0.5
      })

      const response = await fetch(API_CONFIG.feedback.submit, {
        method: 'POST',
        headers: { 'X-API-Key': apiKey },
        body: formData
      })

      console.log('Feedback response:', response.status, response.statusText)
      const data = await response.json()
      console.log('Feedback response data:', data)

      if (response.ok) {
        setMessage(`Thank you for your ${ratingValue === 1 ? '👍' : '👎'} feedback!`)
        setTimeout(() => {
          setMessage('')
          setRating(null)
        }, 2000)
      } else {
        console.error('Failed to submit feedback:', data)
        setMessage('Error submitting feedback')
      }
    } catch (error) {
      console.error('Feedback submission error:', error)
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

  // USER VIEW
  if (userRole === 'user') {
    return (
      <div className="w-full max-w-2xl mx-auto">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-900 dark:to-indigo-900 rounded-lg p-8 text-white mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Rate This Answer</h1>
              <p className="text-blue-100">Help us improve by sharing your feedback</p>
            </div>
            <ThumbsUp size={48} className="opacity-20" />
          </div>
        </div>

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
      </div>
    )
  }

  // ADMIN VIEW
  return (
    <div className="w-full">
      {/* Admin Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
        <button
          onClick={() => setAdminActiveTab('feedback-list')}
          className={`py-3 px-4 font-semibold border-b-2 transition whitespace-nowrap ${
            adminActiveTab === 'feedback-list'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          <List className="inline-block mr-2" size={18} />
          All Feedback ({totalFeedback})
        </button>
        <button
          onClick={() => setAdminActiveTab('analytics')}
          className={`py-3 px-4 font-semibold border-b-2 transition whitespace-nowrap ${
            adminActiveTab === 'analytics'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          <BarChart3 className="inline-block mr-2" size={18} />
          Analytics
        </button>
      </div>

      {/* FEEDBACK LIST TAB */}
      {adminActiveTab === 'feedback-list' && (
        <div className="space-y-6">
          {/* Header Stats */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">User Feedback Submissions</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total feedback: <span className="font-bold text-blue-600 dark:text-blue-400">{totalFeedback}</span></p>
              </div>
              <List size={40} className="text-blue-600 dark:text-blue-400 opacity-20" />
            </div>
          </div>

          {/* Feedback List */}
          {feedbackLoading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
              </div>
              <p className="text-gray-600 dark:text-gray-400 mt-4">Loading feedback...</p>
            </div>
          ) : feedbackList.length > 0 ? (
            <div className="space-y-4">
              {feedbackList.map((fb, idx) => (
                <div key={fb.id} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition">
                  {/* Feedback Header */}
                  <div
                    onClick={() => setExpandedFeedback(expandedFeedback === fb.id ? null : fb.id)}
                    className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition flex items-start justify-between"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-xs font-bold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">#{feedbackPage * 20 + idx + 1}</span>
                        {getRatingBadge(fb.rating)}
                      </div>
                      <p className="font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">
                        {fb.query || 'No query'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(fb.created_at)}
                      </p>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      {expandedFeedback === fb.id ? (
                        <ChevronUp size={20} className="text-gray-400" />
                      ) : (
                        <ChevronDown size={20} className="text-gray-400" />
                      )}
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedFeedback === fb.id && (
                    <div className="px-4 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 space-y-4">
                      {/* Query */}
                      <div>
                        <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">Query</p>
                        <p className="text-sm text-gray-900 dark:text-white bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700">
                          {fb.query || 'N/A'}
                        </p>
                      </div>

                      {/* Answer */}
                      {fb.answer && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">Answer</p>
                          <p className="text-sm text-gray-900 dark:text-white bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 max-h-40 overflow-y-auto">
                            {fb.answer}
                          </p>
                        </div>
                      )}

                      {/* Confidence Score */}
                      {fb.confidence_score !== null && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">Confidence Score</p>
                          <div className="flex items-center gap-3">
                            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full transition-all ${
                                  fb.confidence_score >= 0.7
                                    ? 'bg-green-600'
                                    : fb.confidence_score >= 0.4
                                    ? 'bg-yellow-600'
                                    : 'bg-red-600'
                                }`}
                                style={{ width: `${Math.round(fb.confidence_score * 100)}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-bold text-gray-900 dark:text-white w-12">
                              {Math.round(fb.confidence_score * 100)}%
                            </span>
                          </div>
                        </div>
                      )}

                      {/* User Feedback */}
                      {fb.feedback_text && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">User Comment</p>
                          <p className="text-sm text-gray-900 dark:text-white bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 italic">
                            "{fb.feedback_text}"
                          </p>
                        </div>
                      )}

                      {/* Chunks Used */}
                      {fb.chunks_used && (
                        <div>
                          <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">Chunks Used</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-700 font-mono">
                            {fb.chunks_used}
                          </p>
                        </div>
                      )}

                      {/* Metadata */}
                      <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
                        <div>
                          <p className="text-xs text-gray-600 dark:text-gray-400">Feedback ID</p>
                          <p className="text-sm font-mono text-gray-900 dark:text-white">{fb.id}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 dark:text-gray-400">Last Updated</p>
                          <p className="text-sm text-gray-900 dark:text-white">{formatDate(fb.updated_at || fb.created_at)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <AlertCircle size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400 font-semibold">No feedback yet</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">Users will see their feedback here once submitted</p>
            </div>
          )}

          {/* Pagination */}
          {totalFeedback > 20 && (
            <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Showing <span className="font-bold">{feedbackPage * 20 + 1}</span> to <span className="font-bold">{Math.min((feedbackPage + 1) * 20, totalFeedback)}</span> of <span className="font-bold">{totalFeedback}</span> feedback entries
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setFeedbackPage(Math.max(0, feedbackPage - 1))}
                  disabled={feedbackPage === 0}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg font-semibold hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Previous
                </button>
                <button
                  onClick={() => setFeedbackPage(feedbackPage + 1)}
                  disabled={(feedbackPage + 1) * 20 >= totalFeedback}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ANALYTICS TAB */}
      {adminActiveTab === 'analytics' && (
        <div className="space-y-6">
          {analytics ? (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold">Total Feedback</p>
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-2">
                    {analytics.stats?.total_feedback || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Last 30 days</p>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-lg p-4 border border-green-200 dark:border-green-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold">Positive (👍)</p>
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">
                    {analytics.stats?.thumbs_up || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {analytics.stats?.total_feedback ?
                      Math.round((analytics.stats.thumbs_up / analytics.stats.total_feedback) * 100) : 0}%
                  </p>
                </div>

                <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 rounded-lg p-4 border border-red-200 dark:border-red-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold">Negative (👎)</p>
                  <p className="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">
                    {analytics.stats?.thumbs_down || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {analytics.stats?.total_feedback ?
                      Math.round((analytics.stats.thumbs_down / analytics.stats.total_feedback) * 100) : 0}%
                  </p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-4 border border-purple-200 dark:border-purple-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 font-semibold">Avg Confidence</p>
                  <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-2">
                    {analytics.stats?.avg_confidence ? Math.round(analytics.stats.avg_confidence * 100) : 0}%
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Answer quality</p>
                </div>
              </div>

              {/* Feedback Summary */}
              <div className="bg-white dark:bg-gray-700 rounded-lg p-6 border border-gray-200 dark:border-gray-600">
                <h3 className="text-lg font-bold mb-6 text-gray-900 dark:text-white">Feedback Distribution</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Positive Rate</span>
                      <span className="text-sm font-bold text-green-600 dark:text-green-400">
                        {analytics.stats?.total_feedback ?
                          Math.round((analytics.stats.thumbs_up / analytics.stats.total_feedback) * 100) : 0}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                      <div
                        className="bg-green-600 h-3 rounded-full transition-all"
                        style={{width: `${analytics.stats?.total_feedback ? Math.round((analytics.stats.thumbs_up / analytics.stats.total_feedback) * 100) : 0}%`}}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Negative Rate</span>
                      <span className="text-sm font-bold text-red-600 dark:text-red-400">
                        {analytics.stats?.total_feedback ?
                          Math.round((analytics.stats.thumbs_down / analytics.stats.total_feedback) * 100) : 0}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                      <div
                        className="bg-red-600 h-3 rounded-full transition-all"
                        style={{width: `${analytics.stats?.total_feedback ? Math.round((analytics.stats.thumbs_down / analytics.stats.total_feedback) * 100) : 0}%`}}
                      ></div>
                    </div>
                  </div>

                  {analytics.stats?.neutral !== undefined && (
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Neutral</span>
                        <span className="text-sm font-bold text-yellow-600 dark:text-yellow-400">
                          {analytics.stats?.total_feedback ?
                            Math.round((analytics.stats.neutral / analytics.stats.total_feedback) * 100) : 0}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                        <div
                          className="bg-yellow-600 h-3 rounded-full transition-all"
                          style={{width: `${analytics.stats?.total_feedback ? Math.round((analytics.stats.neutral / analytics.stats.total_feedback) * 100) : 0}%`}}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Low Confidence Queries */}
              {lowConfidenceQueries && lowConfidenceQueries.length > 0 ? (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
                  <h3 className="text-lg font-bold text-yellow-900 dark:text-yellow-300 mb-4 flex items-center gap-2">
                    <AlertCircle size={20} />
                    Low Confidence Queries ({lowConfidenceQueries.length})
                  </h3>
                  <p className="text-sm text-yellow-800 dark:text-yellow-200 mb-4">
                    These queries returned answers with confidence scores below 0.4. Review and update your knowledge base if needed.
                  </p>
                  <div className="space-y-3">
                    {lowConfidenceQueries.slice(0, 10).map((q, idx) => (
                      <div key={idx} className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-yellow-100 dark:border-yellow-700/30">
                        <p className="font-semibold text-gray-900 dark:text-white text-sm mb-2">
                          {idx + 1}. {q.query}
                        </p>
                        <div className="flex gap-6 text-xs text-gray-600 dark:text-gray-400">
                          <span className="flex items-center gap-1">
                            <span className="font-medium">Occurrences:</span> {q.occurrences}
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="font-medium">Avg Confidence:</span>
                            <span className="font-bold">{Math.round((q.avg_confidence || 0) * 100)}%</span>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
                  <div className="flex items-center gap-3">
                    <CheckCircle size={24} className="text-green-600 dark:text-green-400" />
                    <div>
                      <p className="font-semibold text-green-900 dark:text-green-300">All queries have good confidence!</p>
                      <p className="text-sm text-green-800 dark:text-green-200">No queries below the 0.4 confidence threshold.</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <AlertCircle size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No analytics data available yet</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">Submit some feedback to see analytics</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
