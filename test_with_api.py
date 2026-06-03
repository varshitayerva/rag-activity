#!/usr/bin/env python3
"""
Test Generation Service with Real Claude API
Requires: ANTHROPIC_API_KEY environment variable
"""

import asyncio
import json
import os
from backend.app.generation.service import GenerationService
from backend.app.generation.models import Chunk, ChunkMetadata


async def main():
    print("=" * 70)
    print("CLAUDE SONNET 4.0 - STREAMING TEST")
    print("=" * 70)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY not set!")
        print("\nTo get a free API key:")
        print("  1. Go to https://console.anthropic.com/")
        print("  2. Sign up (free)")
        print("  3. Create API key")
        print("  4. Run: set ANTHROPIC_API_KEY=sk-ant-...")
        print("  5. Run this script again")
        return

    print(f"\nAPI Key detected: {api_key[:20]}...")

    # Initialize service
    try:
        service = GenerationService()
        print("[OK] GenerationService initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize service: {e}")
        return

    # Create sample chunks
    chunks = [
        Chunk(
            text="To restart a pod, use the command: kubectl rollout restart deployment/[deployment-name] -n [namespace]. This will create new pods and terminate old ones gracefully without data loss.",
            score=0.95,
            source="kubernetes-guide.pdf",
            chunk_id="chunk-001",
            metadata=ChunkMetadata(
                section="Troubleshooting",
                page=42,
                doc_id="doc-001",
                source="kubernetes-guide.pdf",
            ),
        ),
        Chunk(
            text="Alternative method: Use kubectl delete pod [pod-name] -n [namespace]. The deployment controller will automatically create replacement pods based on the replica set configuration.",
            score=0.87,
            source="kubernetes-guide.pdf",
            chunk_id="chunk-002",
            metadata=ChunkMetadata(
                section="Troubleshooting",
                page=43,
                doc_id="doc-001",
                source="kubernetes-guide.pdf",
            ),
        ),
    ]

    query = "How do I restart a pod in Kubernetes?"

    print(f"\nQuery: {query}")
    print("\n" + "-" * 70)
    print("STREAMING RESPONSE:")
    print("-" * 70 + "\n")

    try:
        # Stream generation
        event_count = 0
        token_count = 0
        input_tokens = 0
        output_tokens = 0

        async for event_str in service.generate_streaming(query, chunks):
            if event_str.strip():
                event = json.loads(event_str.strip())
                event_count += 1

                if event["type"] == "metadata":
                    print("[SOURCES]")
                    for source in event["sources"]:
                        print(
                            f"  - {source['doc']} (Section: {source['section']})"
                        )
                    print()

                elif event["type"] == "token":
                    print(event["content"], end="", flush=True)
                    token_count += 1

                elif event["type"] == "done":
                    input_tokens = event["input_tokens"]
                    output_tokens = event["output_tokens"]
                    print("\n")

        print("-" * 70)
        print(f"\nSTATISTICS:")
        print(f"  Events received: {event_count}")
        print(f"  Tokens streamed: {token_count}")
        print(f"  Input tokens: {input_tokens}")
        print(f"  Output tokens: {output_tokens}")
        print(f"  Total tokens: {input_tokens + output_tokens}")

        print("\n" + "=" * 70)
        print("SUCCESS: Claude Sonnet streaming works!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Streaming failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
