#!/usr/bin/env python
"""Complete workflow test for RAG system."""

import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"
INGEST_API = "http://localhost:8000"

def test_health():
    """Test backend health."""
    print("\n[TEST 1] Backend health check...")
    try:
        resp = requests.get(f"{API_BASE}/health")
        print(f"  ✓ Health: {resp.json()}")
        return True
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        return False

def test_metrics_initial():
    """Test metrics endpoint (should be all zeros initially)."""
    print("\n[TEST 2] Initial metrics (should be zeros)...")
    try:
        resp = requests.get(f"{API_BASE}/api/metrics")
        metrics = resp.json()
        print(f"  ✓ Metrics endpoint working")
        print(f"    - Cache hit rate: {metrics.get('cache_hit_rate', 0)}")
        print(f"    - Total queries: {metrics.get('total_queries', 0)}")
        print(f"    - Avg latency: {metrics.get('avg_latency_ms', 0)}ms")
        return True
    except Exception as e:
        print(f"  ✗ Metrics check failed: {e}")
        return False

def test_config():
    """Test config endpoint."""
    print("\n[TEST 3] Generation config...")
    try:
        resp = requests.get(f"{API_BASE}/api/config")
        config = resp.json()
        print(f"  ✓ Available providers:")
        for provider, info in config.get("available_providers", {}).items():
            print(f"    - {provider}: {info.get('description', 'N/A')}")
        return True
    except Exception as e:
        print(f"  ✗ Config check failed: {e}")
        return False

def test_search_mock():
    """Test search endpoint (may return mock data initially)."""
    print("\n[TEST 4] Search endpoint...")
    try:
        resp = requests.post(
            f"{API_BASE}/api/search",
            json={
                "query": "How do I restart a pod?",
                "top_k": 5,
                "filter": {}
            }
        )
        result = resp.json()
        print(f"  ✓ Search working")
        print(f"    - Results: {len(result.get('chunks', []))}")
        print(f"    - Search type: {result.get('search_type', 'unknown')}")
        latency = result.get("latency_ms", {})
        print(f"    - Total latency: {latency.get('total', 0)}ms")
        return True
    except Exception as e:
        print(f"  ✗ Search check failed: {e}")
        return False

def test_generation():
    """Test generation endpoint."""
    print("\n[TEST 5] Generation endpoint (non-streaming)...")
    try:
        resp = requests.post(
            f"{API_BASE}/api/generate?provider=huggingface",
            json={
                "query": "What is a pod?",
                "chunks": [
                    {
                        "text": "A Kubernetes pod is the smallest deployable unit in Kubernetes",
                        "score": 0.95,
                        "source": "k8s-guide.pdf",
                        "chunk_id": "chunk-001",
                        "metadata": {
                            "section": "Basics",
                            "page": 1,
                            "doc_id": "doc-001",
                            "source": "k8s-guide.pdf"
                        }
                    }
                ],
                "stream": False
            }
        )
        if resp.status_code == 200:
            result = resp.json()
            print(f"  ✓ Generation working")
            print(f"    - Response length: {len(result.get('generation', ''))} chars")
            tokens = result.get("tokens", {})
            print(f"    - Input tokens: {tokens.get('input_tokens', 0)}")
            print(f"    - Output tokens: {tokens.get('output_tokens', 0)}")
            return True
        else:
            print(f"  ✗ Generation returned {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        print(f"  ✗ Generation check failed: {e}")
        return False

def test_metrics_updated():
    """Test metrics endpoint after operations."""
    print("\n[TEST 6] Metrics after operations...")
    try:
        time.sleep(1)  # Wait a moment
        resp = requests.get(f"{API_BASE}/api/metrics")
        metrics = resp.json()
        print(f"  ✓ Metrics updated")
        print(f"    - Cache hit rate: {metrics.get('cache_hit_rate', 0):.1%}")
        print(f"    - Total queries: {metrics.get('total_queries', 0)}")
        print(f"    - Avg latency: {metrics.get('avg_latency_ms', 0):.1f}ms")
        print(f"    - Retrieval hits: {metrics.get('retrieval_cache_hits', 0)}")
        print(f"    - Retrieval misses: {metrics.get('retrieval_cache_misses', 0)}")
        print(f"    - Response hits: {metrics.get('response_cache_hits', 0)}")
        print(f"    - Response misses: {metrics.get('response_cache_misses', 0)}")
        return True
    except Exception as e:
        print(f"  ✗ Metrics check failed: {e}")
        return False

def main():
    print("=" * 70)
    print("RAG SYSTEM WORKFLOW TEST")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Initial Metrics", test_metrics_initial()))
    results.append(("Config", test_config()))
    results.append(("Search", test_search_mock()))
    results.append(("Generation", test_generation()))
    results.append(("Updated Metrics", test_metrics_updated()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All tests passed! System is working end-to-end.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above.")

if __name__ == "__main__":
    main()
