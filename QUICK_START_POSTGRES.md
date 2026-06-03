# PostgreSQL Quick Start (5 minutes)

## TL;DR - Get it running NOW

### 1. Install PostgreSQL (if not already installed)

**Windows**: Download from https://www.postgresql.org/download/windows/
**Mac**: `brew install postgresql`
**Linux**: `sudo apt-get install postgresql postgresql-contrib`

### 2. Start PostgreSQL

**Windows (pgAdmin)**: Click "Start" button in pgAdmin
**Mac**: `brew services start postgresql`
**Linux**: `sudo systemctl start postgresql`

### 3. Copy .env
```bash
cp .env.example .env
```

### 4. Edit .env with your PostgreSQL password
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_actual_password  # ← Change this!
DB_NAME=fde_rag
DATABASE_URL=postgresql://postgres:your_actual_password@localhost:5432/fde_rag
HF_TOKEN=your_hf_token_here
```

### 5. Run setup script
```bash
python setup_db.py
```

You should see:
```
[1] Checking database 'fde_rag'...
  ✓ Database created
[2] Enabling pgvector extension...
  ✓ pgvector extension enabled
[3] Creating tables...
  ✓ documents table created
  ✓ chunks table created
[4] Verifying connection...
  ✓ Connected to PostgreSQL...
  ✓ pgvector is available
```

### 6. Start Backend
```bash
python -m uvicorn backend.main:app --reload
```

### 7. Start Frontend (new terminal)
```bash
cd frontend
npm run dev
```

### 8. Open Browser
Go to: **http://localhost:5173**

---

## That's it! 🎉

Now when you:
- **Upload a document** → Chunks indexed to PostgreSQL
- **Search** → Queries real PostgreSQL (not mock)
- **View metrics** → Shows real data (not mock)

---

## If setup_db.py fails

### Option 1: Manual setup
Open psql and run:
```sql
CREATE DATABASE fde_rag;
\c fde_rag
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
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
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chunks (
    id VARCHAR(255) PRIMARY KEY,
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    document_id VARCHAR(255) REFERENCES documents(id),
    text TEXT NOT NULL,
    chunk_index INTEGER,
    section VARCHAR(255),
    page_number INTEGER,
    token_count INTEGER,
    department VARCHAR(100),
    category VARCHAR(100),
    embedding BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_department ON chunks(department);
CREATE INDEX idx_chunks_category ON chunks(category);
```

### Option 2: Check if pgvector is installed
In psql:
```sql
CREATE EXTENSION vector;
```

If it fails, install pgvector:
- **Windows**: https://github.com/pgvector/pgvector/releases
- **Mac**: `brew install pgvector`
- **Linux**: Build from source (see POSTGRES_SETUP.md)

---

## Common Issues

| Issue | Fix |
|-------|-----|
| "Connection refused" | PostgreSQL not running. Start it first. |
| "password authentication failed" | DB_PASSWORD in .env doesn't match your PostgreSQL password |
| "database does not exist" | Run setup_db.py again |
| "pgvector does not exist" | Install pgvector extension (see links above) |

---

## Next Steps

1. ✅ PostgreSQL running
2. ✅ setup_db.py successful
3. Upload a document in the UI
4. Watch it get indexed to PostgreSQL
5. Search for it
6. View real metrics

---

## Architecture (Now with Real DB!)

```
BEFORE (Mock Data):
  Upload → Mock indexed → Search returns mock → Metrics are mock
  
AFTER (PostgreSQL):
  Upload → Real indexed to PostgreSQL → Search queries PostgreSQL → Real metrics!
```

---

**See POSTGRES_SETUP.md for detailed information**

---

## Useful Commands

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Connect to fde_rag database
psql -U postgres -d fde_rag

# In psql:
\dt                    # List tables
\d chunks              # Describe chunks table
SELECT COUNT(*) FROM chunks;  # Count chunks
```

---

Ready to use real databases? Go! 🚀
