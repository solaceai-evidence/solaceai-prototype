#!/usr/bin/env python3
"""
Test script to verify tokenizer compatibility between local and remote rerankers.
"""

import sys
import os
import requests
import time

# Add the API path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))


def test_reranker_service_tokenizer():
    """Test that the reranker service exposes tokenizer information."""
    print("🧪 Testing reranker service tokenizer endpoint...")

    try:
        # Test tokenizer endpoint
        resp = requests.get("http://localhost:8002/tokenizer", timeout=10)
        resp.raise_for_status()
        tokenizer_info = resp.json()

        print(f"✅ Tokenizer endpoint works!")
        print(f"   - Tokenizer class: {tokenizer_info.get('tokenizer_class')}")
        print(f"   - Vocab size: {tokenizer_info.get('vocab_size')}")
        print(f"   - Max length: {tokenizer_info.get('model_max_length')}")
        print(f"   - Pad token: {tokenizer_info.get('pad_token')}")

        return True

    except requests.RequestException as e:
        print(f"❌ Tokenizer endpoint failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_remote_tokenizer_proxy():
    """Test that RemoteReranker can fetch and use tokenizer info."""
    print("\n🧪 Testing RemoteReranker tokenizer proxy...")

    try:
        from scholarqa.rag.reranker.reranker_base import RemoteReranker

        # Initialize RemoteReranker (but don't test full reranking yet)
        reranker = RemoteReranker(service_name="reranker-service", batch_size=32)

        print(f"✅ RemoteReranker initialized: {reranker.url}")

        # Test tokenizer access
        tokenizer = reranker.get_tokenizer()

        if tokenizer is None:
            print("❌ RemoteReranker returned None for tokenizer")
            return False

        print(f"✅ RemoteReranker tokenizer proxy created!")
        print(f"   - Vocab size: {tokenizer.vocab_size}")
        print(f"   - Max length: {tokenizer.model_max_length}")
        print(f"   - Pad token: {tokenizer.pad_token}")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ RemoteReranker tokenizer test failed: {e}")
        return False


def test_compatibility_with_local_rerankers():
    """Test that all reranker types have consistent tokenizer interface."""
    print("\n🧪 Testing tokenizer interface consistency...")

    try:
        from scholarqa.rag.reranker.reranker_base import RERANKER_MAPPING

        consistent_interface = True

        for reranker_type, reranker_class in RERANKER_MAPPING.items():
            print(f"   - Checking {reranker_type}...")

            # Check if get_tokenizer method exists
            if not hasattr(reranker_class, "get_tokenizer"):
                print(f"     ❌ {reranker_type} missing get_tokenizer method")
                consistent_interface = False
            else:
                print(f"     ✅ {reranker_type} has get_tokenizer method")

        if consistent_interface:
            print("✅ All reranker types have consistent tokenizer interface!")
            return True
        else:
            print("❌ Inconsistent tokenizer interface found")
            return False

    except Exception as e:
        print(f"❌ Interface consistency test failed: {e}")
        return False


def main():
    """Run all tokenizer compatibility tests."""
    print("🚀 Starting tokenizer compatibility tests...")
    print("=" * 50)

    tests = [
        test_reranker_service_tokenizer,
        test_remote_tokenizer_proxy,
        test_compatibility_with_local_rerankers,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test.__name__}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tokenizer compatibility tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - check the output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
