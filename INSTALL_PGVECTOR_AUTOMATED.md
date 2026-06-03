# Automated pgvector Installation for Windows

**Goal**: Automatically download and install pgvector without manual steps

---

## Method 1: PowerShell (RECOMMENDED - More Reliable)

### Step 1: Open PowerShell as Administrator
1. Press **Win + X**
2. Click **Windows PowerShell (Admin)** or **Terminal (Admin)**
3. Click **Yes** when prompted

### Step 2: Allow Script Execution
Copy and paste this command:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

Press **Enter**. This allows PowerShell scripts to run in this session only.

### Step 3: Run the Installation Script
Copy and paste this command:

```powershell
cd "C:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity"
.\install_pgvector.ps1
```

Press **Enter**

### Step 4: Watch It Work!
The script will:
- ✅ Find your PostgreSQL installation
- ✅ Download pgvector (automatically)
- ✅ Extract files
- ✅ Copy to PostgreSQL directories
- ✅ Restart PostgreSQL service
- ✅ Clean up temporary files

Expected output:
```
========================================================
  pgvector Automatic Installation (PowerShell)
========================================================

[Step 1] Detecting PostgreSQL Installation...
Found PostgreSQL at: C:\Program Files\PostgreSQL\15
PostgreSQL Version: 15

[Step 2] Downloading pgvector...
Download successful!

[Step 3] Extracting pgvector...
Extraction successful!

[Step 4] Copying files to PostgreSQL...
Copied: vector.dll
Copied: vector.sql
Copied: vector.control

[Step 5] Restarting PostgreSQL service...
Found service: postgresql-x64-15
Stopping service...
Starting service...
PostgreSQL restarted successfully!

[Step 6] Cleaning up...
Cleanup complete!

========================================================
  Installation Complete!
========================================================

Next steps:
1. Open pgAdmin (http://localhost:5050)
2. Right-click your database
3. Select 'Query Tool'
4. Run: CREATE EXTENSION IF NOT EXISTS vector;
5. You should see: 'Query returned successfully'
```

---

## Method 2: Batch File (.bat)

If PowerShell doesn't work:

### Step 1: Open Command Prompt as Administrator
1. Press **Win + R**
2. Type: `cmd`
3. Press **Ctrl + Shift + Enter** (runs as admin)
4. Click **Yes** when prompted

### Step 2: Run the Batch Script
Copy and paste:

```cmd
cd "C:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity"
install_pgvector.bat
```

Press **Enter**

### Step 3: Watch It Work!
Same process as PowerShell - downloads, installs, restarts PostgreSQL

---

## Troubleshooting

### "ExecutionPolicy" Error
If you get: `cannot be loaded because running scripts is disabled...`

Run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

### "PostgreSQL not found" Error
Make sure PostgreSQL is installed in:
```
C:\Program Files\PostgreSQL\
```

If installed elsewhere, edit the script and change the path.

### Download Failed
If download fails (no internet or firewall):
1. Download manually: https://github.com/pgvector/pgvector/releases
2. Use `PGVECTOR_INSTALLATION.md` for manual installation

### Service Not Found
If PostgreSQL service not detected:
1. Manually restart PostgreSQL via Windows Services
2. Or restart your computer

---

## After Installation

### Verify in pgAdmin

1. Open pgAdmin: http://localhost:5050
2. Right-click your database
3. Select **Query Tool**
4. Run this SQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Expected Result

```
Query returned successfully
```

If you see this, pgvector is installed! ✅

### If It Fails

Run this SQL to check if pgvector is available:

```sql
SELECT * FROM pg_extension WHERE extname='vector';
```

If no results:
1. Restart PostgreSQL again
2. Check files were copied to:
   - `C:\Program Files\PostgreSQL\15\lib\vector.dll`
   - `C:\Program Files\PostgreSQL\15\share\extension\vector.sql`
   - `C:\Program Files\PostgreSQL\15\share\extension\vector.control`
3. If files are there, try:
   ```sql
   CREATE EXTENSION vector;
   ```

---

## Next Steps After Success

1. ✅ pgvector installed
2. ✅ PostgreSQL restarted
3. → Open `PGADMIN_QUICK_CHECKLIST.md`
4. → Continue from "Enable pgvector Extension" step
5. → Create database and tables
6. → Configure .env
7. → Start RAG system

---

## Summary

| Method | Time | Difficulty | Reliability |
|--------|------|------------|-------------|
| PowerShell Script | 2 min | Easy | High |
| Batch Script | 2 min | Easy | Medium |
| Manual | 10 min | Medium | High |

**Recommendation**: Use PowerShell script - it's the most reliable!

---

## What the Scripts Do

Both scripts automate:
1. **Detect** PostgreSQL installation location
2. **Download** pgvector from GitHub (latest version)
3. **Extract** the zip file
4. **Copy** 3 files to PostgreSQL directories:
   - `vector.dll` (the extension)
   - `vector.sql` (schema)
   - `vector.control` (metadata)
5. **Restart** PostgreSQL service
6. **Cleanup** temporary files

All done automatically! ✅

---

## Can't Use Scripts?

If scripts won't run:
1. Download manually: https://github.com/pgvector/pgvector/releases
2. Follow `PGVECTOR_INSTALLATION.md` for manual installation

---

**You're almost there!** Run one of the scripts and you'll have pgvector installed in 2 minutes! 🚀
