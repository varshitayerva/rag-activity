# Test It Yourself - M3 Phase 1

## Quick Start (5 minutes)

### Step 1: Open Terminal & Start Server
```bash
cd c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity
python -m uvicorn backend.main:app --reload
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

**Keep this terminal open!**

### Step 2: Open Another Terminal & Test Endpoints

#### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "provider": "huggingface"
}
```

#### Test 2: Config (See All Providers)
```bash
curl http://localhost:8000/api/config
```

This shows:
- All available LLM providers
- Setup requirements
- Costs
- Example usage

#### Test 3: Generate Response (Non-Streaming)
```bash
curl -X POST "http://localhost:8000/api/generate?provider=huggingface" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I restart a pod?",
    "chunks": [{
      "text": "Use kubectl rollout restart deployment/name",
      "score": 0.95,
      "source": "kubernetes-guide.pdf",
      "chunk_id": "chunk-001",
      "metadata": {
        "section": "Troubleshooting",
        "page": 5,
        "doc_id": "k8s-101",
        "source": "kubernetes-guide.pdf"
      }
    }],
    "stream": false
  }'
```

Expected: Full response in JSON format with:
- `response`: The generated answer
- `sources`: Where the information came from
- `input_tokens`: Tokens used for input
- `output_tokens`: Tokens generated

#### Test 4: Generate Response (STREAMING)
```bash
curl -X POST "http://localhost:8000/api/generate?provider=huggingface" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Kubernetes?",
    "chunks": [{
      "text": "Kubernetes is an open-source container orchestration platform.",
      "score": 0.98,
      "source": "k8s-basics.pdf",
      "chunk_id": "chunk-002",
      "metadata": {
        "section": "Introduction",
        "page": 1,
        "doc_id": "doc-002",
        "source": "k8s-basics.pdf"
      }
    }],
    "stream": true
  }'
```

Expected: Server-Sent Events streaming:
```
{"type": "metadata", "sources": [...]}
{"type": "token", "content": "Kubernetes"}
{"type": "token", "content": " is"}
...
{"type": "done", "input_tokens": 123, "output_tokens": 45}
```

---

## Using Python Client (Alternative)

### Option A: Simple HTTP Requests
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Generate response
response = requests.post(
    "http://localhost:8000/api/generate?provider=huggingface",
    json={
        "query": "How do I restart a pod?",
        "chunks": [{
            "text": "Use kubectl rollout restart deployment/name",
            "score": 0.95,
            "source": "kubernetes-guide.pdf",
            "chunk_id": "chunk-001",
            "metadata": {
                "section": "Troubleshooting",
                "page": 5,
                "doc_id": "k8s-101",
                "source": "kubernetes-guide.pdf"
            }
        }],
        "stream": False
    }
)
print(response.json())
```

### Option B: Streaming with Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/generate?provider=huggingface",
    json={
        "query": "What is Kubernetes?",
        "chunks": [{
            "text": "Kubernetes is an open-source container orchestration platform.",
            "score": 0.98,
            "source": "k8s-basics.pdf",
            "chunk_id": "chunk-002",
            "metadata": {
                "section": "Introduction",
                "page": 1,
                "doc_id": "doc-002",
                "source": "k8s-basics.pdf"
            }
        }],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line)
```

---

## Testing Different Providers

You can switch providers by changing the query parameter:

### Hugging Face (Default - Free Forever)
```bash
curl -X POST "http://localhost:8000/api/generate?provider=huggingface" ...
```

### Groq (Free Cloud API)
```bash
curl -X POST "http://localhost:8000/api/generate?provider=groq" ...
```
Requires: `GROQ_API_KEY` environment variable

### Anthropic Claude (Free $5 Credit)
```bash
curl -X POST "http://localhost:8000/api/generate?provider=anthropic" ...
```
Requires: `ANTHROPIC_API_KEY` environment variable

### Ollama (Local - Free)
```bash
curl -X POST "http://localhost:8000/api/generate?provider=ollama" ...
```
Requires: Ollama installed and running

---

## Understanding the Response

### Non-Streaming Response
```json
{
  "response": "To restart a pod...",           // The actual answer
  "sources": [                                  // Where info came from
    {
      "doc": "kubernetes-guide.pdf",
      "section": "Troubleshooting",
      "chunk_id": "chunk-001"
    }
  ],
  "input_tokens": 349,                          // Tokens for prompt
  "output_tokens": 165                          // Tokens generated
}
```

### Streaming Response (Server-Sent Events)
1. **metadata event** - Sources and document info
2. **token events** - Text generated token by token
3. **done event** - Final token counts

---

## Key Features to Verify

✓ **Hallucination Prevention**
  - Model only uses provided chunks
  - Cites sources for every claim
  - Falls back to "I don't have reliable information" if needed

✓ **Streaming Works**
  - Tokens arrive one at a time
  - Metadata comes first
  - Done event includes token counts

✓ **Source Attribution**
  - Document name shown
  - Section referenced
  - Chunk ID tracked

✓ **Token Counting**
  - input_tokens matches prompt size
  - output_tokens counts generated tokens
  - Useful for cost tracking

✓ **Multiple Providers**
  - Can switch providers via query parameter
  - Each has own setup (API keys)
  - Fallback to HF if others fail

---

## Troubleshooting

### "Connection refused"
- Make sure server is still running in first terminal
- Server must be running: `python -m uvicorn backend.main:app --reload`

### "HF_TOKEN not set"
- Token is in `.env` file
- Or set manually: `set HF_TOKEN=hf_your_token_here`
- Get token: https://huggingface.co/settings/tokens

### "Provider not found"
- Check `/api/config` to see available providers
- Make sure provider parameter matches exactly

### "Invalid request"
- Check JSON format is valid
- All required fields: query, chunks, stream
- Each chunk needs: text, score, source, chunk_id, metadata

---

## Next Steps After Testing

1. ✅ Verify health check works
2. ✅ Verify config endpoint shows all providers
3. ✅ Test non-streaming generation
4. ✅ Test streaming generation
5. ✅ Check source attribution
6. ✅ Verify token counts

**Once verified:**
- Create a Pull Request: `gh pr create ...`
- Merge to develop branch
- Proceed to Phase 2 implementation

---

## Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/` | GET | Service info |
| `/api/config` | GET | Available providers |
| `/api/generate` | POST | Generate response |

| Query Parameter | Values | Default |
|-----------------|--------|---------|
| `provider` | huggingface, groq, anthropic, ollama | huggingface |

---

**Have fun testing! 🚀**
