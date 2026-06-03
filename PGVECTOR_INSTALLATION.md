# pgvector Installation Guide

**Error**: `extension "vector" is not available`

**Solution**: Install pgvector on your PostgreSQL system

---

## Choose Your Operating System

### Windows

#### Option 1: Using Pre-compiled Binary (EASIEST)

1. **Download pgvector DLL**
   - Go to: https://github.com/pgvector/pgvector/releases
   - Download: `pgvector-x.y.z-postgresql-VERSION-windows-x64.zip`
   - (Replace VERSION with your PostgreSQL version, e.g., 15, 16)

2. **Extract to PostgreSQL lib directory**
   ```
   Default location: C:\Program Files\PostgreSQL\15\lib\
   (or C:\Program Files\PostgreSQL\16\lib\ if you have v16)
   ```

3. **Find your PostgreSQL version**
   - Open pgAdmin
   - Right-click server
   - Click "Properties"
   - See "PostgreSQL Version" at top

4. **Extract the DLL**
   - Extract zip file
   - Copy `vector.dll` to PostgreSQL lib directory
   - Copy `vector.sql` to PostgreSQL share/extension directory
   - Copy `vector.control` to PostgreSQL share/extension directory

5. **Restart PostgreSQL**
   - Windows: Services → PostgreSQL → Restart
   - Or: Right-click PostgreSQL in system tray → Restart

6. **Verify in pgAdmin Query Tool**
   ```sql
   CREATE EXTENSION vector;
   ```
   Expected: `Query returned successfully`

#### Option 2: Build from Source (ADVANCED)

If pre-compiled binary doesn't work:

1. Install Visual Studio Build Tools (free)
2. Clone pgvector repo
3. Build and install

(See: https://github.com/pgvector/pgvector#windows)

---

### Mac

#### Option 1: Using Homebrew (EASIEST)

```bash
# Install pgvector
brew install pgvector

# If you already have PostgreSQL installed
brew reinstall postgresql
```

#### Option 2: Build from Source

```bash
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**Verify:**
```sql
CREATE EXTENSION vector;
```

---

### Linux (Ubuntu/Debian)

#### Option 1: Using Package Manager (EASIEST)

```bash
# Install pgvector package
sudo apt-get update
sudo apt-get install postgresql-16-pgvector
# (Replace 16 with your PostgreSQL version)

# Or for generic installation:
sudo apt-get install pgvector
```

#### Option 2: Build from Source

```bash
# Install dependencies
sudo apt-get install postgresql-server-dev-16
# (Replace 16 with your PostgreSQL version)

# Clone and build
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**Verify:**
```sql
CREATE EXTENSION vector;
```

---

## After Installation

### 1. Restart PostgreSQL

**Windows**
```
Services → PostgreSQL → Restart
```

**Mac**
```bash
brew services restart postgresql
```

**Linux**
```bash
sudo systemctl restart postgresql
```

### 2. Verify Installation

Open pgAdmin Query Tool and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Expected: `Query returned successfully`

### 3. Check it's Installed

```sql
SELECT * FROM pg_extension WHERE extname='vector';
```

Expected: One row with pgvector extension

---

## If Still Not Working

### Check PostgreSQL Version

```sql
SELECT version();
```

Make sure you installed pgvector for the **correct version** (e.g., v15, v16)

### Check Installation Location

Find where PostgreSQL installed pgvector:

**Windows**
- Check: `C:\Program Files\PostgreSQL\15\lib\vector.dll`
- Check: `C:\Program Files\PostgreSQL\15\share\extension\vector.control`

**Mac/Linux**
```bash
pg_config --libdir
pg_config --sharedir
```

Verify `vector.so` (Mac/Linux) or `vector.dll` (Windows) exists in these locations

### Reinstall PostgreSQL (Last Resort)

If pgvector won't work:
1. Uninstall PostgreSQL completely
2. Delete PostgreSQL directory
3. Reinstall PostgreSQL
4. Install pgvector **before** creating databases

---

## Common Issues

### "Cannot find vector.dll"

**Solution**:
1. Download correct version for your PostgreSQL version
2. Extract to correct lib directory
3. Make sure file is named exactly `vector.dll`
4. Restart PostgreSQL

### "Wrong version of vector.dll"

**Solution**:
- Windows and PostgreSQL must match: both 32-bit or both 64-bit
- Check PostgreSQL version: Right-click server in pgAdmin → Properties

### "Build tools not found" (when building from source)

**Windows**:
- Install Visual Studio Build Tools (free)
- https://visualstudio.microsoft.com/visual-cpp-build-tools/

**Mac**:
- Install Xcode Command Line Tools: `xcode-select --install`

**Linux**:
- Install build tools: `sudo apt-get install build-essential postgresql-server-dev-16`

---

## Step-by-Step for Windows (Most Common)

### 1. Find Your PostgreSQL Version
- Open pgAdmin
- Right-click server → Properties
- Note the version (e.g., "PostgreSQL 15.2")

### 2. Download pgvector
- Go to: https://github.com/pgvector/pgvector/releases
- Download `pgvector-x.x.x-postgresql-15-windows-x64.zip` (for v15)
- Or `pgvector-x.x.x-postgresql-16-windows-x64.zip` (for v16)

### 3. Extract Files
- Extract zip to temp folder
- You should see: `vector.dll`, `vector.sql`, `vector.control`

### 4. Find PostgreSQL Installation
- Usually: `C:\Program Files\PostgreSQL\15\`
- Or: `C:\Program Files\PostgreSQL\16\`

### 5. Copy Files
```
Copy vector.dll 
  FROM: extracted zip
  TO: C:\Program Files\PostgreSQL\15\lib\
  
Copy vector.sql
  FROM: extracted zip  
  TO: C:\Program Files\PostgreSQL\15\share\extension\
  
Copy vector.control
  FROM: extracted zip
  TO: C:\Program Files\PostgreSQL\15\share\extension\
```

### 6. Restart PostgreSQL

**Option A**: Using Services
- Press `Win + R`
- Type: `services.msc`
- Find: PostgreSQL (version)
- Right-click → Restart

**Option B**: Using Command Prompt (Admin)
```cmd
net stop postgresql-x64-15
net start postgresql-x64-15
```

### 7. Test in pgAdmin

Open pgAdmin Query Tool:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
SELECT * FROM pg_extension WHERE extname='vector';
```

Expected: Both queries succeed ✅

---

## After pgvector Works

### Now Create Database

In pgAdmin Query Tool:

```sql
-- Create extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database
CREATE DATABASE fde_rag;
```

### Then Create Tables

```sql
-- Connect to fde_rag database first

-- Create documents table
CREATE TABLE documents (
    id VARCHAR(255) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    ... (rest of schema)
);

-- Create chunks table with vector support
CREATE TABLE chunks (
    id VARCHAR(255) PRIMARY KEY,
    ... columns ...
    embedding BYTEA,  -- Vector storage
    ...
);
```

---

## Verification Commands

```sql
-- Check extension is loaded
SELECT * FROM pg_extension WHERE extname='vector';

-- Check you can create vector type
CREATE TABLE test_vector (
    id SERIAL PRIMARY KEY,
    embedding BYTEA
);

-- Drop test table
DROP TABLE test_vector;
```

---

## Still Having Issues?

1. **Restart PostgreSQL** - Very common to need restart
2. **Check file permissions** - Make sure PostgreSQL can read the files
3. **Try reinstalling** - Uninstall and reinstall pgvector
4. **Check PostgreSQL version** - Make sure pgvector matches your version
5. **Check PostgreSQL architecture** - Both must be 64-bit or both 32-bit

---

## Get Help

If still stuck:
1. Post issue: https://github.com/pgvector/pgvector/issues
2. PostgreSQL docs: https://www.postgresql.org/docs/
3. Or run your RAG system without pgvector (system will work with mock data)

---

## Next Steps After Installation

1. ✅ pgvector installed
2. ✅ PostgreSQL restarted
3. → Go back to PGADMIN_QUICK_CHECKLIST.md
4. → Continue from "Enable pgvector Extension" step
5. → Create database and tables
6. → Configure .env
7. → Start RAG system

You're almost there! 🚀
