#!/usr/bin/env python3
"""Simple reranker test"""

import requests
import time

print("Testing reranker service...")

# Simple test data
data = {
    "query": "climate change effects",
    "passages": [
        "Global warming causes sea level rise",
        "Stock market volatility continues",
        "Renewable energy investments grow",
        "Sports team wins championship",
    ],
    "batch_size": 32,
}

try:
    start = time.time()
    response = requests.post("http://localhost:8001/rerank", json=data, timeout=30)
    elapsed = time.time() - start

    print(f"Response received in {elapsed:.2f}s")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Scores: {result['scores']}")
        print(f"Processing time: {result.get('processing_time', 'N/A')}s")
        print("✅ Reranker is working with batch processing!")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")
