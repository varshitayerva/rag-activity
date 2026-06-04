#!/usr/bin/env python3
"""Test script to diagnose search issues."""

import os
import sys

# Fix Windows encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'varsh'
os.environ['DB_NAME'] = 'fde_rag'

from backend.app.database.postgres import db_client
from backend.app.search.embeddings import EmbeddingsClient
from backend.app.search.bm25_search import BM25SearchEngine

print("=" * 60)
print("RAG PIPELINE DIAGNOSTIC TEST")
print("=" * 60)

# Test 1: Check database connection
print("\n[1] Database Connection")
try:
    docs = db_client.list_documents()
    print(f"[OK] Connected to PostgreSQL")
    print(f"  Documents: {len(docs)}")
    for doc in docs[:3]:
        print(f"    - {doc.get('filename')} (ID: {doc.get('id')})")
except Exception as e:
    print(f"[ERROR] Database error: {e}")
    sys.exit(1)

# Test 2: Check chunks
print("\n[2] Chunks in Database")
try:
    chunks = db_client.get_all_chunks()
    print(f"[OK] Total chunks: {len(chunks)}")
    if chunks:
        print(f"  Sample: {chunks[0]['text'][:80]}...")
        print(f"  Has embedding: {chunks[0].get('embedding') is not None}")
except Exception as e:
    print(f"[ERROR] Chunks error: {e}")

# Test 3: Test embeddings
print("\n[3] OpenAI Embeddings")
try:
    embeddings = EmbeddingsClient(use_cache=False)
    test_embedding = embeddings.embed_query("test")
    print(f"[OK] Embeddings working")
    print(f"  Dimension: {len(test_embedding)}")
    print(f"  Sample values: {test_embedding[:3]}")
except Exception as e:
    print(f"[ERROR] Embeddings error: {e}")

# Test 4: Test BM25
print("\n[4] BM25 Index")
try:
    bm25 = BM25SearchEngine()
    if chunks:
        texts = [chunk['text'] for chunk in chunks]
        bm25.build_index(texts, chunks)
        print(f"[OK] BM25 index built")
        print(f"  Corpus size: {bm25.get_corpus_size()}")

        # Test search
        bm25_results = bm25.search("docker", top_k=5)
        print(f"  BM25 search for 'docker': {len(bm25_results)} results")
        if bm25_results:
            print(f"    - Top result: {bm25_results[0]['text'][:60]}...")
    else:
        print("[ERROR] No chunks available to build BM25 index")
except Exception as e:
    print(f"[ERROR] BM25 error: {e}")

# Test 5: Test Vector Search (PostgreSQL)
print("\n[5] Vector Search (PostgreSQL + pgvector)")
try:
    if chunks:
        query_embedding = embeddings.embed_query("docker")
        # Try to search directly via postgres_client
        from backend.app.search.postgres_client import PostgresVectorDB
        vector_db = PostgresVectorDB()
        vector_results = vector_db.search(query_embedding, top_k=5)
        print(f"[OK] Vector search working")
        print(f"  Results for 'docker': {len(vector_results)} results")
        if vector_results:
            print(f"    - Top result score: {vector_results[0].get('score', 'N/A')}")
    else:
        print("[ERROR] No chunks to search")
except Exception as e:
    print(f"[ERROR] Vector search error: {e}")

# Test 6: Test Full Hybrid Search
print("\n[6] Hybrid Search (Vector + BM25 + RRF)")
try:
    from backend.app.search.hybrid_search import HybridSearchService
    hybrid = HybridSearchService()
    import asyncio
    results = asyncio.run(hybrid.search("docker", top_k=5))
    print(f"[OK] Hybrid search working")
    print(f"  Results: {len(results.get('chunks', []))}")
    print(f"  Latency: {results.get('latency_ms', {})}")
    if results.get('chunks'):
        for i, chunk in enumerate(results['chunks'][:3], 1):
            print(f"    {i}. {chunk.get('text', 'N/A')[:60]}...")
except Exception as e:
    print(f"[ERROR] Hybrid search error: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
