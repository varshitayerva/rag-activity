export function ArchitectureDiagram() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold mb-4">System Architecture</h2>

      <div className="bg-gray-50 p-4 rounded border border-gray-300 overflow-x-auto text-xs font-mono">
        <pre>{`
┌─────────────────────────────────────────────────────────────────────────┐
│                    TECHNICAL SUPPORT COPILOT                            │
├─────────────────────────────────────────────────────────────────────────┤
│ Frontend (React + Vite)                                                 │
│  ├─ Chat Panel (streaming SSE from /api/generate)                       │
│  ├─ Upload Panel (POST to /api/ingest)                                  │
│  ├─ Source Cards (display /api/search results)                          │
│  ├─ Metrics Bar (live /api/metrics)                                     │
│  └─ Filter Bar (department, category, date range)                       │
├─────────────────────────────────────────────────────────────────────────┤
│ API Layer (FastAPI)                                                    │
│  ├─ POST /api/ingest (M1)     → parser → chunker → DB                  │
│  ├─ POST /api/search (M2)     → embed → vector+bm25 → rrf + filter    │
│  ├─ POST /api/generate (M3)   → stream → Claude → sources              │
│  ├─ GET /api/metrics (M4)     → cache stats + latency KPIs             │
│  └─ Cache Middleware (M4)     → L1, L2, L3 intercept                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Data & Processing Layer                                                │
│  ├─ Qdrant (vector DB, HNSW indexing, metadata payload)                 │
│  ├─ BM25 Index (sparse search, exact-match ranking)                     │
│  ├─ PostgreSQL (metadata, chunks, audit log)                            │
│  ├─ Redis (3-layer cache: embed/retrieval/response)                     │
│  └─ OpenAI Embeddings (text-embedding-3-small, 1,536-dim)               │
├─────────────────────────────────────────────────────────────────────────┤
│ Infrastructure                                                         │
│  └─ Docker Compose (all services)                                      │
└─────────────────────────────────────────────────────────────────────────┘

DATA FLOW:
User Query → Embed (cached) → Search (vector+BM25 → RRF)
         → Context Assembly → Generate (Claude stream) → Sources + Response
`}</pre>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <p className="font-medium mb-2">Key Features:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Semantic chunking for accurate document parsing</li>
          <li>Hybrid search combining vector + BM25 ranking</li>
          <li>3-layer Redis caching (embedding, retrieval, response)</li>
          <li>Streaming SSE for real-time response generation</li>
          <li>Source attribution on all responses</li>
        </ul>
      </div>
    </div>
  )
}
