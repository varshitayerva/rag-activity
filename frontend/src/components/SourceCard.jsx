import { ExternalLink, Zap } from 'lucide-react'

export function SourceCard({ source }) {
  const { text, doc, section, page_number: page, score, chunk_id: chunkId } = source

  // Get relevance color based on score
  const getRelevanceColor = (score) => {
    if (score > 0.8) return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20'
    if (score > 0.6) return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
    if (score > 0.4) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
    return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
  }

  const getDocumentIcon = (docName) => {
    const lowerDoc = docName?.toLowerCase() || ''
    if (lowerDoc.includes('kubernetes') || lowerDoc.includes('platform')) return '☸️'
    if (lowerDoc.includes('docker') || lowerDoc.includes('devops')) return '🐳'
    if (lowerDoc.includes('python')) return '🐍'
    if (lowerDoc.includes('security') || lowerDoc.includes('faq')) return '🔒'
    if (lowerDoc.includes('network') || lowerDoc.includes('api')) return '🌐'
    return '📄'
  }

  return (
    <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-700/50 dark:to-gray-800 rounded-2xl border-2 border-gray-200 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-2xl transition-all duration-300 overflow-hidden group transform hover:scale-105">
      {/* Top Accent Gradient */}
      <div className="h-1.5 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600"></div>

      <div className="p-5">
        {/* Header */}
        <div className="flex justify-between items-start mb-4 gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">{getDocumentIcon(doc)}</span>
              <h4 className="font-bold text-gray-900 dark:text-white truncate text-lg">
                {doc?.replace('.txt', '').replace(/_/g, ' ') || 'Unknown'}
              </h4>
            </div>
            {section && (
              <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                📌 {section}
              </p>
            )}
          </div>

          {/* Relevance Badge */}
          {score && (
            <div className={`px-4 py-2 rounded-xl text-center font-bold ${getRelevanceColor(score)} flex-shrink-0 shadow-md`}>
              <div className="text-lg font-black">
                {(score * 100).toFixed(0)}%
              </div>
              <div className="text-xs opacity-75 font-semibold">Match</div>
            </div>
          )}
        </div>

        {/* Content */}
        <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3 mb-5 leading-relaxed font-medium">
          {text}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t-2 border-gray-200 dark:border-gray-600">
          <div className="text-xs text-gray-600 dark:text-gray-400 font-semibold">
            {page && <span>📖 Page {page}</span>}
            {!page && <span>🔑 #{chunkId}</span>}
          </div>
          <button
            onClick={() => {
              console.log('View source:', chunkId)
            }}
            className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-bold flex items-center gap-1.5 group-hover:translate-x-2 transition-all"
          >
            View More
            <ExternalLink size={14} className="transition-transform group-hover:rotate-45" />
          </button>
        </div>
      </div>
    </div>
  )
}
