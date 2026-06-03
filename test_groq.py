#!/usr/bin/env python3
"""
Test Groq Generation (Free Tier - No Payment Required)

Setup:
  1. Go to https://console.groq.com/
  2. Sign up (free)
  3. Create API key
  4. Run: set GROQ_API_KEY=your-key
  5. Run this script
"""

import asyncio
import json
import os
from backend.app.generation.service_groq import GroqGenerationService
from backend.app.generation.models import Chunk, ChunkMetadata


async def main():
    print("=" * 70)
    print("GROQ - FREE TIER GENERATION TEST")
    print("=" * 70)

    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("\nERROR: GROQ_API_KEY not set!")
        print("\nSetup:")
        print("  1. Go to: https://console.groq.com/")
        print("  2. Sign up (free)")
        print("  3. Create API key")
        print("  4. Run: set GROQ_API_KEY=sk-...")
        print("  5. Run this script again")
        print("\nAdvantages:")
        print("  - Completely free (no payment)")
        print("  - Very fast (faster than Anthropic)")
        print("  - No card required")
        return

    print(f"\nAPI Key detected: {api_key[:15]}...")

    # Initialize service
    try:
        service = GroqGenerationService()
        print("[OK] GroqGenerationService initialized")
    except ImportError:
        print("[ERROR] groq package not installed")
        print("Install it: pip install groq")
        return
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}")
        return

    # Create sample chunks
    chunks = [
        Chunk(
            text="To restart a pod, use the command: kubectl rollout restart deployment/[deployment-name] -n [namespace]. This creates new pods and terminates old ones gracefully.",
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
            text="Alternative: kubectl delete pod [pod-name] -n [namespace]. The deployment controller automatically creates replacement pods.",
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
    print("STREAMING RESPONSE (GROQ):")
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
                        print(f"  - {source['doc']} (Section: {source['section']})")
                    print()

                elif event["type"] == "token":
                    print(event["content"], end="", flush=True)
                    token_count += 1

                elif event["type"] == "error":
                    print(f"\n[ERROR] {event['message']}")

                elif event["type"] == "done":
                    print(f"\n")
                    input_tokens = event.get("input_tokens", 0)
                    output_tokens = event.get("output_tokens", 0)

        print("-" * 70)
        print(f"\nSTATISTICS:")
        print(f"  Events: {event_count}")
        print(f"  Tokens streamed: {token_count}")
        print(f"  Input tokens: {input_tokens}")
        print(f"  Output tokens: {output_tokens}")

        print("\n" + "=" * 70)
        print("SUCCESS: Groq streaming works!")
        print("=" * 70)
        print("\nAdvantages:")
        print("  - Free tier (no payment)")
        print("  - Very fast inference")
        print("  - No card required")
        print("  - Same streaming format")

    except Exception as e:
        print(f"\n[ERROR] Streaming failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
