# pgAdmin Quick Setup Checklist

**Time to complete**: 5-10 minutes  
**Difficulty**: Easy (GUI-based)

---

## ✅ Pre-Setup

- [ ] PostgreSQL installed and running
- [ ] pgAdmin installed and accessible at http://localhost:5050
- [ ] pgAdmin login working
- [ ] PostgreSQL server visible in pgAdmin left sidebar

---

## ✅ Database Creation

- [ ] Right-click "Databases" in left sidebar
- [ ] Select "Create" → "Database..."
- [ ] Enter name: `fde_rag`
- [ ] Click "Save"
- [ ] Verify database appears in sidebar

---

## ✅ Enable pgvector Extension

- [ ] Right-click on `fde_rag` database
- [ ] Select "Query Tool"
- [ ] Paste: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] Click Execute (F5)
- [ ] Verify: "Query returned successfully"

---

## ✅ Create Tables

### documents table
- [ ] Open Query Tool for `fde_rag`
- [ ] Copy and paste documents table SQL
- [ ] Click Execute
- [ ] Verify: "Query returned successfully"

### chunks table
- [ ] In same Query Tool
- [ ] Copy and paste chunks table SQL
- [ ] Click Execute
- [ ] Verify: "Query returned successfully"

---

## ✅ Create Indices

- [ ] In same Query Tool
- [ ] Copy and paste all 4 index creation queries
- [ ] Click Execute
- [ ] Verify: "Query returned successfully"

---

## ✅ Verify Setup

Run verification query:

```sql
-- Check tables exist
SELECT tablename FROM pg_tables 
WHERE schemaname='public' AND tablename IN ('documents', 'chunks');

-- Check pgvector
SELECT * FROM pg_extension WHERE extname='vector';

-- Check indices
SELECT indexname FROM pg_indexes WHERE tablename = 'chunks';
```

Verify:
- [ ] 2 tables found (documents, chunks)
- [ ] vector extension exists
- [ ] 4 indices found (idx_chunks_document_id, idx_chunks_department, idx_chunks_category, idx_chunks_text)

---

## ✅ Configure Environment

- [ ] Copy: `cp .env.example .env`
- [ ] Edit `.env`:
  - [ ] `DB_HOST=localhost`
  - [ ] `DB_PORT=5432`
  - [ ] `DB_USER=postgres`
  - [ ] `DB_PASSWORD=` (your PostgreSQL password)
  - [ ] `DB_NAME=fde_rag`
  - [ ] `HF_TOKEN=` (your Hugging Face token)

---

## ✅ Test Connection

Run:
```bash
python test_db_connection.py
```

Expected output:
```
✅ Connected! Documents table has 0 rows
```

---

## ✅ Start RAG System

### Terminal 1 - Backend
```bash
python -m uvicorn backend.main:app --reload
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

Wait for:
```
Local:   http://localhost:5173/
```

### Browser
```
Open: http://localhost:5173
```

---

## ✅ Test Everything

1. [ ] Frontend loads
2. [ ] Upload Docs tab works
3. [ ] Upload a test PDF or Markdown file
4. [ ] See: "Successfully uploaded and indexed!"
5. [ ] Click Chat tab
6. [ ] Ask a question
7. [ ] See response with sources
8. [ ] View metrics showing real data

---

## ✅ Common Issues & Solutions

### Can't connect to pgAdmin?
- [ ] Check: http://localhost:5050 (Windows/Mac) or http://localhost/pgadmin4 (Linux)
- [ ] Check PostgreSQL is running

### Extension "vector" doesn't exist?
- [ ] Install pgvector first (see POSTGRES_SETUP.md)
- [ ] Then: `CREATE EXTENSION vector;`

### Tables not showing in pgAdmin?
- [ ] Right-click "Tables" folder → "Refresh"
- [ ] Or right-click database → "Refresh"

### Can't insert data?
- [ ] Check: PRIMARY KEY constraint (id must be unique)
- [ ] Check: FOREIGN KEY constraint (document_id must exist in documents)
- [ ] Run verification query to see table structure

### Connection refused?
- [ ] Verify .env has correct DB_PASSWORD
- [ ] Check PostgreSQL is running: `psql -U postgres`
- [ ] Verify port 5432 is available: `telnet localhost 5432`

---

## ✅ You're Done!

Your RAG system is now:
- ✅ Using real PostgreSQL (not mock)
- ✅ Documents auto-indexed on upload
- ✅ Search queries PostgreSQL
- ✅ Metrics show real data
- ✅ Production-ready

**Happy searching!** 🚀

---

## 📖 Full Guides

For more details:
- **PGADMIN_SETUP.md** - Complete pgAdmin setup guide
- **POSTGRES_SETUP.md** - PostgreSQL setup details
- **QUICK_START_POSTGRES.md** - 5-minute quick start
- **POSTGRES_COMPLETE.md** - Production guide

