import { ExternalLink, Zap } from 'lucide-react'

export function SourceCard({ source }) {
  const { text, doc, section, page, score, chunkId } = source

  // Get relevance color based on score
  const getRelevanceColor = (score) => {
    if (score > 0.8) return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20'
    if (score > 0.6) return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
    if (score > 0.4) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
    return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
  }

  const getDocumentIcon = (docName) => {
    if (docName?.includes('kubernetes')) return '☸️'
    if (docName?.includes('docker')) return '🐳'
    if (docName?.includes('python')) return '🐍'
    return '📄'
  }

  return (
    <div className="bg-white dark:bg-gray-700 rounded-xl border border-gray-200 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden group">
      {/* Top Accent */}
      <div className="h-1 bg-gradient-to-r from-blue-500 to-blue-600"></div>

      <div className="p-4">
        {/* Header */}
        <div className="flex justify-between items-start mb-3 gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{getDocumentIcon(doc)}</span>
              <h4 className="font-semibold text-gray-900 dark:text-white truncate">
                {doc?.replace('.txt', '') || 'Unknown'}
              </h4>
            </div>
            {section && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                § {section}
              </p>
            )}
          </div>

          {/* Relevance Badge */}
          {score && (
            <div className={`px-3 py-1 rounded-lg text-center ${getRelevanceColor(score)} flex-shrink-0`}>
              <div className="text-xs font-semibold">
                {(score * 100).toFixed(0)}%
              </div>
              <div className="text-xs opacity-75">Match</div>
            </div>
          )}
        </div>

        {/* Content */}
        <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3 mb-4 leading-relaxed">
          {text}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-600">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {page && <span>📄 Page {page}</span>}
            {!page && <span>ID: {chunkId}</span>}
          </div>
          <button
            onClick={() => {
              console.log('View source:', chunkId)
            }}
            className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold flex items-center gap-1 group-hover:translate-x-1 transition"
          >
            View
            <ExternalLink size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}
