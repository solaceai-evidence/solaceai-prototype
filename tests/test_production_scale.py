#!/usr/bin/env python3
"""
Production-scale test for 300+ document reranking.
Tests performance at scale to determine if current solution is production-ready.
"""

import requests
import time
import json


def generate_test_documents(count: int = 300) -> list:
    """Generate realistic test documents for large-scale testing."""
    base_docs = [
        "Climate change is causing unprecedented global warming and environmental disruption worldwide.",
        "Rising sea levels threaten coastal communities and island nations due to melting ice caps.",
        "Renewable energy technologies like solar and wind power are becoming increasingly cost-effective.",
        "Greenhouse gas emissions from fossil fuels are the primary driver of anthropogenic climate change.",
        "Ocean acidification is affecting marine ecosystems and coral reef systems globally.",
        "Extreme weather events are becoming more frequent and severe due to climate disruption.",
        "Carbon capture and storage technologies offer potential solutions for reducing atmospheric CO2.",
        "Deforestation in tropical regions contributes significantly to global carbon emissions.",
        "Electric vehicles are gaining market share as alternatives to fossil fuel transportation.",
        "Climate adaptation strategies are essential for vulnerable communities facing environmental changes.",
        "Artificial intelligence applications are being developed to optimize energy consumption patterns.",
        "Machine learning algorithms can predict weather patterns with improved accuracy and reliability.",
        "Deep learning models are used for image recognition and natural language processing tasks.",
        "Neural networks require significant computational resources for training and inference operations.",
        "Data science techniques help extract insights from large datasets in various industries.",
        "Software engineering practices ensure reliable and maintainable code development processes.",
        "Cloud computing platforms provide scalable infrastructure for modern application deployment.",
        "Cybersecurity measures protect against increasingly sophisticated digital threats and attacks.",
        "Database management systems handle storage and retrieval of structured information efficiently.",
        "Web development frameworks enable rapid creation of interactive online applications."
    ]
    
    # Expand to desired count by cycling through and adding variations
    documents = []
    for i in range(count):
        base_doc = base_docs[i % len(base_docs)]
        # Add slight variations to make each document unique
        variation = f" Document variant {i + 1} with additional context and specificity."
        documents.append(base_doc + variation)
    
    return documents


def test_production_scale_reranking():
    """Test reranker performance with production-scale document counts."""
    
    print("🏭 Testing Production-Scale Reranking Performance")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    query = "climate emergency and global warming effects on environment"
    
    # Test different document counts to find performance characteristics
    test_sizes = [50, 100, 200, 300]
    
    for doc_count in test_sizes:
        print(f"\n📊 Testing with {doc_count} documents...")
        
        documents = generate_test_documents(doc_count)
        
        request_data = {
            "query": query,
            "passages": documents,
            "batch_size": 64  # Use larger batch size for production
        }
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{base_url}/rerank",
                json=request_data,
                timeout=300  # 5 minute timeout for large batches
            )
            
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                processing_time = result.get("processing_time", total_time)
                scores = result.get("scores", [])
                
                docs_per_sec = len(scores) / processing_time if processing_time > 0 else 0
                
                print(f"✅ Success - {doc_count} documents")
                print(f"   Processing time: {processing_time:.2f}s")
                print(f"   Total time: {total_time:.2f}s")
                print(f"   Performance: {docs_per_sec:.1f} docs/sec")
                print(f"   Scores received: {len(scores)}")
                
                # Performance evaluation
                if docs_per_sec >= 10:
                    status = "🚀 EXCELLENT"
                elif docs_per_sec >= 5:
                    status = "✅ GOOD"
                elif docs_per_sec >= 2:
                    status = "⚠️  ACCEPTABLE"
                else:
                    status = "❌ TOO SLOW"
                
                print(f"   Status: {status}")
                
                # Production readiness assessment
                if doc_count == 300:
                    print(f"\n🎯 PRODUCTION ASSESSMENT for 300 documents:")
                    print(f"   Current: {docs_per_sec:.1f} docs/sec")
                    print(f"   Time: {processing_time:.1f}s")
                    
                    if docs_per_sec >= 5:
                        print("   ✅ PRODUCTION READY - Good performance")
                    elif docs_per_sec >= 2:
                        print("   ⚠️  MARGINAL - Consider optimization")
                    else:
                        print("   ❌ NOT READY - Requires optimization or scaling")
                        print("   💡 Recommendations:")
                        print("      - Add GPU acceleration")
                        print("      - Scale horizontally with multiple instances")
                        print("      - Consider lighter model")
                        print("      - Implement document pre-filtering")
                
            else:
                print(f"❌ Failed - {doc_count} documents")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT - {doc_count} documents (>5 minutes)")
            print("   This indicates the current solution is not production-ready")
        except Exception as e:
            print(f"❌ ERROR - {doc_count} documents: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 ANALYSIS COMPLETE")
    print("\n💡 SCALING OPTIONS IF PERFORMANCE IS INSUFFICIENT:")
    print("1. 🖥️  GPU Acceleration (NVIDIA/Apple Metal)")
    print("2. 📈 Horizontal Scaling (multiple reranker instances)")
    print("3. 🏃 Faster Model (trade accuracy for speed)")
    print("4. 🔄 Hybrid Approach (pre-filter + rerank top candidates)")
    print("5. ⚡ Async Processing (return top results first, refine later)")


if __name__ == "__main__":
    test_production_scale_reranking()
