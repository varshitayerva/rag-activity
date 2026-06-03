# Track 4: Performance & Scalability in RAG Systems
## Production-Grade Implementation Plan

---

## 1. CONTEXT & OBJECTIVE

### Problem Statement
Production RAG systems suffer from four critical performance bottlenecks:
- **Vector DB Scaling**: 100M+ vectors cause serious latency (O(n) without indexing)
- **Token Explosion**: Retrieving top-k=20 chunks creates 10K-token prompts, multiplying LLM cost and latency
- **LLM Inference Delay**: Average 12-second end-to-end latency violates SLA targets (<2 seconds)
- **Network Overhead**: 3–5 round-trip API calls per query add cascading delays

### Deliverable
Build **Technical Support Copilot** — a production-ready RAG system demonstrating:
- Retrieval accuracy via hybrid search (vector + BM25)
- Hallucination control via grounding and source attribution
- Performance optimization via ANN indexing, three-layer caching, and context compression
- Scalability from 100K to 100M documents without latency degradation

### Success Metrics
- **Before optimization**: ~2,250ms latency, 10K tokens per request
- **After optimization**: <500ms latency (cold), <5ms (cached), <2,500 tokens per request
- **Rubric alignment**: Depth (30%) + Practical Understanding (25%) + Production Awareness (20%)

---

## 2. ARCHITECTURE OVERVIEW

### RAG Pipeline (5 Stages)
```
User Query
    ↓
[1] Embedding (100ms) — OpenAI text-embedding-3-small cached
    ↓
[2] Hybrid Search (100-350ms) — Qdrant HNSW + BM25 RRF fusion
    ↓
[3] Context Assembly (50ms) — Compression & reranking (top-20 → top-5)
    ↓
[4] LLM Generation (1,500-1,800ms) — Claude streaming SSE
    ↓
[5] Attribution (0ms) — Source citation + confidence scoring

Total before: ~2,250ms | After: ~500ms (cold), ~5ms (cached)
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Vector DB** | Qdrant (HNSW, native hybrid) | Production-grade, <2ms query latency |
| **Sparse Search** | rank-bm25 (Python) | Exact-match precision for error codes |
| **Embeddings** | OpenAI text-embedding-3-small (1,536 dims) | Industry standard |
| **Caching** | Redis 7 (3-layer) | Embedding, retrieval, response cache |
| **LLM** | Claude Sonnet 4.0 via Anthropic SDK | Streaming, source attribution |
| **API** | FastAPI (Python) | SSE streaming, async, per-feature endpoints |
| **Frontend** | React 18 + Vite + TailwindCSS | Real-time chat, metrics display |
| **Metadata** | PostgreSQL 15 | Document metadata, access control |
| **Infrastructure** | Docker Compose | All services in one compose file |

---

## 3. TEAM ASSIGNMENTS

### Member 1: Document Ingestion & Chunking (M1)
**Git Branch**: `feature/ingestion-pipeline`  
**Endpoint**: `POST /api/ingest`  
**Deliverable**: PDF/Markdown parser with fixed & semantic chunking comparison

#### Scope
- PDF text extraction (pypdf, pdfplumber)
- Markdown parsing (simple frontmatter + sections)
- **Fixed-size chunking**: 500-token sliding window (overlap=100)
- **Semantic chunking**: Sentence-aware, paragraph boundaries, section detection
- Metadata extraction: `{doc_id, filename, section, page, uploaded_at, department, category}`
- Chunk storage to PostgreSQL + Qdrant vector DB

#### Key Implementation Details
```python
# chunker.py structure
class FixedChunker:
    def chunk(text, chunk_size=500, overlap=100) → List[Chunk]

class SemanticChunker:
    def chunk(text) → List[Chunk]  # Uses sentence boundaries + section headers
    
class MetadataExtractor:
    def extract(doc, metadata_override) → Dict
```

#### Demo 1 Requirement (Member 1 owns)
Query: "How do I fix the database connection timeout in step 3?"
- **Bad (fixed chunking)**: Returns steps 2-4 fragmented, LLM answer is wrong
- **Good (semantic)**: Returns step 3 complete, LLM answer is exact and helpful
- **Metrics**: token_count drops from 850 → 450, accuracy improves from 40% → 95%

#### Acceptance Criteria
- [ ] Parse 3+ PDF formats (structured, scanned, with tables)
- [ ] Semantic chunker outperforms fixed by >20% on retrieval accuracy benchmark
- [ ] Metadata extraction captures: filename, section, page, department, category
- [ ] All chunks stored with embeddings in Qdrant + metadata in PostgreSQL
- [ ] Unit tests: 10+ edge cases (empty doc, single page, no sections, non-ASCII)

---

### Member 2: Hybrid Search & Retrieval (M2)
**Git Branch**: `feature/hybrid-search`  
**Endpoint**: `POST /api/search`  
**Deliverable**: Qdrant HNSW + BM25 RRF fusion with metadata filtering

#### Scope
- Qdrant client setup: HNSW index, cosine similarity, 1,536-dim embeddings
- BM25 sparse search: rank-bm25 library, tokenization, scoring
- **RRF (Reciprocal Rank Fusion)**: Combine vector & BM25 scores
  - Formula: `score = 1/(k + rank_vector) + 1/(k + rank_bm25)` where k=60
- Metadata filtering: Department, category, date range
- Latency instrumentation: Track search breakdown (embedding, vector, BM25, fusion)

#### Key Implementation Details
```python
# hybrid.py structure
class HybridSearch:
    async def search(query, top_k=20, metadata_filter=None):
        # 1. Embed query (cached in Redis)
        embedding = await embed_cached(query)
        
        # 2. Vector search in Qdrant
        vector_results = await qdrant.search(embedding, top_k=50)
        
        # 3. BM25 search
        bm25_results = bm25.search(query, top_k=50)
        
        # 4. RRF fusion
        fused = rrf_fusion(vector_results, bm25_results, k=60)
        
        # 5. Apply metadata filter
        filtered = apply_metadata_filter(fused, metadata_filter)
        
        # 6. Return top_k with latency breakdown
        return {
            "chunks": filtered[:top_k],
            "search_type": "hybrid",
            "latency_ms": {
                "embedding": 45,
                "vector": 120,
                "bm25": 80,
                "rrf": 15,
                "total": 260
            }
        }
```

#### Demo 2 Requirement (Member 2 owns)
Query: "How do I fix ImagePullBackOff?"
- **Vector-only (fails)**: Finds general "container errors" docs, misses exact "ImagePullBackOff"
- **Hybrid (succeeds)**: BM25 exact-matches "ImagePullBackOff", RRF ranks it top
- **Metrics**: Retrieval rank improves from 47th → 1st, token precision +35%

#### Acceptance Criteria
- [ ] Qdrant collection created with HNSW, cosine similarity, payload storage
- [ ] BM25 index built from all ingested documents
- [ ] RRF fusion implemented and tested with multiple k values (k=30, 60, 100)
- [ ] Metadata filtering works for department, category, date ranges
- [ ] Latency instrumentation captures per-stage breakdown
- [ ] Unit tests: 15+ queries testing vector vs BM25 strengths
- [ ] Integration tests: Hybrid outperforms vector-only on 10 error code queries

---

### Member 3: LLM Generation & Guardrails (M3)
**Git Branch**: `feature/generation-guardrails`  
**Endpoint**: `POST /api/generate` (streaming SSE)  
**Deliverable**: Claude integration with source attribution and hallucination fallback

#### Scope
- Claude Sonnet 4.0 integration via Anthropic SDK
- Prompt engineering: System message + context grounding + source instructions
- **Streaming SSE**: Token-by-token output via Server-Sent Events
- Source attribution: Emit source metadata alongside generation
- Hallucination fallback: Detect "I don't have reliable information" and gracefully respond
- Token counting: Track input/output tokens per request

#### Key Implementation Details
```python
# generation.py structure
SYSTEM_PROMPT = """You are a technical support assistant. 
You MUST answer based only on the provided documentation chunks. 
If the documentation does not contain enough information to answer reliably, 
respond with exactly: "I don't have reliable information to answer this question. 
Please consult [source] or contact support."

For every answer, cite the exact source document and section."""

class GenerationService:
    async def generate_streaming(query, chunks):
        # 1. Build grounded prompt
        context = format_context(chunks)
        prompt = build_prompt(query, context)
        
        # 2. Stream from Claude
        async with client.messages.stream(...) as stream:
            sources = extract_sources(chunks)
            
            yield {"type": "metadata", "sources": sources}
            
            async for text in stream:
                yield {"type": "token", "content": text}
            
            yield {"type": "done"}
        
        # 3. Track tokens
        log_token_usage(input_tokens, output_tokens)
```

#### Demo 3 Support (Source Attribution)
- Every response includes: `[source: k8s-guide.pdf § Troubleshooting, line 234]`
- User can click source to view exact chunk in sidebar
- Confidence scoring (optional): Mark if answer is "high confidence" (multiple sources) or "low confidence" (single source)

#### Acceptance Criteria
- [ ] Claude Sonnet 4.0 integrated with streaming SSE
- [ ] Grounding prompt enforces context-only answers
- [ ] Hallucination fallback message tested and deployed
- [ ] Source attribution metadata embedded in every response
- [ ] Token counting working: input_tokens + output_tokens logged
- [ ] Streaming latency <100ms time-to-first-token
- [ ] Unit tests: 10+ hallucination scenarios (query outside docs, contradictions, unknowns)

---

### Member 4: Redis Caching & Performance (M4)
**Git Branch**: `feature/caching-performance`  
**Endpoint**: `GET /api/metrics` + cache integration across /api/search, /api/generate  
**Deliverable**: Three-layer Redis cache + context compression + performance instrumentation

#### Scope
- **Layer 1 (Embedding Cache)**: Cache query embeddings (key: query hash, TTL: 24h)
  - Hit rate target: 50-70% (repeated/similar queries)
- **Layer 2 (Retrieval Cache)**: Cache search results per query+filter combo (TTL: 4h)
  - Hit rate target: 30-50%
- **Layer 3 (Response Cache)**: Cache full LLM responses (TTL: 2h)
  - Hit rate target: 10-20%
- **Context Compression**: Reduce top-20 chunks to top-5 via reranking/extractive summarization
  - Token reduction: 10,000 → 2,500 (75% less)
- **Metrics Endpoint**: Expose cache hit rates, latency breakdown, token usage

#### Key Implementation Details
```python
# cache.py structure
class RedisCache:
    async def get_embedding_cached(query):
        key = f"embedding:{hash(query)}"
        cached = await redis.get(key)
        if cached: return json.loads(cached)
        
        embedding = await openai.embed(query)
        await redis.setex(key, 86400, json.dumps(embedding))  # 24h TTL
        return embedding
    
    async def get_retrieval_cached(query, filter_key):
        key = f"retrieval:{hash(query)}:{filter_key}"
        cached = await redis.get(key)
        if cached: return json.loads(cached)
        
        results = await hybrid_search(query, filter_key)
        await redis.setex(key, 14400, json.dumps(results))  # 4h TTL
        return results

class ContextCompression:
    def compress(chunks, max_tokens=2500):
        # Rerank top-20 with cross-encoder (bonus)
        # Or: extract top-5 by similarity + relevance
        return chunks[:5]  # Simple truncation for MVP

class MetricsCollector:
    def report():
        return {
            "cache_hit_rate": 0.73,
            "avg_latency_ms": 340,  # was 2250
            "embedding_cache_hits": 45,
            "retrieval_cache_hits": 12,
            "response_cache_hits": 5,
            "total_queries": 89,
            "avg_tokens_in_context": 2450,  # was 10000
            "cost_per_query": 0.0012  # estimate
        }
```

#### Demo 3 Requirement (Member 4 owns)
Query: "How do I restart a pod?" (cold cache)
- **Cold**: Embed (100ms) + Search (350ms) + Generate (1,800ms) = 2,250ms total
- **Warm** (repeat same query): Embed (0ms, cache hit) + Search (0ms, cache hit) + Generate (0ms, response cache) = 5ms
- **Metrics panel shows live**:
  ```
  cache_hit_rate: 0.73 | avg_latency_ms: 340 (was 2250) 
  | embedding_cache_hits: 45 | total_queries: 89
  ```

#### Acceptance Criteria
- [ ] Redis 7 running via Docker Compose
- [ ] 3-layer cache implemented with correct TTLs (24h, 4h, 2h)
- [ ] Cache hit rate instrumentation working for all 3 layers
- [ ] Context compression reduces top-20 → top-5 (verified via token counting)
- [ ] /api/metrics endpoint returns all KPIs above
- [ ] Latency breakdown: cold (~500ms) vs warm (<5ms) confirmed
- [ ] Unit tests: Cache eviction, TTL expiry, collision handling

---

### Member 5: React Frontend & Integration (M5)
**Git Branch**: `feature/frontend-ui`  
**Deliverable**: Chat UI with upload, filtering, metrics display, and architecture diagram

#### Scope
- Chat panel: User input, response display with streaming
- Document upload panel: Drag-and-drop PDF/Markdown, metadata tagging (department, category)
- Filter bar: Department, category, date range dropdowns
- Source cards: Display retrieved chunks with metadata (doc name, section, score)
- Metrics bar: Live KPIs (latency, cache hit rate, tokens)
- Architecture diagram: System diagram (React component or SVG)

#### Key Implementation Details
```javascript
// ChatPanel.jsx
export function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [query, setQuery] = useState("")
  
  async function handleSubmit() {
    // Stream response from /api/generate
    const response = await fetch("/api/generate", {
      method: "POST",
      body: JSON.stringify({ query, chunks: retrievedChunks })
    })
    
    const reader = response.body.getReader()
    let fullText = ""
    let sources = []
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const event = JSON.parse(new TextDecoder().decode(value))
      
      if (event.type === "token") {
        fullText += event.content
        setMessages(prev => [...prev.slice(0,-1), { role: "assistant", content: fullText }])
      } else if (event.type === "sources") {
        sources = event.sources
      }
    }
    
    setMessages(prev => [...prev, { role: "assistant", sources }])
  }
  
  return (
    <div className="flex flex-col">
      {messages.map(msg => (
        <ChatMessage message={msg} />
      ))}
      <ChatInput onSubmit={handleSubmit} />
    </div>
  )
}

// UploadPanel.jsx
export function UploadPanel() {
  async function handleUpload(files, metadata) {
    const formData = new FormData()
    formData.append("file", files[0])
    formData.append("department", metadata.department)
    formData.append("category", metadata.category)
    
    const response = await fetch("/api/ingest", {
      method: "POST",
      body: formData
    })
    
    const result = await response.json()
    alert(`${result.chunks_created} chunks created with ${result.strategy} chunking`)
  }
  
  return (
    <div className="border-2 border-dashed rounded p-4">
      <input type="file" onChange={handleUpload} />
    </div>
  )
}

// MetricsBar.jsx
export function MetricsBar() {
  const [metrics, setMetrics] = useState(null)
  
  useEffect(() => {
    const interval = setInterval(async () => {
      const resp = await fetch("/api/metrics")
      setMetrics(await resp.json())
    }, 1000)
    return () => clearInterval(interval)
  }, [])
  
  if (!metrics) return null
  return (
    <div className="flex gap-4 p-2 bg-gray-100">
      <Metric label="Latency" value={`${metrics.avg_latency_ms}ms`} />
      <Metric label="Cache Hit" value={`${(metrics.cache_hit_rate * 100).toFixed(1)}%`} />
      <Metric label="Avg Tokens" value={metrics.avg_tokens_in_context} />
      <Metric label="Queries" value={metrics.total_queries} />
    </div>
  )
}
```

#### Acceptance Criteria
- [ ] Chat panel streams responses with Server-Sent Events
- [ ] Upload panel supports PDF and Markdown with metadata tagging
- [ ] Filter dropdowns wired to /api/search
- [ ] Source cards display doc name, section, relevance score, clickable to view full chunk
- [ ] Metrics bar updates live every 1 second via /api/metrics
- [ ] Architecture diagram rendered (ASCII or SVG)
- [ ] Responsive design (desktop first, mobile optional)
- [ ] Integration tests: Full chat flow from upload → query → response with sources

---

## 4. API CONTRACTS (Single Source of Truth)

### POST /api/ingest
**Owned by M1**  
Ingest and chunk documents.

```json
Request:
{
  "file": "application/pdf | text/markdown",
  "department": "string",
  "category": "string"
}

Response: (200 OK)
{
  "doc_id": "uuid",
  "chunks_created": 42,
  "strategy": "semantic",
  "tokens_total": 18500,
  "metadata": {
    "filename": "k8s-guide.pdf",
    "uploaded_at": "2024-06-03T10:30:00Z",
    "page_count": 12
  }
}
```

---

### POST /api/search
**Owned by M2**  
Hybrid search (vector + BM25).

```json
Request:
{
  "query": "string",
  "top_k": "integer (default 20)",
  "filter": {
    "department": "string (optional)",
    "category": "string (optional)",
    "date_from": "ISO8601 (optional)",
    "date_to": "ISO8601 (optional)"
  }
}

Response: (200 OK)
{
  "chunks": [
    {
      "text": "Step 3: Verify the pod is running...",
      "score": 0.89,
      "source": "k8s-guide.pdf",
      "chunk_id": "uuid",
      "metadata": {
        "section": "Troubleshooting",
        "page": 5,
        "doc_id": "uuid"
      }
    }
  ],
  "search_type": "hybrid",
  "latency_ms": {
    "embedding": 45,
    "vector": 120,
    "bm25": 80,
    "rrf": 15,
    "total": 260
  }
}
```

---

### POST /api/generate
**Owned by M3**  
Generate response with streaming SSE.

```
Request:
{
  "query": "string",
  "chunks": [{text, source, metadata}],
  "stream": true
}

Response: (200 OK, Content-Type: text/event-stream)

data: {"type":"metadata","sources":[{"doc":"k8s-guide.pdf","section":"Troubleshooting"}]}

data: {"type":"token","content":"Based"}

data: {"type":"token","content":" on"}

data: {"type":"token","content":" the"}

...

data: {"type":"done","input_tokens":2450,"output_tokens":340}
```

---

### GET /api/metrics
**Owned by M4**  
Performance metrics and cache statistics.

```json
Response: (200 OK)
{
  "cache_hit_rate": 0.73,
  "avg_latency_ms": 340,
  "embedding_cache_hits": 45,
  "embedding_cache_misses": 44,
  "retrieval_cache_hits": 12,
  "retrieval_cache_misses": 33,
  "response_cache_hits": 5,
  "response_cache_misses": 89,
  "total_queries": 89,
  "avg_tokens_in_context": 2450,
  "avg_input_tokens": 2450,
  "avg_output_tokens": 340,
  "estimated_cost_usd": 12.45,
  "uptime_seconds": 3600
}
```

---

## 5. GITHUB STRATEGY: COMPLETE BRANCHING & WORKFLOW PLAN

### 5.1 Repository Setup

**Repository Name**: `enterprise-rag-capstone` or `technical-support-copilot`

**Visibility**: Private (capstone team only)

**Branch Protection Rules** (on `main` and `develop`):
```
- Require pull request reviews before merging (1 approver minimum)
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Dismiss stale pull request approvals when new commits are pushed
- Require code owners review (optional, if using CODEOWNERS file)
```

**Collaborators**:
- M1: Ingestion owner
- M2: Search owner
- M3: Generation owner
- M4: Caching owner
- M5: Frontend owner
- All: Reviewers (review each other's PRs)

---

### 5.2 Branch Hierarchy & Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MAIN (production)                               │
│              [PROTECTED] Only merges at v0.5.0, v1.0.0                 │
│              Tags: v0.5.0 (2h), v1.0.0 (4h)                            │
└────────────────────────────────────────────────────────────────────────┘
                                    ↑
                    Merge at 2h & 4h checkpoints
                                    │
┌────────────────────────────────────────────────────────────────────────┐
│                       DEVELOP (integration)                             │
│            [PROTECTED] All features merge here first                   │
│            Master copy: contains all working code                      │
└────────────────────────────────────────────────────────────────────────┘
                                    ↑
                        All PRs merge here
        ┌───────────────┬───────────────┬──────────────┬──────────┐
        │               │               │              │          │
┌───────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────┐ ┌───────┐
│ feature/      │ │ feature/     │ │ feature/     │ │feat/  │ │feat/  │
│ ingestion-    │ │ hybrid-      │ │ generation-  │ │cache- │ │front- │
│ pipeline (M1) │ │ search (M2)  │ │ guardrails   │ │perf   │ │end-ui │
│               │ │              │ │ (M3)         │ │(M4)   │ │(M5)   │
│ ✓ Short-lived │ │ ✓ Short-lived│ │ ✓ Short-lived│ │✓Short │ │✓Short │
│ ✓ Rebased on  │ │ ✓ Rebased on │ │ ✓ Rebased on │ │ lived │ │ lived │
│   develop     │ │   develop    │ │   develop    │ │✓Rebase│ │✓Rebase│
│ ✓ No merges   │ │ ✓ No merges  │ │ ✓ No merges  │ │on dev │ │on dev │
│   from main   │ │   from main  │ │   from main  │ │✓No m  │ │✓No m  │
└───────────────┘ │   from main  │ │   from main  │ │from m │ │from m │
                  │              │ │              │ │       │ │       │
                  └──────────────┘ └──────────────┘ └───────┘ └───────┘
```

---

### 5.3 Branch Naming Convention

**Format**: `[type]/[scope]-[description]`

| Type | Use Case | Examples |
|------|----------|----------|
| `feature/` | New feature development | `feature/ingestion-pipeline` |
| `bugfix/` | Bug fixes on feature branches | `bugfix/cache-ttl-not-expiring` |
| `docs/` | Documentation updates | `docs/architecture-diagram` |
| `test/` | Test additions/fixes | `test/retrieval-accuracy-benchmark` |
| `perf/` | Performance optimizations | `perf/qdrant-index-tuning` |

**Team Assignment Branch Names:**
```
feature/ingestion-pipeline      (M1)
feature/hybrid-search           (M2)
feature/generation-guardrails   (M3)
feature/caching-performance     (M4)
feature/frontend-ui             (M5)
```

---

### 5.4 Commit Message Format (Conventional Commits)

```
<type>(<scope>): <subject> (#<issue-id>)

<body>

<footer>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`  
**Scope**: `ingestion`, `search`, `generation`, `cache`, `frontend`, `infra`, `api`  
**Subject**: Imperative, present tense, <50 chars  
**Body**: Why and what (not how), wrapped at 72 chars  
**Footer**: References issues (`Closes #123`), breaking changes  

**Examples**:
```
feat(ingestion): add semantic chunking algorithm (#1)

Implement semantic chunking that detects paragraph and section
boundaries instead of fixed-size token chunks. Improves retrieval
accuracy by 25% on benchmark set.

Closes #1

Co-Authored-By: Claude <noreply@anthropic.com>
```

```
feat(search): implement RRF fusion for hybrid ranking (#2)

Combine vector search (dense) and BM25 (sparse) results using
Reciprocal Rank Fusion (k=60). Enables error code detection while
maintaining semantic understanding.

- Vector results: k=50, deduplicate
- BM25 results: k=50, tokenize
- RRF score: 1/(k + rank_v) + 1/(k + rank_bm25)
- Filter metadata: department, category, date range

Closes #2

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 5.5 Pull Request Workflow (Detailed Steps)

**STEP 1: Create Feature Branch**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/ingestion-pipeline
```

**STEP 2: Make Commits** (small, logical chunks)
```bash
git add backend/app/ingestion/chunker.py
git commit -m "feat(ingestion): add SemanticChunker class"

git add backend/app/ingestion/parser.py
git commit -m "feat(ingestion): add PDF parser with pypdf"

git add tests/test_chunker.py
git commit -m "test(ingestion): add 10 chunking edge case tests"
```

**STEP 3: Push and Create PR**
```bash
git push -u origin feature/ingestion-pipeline
```

Go to GitHub → "Create Pull Request" → fill in:

**PR Title** (follows format):
```
[M1] Implement document ingestion with semantic chunking
```

**PR Description**:
```markdown
## Summary
Implement PDF/Markdown parsing and chunking (fixed vs semantic) for document ingestion.

## Changes
- Added `FixedChunker` class (500-token sliding window, overlap=100)
- Added `SemanticChunker` class (section-aware, paragraph boundaries)
- Added `PDFParser` using pypdf for text extraction
- Added `MarkdownParser` for frontmatter + section detection
- Added unit tests (10+ edge cases)
- All chunks stored in Qdrant with metadata in PostgreSQL

## Metrics
- Semantic vs fixed accuracy: 95% vs 40% on test set
- Chunk count: 42 chunks from 12-page PDF
- Token reduction: 18,500 tokens total

## Demo
Demonstrates bad fixed chunking (splits troubleshooting step mid-sentence)
vs good semantic chunking (preserves complete steps).

## Closes
#1
```

**STEP 4: Request Reviewers**
- Add 1-2 reviewers (ideally from other members)
- Suggested: M2 + M4 (search and cache depend on ingestion)

**STEP 5: Respond to Review Comments**
- Make changes on same branch (don't create new branch)
- Push new commits
- PR automatically updates

```bash
git add backend/app/ingestion/parser.py
git commit -m "fix(ingestion): handle non-ASCII characters in PDF extraction"
git push origin feature/ingestion-pipeline
```

**STEP 6: Merge When Approved**
- Reviewer clicks "Approve"
- Merge button becomes available
- **Merge strategy**: Squash commits (if <5 commits) OR Rebase + Merge

```bash
# Option A: Squash (if PR has multiple small commits)
# Squash 5 commits → 1 commit on develop

# Option B: Rebase + Merge (clean linear history)
```

**STEP 7: Delete Branch**
- GitHub auto-deletes remote branch after merge (enable in settings)
- Delete local branch:
```bash
git checkout develop
git pull origin develop
git branch -d feature/ingestion-pipeline
```

---

### 5.6 Pull Request Template (Create `.github/pull_request_template.md`)

```markdown
## 🎯 Summary
Brief description of what this PR does and why (1-3 sentences).

## 📝 Changes
- [ ] Feature 1
- [ ] Feature 2
- [ ] Unit tests added
- [ ] Integration tests added

## 🧪 Testing
Describe how you tested this change. Include:
- Unit test coverage (lines of code tested)
- Edge cases tested
- Load tested? (if relevant)

Example:
```bash
pytest tests/test_chunker.py -v
# 12 passed in 0.34s

# Tested with real PDF: k8s-guide.pdf (12 pages, 18.5K tokens)
# Semantic chunking: 42 chunks, 450 avg tokens per chunk
# Fixed chunking: 37 chunks, 500 avg tokens per chunk
```

## 📊 Metrics
Before/after numbers (if applicable):
- **Accuracy**: 40% → 95%
- **Recall@5**: 0.71 → 0.87
- **Latency**: 2,250ms → 340ms
- **Cache hit**: 0% → 73%

## 📚 Demo
Link to or describe the demo scenario this PR enables.
Example: "Demo 1: Fixed vs semantic chunking comparison"

## ✅ Checklist
- [ ] Code follows style guide
- [ ] No merge conflicts with develop
- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] Commits follow conventional commit format
- [ ] PR title matches format: `[M#] Description`
- [ ] Documentation updated (if applicable)

## 👥 Reviewers
Request reviewers from other team members (max 2).

## 🔗 Closes
#1 (if applicable, or remove this section)
```

---

### 5.7 Merge Conflict Resolution Strategy

**Prevention** (best):
- Keep feature branches short-lived (<2 hours)
- Rebase on develop frequently: `git rebase origin/develop`
- Separate file ownership (Section 5 file structure)

**If Conflict Occurs**:
1. **Notify all members** in Slack immediately
2. **Pause other merges** until conflict resolved
3. **Conflict owner** (feature branch owner) resolves
4. **Steps to resolve**:
   ```bash
   git fetch origin
   git rebase origin/develop
   # or
   git merge origin/develop
   # Edit files to resolve conflicts
   git add <resolved-files>
   git rebase --continue  # or git commit -m "Merge conflict resolved"
   git push origin feature/branch-name -f  # -f only for rebase
   ```
5. **Re-run tests** to ensure merge is good
6. **Request review again** from original reviewer

**Common Conflicts**:
- `models/schemas.py`: Add new schema classes carefully, don't delete others
- `docker-compose.yml`: Each member adds their own service, coordinate at sync points
- `requirements.txt`: Add dependencies only in feature branch, deduplicate before merge

**Prevention Rule**: **No one edits another member's files** (see Section 5 file structure)

---

### 5.8 Synchronization Points & Milestone Merges

**Sync 1 (0:30)**
- [ ] All members: `git clone` repo, checkout feature branch
- [ ] Verify: `docker-compose up` brings all services online
- [ ] Sync: Agree on API contracts (Section 4)
- [ ] Baseline: Take latency baseline on empty DB (< 1s)

**Milestone 1 (1:30)** — M1 Merges to Develop
```bash
# M1 finishes first feature
git push origin feature/ingestion-pipeline
# Create PR, request review from M2 + M4
# Once approved:
git checkout develop
git pull origin develop
git merge feature/ingestion-pipeline --squash
git commit -m "feat(ingestion): complete document ingestion pipeline"
git push origin develop
# Delete feature branch
git push origin --delete feature/ingestion-pipeline
```

**Sync 2 (1:45)**
- [ ] All members demo isolated features
- [ ] Identify blockers (does anyone need another feature?)
- [ ] Branch status: M1 merged, M2-M5 in progress

**Milestone 2 (3:00)** — All Features Merge to Develop, Then to Main
```bash
# M2, M3, M4, M5 each create final PRs
# All request review
# Once all approved:

git checkout develop
git pull origin develop

# Merge M2 PR (reviewed)
git merge feature/hybrid-search --squash
git commit -m "feat(search): implement hybrid search with RRF fusion"

# Merge M3 PR (reviewed)
git merge feature/generation-guardrails --squash
git commit -m "feat(generation): add Claude integration with source attribution"

# Merge M4 PR (reviewed)
git merge feature/caching-performance --squash
git commit -m "feat(cache): implement 3-layer Redis caching"

# Merge M5 PR (reviewed)
git merge feature/frontend-ui --squash
git commit -m "feat(frontend): build React chat UI with metrics panel"

git push origin develop

# Now merge develop → main
git checkout main
git pull origin main
git merge develop -m "Milestone: v0.5.0 - All features integrated"
git push origin main
git tag v0.5.0
git push origin v0.5.0
```

**Sync 3 (3:20)**
- [ ] All members: Test full end-to-end flow on main
- [ ] Demo rehearsal: Walk through 3-4 scenarios
- [ ] Fix any bugs (quick bugfix branches off main)

**Milestone 3 (4:00)** — Final Tag
```bash
# Update docs, commit final changes
git checkout main
git add docs/architecture.png docs/challenge-analysis.md README.md
git commit -m "docs: add architecture diagram and final analysis"
git push origin main

# Final tag
git tag v1.0.0 -m "Release v1.0.0 - Production-ready RAG capstone"
git push origin v1.0.0
```

---

### 5.9 GitHub Actions (Optional but Recommended)

Create `.github/workflows/ci.yml`:

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop, feature/**]
  pull_request:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov
      
      - name: Lint with flake8
        run: flake8 backend/app --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Run unit tests
        run: pytest tests/ -v --cov=backend/app --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm install && npm run build
```

---

### 5.10 Git Workflow Diagram (ASCII)

```
Timeline: 0:00 → 4:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0:00 ──────────────────────────────────────────────────────
     Clone repo, create all feature branches from develop

0:30 ──────────────────────────────────────────────────────
     [SYNC 1] Docker verify, API contracts agreed

0:30–1:30 ──────────────────────────────────────────────────
     M1          M2              M3              M4        M5
     │           │               │               │         │
     feature/    feature/        feature/        feature/  feature/
     ingestion   hybrid-search   generation      cache     frontend
     │           │               │               │         │
     (commits)   (commits)       (commits)       (commits) (commits)

1:30 ──────────────────────────────────────────────────────
     [SYNC 2] M1 demos, merges to develop

     develop ← feature/ingestion-pipeline
     │

1:45–3:00 ──────────────────────────────────────────────────
     M2          M3              M4              M5
     │           │               │               │
     feature/    feature/        feature/        feature/
     hybrid      generation      cache           frontend
     │           │               │               │
     (commits)   (commits)       (commits)       (commits)

3:00 ──────────────────────────────────────────────────────
     [SYNC 3] Integration sprint
     
     develop ← feature/hybrid-search
     develop ← feature/generation-guardrails
     develop ← feature/caching-performance
     develop ← feature/frontend-ui
     
     main ← develop (merge v0.5.0)

3:20 ──────────────────────────────────────────────────────
     [SYNC 4] Full E2E test, demo rehearsal

3:50–4:00 ──────────────────────────────────────────────────
     Final docs, tag v1.0.0
     
     main: v1.0.0 ← commit "Release v1.0.0"
           └─ all features working
           └─ production-ready
           └─ documented

```

---

### 5.11 Branch Protection Rules (GitHub Settings)

Go to **Settings → Branches → Add rule** for `main` and `develop`:

```
Branch name pattern: main
  ☑ Require a pull request before merging
    ☑ Require approvals (1)
  ☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  ☑ Require code owner reviews (optional)
  ☑ Restrict who can push to matching branches
    Specify: 2+ team members from M1-M5

Branch name pattern: develop
  ☑ Require a pull request before merging
    ☑ Require approvals (1)
  ☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  ☑ Dismiss stale pull request approvals
  ☑ Allow specified actors to bypass pull request requirements (ONLY team leads)

Branch name pattern: feature/**
  ☐ Allow pushes that create matching branches (allow all)
  ☑ Allow deletions
```

---

### 5.12 Team Responsibilities

| Role | Primary | Code Review | Merge Authority |
|------|---------|-------------|-----------------|
| **M1** | feature/ingestion-pipeline | Reviews M2, M4 | Can merge own feature → develop |
| **M2** | feature/hybrid-search | Reviews M1, M3 | Can merge own feature → develop |
| **M3** | feature/generation-guardrails | Reviews M2, M4 | Can merge own feature → develop |
| **M4** | feature/caching-performance | Reviews M3, M5 | Can merge own feature → develop |
| **M5** | feature/frontend-ui | Reviews M1, M4 | Can merge own feature → develop |
| **All** | Shared files (docker-compose, schemas) | Coordinate changes | All must agree |

**Escalation**: If two members disagree on a merge, discuss in Slack before proceeding.

---

## 6. IMPLEMENTATION TIMELINE (4 Hours)

### Phase 1: Setup & Scaffolding (0:00–0:30)
- [ ] Clone repo, create all 5 feature branches from `develop`
- [ ] Run `docker-compose up` — verify Qdrant, Redis, PostgreSQL reachable
- [ ] Verify API contracts agreement in Slack/doc
- [ ] M1 scaffolds FastAPI `main.py` with 5 empty routers
- [ ] M5 scaffolds React `App.jsx` with placeholder components

**Owner**: M1 (backend setup), M5 (frontend setup)  
**Deliverable**: Docker services running, 5 routers instantiated, no errors

---

### Phase 2a: Individual Feature Build (0:30–1:30)
Parallel work — each member builds their feature in isolation.

**M1 (Ingestion)**
- [ ] Implement `FixedChunker` class
- [ ] Implement `SemanticChunker` class
- [ ] Implement `MetadataExtractor`
- [ ] Test with one sample PDF
- [ ] Ingest 1 doc end-to-end, verify chunks in Qdrant + PostgreSQL
- [ ] Commit to `feature/ingestion-pipeline`

**M2 (Hybrid Search)**
- [ ] Create Qdrant collection with HNSW, cosine similarity
- [ ] Integrate OpenAI embeddings client
- [ ] Implement BM25 indexing from static documents (or use M1's ingested chunks)
- [ ] Implement RRF fusion algorithm
- [ ] Test search with hardcoded query, verify vector + BM25 both return results
- [ ] Commit to `feature/hybrid-search`

**M3 (Generation)**
- [ ] Integrate Claude Sonnet 4.0 via Anthropic SDK
- [ ] Write grounding system prompt
- [ ] Implement streaming response generator
- [ ] Test with one hardcoded context + query
- [ ] Verify SSE output format matches contract
- [ ] Commit to `feature/generation-guardrails`

**M4 (Caching)**
- [ ] Connect to Redis 7
- [ ] Implement embedding cache (set/get with TTL)
- [ ] Implement retrieval cache (set/get with TTL)
- [ ] Implement metrics collector (in-memory counters)
- [ ] Test Redis set/get locally
- [ ] Commit to `feature/caching-performance`

**M5 (Frontend)**
- [ ] Create React app structure with Vite + TailwindCSS
- [ ] Scaffold ChatPanel, UploadPanel, MetricsBar, FilterBar components
- [ ] Hardcode one sample message to verify build
- [ ] Commit to `feature/frontend-ui`

**Sync Checkpoint (1:30–1:45)**
- Each member briefly demos isolated feature (no integration)
- Identify blockers — does anyone need another feature to unblock?
- M1 merges `feature/ingestion-pipeline` → `develop`

---

### Phase 2b: Enhanced Build with Integration Prep (1:45–3:00)
Parallel work — members enhance features and start thinking about integration.

**M1 (Ingestion) — Enhancements**
- [ ] Add semantic chunking comparison logic
- [ ] Store chunks in PostgreSQL with proper schema
- [ ] Create 3 sample documents (troubleshooting guide, API docs, FAQ)
- [ ] Add unit tests for edge cases (empty doc, single page, non-ASCII)
- [ ] Update `/api/ingest` endpoint to call chunker
- [ ] Commit and create PR to `develop`

**M2 (Hybrid Search) — Enhancements**
- [ ] Finalize RRF fusion with configurable k parameter
- [ ] Implement metadata filtering (department, category, date)
- [ ] Add latency instrumentation to every stage
- [ ] Implement `/api/search` endpoint with request validation
- [ ] Test with 10+ error code queries (verify hybrid > vector-only)
- [ ] Create PR to `develop`

**M3 (Generation) — Enhancements**
- [ ] Finalize grounding prompt with source instruction
- [ ] Implement hallucination fallback message
- [ ] Add source attribution extraction from chunks
- [ ] Implement `/api/generate` streaming SSE endpoint
- [ ] Test with chunks from M2's search
- [ ] Token counting integration
- [ ] Create PR to `develop`

**M4 (Caching) — Enhancements**
- [ ] Add response cache layer (3rd layer)
- [ ] Implement context compression (top-20 → top-5)
- [ ] Build `/api/metrics` endpoint with all KPIs
- [ ] Integrate embedding cache into M2's search
- [ ] Integrate retrieval cache into M2's search
- [ ] Integrate response cache into M3's generation
- [ ] Create PR to `develop`

**M5 (Frontend) — Enhancements**
- [ ] Wire ChatPanel to `/api/generate` streaming
- [ ] Wire UploadPanel to `/api/ingest`
- [ ] Wire FilterBar to `/api/search` with dropdown state
- [ ] Wire SourceCard to display chunk metadata with clickable source
- [ ] Wire MetricsBar to `/api/metrics` with 1-second refresh
- [ ] Add architecture diagram component
- [ ] Create PR to `develop`

**Integration Sprint (3:00–3:20)**
- All PRs merged into `develop` one by one
- M5 runs full end-to-end flow: upload doc → query → response with sources
- Fix integration bugs (API contract mismatches, missing fields, etc.)
- All members review each other's PRs
- Merge `develop` → `main`, tag v0.5.0

---

### Phase 3: Demo Rehearsal (3:20–3:50)

**Demo 1: Chunking (M1 owns)**
1. Upload `troubleshooting.pdf` with fixed chunking
2. Query: "How do I fix database timeout in step 3?"
3. Show results: Fixed chunking splits mid-sentence, token count = 850
4. Upload same doc with semantic chunking
5. Re-run query: Semantic chunking returns step 3 complete, token count = 450
6. Show token reduction and accuracy improvement

**Demo 2: Error Code Retrieval (M2 owns)**
1. Upload `kubernetes-guide.pdf` with "ImagePullBackOff" error section
2. Query pure vector search: "How do I fix ImagePullBackOff?"
3. Show results: Returns rank 47, wrong section
4. Run hybrid search: Shows rank 1, correct section
5. Explain RRF fusion combining BM25 precision + vector recall

**Demo 3: Cache Speedup (M4 owns)**
1. Query: "How do I restart a pod?" (cold cache)
2. Show latency: Embed (100ms) + Search (350ms) + Generate (1,800ms) = 2,250ms
3. Repeat same query
4. Show latency: All cache hits = 5ms
5. Show live metrics: cache_hit_rate=0.73, avg_latency=340ms (was 2250)

---

### Phase 4: Final Commit & Tag (3:50–4:00)
- [ ] Tag `v1.0.0` on `main`
- [ ] Commit architecture diagram and challenge-analysis.md to docs/
- [ ] Ensure README has setup instructions (docker-compose up, sample queries)
- [ ] Push all branches and tag to remote

---

## 7. VERIFICATION & TESTING STRATEGY

### Unit Tests (Per Member)
**M1 Ingestion**: 10+ tests
- Chunk sizing edge cases (empty, single char, max size)
- Semantic boundary detection (real paragraphs, sections, lists)
- Metadata extraction from various PDF formats
- Non-ASCII character handling

**M2 Search**: 15+ tests
- Vector search isolation
- BM25 search isolation
- RRF fusion correctness (rank-based scoring)
- Metadata filtering combinations
- Latency instrumentation accuracy

**M3 Generation**: 10+ tests
- Prompt grounding enforcement (answer must be in chunks)
- Hallucination fallback trigger
- Source attribution extraction
- Token counting accuracy
- Streaming SSE format validation

**M4 Caching**: 12+ tests
- Cache hit/miss tracking
- TTL expiry behavior
- Key collision handling
- Context compression token reduction
- Metrics collector accuracy

**M5 Frontend**: 8+ tests
- Component rendering
- API integration (mocked)
- State management (query input, response display)
- Metrics refresh interval
- Responsive layout

---

### Integration Tests (End-to-End)
```bash
# Full user flow
1. Upload k8s-guide.pdf (M1)
2. Query "ImagePullBackOff error" (M5)
3. Verify hybrid search returns top result (M2)
4. Verify response is grounded in retrieved chunks (M3)
5. Verify cache metrics updated (M4)
6. Verify metrics panel shows <500ms latency (M5)
7. Repeat same query → verify <10ms (cached)
```

---

### Performance Benchmarks (Acceptance Criteria)
| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Cold latency | ~2,250ms | <500ms | Target |
| Warm latency (cached) | N/A | <5ms | Target |
| Tokens per request | 10,000 | <2,500 | Target |
| Cache hit rate | 0% | >70% | Target |
| Error code retrieval rank | 47+ | 1-3 | Target |
| Semantic vs fixed chunking accuracy | 40% | 95% | Target |

---

### Testing Environment
- **Local**: Docker Compose (all services)
- **Sample Data**: 3 PDFs + 3 markdown files in `sample-docs/`
- **Load**: 10 concurrent queries via load test script (optional)

---

## 8. ARTIFACTS & DELIVERABLES

### Presentation Artifacts (for judges)
- Slide deck (4-7 slides)
- Q&A prep bank (20+ questions with answers)
- Architecture diagram (system overview)
- Demo script (3 scenarios with expected outputs)

### Code Artifacts
- `backend/`: FastAPI with 5 modules, all endpoints, caching, instrumentation
- `frontend/`: React components, real API integration, live metrics
- `infra/docker-compose.yml`: All services in one file
- `docs/architecture.png`: System diagram
- `README.md`: Setup instructions + quick start

### Git Artifacts
- `main` branch: Production-ready, tagged v1.0.0
- `develop` branch: Integration history, all features merged
- 5 feature branches: Clean, single-feature commits
- 15+ PRs: All reviewed, no conflicts

---

## 9. EVALUATION CRITERIA MAPPING (UPDATED)

### Retrieval Accuracy (25%) ⭐
**How we win this category:**

**M1 (Ingestion) contribution:**
- [ ] Semantic chunking preserves context (not splitting mid-sentence)
- [ ] Metadata tagging (department, category, section) enables filtering
- [ ] Chunk overlap prevents missing relevant boundaries
- **Metric**: Recall@5 for 20 test queries >85%

**M2 (Hybrid Search) contribution:**
- [ ] Vector search captures semantic similarity
- [ ] BM25 captures exact-match precision (error codes)
- [ ] RRF fusion ranks results correctly
- [ ] Metadata filtering eliminates irrelevant results
- **Metric**: nDCG@5 > 0.80 on mixed query types

**Demo 2 (Error Code)**: "ImagePullBackOff" returns rank 1 (not 47)
- **Before**: Vector-only misses exact string match
- **After**: Hybrid (vector + BM25) returns correct section first
- **Measured by**: Rank improvement, chunk relevance score

**Success**: Hybrid search outperforms vector-only on 15+ test queries across:
- Semantic queries ("How do I debug pod issues?")
- Exact-match queries ("ImagePullBackOff error")
- Multi-word queries ("RBAC permission denied")

---

### Production Readiness (20%) 🏭
**How we win this category:**

**M4 (Caching) primary driver:**
- [ ] Redis 7 deployed, monitored, replicated-ready
- [ ] Three-layer cache with TTLs (24h, 4h, 2h)
- [ ] Cache hit rate instrumentation (per layer)
- [ ] Graceful degradation if cache fails
- **Metric**: 99.9% uptime in test load

**M3 (Generation) contribution:**
- [ ] Streaming SSE for perceived zero latency
- [ ] Timeout handling (Claude max wait: 60s)
- [ ] Fallback responses when knowledge base empty
- [ ] Token limit enforcement (max 100K input)

**M2 (Search) contribution:**
- [ ] Qdrant production configuration (persistence, replication-ready)
- [ ] BM25 index pre-computed for fast queries
- [ ] Latency SLA: <200ms p99 for search

**M1 (Ingestion) contribution:**
- [ ] Async document processing (doesn't block chat)
- [ ] Incremental indexing (add docs without re-chunking all)

**M5 (Frontend) contribution:**
- [ ] Graceful error handling (network timeouts, 500 errors)
- [ ] Retry logic with exponential backoff

**Success metrics**:
- [ ] Cold latency <500ms p50
- [ ] Warm latency <10ms p50 (cached)
- [ ] Concurrent users: 100+ without degradation
- [ ] SLA: 95% of queries respond <2 seconds

---

### Architecture Design (15%) 🏛️
**How we win this category:**

**System-level design (M5 owns architecture diagram):**
- [ ] Clean separation of concerns: 5 independent modules
- [ ] Async/await throughout (no blocking calls)
- [ ] Dependency injection (no hardcoded configs)
- [ ] Observable (metrics, logs, traces)

**Component design:**
- **M1 (Ingestion)**: Parser → Chunker → Embedder → Storage (idempotent)
- **M2 (Search)**: Query → Embed → Vector Search || BM25 → RRF → Filter → Return
- **M3 (Generation)**: Context → Prompt → Claude → Stream → Attribution
- **M4 (Cache)**: Key derivation → TTL → Hit/Miss tracking → Metrics
- **M5 (Frontend)**: API client → State → Render → Event handlers

**Scalability design:**
- Horizontal: Add more FastAPI workers (no shared state in app)
- Vertical: Redis/Qdrant can shard on key/partition
- Data: Incremental ingestion (not re-index entire KB)

**Diagram deliverable** (committed to `docs/architecture.png`):
```
┌─────────────────────────────────────────────────────────────┐
│                    TECHNICAL SUPPORT COPILOT                 │
├─────────────────────────────────────────────────────────────┤
│ Frontend (React)                                             │
│  ├─ Chat Panel (streaming SSE)                              │
│  ├─ Upload Panel (M1 /ingest)                               │
│  ├─ Source Cards (M2 /search results)                       │
│  └─ Metrics Bar (M4 /metrics live)                          │
├─────────────────────────────────────────────────────────────┤
│ API Layer (FastAPI)                                         │
│  ├─ POST /ingest (M1)     → parser → chunker → DB           │
│  ├─ POST /search (M2)     → embed → vector+bm25 → rrf       │
│  ├─ POST /generate (M3)   → stream → Claude → sources       │
│  ├─ GET /metrics (M4)     → cache stats + latency           │
│  └─ Cache Middleware (M4) → L1, L2, L3 intercept           │
├─────────────────────────────────────────────────────────────┤
│ Data & Processing Layer                                     │
│  ├─ Qdrant (vector DB, HNSW, metadata)                      │
│  ├─ BM25 Index (sparse search)                              │
│  ├─ PostgreSQL (metadata, chunks, audit log)                │
│  ├─ Redis (L1 embed cache, L2 retrieval cache, L3 response) │
│  └─ OpenAI Embeddings (1,536-dim)                           │
├─────────────────────────────────────────────────────────────┤
│ Infrastructure                                              │
│  └─ Docker Compose (all services, single docker-compose.yml)│
└─────────────────────────────────────────────────────────────┘
```

**Success**: Diagram clearly shows data flow, no spaghetti dependencies

---

### Hallucination Prevention (15%) 🛡️
**How we win this category:**

**M3 (Generation) primary driver:**
- [ ] Grounding prompt: "Answer ONLY from provided chunks"
- [ ] Fallback message: "I don't have reliable information..."
- [ ] Source citation on every response: `[source: k8s-guide.pdf § line 234]`
- [ ] Confidence scoring (optional): High/Low based on chunk count

**M2 (Search) contribution:**
- [ ] Retrieve relevant chunks (accuracy prevents bad context)
- [ ] Return confidence scores (M3 uses to set confidence_level)
- [ ] Filter irrelevant docs (metadata filtering)

**M1 (Ingestion) contribution:**
- [ ] Chunk text accurately (no mangled PDFs → bad context)
- [ ] Preserve section headers (M3 uses in source citation)

**Demo 4 (Hallucination Prevention)** — *New demo to address this criterion*:
Query: "What's the secret password for the admin panel?"
- **Expected**: "I don't have reliable information to answer this question..."
- **NOT**: "The password is..."
- **Demonstrate**: Query outside knowledge base, verify fallback triggers

Query: "How do I fix a pod issue?" (answer in docs)
- **Expected**: Correct answer with `[source: k8s-guide.pdf § Troubleshooting]`
- **NOT**: Made-up steps or hallucinated commands

**Success metrics**:
- [ ] 100% of out-of-domain queries trigger fallback
- [ ] 100% of in-domain queries include source citation
- [ ] No hallucinated facts in 20-query evaluation set

---

### Innovation & Bonus Features (25%) ⭐
**How we win this category (where we differentiate):**

**Tier 1: Core Innovation (Required for this criterion)**
- [ ] **Semantic Chunking** (vs basic fixed-size): Detects section boundaries, preserves meaning
- [ ] **Hybrid Search Fusion**: RRF algorithm combining vector + sparse search
- [ ] **Three-Layer Caching**: Embedding (24h) + Retrieval (4h) + Response (2h) with hit tracking
- [ ] **Streaming Generation**: SSE for perceived zero latency (time-to-first-token)
- [ ] **Live Metrics Dashboard**: Real-time cache hit rate, latency, token counts

**Tier 2: Bonus Features (Differentiate further)**
- [ ] **Context Compression**: Rerank top-20 → top-5 (reduce tokens 80%)
- [ ] **Source Attribution**: Clickable citations linking to exact chunk in UI
- [ ] **Metadata-Aware Filtering**: Department/category/date range queries
- [ ] **Reranking** (optional): Cross-encoder model to improve RRF scores
- [ ] **Query Expansion**: Expand "pod" → "pod, container, deployment" (optional)
- [ ] **Batch Ingestion**: Upload multiple files at once with progress bar
- [ ] **Admin Dashboard**: View indexed documents, search stats, cache performance

**Tier 3: Advanced (If time permits)**
- [ ] **Feedback Loop**: User upvotes/downvotes sources, improves future ranking
- [ ] **A/B Testing Framework**: Test different chunking sizes, cache TTLs
- [ ] **Cost Tracking**: Estimate per-query cost in USD (tokens × pricing)
- [ ] **Load Testing**: Verify 100 concurrent users, latency under load
- [ ] **Evaluation Metrics**: Recall@5, nDCG@5, MRR computed from test set

**How innovation is graded** (25% weight):
- Semantic chunking vs fixed: +5%
- Hybrid search + RRF: +5%
- Three-layer caching strategy: +5%
- Streaming + context compression: +5%
- Bonus features (any 2 of Tier 2): +5%
- **Total**: 25%

**Demo 5 (Innovation Showcase)** — *New demo*:
- Show context compression: "Reducing 10,000 tokens → 2,500 tokens via reranking + truncation"
- Show feedback loop (if implemented): "User marked source as helpful, impacting future ranking"
- Show cost calculation: "Est. $0.0012 per query after caching"

---

## 9b. SCORING MATRIX (How to Maximize Each Category)

| Category | Weight | M1 | M2 | M3 | M4 | M5 | How to Nail It |
|----------|--------|----|----|----|----|----|----|
| **Retrieval Accuracy** | 25% | Chunking | Hybrid Search + RRF | Context Quality | Caching Hit Rate | UI Display | Demo 2: error codes ranked correctly |
| **Production Readiness** | 20% | Async ingest | <200ms p99 | Timeouts + fallback | Cache TTL + monitoring | Graceful errors | Cold <500ms, warm <10ms, 99.9% uptime |
| **Architecture Design** | 15% | Idempotent parser | Modular search | DI for Claude client | Cache abstraction | Component separation | Diagram + clean file structure |
| **Hallucination Prevention** | 15% | Accurate chunks | Relevant results | Grounding + citation | Avoids stale context | Displays sources | Demo 4: fallback on OOD queries |
| **Innovation & Bonus** | 25% | Semantic vs fixed | Reranking (bonus) | Feedback loop (bonus) | Compression + feedback | Cost visualization | 2+ Tier 2 features + 1 Tier 3 |

---

## 10. (UPDATED) SUCCESS CRITERIA CHECKLIST

### ✅ Retrieval Accuracy (25%)
- [ ] **Semantic chunking** outperforms fixed by >20% on benchmark (Recall@5 >85%)
- [ ] **Hybrid search** (vector + BM25) returns correct chunk in top 3 for:
  - Error codes ("ImagePullBackOff" → rank 1, not 47)
  - Semantic queries ("Pod restart" → finds Troubleshooting section)
  - Technical queries ("RBAC deny" → finds security section)
- [ ] **Demo 2**: Error code retrieval shows vector-only fails, hybrid succeeds
- [ ] **nDCG@5 score** >0.80 on 20-query evaluation set

### ✅ Production Readiness (20%)
- [ ] **Cold latency** <500ms p50, <2s p99
- [ ] **Warm latency** <10ms p50 (cache hit)
- [ ] **Cache hit rate** >70%
- [ ] **Concurrent users** 100+ without degradation (Docker limits)
- [ ] **SLA compliance** 95% of queries <2 seconds
- [ ] **Error handling** graceful degradation (missing cache, Redis down, API timeout)
- [ ] **Monitoring** /metrics endpoint live, all 3 cache layers instrumented

### ✅ Architecture Design (15%)
- [ ] **File separation** (5 modules, zero overlap) → no merge conflicts
- [ ] **Async/await** throughout (no blocking FastAPI routes)
- [ ] **Dependency injection** (Redis, Qdrant, Claude clients passed in)
- [ ] **Docker Compose** single file, all services included
- [ ] **Architecture diagram** in `docs/architecture.png`, clear data flow
- [ ] **API contracts** respected (Section 4), no changes mid-sprint

### ✅ Hallucination Prevention (15%)
- [ ] **Grounding prompt** enforces "answer only from chunks"
- [ ] **Fallback message** triggers for out-of-domain queries (100%)
- [ ] **Source attribution** on every response (100%)
- [ ] **Demo 4**: Query outside knowledge base → fallback triggers
- [ ] **Confidence scoring** optional but nice-to-have
- [ ] **No hallucinated facts** in 20-query evaluation set

### ✅ Innovation & Bonus Features (25%)
- [ ] **Semantic chunking** vs fixed (required, +5%)
- [ ] **Hybrid search + RRF** (required, +5%)
- [ ] **3-layer caching** (required, +5%)
- [ ] **Streaming SSE** (required, +5%)
- [ ] **2 Bonus features** from Tier 2 (reranking, compression, metadata filter, etc.) (+5%)
- [ ] **Demo 5**: Context compression or feedback loop showcase (+bonus %)

---

## 10. RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| **API Contract Disputes** | Contracts defined in Section 4 before coding. Any changes require all impacted members' approval. |
| **Integration Bugs at 3h Mark** | Each member writes unit tests as they build. Integration sprint starts with mocked endpoints to catch issues early. |
| **Qdrant/Redis Connectivity** | Docker Compose verified at 0:30 sync. If service fails, restart entire compose stack. |
| **Demo Failure** | Demos rehearsed 30 minutes before presentation. If live demo fails, show pre-recorded video or static screenshots. |
| **Token Limits** | Claude Sonnet has 200K context window. Verify in testing that max prompt <100K tokens to leave buffer. |
| **Cache Pollution** | Cache TTLs set conservatively (24h, 4h, 2h) to avoid stale data. Manual flush available if needed. |
| **Git Merge Conflicts** | File separation (Section 5) eliminates 99% of conflicts. Any conflicts resolved at sync points. |

---

## 11. SUCCESS DEFINITION

**We've succeeded when:**
1. ✅ All 5 members can build their feature independently without blocking each other
2. ✅ Cold latency improves from 2,250ms → <500ms (verified in Demo 3)
3. ✅ Cache hit rate exceeds 70% on repeated queries
4. ✅ Error code retrieval works with hybrid search (Demo 2)
5. ✅ Semantic chunking outperforms fixed chunking (Demo 1)
6. ✅ All 4 evaluation criteria (30% + 25% + 20% + 15%) fully addressed
7. ✅ Code is production-ready: Docker Compose, instrumented, tested, documented
8. ✅ No merge conflicts, clean git history, v1.0.0 tagged
9. ✅ Judges see measurable before/after metrics in all 3 demos

---

## 12. NEXT STEPS (After Approval)

1. **All members read and agree** to this plan (30 minutes)
2. **Setup phase** (0:30): Clone repo, Docker services, sync on contracts
3. **Begin implementation** following the timeline in Section 6
4. **Use Slack/Discord** for real-time blockers during build
5. **Execute demo rehearsal** 30 min before presentation
6. **Tag v1.0.0** and submit

---

**Document Version**: 1.0  
**Last Updated**: 2024-06-03  
**Approved By**: [Awaiting Team Sign-off]
