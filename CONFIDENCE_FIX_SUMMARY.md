# Confidence Scoring Fix - Summary

## Problem Identified
The system was returning confidence scores > 50% even when user queries **don't match** the provided documents.

### Root Causes
1. **High Default Initialization** — Confidence components initialized to 0.55-0.78, masking poor actual scores
2. **Artificial Confidence Floor** — `max(0.55, ...)` forced minimum confidence even for irrelevant queries
3. **No BM25 Penalty** — Low keyword matching scores weren't penalizing confidence
4. **No Sanity Check** — No mechanism to catch cases where BOTH semantic AND keyword matching failed

---

## Solution Implemented

### 1. Lower Initialization Defaults
**File:** `backend/app/search/hybrid_search.py:377-382`

**Before:**
```python
vector_confidence = 0.50      # Too high
bm25_confidence = 0.55        # Too high
quality_confidence = 0.60     # Too high
count_confidence = 0.55       # Too high
intent_confidence = 0.78      # Too high
```

**After:**
```python
vector_confidence = 0.25      # Low baseline
bm25_confidence = 0.25        # Low baseline
quality_confidence = 0.30     # Low baseline
count_confidence = 0.30       # Low baseline
intent_confidence = 0.40      # Low baseline
```

**Impact:** Prevents high confidence when actual signal values are poor

---

### 2. Penalize Low BM25 Scores
**File:** `backend/app/search/hybrid_search.py:399-420`

**New Logic:**
```python
max_bm25_score = bm25_results[0].get('score', 0)

# Penalty: if top result has very low BM25 score, penalize heavily
if max_bm25_score < 1.0:
    bm25_confidence *= 0.6  # Reduce confidence by 40%
elif max_bm25_score < 3.0:
    bm25_confidence *= 0.8  # Reduce confidence by 20%
```

**Mapping:**
- BM25 score 0 → confidence 0.09 (0.15 × 0.6)
- BM25 score 1 → confidence 0.12 (0.15 × 0.8)
- BM25 score 3 → confidence 0.32 (0.40 × 0.8)
- BM25 score 5+ → confidence 0.40+

**Impact:** Low keyword matches directly reduce confidence

---

### 3. Dual-Match Sanity Check
**File:** `backend/app/search/hybrid_search.py:491-495`

**New Logic:**
```python
# If BOTH semantic and keyword matching are weak, confidence must be low
if vector_confidence < 0.35 and bm25_confidence < 0.40:
    overall = overall * 0.60  # Penalize by 40%
    logger.warning(f"Poor match on both vector and BM25...")
```

**Impact:** Catches queries that don't match documents on ANY dimension

---

### 4. Lower Confidence Floor
**File:** `backend/app/search/hybrid_search.py:507`

**Before:**
```python
return max(0.55, min(0.95, overall))  # Min 55% confidence
```

**After:**
```python
return max(0.20, min(0.95, overall))  # Min 20% confidence
```

**Impact:** Allows truly low confidence scores to be returned

---

### 5. Fix Unknown Document Names
**Files:**
- `backend/app/search/postgres_client.py` — JOIN with documents table
- `backend/app/search/rrf_fusion.py` — Preserve 'doc' field

**Result:** Source cards now display actual document names instead of "Unknown"

---

## Expected Behavior After Fix

### Matched Query
```
Query: "What is Kubernetes?"
Documents: Kubernetes guide
Confidence: 0.75-0.85 (HIGH)
```

### Completely Mismatched Query
```
Query: "How to make pizza with pineapple?"
Documents: Kubernetes guide
Confidence: 0.20-0.35 (LOW)
```

### Random Gibberish
```
Query: "xyz123 garbage nonsense random"
Documents: Kubernetes guide
Confidence: 0.20-0.25 (VERY LOW)
```

---

## Testing

Run the confidence scoring test:
```bash
python test_confidence_fix.py
```

Expected results:
- ✓ Matched queries → HIGH confidence (>0.65)
- ✓ Mismatched queries → LOW confidence (<0.40)
- ✓ Random queries → VERY LOW confidence (<0.30)

---

## Logging

The system now logs confidence calculations with detailed breakdown:
```
Overall confidence: 0.32 | Vector=0.25 | BM25=0.15 | Quality=0.30 | Count=0.30 | Intent=0.40
Poor match on both vector and BM25 - confidence reduced to 0.192
```

This makes debugging confidence scores much easier.

---

## Backward Compatibility

The changes are backward compatible:
- Frontend sees the same `confidence_score` field
- Confidence range still 0-1, with HIGH/MEDIUM/LOW classifications
- No API changes required
