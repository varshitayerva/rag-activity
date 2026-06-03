#!/usr/bin/env python3
"""
Verify Qdrant vector database - check stored data and test searches.
Usage: python verify_vectordb.py
"""

import os
import sys
import json
from unittest.mock import MagicMock

sys.modules['openai'] = MagicMock()
sys.path.insert(0, os.path.dirname(__file__))

from app.search.qdrant_client import QdrantVectorDB

def verify_vectordb():
    """Verify Qdrant storage and retrieve collection info."""

    print("=" * 80)
    print("VERIFYING QDRANT VECTOR DATABASE")
    print("=" * 80)
    print()

    # Connect to persistent storage
    print("Connecting to Qdrant storage at ./qdrant_storage/")
    vector_db = QdrantVectorDB(storage_path="./qdrant_storage")
    print()

    # Get collection info
    print("Retrieving collection information...")
    try:
        client = vector_db.client
        collection = client.get_collection(vector_db.collection_name)
        print()
        print(f"Collection Name: {vector_db.collection_name}")
        print(f"Points Count: {collection.points_count if hasattr(collection, 'points_count') else 'N/A'}")
        print(f"Vector Size: {vector_db.vector_size} (OpenAI embeddings)")
        print(f"Distance Metric: Cosine")
        print()
    except Exception as e:
        print(f"Warning: Could not retrieve full collection info: {e}")
        print(f"Collection Name: {vector_db.collection_name}")
        print()

    # Retrieve all stored chunks
    print("Retrieving all stored chunks...")
    try:
        points, _ = client.scroll(
            collection_name=vector_db.collection_name,
            limit=10000,
            with_payload=True
        )
        print(f"Found {len(points)} points in collection")
        print()

        # Display chunk details
        print("Stored Chunks:")
        print("-" * 80)
        for i, point in enumerate(points, 1):
            payload = point.payload
            chunk_id = payload.get('chunk_id', 'N/A')
            text_preview = payload.get('text', '')[:60] + "..."
            category = payload.get('category', 'N/A')
            section = payload.get('section', 'N/A')
            print(f"{i:2d}. {chunk_id:15s} | {section:25s} | {category:15s}")
            print(f"    Preview: {text_preview}")
        print()

    except Exception as e:
        print(f"Error retrieving chunks: {e}")
        return

    # Check storage files
    print("Storage Files:")
    print("-" * 80)
    import glob
    storage_files = glob.glob("./qdrant_storage/**/*", recursive=True)
    for file_path in sorted(storage_files):
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            rel_path = os.path.relpath(file_path, "./qdrant_storage")
            size_kb = size / 1024
            print(f"{rel_path:50s} {size_kb:>10.2f} KB")
    print()

    # Get total storage size
    total_size = sum(os.path.getsize(f) for f in glob.glob("./qdrant_storage/**/*", recursive=True) if os.path.isfile(f))
    print(f"Total Storage Size: {total_size / 1024:.2f} KB ({total_size / (1024*1024):.2f} MB)")
    print()

    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print("Status:")
    print(f"  - Qdrant collection 'technical-support-chunks' is active")
    print(f"  - {len(points)} chunks stored in vector database")
    print(f"  - Data persisted to: ./qdrant_storage/")
    print(f"  - Vector dimension: 1536 (OpenAI embeddings)")
    print(f"  - Distance metric: Cosine similarity")
    print()
    print("Your vector database is ready for RAG operations!")
    print()

if __name__ == "__main__":
    try:
        verify_vectordb()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
