# How to Run the RAG System

Complete working system ready to go!

---

## **What You Have**

✅ **Real Embeddings**: sentence-transformers (free, auto-downloads model)
✅ **Fast Search**: In-memory vector store (sub-100ms queries)
✅ **PostgreSQL**: Document/chunk storage (no pgvector!)
✅ **FastAPI Backend**: REST API with Swagger docs
✅ **React Frontend**: User interface with Vite
✅ **Multi-LLM Support**: HuggingFace, Groq, Anthropic, Ollama

---

## **Quick Start (5 Minutes)**

### **Step 1: Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Step 2: Create .env**

```bash
cp .env.example .env
```

Edit `.env` and add your LLM keys (both free):

```env
# HuggingFace (free)
HF_TOKEN=your_hf_token_here

# OR Groq (free)
GROQ_API_KEY=your_groq_key_here
```

Optional: Get free tokens from:
- HuggingFace: https://huggingface.co/settings/tokens
- Groq: https://console.groq.com/

### **Step 3: Initialize Database**

```bash
python init_db.py
```

Creates tables:
- `documents` - document metadata
- `chunks` - text chunks
- `metrics` - performance metrics
- `search_queries` - search analytics

### **Step 4: Ingest Sample Data**

```bash
python ingest_sample.py
```

This creates 3 sample documents automatically:
1. `kubernetes_basics.txt` - Kubernetes guide
2. `docker_guide.txt` - Docker commands
3. `python_practices.txt` - Python best practices

Each document is chunked and embedded.

### **Step 5: Start Backend**

**Terminal 1:**

```bash
python -m uvicorn backend.main:app --reload
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### **Step 6: Start Frontend**

**Terminal 2:**

```bash
cd frontend
npm install
npm run dev
```

Wait for:
```
➜  Local:   http://localhost:5173/
```

---

## **Test It**

### **Option 1: API Swagger (Easiest)**

1. Go to: http://localhost:8000/docs
2. Find `/api/search` endpoint
3. Click "Try it out"
4. Enter query: `"What is Kubernetes?"`
5. Click Execute

Response:
```json
{
  "query": "What is Kubernetes?",
  "results": [
    {
      "score": 0.95,
      "text": "Kubernetes (K8s) is an open-source orchestration...",
      "chunk_id": 0,
      "doc_id": 1,
      "document_name": "kubernetes_basics.txt"
    }
  ],
  "latency_ms": 125,
  "result_count": 1
}
```

### **Option 2: Frontend UI**

Go to: http://localhost:5173

Use the search interface to query documents.

### **Option 3: curl**

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Kubernetes?","top_k":5}'
```

### **Option 4: Python**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "query": "What is Kubernetes?",
        "top_k": 10
    }
)

print(response.json())
```

---

## **Available Endpoints**

### **Search**
```
POST /api/search
{
  "query": "your question",
  "top_k": 10
}
```

### **Documents**
```
GET /api/documents
GET /api/documents/{doc_id}/chunks
```

### **Generation** (with search context)
```
POST /api/generate?provider=huggingface
{
  "query": "your question",
  "context": "search results..."
}
```

### **Metrics**
```
GET /api/metrics
```

### **Health**
```
GET /health
GET /
```

---

## **Architecture**

```
┌──────────────────────────────────────┐
│        User Browser                  │
│    http://localhost:5173             │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│      React + Vite Frontend           │
│       Search UI, Results             │
└──────────────────┬───────────────────┘
                   │
                   ▼ HTTP requests
┌──────────────────────────────────────┐
│       FastAPI Backend                │
│    http://localhost:8000             │
│    - /api/search                     │
│    - /api/generate                   │
│    - /api/metrics                    │
└────┬──────────────────────┬──────────┘
     │                      │
     ▼                      ▼
┌──────────────────┐  ┌──────────────────┐
│ Vector Store     │  │   PostgreSQL     │
│  (in-memory)     │  │  Database        │
│                  │  │  - documents     │
│ - embeddings     │  │  - chunks        │
│ - similarity     │  │  - metrics       │
│   search         │  │  - queries       │
└────┬─────────────┘  └──────────────────┘
     │
     ▼
┌──────────────────────┐
│sentence-transformers │
│  (embeddings)        │
│  all-MiniLM-L6-v2    │
└──────────────────────┘
```

---

## **Ingesting Your Own Documents**

### **From Python**

```python
from backend.app.ingestion.ingest import ingest

# Ingest a single file
result = ingest("path/to/document.pdf")
print(result)

# Or ingest a directory
from backend.app.ingestion.ingest import DocumentIngester
ingester = DocumentIngester()
result = ingester.ingest_directory("path/to/documents")
print(result)
```

### **From Command Line**

Create `ingest_my_docs.py`:

```python
from backend.app.ingestion.ingest import DocumentIngester

ingester = DocumentIngester()
result = ingester.ingest_directory("./my_documents")
print(result)
```

Then run:
```bash
python ingest_my_docs.py
```

---

## **Sample Queries to Try**

Based on provided sample documents:

1. "What is Kubernetes?"
2. "How do I restart a pod?"
3. "What is Docker?"
4. "How to create a Docker container?"
5. "Docker networking"
6. "Python best practices"
7. "How to write docstrings?"
8. "Virtual environments"
9. "PEP 8"
10. "Exception handling"

---

## **Troubleshooting**

### **"Cannot connect to PostgreSQL"**

```bash
# Check if running
pg_isready -h localhost -p 5432

# Or in Windows Services:
# services.msc → PostgreSQL → Right-click → Start
```

### **"Port 8000 already in use"**

```bash
# Use different port
python -m uvicorn backend.main:app --port 8001
```

### **"Module not found"**

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### **"Database does not exist"**

```bash
# Create it
psql -U postgres -c "CREATE DATABASE fde_rag;"

# Then init
python init_db.py
```

### **"HuggingFace 401 error"**

First run downloads model from HuggingFace.
If you have authentication issues:

1. Get token: https://huggingface.co/settings/tokens
2. Set in .env: `HF_TOKEN=your_token`
3. Or set environment: `set HF_TOKEN=your_token`

### **"Model download too slow"**

Model (~150MB) downloads on first use.
Subsequent searches use cached model.

### **"Embedding timeout"**

First embedding takes 30-60 seconds (model loading).
Subsequent embeddings are much faster.

---

## **Next Steps**

1. ✅ System running
2. Test with samples
3. Ingest your documents
4. Test search functionality
5. Build frontend features
6. Deploy to production

---

## **Production Deployment**

For production:

1. Set `ENVIRONMENT=production` in .env
2. Use PostgreSQL managed instance (RDS, Azure Database, etc.)
3. Configure environment variables securely
4. Use reverse proxy (nginx)
5. Add authentication
6. Deploy with Docker or systemd
7. Monitor metrics endpoint

---

## **Database Management**

### **Connect to PostgreSQL**

```bash
psql -U postgres -d fde_rag
```

### **View Tables**

```sql
\dt
```

### **Check Documents**

```sql
SELECT * FROM documents;
```

### **Check Chunks**

```sql
SELECT * FROM chunks LIMIT 10;
```

### **Check Metrics**

```sql
SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10;
```

---

## **Performance**

Typical performance metrics:

| Operation | Time |
|-----------|------|
| Load embedding model | 30-60s (first run) |
| Create 1 embedding | 10-50ms |
| Vector search (1000 vectors) | 10-50ms |
| Full search pipeline | 100-500ms |
| API response | <1s |

---

## **API Documentation**

Full Swagger UI available at:

```
http://localhost:8000/docs
```

Interactive docs with:
- All endpoints
- Request/response schemas
- Try it out button
- Example payloads

---

## **System Info**

### **Backend**
- Framework: FastAPI
- Server: Uvicorn
- Port: 8000
- Host: 0.0.0.0

### **Frontend**
- Framework: React
- Build tool: Vite
- Port: 5173
- Host: localhost

### **Database**
- Engine: PostgreSQL 16
- Host: localhost
- Port: 5432
- Database: fde_rag

### **Search**
- Embeddings: sentence-transformers
- Model: all-MiniLM-L6-v2 (22MB)
- Vector storage: In-memory
- Search type: Cosine similarity

---

## **Support**

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Root Info: http://localhost:8000/

---

**You're all set!** 🚀

The system is completely functional and ready to use.
