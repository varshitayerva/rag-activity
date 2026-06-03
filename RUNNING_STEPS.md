# How to Run the RAG Application

## PREREQUISITES
- Python 3.8+
- Node.js 16+
- npm or yarn
- Git

---

## STEP 1: Navigate to Project

```bash
cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity
```

---

## STEP 2: Setup Environment Variables

### 2A. Backend Environment (.env)

```bash
cp .env.example .env
```

Edit `.env` and set at least one LLM provider:

```
# Hugging Face (FREE - Recommended)
HF_TOKEN=your_hugging_face_token_here

# Or use other providers:
GROQ_API_KEY=your_groq_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional - Database & Cache
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://postgres:password@localhost/rag_db
QDRANT_URL=http://localhost:6333

# Provider to use
GENERATION_PROVIDER=huggingface
```

Get free tokens:
- **Hugging Face**: https://huggingface.co/settings/tokens (FREE forever)
- **Groq**: https://console.groq.com (FREE forever)
- **Anthropic**: https://console.anthropic.com ($5 free credit)

### 2B. Frontend Environment

```bash
cp frontend/.env.example frontend/.env
```

Edit `frontend/.env`:

```
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Technical Support Copilot
VITE_ENABLE_METRICS=true
```

---

## STEP 3: Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

This installs:
- FastAPI, Uvicorn (web framework)
- OpenAI, Anthropic, Groq (LLM providers)
- Redis, Qdrant (databases)
- Pydantic, SQLAlchemy (data validation)
- And more...

---

## STEP 4: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

Or with yarn:
```bash
cd frontend
yarn install
cd ..
```

---

## STEP 5: Start Backend (Terminal 1)

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Backend is now available at: `http://localhost:8000`

API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## STEP 6: Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Expected output:
```
Local:   http://localhost:5173/
```

Frontend is now available at: `http://localhost:5173`

---

## STEP 7: Verify Everything Works

### 7A. Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"ok","version":"0.1.0","provider":"huggingface"}
```

### 7B. Check API Docs

Open browser: `http://localhost:8000/docs`

You should see all endpoints:
- POST /api/generate
- POST /api/search
- GET /api/metrics
- POST /api/ingest
- GET /api/config
- GET /health

### 7C. Open Frontend

Open browser: `http://localhost:5173`

You should see:
- Header: "Technical Support Copilot"
- Navigation tabs: Chat, Upload Docs, Architecture
- Main interface with panels

---

## STEP 8: Test the Complete Workflow (Optional)

### 8A. Test Generation Endpoint

```bash
curl -X POST "http://localhost:8000/api/generate?provider=huggingface" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Kubernetes?",
    "chunks": [{
      "text": "Kubernetes is an open-source container orchestration platform",
      "score": 0.98,
      "source": "k8s-intro.pdf",
      "chunk_id": "chunk-001",
      "metadata": {
        "section": "Introduction",
        "page": 1,
        "doc_id": "doc-001",
        "source": "k8s-intro.pdf"
      }
    }],
    "stream": false
  }'
```

Expected: JSON response with generation, sources, and confidence score

### 8B. Test Search Endpoint

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to restart a pod?",
    "top_k": 5,
    "filter": {}
  }'
```

Expected: Mock search results with latency breakdown

### 8C. Test Metrics Endpoint

```bash
curl http://localhost:8000/api/metrics
```

Expected: Performance metrics with cache hit rate, latency, etc.

---

## PORTS & SERVICES

| Service | Port | URL |
|---------|------|-----|
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| Frontend (Vite) | 5173 | http://localhost:5173 |
| Frontend (alt) | 3000 | http://localhost:3000 |

---

## Running Tests

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_generation.py -v
```

Run with coverage report:
```bash
python -m pytest tests/ --cov=backend/app
```

---

## Architecture Layers

The application has 5 integrated layers:

**Layer 1: Document Ingestion** (Member 1)
- Parses PDF, Markdown files
- Creates semantic or fixed-size chunks
- Extracts metadata automatically

**Layer 2: Hybrid Search** (Member 2)
- BM25 full-text search
- Vector similarity (embeddings)
- RRF fusion ranking
- Qdrant vector database

**Layer 3: LLM Generation** (Member 3)
- Multi-provider support (HF, Groq, Anthropic, Ollama)
- Streaming SSE responses
- 5-metric confidence scoring
- Hallucination prevention

**Layer 4: Caching & Performance** (Member 4)
- Redis 3-layer caching
- Context compression
- Latency analysis
- Metrics collection

**Layer 5: Frontend UI** (Member 5)
- React SPA with Vite
- Real-time chat interface
- Document upload
- Performance dashboard

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
**Fix:**
```bash
pip install -r backend/requirements.txt
```

### Issue: "Port 8000 already in use"
**Fix:**
```bash
python -m uvicorn backend.main:app --port 8001
```

### Issue: "HF_TOKEN not set"
**Fix (Linux/Mac):**
```bash
export HF_TOKEN=your_token_here
```

**Fix (Windows PowerShell):**
```powershell
$env:HF_TOKEN="your_token_here"
```

### Issue: Frontend can't reach backend
**Fix:** Check `frontend/.env` has correct `VITE_API_URL=http://localhost:8000`

### Issue: "npm: command not found"
**Fix:** Install Node.js from https://nodejs.org

### Issue: "Module not found" in frontend
**Fix:**
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

---

## Quick Start (Copy-Paste)

### Terminal 1 - Backend
```bash
cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

### Terminal 2 - Frontend
```bash
cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity\frontend
npm install
npm run dev
```

### Terminal 3 - Test
```bash
curl http://localhost:8000/health
```

Then open:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## Environment Variables Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| HF_TOKEN | Yes* | - | Hugging Face API token |
| GROQ_API_KEY | Yes* | - | Groq API key |
| ANTHROPIC_API_KEY | Yes* | - | Anthropic API key |
| GENERATION_PROVIDER | No | huggingface | LLM provider to use |
| REDIS_URL | No | redis://localhost:6379 | Redis connection |
| DATABASE_URL | No | postgresql://... | PostgreSQL connection |
| QDRANT_URL | No | http://localhost:6333 | Qdrant vector DB |
| VITE_API_URL | No | http://localhost:8000 | Frontend backend URL |

*At least one LLM provider API key is required

---

## What's Running

After everything is started:

1. **Backend API** (Python/FastAPI) - Port 8000
   - Handles document ingestion
   - Performs hybrid search
   - Generates responses with LLM
   - Manages caching
   - Provides metrics

2. **Frontend** (React/Vite) - Port 5173
   - User interface for chat
   - Document upload
   - Real-time streaming responses
   - Performance metrics visualization

3. **Documentation** - Port 8000/docs
   - Interactive API documentation
   - Test endpoints directly

---

## Ready to Go!

Your RAG application is now running! Start chatting, uploading documents, and exploring the hybrid search capabilities.

All 5 members' work is integrated:
✓ Ingestion (Member 1)
✓ Hybrid Search (Member 2)
✓ LLM Generation (Member 3)
✓ Caching & Performance (Member 4)
✓ Frontend UI (Member 5)

Enjoy! 🚀
