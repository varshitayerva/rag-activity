#!/usr/bin/env python3
"""Regenerate embeddings for all chunks in the database."""

import os
import sys
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'varsh'
os.environ['DB_NAME'] = 'fde_rag'

from backend.app.database.postgres import db_client
from backend.app.search.embeddings import EmbeddingsClient
import psycopg2

print("[STEP 1] Getting all chunks from database...")
try:
    chunks = db_client.get_all_chunks()
    print(f"[OK] Found {len(chunks)} chunks to embed")
except Exception as e:
    print(f"[ERROR] Failed to fetch chunks: {e}")
    sys.exit(1)

if not chunks:
    print("[ERROR] No chunks found in database")
    sys.exit(1)

print("\n[STEP 2] Initializing embeddings client...")
try:
    embeddings = EmbeddingsClient()
    print(f"[OK] Embedding model loaded: {embeddings.model}")
    print(f"[OK] Embedding dimension: {embeddings.embedding_dim}")
except Exception as e:
    print(f"[ERROR] Failed to load embeddings: {e}")
    sys.exit(1)

print("\n[STEP 3] Generating embeddings for all chunks...")
try:
    texts = [chunk['text'] for chunk in chunks]
    print(f"[PROGRESS] Embedding {len(texts)} chunks...")
    embeddings_list = embeddings.embed_batch(texts)
    print(f"[OK] Generated {len(embeddings_list)} embeddings")
except Exception as e:
    print(f"[ERROR] Failed to generate embeddings: {e}")
    sys.exit(1)

print("\n[STEP 4] Storing embeddings in database...")
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="varsh",
        database="fde_rag"
    )
    cursor = conn.cursor()

    updated = 0
    for chunk, embedding in zip(chunks, embeddings_list):
        cursor.execute(
            "UPDATE chunks SET embedding = %s WHERE id = %s",
            (embedding, chunk['id'])
        )
        updated += 1
        if updated % 10 == 0:
            print(f"[PROGRESS] Updated {updated}/{len(chunks)} chunks...")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"[OK] Updated {updated} chunks with embeddings")
except Exception as e:
    print(f"[ERROR] Failed to store embeddings: {e}")
    sys.exit(1)

print("\n[STEP 5] Verifying embeddings...")
try:
    chunks_with_embeddings = db_client.get_all_chunks()
    embedded_count = sum(1 for c in chunks_with_embeddings if c.get('embedding') is not None)
    print(f"[OK] {embedded_count}/{len(chunks_with_embeddings)} chunks now have embeddings")
except Exception as e:
    print(f"[WARNING] Failed to verify: {e}")

print("\n" + "="*60)
print("REGENERATION COMPLETE")
print("="*60)
print("\nYour embeddings are now real HuggingFace embeddings!")
print("Try searching again - similarity scores should be much higher (60-90%+)")
