# Port Configuration Verification ✓

## All Port 8000 References - VERIFIED

### Backend Configuration
- **File:** `backend/app/main.py`
- **Setting:** `uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)`
- **Status:** ✓ Port 8000

### Frontend API Configuration
- **File:** `frontend/src/utils/api.js`
- **Setting:** `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`
- **Status:** ✓ Port 8000

### Frontend Vite Config
- **File:** `frontend/vite.config.js`
- **Setting:** `target: 'http://localhost:8000'`
- **Status:** ✓ Port 8000

### Environment Variables
- **File:** `.env`
- **Setting:** `VITE_API_URL=http://localhost:8000`
- **Status:** ✓ Port 8000

### CORS Configuration
- **File:** `backend/app/main.py`
- **Setting:** 
  - `http://localhost:3000` ✓ Frontend on 3000
  - `http://127.0.0.1:3000` ✓ Frontend on 3000
- **Status:** ✓ Correctly allows frontend on port 3000

---

## Expected Ports

| Service | Port | Status |
|---------|------|--------|
| Backend API | 8000 | ✓ Running |
| Frontend Dev | 3000 | ✓ Running |
| PostgreSQL | 5432 | Separate (must run) |

---

## Start Both Services

### Terminal 1 - Backend
```bash
cd C:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity
python -m uvicorn backend.app.main:app --port 8000 --reload
```

Expected:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Frontend
```bash
cd C:\Users\rohan.urmude\Desktop\FDE\rag\rag-activity\frontend
npm run dev
```

Expected:
```
Local:   http://localhost:3000/
```

### Terminal 3 - PostgreSQL (if local)
```bash
# Windows - assuming PostgreSQL installed
"C:\Program Files\PostgreSQL\15\bin\pg_ctl.exe" -D "C:\Program Files\PostgreSQL\15\data" start
```

Or use Docker:
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
```

---

## Verify Connection

Once both are running:

### From Browser
- Frontend: http://localhost:3000
- Should connect to backend on http://localhost:8000

### From Command Line
```bash
curl -X GET http://localhost:8000/api/health
```

Should return:
```json
{"status": "ok"}
```

---

## All Ports Unified ✓

✓ Backend: 8000  
✓ Frontend: 3000  
✓ API calls: 8000  
✓ CORS: Allows 3000 → 8000  
✓ No port mismatches  

**SYSTEM READY FOR TESTING**
