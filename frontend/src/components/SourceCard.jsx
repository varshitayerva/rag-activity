export function SourceCard({ source }) {
  const { text, doc, section, page, score, chunkId } = source

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-medium text-gray-900">{doc}</h4>
          {section && (
            <p className="text-sm text-gray-600">§ {section}</p>
          )}
          {page && (
            <p className="text-sm text-gray-500">Page {page}</p>
          )}
        </div>
        {score && (
          <div className="text-right">
            <div className="text-xs text-gray-600">Relevance</div>
            <div className="text-lg font-semibold text-blue-600">
              {(score * 100).toFixed(0)}%
            </div>
          </div>
        )}
      </div>

      <p className="text-sm text-gray-700 line-clamp-3 mb-3">
        {text}
      </p>

      <button
        onClick={() => {
          console.log('View source:', chunkId)
        }}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        View full source →
      </button>
    </div>
  )
}
