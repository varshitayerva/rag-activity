# MergeAll Strategy: Integrating Member 1 & Member 2 Work

**Current Status**: You are on branch `MergeAll` (created from `feature/hybrid-search`)

---

## 1. REFERENCE ARCHITECTURE

From `production-rag-track4.md` (origin/main):

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
```

**Key Requirement**: Ingestion pipeline (M1) + Hybrid search (M2) must work **end-to-end**.

---

## 2. WHAT EACH MEMBER BUILT

### Member 1: Ingestion Pipeline (feature/ingestion-pipeline)
**Status**: ✅ Merged into `origin/develop`

**Deliverables**:
- PDF/Markdown parser with fixed & semantic chunking
- Metadata extraction: `{doc_id, filename, section, page, uploaded_at, department, category}`
- Chunk storage to PostgreSQL + Vector DB

**Files** (already in your MergeAll):
- `backend/app/ingestion/chunker.py` — FixedChunker, SemanticChunker
- `backend/app/ingestion/parser.py` — PDF/Markdown parsing
- `backend/app/ingestion/metadata.py` — Metadata extraction
- `backend/app/ingestion/service.py` — Orchestration
- `backend/app/schemas.py` — Pydantic models

**Endpoint**: `POST /api/ingest` (should be in `backend/app/main.py`)

---

### Member 2: Hybrid Search (feature/hybrid-search)
**Status**: ✅ Merged into `origin/develop` (this is what was added in 40e0ea4)

**Deliverables**:
- Qdrant HNSW vector search
- BM25 sparse search
- RRF (Reciprocal Rank Fusion) combination
- Metadata filtering
- Latency instrumentation

**New Files in 40e0ea4**:
- `backend/app/search/bm25_search.py` — BM25 implementation
- `backend/app/search/embeddings.py` — Embedding client with mock fallback
- `backend/app/search/hybrid_search.py` — HybridSearchService orchestration
- `backend/app/search/postgres_client.py` — PostgreSQL vector storage
- `backend/app/search/qdrant_client.py` — Qdrant client (optional, pgvector chosen)
- `backend/app/search/rrf_fusion.py` — RRF fusion algorithm
- `backend/main.py` — FastAPI endpoints for search
- `SETUP_GUIDE.md` — Complete setup documentation
- `IMPLEMENTATION_COMPLETE.md` — Status report

**Endpoint**: `POST /api/search` (in `backend/main.py`)

---

## 3. WHAT NEEDS TO BE INTEGRATED

### Current Situation
Your `MergeAll` branch (`eb195a0`) has:
- ✅ Member 1's ingestion pipeline code
- ❌ Member 2's search code is NOT yet integrated (newer commit 40e0ea4)
- ❌ The `backend/main.py` needs to have BOTH ingestion AND search endpoints

### Integration Tasks

#### A. Pull Member 2's Search Code into MergeAll
1. **Merge `origin/develop` into `MergeAll`**
   - This will pull commit 40e0ea4 (Member 2's work)
   - Likely conflicts: `backend/main.py` (both sides add endpoints)
   - Resolution: Keep BOTH `/api/ingest` (Member 1) AND `/api/search` (Member 2)

#### B. Verify the Integration Endpoints
After merging, `backend/main.py` should have:
- `POST /api/ingest` — Member 1's ingestion
- `POST /api/search` — Member 2's hybrid search (vector + BM25 + RRF)
- `GET /api/stats` — Statistics about indexed data
- `POST /api/load-demo` — Load demo chunks (Member 2 added this)

#### C. Test End-to-End Flow
1. **Ingest a document** via `POST /api/ingest`
   - Chunks are extracted (fixed or semantic)
   - Metadata is stored
   - Chunks are embedded
   - Embeddings + metadata stored in PostgreSQL / Qdrant

2. **Search ingested document** via `POST /api/search`
   - Query is embedded
   - Vector search runs on Qdrant
   - BM25 search runs on chunks
   - RRF fuses results
   - Top-k returned with metadata and latency breakdown

---

## 4. EXPECTED MERGE CONFLICTS

### Conflict 1: `backend/main.py`
**Reason**: Both Member 1 and Member 2 modified the main FastAPI app

**Current MergeAll `main.py`**:
- Has ingestion endpoint structure
- May or may not have search endpoints

**Incoming `origin/develop` `main.py`**:
- Has Member 2's search endpoints
- Has `/load-demo`, `/stats`, `/health`

**Resolution Strategy**:
✅ **KEEP BOTH** — Merge all endpoints from both sides:
```python
# From Member 1
@app.post("/api/ingest")
async def ingest_documents(request: IngestRequest):
    ...

# From Member 2
@app.post("/api/search")
async def search(request: SearchRequest):
    ...

@app.get("/api/stats")
@app.post("/api/load-demo")
@app.get("/api/health")
```

### Conflict 2: `backend/app/__init__.py` or `backend/app/search/__init__.py`
**Reason**: Imports might differ (Qdrant vs PostgreSQL vector DB)

**Resolution Strategy**:
✅ Keep both imports:
```python
from .ingestion import *  # Member 1
from .search import *     # Member 2
```

### Conflict 3: `backend/app/models.py` or `backend/app/schemas.py`
**Reason**: Both members might define Pydantic models

**Resolution Strategy**:
✅ **KEEP BOTH** — Merge all Pydantic models:
- Member 1: `IngestRequest`, `ChunkSchema`, `IngestResponse`
- Member 2: `SearchRequest`, `SearchResponse`, `StatsResponse`

### Conflict 4: `backend/setup_postgres.py`
**Reason**: Both might define database schema

**Resolution Strategy**:
⚠️ **BE CAREFUL** — Make sure the schema supports:
- Chunks table with: `id, chunk_id, text, doc_id, filename, section, page, department, category, embedding, created_at`
- Correct indexes for search performance
- Choose ONE version that has all necessary columns

---

## 5. MERGE PROCEDURE (Step-by-Step)

### Step 1: Fetch Latest from Remote
```bash
git fetch origin
```

### Step 2: Merge `origin/develop` into `MergeAll`
```bash
git merge origin/develop
```

### Step 3: Resolve Conflicts (if any)
For each conflicted file:
1. Open file in VS Code
2. Use **"Accept Both Changes"** or manually edit to keep essentials from both sides
3. Stage the file: `git add <file>`

### Step 4: Verify Integration
After merge:
1. Check that `backend/main.py` has BOTH `/api/ingest` and `/api/search` endpoints
2. Check that all imports work: `from app.ingestion import *` and `from app.search import *`
3. Check that database schema includes all columns needed by both pipelines

### Step 5: Commit the Merge
```bash
git commit -m "Merge: Integrate Member 1 (ingestion) + Member 2 (hybrid search) pipelines"
```

### Step 6: Test End-to-End (Post-Merge)
```bash
# Run the server
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 9999

# Test ingestion (Member 1)
curl -X POST http://localhost:9999/api/ingest \
  -H "Content-Type: application/json" \
  -d '{...}'

# Test search (Member 2)
curl -X POST http://localhost:9999/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "top_k": 5, "search_type": "hybrid"}'
```

---

## 6. CRITICAL INTEGRATION POINTS

### Database Initialization
**File**: `backend/setup_postgres.py`
- Ensure table `chunks` has all columns: `chunk_id, text, doc_id, filename, section, page, department, category, embedding`
- Both pipelines read/write to this table

### Vector DB Connection
**Decision Point**: Qdrant vs PostgreSQL pgvector
- **Member 2's choice**: Started with Qdrant, then switched to PostgreSQL pgvector
- **Your current choice**: PostgreSQL + BYTEA (since pgvector unavailable)
- **Recommendation**: Stick with PostgreSQL solution (in 40e0ea4)

### Service Initialization
**File**: `backend/app/main.py`
```python
from app.ingestion import IngestionService  # Member 1
from app.search import HybridSearchService   # Member 2

# Initialize both
ingestion_service = IngestionService(...)
search_service = HybridSearchService(...)
```

### Workflow Integration
```
1. User uploads document via POST /api/ingest (Member 1 endpoint)
   ↓ Document is parsed, chunked, embedded
   ↓ Chunks stored in PostgreSQL with embeddings
   ↓ Response: { "status": "success", "chunks_count": 50 }

2. User searches via POST /api/search (Member 2 endpoint)
   ↓ Query is embedded
   ↓ Vector search + BM25 search + RRF fusion
   ↓ Response: { "chunks": [...], "latency_ms": {...} }
```

---

## 7. SUCCESS CRITERIA AFTER MERGE

- [ ] `git merge origin/develop` completes (with or without conflicts)
- [ ] All conflicts resolved by keeping essential code from BOTH sides
- [ ] `backend/main.py` has both `/api/ingest` and `/api/search` endpoints
- [ ] Server starts without import errors: `uvicorn main:app`
- [ ] `/api/health` returns 200
- [ ] `/api/ingest` accepts documents
- [ ] `/api/search` returns hybrid results
- [ ] End-to-end test: ingest → search → get results with metadata
- [ ] No Python import errors or name collisions

---

## 8. NEXT STEPS (After Merge)

1. **Push to remote**: `git push origin MergeAll`
2. **Create PR**: `MergeAll → develop` (for team review)
3. **Deploy test**: Run full integration tests
4. **Prepare for Member 3**: LLM generation pipeline (separate PR)

---

**Ready to merge? Let me know and I'll help resolve any conflicts!**
