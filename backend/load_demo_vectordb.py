#!/usr/bin/env python3
"""
Load demo chunks into Qdrant vector database for RAG operations.
Usage: python load_demo_vectordb.py
"""

import os
import sys
import hashlib
import numpy as np
from demo_chunks import get_demo_chunks

# Mock external dependencies before importing
from unittest.mock import MagicMock, patch

sys.modules['openai'] = MagicMock()

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.search.qdrant_client import QdrantVectorDB

def generate_mock_embeddings(chunks):
    """Generate deterministic mock embeddings based on chunk text."""
    embeddings = []
    for chunk in chunks:
        # Use hash of text to generate deterministic 1536-dim vector
        text_hash = hashlib.md5(chunk['text'].encode()).digest()
        # Seed numpy random with hash
        np.random.seed(int.from_bytes(text_hash[:4], 'big'))
        # Generate consistent 1536-dimensional vector
        embedding = np.random.randn(1536).astype(np.float32)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        embeddings.append(embedding.tolist())
    return embeddings

def load_demo_data():
    """Load demo chunks into vector database."""

    print("=" * 80)
    print("LOADING DEMO CHUNKS INTO QDRANT VECTOR DATABASE")
    print("=" * 80)
    print()

    # Get demo chunks
    chunks = get_demo_chunks()
    print(f"Loaded {len(chunks)} demo chunks from demo_chunks.py")
    print()

    # Initialize vector DB with persistent storage
    print("Initializing Qdrant with persistent storage at ./qdrant_storage/")
    vector_db = QdrantVectorDB(storage_path="./qdrant_storage")
    print()

    # Generate mock embeddings
    print("Generating mock embeddings for chunks...")
    embeddings = generate_mock_embeddings(chunks)
    print(f"Generated {len(embeddings)} embeddings (1536-dim vectors)")
    print()

    # Add chunks and embeddings to Qdrant
    print("Adding chunks to Qdrant vector database...")
    vector_db.add_points(chunks, embeddings)
    print()

    # Display summary
    print("=" * 80)
    print("DEMO DATA LOADED SUCCESSFULLY")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - {len(chunks)} chunks indexed")
    print(f"  - Vector embeddings generated")
    print(f"  - Data persisted to: ./qdrant_storage/")
    print()
    print("Chunks loaded:")
    for i, chunk in enumerate(chunks, 1):
        print(f"  {i:2d}. {chunk['chunk_id']:15s} - {chunk['section']:25s} ({chunk['category']})")
    print()
    print("Your vector database is ready for RAG operations!")
    print()

if __name__ == "__main__":
    try:
        load_demo_data()
    except Exception as e:
        print(f"Error loading demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
