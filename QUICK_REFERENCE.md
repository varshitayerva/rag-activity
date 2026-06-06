# Hallucination Controls - Quick Reference

## 🎯 What It Does

Prevents the LLM from making up facts by validating answers at **3 stages**:
1. **Retrieval**: Only use coherent, confident document chunks
2. **Generation**: Force citations, detect uncertain language
3. **Frontend**: Show confidence levels to users

## ⚡ Quick Start

### For Backend Developers

**Check hallucination risk in responses:**
```python
response = await apiClient.generate(query, top_k=10)
# Response includes:
# - hallucination_risk: 0-1 (0 = safe, 1 = risky)
# - risk_level: "LOW" | "MEDIUM" | "HIGH"
# - validation.citation_validation.citation_rate: % of claims cited
```

**Adjust confidence threshold:**
```python
# In backend/app/search/routes.py - line 232
confidence_threshold: float = 0.5  # Default
# Change to 0.6 for stricter safety
# Change to 0.4 for more coverage
```

**Add custom forbidden phrases:**
```python
# In backend/app/hallucination_control.py
FORBIDDEN_PATTERNS = [
    r"\bI believe\b",  # Existing
    r"\byour custom pattern\b",  # Add yours
]
```

### For Frontend Developers

**Display risk to users:**
```jsx
// In ChatPanel.jsx - already implemented!
{msg.risk_level === 'HIGH'
  ? <RedWarning>High accuracy risk</RedWarning>
  : msg.risk_level === 'MEDIUM'
  ? <YellowWarning>Review sources</YellowWarning>
  : <GreenOk>Low risk</GreenOk>}
```

**Show hallucination warning:**
```jsx
if (response.hallucination_risk > 0.6) {
  showWarning("This answer may contain inaccuracies. Please review sources.")
}
```

## 📊 Key Numbers

| Metric | Meaning |
|--------|---------|
| `confidence_score: 0.75` | Search found good matches (75% confident) |
| `hallucination_risk: 0.25` | Answer has 25% risk of inaccuracy |
| `citation_rate: 0.9` | 90% of claims are properly cited |
| `coherence_score: 0.85` | Source chunks are coherent (about same topic) |

## 🚨 Risk Levels

| Level | Risk Score | Action |
|-------|-----------|--------|
| **LOW** | < 0.3 | Show answer, green badge |
| **MEDIUM** | 0.3-0.6 | Show answer + "Review sources" warning |
| **HIGH** | > 0.6 | Block answer or show strong warning |

## 🔍 How to Debug

### Query returned "I don't know" but should work?
```python
# Check search confidence
print(f"Confidence: {response['confidence_score']}")
# If < 0.5, retrieval found no good matches
# Try: make query more specific, adjust filters
```

### Answer shows HIGH hallucination risk?
```python
# Check validation details
print(response['validation']['citation_validation'])
# If citation_rate < 0.7, claims not well-cited
# Fix: LLM prompt or source quality issue
```

### Answer has [UNCERTAIN] tags?
```python
# This is intentional - LLM marked uncertain claims
# Review those sections carefully
```

## 🧪 Quick Test

```bash
# Test confidence thresholding
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what is the answer to life the universe and everything",
    "confidence_threshold": 0.5
  }'

# Should return: "I don't have reliable information..."
# And: hallucination_risk: 1.0
```

## 🔧 Common Customizations

### Make it stricter (fewer answers, lower hallucination):
```python
# In routes.py
confidence_threshold = 0.6  # Up from 0.5
```

### Make it more permissive (more answers, slightly riskier):
```python
confidence_threshold = 0.4  # Down from 0.5
```

### Reduce false positives for forbidden phrases:
```python
# In hallucination_control.py
'forbidden_phrases': min(len(violations) * 0.05, 1.0),  # Down from 0.2
```

### Make coherence check stricter:
```python
is_coherent = coherence_score > 0.7  # Up from 0.6
```

## 📡 API Response Template

```json
{
  "answer": "...",
  "confidence_score": 0.75,
  "hallucination_risk": 0.25,
  "risk_level": "LOW",
  "validation": {
    "citation_validation": {
      "citation_rate": 0.9,
      "uncited_claims": 1,
      "total_claims": 10
    },
    "source_coherence": {
      "is_coherent": true,
      "score": 0.92
    },
    "forbidden_violations": [],
    "recommendation": "LOW RISK: Answer is well-grounded..."
  }
}
```

## 🎓 Key Concepts

**Confidence Score** = Search quality (do we have good docs?)
- Based on vector similarity, BM25 match, result count
- If < 0.5 → block and return safe "I don't know"

**Hallucination Risk** = Answer quality (does LLM make stuff up?)
- Based on citations, forbidden phrases, coherence
- If > 0.6 → mark as HIGH RISK

**Citation Rate** = % of answer claims that cite sources
- Target: > 0.7 (70% of claims cited)
- < 0.7 → signal MEDIUM RISK

**Coherence** = Are source chunks about same topic?
- Score > 0.6 → coherent ✅
- Score < 0.6 → incoherent (scattered) ⚠️

## 📞 Support

**Questions?** Check:
1. [HALLUCINATION_CONTROLS.md](HALLUCINATION_CONTROLS.md) - Full documentation
2. [backend/app/hallucination_control.py](backend/app/hallucination_control.py) - Source code
3. Logs: `DEBUG` level shows detailed validation steps
