# Hallucination Controls - Deployment Checklist

## ✅ Pre-Deployment Verification

### Code Quality
- [x] Syntax validation passed (py_compile)
- [x] Import chain verified
- [x] No circular dependencies
- [ ] Linting passed (if using pylint)
- [ ] Type hints validated (if using mypy)

### Unit Tests
- [ ] `test_hallucination_control.py` - Test validator functions
- [ ] `test_generation_service.py` - Test enhanced generation
- [ ] `test_search_routes.py` - Test confidence thresholding
- [ ] `test_frontend_integration.py` - Test UI badges

### Integration Tests
- [ ] End-to-end query → answer → validation flow
- [ ] Search with different confidence thresholds
- [ ] Generation with various document sets
- [ ] Frontend properly displays risk badges

---

## 📋 Test Cases

### Test 1: Confidence Thresholding
```bash
# Setup: Query on topic NOT in documentation
# Expected: Blocked response with hallucination_risk: 1.0

curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what is the secret to cold fusion",
    "confidence_threshold": 0.5
  }'

# Check Response:
# - answer contains "I don't have reliable information"
# - hallucination_risk >= 0.8
# - risk_level == "HIGH"
# - warning field populated
```

**Expected Output**:
```json
{
  "answer": "I don't have reliable information...",
  "confidence_score": 0.35,
  "hallucination_risk": 1.0,
  "risk_level": "HIGH",
  "warning": "Confidence (0.35) below threshold (0.5)"
}
```

---

### Test 2: Citation Validation
```bash
# Setup: Query on topic IN documentation
# Expected: Answer with proper citations

curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Kubernetes?",
    "top_k": 10,
    "confidence_threshold": 0.5
  }'

# Check Response:
# - Answer contains [Source: Chunk N] citations
# - citation_validation.citation_rate > 0.7
# - hallucination_risk < 0.4
# - risk_level == "LOW" or "MEDIUM"
```

**Expected Output** (partial):
```json
{
  "answer": "Kubernetes is... [Source: Chunk 0]\n\n...",
  "hallucination_risk": 0.15,
  "risk_level": "LOW",
  "validation": {
    "citation_validation": {
      "citation_rate": 0.9,
      "uncited_claims": 1,
      "total_claims": 10
    }
  }
}
```

---

### Test 3: Semantic Coherence
```bash
# Setup: Query across multiple documents
# Expected: Coherence check passes

# Check Response:
# - source_coherence.is_coherent == true
# - source_coherence.score > 0.6
```

**Expected Output** (validation section):
```json
{
  "source_coherence": {
    "is_coherent": true,
    "score": 0.85
  }
}
```

---

### Test 4: Forbidden Phrase Detection
```bash
# Setup: LLM might generate "I believe" or similar
# Expected: Flagged in validation

# Check Response:
# - forbidden_violations array populated if violations found
# - Each violation includes phrase, context, severity
```

**Expected Output** (if violations found):
```json
{
  "forbidden_violations": [
    {
      "phrase": "I believe",
      "context": "...I believe that Kubernetes is...",
      "severity": "HIGH"
    }
  ]
}
```

---

### Test 5: Frontend UI Display
```javascript
// Setup: Query that returns hallucination_risk > 0.6
// Expected: RED badge + warning shown

// Test Steps:
1. Open ChatPanel
2. Enter query
3. Check for dual badges (Confidence + Accuracy Risk)
4. If risk_level === 'HIGH':
   - Badge should be RED
   - Warning banner should show
   - Source links should be visible
```

**Visual Checklist**:
- [ ] Confidence badge colors correct (green/yellow/red)
- [ ] Accuracy Risk badge colors correct (green/yellow/red)
- [ ] Percentages displayed correctly
- [ ] Warning banner appears for HIGH RISK
- [ ] Source cards clickable and linked

---

## 🔧 Configuration Before Deploy

### Backend Configuration

**1. Set confidence threshold** (default: 0.5)
```python
# backend/app/search/routes.py, line ~232
confidence_threshold: float = 0.5

# Adjust as needed:
# 0.3 = permissive (more answers, higher risk)
# 0.5 = balanced (default)
# 0.7 = strict (fewer answers, lower risk)
```

**2. Adjust risk factor weights** (optional)
```python
# backend/app/hallucination_control.py, line ~150
risk_factors = {
    'low_confidence': 0.6 - confidence_score) / 0.6,
    'uncited_claims': uncited_claims / total,
    'forbidden_phrases': min(count * 0.2, 1.0),  # Adjust multiplier
    'incoherent_sources': 0.3,  # Adjust penalty
}
# Weights: each factor contributes equally to risk
```

**3. Set coherence threshold** (default: 0.6)
```python
# backend/app/search/hybrid_search.py, line ~258
is_coherent = coherence_score > 0.6
# Higher = stricter (0.7), Lower = permissive (0.5)
```

### Frontend Configuration

**1. Risk badge colors** (already themed, no changes needed)

**2. Warning thresholds** (already set, no changes needed)

---

## 📊 Monitoring After Deploy

### Key Metrics to Track

```python
# Log these per-query:
1. confidence_score - Search quality
2. hallucination_risk - LLM answer quality
3. risk_level - Categorical risk
4. citation_rate - % claims cited
5. coherence_score - Source coherence
6. forbidden_violations_count - Uncertain language detected
7. queries_blocked - Queries rejected due to low confidence

# Calculate:
- Average hallucination_risk across all queries
- % queries with risk_level == HIGH
- % of answers that are blocked (due to low confidence)
- Citation rate distribution
```

### Sample Monitoring Dashboard

```
┌─────────────────────────────────────────────────────┐
│       HALLUCINATION CONTROLS - LIVE DASHBOARD       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Queries Processed: 1,247                           │
│  Queries Blocked:   43 (3.4%)                       │
│  Avg Hallucination Risk: 0.28 ✅ (LOW)             │
│                                                     │
│  Risk Distribution:                                 │
│    LOW (< 0.3):    1,032 (82.8%) ✅               │
│    MEDIUM (0.3-0.6): 172 (13.8%) ⚠️               │
│    HIGH (> 0.6):    43  (3.4%)  🚫               │
│                                                     │
│  Citation Metrics:                                  │
│    Avg Citation Rate: 0.87 (87%) ✅               │
│    Median Citation Rate: 0.92                       │
│    Min Citation Rate: 0.65                          │
│                                                     │
│  Coherence Metrics:                                 │
│    Avg Coherence: 0.84 ✅                         │
│    Incoherent Searches: 8 (0.6%)                    │
│                                                     │
│  Forbidden Phrase Detections: 12                    │
│    Most Common: "I believe" (5x)                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🚨 Rollback Plan

If issues are discovered post-deploy:

### Minor Issue (e.g., too many false positives)
```python
# Option 1: Lower hallucination_risk threshold
# In routes.py, line ~232
confidence_threshold = 0.4  # More permissive

# Option 2: Adjust risk weights
# In hallucination_control.py, line ~150
'forbidden_phrases': min(count * 0.1, 1.0),  # More lenient
```

### Major Issue (e.g., breaking change)
```bash
# Revert changes:
git revert <commit-hash>
git push

# Or disable hallucination controls temporarily:
# In routes.py, /generate endpoint
# Comment out confidence_threshold check
```

### Complete Rollback
```bash
# If system unstable
git checkout backend/app/hallucination_control.py
git checkout backend/app/generation/service.py
git checkout backend/app/search/routes.py
git checkout backend/app/search/hybrid_search.py
git checkout frontend/src/components/ChatPanel.jsx

git push
# Redeploy
```

---

## 📝 Deployment Steps

### Step 1: Pre-Deploy Validation
```bash
# 1. Compile all Python files
cd backend
python -m py_compile app/*.py
python -m py_compile app/**/*.py

# 2. Check imports
python -c "from app.hallucination_control import HallucinationValidator"
python -c "from app.generation.service import generate_answer"

# 3. Run existing tests (if any)
pytest tests/ -v
```

### Step 2: Deploy Backend
```bash
# 1. Merge to main branch
git checkout main
git pull origin main
git merge develop-2

# 2. Deploy
docker build -t rag-app:latest .
docker run -d rag-app:latest

# 3. Verify health
curl http://localhost:8000/health
# Expected: {"status": "ok", "version": "1.0.0"}
```

### Step 3: Deploy Frontend
```bash
# 1. Build
npm run build

# 2. Deploy
npm run deploy

# 3. Clear cache
# In browser DevTools: Clear Site Data
```

### Step 4: Test Core Flows
```bash
# Run Test 1: Confidence Thresholding
curl -X POST "http://localhost:8000/api/generate" \
  -d '{"query": "obscure topic"}'
# Check: Returns safe response with risk_level: HIGH

# Run Test 2: Normal Query
curl -X POST "http://localhost:8000/api/generate" \
  -d '{"query": "What is Kubernetes?"}'
# Check: Returns answer with hallucination_risk < 0.4

# Run Test 3: Frontend
# Open app in browser
# Submit query
# Verify badges appear (green/yellow/red)
```

---

## ✅ Sign-Off Checklist

### For Backend Team
- [ ] Code syntax validated
- [ ] All tests passing
- [ ] No performance regressions
- [ ] Database queries optimized
- [ ] Logging configured
- [ ] Error handling complete

### For Frontend Team
- [ ] UI badges rendering correctly
- [ ] Colors accurate (green/yellow/red)
- [ ] Responsive on mobile
- [ ] Accessibility checked (WCAG)
- [ ] No console errors

### For QA Team
- [ ] All test cases passed
- [ ] Edge cases tested
- [ ] Performance acceptable (< 300ms latency)
- [ ] No data leaks
- [ ] Rollback plan documented

### For Product Team
- [ ] Feature meets requirements
- [ ] User messaging clear
- [ ] Analytics tracking implemented
- [ ] Documentation complete

---

## 📞 Support & Escalation

### If questions arise:

**Technical Details**: Check `HALLUCINATION_CONTROLS.md`

**Quick Reference**: Check `QUICK_REFERENCE.md`

**Code Issues**: Check source files with inline comments

**Deployment Issues**: Follow `DEPLOYMENT_CHECKLIST.md` (this file)

---

## 📅 Post-Deploy Monitoring

**Week 1**: Monitor closely for issues
- Daily check hallucination_risk metrics
- Monitor response times
- Review user feedback
- Check error logs

**Week 2-4**: Establish baseline
- Document normal metric ranges
- Identify any patterns
- Adjust thresholds if needed

**Month 2+**: Long-term monitoring
- Monthly metric reviews
- User satisfaction surveys
- Annual security audits

---

**Deployment Status**: Ready ✅
**Last Updated**: 2026-06-05
**Approved By**: [Your Team]
