const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Mock data for Phase 2 development
const MOCK_SEARCH_RESULTS = [
  {
    text: 'To restart a pod, use: kubectl rollout restart deployment/[name]. This triggers a rolling restart of all replicas.',
    score: 0.94,
    source: 'kubernetes-guide.pdf',
    chunk_id: 'chunk-001',
    metadata: {
      section: 'Troubleshooting',
      page: 5,
      doc_id: 'doc-001'
    }
  },
  {
    text: 'Verify the pod is running with: kubectl get pods. Look for pods with status Running.',
    score: 0.87,
    source: 'kubernetes-guide.pdf',
    chunk_id: 'chunk-002',
    metadata: {
      section: 'Troubleshooting',
      page: 6,
      doc_id: 'doc-001'
    }
  },
  {
    text: 'Check pod logs using: kubectl logs [pod-name]. Add -f flag to follow logs in real-time.',
    score: 0.82,
    source: 'kubernetes-guide.pdf',
    chunk_id: 'chunk-003',
    metadata: {
      section: 'Debugging',
      page: 8,
      doc_id: 'doc-001'
    }
  }
]

const MOCK_METRICS = {
  cache_hit_rate: 0.73,
  avg_latency_ms: 340,
  embedding_cache_hits: 45,
  embedding_cache_misses: 44,
  retrieval_cache_hits: 12,
  retrieval_cache_misses: 33,
  response_cache_hits: 5,
  response_cache_misses: 89,
  total_queries: 89,
  avg_tokens_in_context: 2450,
  avg_input_tokens: 2450,
  avg_output_tokens: 340,
  estimated_cost_usd: 0.0012,
  uptime_seconds: 3600
}

export const apiClient = {
  async ingest(file, metadata) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('department', metadata.department)
      formData.append('category', metadata.category)

      const response = await fetch(`${API_URL}/api/ingest`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) throw new Error('Upload failed')
      return await response.json()
    } catch (error) {
      console.warn('Using mock ingest response:', error.message)
      return {
        doc_id: 'mock-' + Date.now(),
        chunks_created: 42,
        strategy: 'semantic',
        tokens_total: 18500,
        metadata: {
          filename: file.name,
          uploaded_at: new Date().toISOString(),
          page_count: 12
        }
      }
    }
  },

  async search(query, filters = {}, topK = 20) {
    try {
      const response = await fetch(`${API_URL}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          top_k: topK,
          filter: filters
        })
      })

      if (!response.ok) throw new Error('Search failed')
      return await response.json()
    } catch (error) {
      console.warn('Using mock search response:', error.message)
      return {
        chunks: MOCK_SEARCH_RESULTS,
        search_type: 'hybrid',
        latency_ms: {
          embedding: 45,
          vector: 120,
          bm25: 80,
          rrf: 15,
          total: 260
        }
      }
    }
  },

  async *generateStreaming(query, chunks) {
    try {
      const response = await fetch(`${API_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          chunks: chunks,
          stream: true
        })
      })

      if (!response.ok) throw new Error('Generation failed')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6))
              yield event
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error) {
      console.warn('Using mock generate response:', error.message)
      const mockResponse = `Based on the documentation, to restart a pod you should use kubectl rollout restart deployment/[name]. This command triggers a rolling restart of all replicas in the deployment, which ensures zero-downtime updates.

The restart process will:
1. Create new pods with the latest image
2. Route traffic to new pods as they become ready
3. Terminate old pods once new ones are healthy

You can monitor the restart with: kubectl rollout status deployment/[name]`

      yield {
        type: 'metadata',
        sources: chunks.slice(0, 3).map(c => ({
          doc: c.source,
          section: c.metadata?.section || 'General'
        }))
      }

      const words = mockResponse.split(' ')
      for (const word of words) {
        yield { type: 'token', content: word + ' ' }
        await new Promise(r => setTimeout(r, 10))
      }

      yield {
        type: 'done',
        input_tokens: 2450,
        output_tokens: 340
      }
    }
  },

  async getMetrics() {
    try {
      const response = await fetch(`${API_URL}/api/metrics`)
      if (!response.ok) throw new Error('Metrics fetch failed')
      return await response.json()
    } catch (error) {
      console.warn('Using mock metrics:', error.message)
      return MOCK_METRICS
    }
  }
}

export default apiClient
