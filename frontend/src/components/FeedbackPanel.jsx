import { useState, useEffect } from 'react'
import { MessageSquare, Send, Star, TrendingUp, AlertCircle } from 'lucide-react'

export function FeedbackPanel({ apiKey }) {
  const [activeTab, setActiveTab] = useState('submit')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [stats, setStats] = useState(null)
  const [trends, setTrends] = useState(null)

  useEffect(() => {
    if (activeTab === 'analytics') {
      fetchAnalytics()
    }
  }, [activeTab])

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('http://localhost:8007/api/feedback/stats')
      const data = await response.json()
      setStats(data.stats)
      setTrends(data.trends)
    } catch (error) {
      console.error('Failed to fetch feedback analytics:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      const response = await fetch('http://localhost:8007/api/feedback/submit', {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query,
          answer,
          rating,
          comment: comment || null
        })
      })

      const data = await response.json()
      if (response.ok) {
        setMessage('✅ Feedback submitted successfully!')
        setQuery('')
        setAnswer('')
        setRating(5)
        setComment('')
        setTimeout(() => setMessage(''), 3000)
      } else {
        setMessage('❌ Failed to submit feedback')
      }
    } catch (error) {
      setMessage('❌ Error submitting feedback')
    } finally {
      setLoading(false)
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
          <MessageSquare className="inline-block mr-2" size={20} />
          Submit Feedback
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`py-3 px-4 font-semibold border-b-2 transition ${
            activeTab === 'analytics'
              ? 'border-blue-600 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          <TrendingUp className="inline-block mr-2" size={20} />
          Analytics
        </button>
      </div>

      {/* Submit Tab */}
      {activeTab === 'submit' && (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Query (optional)
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What did you ask?"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Answer (optional)
            </label>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="What was the answer?"
              rows="4"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            ></textarea>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Rating <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className={`text-3xl transition transform hover:scale-110 ${
                    star <= rating ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'
                  }`}
                >
                  ⭐
                </button>
              ))}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              {['Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][rating - 1]}
            </p>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Comment (optional)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Any additional feedback?"
              rows="3"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            ></textarea>
          </div>

          {message && (
            <div className={`p-4 rounded-lg ${message.includes('✅') ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'}`}>
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition"
          >
            <Send size={20} />
            {loading ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </form>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {stats && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-6">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Total Feedback</p>
                  <p className="text-4xl font-bold text-blue-600 dark:text-blue-400 mt-2">
                    {stats.total_feedback}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/30 dark:to-yellow-800/30 rounded-lg p-6">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Average Rating</p>
                  <p className="text-4xl font-bold text-yellow-600 dark:text-yellow-400 mt-2">
                    {stats.avg_rating}/5
                  </p>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-6">
                  <p className="text-sm text-gray-600 dark:text-gray-400">Quality</p>
                  <p className="text-4xl font-bold text-purple-600 dark:text-purple-400 mt-2">
                    {stats.quality_score}
                  </p>
                </div>
              </div>

              {/* Rating Distribution */}
              <div className="bg-white dark:bg-gray-700 rounded-lg p-6">
                <h3 className="text-lg font-bold mb-6">Rating Distribution</h3>
                <div className="flex items-end gap-4 h-40">
                  {[5, 4, 3, 2, 1].map((rating) => (
                    <div key={rating} className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-gradient-to-t from-blue-500 to-purple-500 rounded-t"
                           style={{height: `${(stats.distribution[rating] / Math.max(...Object.values(stats.distribution))) * 100}px`}}>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{rating}⭐</p>
                      <p className="text-xs text-gray-500">({stats.distribution[rating]})</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {trends && (
            <div className="bg-white dark:bg-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4">Feedback Trends</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span>Total Feedback</span>
                  <span className="font-bold">{trends.total_feedback_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Good Answers (≥4 stars)</span>
                  <span className="font-bold text-green-600 dark:text-green-400">{trends.good_answers}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Poor Answers (≤2 stars)</span>
                  <span className="font-bold text-red-600 dark:text-red-400">{trends.poor_answers}</span>
                </div>
                {trends.needs_improvement && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 flex gap-3 mt-4">
                    <AlertCircle className="text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
                    <span className="text-yellow-900 dark:text-yellow-300">Answer quality needs improvement</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
