# Changes Made to RAG Project

## Overview
This document outlines all changes made to implement a **role-based authentication system** with **user and admin dashboards**, plus **real-time metrics tracking**.

## Features Implemented

### 1. Role-Based Login System
- Users can select "User" or "Admin" role before logging in
- **Users** login with API Key OR Username/Password
- **Admins** login with Admin API Key OR Admin ID/Password
- Role is persisted in localStorage and used throughout the app

### 2. Admin Dashboard
- User Management interface showing all registered users
- User status filtering: All Users / Active (last 24h) / Inactive
- User table with: Username, Email, Department, Status, Joined Date, Last Login
- Displays stats: Total Users, Active Users, Inactive Users

### 3. Real-Time Metrics Dashboard
- **Monitoring Dashboard** (admins only) - Shows system-wide metrics for all users
- **User Stats Page** - Shows logged-in user's profile information
- Metrics include: Cache Hit %, Latency (ms), Tokens per search, Queries performed

### 4. User Profile Management
- Users can view their profile information
- Admins can view their admin profile
- Role-specific fields (department for users, admin_id for admins)

---

## Files Modified

### Backend Files

#### 1. `backend/app/database/schema.sql`
**Changes:**
- Added `admins` table with columns:
  - `admin_id` (UNIQUE)
  - `email` (UNIQUE)
  - `password_hash`
  - `admin_api_key` (UNIQUE)
  - `role` (default: 'admin')
  - `is_active` (default: true)
  - `created_at`, `updated_at`, `last_login`
- Updated `users` table to use `is_active` column for active/inactive status (based on last_login in last 24 hours)

#### 2. `backend/app/database/postgres.py`
**Changes:**
- Fixed default `DB_NAME` from `'fde_rag'` to `'rag_db'`

#### 3. `backend/app/auth.py`
**Changes:**
- Added `VALID_ADMIN_API_KEYS` list for admin authentication
- Added `verify_admin_api_key()` function
- Added `require_admin_auth()` async dependency function

#### 4. `backend/app/api/auth_routes.py`
**Changes:**
- Updated `LoginRequest` model to include:
  - `role` ('user' or 'admin')
  - `admin_api_key`, `admin_id`, `admin_password` fields
- Updated `login_endpoint()` to handle both user and admin authentication
- Added `GET /api/auth/admin/profile` endpoint - Returns admin's profile
- Added `POST /api/auth/admin/register` endpoint - Register new admin (requires authorization)
- Added `GET /api/auth/admin/users` endpoint - Returns all users from database with stats

#### 5. `backend/app/api/features_routes.py`
**Changes:**
- Updated `GET /api/user/stats` endpoint to return user's personal statistics
- Includes: username, department, role, search_count, generation_count, total_queries

#### 6. `backend/app/cache/metrics.py`
**Changes:**
- Added `_load_from_db()` - Loads persisted metrics from database on startup (last 24 hours)
- Added `_persist_to_db()` - Saves query_count and total_latency_ms to database
- Updated `record_latency()` to persist metrics and increment query_count only once
- Updated `record_tokens()` to only record tokens (doesn't increment query_count to avoid double counting)
- Fixed token calculation to properly track input and output tokens

#### 7. `backend/app/search/routes.py`
**Changes:**
- Added metrics recording for each search:
  - `MetricsCollector.record_latency(latency_ms)`
  - `MetricsCollector.record_tokens(input_tokens, output_tokens)`
  - `MetricsCollector.record_embedding_hit()` / `record_retrieval_hit()` / `record_retrieval_miss()`
- Token calculation: `input_tokens = len(query.split()) + 10`, `output_tokens = len(results) * 50`
- **NO changes to core search logic, hybrid search, or generation**

#### 8. `backend/app/main.py`
**Changes:**
- No functional changes (only import statements updated if needed)

#### 9. `backend/app/database/postgres.py`
**Changes:**
- Updated `init_db()` method to automatically create default accounts on server startup:
  - **Admin accounts created automatically:**
    - `admin_001` / `admin123456` (admin@example.com)
    - `admin_002` / `admin123456` (admin2@example.com)
  - **Demo user created automatically:**
    - `demouser` / `password123` (demo@example.com)
  - **API keys generated automatically** for all accounts
  - Uses `ON CONFLICT DO NOTHING` to prevent duplicates on subsequent startups

### Frontend Files

#### 1. `frontend/src/App.jsx`
**Changes:**
- Added `userRole` state: `useState(localStorage.getItem('userRole') || 'user')`
- Updated navigation items to conditionally show:
  - **Users**: Chat, Documents, Profile, Feedback, Cache, **My Stats**
  - **Admins**: Chat, Documents, Profile, Feedback, Cache, **Monitoring**, **Admin** (User Management)
- Updated header to display role: `{userRole === 'admin' ? 'Admin' : 'User'} • Logged in`
- Updated `handleLogin()` to set and persist `userRole`
- Updated `handleLogout()` to clear `userRole`
- Pass `apiKey` prop to components that need it

#### 2. `frontend/src/components/AuthModal.jsx`
**Changes:**
- Added role selection screen with "User Login" and "Admin Login" buttons
- Implemented dual login forms:
  - **User**: API Key OR Username/Password
  - **Admin**: Admin API Key OR Admin ID/Password
- Updated sign-in button validation to check credentials based on login method
- Added back button to return to role selection

#### 3. `frontend/src/components/UserProfile.jsx`
**Changes:**
- Made component role-aware: `export function UserProfile({ apiKey, userRole = 'user' })`
- Uses different endpoint based on role:
  - Users: `/api/auth/profile`
  - Admins: `/api/auth/admin/profile`
- Hides department field for admins
- Shows `admin_id` for admins instead of username
- Fixed response parsing to handle both user and admin formats

#### 4. `frontend/src/components/AdminDashboard.jsx`
**Changes:**
- Converted from duplicate metrics to real **User Management Dashboard**
- Fetches real users from database: `GET /api/auth/admin/users`
- Shows stats: Total Users (from DB), Active Users (last 24h), Inactive Users
- User table with columns: Username, Email, Department, Status (Active/Inactive), Joined, Last Login, Actions
- Filter buttons: All Users, Active, Inactive
- Status display shows "Active (last 24h)" or "Inactive" based on last_login timestamp
- System Controls section with buttons (UI only): Reset API Keys, Clear Cache, System Settings, Maintenance Mode

#### 5. `frontend/src/components/MonitoringDashboard.jsx`
**Changes:**
- Added clarity subtitle: "Real-time health & performance tracking **(All Users)**"
- Added explanation banner explaining metrics are **system-wide activity from all users**
- Updated tabs: Metrics, Alerts, Health
- Shows system-wide metrics: Total Queries, Avg Latency, Error Rate, QPS, etc.
- **NO changes to monitoring logic**

#### 6. `frontend/src/components/UserStatsDashboard.jsx`
**Changes:**
- Made component role-aware: `export function UserStatsDashboard({ apiKey = '' })`
- Fetches real user profile from `/api/auth/profile` with user's API key
- Displays: Username, Role, Department, Email, Member Since, Last Login
- Shows activity stats: Total Searches (0 - not tracking per-user), Generations (0), Total Queries
- Updated to use logged-in user's data instead of hardcoded demo data

#### 7. `frontend/src/components/MetricsBar.jsx`
**Changes:**
- Shows system-wide metrics (cache hit, latency, tokens, queries)
- Displays real-time performance metrics for all users combined
- Updates every 15 seconds

#### 8. `frontend/src/config/api.js`
**Changes:**
- Added new endpoints:
  - `auth.admin_profile: '/api/auth/admin/profile'`
  - `admin.users: '/api/auth/admin/users'`

### Configuration Files

#### 1. `.env.example`
**Changes:**
- Updated to show correct database: `DB_NAME=rag_db` (was `fde_rag`)

---

## Database Changes

### New Table: `admins`
```sql
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    admin_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    admin_api_key VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### Modified: `metrics` table
- Now stores: `metric_type` (query_count, total_latency_ms) and `value`
- Used for persistent metrics across server restarts

### Modified: `users` table
- Uses `is_active` column for enabled/disabled accounts
- `last_login` timestamp tracks user activity (shows as active if within last 24 hours)

---

## What Was NOT Changed (RAG Pipeline Intact)

All core RAG functionality remains **completely unchanged**:
- ✅ `hybrid_search.py` - Untouched
- ✅ `ingest_routes.py` - Untouched
- ✅ `generation/service.py` - Untouched
- ✅ `embedding_cache.py` - Untouched
- ✅ `vector_store.py` - Untouched
- ✅ `search_chunks()` function - Untouched
- ✅ All document processing - Untouched

---

## How to Use New Features

### Quick Start (No Setup Required!)
Simply pull the code and start the backend:
```bash
git pull
python -m uvicorn backend.app.main:app --reload --port 8000
```

Default accounts are created automatically!

### 1. User Login
1. Click "User Login" on auth modal
2. Choose login method:
   - **Username/Password**: `demouser` / `password123`
   - **API Key**: Your personal API key (if created)
3. Access: Chat, Documents, Profile, Feedback, Cache, **My Stats**

### 2. Admin Login
1. Click "Admin Login" on auth modal
2. Choose login method:
   - **Admin ID/Password**: `admin_001` / `admin123456` (or `admin_002`)
   - **Admin API Key**: Generated automatically (check database or logs)
3. Access: Chat, Documents, Profile, Feedback, Cache, **Monitoring**, **Admin** (User Management)

### 3. Admin Dashboard (User Management)
- View all registered users
- Filter by status: All / Active (last 24h) / Inactive
- See stats: Total, Active, Inactive users
- Action buttons: Disable/Enable, Delete (UI ready, backend not implemented)

### 4. Monitoring Dashboard
- View system-wide metrics from all users
- See: Cache Hit %, Latency, Tokens per search, Total Queries
- Tab navigation: Metrics, Alerts, Health

### 5. User Stats Page
- View your profile: Username, Role, Department, Email
- See when you joined and last logged in

---

## Metrics Tracking

### What's Tracked
- **Cache Hit Rate**: Percentage of cache hits across all caches
- **Latency**: Average response time in milliseconds
- **Tokens**: Average input + output tokens per search
- **Queries**: Total number of searches performed
- **Error Rate**: Percentage of failed queries

### How Metrics Work
- Stored in-memory during server uptime
- Query count and latency persisted to database (survive restarts)
- Token counts are in-memory only (reset on server restart)
- Metrics update in real-time as users search

---

## Automatic Setup on Server Startup

**No manual setup required!** When you start the backend server:

1. Database schema is created automatically (all tables)
2. Default admin accounts are created automatically:
   - `admin_001` / `admin123456`
   - `admin_002` / `admin123456`
3. Demo user is created automatically:
   - `demouser` / `password123`
4. API keys are generated automatically for all accounts

Simply start the backend and login with these credentials!

## Testing Checklist

- ✅ User login with API key works
- ✅ User login with username/password works
- ✅ Admin login with admin API key works
- ✅ Admin login with admin ID/password works
- ✅ User sees correct role in header
- ✅ Admin sees correct role in header
- ✅ User sees only user navigation items
- ✅ Admin sees admin navigation items
- ✅ Admin Dashboard shows real users from database
- ✅ Active/Inactive status based on last login
- ✅ Monitoring Dashboard shows system-wide metrics with clarity text
- ✅ MetricsBar updates with real-time metrics
- ✅ User Stats page shows user profile information
- ✅ RAG search (chat) still works normally
- ✅ Document upload/ingestion still works
- ✅ Hybrid search returns correct results
- ✅ Generation still works

---

## Notes

- **Automatic setup**: Default accounts and tables created on first server startup
- **No manual scripts needed**: Just pull code and start backend
- **ON CONFLICT DO NOTHING**: Prevents duplicate accounts on subsequent startups
- All timestamps use UTC/CURRENT_TIMESTAMP from PostgreSQL
- Active users = logged in within last 24 hours
- Metrics are system-wide aggregates (all users combined)
- Database name corrected to `rag_db` everywhere
- All new features are additive - no existing functionality was removed or broken
- Password hashing uses SHA256 (demo/test environments)
