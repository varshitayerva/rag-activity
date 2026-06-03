# pgvector Installation for PostgreSQL 18 - Manual Method

**Issue**: PostgreSQL 18 doesn't have pre-built pgvector binaries yet

**Solution**: Install pgvector from source (simple steps below)

---

## Option 1: Downgrade to PostgreSQL 16 (EASIEST)

### Why?
- pgvector has pre-built binaries for PostgreSQL 16
- Simpler installation (no build tools needed)
- Still production-ready

### Steps:

1. **Uninstall PostgreSQL 18**
   - Control Panel → Programs → Uninstall
   - Find PostgreSQL 18
   - Click Uninstall
   - Backup your data first if needed

2. **Install PostgreSQL 16**
   - Download: https://www.postgresql.org/download/windows/
   - Run installer
   - Select version 16.x
   - Install normally

3. **Then run the pgvector installer**
   ```
   Right-click RUN_ME_FIRST.bat
   Run as Administrator
   ```

This is the easiest path! ✅

---

## Option 2: Build pgvector from Source (ADVANCED)

If you want to keep PostgreSQL 18:

### Step 1: Install Build Tools

Download and install (free):
```
Visual Studio Build Tools
https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

During installation, select:
- "Desktop development with C++"
- "MSVC v143 or later compiler"

### Step 2: Download pgvector Source

1. Go to: https://github.com/pgvector/pgvector/releases
2. Download: `Source code (zip)`
3. Extract to: `C:\pgvector`

### Step 3: Get PostgreSQL Headers

In Command Prompt as Administrator:

```cmd
cd C:\pgvector
"C:\Program Files\PostgreSQL\18\bin\pg_config" --includedir
```

This shows where PostgreSQL header files are. Note this path.

### Step 4: Build pgvector

In Command Prompt (same directory):

```cmd
cd C:\pgvector

REM Set environment for Visual Studio
"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

REM Build pgvector
nmake /F Makefile.win USE_PGXS=1 PG_CONFIG="C:\Program Files\PostgreSQL\18\bin\pg_config.exe"
```

### Step 5: Install pgvector

Still in Command Prompt:

```cmd
nmake /F Makefile.win USE_PGXS=1 PG_CONFIG="C:\Program Files\PostgreSQL\18\bin\pg_config.exe" install
```

### Step 6: Restart PostgreSQL

```cmd
net stop postgresql-x64-18
net start postgresql-x64-18
```

### Step 7: Test

In pgAdmin Query Tool:

```sql
CREATE EXTENSION vector;
```

Should see: `Query returned successfully` ✅

---

## Option 3: Use Docker (ALTERNATIVE)

If building is too complicated:

### Install pgvector in Docker

```bash
docker run -d \
  --name pgvector-db \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  pgvector/pgvector:latest-postgres18
```

Then update `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=fde_rag
```

---

## My Recommendation

**Go with Option 1 (Downgrade to PostgreSQL 16)**

Why?
- ✅ Simplest (no build tools)
- ✅ pgvector has pre-built binaries
- ✅ Still fully supported
- ✅ No compatibility issues
- ✅ Takes 15 minutes total

Steps:
1. Uninstall PostgreSQL 18
2. Install PostgreSQL 16
3. Run `RUN_ME_FIRST.bat`
4. Done!

---

## If You Want to Keep PostgreSQL 18

Follow **Option 2** above if you're comfortable with command line and installing build tools.

It takes:
- 30 min to install Visual Studio Build Tools
- 10 min to build pgvector
- 5 min to restart and test

Total: ~45 minutes

---

## Quick Comparison

| Method | Time | Difficulty | Recommendation |
|--------|------|-----------|-----------------|
| Downgrade to PG16 | 15 min | Very Easy | ⭐ BEST |
| Build from source | 45 min | Medium | If you need PG18 |
| Docker | 10 min | Easy | Alternative |

---

## After Installing pgvector

Regardless of method, once pgvector is installed:

1. Open pgAdmin
2. Query Tool
3. Run: `CREATE EXTENSION IF NOT EXISTS vector;`
4. Should see: `Query returned successfully`
5. Continue with `PGADMIN_QUICK_CHECKLIST.md`

---

## Still Having Issues?

1. Verify pgvector is in PostgreSQL directories:
   - `C:\Program Files\PostgreSQL\16\lib\vector.dll`
   - `C:\Program Files\PostgreSQL\16\share\extension\vector.sql`
   - `C:\Program Files\PostgreSQL\16\share\extension\vector.control`

2. Restart PostgreSQL:
   ```cmd
   net stop postgresql-x64-16
   net start postgresql-x64-16
   ```

3. Test again in pgAdmin

---

## Contact

If you get stuck on building from source:
- GitHub Issues: https://github.com/pgvector/pgvector
- PostgreSQL Community: https://www.postgresql.org/community/

---

**Recommendation: Downgrade to PostgreSQL 16 and use the automated installer.** It's the simplest path! 🚀
