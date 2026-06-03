# Testing Guide - M3 Generation Module

## Quick Start: 3 Ways to Test

### 1️⃣ **Structure Test (No API Key Needed)** ✅ EASIEST

Test that all code compiles and prompts work:

```bash
cd "c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity"
python test_phase1.py
```

**Expected output:**
```
[OK] Prompts module loaded
[OK] Context-only rule
[OK] Fallback message
[OK] Source attribution
[OK] format_context works
[OK] build_prompt works
[OK] ChunkMetadata created
...
PHASE 1 STRUCTURE TESTS PASSED
```

✅ **This test works NOW** - no API key needed!

---

### 2️⃣ **Full Streaming Test (With Free API Key)** 🚀 RECOMMENDED

#### Step 1: Get Free API Key
1. Go to https://console.anthropic.com/
2. Sign up (takes 2 minutes)
3. Click "API Keys" on left sidebar
4. Click "Create Key"
5. Copy the key

#### Step 2: Set API Key & Run Test
```bash
cd "c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity"

# Windows Command Prompt:
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# OR Windows PowerShell:
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Run the test
python test_with_api.py
```

**Expected output:**
```
======================================================================
CLAUDE SONNET 4.0 - STREAMING TEST
======================================================================

API Key detected: sk-ant-XXXXX...
[OK] GenerationService initialized

Query: How do I restart a pod in Kubernetes?

----------------------------------------------------------------------
STREAMING RESPONSE:
----------------------------------------------------------------------

[SOURCES]
  - kubernetes-guide.pdf (Section: Troubleshooting)

To restart a pod in Kubernetes, you can use the kubectl rollout restart 
command. Here's how: kubectl rollout restart deployment/[deployment-name] 
-n [namespace]. This approach creates new pods and gracefully terminates 
old ones, ensuring your application experiences minimal downtime...

----------------------------------------------------------------------

STATISTICS:
  Events received: 25
  Tokens streamed: 145
  Input tokens: 2450
  Output tokens: 340
  Total tokens: 2790

======================================================================
SUCCESS: Claude Sonnet streaming works!
======================================================================
```

---

### 3️⃣ **HTTP Server Test (With API Key)** 🌐 ADVANCED

#### Step 1: Start Server
```bash
cd "c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity"

# Set API key
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Start FastAPI server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
Uvicorn running on http://0.0.0.0:8000
Press CTRL+C to quit
```

#### Step 2: Health Check (Open new terminal)
```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"ok","version":"0.1.0"}
```

#### Step 3: Test Generate Endpoint

**Create file** `request.json`:
```json
{
  "query": "How do I restart a pod?",
  "chunks": [
    {
      "text": "To restart a pod: kubectl rollout restart deployment/[name] -n [namespace]",
      "score": 0.95,
      "source": "kubernetes-guide.pdf",
      "chunk_id": "chunk-001",
      "metadata": {
        "section": "Troubleshooting",
        "page": 42,
        "doc_id": "doc-001",
        "source": "kubernetes-guide.pdf"
      }
    }
  ],
  "stream": true
}
```

**Test streaming endpoint:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d @request.json
```

**Expected response** (streaming events):
```
{"type":"metadata","sources":[{"doc":"kubernetes-guide.pdf","section":"Troubleshooting","chunk_id":"chunk-001"}]}
{"type":"token","content":"To"}
{"type":"token","content":" restart"}
...
{"type":"done","input_tokens":2450,"output_tokens":340}
```

---

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"
**Solution:**
```bash
# Windows Command Prompt:
set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Windows PowerShell:
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Verify it's set:
echo %ANTHROPIC_API_KEY%        # CMD
echo $env:ANTHROPIC_API_KEY     # PowerShell
```

### Issue: "TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'"
**Solution:** Already fixed in code. Just ensure you're using the latest code from the branch.

```bash
git pull origin feature/generation-guardrails
```

### Issue: "Cannot find module 'backend.app.generation'"
**Solution:** Make sure you're in the correct directory:
```bash
cd "c:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity"
python test_phase1.py
```

### Issue: Server won't start
**Solution:** Kill the process on port 8000:
```bash
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Then try again:
python -m uvicorn backend.main:app --reload
```

---

## What Each Test Validates

| Test | Checks | API Key? | Time |
|------|--------|----------|------|
| **test_phase1.py** | ✅ Prompts + models + formatting | No | 5s |
| **test_with_api.py** | ✅ Streaming + Claude API | Yes | 15s |
| **HTTP Server** | ✅ Full endpoint + SSE | Yes | 20s |

---

## Recommended Testing Flow

1. **Start here:**
   ```bash
   python test_phase1.py
   ```
   _Should pass instantly, no API key needed_

2. **If that works, get API key:**
   https://console.anthropic.com/

3. **Then run:**
   ```bash
   set ANTHROPIC_API_KEY=sk-ant-...
   python test_with_api.py
   ```
   _This tests real Claude Sonnet streaming_

4. **Finally, start server:**
   ```bash
   set ANTHROPIC_API_KEY=sk-ant-...
   python -m uvicorn backend.main:app --reload
   ```
   _Full HTTP endpoint testing_

---

## What's Being Tested

### test_phase1.py (No API)
- ✅ Grounding prompt prevents hallucination
- ✅ Pydantic models validate correctly
- ✅ Prompt formatting works
- ✅ Source extraction works

### test_with_api.py (With API)
- ✅ Claude Sonnet 4.0 connection
- ✅ Streaming SSE format
- ✅ Token counting (input + output)
- ✅ Source attribution in responses
- ✅ Hallucination prevention works

### HTTP Server (With API)
- ✅ FastAPI routing
- ✅ SSE streaming over HTTP
- ✅ Request validation
- ✅ Real-world integration

---

## Free API Tier

Anthropic gives you **$5 free credits** to test:
- Claude 3.5 Sonnet (latest, fastest)
- Claude 3 Opus (most capable)
- All the features you need for Phase 1

**No payment required** to get started.

---

## Next Steps After Testing

✅ **If test_phase1.py passes** → Code structure is good, ready for PR

✅ **If test_with_api.py passes** → Claude integration works, Phase 1 complete

✅ **If HTTP server works** → Ready for Phase 2 integration with M1, M2, M4, M5

---

**You're ready to test!** 🚀
