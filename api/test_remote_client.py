#!/usr/bin/env python3
"""
Test the RemoteRerankerClient integration
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import logging
from scholarqa.rag.reranker.remote_reranker import RemoteRerankerClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_remote_client():
    """Test the remote reranker client"""
    logger.info("🧪 Testing RemoteRerankerClient...")
    
    try:
        # Initialize remote client
        client = RemoteRerankerClient(
            service_url="http://localhost:8001",
            model_name_or_path="mixedbread-ai/mxbai-rerank-large-v1",
            reranker_type="crossencoder"
        )
        
        # Test query
        query = "machine learning algorithms"
        passages = [
            "Random forests are ensemble learning methods",
            "Today is a sunny day",
            "Support vector machines are powerful classifiers", 
            "Pizza is delicious food"
        ]
        
        logger.info(f"🔍 Query: {query}")
        logger.info(f"📄 Testing {len(passages)} passages")
        
        # Get scores
        scores = client.get_scores(query, passages)
        
        logger.info(f"✅ Scores received: {scores}")
        
        # Verify scores make sense
        assert len(scores) == len(passages), "Score count mismatch"
        assert all(isinstance(s, float) for s in scores), "Invalid score types"
        
        # ML-related passages should score higher
        ml_scores = [scores[0], scores[2]]  # Random forests, SVMs
        other_scores = [scores[1], scores[3]]  # Weather, pizza
        
        logger.info(f"📊 ML-related scores: {ml_scores}")
        logger.info(f"📊 Other scores: {other_scores}")
        
        if max(ml_scores) > max(other_scores):
            logger.info("✅ Reranking appears to work correctly!")
        else:
            logger.warning("⚠️ Unexpected score pattern")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Remote client test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_remote_client()
    exit(0 if success else 1)
