#!/usr/bin/env python3
"""
Transform chunking JSON output into Qdrant-compatible format.

This module provides utilities for converting structured JSON from chunking
operations into a flat list of chunk dictionaries ready for vector embedding
and ingestion into Qdrant.
"""

import json
from typing import Any, Dict, List
from pathlib import Path


def transform_for_qdrant(chunking_output: Dict[str, Any], strategy: str = "semantic") -> List[Dict[str, Any]]:
    """
    Transforms the chunking output into a flat list of chunk dictionaries
    compatible with the QdrantVectorDB client.

    Args:
        chunking_output: The JSON object from your chunking process.
        strategy: The chunking strategy to use ('fixed' or 'semantic').

    Returns:
        A list of chunk dictionaries ready for ingestion.

    Raises:
        ValueError: If the specified strategy is not found in the input data.
    """
    if strategy not in chunking_output:
        raise ValueError(f"Strategy '{strategy}' not found in the input data. Available: {list(chunking_output.keys())}")

    source_data = chunking_output[strategy]
    transformed_chunks = []

    for chunk in source_data.get("chunks", []):
        transformed_chunk = {
            'chunk_id': chunk.get('id'),
            'text': chunk.get('text'),
            'section': chunk.get('section'),
            'doc_id': source_data.get('doc_id'),
            'filename': source_data.get('filename'),
            'department': source_data.get('metadata', {}).get('department'),
            'category': source_data.get('metadata', {}).get('category'),
            'uploaded_at': source_data.get('metadata', {}).get('uploaded_at'),
            'page': chunk.get('page', 0)
        }
        transformed_chunks.append(transformed_chunk)

    return transformed_chunks


def transform_from_file(json_file: str, strategy: str = "semantic") -> List[Dict[str, Any]]:
    """
    Load JSON from file and transform it into Qdrant-compatible format.

    Args:
        json_file: Path to the JSON file containing chunking output.
        strategy: The chunking strategy to use ('fixed' or 'semantic').

    Returns:
        A list of chunk dictionaries ready for ingestion.

    Raises:
        FileNotFoundError: If the JSON file is not found.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the specified strategy is not found.
    """
    file_path = Path(json_file)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file}")

    with open(file_path, 'r', encoding='utf-8') as f:
        chunking_output = json.load(f)

    return transform_for_qdrant(chunking_output, strategy)


def transform_multiple_files(json_files: List[str], strategy: str = "semantic") -> List[Dict[str, Any]]:
    """
    Transform multiple JSON files and combine results into a single list.

    Args:
        json_files: List of paths to JSON files containing chunking output.
        strategy: The chunking strategy to use ('fixed' or 'semantic').

    Returns:
        Combined list of chunk dictionaries from all files.

    Raises:
        FileNotFoundError: If any JSON file is not found.
        json.JSONDecodeError: If any file is not valid JSON.
        ValueError: If the specified strategy is not found in any file.
    """
    all_chunks = []
    for json_file in json_files:
        chunks = transform_from_file(json_file, strategy)
        all_chunks.extend(chunks)
    return all_chunks


if __name__ == "__main__":
    example_data = {
        "semantic": {
            "doc_id": "72bc7e6a-a3de-4382-8ec2-775e907c76bd",
            "filename": "troubleshooting-guide.md_semantic",
            "metadata": {
                "department": "General",
                "category": "Uncategorized",
                "uploaded_at": "2026-06-03T08:35:21.226774"
            },
            "chunks": [
                {
                    "id": "138f1d19-92f9-4812-ae85-74dcc10fb69c",
                    "text": "--- title: Kubernetes Troubleshooting Guide...",
                    "section": None
                },
                {
                    "id": "6f7f7da4-8a10-4350-ac3e-8f95036ede39",
                    "text": "### Step 2: Verify Database Service...",
                    "section": "Step 2: Verify Database Service..."
                }
            ]
        }
    }

    qdrant_compatible_chunks = transform_for_qdrant(example_data, strategy="semantic")

    print("Transformed chunks ready for Qdrant:")
    print(json.dumps(qdrant_compatible_chunks, indent=2))
