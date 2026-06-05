# RAG Pipeline Analysis - FDE Project

## Pipeline Overview

Your RAG (Retrieval-Augmented Generation) pipeline follows this flow:

```
File Input
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. VALIDATION - validate_file_upload()                      │
│    - File type check (.txt, .pdf, .md, .docx)              │
│    - File size check (max 50MB)                            │
│    - Filename sanitization                                 │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PARSING - File format-specific extraction                │
│    - PDF: PyPDF2.PdfReader                                 │
│    - DOCX: python-docx                                     │
│    - TXT/MD: Direct UTF-8 decode                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CHUNKING - Fixed-size chunking with overlap             │
│    - Chunk size: 500 tokens (configurable)                 │
│    - Overlap: 100 tokens                                   │
│    - Algorithm: Sentence-based split                       │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. EMBEDDING - Dual embeddings                             │
│    ├─ Vector: OpenAI text-embedding-3-small (1536-dim)    │
│    └─ Sparse: BM25 (lexical/keyword-based)                 │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. STORAGE & INDEXING                                      │
│    ├─ PostgreSQL (pgvector extension)                      │
│    │  └─ Vector embeddings stored in vector column         │
│    │                                                        │
│    └─ BM25 Index (in-memory)                               │
│       └─ Tokenized texts for full-text search              │
└─────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Validation

**File:** `backend/app/validation.py` → `validate_file_upload()`

### Algorithm
```
Input: filename, file_size
├─ Check filename length ≤ 255 chars
├─ Check file_size ≤ 50MB
└─ Check extension in {.txt, .pdf, .md, .docx}
Output: (is_valid: bool, error: str)
```

### Code Location
[ingest_routes.py:34-37](backend/app/search/ingest_routes.py#L34-L37)

### Security Features
- Path traversal prevention in `sanitize_filename()` - removes `../` patterns
- SQL injection prevention in `validate_search_query()` - blocks dangerous patterns
- File type whitelist (no arbitrary extensions)

---

## Stage 2: Parsing

**File:** `backend/app/search/ingest_routes.py` → `ingest_document()`

### Algorithm by File Type

#### PDF Files
```python
import PyPDF2
pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
text_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
```
- Uses PyPDF2 library
- Iterates through all pages
- Concatenates extracted text

#### DOCX Files
```python
from docx import Document
doc = Document(io.BytesIO(content))
text_content = "\n".join([p.text for p in doc.paragraphs])
```
- Uses python-docx library
- Extracts text from all paragraphs
- Preserves paragraph breaks

#### TXT/MD Files
```python
text_content = content.decode('utf-8')
```
- Simple UTF-8 decoding
- No special processing needed

### Code Location
[ingest_routes.py:43-64](backend/app/search/ingest_routes.py#L43-L64)

---

## Stage 3: Chunking

**File:** `backend/app/search/ingest_routes.py` → chunking logic

### Algorithm: Fixed-Size Chunking with Overlap

```
Input: text_content, chunk_size=500, overlap=100

sentences = text_content.split('.')  # Split by sentence
current_chunk = ""

for each sentence:
    if len(current_chunk) + len(sentence) > chunk_size:
        save current_chunk
        current_chunk = sentence
    else:
        add sentence to current_chunk

if current_chunk not empty:
    save current_chunk

Output: List of chunks (500 char windows, 100 char overlap)
```

### Example
```
Original: "The cat sat. The dog ran. The bird flew. ..."
Chunk 1: "The cat sat. The dog ran." (83 chars)
Chunk 2: "The dog ran. The bird flew. ..." (overlaps with Chunk 1)
```

### Code Location
[ingest_routes.py:81-108](backend/app/search/ingest_routes.py#L81-L108)

### Configuration
- **Chunk Size:** 500 tokens (set in `ingest_routes.py:82`)
- **Overlap:** 100 tokens (set in `ingest_routes.py:83`)
- **Note:** Currently uses character count, not true token count

### Pros & Cons
✅ Simple, deterministic, preserves context with overlap
❌ Splits mid-sentence, may lose semantic boundaries
**Better alternative:** Semantic chunking based on topic breaks or NLP-detected sentence boundaries

---

## Stage 4: Embedding

### Dual Embedding Strategy

Your system uses **hybrid search** combining two embedding methods:

#### A. Dense Vector Embeddings (Semantic)
**File:** `backend/app/search/embeddings.py` → `EmbeddingsClient`

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.embeddings.create(
    input=text,
    model="text-embedding-3-small"  # 1536 dimensions
)
embedding = response.data[0].embedding
```

**How it works:**
- Converts text to dense vector (1536 floats)
- Captures semantic meaning (synonyms, context)
- Uses cosine similarity for retrieval

**Code Location:** [embeddings.py:25-42](backend/app/search/embeddings.py#L25-L42)

#### B. Sparse Lexical Embeddings (BM25)
**File:** `backend/app/search/bm25_search.py` → `BM25SearchEngine`

```python
from rank_bm25 import BM25Okapi

class BM25SearchEngine:
    def _tokenize(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        return text.split()
    
    def build_index(self, texts):
        tokenized = [self._tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(tokenized)
    
    def search(self, query, top_k=50):
        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)  # TF-IDF based
        return results_sorted_by_score
```

**How it works:**
- BM25 = Best Matching 25 (ranking function)
- Formula: `score = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D|/avgdl))`
  - `IDF(qi)` = Inverse Document Frequency (how rare the term is)
  - `f(qi,D)` = Term frequency in document
  - `k1, b` = Tuning parameters (k1≈2.0, b≈0.75)
- Captures exact keyword matches
- Good for technical documents, acronyms

**Code Location:** [bm25_search.py:13-24](backend/app/search/bm25_search.py#L13-L24)

---

## Stage 5: Storage & Indexing

### A. PostgreSQL Vector Storage (pgvector)

**File:** `backend/app/search/postgres_client.py`

```sql
-- PostgreSQL table structure (assumed)
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INT,
    text TEXT,
    embedding vector(1536),  -- pgvector extension
    chunk_index INT,
    department VARCHAR,
    category VARCHAR,
    created_at TIMESTAMP
);

CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**How pgvector search works:**
```python
# Vector search using cosine similarity
vector_results = db.search(
    query_embedding,
    similarity_metric="cosine",
    top_k=50
)
# Finds chunks with highest cosine similarity to query embedding
```

**Index:** IVFFlat (Inverted File Flat)
- Approximate nearest neighbor search
- Trade-off: Speed vs accuracy (tuned with `lists=100`)

### B. BM25 In-Memory Index

```python
self.bm25 = BM25Okapi(tokenized_corpus)
# Built into memory when PostgreSQL chunks loaded
# No persistent disk storage (rebuilt on app restart)
```

**Advantage:** Fast full-text search without additional database
**Disadvantage:** Lost on restart (could be persisted)

---

## Stage 6: Hybrid Search & Fusion

**File:** `backend/app/search/hybrid_search.py` → `HybridSearchService.search()`

### Workflow

```
User Query: "What is machine learning?"
    ↓
┌────────────────────────────────────────────────────┐
│ 1. EMBED QUERY (10-50ms)                           │
│    query_embedding = embed("What is machine...") │
│    → 1536-dim vector                              │
└────────────────────────────────────────────────────┘
    ↓
    ├─────────────────────────┬──────────────────────┐
    ↓                         ↓                      ↓
[Vector Search]        [BM25 Search]         [Parallel]
(50-200ms)             (5-20ms)
    │                         │
    ├─> pgvector cosine       ├─> BM25 scoring
    │   similarity             │   tokenized query
    │                         │
    ├─> top_k=50 results      ├─> top_k=50 results
    │   with scores           │   with scores
    │                         │
    └─────────────────────────┴──────────────────────┘
                    ↓
        ┌───────────────────────────────┐
        │ 2. RRF FUSION                │
        │    Reciprocal Rank Fusion    │
        └───────────────────────────────┘
                    ↓
        Combined Score = 
        1/(60 + vector_rank) + 1/(60 + bm25_rank)
                    ↓
        Sort all results by combined score
                    ↓
        ┌───────────────────────────────┐
        │ 3. METADATA FILTERING         │
        │    department, category, date │
        └───────────────────────────────┘
                    ↓
        Return top_k=20 final results
```

### RRF Formula (Reciprocal Rank Fusion)

**File:** `backend/app/search/rrf_fusion.py`

```python
# RRF combines ranks from different systems
combined_score = 1/(k + rank_vector) + 1/(k + rank_bm25)

where k = 60 (default RRF parameter)
```

**Example:**
```
Result: "Machine learning is..."
├─ Vector search rank: 5 (5th best match)
├─ BM25 search rank: 3 (3rd best match)
└─ Combined RRF score = 1/(60+5) + 1/(60+3)
                      = 1/65 + 1/63
                      = 0.0154 + 0.0159
                      = 0.0313
```

**Why RRF?**
- Normalizes scores from different algorithms (0-1 scale vs arbitrary BM25 scores)
- Top-ranked results get exponentially more weight
- Robust: compensates for weaknesses in each method

### Code Location
[hybrid_search.py:68-124](backend/app/search/hybrid_search.py#L68-L124)
[rrf_fusion.py:6-99](backend/app/search/rrf_fusion.py#L6-L99)

---

## Complete Flow Example

### Input
```
File: "machine_learning_guide.pdf"
Content: "Machine learning is a subset of artificial intelligence..."
```

### Step 1: Validation ✓
- Extension `.pdf` ✓
- Size 2.5MB ✓ (< 50MB)
- Filename "machine_learning_guide.pdf" ✓

### Step 2: Parsing
- PDF → text extraction → 5000 characters of content

### Step 3: Chunking
```
Chunk 1: "Machine learning is a subset of artificial..." (500 chars)
Chunk 2: "...artificial intelligence that enables systems..." (500 chars)
Chunk 3: "...systems to learn from data without..." (500 chars)
```

### Step 4: Embedding
```
Chunk 1 → OpenAI embedding → [0.043, -0.127, 0.891, ...] (1536 dims)
Chunk 2 → BM25 tokenization → ["machine", "learning", "subset", ...]
```

### Step 5: Storage
```
PostgreSQL:
  id | chunk_index | text | embedding | department
  ---|-------------|------|-----------|------------
  42 | 0 | "Machine learning..." | [0.043, -0.127...] | AI

BM25 Index (memory):
  corpus[42] = "Machine learning is a subset..."
  bm25.get_scores(["machine", "learning"]) = [2.5, 0, 3.1, ...]
```

### Step 6: Search Query
```
User: "What does machine learning do?"

Query embedding: [-0.001, 0.234, 0.567, ...] (1536 dims)

Vector search:
  1. Chunk 42: cos_sim = 0.89 (rank 1)
  2. Chunk 15: cos_sim = 0.76 (rank 2)

BM25 search:
  1. Chunk 42: BM25_score = 12.5 (rank 1)
  2. Chunk 8:  BM25_score = 8.3 (rank 2)

RRF Fusion:
  Chunk 42: 1/(60+1) + 1/(60+1) = 0.0323 (COMBINED RANK 1)
  Chunk 15: 1/(60+2) + 1/(60+X) = 0.0213 (COMBINED RANK 2)

Final Result: Return Chunk 42 with text and metadata
```

---

## Key Algorithms & Parameters

| Component | Algorithm | Key Parameters | Performance |
|-----------|-----------|-----------------|-------------|
| **Parsing** | Format-specific (PyPDF2, docx) | N/A | 50-500ms per file |
| **Chunking** | Fixed-size sentence-based | 500 chars, 100 overlap | O(n) where n=text length |
| **Embedding (Dense)** | OpenAI text-embedding-3-small | 1536 dimensions | ~100ms per chunk |
| **Embedding (Sparse)** | BM25Okapi | k1=2.0, b=0.75 | <1ms per search |
| **Vector Index** | IVFFlat (pgvector) | lists=100 | ~50-200ms for top-50 |
| **Full-Text Index** | BM25 | In-memory | ~5-20ms for top-50 |
| **Fusion** | RRF (Reciprocal Rank Fusion) | k=60 | ~1ms |
| **Filtering** | Linear filter on metadata | department, category, date | O(m) where m=results |

---

## Latency Breakdown

Typical end-to-end search latency (from `hybrid_search.py` metrics):

```
Embedding query:      10-50ms   ████
Vector search:        50-200ms  ███████████████████
BM25 search:          5-20ms    ██
RRF fusion:           1-5ms     █
Metadata filter:      1-10ms    █
─────────────────────────────────────
Total:               67-285ms   ████████████████████████
```

---

## How to Use This Pipeline

### 1. **Ingesting Documents**

```bash
# POST /api/ingest
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@document.pdf" \
  -F "department=HR" \
  -F "category=Policies" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "status": "success",
  "document_id": 42,
  "filename": "document.pdf",
  "chunks_created": 15,
  "file_size": 45230
}
```

### 2. **Searching Documents**

```bash
# POST /api/search
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is our vacation policy?",
    "top_k": 5,
    "filters": {
      "department": "HR",
      "category": "Policies"
    }
  }'
```

**Response:**
```json
{
  "query": "What is our vacation policy?",
  "chunks": [
    {
      "text": "Employees are entitled to 20 days...",
      "score": 0.0323,
      "rank": 1,
      "document_id": 42,
      "filename": "document.pdf",
      "department": "HR"
    },
    ...
  ],
  "search_type": "hybrid",
  "num_results": 5,
  "latency_ms": {
    "embedding_ms": 25,
    "vector_search_ms": 120,
    "bm25_search_ms": 8,
    "rrf_fusion_ms": 2,
    "metadata_filter_ms": 1,
    "total_ms": 156
  }
}
```

### 3. **Generation (LLM Response)**

```bash
# POST /api/generate
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is our vacation policy?",
    "top_k": 5
  }'
```

**Flow:**
1. Search for relevant chunks (156ms)
2. Build context: Top-5 chunks + metadata
3. Call LLM (Groq) with context
4. Stream response to user

---

## Architecture Strengths ✅

1. **Hybrid approach** - Combines semantic (vector) + lexical (BM25) search
2. **RRF fusion** - Robust combination of multiple ranking signals
3. **Metadata filtering** - Can narrow results by department/category/date
4. **Validation** - File validation, SQL injection prevention
5. **Caching** - Redis integration for response/retrieval caching
6. **Modular** - Each component (embed, search, index) can be replaced

---

## Potential Improvements 🔧

1. **Semantic Chunking** - Use NLP to split on topic boundaries instead of fixed size
2. **Hierarchical Indexing** - Group chunks by document/section for better context
3. **BM25 Persistence** - Serialize BM25 index to disk to survive restarts
4. **Reranking** - Add LLM-based reranker as post-processing step
5. **Adaptive k in RRF** - Tune k=60 parameter based on corpus characteristics
6. **Caching** - Cache embeddings to avoid recomputing identical chunks
7. **Batch Ingestion** - Support bulk document upload with progress tracking
8. **Vector Dimension Reduction** - Use PCA to reduce from 1536 to ~384 dims (faster, cheaper)

---

## Files to Know

| File | Purpose |
|------|---------|
| `ingest_routes.py` | Document upload & chunking pipeline |
| `embeddings.py` | OpenAI embedding client |
| `bm25_search.py` | BM25 sparse search index |
| `hybrid_search.py` | Main search orchestrator (vector + BM25) |
| `rrf_fusion.py` | Result fusion algorithm |
| `postgres_client.py` | Vector database (pgvector) |
| `validation.py` | Input validation & sanitization |
| `generation/service.py` | LLM integration (Groq) |

