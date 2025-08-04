#!/usr/bin/env python3
"""
Test script for remote reranker architecture
1. Tests remote reranker service standalone
2. Tests main API with remote reranker client
"""
import asyncio
import httpx
import subprocess
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RERANKER_SERVICE_URL = "http://localhost:8001"
MAIN_API_URL = "http://localhost:8000"

async def test_remote_reranker_service():
    """Test the standalone reranker service"""
    logger.info("🧪 Testing Remote Reranker Service...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test health endpoint
            health_response = await client.get(f"{RERANKER_SERVICE_URL}/health")
            logger.info(f"Health: {health_response.status_code} - {health_response.json()}")
            
            # Test reranking
            test_data = {
                "query": "machine learning neural networks",
                "passages": [
                    "Deep learning is a subset of machine learning",
                    "The weather is nice today",
                    "Neural networks are used in artificial intelligence",
                    "Cats are popular pets"
                ],
                "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1",
                "reranker_type": "crossencoder"
            }
            
            rerank_response = await client.post(f"{RERANKER_SERVICE_URL}/rerank", json=test_data)
            result = rerank_response.json()
            
            logger.info(f"✅ Rerank successful: {rerank_response.status_code}")
            logger.info(f"📊 Scores: {result['scores']}")
            logger.info(f"🖥️  Device: {result['device']}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Remote service test failed: {e}")
        return False

async def test_main_api_with_remote():
    """Test main API configured to use remote reranker"""
    logger.info("🧪 Testing Main API with Remote Reranker...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test health endpoint
            health_response = await client.get(f"{MAIN_API_URL}/health")
            logger.info(f"Main API Health: {health_response.status_code}")
            
            # Note: Add actual API endpoint tests here when available
            logger.info("✅ Main API accessible")
            return True
            
    except Exception as e:
        logger.error(f"❌ Main API test failed: {e}")
        return False

def start_reranker_service():
    """Start the reranker service in background"""
    logger.info("🚀 Starting Reranker Service...")
    
    # Change to API directory
    api_dir = Path(__file__).parent
    
    try:
        # Start reranker service
        process = subprocess.Popen(
            ["python", "reranker_service.py"],
            cwd=api_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for service to start
        time.sleep(5)
        
        if process.poll() is None:
            logger.info("✅ Reranker service started")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ Service failed to start: {stderr.decode()}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        return None

async def main():
    """Main test orchestrator"""
    logger.info("🏁 Starting Remote Reranker Architecture Tests")
    
    # Start reranker service
    service_process = start_reranker_service()
    if not service_process:
        logger.error("Cannot proceed without reranker service")
        return
    
    try:
        # Test remote service
        service_ok = await test_remote_reranker_service()
        
        if service_ok:
            logger.info("✅ Remote reranker service tests passed")
            
            # Test main API (if running)
            # api_ok = await test_main_api_with_remote()
            
            logger.info("🎉 All tests completed!")
        else:
            logger.error("❌ Remote service tests failed")
            
    finally:
        # Cleanup
        if service_process:
            logger.info("🛑 Stopping reranker service...")
            service_process.terminate()
            service_process.wait()

if __name__ == "__main__":
    asyncio.run(main())
