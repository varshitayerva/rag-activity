# FDE RAG - PostgreSQL + pgvector + BM25 Setup Guide

## Overview
Full end-to-end RAG system with:
- **PostgreSQL** for persistent vector storage with BM25 keyword search
- **Vector embeddings** for semantic search (mock embeddings fallback)
- **BM25** algorithm for keyword search
- **RRF (Reciprocal Rank Fusion)** for hybrid search combining both methods
- **FastAPI** REST API with full documentation

---

## Prerequisites

### 1. PostgreSQL Installation
- Download from: https://www.postgresql.org/download/windows/
- Install with default settings
- **Credentials:**
  - Username: `postgres`
  - Password: `1234`
  - Port: `5432`
  - Database: `fde_rag` (created automatically)

### 2. Python Dependencies
```bash
pip install psycopg2-binary sqlalchemy pgvector fastapi uvicorn
```

---

## Setup Instructions

### Step 1: Initialize PostgreSQL Database
```bash
cd backend
python setup_postgres.py
```

**Output:** Creates `fde_rag` database with `chunks` table

---

### Step 2: Start FastAPI Server
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 9999
```

Server runs at: `http://localhost:9999`

---

### Step 3: Load Demo Data
```bash
curl -X POST http://localhost:9999/load-demo \
  -H "Content-Type: application/json"
```

Or use Thunder Client: `POST /load-demo`

---

## API Endpoints

### 1. Health Check
```
GET http://localhost:9999/health
```
**Response:**
```json
{
  "status": "healthy",
  "service_initialized": true
}
```

### 2. Get Statistics
```
GET http://localhost:9999/stats
```
**Response:**
```json
{
  "qdrant_documents": 5,
  "bm25_documents": 5,
  "vector_dimension": 1536,
  "embedding_model": "text-embedding-3-small"
}
```

### 3. BM25 Keyword Search
```
POST http://localhost:9999/search
Content-Type: application/json

{
  "query": "kubernetes pod crash",
  "top_k": 3,
  "search_type": "bm25"
}
```

**Parameters:**
- `query`: Search string (required)
- `top_k`: Number of results (1-100, default 20)
- `search_type`: "bm25" | "vector" | "hybrid" (default "hybrid")
- `metadata_filter`: Optional filters (department, category, etc.)

**Response:**
```json
{
  "query": "kubernetes pod crash",
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "text": "...",
      "doc_id": "doc_001",
      "filename": "k8s.pdf",
      "section": "Pod Errors",
      "page": 1,
      "department": "Engineering",
      "category": "Kubernetes",
      "score": 0.72,
      "rank": 0
    }
  ],
  "search_type": "bm25",
  "num_results": 1,
  "latency_ms": {
    "bm25_search_ms": 2,
    "total_ms": 2
  }
}
```

### 4. Vector Semantic Search
```
POST http://localhost:9999/search

{
  "query": "pod startup issues",
  "top_k": 3,
  "search_type": "vector"
}
```
Returns results based on semantic similarity (not exact keyword match)

### 5. Hybrid Search (BM25 + Vector with RRF)
```
POST http://localhost:9999/search

{
  "query": "kubernetes error",
  "top_k": 3,
  "search_type": "hybrid"
}
```
Combines both keyword and semantic search, ranks by RRF fusion score

### 6. Index New Chunks
```
POST http://localhost:9999/index

{
  "chunks": [
    {
      "chunk_id": "chunk_123",
      "text": "Your document text here",
      "doc_id": "doc_1",
      "filename": "example.pdf",
      "section": "Introduction",
      "page": 1,
      "department": "Engineering",
      "category": "Bug Fix"
    }
  ]
}
```

### 7. Clear All Data
```
DELETE http://localhost:9999/index
```
⚠️ **Warning:** Deletes all indexed data

---

## Using Thunder Client

1. **Install:** VS Code Extensions → Thunder Client
2. **Create Request** → Click the ⚡ icon in left sidebar
3. **Example:**
   - Method: `POST`
   - URL: `http://localhost:9999/search`
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "query": "kubernetes pod",
     "top_k": 3,
     "search_type": "bm25"
   }
   ```
4. **Send** → View results in Response tab

---

## Architecture

```
FastAPI (main.py)
    ↓
HybridSearchService
    ├── PostgresVectorDB (vectors stored in PostgreSQL)
    │   └── EmbeddingsClient (OpenAI API with mock fallback)
    ├── BM25SearchEngine (keyword search)
    └── RRFFusion (combines results)
```

### Data Flow

**Indexing:**
1. Raw text chunks → OpenAI embeddings
2. Embeddings + metadata → PostgreSQL
3. Text → BM25 tokenization & indexing

**Searching:**
1. Query → Embed (OpenAI or mock)
2. Vector search in PostgreSQL
3. BM25 search on tokens
4. RRF fusion combines results
5. Metadata filters applied
6. Return top K results

---

## Key Features

✅ **Persistent Storage** - Data survives server restarts  
✅ **No Lock Issues** - PostgreSQL handles concurrency  
✅ **Hybrid Search** - BM25 + Vector search combined  
✅ **Mock Embeddings** - Works without OpenAI API  
✅ **Full Metadata** - Store and filter by department, category, etc.  
✅ **RRF Fusion** - Advanced ranking combining multiple signals  
✅ **REST API** - Simple JSON endpoints  

---

## Troubleshooting

### Server won't start
- Check PostgreSQL is running: `psql -U postgres -d fde_rag`
- Check port 9999 is free: `netstat -an | grep 9999`

### OpenAI API errors
- Falls back to mock embeddings automatically
- Check if OPENAI_API_KEY environment variable is set

### No results returned
- Ensure demo data loaded: `POST /load-demo`
- Check stats: `GET /stats` shows document count > 0
- Try different `top_k` value

### Database already has data
- Clear all: `DELETE /index`
- Or restart PostgreSQL to reset (in-development)

---

## Environment Variables (Optional)

```bash
# PostgreSQL Connection
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1234
POSTGRES_DB=fde_rag

# OpenAI API (optional, falls back to mock)
OPENAI_API_KEY=sk-...
```

Set in `.env` file or system environment before starting server.

---

## Next Steps

1. **Load your own data:** Use `/index` endpoint or modify `demo_chunks.py`
2. **Fine-tune search:** Adjust `top_k`, try different queries
3. **Production setup:** Install pgvector extension in PostgreSQL for optimized vector search
4. **Monitor:** Check `/stats` endpoint for index size and performance
5. **Deploy:** Use Docker/cloud hosting with persistent PostgreSQL

---

**Last Updated:** 2026-06-03  
**Version:** 1.0.0 - PostgreSQL + BM25 + RRF Fusion
