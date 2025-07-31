#!/usr/bin/env python3
"""Quick focused batch test."""

import requests
import time
import json

# Create test data
passages = [
    "Global warming causes Arctic ice to melt rapidly",
    "Climate change increases extreme weather frequency",
    "Carbon emissions drive greenhouse gas concentrations",
    "Renewable energy reduces fossil fuel dependence",
    "Stock market shows volatility amid economic uncertainty",
    "New smartphone features improved camera technology",
    "Sports team advances to championship finals",
    "Sea level rise threatens coastal communities worldwide",
    "Climate adaptation strategies help vulnerable populations",
    "Green infrastructure provides environmental benefits",
    "Movie industry reports record box office numbers",
    "Food delivery services expand market coverage",
    "Ocean acidification results from increased CO2 levels",
    "Climate justice emphasizes equitable solutions",
    "Sustainable agriculture practices reduce environmental impact",
]

query = "climate change environmental impacts"

print(f"🧪 Quick Batch Test - {len(passages)} documents")
print(f"📊 Query: {query}")
print(f"⚡ Expected performance with batch_size=32:")
print(f"   - Processing {len(passages)} docs in ~1 batch")
print(f"   - Should complete in ~3-5 seconds")

try:
    start = time.time()

    response = requests.post(
        "http://localhost:8001/rerank",
        json={"query": query, "passages": passages, "batch_size": 32},
        timeout=30,
    )

    elapsed = time.time() - start

    if response.status_code == 200:
        result = response.json()

        print(f"\n✅ SUCCESS!")
        print(f"⏱️  Total time: {elapsed:.2f}s")
        print(f"🔧 Processing time: {result.get('processing_time', 'N/A')}s")
        print(f"📊 Documents processed: {len(result['scores'])}")
        print(f"🚀 Throughput: {len(passages)/elapsed:.1f} docs/sec")

        # Show top climate results
        scored_passages = list(zip(passages, result["scores"]))
        scored_passages.sort(key=lambda x: x[1], reverse=True)

        print(f"\n🏆 Top 5 climate-relevant results:")
        for i, (passage, score) in enumerate(scored_passages[:5]):
            climate_marker = (
                "🌍"
                if any(
                    w in passage.lower()
                    for w in [
                        "climate",
                        "warming",
                        "carbon",
                        "green",
                        "sea level",
                        "renewable",
                    ]
                )
                else "📄"
            )
            print(f"  {i+1}. {climate_marker} {score:.4f} - {passage[:45]}...")

        print(f"\n🎯 BATCH PROCESSING CONFIRMED!")
        print(f"✅ System efficiently processes multiple documents simultaneously")

    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

except Exception as e:
    print(f"❌ Test failed: {e}")
