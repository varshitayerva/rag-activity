# Execute RAG System NOW

Your system is **FULLY CONFIGURED** and ready to run!

---

## ✅ **Configuration Done**

Your `.env` file now has:

```env
HF_TOKEN=hf_*** (your HuggingFace token)
GROQ_API_KEY=gsk_*** (your Groq API key)
GENERATION_PROVIDER=groq
```

✅ Both APIs are configured
✅ HuggingFace embeddings available
✅ Groq LLM ready

Note: Your actual API keys are stored in `.env` (not tracked in git for security)

---

## 🚀 **Run These 6 Commands**

### **Command 1: Initialize Database**

```bash
python init_db.py
```

Expected output:
```
[1/3] Checking PostgreSQL connection...
✅ Connected to PostgreSQL
[2/3] Creating database schema...
✅ Database initialized successfully
[3/3] Verifying database schema...
   ✅ documents: 0 rows
   ✅ chunks: 0 rows
   ✅ metrics: 0 rows
   ✅ search_queries: 0 rows
```

---

### **Command 2: Ingest Sample Documents**

```bash
python ingest_sample.py
```

Expected output:
```
Loading embedding model: all-MiniLM-L6-v2...
Model loaded. Embedding dimension: 384

[1/3] Creating sample documents...
Created sample documents in sample_docs/

[2/3] Initializing ingester...
Ingester ready

[3/3] Ingesting documents...
   Ingestion complete for kubernetes_basics.txt
   Ingestion complete for docker_guide.txt
   Ingestion complete for python_practices.txt

Ingestion Results
Total files: 3
Successful: 3
```

---

### **Command 3: Start Backend (Terminal 1)**

Open a **new terminal** and run:

```bash
python -m uvicorn backend.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Keep this terminal open.

---

### **Command 4: Start Frontend (Terminal 2)**

Open a **new terminal** and run:

```bash
cd frontend
npm install
npm run dev
```

Expected output:
```
VITE v... ready in 123 ms
➜  Local:   http://localhost:5173/
```

Keep this terminal open.

---

### **Command 5: Test the API (Terminal 3)**

Open a **new terminal** and run:

```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Kubernetes?","top_k":5}'
```

Expected response:
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
  "result_count": 1,
  "search_type": "vector-semantic"
}
```

---

### **Command 6: Open in Browser**

You have two options:

**Option A: Swagger UI (API Testing)**
```
http://localhost:8000/docs
```
- Click on `/api/search`
- Click "Try it out"
- Enter query: `"What is Kubernetes?"`
- Click Execute

**Option B: Frontend UI**
```
http://localhost:5173
```
- Use the search interface
- Type your query
- See results displayed

---

## 📊 **What Will Happen**

### **Step 1: Database Initialization**
- Creates 4 tables: documents, chunks, metrics, search_queries
- Time: ~2 seconds
- Status: Should show all tables created successfully

### **Step 2: Sample Document Ingestion**
- Creates 3 sample documents (Kubernetes, Docker, Python)
- Splits each into chunks
- Generates embeddings using sentence-transformers
- Stores in vector store
- Time: ~1-2 minutes
- Status: Should show 3 successful ingestions

### **Step 3: Backend Startup**
- Loads FastAPI application
- Initializes all endpoints
- Ready for API requests
- Time: ~5 seconds
- Status: "Uvicorn running on http://0.0.0.0:8000"

### **Step 4: Frontend Startup**
- Builds React + Vite application
- Starts development server
- Time: ~5 seconds
- Status: "Local: http://localhost:5173/"

### **Step 5: API Test**
- Sends search query to backend
- Loads embedding model (30-60s first time, then cached)
- Creates query embedding
- Searches in vector store
- Returns results
- Time: 100-500ms (after model loads)

### **Step 6: Browser Test**
- Frontend makes API calls
- Displays search results
- Shows latency metrics
- Interactive search working

---

## ✨ **Key Timings**

```
Database init:          2 seconds
Ingest 3 docs:          1-2 minutes
Backend startup:        5 seconds
Frontend startup:       5 seconds
First search (init):    30-60 seconds (model download)
Subsequent searches:    100-500ms
Frontend response:      <1 second
```

---

## 🔍 **Sample Queries to Try**

After everything is running, try these queries:

1. `"What is Kubernetes?"` - From kubernetes_basics.txt
2. `"How do I restart a pod?"` - From kubernetes_basics.txt
3. `"What is Docker?"` - From docker_guide.txt
4. `"Docker networking"` - From docker_guide.txt
5. `"Python best practices"` - From python_practices.txt
6. `"Virtual environments"` - From python_practices.txt
7. `"How to write docstrings?"` - From python_practices.txt

---

## 🛠️ **Troubleshooting While Running**

### **"Cannot connect to PostgreSQL"**
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# If not, start it:
# Windows: services.msc -> PostgreSQL -> Right-click -> Start
```

### **"Port 8000 already in use"**
```bash
# Use different port
python -m uvicorn backend.main:app --port 8001
```

### **"Port 5173 already in use"**
```bash
# Vite will auto-use next available port, check terminal output
```

### **"Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt
cd frontend && npm install
```

### **"First search is slow"**
This is expected! The embedding model is loading for the first time (~30-60s).
Subsequent searches are much faster (100-500ms).

### **"HuggingFace authentication error"**
Your token is configured. If you still see errors, try:
```bash
# Set token as environment variable
set HF_TOKEN=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
```

---

## 📋 **Complete Terminal Setup**

### **Terminal 1: Database Setup (one-time)**
```bash
cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity
python init_db.py
python ingest_sample.py
# Then close this terminal or run Command 3 here
```

### **Terminal 2: Backend**
```bash
cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity
python -m uvicorn backend.main:app --reload
# KEEP RUNNING
```

### **Terminal 3: Frontend**
```bash
cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity\frontend
npm run dev
# KEEP RUNNING
```

### **Terminal 4: Testing (optional)**
```bash
# Use for curl commands or other testing
# Can be closed when done testing
```

### **Browser Windows**
```
Tab 1: http://localhost:8000/docs (Swagger UI)
Tab 2: http://localhost:5173 (Frontend)
```

---

## ✅ **Success Checklist**

After running all commands, you should have:

- [ ] Database initialized successfully
- [ ] 3 sample documents ingested
- [ ] Backend running (terminal shows "Uvicorn running")
- [ ] Frontend running (terminal shows "Local: http://localhost:5173")
- [ ] Swagger UI accessible at http://localhost:8000/docs
- [ ] Frontend accessible at http://localhost:5173
- [ ] API search returns results in <1 second
- [ ] Sample queries return relevant results

---

## 🎯 **You're All Set!**

Everything is configured and ready to run.

Just execute the 6 commands and enjoy your working RAG system! 🚀

---

## 📞 **Need Help?**

- **Setup help**: See SETUP.md
- **Running help**: See RUN.md
- **Quick start**: See START.md
- **API docs**: http://localhost:8000/docs

---

**Execute now!** All commands are ready to go! 🎉
