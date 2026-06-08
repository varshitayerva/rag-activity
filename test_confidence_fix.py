#!/usr/bin/env python
"""
Test script to verify confidence scoring improvements.
Tests that mismatched queries return low confidence scores.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.search.hybrid_search import HybridSearchService


async def test_confidence_scoring():
    """Test confidence scoring with matched and mismatched queries."""

    try:
        print("Initializing HybridSearchService...")
        hybrid_search = HybridSearchService()
        print("✓ Service initialized\n")

        # Test queries: one matching docs, one not matching
        test_cases = [
            {
                "query": "What is Kubernetes?",
                "expected": "HIGH",
                "reason": "Should match K8s documentation"
            },
            {
                "query": "xyz123 random gibberish garbage nonsense",
                "expected": "LOW",
                "reason": "Should NOT match any documentation"
            },
            {
                "query": "How to make a pizza with pineapple?",
                "expected": "LOW",
                "reason": "Off-topic query, no matching docs"
            }
        ]

        print("=" * 70)
        print("CONFIDENCE SCORING TEST")
        print("=" * 70)

        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case['query']}")
            print(f"Expected: {test_case['expected']} confidence")
            print(f"Reason: {test_case['reason']}")

            result = await hybrid_search.search(test_case['query'], top_k=5)
            confidence = result.get('confidence_score', 0)

            # Determine actual confidence level
            if confidence > 0.65:
                actual = "HIGH"
            elif confidence > 0.40:
                actual = "MEDIUM"
            else:
                actual = "LOW"

            status = "✓ PASS" if actual == test_case['expected'] else "✗ FAIL"
            print(f"Actual: {actual} ({confidence:.3f}) {status}")
            print(f"Matching docs: {result.get('num_results', 0)}")

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_confidence_scoring())
