#!/usr/bin/env python3
"""
Test Ollama Generation (Local, Free - No API Key Needed)

Setup:
  1. Download Ollama from https://ollama.ai/
  2. Install it
  3. Run: ollama pull mistral
  4. Then run this script
"""

import asyncio
import json
from backend.app.generation.service_ollama import OllamaGenerationService
from backend.app.generation.models import Chunk, ChunkMetadata


async def main():
    print("=" * 70)
    print("OLLAMA - LOCAL FREE GENERATION TEST")
    print("=" * 70)

    # Check if Ollama is running
    print("\nChecking Ollama server...")
    print("  Expected: http://localhost:11434")
    print("  Make sure Ollama is running: ollama serve")

    # Initialize service
    try:
        service = OllamaGenerationService(model="mistral")
        print("[OK] OllamaGenerationService initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}")
        print("\nSetup required:")
        print("  1. Download Ollama: https://ollama.ai/")
        print("  2. Run: ollama pull mistral")
        print("  3. Start Ollama: ollama serve")
        print("  4. Run this script again")
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
    print("STREAMING RESPONSE (LOCAL OLLAMA):")
    print("-" * 70 + "\n")

    try:
        # Stream generation
        event_count = 0
        token_count = 0

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

        print("\n" + "=" * 70)
        print("SUCCESS: Ollama streaming works locally!")
        print("=" * 70)
        print("\nAdvantages:")
        print("  - Runs locally (no API calls)")
        print("  - Completely free (no cost)")
        print("  - No API key needed")
        print("  - Works offline")

    except Exception as e:
        print(f"\n[ERROR] Streaming failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
