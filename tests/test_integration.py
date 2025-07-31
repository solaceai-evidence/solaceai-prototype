#!/usr/bin/env python3
"""
Integration test for GPU-accelerated reranker service.
Demonstrates compatibility with existing RemoteReranker interface.
"""

import requests
import time
import json
from typing import List


class TestRemoteReranker:
    """
    Test class that mimics the existing RemoteReranker interface
    to verify GPU service compatibility.
    """

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")
        self.rerank_url = f"{self.base_url}/rerank"

    def get_scores(
        self, query: str, passages: List[str], batch_size: int = 32
    ) -> List[float]:
        """
        Main method that existing ScholarQA code expects.
        Tests compatibility with RemoteReranker interface.
        """
        try:
            response = requests.post(
                self.rerank_url,
                json={
                    "query": query,
                    "passages": passages,  # Use 'passages' as expected by RemoteReranker
                    "batch_size": batch_size,
                },
                timeout=300,  # 5 minute timeout for large document sets
            )
            response.raise_for_status()

            result = response.json()
            return result["scores"]  # Return just the scores as expected

        except Exception as e:
            print(f"Error calling reranker service: {e}")
            return []


def test_small_batch():
    """Test with a small batch of documents."""
    print("Testing small batch (10 documents)...")

    reranker = TestRemoteReranker()
    query = "machine learning applications in healthcare"
    passages = [
        "Machine learning algorithms are revolutionizing medical diagnosis",
        "Deep learning models can detect cancer in medical images",
        "AI assists doctors in making better treatment decisions",
        "Neural networks analyze patient data for personalized medicine",
        "Computer vision helps identify diseases from X-rays",
        "Natural language processing extracts insights from medical records",
        "Predictive models forecast patient outcomes and recovery",
        "Automated systems reduce medical errors and improve safety",
        "AI-powered tools enable early disease detection and prevention",
        "Machine learning optimizes drug discovery and development processes",
    ]

    start_time = time.time()
    scores = reranker.get_scores(query, passages, batch_size=32)
    processing_time = time.time() - start_time

    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Scores received: {len(scores)}")
    print(f"Top 3 scores: {scores[:3] if scores else 'None'}")
    print()


def test_large_batch():
    """Test with a large batch simulating 300+ document processing."""
    print(
        "Testing large batch (300 documents) - this demonstrates the performance improvement..."
    )

    reranker = TestRemoteReranker()
    query = "climate change impacts on biodiversity"

    # Generate 300 test documents
    base_docs = [
        "Climate change affects species distribution and migration patterns",
        "Rising temperatures threaten coral reef ecosystems worldwide",
        "Deforestation accelerates habitat loss for endangered species",
        "Ocean acidification impacts marine food chains significantly",
        "Polar ice melting affects Arctic wildlife populations",
        "Extreme weather events disrupt breeding cycles of many species",
        "Shifting precipitation patterns alter plant communities",
        "Sea level rise threatens coastal wetland habitats",
        "Temperature increases stress cold-adapted mountain species",
        "Drought conditions affect freshwater ecosystem biodiversity",
    ]

    # Create 300 documents by expanding the base set
    passages = []
    for i in range(300):
        base_doc = base_docs[i % len(base_docs)]
        passages.append(f"{base_doc} Document variation {i+1}.")

    print(f"Generated {len(passages)} test documents")

    start_time = time.time()
    scores = reranker.get_scores(query, passages, batch_size=32)
    processing_time = time.time() - start_time

    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Documents per second: {len(passages) / processing_time:.1f}")
    print(f"Scores received: {len(scores)}")

    if processing_time < 120:  # Less than 2 minutes is good
        print("✅ Excellent performance! GPU acceleration is working.")
    elif processing_time < 180:  # Less than 3 minutes is acceptable
        print("⚠️  Good performance, but could be optimized further.")
    else:
        print("❌ Slow performance - check GPU acceleration setup.")

    print()


def test_service_health():
    """Test service health and device information."""
    print("Testing service health...")

    try:
        response = requests.get("http://localhost:8001/health", timeout=10)
        response.raise_for_status()

        health_data = response.json()
        print(f"Service status: {health_data.get('status')}")
        print(f"Device: {health_data.get('device')}")
        print(f"GPU available: {health_data.get('gpu_available')}")
        print(f"Model loaded: {health_data.get('model_loaded')}")
        print()

        return health_data.get("status") == "healthy"

    except Exception as e:
        print(f"Health check failed: {e}")
        print("Make sure the service is running: python high_performance_service.py")
        return False


def main():
    """Run integration tests."""
    print("GPU-Accelerated Reranker Integration Test")
    print("=" * 50)
    print()

    # Test service health first
    if not test_service_health():
        print("Service not available. Please start the service first:")
        print("cd reranker_service && python high_performance_service.py")
        return

    # Test small batch
    test_small_batch()

    # Test large batch (demonstrates the performance improvement)
    test_large_batch()

    print("Integration tests completed!")
    print()
    print("Performance expectations:")
    print("- CPU: 200+ seconds for 300 documents")
    print("- Apple M2 Max (MPS): 30-60 seconds")
    print("- NVIDIA GPU: 10-20 seconds")


if __name__ == "__main__":
    main()
