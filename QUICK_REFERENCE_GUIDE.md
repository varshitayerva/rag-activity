# Quick Reference Guide - AI Search Copilot

**Last Updated**: June 4, 2026  
**Version**: 2.0 (With Authentication & Real Accounts)

---

## 🚀 Quick Start

### Start Backend
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8003
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Open Browser
```
http://localhost:3000
```

---

## 🔑 API Keys

### Demo Account
```
API Key: sk-demo-key-12345
Status: Ready to use
```

### Generate New Key
```javascript
'sk-' + Math.random().toString(36).slice(2, 15)
```

### Store Key Securely
```bash
# In browser
localStorage.setItem('apiKey', 'sk-your-key-here')

# In environment
export API_KEY="sk-your-key-here"
```

---

## 📋 Feature Overview

| Feature | Status | Access | Details |
|---------|--------|--------|---------|
| Login/Authentication | ✅ | On startup | API key validation |
| User Profile (Editable) | ✅ | Profile tab | Edit username, email, dept |
| Chat Search | ✅ | Chat tab | Hybrid semantic search |
| Document Upload | ✅ | Documents tab | Support: TXT, PDF, DOCX, MD |
| Real-Time Metrics | ✅ | Header bar | Cache %, latency, tokens, queries |
| Admin Dashboard | ✅ | Admin tab | System health & alerts |
| Cache Monitoring | ✅ | Cache tab | Hit rate, misses, performance |
| User Statistics | ✅ | My Stats tab | Personal usage analytics |
| Feedback Panel | ✅ | Feedback tab | Rate and comment on results |

---

## 🎯 Navigation

### Main Tabs (Sidebar)
```
1. Chat          → Semantic search + sources
2. Documents     → Upload and manage files
3. Profile       → View/edit user info (EDITABLE)
4. Feedback      → Rate search results
5. Cache         → Monitor caching performance
6. Monitoring    → Real-time system metrics
7. Admin         → Dashboard and analytics
8. My Stats      → Personal statistics
```

---

## 🔐 Authentication Flow

```
1. App opens
   ↓
2. Check localStorage for 'apiKey'
   ↓
3. If exists: Load app with session
   ↓
4. If not: Show login modal
   ↓
5. Enter API key (demo: sk-demo-key-12345)
   ↓
6. Click "Sign In"
   ↓
7. System validates against /api/user/profile
   ↓
8. Success: Store key + email, load app
   ↓
9. Error: Show error message, try again
```

---

## 💡 Login Tips

### Copy Demo Key
1. Open login modal
2. Scroll to "Demo API Key" box
3. Click copy icon 📋
4. Key auto-fills input field
5. Click "Sign In"

### Show/Hide Password
1. Click eye icon 👁️ on right of input
2. Toggle between hidden/visible
3. Password appears as dots when hidden

### API Information
1. Click "▶ Show API Information" at bottom
2. View security docs
3. See key generation guide
4. Click "▼ Hide" to collapse

---

## 📊 Real-Time Updates

### Metrics Bar (Refreshes Every 1 Second)
```
⚡ Cache Hit Rate: X.X%
⏱️  Avg Latency: Xms
🪙  Avg Tokens: X per search
📊 Total Queries: X
```

### Dashboard Refresh Rates
```
Document Count: Every 10 seconds
System Health: Every 5 seconds
Chunk Count: Every 10 seconds
Metrics: Every 1 second
```

---

## 🎨 Dark Mode

### Toggle
- Click sun/moon icon in header
- Preference saved automatically
- Applies to entire app

### Shortcuts
```
No keyboard shortcut (use button only)
```

---

## ✏️ Edit Profile

### Steps
```
1. Click "Profile" tab
2. Click "Edit Profile" button
3. Modify desired fields:
   - Username
   - Email
   - Department
4. Click "Save" to persist
5. Click "Cancel" to discard
```

### Fields
- **Username**: Any text
- **Email**: Valid email format
- **Department**: Department name
- **Role**: Read-only (admin/user)
- **Member Since**: Read-only (date)

---

## 🔍 Search

### Basic Search
```
1. Type question in chat box
2. Press Enter or click "Search"
3. Results appear in right panel
4. Answer generated below
```

### Example Queries
```
"What is Kubernetes?"
"How do I restart a pod?"
"Docker and containers"
"Python best practices"
```

### Filters
```
Department: Filter by department
Category: Filter by category
Date From: Start date
Date To: End date
```

---

## 📁 Document Management

### Upload Document
```
1. Click "Documents" tab
2. Click upload area or drag file
3. Select file (TXT, MD, PDF, DOCX)
4. Enter Department (e.g., "DevOps")
5. Enter Category (e.g., "Setup")
6. Click "Upload"
```

### Supported Formats
```
✅ TXT  - Plain text
✅ MD   - Markdown
✅ PDF  - PDF documents
✅ DOCX - Word documents
```

### Limits
```
Max file size: 10MB
Max files per upload: 1
Concurrent uploads: Allowed
```

---

## 📊 Dashboards

### Chat Dashboard
- Search interface
- Real-time source display
- Message history
- Quick suggestions

### Admin Dashboard
- System health score
- Total queries
- Average latency
- Active alerts
- Cache performance
- Feedback quality
- Rating distribution

### Monitoring Dashboard
- Real-time metrics
- Performance charts
- System status
- Resource usage

### Cache Dashboard
- Hit/miss rate
- Cache efficiency
- Performance metrics
- Clear cache option

### User Stats Dashboard
- Personal searches
- Generations performed
- Total queries
- Last activity

---

## 🔧 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Tab | Navigate between fields |
| Enter | Submit form / Search |
| Escape | Close modal (if applicable) |
| Ctrl+D | Toggle dark mode (not enabled) |

---

## 🆘 Troubleshooting

### Login Issues
```
Problem: "Invalid API key" error
Solution: Check key format (must start with 'sk-')
         Use demo key: sk-demo-key-12345

Problem: "Failed to authenticate"
Solution: Ensure backend is running on port 8003
         Check network connection
         Verify CORS enabled
```

### Profile Issues
```
Problem: Changes not saving
Solution: Check backend connection
         Verify API key is valid
         Check network in Dev Tools

Problem: Form won't submit
Solution: Fill all required fields
         Check for validation errors
```

### Search Issues
```
Problem: No results found
Solution: Upload documents first
         Try different keywords
         Check department filters

Problem: Slow search
Solution: Too many documents?
         Check system metrics
         Rebuild index
```

### Performance Issues
```
Problem: Slow metrics updates
Solution: Check network bandwidth
         Clear browser cache
         Reduce refresh frequency

Problem: High latency
Solution: Check backend load
         Reduce concurrent searches
         Scale up resources
```

---

## 📱 Mobile Usage

### Recommended
✅ Chat & search  
✅ View results  
✅ Edit profile  

### Works But Not Optimal
⚠️ Document upload (file picker)  
⚠️ Admin dashboard (many columns)  

### Not Recommended
❌ Load testing  
❌ Bulk operations  

---

## 🔒 Security

### Do's
```
✅ Keep API keys secret
✅ Use HTTPS in production
✅ Rotate keys regularly
✅ Use different keys per environment
✅ Enable 2FA if available
```

### Don'ts
```
❌ Share API keys publicly
❌ Commit keys to git
❌ Use same key for multiple services
❌ Store keys in code
❌ Log API keys
```

---

## 📞 Support

### Common Issues
- **Login not working**: Check backend status
- **No search results**: Upload documents first
- **Metrics not updating**: Check network
- **Profile edit fails**: Verify API key
- **Mobile issues**: Try desktop browser

### Backend Required Endpoints
```
GET  /api/user/profile              (Validate + get user)
PUT  /api/user/profile              (Update profile)
GET  /api/metrics                   (Real-time metrics)
GET  /api/documents                 (List documents)
POST /api/search                    (Hybrid search)
POST /api/ingest                    (Upload document)
GET  /api/health                    (System health)
```

---

## 📈 Performance Tips

### Faster Searches
1. Use specific keywords
2. Add filters (department, date)
3. Reduce top_k parameter
4. Index smaller documents

### Better Metrics
1. Perform multiple searches
2. Let caching work (repeat queries)
3. Monitor over time
4. Check dashboard regularly

### Efficient Uploads
1. Upload organized documents
2. Use consistent metadata
3. Batch similar documents
4. Clean text before upload

---

## 🚀 Advanced Features

### API Access
```bash
# Search with curl
curl -X POST "http://localhost:8003/api/search" \
  -H "X-API-Key: sk-demo-key-12345" \
  -d "query=kubernetes&top_k=10"

# Get metrics
curl -H "X-API-Key: sk-demo-key-12345" \
  http://localhost:8003/api/metrics
```

### Custom Integrations
```python
# Python
import requests

headers = {"X-API-Key": "sk-demo-key-12345"}
response = requests.get("http://localhost:8003/api/documents", headers=headers)
```

### Webhook Integration (Future)
```
Enable in settings
Configure endpoint
Subscribe to events
```

---

## 📚 Documentation

### Available Docs
- QUICK_START.md - 60-second setup
- README.md - Overview
- IMPLEMENTATION_SUMMARY.md - Detailed architecture
- EVALUATION_SCORECARD.md - Scoring breakdown
- PHASE_2_COMPLETION_SUMMARY.md - Latest features
- LOGIN_MODAL_ENHANCEMENT.md - Auth UI details

---

## 💾 Browser Storage

### Stored Data
```javascript
localStorage.apiKey      // API key (encrypted recommended)
localStorage.userEmail   // User email address
```

### Clear Session
```javascript
localStorage.removeItem('apiKey')
localStorage.removeItem('userEmail')
// Then refresh page
```

---

## 📅 Changelog

### Version 2.0 (Current)
- ✅ User authentication system
- ✅ Editable profiles
- ✅ Real-time data updates
- ✅ Enhanced login modal
- ✅ API key management

### Version 1.0 (Previous)
- PGVector integration
- Hybrid search (vector + BM25)
- HNSW indexing
- Dashboard views
- Document upload

---

## 🎯 Next Steps

1. Login with `sk-demo-key-12345`
2. Upload a test document
3. Perform a search
4. Edit your profile
5. Check metrics in real-time
6. Explore dashboards

---

## ✨ Tips & Tricks

### Pro Tips
- Use Ctrl+A to select all text in search
- Click suggestions for quick search
- Dark mode easier on eyes at night
- Logout from header anytime
- Copy API key from login modal

### Keyboard Navigation
- Tab to next field
- Shift+Tab to previous field
- Enter to submit
- Escape to close modals

### Browser DevTools
- F12 to open DevTools
- Network tab to monitor API calls
- Console to check errors
- Application tab to view localStorage

---

**Status**: ✅ Complete  
**Version**: 2.0  
**Last Updated**: June 4, 2026  
**Ready for**: Production Use
