"""
Remote Reranker Client - integrates with existing reranker architecture
"""
import os
import logging
from typing import List
import httpx
from .reranker_base import AbstractReranker

logger = logging.getLogger(__name__)

class RemoteRerankerClient(AbstractReranker):
    """Client for remote reranker service - maintains same interface as local rerankers"""
    
    def __init__(self, model_name_or_path: str = "mixedbread-ai/mxbai-rerank-large-v1", 
                 reranker_type: str = "crossencoder", 
                 timeout: float = 60.0):
        self.service_url = os.getenv("RERANKER_SERVICE_URL", "http://localhost:8001").rstrip('/')
        self.model_name_or_path = model_name_or_path
        self.reranker_type = reranker_type
        self.timeout = timeout
        
        logger.info(f"Initialized RemoteRerankerClient: {self.service_url}")
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to remote service"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.service_url}/health")
                if response.status_code == 200:
                    logger.info("✅ Connected to remote reranker service")
                else:
                    logger.warning(f"⚠️ Service health check failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to reranker service: {e}")
            raise ConnectionError(f"Cannot connect to reranker service at {self.service_url}")
    
    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        """Get scores from remote service - same interface as local rerankers"""
        try:
            request_data = {
                "query": query,
                "passages": passages,
                "model_name_or_path": self.model_name_or_path,
                "reranker_type": self.reranker_type
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.service_url}/rerank", json=request_data)
                
                if response.status_code != 200:
                    raise Exception(f"Service error: {response.status_code} - {response.text}")
                
                result = response.json()
                return result["scores"]
                
        except httpx.TimeoutException:
            logger.error(f"Timeout after {self.timeout}s")
            raise Exception("Remote reranker timeout")
        except Exception as e:
            logger.error(f"Remote reranker error: {e}")
            raise
