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
                 batch_size: int = 64,
                 timeout: float = None):
        # Get service URL from environment variable (set by Docker Compose)
        self.service_url = os.getenv("RERANKER_SERVICE_URL", "http://localhost:10001").rstrip('/')
        self.model_name_or_path = model_name_or_path
        self.reranker_type = reranker_type
        self.batch_size = batch_size
        # Use environment variable for timeout, fall back to parameter, then default
        self.timeout = timeout or float(os.getenv("RERANKER_CLIENT_TIMEOUT", "120.0"))
        self.device = "remote"  # Indicate this is a remote service
        
        logger.info(f"Initialized RemoteRerankerClient: {self.service_url} with model: {model_name_or_path}, batch_size: {batch_size}")
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to remote service"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.service_url}/health")
                if response.status_code == 200:
                    logger.info(">> Connected to remote reranker service")
                else:
                    logger.warning(f"Service health check failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to reranker service: {e}")
            raise ConnectionError(f"Cannot connect to reranker service at {self.service_url}")
    
    def get_scores(self, query: str, passages: List[str]) -> List[float]:
        """Get scores from remote service - same interface as local rerankers"""
        try:
            request_data = {
                "query": query,
                "passages": passages,
                "model_name_or_path": self.model_name_or_path,
                "reranker_type": self.reranker_type,
                "batch_size": self.batch_size
            }
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.service_url}/rerank", json=request_data)
                
                if response.status_code != 200:
                    raise Exception(f"Service error: {response.status_code} - {response.text}")
                
                result = response.json()
                # Log the actual device being used by the remote service
                if "device" in result:
                    logger.info(f"Remote reranker using device: {result['device']}")
                return result["scores"]
                
        except httpx.TimeoutException:
            logger.error(f"Timeout after {self.timeout}s")
            raise Exception("Remote reranker timeout")
        except Exception as e:
            logger.error(f"Remote reranker error: {e}")
            raise
