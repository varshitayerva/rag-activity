# Verification Guide - Confidence Scoring Fix

## Test Scenarios

### Scenario 1: Correct Question on Matching Documents ✓
**Query:** "What is Kubernetes?"  
**Documents:** Kubernetes guide, K8s tutorial  

**Expected Result:**
- Confidence: 70-85% (HIGH)
- Hallucination Risk: 10-25% (LOW)
- Shows relevant information with sources

**What to Check:**
- ✓ Confidence is HIGH (>0.65)
- ✓ Sources display real document names
- ✓ Answer cites chunks properly

---

### Scenario 2: Wrong Question on Matching Documents ⚠️ CRITICAL TEST
**Query:** "What is Jupiter?" (or "How to cook pizza?")  
**Documents:** Kubernetes guide, Docker tutorial  

**Expected Result (After Fix):**
- Confidence: 20-30% (LOW) ← **This was the bug (was 40-42%)**
- Hallucination Risk: 100% or very high
- Message: "I don't have reliable information..."

**What to Check:**
- ✓ Confidence is LOW (<0.35)
- ✓ System says "I don't have reliable information"
- ✓ Hallucination risk is HIGH

**Failure Indicators:**
- ✗ Confidence > 40% = Fix didn't work
- ✗ Tries to answer about Jupiter = Hallucination issue
- ✗ System seems confident = Penalizing not strong enough

---

### Scenario 3: Partial Match
**Query:** "Docker networking best practices"  
**Documents:** Docker guide (with some networking), K8s docs  

**Expected Result:**
- Confidence: 40-65% (MEDIUM)
- Hallucination Risk: 25-50% (MEDIUM)
- Shows relevant information with warnings

**What to Check:**
- ✓ Confidence is MEDIUM
- ✓ Sources are relevant
- ✓ Warnings about incomplete information

---

### Scenario 4: Random Gibberish
**Query:** "xyz123 random garbage nonsense qwerty"  
**Documents:** Any documents  

**Expected Result:**
- Confidence: 20-25% (VERY LOW)
- Hallucination Risk: 95-100% (CRITICAL)
- Message: "I don't have reliable information..."

**What to Check:**
- ✓ Confidence is minimum/very low
- ✓ System refuses to answer
- ✓ High hallucination risk

---

## How to Verify the Fix

### Step 1: Test in UI
```
1. Open the application
2. Ask: "What is Jupiter?"
3. Observe confidence score
4. Expected: 20-30% (not 40-42%)
```

### Step 2: Check Logs
```bash
# Start backend with debug logging
tail -f <backend-logs>

# Look for:
Stricter BM25 penalties applied
Poor match on both vector AND BM25 - confidence severely reduced
Critically low match signal - confidence reduced
```

### Step 3: Verify Signal Breakdown
Logs should show:
```
Overall confidence: 0.24 | Vector=0.15 | BM25=0.12 | Quality=0.30 | Count=0.35 | Intent=0.40
Poor match on both vector AND BM25 - confidence severely reduced to 0.192
```

### Step 4: Database Check
Verify document names are displaying:
```
Source 1: Kubernetes Basics (not "Unknown")
Source 2: Docker Guide (not "Unknown")
```

---

## Regression Tests

### Check These Don't Break:
1. ✓ Normal Kubernetes questions still return 70%+ confidence
2. ✓ Docker questions still work correctly
3. ✓ Multi-document searches still function
4. ✓ Filters (department, category, date) still work
5. ✓ Response times not degraded

---

## Confidence Score Mappings (After Fix)

| Scenario | Score | Level | Indicator |
|----------|-------|-------|-----------|
| Perfect match | 0.75-0.95 | HIGH | ✓ Green dot, full answer |
| Good match | 0.65-0.75 | HIGH | ✓ Green dot, full answer |
| Partial match | 0.40-0.65 | MEDIUM | ⚠ Yellow dot, conditional answer |
| Poor match | 0.28-0.40 | MEDIUM-LOW | ⚠ Yellow/Red dot, disclaimer |
| No match | 0.20-0.28 | LOW | ✗ Red dot, "don't have info" |
| Wrong domain | 0.20-0.25 | VERY LOW | ✗ Red dot, refuses to answer |

---

## Known Edge Cases

### Case 1: Document with Keywords but Wrong Context
**Query:** "Pod deployment in Kubernetes"  
**Document:** Podcast guide (contains word "pod")  
**Expected:** 30-40% confidence (medium-low)
**Reason:** BM25 finds "pod" but context mismatch detected by semantic scoring

### Case 2: Typo in Query
**Query:** "Kubernetis cluster" (typo)  
**Expected:** 50-65% confidence (medium)
**Reason:** BM25 fuzzy matching still works somewhat

### Case 3: Acronym Variations
**Query:** "K8s configuration"  
**Expected:** 70%+ confidence (high)
**Reason:** Both "K8s" and "Kubernetes" match

---

## Performance Metrics to Track

### Before the Fix
- Wrong queries avg confidence: 55%
- Correct queries avg confidence: 72%
- User confusion: HIGH

### After the Fix (Expected)
- Wrong queries avg confidence: 25%
- Correct queries avg confidence: 78%
- User confusion: LOW

---

## Deployment Checklist

- [ ] Code deployed to staging
- [ ] Test Scenario 1 (correct question) ✓ passes
- [ ] Test Scenario 2 (wrong question) ✓ confidence < 0.30
- [ ] Test Scenario 3 (partial match) ✓ passes
- [ ] Test Scenario 4 (gibberish) ✓ passes
- [ ] Check logs for new penalty messages
- [ ] Verify document names display correctly
- [ ] Run regression tests
- [ ] Monitor for 48 hours in production
- [ ] Collect user feedback on confidence accuracy

---

## Troubleshooting

### Issue: Still getting 40%+ on wrong questions
**Solution:** Check if BM25 penalties are being applied. Look for logs showing BM25 score and confidence calculations.

### Issue: Correct queries getting low confidence
**Solution:** Check vector_confidence and bm25_confidence values. Both should be high for correct matches.

### Issue: Document names still showing "Unknown"
**Solution:** Verify postgres_client.py has the documents table JOIN, and rrf_fusion.py preserves the 'doc' field.

### Issue: Performance degradation
**Solution:** Check if new penalty logic is causing slowdowns. Penalties are just arithmetic, should be <1ms.

---

## Questions?

See:
- `CONFIDENCE_FIX_SUMMARY.md` - Technical details
- `CHANGES_OVERVIEW.md` - High-level overview
- Git commit `280c787` - Code changes with detailed explanation
