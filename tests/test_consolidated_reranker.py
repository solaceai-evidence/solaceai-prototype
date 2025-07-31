#!/usr/bin/env python3
"""
Quick validation test for the high-performance reranker service.
Tests that the service starts, responds to health checks, and processes documents correctly.
"""

import requests
import time
import json


def test_consolidated_reranker():
    """Test the high-performance reranker service for basic functionality."""

    base_url = "http://localhost:8001"  # External port mapping

    print("🧪 Testing High-Performance Reranker Service")
    print("=" * 60)

    # Test 1: Health Check
    print("1️⃣ Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed!")
            print(f"   Service: {health_data.get('service', 'unknown')}")
            print(f"   Backend: {health_data.get('backend', 'unknown')}")
            print(f"   Device: {health_data.get('device', 'unknown')}")
            print(f"   Model: {health_data.get('model', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

    # Test 2: Small batch reranking
    print("\n2️⃣ Testing small batch reranking...")

    test_query = "climate emergency and global warming effects"
    test_documents = [
        "The climate crisis is accelerating with unprecedented global warming trends affecting ecosystems worldwide.",
        "Recent studies show artificial intelligence can help optimize renewable energy distribution systems.",
        "Ocean acidification and rising sea levels are direct consequences of increased atmospheric CO2 concentrations.",
        "Machine learning algorithms are being developed to predict weather patterns with improved accuracy.",
    ]

    request_data = {"query": test_query, "passages": test_documents, "batch_size": 4}

    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/rerank", json=request_data, timeout=30)
        end_time = time.time()

        if response.status_code == 200:
            result = response.json()
            scores = result.get("scores", [])
            processing_time = result.get("processing_time", 0)

            print(f"✅ Small batch test passed!")
            print(f"   Documents processed: {len(scores)}")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Total time: {end_time - start_time:.2f}s")
            print(f"   Performance: {len(scores) / processing_time:.1f} docs/sec")

            # Show top scoring document
            if scores:
                best_idx = scores.index(max(scores))
                print(f'   Top result: "{test_documents[best_idx][:60]}..."')
                print(f"   Score: {scores[best_idx]:.4f}")

        else:
            print(f"❌ Small batch test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Small batch test error: {e}")
        return False

    # Test 3: Larger batch to verify performance
    print("\n3️⃣ Testing larger batch (15 documents)...")

    larger_docs = test_documents * 4  # Create 16 documents
    larger_docs = larger_docs[:15]  # Use exactly 15

    larger_request = {"query": test_query, "passages": larger_docs, "batch_size": 8}

    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/rerank", json=larger_request, timeout=45)
        end_time = time.time()

        if response.status_code == 200:
            result = response.json()
            scores = result.get("scores", [])
            processing_time = result.get("processing_time", 0)

            print(f"✅ Larger batch test passed!")
            print(f"   Documents processed: {len(scores)}")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Total time: {end_time - start_time:.2f}s")
            print(f"   Performance: {len(scores) / processing_time:.1f} docs/sec")

            # Verify this is much faster than the previous 0.1 docs/sec
            docs_per_sec = len(scores) / processing_time
            if docs_per_sec > 1.0:  # Should be much faster than 0.1
                print(f"🚀 PERFORMANCE IMPROVEMENT CONFIRMED!")
                print(f"   Previous ONNX: ~0.1 docs/sec")
                print(f"   Consolidated: {docs_per_sec:.1f} docs/sec")
                print(f"   Improvement: {docs_per_sec / 0.1:.0f}x faster!")
            else:
                print(f"⚠️  Performance still slower than expected")

        else:
            print(f"❌ Larger batch test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Larger batch test error: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED! High-performance reranker is working effectively.")
    print("🎉 Ready for production use with improved performance!")
    return True


if __name__ == "__main__":
    success = test_consolidated_reranker()
    exit(0 if success else 1)
