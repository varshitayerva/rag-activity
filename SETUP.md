# Setup Guide - Technical Support Copilot

## Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/varshitayerva/rag-activity.git
cd rag-activity
```

### 2. Configure Environment Variables

Copy the example files to create your local `.env` files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Then edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### 3. Start Docker Services

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** (port 5432) - Document metadata
- **Redis** (port 6379) - Caching layer
- **Qdrant** (port 6333) - Vector database
- **FastAPI Backend** (port 8000) - /api endpoints
- **React Frontend** (port 3000) - Web UI

Verify all services:
```bash
docker-compose ps
docker-compose logs -f
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Environment Variables

### Root Level (.env)
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag_db
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/rag_db
REDIS_URL=redis://redis:6379
QDRANT_URL=http://qdrant:6333
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
VITE_API_URL=http://localhost:8000
ENVIRONMENT=development
```

### Backend (.env)
Backend-specific settings for FastAPI:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `QDRANT_URL` - Qdrant connection
- `OPENAI_API_KEY` - OpenAI embeddings
- `ANTHROPIC_API_KEY` - Claude API
- `ENVIRONMENT` - development/production
- `DEBUG` - Enable debug logging

### Frontend (.env)
Frontend-specific settings for React:
- `VITE_API_URL` - Backend API URL
- `VITE_APP_NAME` - Application name
- `VITE_ENABLE_METRICS` - Enable metrics display
- `VITE_METRICS_REFRESH_RATE` - Metrics update interval (ms)
- `VITE_STREAMING_ENABLED` - Enable streaming responses

## Local Development (Without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Make sure Redis, PostgreSQL, Qdrant are running
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## File Structure

```
rag-activity/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx
│   │   │   ├── UploadPanel.jsx
│   │   │   ├── FilterBar.jsx
│   │   │   ├── SourceCard.jsx
│   │   │   ├── MetricsBar.jsx
│   │   │   └── ArchitectureDiagram.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── app/
│       ├── ingestion/
│       ├── search/
│       ├── generation/
│       └── cache/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── SETUP.md
```

## API Endpoints (Phase 2)

- `POST /api/ingest` - Upload and chunk documents (M1)
- `POST /api/search` - Hybrid search with filters (M2)
- `POST /api/generate` - Stream responses with SSE (M3)
- `GET /api/metrics` - Performance metrics (M4)
- `GET /health` - Health check

## Troubleshooting

### Docker Services Not Starting
```bash
# Check logs
docker-compose logs [service-name]

# Rebuild images
docker-compose build --no-cache

# Reset everything
docker-compose down -v
docker-compose up -d
```

### Port Already in Use
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # backend
  - "3001:3000"  # frontend
```

### API Keys Missing
Make sure `.env` includes:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Team Assignments (Phase 1-2)

- **M1 (Ingestion)**: Implement `/api/ingest` - PDF/Markdown parsing + semantic chunking
- **M2 (Search)**: Implement `/api/search` - Hybrid search (vector + BM25) with RRF
- **M3 (Generation)**: Implement `/api/generate` - Claude integration with streaming SSE
- **M4 (Caching)**: Implement `/api/metrics` - Redis caching + performance monitoring
- **M5 (Frontend)**: Wire components to M1-M4 APIs

## Next Steps

1. **Phase 1 (Done)**: Frontend scaffolding ✓
2. **Phase 2 (1:45-3:00)**: 
   - M1-M4 implement backend endpoints
   - M5 wires frontend to real APIs
3. **Integration (3:00-3:20)**: 
   - All PRs merged to develop
   - Full E2E testing
4. **Demo & Tag (3:50-4:00)**: 
   - Demo rehearsal
   - Tag v1.0.0 on main

## Questions?

See `production-rag-track4.md` for complete implementation plan.
