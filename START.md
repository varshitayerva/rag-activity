# Quick Start Guide

## 1. Add Your Groq API Key

Edit `backend/.env`:

```env
GROQ_API_KEY=gsk_YOUR_ACTUAL_KEY_HERE
```

Get your key from: https://console.groq.com/keys

## 2. Start Backend

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8081
```

## 3. Start Frontend (New Terminal)

```bash
cd frontend
npm run dev
```

## 4. Open Browser

Go to: `http://localhost:3000`

## 5. Use It

1. Upload a PDF document
2. Ask a question about the document
3. Get response from Groq's Mixtral model in real-time

---

## System

- **LLM**: Groq API (Mixtral-8x7b-32768)
- **Embeddings**: HF Inference API (sentence-transformers)
- **Vector DB**: PostgreSQL + pgvector
- **Search**: Hybrid (vector + BM25)
- **Frontend**: React + Vite with streaming chat

Done!
