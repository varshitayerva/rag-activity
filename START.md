# Quick Start Guide

Get the RAG system running in 5 minutes!

---

## **Step 1: Install Dependencies (1 min)**

```bash
pip install -r requirements.txt
```

---

## **Step 2: Setup Environment (1 min)**

Copy and edit `.env`:

```bash
cp .env.example .env
```

Edit `.env` - add your API keys:

```env
HF_TOKEN=your_huggingface_token_here
# OR
GROQ_API_KEY=your_groq_key_here
```

(Optional - both free to get)

---

## **Step 3: Create Database (1 min)**

```bash
# Create database in PostgreSQL
psql -U postgres -c "CREATE DATABASE fde_rag;"

# Initialize schema
python init_db.py
```

---

## **Step 4: Ingest Sample Documents (1 min)**

```bash
python ingest_sample.py
```

Creates sample docs + embeddings automatically.

---

## **Step 5: Start Everything (1 min)**

### **Terminal 1: Backend**

```bash
python -m uvicorn backend.main:app --reload
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### **Terminal 2: Frontend**

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

## **Done! 🎉**

### **Test the System**

**Option 1: Swagger Docs (Easiest)**
- Go to: http://localhost:8000/docs
- Click `/api/search`
- Click "Try it out"
- Enter a query: `"What is Kubernetes?"`
- Click Execute

**Option 2: Frontend**
- Go to: http://localhost:5173
- Use the search interface

**Option 3: curl**
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Kubernetes?","top_k":5}'
```

---

## **Architecture**

```
┌─────────────┐
│   React     │  Frontend UI
│  (5173)     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│    FastAPI      │  REST API (8000)
│   (Backend)     │
└──────┬──────────┘
       │
       ├─────────────────────────────┐
       │                             │
       ▼                             ▼
┌────────────────┐         ┌─────────────────┐
│  Vector Store  │         │   PostgreSQL    │
│  (in-memory)   │         │   (metadata)    │
└────────────────┘         └─────────────────┘
       ▲
       │
┌──────────────────────┐
│sentence-transformers │ (embeddings)
└──────────────────────┘
```

---

## **What's Included**

✅ **Real Embeddings**: sentence-transformers (free, 150MB auto-download)
✅ **Fast Search**: In-memory vector store (sub-100ms)
✅ **PostgreSQL**: Document & chunk storage (no pgvector needed!)
✅ **React Frontend**: Modern UI with Vite
✅ **Multiple LLMs**: HuggingFace, Groq, Anthropic, Ollama
✅ **Metrics**: Real-time performance tracking
✅ **Caching**: Redis optional, in-memory default

---

## **Sample Queries to Try**

```
- "What is Kubernetes?"
- "How do I restart a pod?"
- "What is Docker?"
- "How to create containers?"
- "Python best practices"
```

---

## **Troubleshooting**

### **"Cannot connect to PostgreSQL"**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432
```

### **"Port 8000 already in use"**
```bash
# Use different port
python -m uvicorn backend.main:app --port 8001
```

### **"Module not found"**
```bash
pip install -r requirements.txt
```

### **"Download too slow"**
Embedding model downloads on first use (~150MB).
Uses cached version after that.

---

## **Next Steps**

1. ✅ System running
2. Test with sample docs
3. Ingest your own documents
4. Build integrations
5. Deploy to production

---

## **Production Deployment**

See [SETUP.md](SETUP.md) for production instructions.

---

**Questions?** Check [SETUP.md](SETUP.md) for detailed docs.

**API Docs**: http://localhost:8000/docs
