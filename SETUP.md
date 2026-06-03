# FDE RAG System - Setup Guide

Complete setup for real-time RAG with sentence-transformers embeddings (NO pgvector needed).

---

## **Phase 1: Environment Setup**

### **Step 1: Python Dependencies**

```bash
pip install -r requirements.txt
```

This installs:
- ✅ sentence-transformers (real embeddings)
- ✅ psycopg2-binary (PostgreSQL)
- ✅ FastAPI & Uvicorn (backend)
- ✅ All other dependencies

### **Step 2: Create .env File**

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=fde_rag

# LLM (choose one)
HF_TOKEN=your_hf_token_here
# OR
GROQ_API_KEY=your_groq_key_here

# Optional
REDIS_URL=redis://localhost:6379

# Frontend
VITE_API_URL=http://localhost:8000

# Environment
ENVIRONMENT=development
```

---

## **Phase 2: Database Setup**

### **Step 1: Create PostgreSQL Database**

```bash
# Connect to PostgreSQL
psql -U postgres
```

Then run:

```sql
-- Create database
CREATE DATABASE fde_rag;

-- Exit
\q
```

### **Step 2: Initialize Database Schema**

```bash
# Python setup script
python -c "
from backend.app.database.postgres import db_client
db_client.init_db()
"
```

This creates:
- `documents` table
- `chunks` table
- `metrics` table
- `search_queries` table
- All indexes

✅ Database ready!

---

## **Phase 3: Optional - Ingest Sample Data**

### **Option A: Ingest from Directory**

```python
from backend.app.ingestion.ingest import DocumentIngester

ingester = DocumentIngester()
result = ingester.ingest_directory("./sample_docs", extensions=['pdf', 'txt', 'md'])
print(result)
```

### **Option B: Ingest Single File**

```python
from backend.app.ingestion.ingest import ingest

result = ingest("./path/to/document.pdf")
print(result)
```

---

## **Phase 4: Start the System**

### **Terminal 1: Backend API**

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Response:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### **Terminal 2: Frontend (React)**

```bash
cd frontend
npm install
npm run dev
```

Response:
```
VITE v... ready in 123 ms
➜  Local:   http://localhost:5173/
```

### **Access**

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

---

## **Phase 5: Test the System**

### **Option A: API Documentation (Easiest)**

1. Go to: http://localhost:8000/docs
2. Click on `/api/search` endpoint
3. Try it out with sample query:
   ```json
   {
     "query": "your search query",
     "top_k": 5
   }
   ```

### **Option B: curl**

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your search query here",
    "top_k": 10
  }'
```

### **Option C: Python**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "query": "your search query here",
        "top_k": 10
    }
)

print(response.json())
```

---

## **System Architecture**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Embeddings** | sentence-transformers | Real, free embeddings |
| **Vector Search** | In-memory store | Fast similarity search |
| **Document Storage** | PostgreSQL | Document & chunk metadata |
| **API** | FastAPI | REST endpoints |
| **Frontend** | React + Vite | User interface |
| **LLM** | HuggingFace/Groq | Text generation |

---

## **API Endpoints**

### **Search**
- `POST /api/search` - Search documents

### **Documents**
- `GET /api/documents` - List all documents
- `GET /api/documents/{doc_id}/chunks` - Get chunks for document

### **Generation**
- `POST /api/generate` - Generate response with search context

### **Metrics**
- `GET /api/metrics` - Get system performance metrics

### **Health**
- `GET /health` - Health check
- `GET /` - Service info

---

## **Troubleshooting**

### **"psycopg2 connection refused"**
Make sure PostgreSQL is running:
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432
```

### **"No module named sentence_transformers"**
```bash
pip install sentence-transformers
```

### **"Database does not exist"**
Create it:
```bash
psql -U postgres -c "CREATE DATABASE fde_rag;"
```

### **"Embedding model not found"**
First run will auto-download (~150MB). Make sure you have internet connection.

### **"Port 8000 already in use"**
Use a different port:
```bash
python -m uvicorn backend.main:app --port 8001
```

---

## **Performance Metrics**

Expected performance:

| Operation | Time |
|-----------|------|
| Load embedding model | 30-60s |
| Create embeddings | 10-50ms per chunk |
| Vector search | 10-100ms |
| Full search pipeline | 100-500ms |

---

## **Production Deployment**

For production:

1. Use a managed PostgreSQL instance
2. Configure environment variables
3. Use a reverse proxy (nginx)
4. Add authentication
5. Deploy with Docker or systemd
6. Monitor with metrics endpoint

---

## **Next Steps**

1. ✅ Setup complete
2. Ingest your documents
3. Test search functionality
4. Integrate with frontend
5. Deploy to production

---

**You're all set!** 🚀

For detailed API docs, visit: http://localhost:8000/docs
