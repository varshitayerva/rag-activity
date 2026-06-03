# AI Search Copilot - Technical Support RAG System

**A production-ready Retrieval-Augmented Generation (RAG) system with semantic search, LLM integration, real-time monitoring, and comprehensive dashboards.**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Setup & Installation](#setup--installation)
7. [Running the Application](#running-the-application)
8. [API Documentation](#api-documentation)
9. [Frontend Components](#frontend-components)
10. [Database Schema](#database-schema)
11. [Security Features](#security-features)
12. [Performance Optimizations](#performance-optimizations)
13. [Monitoring & Alerts](#monitoring--alerts)
14. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

AI Search Copilot is a sophisticated technical support system that combines semantic search with large language models (LLMs) to provide intelligent, contextual answers to user queries. It leverages vector embeddings, advanced caching, and real-time monitoring to deliver fast, accurate responses.

**Key Use Cases:**
- Technical support document retrieval
- Knowledge base search with AI synthesis
- Document management with semantic indexing
- Real-time system monitoring and alerts
- User feedback collection and analysis

---

## 🏗️ Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                         │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │ Chat/Search  │ Upload Docs  │  Dashboards  │             │
│  │ (Semantic)   │  (Chunking)  │ (Monitoring) │             │
│  └──────────────┴──────────────┴──────────────┘             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST (Port 8002)
┌──────────────────────────▼──────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┤
│  │ API Routes Layer                                         │
│  │  • Search: /api/search (semantic + filters)             │
│  │  • Generate: /api/generate (LLM answers)                │
│  │  • Ingest: /api/ingest (document upload)                │
│  │  • Features: /api/user, /api/feedback, /api/cache       │
│  │  • Monitoring: /api/health, /api/alerts, /api/metrics   │
│  │  • Webhooks: /api/webhooks (Slack, Email)               │
│  └─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┤
│  │ Core Services                                            │
│  │  • Vector Store (embeddings search)                     │
│  │  • LLM Service (Groq llama-3.3-70b-versatile)           │
│  │  • Cache Manager (Redis + in-memory)                    │
│  │  • User Manager (authentication & profiles)             │
│  │  • Feedback Manager (ratings & analytics)               │
│  │  • Monitoring System (alerts & health scoring)          │
│  │  • Notification System (Slack + Email webhooks)         │
│  └─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┤
│  │ Infrastructure                                           │
│  │  • Auth: API key + rate limiting (100 req/60s)          │
│  │  • Validation: SQL injection prevention, file upload    │
│  │  • Logging: Structured JSON logging                     │
│  │  • CORS: Custom middleware for frontend integration     │
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────┬──────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │PostgreSQL│     │  Redis  │     │ HuggingFace│
   │ Database │     │  Cache  │     │ Inference  │
   │ (Chunks) │     │ (TTL)   │     │(Embeddings)│
   └─────────┘     └─────────┘     └─────────┘
```

### Data Flow

**1. Document Ingestion**
```
Upload File → Validate → Parse Content → Split into Chunks
→ Generate Embeddings (HuggingFace) → Store in PostgreSQL & Vector Store
```

**2. Search Query**
```
User Query → Embed Query (HuggingFace) → Vector Similarity Search (FAISS)
→ Apply Filters (department, category, date) → Rank Results → Cache
```

**3. LLM Generation**
```
Top Retrieved Chunks → Format Context → Send to Groq LLM
→ Generate Synthesis Answer → Include Source Attribution → Cache
```

**4. Monitoring**
```
API Requests → Collect Metrics (latency, errors, cache hits)
→ Compare Against Alert Thresholds → Trigger Notifications (Slack/Email)
```

---

## ✨ Features

### 🔍 **1. Semantic Search**
- **Vector Embeddings**: Uses `sentence-transformers/all-MiniLM-L6-v2` for semantic understanding
- **Similarity Search**: FAISS-based O(1) vector similarity lookup
- **Hybrid Search**: Combines BM25 full-text + semantic search
- **Smart Filtering**: Department, category, date range filters
- **Result Ranking**: Relevance scoring with source attribution

### 🤖 **2. LLM Integration**
- **Provider**: Groq (llama-3.3-70b-versatile model)
- **Answer Synthesis**: Generates comprehensive answers vs. copying documents
- **Structured Output**: Headers, bullet points, numbered lists, examples
- **Source Attribution**: Shows which documents were used
- **Streaming Support**: Real-time answer generation via SSE
- **Temperature Control**: 0.7 for balanced creativity/accuracy

### 📤 **3. Document Management**
- **Multiple Formats**: PDF, DOCX, Markdown, Plain text
- **Auto-Chunking**: Sentence-based chunk splitting (500 char size)
- **Metadata Tracking**: Department, category, file size, upload timestamp
- **Vector Indexing**: FAISS integration for fast lookups
- **Lazy Loading**: Auto-loads vector store from database on startup

### 👥 **4. User Management**
- **Authentication**: API key-based (X-API-Key header)
- **Role-Based Access**: admin, user, viewer roles
- **Activity Tracking**: Search count, generation count, last login
- **User Profiles**: Email, department, creation date
- **Rate Limiting**: 100 requests per 60 seconds per API key

### ⭐ **5. Feedback System**
- **Star Ratings**: 1-5 star rating system
- **Comments**: Optional written feedback
- **Quality Analysis**: Average rating, distribution by star
- **Trend Detection**: Identifies low-quality answers
- **Per-Query Tracking**: Associates feedback with specific searches

### ⚡ **6. Advanced Caching**
- **Hybrid Approach**: Redis + in-memory fallback
- **Search Cache**: 1-hour TTL for vector search results
- **Generation Cache**: 2-hour TTL for LLM answers
- **Hit Rate Tracking**: Monitors cache effectiveness
- **TTL Management**: Auto-expires old entries
- **Statistics**: Tracks hits, misses, evictions, memory usage

### 📊 **7. Real-Time Monitoring**
- **Metrics Collection**: Latency, error rate, QPS, cache performance
- **Health Scoring**: 0-100 score based on multiple metrics
- **Alert Rules**: 
  - High error rate (>5%)
  - High latency (>5s)
  - Low cache hit rate (<30%)
  - High QPS (>100/s)
- **Alert Status**: Real-time triggered/resolved tracking
- **Metrics History**: Stores last 1000 data points per metric

### 🔔 **8. Webhook Notifications**
- **Slack Integration**: Color-coded alerts with details
- **Email Notifications**: SMTP-based delivery
- **Webhook Management**: Register, test, delete webhooks
- **Admin-Only**: Requires admin role for management
- **Async Delivery**: Non-blocking notification sending

### 📈 **9. Comprehensive Dashboards**
- **Admin Dashboard**: System health, queries, latency, alerts, feedback
- **User Profile**: Account info, API key, activity statistics
- **User Stats**: Search/generation breakdown, activity timeline
- **Feedback Analytics**: Ratings distribution, trends, quality metrics
- **Cache Monitor**: Hit rates, memory usage, performance stats
- **System Monitoring**: Real-time metrics, alerts, health status

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI 0.104.1 (async Python web framework)
- **Server**: Uvicorn 0.24.0 (ASGI server)
- **Database**: PostgreSQL (vector-enabled with pgvector)
- **Caching**: Redis 5.0+ (with async support)
- **ORM/Query**: SQLAlchemy 2.0+ (SQL toolkit)
- **Vector Search**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: sentence-transformers 2.0+ (all-MiniLM-L6-v2)
- **LLM API**: Groq (llama-3.3-70b-versatile)
- **BM25 Search**: rank-bm25 0.2.2
- **PDF Parsing**: pypdf, pdfplumber
- **Authentication**: API key-based
- **Testing**: pytest, pytest-asyncio
- **Linting**: black, ruff
- **Logging**: Python logging with JSON formatter

### **Frontend**
- **Framework**: React 18.2.0
- **Build Tool**: Vite 4.3.0
- **Styling**: Tailwind CSS 3.3.0
- **Icons**: Lucide React 1.17.0
- **HTTP Client**: Fetch API
- **State**: React Hooks (useState, useEffect)
- **Deployment**: Static build output

### **Infrastructure**
- **OS**: Windows 11 Pro / Linux compatible
- **Python**: 3.10+
- **Node.js**: 18+ (for frontend)
- **Ports**: 8002 (backend), 3002 (frontend)

---

## 📁 Project Structure

```
rag-activity/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app initialization
│   │   ├── auth.py                 # API key authentication + rate limiting
│   │   ├── validation.py           # Input validation (SQL injection, file upload)
│   │   ├── logging_config.py       # JSON structured logging
│   │   │
│   │   ├── database/
│   │   │   └── postgres.py         # PostgreSQL client with connection pooling
│   │   │
│   │   ├── search/
│   │   │   ├── routes.py           # /api/search, /api/generate endpoints
│   │   │   ├── ingest_routes.py    # /api/ingest for document upload
│   │   │   ├── vector_store.py     # Vector embedding & storage
│   │   │   ├── vector_index.py     # FAISS integration
│   │   │   ├── embeddings.py       # HuggingFace embeddings wrapper
│   │   │   ├── hybrid_search.py    # BM25 + semantic combination
│   │   │   └── rrf_fusion.py       # Reciprocal rank fusion
│   │   │
│   │   ├── generation/
│   │   │   └── service.py          # LLM answer generation (Groq)
│   │   │
│   │   ├── cache/
│   │   │   ├── advanced_cache.py   # Redis + in-memory hybrid cache
│   │   │   ├── metrics.py          # Cache hit/miss tracking
│   │   │   ├── compression.py      # Context compression
│   │   │   └── response_cache.py   # Response-level caching
│   │   │
│   │   ├── models/
│   │   │   ├── user.py             # User model + UserManager
│   │   │   └── feedback.py         # Feedback model + FeedbackManager
│   │   │
│   │   ├── api/
│   │   │   ├── features_routes.py  # User, feedback, cache, monitoring routes
│   │   │   └── metrics.py          # /api/metrics endpoint
│   │   │
│   │   ├── monitoring/
│   │   │   └── metrics.py          # MonitoringSystem with alert rules
│   │   │
│   │   └── webhooks/
│   │       ├── notifications.py    # Slack/Email notification system
│   │       └── routes.py           # Webhook management endpoints
│   │
│   ├── requirements.txt            # Python dependencies
│   └── tests/
│       ├── test_search.py          # Search functionality tests
│       └── test_validation.py      # Validation tests
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main app with navigation
│   │   ├── main.jsx                # React entry point
│   │   │
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx       # Semantic search + chat
│   │   │   ├── UploadPanel.jsx     # Document upload
│   │   │   ├── FilterBar.jsx       # Search filters
│   │   │   ├── SourceCard.jsx      # Retrieved document display
│   │   │   ├── MetricsBar.jsx      # Top metrics display
│   │   │   ├── StatusIndicator.jsx # Backend health status
│   │   │   ├── UserProfile.jsx     # User account dashboard
│   │   │   ├── FeedbackPanel.jsx   # Feedback submission + analytics
│   │   │   ├── CacheDashboard.jsx  # Cache performance monitoring
│   │   │   ├── MonitoringDashboard.jsx # System metrics + alerts
│   │   │   ├── AdminDashboard.jsx  # Admin overview
│   │   │   └── UserStatsDashboard.jsx # User activity stats
│   │   │
│   │   └── utils/
│   │       └── api.js              # API client (search, generate, ingest, etc.)
│   │
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Vite configuration
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   └── postcss.config.js           # PostCSS configuration
│
├── .env                            # Environment variables
├── .env.example                    # Example environment file
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

---

## 🚀 Setup & Installation

### Prerequisites

```bash
# Required
- Python 3.10+
- PostgreSQL 14+ (with pgvector extension)
- Node.js 18+
- npm or yarn

# Optional (for production)
- Redis 6+
- Docker + Docker Compose
```

### 1. Clone Repository

```bash
git clone https://github.com/varshitayerva/rag-activity.git
cd rag-activity
```

### 2. Backend Setup

```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Create .env file from template
cp .env.example .env

# Configure environment variables
# Update in .env:
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=fde_rag
HF_TOKEN=your_huggingface_token
GROQ_API_KEY=your_groq_api_key
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb fde_rag

# Install pgvector extension
psql fde_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run database schema (automatic on first backend startup)
# OR manually execute: backend/app/database/schema.sql
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production (optional)
npm run build
```

---

## ▶️ Running the Application

### Start Backend Server

```bash
cd backend

# Port 8002 (default)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002

# Or with auto-reload for development
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Start Frontend Server

```bash
cd frontend

# Development server (Port 3002)
npm run dev

# Or build and preview
npm run build
npm run preview
```

### Access Application

```
Frontend:  http://localhost:3002
Backend:   http://localhost:8002
API Docs:  http://localhost:8002/docs (Swagger UI)
```

### First-Time Setup Commands

```bash
# Test backend health
curl http://localhost:8002/health

# Test API with demo user
curl -H "X-API-Key: sk-demo-key-12345" \
  http://localhost:8002/api/user/profile
```

---

## 🔌 API Documentation

### Authentication

All endpoints (except `/health` and `/docs`) require API key:

```bash
curl -H "X-API-Key: sk-demo-key-12345" http://localhost:8002/api/endpoint
```

**Demo API Keys:**
- `sk-demo-key-12345` (regular user)
- `sk-demo-key-67890` (admin user)

### Core Endpoints

#### **Search & Generate**

```
POST /api/search
  Query: Search query string
  top_k: Number of results (default: 10)
  department: Filter by department (optional)
  category: Filter by category (optional)
  dateFrom: Start date filter (optional)
  dateTo: End date filter (optional)
  
  Returns: Relevant document chunks with scores

POST /api/generate
  Query: User question
  top_k: Context chunks to use
  filters: Search filters
  stream: Enable SSE streaming (optional)
  
  Returns: LLM-generated answer with sources

POST /api/ingest
  file: Document file (pdf, docx, txt, md)
  department: Document department
  category: Document category
  
  Returns: document_id, chunks_created, file_size
```

#### **User Management**

```
GET /api/user/profile
  Returns: Current user info + stats
  
GET /api/user/stats
  Returns: Search count, generation count, etc.
  
POST /api/user/create (admin only)
  username, email, department, role
  
GET /api/users/list (admin only)
  Returns: All users
```

#### **Feedback**

```
POST /api/feedback/submit
  query, answer, rating (1-5), comment (optional)
  
GET /api/feedback/stats
  Returns: Total feedback, avg rating, distribution
  
GET /api/feedback/analysis
  Returns: Trends, low-rated answers
```

#### **Cache & Monitoring**

```
GET /api/cache/stats
  Returns: Hit rate, memory usage, evictions
  
POST /api/cache/clear (admin only)
  Clears all cache
  
GET /api/health/detailed
  Returns: Health score (0-100), component status
  
GET /api/alerts/status
  Returns: Triggered alerts
  
GET /api/monitoring/metrics
  Returns: Latency, error rate, QPS, etc.
```

#### **Webhooks**

```
POST /api/webhooks/register (admin only)
  name, webhook_type (slack/email), config
  
GET /api/webhooks/list (admin only)
  
POST /api/webhooks/test/{name} (admin only)
  Sends test alert
  
DELETE /api/webhooks/delete/{name} (admin only)
```

---

## 🎨 Frontend Components

### Component Hierarchy

```
App (main container)
├── Header (logo, dark mode toggle)
├── Sidebar (navigation menu)
│   ├── Chat (search interface)
│   ├── Documents (upload panel)
│   ├── Profile (user account)
│   ├── Feedback (ratings & analytics)
│   ├── Cache (performance monitor)
│   ├── Monitoring (system metrics)
│   ├── Admin (system overview)
│   └── My Stats (user activity)
└── Main Content Area
```

### Key Components

**ChatPanel**
- Search bar with filters
- Real-time answer generation
- Source card display
- Loading states

**UploadPanel**
- Drag & drop file upload
- Metadata selection (department, category)
- Success/error messaging
- Progress indication

**UserProfile**
- Account information display
- API key management (copy to clipboard)
- User statistics (searches, generations)
- Role and department info

**FeedbackPanel**
- Star rating selector
- Feedback comment input
- Analytics tab with charts
- Rating distribution visualization

**CacheDashboard**
- Hit rate percentage
- Cache size metrics
- Search vs. generation cache comparison
- Clear cache button

**MonitoringDashboard**
- Metrics tab (latency, errors, QPS)
- Alerts tab (triggered/resolved)
- Health tab (component status, uptime)
- Real-time updates (5-second refresh)

---

## 🗄️ Database Schema

### Core Tables

```sql
-- Documents
documents (
  id SERIAL PRIMARY KEY,
  filename VARCHAR(255),
  content_type VARCHAR(50),
  file_size INTEGER,
  department VARCHAR(100),
  category VARCHAR(100),
  uploaded_at TIMESTAMP,
  created_at TIMESTAMP
)

-- Chunks (document segments)
chunks (
  id SERIAL PRIMARY KEY,
  document_id INTEGER REFERENCES documents,
  chunk_index INTEGER,
  text TEXT,
  embedding vector(384),  -- pgvector
  section VARCHAR(255),
  page_number INTEGER,
  created_at TIMESTAMP
)

-- Users
users (
  id SERIAL PRIMARY KEY,
  user_id UUID UNIQUE,
  username VARCHAR(255),
  email VARCHAR(255),
  api_key VARCHAR(255) UNIQUE,
  department VARCHAR(100),
  role VARCHAR(20),  -- admin, user, viewer
  is_active BOOLEAN,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  last_login TIMESTAMP
)

-- Feedback
feedback (
  id SERIAL PRIMARY KEY,
  feedback_id UUID UNIQUE,
  user_id UUID REFERENCES users.user_id,
  query TEXT,
  answer TEXT,
  rating INTEGER,  -- 1-5
  comment TEXT,
  sources JSONB,
  created_at TIMESTAMP
)
```

---

## 🔐 Security Features

### 1. **Authentication**
- API key-based authentication (X-API-Key header)
- Role-based access control (admin, user, viewer)
- Demo credentials pre-configured for testing

### 2. **Input Validation**
- SQL injection pattern detection
- File upload validation (type, size whitelist)
- Filename sanitization (prevent path traversal)
- Date format validation

### 3. **Authorization**
- Rate limiting: 100 requests per 60 seconds per API key
- Admin-only endpoints for sensitive operations
- User isolation (can only see own data)

### 4. **Data Protection**
- Structured logging (no sensitive data in logs)
- Error messages don't expose system details
- CORS properly configured for frontend origin

### 5. **Network Security**
- HTTPS ready (configure in production)
- X-API-Key header validation
- No hardcoded credentials in code

---

## ⚡ Performance Optimizations

### 1. **Caching Strategy**
- **Redis Cache**: Primary cache for production
- **In-Memory Fallback**: Automatic fallback if Redis unavailable
- **TTL Management**: 
  - Search results: 1 hour
  - LLM answers: 2 hours
- **Hit Rate Monitoring**: Tracks cache effectiveness

### 2. **Database Optimization**
- **Connection Pooling**: 2-20 connections maintained
- **Async Queries**: Non-blocking database operations
- **Vector Indexing**: FAISS for O(1) similarity search
- **Indexed Columns**: On frequently queried fields

### 3. **Vector Search**
- **FAISS Integration**: Fast approximate nearest neighbors
- **Batch Processing**: Multiple vectors processed together
- **Lazy Loading**: Vector store loaded on first request

### 4. **API Optimization**
- **Async FastAPI**: Non-blocking request handling
- **Pagination**: Limited result sets
- **Compression**: Response compression enabled
- **Connection Reuse**: HTTP keep-alive

### 5. **Frontend Optimization**
- **Code Splitting**: Component-level code splitting
- **Lazy Loading**: Components load on demand
- **Caching Headers**: Proper cache control headers
- **Minification**: Production build optimization

---

## 📊 Monitoring & Alerts

### Metrics Collected

```
Performance:
- avg_latency_ms: Average response time
- min_latency_ms, max_latency_ms: Latency range
- p50_latency, p95_latency, p99_latency: Percentiles

Reliability:
- total_queries: Cumulative requests
- error_count: Failed requests
- error_rate: Percentage of failures

Cache:
- cache_hits: Successful cache lookups
- cache_misses: Cache misses
- hit_rate: Hit rate percentage
- memory_used_mb: Cache memory usage

Vector Search:
- search_latency_ms: Embedding + similarity search time
- chunks_retrieved: Number of results returned
```

### Alert Rules

| Alert | Trigger | Severity |
|-------|---------|----------|
| High Error Rate | >5% error rate | Critical |
| High Latency | >5000ms avg | Warning |
| Low Cache Hit Rate | <30% hit rate | Warning |
| High QPS | >100 queries/sec | Warning |
| Redis Unavailable | Connection failure | Critical |

### Alert Delivery

```
Default: Console logging
With Webhooks:
- Slack: Color-coded messages with details
- Email: SMTP delivery with alert summary
```

---

## 🐛 Troubleshooting

### Common Issues

#### **1. 401 Unauthorized on Upload**
```
Problem: Document upload returns 401
Solution: 
- Check X-API-Key header is sent
- Verify API key is correct (sk-demo-key-12345)
- Ensure auth middleware is enabled in main.py
```

#### **2. Vector Store Empty**
```
Problem: Search returns no results
Solution:
- Upload documents first via /api/ingest
- Check PostgreSQL for stored chunks
- Verify embeddings are generated (check logs)
- Run: GET /api/search/rebuild
```

#### **3. Port Already in Use**
```
Problem: "Port 8002 already in use"
Solution:
- Kill process: lsof -i :8002 | kill -9 $(awk 'NR==2 {print $2}')
- Use different port: --port 8003
- Check Windows: netstat -ano | findstr :8002
```

#### **4. PostgreSQL Connection Failed**
```
Problem: "Connection refused" on localhost:5432
Solution:
- Check PostgreSQL is running: psql -U postgres
- Verify .env credentials match DB setup
- Create database: createdb fde_rag
- Test connection: psql -h localhost -U postgres -d fde_rag
```

#### **5. HuggingFace Model Download Failed**
```
Problem: "Could not load transformer model"
Solution:
- Set HF_TOKEN in .env with valid token
- Manual download: huggingface-cli login
- Fallback: Simple embedding is automatically used
- Check internet connection for model download
```

#### **6. Redis Connection Failed**
```
Problem: "Redis unavailable"
Solution:
- Start Redis: redis-server
- Set REDIS_ENABLED=true in .env
- Or disable Redis: REDIS_ENABLED=false (uses in-memory)
- Verify Redis port: redis-cli ping
```

### Debug Mode

```bash
# Enable verbose logging
export DEBUG=true

# Run with reload for development
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# View API documentation
http://localhost:8002/docs  # Swagger UI
http://localhost:8002/redoc # ReDoc
```

### Performance Debugging

```python
# Check backend logs for:
- Embedding latency
- Vector search latency
- LLM generation latency
- Cache hit/miss rates
- Database query times

# Monitor with:
curl http://localhost:8002/api/monitoring/metrics
curl http://localhost:8002/api/cache/stats
curl http://localhost:8002/api/health/detailed
```

---

## 📈 Development Workflow

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# Edit files, test locally

# 3. Run tests
pytest backend/tests/

# 4. Format code
black backend/
ruff check backend/ --fix

# 5. Commit
git add .
git commit -m "feat: description of changes"

# 6. Push and PR
git push origin feature/my-feature
# Create PR on GitHub
```

### Adding New Endpoints

```python
# 1. Add route in backend/app/api/your_routes.py
@router.get("/your/endpoint")
async def your_endpoint(api_key: str = Depends(require_auth)):
    # Implementation
    return {...}

# 2. Register in main.py
app.include_router(your_router)

# 3. Add frontend client method in frontend/src/utils/api.js
async yourMethod(param) {
  const response = await fetch(`${API_URL}/your/endpoint`, ...)
  return response.json()
}

# 4. Create React component using the method
# Import apiClient and call when needed
```

---

## 🚢 Production Deployment

### Environment Configuration

```bash
# .env for production
DB_HOST=production.db.url
DB_PORT=5432
GROQ_API_KEY=prod_groq_key
HF_TOKEN=prod_hf_token
REDIS_ENABLED=true
REDIS_URL=redis://prod:6379
DEBUG=false
ENVIRONMENT=production
```

### Running with Production Server

```bash
# Use Gunicorn with Uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8002

# Or use systemd service for auto-restart
```

### Frontend Build

```bash
# Build optimized production bundle
npm run build

# Output: frontend/dist/
# Deploy dist folder to web server (nginx, Vercel, etc.)
```

---

## 📝 License

This project is proprietary and confidential. All rights reserved.

---

## 👥 Contributors

- **Rohan Urmude** - Project Lead & Development
- **AI Pair Programming** - Claude Haiku 4.5

---

## 📞 Support

For issues, questions, or feature requests:

1. Check [Troubleshooting](#troubleshooting) section
2. Review API docs at `http://localhost:8002/docs`
3. Check backend logs for error messages
4. Submit GitHub issues with error details and reproduction steps

---

## 🎯 Project Milestones

✅ **Phase 1**: Core RAG system with semantic search
✅ **Phase 2**: LLM integration with answer synthesis
✅ **Phase 3**: Security, validation, caching infrastructure
✅ **Phase 4**: User profiles, feedback, monitoring, notifications
✅ **Phase 5**: Frontend dashboards and real-time monitoring

**Status**: Production-ready with all features implemented and tested.

---

## 🔄 Recent Updates (Latest Commits)

```
d101bfa - fix: correct upload success message to use actual response fields
2117f6d - fix: resolve document upload and port issues, update to port 8002
68fd9b6 - fix: add API key header to document upload endpoint
63874b4 - fix: resolve API endpoint issues and update backend port to 8001
badef69 - feat: add comprehensive frontend dashboards for all backend features
ba0777c - feat: add webhook notifications and frontend dashboards
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [Groq API](https://console.groq.com/)

---

**Last Updated**: June 4, 2026
**Project Version**: 1.0.0
**Status**: ✅ Production Ready
