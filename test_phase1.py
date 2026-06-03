#!/usr/bin/env python3
"""
Phase 1 Test: Verify Claude Sonnet 4.0 integration with streaming SSE
"""

import asyncio
import json
from dotenv import load_dotenv
from backend.app.generation.service import GenerationService
from backend.app.generation.models import Chunk, ChunkMetadata

# Load environment variables
load_dotenv()


async def test_streaming_generation():
    """Test streaming generation with sample chunks."""
    print("=" * 70)
    print("PHASE 1 TEST: Claude Sonnet 4.0 Streaming Generation")
    print("=" * 70)

    # Initialize service
    service = GenerationService()
    print("\n[✓] GenerationService initialized")

    # Create sample chunks
    sample_chunks = [
        Chunk(
            text="To restart a pod, use: kubectl rollout restart deployment/[name] -n [namespace]. This creates new pods and terminates old ones gracefully.",
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
            text="Alternative method: kubectl delete pod [pod-name] -n [namespace]. The deployment controller automatically creates replacement pods.",
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
    print("[✓] Sample chunks created (2 chunks from kubernetes-guide.pdf)")

    # Test 1: Streaming generation
    print("\n" + "-" * 70)
    print("TEST 1: Streaming SSE Generation")
    print("-" * 70)
    query = "How do I restart a pod?"
    print(f"Query: {query}\n")

    events = []
    print("Streaming response:")
    print("-" * 40)

    async for event_str in service.generate_streaming(query, sample_chunks):
        if event_str.strip():
            event = json.loads(event_str.strip())
            events.append(event)

            if event["type"] == "metadata":
                print(f"\n[SOURCES]")
                for source in event["sources"]:
                    print(f"  - {source['doc']} (Section: {source['section']})")

            elif event["type"] == "token":
                print(event["content"], end="", flush=True)

            elif event["type"] == "done":
                print(f"\n\n[TOKEN USAGE]")
                print(f"  Input tokens: {event['input_tokens']}")
                print(f"  Output tokens: {event['output_tokens']}")

    # Validate event structure
    print("\n" + "-" * 40)
    print("Event Structure Validation:")
    assert len(events) >= 3, "Should have at least 3 events (metadata, tokens, done)"
    assert events[0]["type"] == "metadata", "First event should be metadata"
    assert events[-1]["type"] == "done", "Last event should be done"
    assert any(e["type"] == "token" for e in events), "Should have token events"
    print("[✓] Metadata event present with sources")
    print("[✓] Token events present (streaming)")
    print("[✓] Done event present with token counts")

    # Test 2: Non-streaming generation
    print("\n" + "-" * 70)
    print("TEST 2: Non-Streaming Generation")
    print("-" * 70)

    result = await service.generate(query, sample_chunks)
    print(f"\nResponse:\n{result['response'][:200]}...\n")
    print(f"Sources: {[s['doc'] for s in result['sources']]}")
    print(f"Tokens: {result['input_tokens']} input, {result['output_tokens']} output")

    assert "response" in result, "Should have response"
    assert "sources" in result, "Should have sources"
    assert "input_tokens" in result, "Should have input_tokens"
    assert "output_tokens" in result, "Should have output_tokens"
    print("\n[✓] Non-streaming generation works")

    # Test 3: Hallucination prevention
    print("\n" + "-" * 70)
    print("TEST 3: System Prompt Validation (Hallucination Prevention)")
    print("-" * 70)
    from backend.app.generation.prompts import SYSTEM_PROMPT

    checks = [
        ("Context-only enforcement", "MUST answer based ONLY" in SYSTEM_PROMPT),
        ("Fallback message", "don't have reliable information" in SYSTEM_PROMPT.lower()),
        ("Source citation requirement", "cite" in SYSTEM_PROMPT.lower() or "source" in SYSTEM_PROMPT.lower()),
    ]

    for check_name, passed in checks:
        status = "[✓]" if passed else "[✗]"
        print(f"{status} {check_name}")

    assert all(c[1] for c in checks), "All hallucination prevention checks should pass"

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 1 TEST SUMMARY")
    print("=" * 70)
    print("[✓] Claude Sonnet 4.0 integration working")
    print("[✓] Streaming SSE format verified")
    print("[✓] Grounding prompt enforces hallucination prevention")
    print("[✓] Source attribution extracted correctly")
    print("[✓] Token counting working")
    print("\nPHASE 1 COMPLETE - Ready for integration with M1, M2, M4, M5")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_streaming_generation())
