# PostgreSQL pgvector Setup using pgAdmin

**Status**: ✅ Easy GUI-based setup  
**Tool**: pgAdmin (web-based PostgreSQL management)

---

## Step 1: Install pgAdmin

### Windows
```
1. Download from https://www.pgadmin.org/download/pgadmin-4-windows/
2. Run installer
3. Follow setup wizard
4. Default port: http://localhost:5050
```

### Mac
```bash
brew install pgadmin4
# or download from: https://www.pgadmin.org/download/pgadmin-4-macos/
```

### Linux (Ubuntu)
```bash
sudo apt-get install pgadmin4
# Then access at: http://localhost/pgadmin4
```

---

## Step 2: Open pgAdmin

**URL**: http://localhost:5050 (or http://localhost/pgadmin4 on Linux)

**Login**: 
- Email: (your email)
- Password: (your pgAdmin password)

You should see a dashboard like:
```
pgAdmin 4
├─ Dashboard
├─ Servers
│  └─ PostgreSQL Server (your connection)
```

---

## Step 3: Create Database via pgAdmin

### 3A. Connect to PostgreSQL Server
1. In left sidebar, expand "Servers"
2. Right-click on your PostgreSQL server
3. Click "Properties" or double-click to verify connection
4. You should see: ✅ Connected

### 3B. Create New Database
1. Right-click on "Databases" under your server
2. Select "Create" → "Database..."
3. Fill in:
   ```
   Database name: fde_rag
   Owner: postgres
   ```
4. Click "Save"

**Result**: New database `fde_rag` created ✅

---

## Step 4: Enable pgvector Extension

### 4A. Open Query Tool
1. In left sidebar, expand your server
2. Expand "Databases" 
3. Right-click on "fde_rag"
4. Select "Query Tool" (or Tools → Query Tool)

You'll see a SQL editor window.

### 4B. Create pgvector Extension
Copy and paste this SQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then click **Execute** (play button) or press **F5**.

You should see:
```
Query returned successfully in 123 ms.
```

✅ pgvector is now enabled!

---

## Step 5: Create Tables

### 5A. Create documents Table
In the Query Tool, copy and paste:

```sql
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    department VARCHAR(100),
    category VARCHAR(100),
    page_count INTEGER,
    total_tokens INTEGER,
    chunks_created INTEGER,
    chunking_strategy VARCHAR(50),
    doc_metadata JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Click **Execute**.

Expected: `Query returned successfully`

✅ documents table created!

### 5B: Create chunks Table
Copy and paste:

```sql
CREATE TABLE IF NOT EXISTS chunks (
    id VARCHAR(255) PRIMARY KEY,
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    document_id VARCHAR(255) REFERENCES documents(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    chunk_index INTEGER,
    section VARCHAR(255),
    page_number INTEGER,
    token_count INTEGER,
    filename VARCHAR(255),
    doc_id VARCHAR(255),
    department VARCHAR(100),
    category VARCHAR(100),
    embedding BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Click **Execute**.

Expected: `Query returned successfully`

✅ chunks table created!

---

## Step 6: Create Indices

### 6A: Create Performance Indices
Copy and paste:

```sql
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_department ON chunks(department);
CREATE INDEX IF NOT EXISTS idx_chunks_category ON chunks(category);
CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks USING gin(to_tsvector('english', text));
```

Click **Execute**.

Expected: `Query returned successfully`

✅ All indices created!

---

## Step 7: Verify Setup

Copy and paste in Query Tool:

```sql
-- Check tables
SELECT * FROM information_schema.tables 
WHERE table_name IN ('documents', 'chunks');

-- Check extensions
SELECT * FROM pg_extension WHERE extname='vector';

-- Check indices
SELECT indexname FROM pg_indexes WHERE tablename = 'chunks';
```

Click **Execute**.

You should see:
- ✅ 2 tables (documents, chunks)
- ✅ vector extension
- ✅ 4 indices

---

## Step 8: Configure .env

Create/edit `.env` file in your project root:

```env
# PostgreSQL Connection (from pgAdmin)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password  # ← Use password you set in pgAdmin
DB_NAME=fde_rag

# For SQLAlchemy ORM
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/fde_rag

# LLM Provider
HF_TOKEN=your_huggingface_token
GENERATION_PROVIDER=huggingface

# Optional: Redis (not required)
REDIS_URL=redis://localhost:6379
```

---

## Step 9: Test Connection from Python

Create a test file `test_db_connection.py`:

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        database=os.getenv("DB_NAME", "fde_rag"),
        port=os.getenv("DB_PORT", "5432")
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    print(f"✅ Connected! Documents table has {count} rows")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

Run it:
```bash
python test_db_connection.py
```

Expected output:
```
✅ Connected! Documents table has 0 rows
```

✅ Database is ready!

---

## Step 10: Start RAG System

### Terminal 1 - Backend
```bash
python -m uvicorn backend.main:app --reload
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

### Browser
Open: http://localhost:5173

---

## Using pgAdmin for Daily Tasks

### View Your Data

1. In left sidebar: Servers → PostgreSQL → Databases → fde_rag → Schemas → public → Tables
2. Right-click "documents" or "chunks"
3. Select "View/Edit Data" → "All Rows"

You'll see your data in a spreadsheet view!

### Run SQL Queries

1. Right-click on database "fde_rag"
2. Select "Query Tool"
3. Write SQL:
   ```sql
   SELECT COUNT(*) as total_documents FROM documents;
   SELECT COUNT(*) as total_chunks FROM chunks;
   ```
4. Click Execute

### Backup Database

1. Right-click on database "fde_rag"
2. Select "Backup..."
3. Choose location and format
4. Click Backup

### View Database Size

```sql
SELECT pg_size_pretty(pg_database_size('fde_rag'));
```

### View Active Queries

```sql
SELECT pid, usename, query FROM pg_stat_activity;
```

### Optimize Tables

```sql
VACUUM ANALYZE documents;
VACUUM ANALYZE chunks;
```

---

## Monitoring in pgAdmin

### Dashboard
- Click "Dashboard" at the top
- See: connections, transactions, queries per second

### Server Monitoring
- Right-click server → "Properties"
- See: connections, version, size

### Query Performance
- Tools → Server Log
- See queries and their performance

---

## Troubleshooting with pgAdmin

### Can't Connect to Server?
1. Right-click server → "Properties"
2. Check: Host, Port, Username
3. Click "Test" button
4. If it fails, go to "Connection" tab
5. Verify settings match your PostgreSQL installation

### Database Won't Show?
1. Click refresh button (↻) in toolbar
2. Or right-click "Databases" → "Refresh"

### Extension Not Found?
1. Query Tool: `CREATE EXTENSION vector;`
2. If error: pgvector not installed in PostgreSQL
3. Install: brew install pgvector (Mac) or build from source

### Can't Insert Data?
1. Check PRIMARY KEY constraint: `id` must be unique
2. Check FOREIGN KEY: `document_id` must exist in documents table
3. View error: Right-click table → "View/Edit Data" → try insert

### Performance Slow?
1. Run: `VACUUM ANALYZE chunks;`
2. Check indices exist: Query Tool → `SELECT * FROM pg_indexes;`
3. Check table size: Query Tool → `SELECT pg_size_pretty(pg_total_relation_size('chunks'));`

---

## Next Steps

1. ✅ Open pgAdmin
2. ✅ Create database "fde_rag"
3. ✅ Enable pgvector extension
4. ✅ Create documents + chunks tables
5. ✅ Create indices
6. ✅ Configure .env
7. ✅ Test connection
8. ✅ Start RAG system

Then upload documents and search!

---

## Useful pgAdmin Tips

### Keyboard Shortcuts
- **F5**: Execute query
- **Ctrl+Shift+E**: Execute query
- **Ctrl+;**: Run selected SQL

### View Table Structure
1. Right-click table
2. Click "Properties"
3. Go to "Columns" tab
4. See all column definitions

### Export Data
1. Right-click table
2. Select "Backup..."
3. Choose CSV format
4. Open in Excel

### Import Data
1. Right-click table
2. Select "Import/Export"
3. Choose your file
4. Map columns
5. Click Import

---

## When to Use pgAdmin vs Command Line

| Task | pgAdmin | Command Line |
|------|---------|--------------|
| Create database | ✅ Easy | Complex |
| Create tables | ✅ Easy | Simple |
| View data | ✅ Great | `psql` harder |
| Run queries | ✅ Easy | `psql` fine |
| Backup | ✅ GUI | `pg_dump` better |
| Automate | ❌ No | ✅ Yes |

**Recommendation**: Use pgAdmin for setup and daily tasks, command line for backups and automation.

---

## Summary

With pgAdmin, you can:
- ✅ Create database visually
- ✅ Create tables visually
- ✅ Enable pgvector extension
- ✅ View and edit data
- ✅ Run SQL queries
- ✅ Monitor performance
- ✅ Backup database

**Your RAG system is ready to use!** 🚀

