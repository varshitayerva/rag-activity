# Quick Start - Production Ready

## 🚀 **Option 1: Use Groq (Recommended - Cloud, Free)**

### Setup (2 minutes)

1. **Get Free API Key**
   ```
   https://console.groq.com/
   ```
   - Sign up (free, takes 2 minutes)
   - Create API key (get `gsk_...`)

2. **Set Environment Variable**
   ```bash
   # Windows Command Prompt:
   set GROQ_API_KEY=gsk_your-key-here
   
   # Windows PowerShell:
   $env:GROQ_API_KEY="gsk_your-key-here"
   ```

3. **Install Dependencies**
   ```bash
   cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity
   pip install -q -r backend/requirements.txt
   ```

4. **Start Server**
   ```bash
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

   You should see:
   ```
   Uvicorn running on http://0.0.0.0:8000
   ```

5. **Test It** (in new terminal)
   ```bash
   curl http://localhost:8000/
   ```

   Response:
   ```json
   {
     "service": "Technical Support Copilot RAG",
     "provider": "groq",
     "endpoints": {...}
   }
   ```

---

## **Option 2: Use Anthropic Claude (If you prefer)**

### Setup (2 minutes)

1. **Get Free API Key**
   ```
   https://console.anthropic.com/
   ```
   - Sign up (free)
   - Create API key (get `sk-ant-...`)

2. **Set Environment Variable**
   ```bash
   set ANTHROPIC_API_KEY=sk-ant-your-key-here
   set GENERATION_PROVIDER=anthropic
   ```

3. **Start Server**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

---

## **Option 3: Use Ollama (Local, No Internet)**

### Setup (10 minutes)

1. **Download Ollama**
   ```
   https://ollama.ai/
   ```

2. **Install & Download Model**
   ```bash
   ollama pull mistral
   ```

3. **Start Ollama** (Terminal 1)
   ```bash
   ollama serve
   ```

4. **Start RAG Server** (Terminal 2)
   ```bash
   set GENERATION_PROVIDER=ollama
   python -m uvicorn backend.main:app --reload
   ```

---

## **How to Use the API**

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Get Configuration
```bash
curl http://localhost:8000/api/config
```

Shows all available providers and how to set them up.

### 3. Generate Response (Non-Streaming)

Create `request.json`:
```json
{
  "query": "How do I restart a pod?",
  "chunks": [{
    "text": "To restart: kubectl rollout restart deployment/[name]",
    "score": 0.95,
    "source": "kubernetes-guide.pdf",
    "chunk_id": "chunk-001",
    "metadata": {
      "section": "Troubleshooting",
      "page": 42,
      "doc_id": "doc-001",
      "source": "kubernetes-guide.pdf"
    }
  }],
  "stream": false
}
```

Send request:
```bash
curl -X POST http://localhost:8000/api/generate ^
  -H "Content-Type: application/json" ^
  -d @request.json
```

Response:
```json
{
  "response": "To restart a pod in Kubernetes...",
  "sources": [{"doc": "kubernetes-guide.pdf", "section": "Troubleshooting"}],
  "input_tokens": 2450,
  "output_tokens": 340
}
```

### 4. Generate Response (Streaming)

Same request, but add `?provider=groq` to URL:

```bash
curl -X POST "http://localhost:8000/api/generate?provider=groq" ^
  -H "Content-Type: application/json" ^
  -d @request.json
```

Response (Server-Sent Events):
```
data: {"type":"metadata","sources":[{"doc":"kubernetes-guide.pdf","section":"Troubleshooting"}]}
data: {"type":"token","content":"To"}
data: {"type":"token","content":" restart"}
...
data: {"type":"done","input_tokens":2450,"output_tokens":340}
```

---

## **Choose Provider at Runtime**

Change provider without restarting:

```bash
# Use Groq
curl -X POST "http://localhost:8000/api/generate?provider=groq" ...

# Use Anthropic
curl -X POST "http://localhost:8000/api/generate?provider=anthropic" ...

# Use Ollama
curl -X POST "http://localhost:8000/api/generate?provider=ollama" ...
```

---

## **Environment Variables**

### Default Provider
```bash
set GENERATION_PROVIDER=groq  # or anthropic, ollama
```

### API Keys
```bash
# Groq (free cloud)
set GROQ_API_KEY=gsk_...

# Anthropic (cloud)
set ANTHROPIC_API_KEY=sk-ant-...

# Ollama (local)
set OLLAMA_BASE_URL=http://localhost:11434
```

---

## **Comparison**

| Feature | Groq | Anthropic | Ollama |
|---------|------|-----------|--------|
| Cost | Free | Free tier | Free (local) |
| Setup | 2 min | 2 min | 10 min |
| Speed | Very Fast | Fast | Medium |
| Internet | Required | Required | No |
| Download Models | No | No | Yes |
| API Key | Yes | Yes | No |

---

## **Recommended: START WITH GROQ**

**Groq is:**
- ✅ Completely free
- ✅ Super fast (50+ tokens/sec)
- ✅ No model download
- ✅ 2 minute setup
- ✅ Production ready
- ✅ No payment ever required

Get your free key: https://console.groq.com/

---

## **Docker (Optional)**

If you want to run in Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -q -r requirements.txt

COPY backend/ .

ENV GENERATION_PROVIDER=groq
# Or set via: docker run -e GROQ_API_KEY=...

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build & run:
```bash
docker build -t rag .
docker run -e GROQ_API_KEY=gsk_... -p 8000:8000 rag
```

---

## **Troubleshooting**

### "GROQ_API_KEY not set"
```bash
set GROQ_API_KEY=gsk_...
# Verify:
echo %GROQ_API_KEY%
```

### "Connection refused"
Make sure server is running:
```bash
python -m uvicorn backend.main:app --reload
```

### "Module not found"
Install dependencies:
```bash
pip install -q -r backend/requirements.txt
```

### "Provider not available"
Check `/api/config` endpoint to see available providers and what's needed.

---

**You're ready! Pick your provider and start testing.** 🎉
