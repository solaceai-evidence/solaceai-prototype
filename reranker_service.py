
#!/usr/bin/env python3
"""
Standalone Reranker Service Server
Designed to work alongside containerized main API
"""
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os

# Get host and port 
host = "0.0.0.0"
port = int(os.getenv("RERANKER_PORT", "8001"))

# Use existing reranker infrastructure 
from api.scholarqa.rag.reranker.reranker_base import RERANKER_MAPPING

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Solace AI Reranker Service", version="1.0.0")

# Global reranker instances - lazy loading
_reranker_cache = {}

class RerankRequest(BaseModel):
    query: str
    passages: List[str]
    model_name_or_path: str = "mixedbread-ai/mxbai-rerank-large-v1"
    reranker_type: str = "crossencoder"
    batch_size: int = 64

class RerankResponse(BaseModel):
    scores: List[float]
    model_used: str
    device: str

class HealthResponse(BaseModel):
    status: str
    service: str
    available_rerankers: List[str]

def get_reranker(reranker_type: str, model_name_or_path: str, batch_size: int = 64):
    """Get or create reranker instance with caching"""
    cache_key = f"{reranker_type}:{model_name_or_path}:{batch_size}"
    if cache_key not in _reranker_cache:
        if reranker_type not in RERANKER_MAPPING:
            raise ValueError(f"Unknown reranker type: {reranker_type}")
        logger.info(f"Initializing {reranker_type} with {model_name_or_path}, batch_size: {batch_size}")
        reranker_class = RERANKER_MAPPING[reranker_type]
        
        # Pass batch_size if the reranker supports it
        try:
            reranker = reranker_class(model_name_or_path=model_name_or_path, batch_size=batch_size)
        except TypeError:
            # Fallback for rerankers that don't support batch_size parameter
            logger.warning(f"Reranker {reranker_type} doesn't support batch_size parameter, using default")
            reranker = reranker_class(model_name_or_path=model_name_or_path)
            
        _reranker_cache[cache_key] = reranker
        logger.info(f"Cached reranker: {cache_key}")
    return _reranker_cache[cache_key]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="reranker",
        available_rerankers=list(RERANKER_MAPPING.keys())
    )

@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """Rerank documents using specified model"""
    try:
        reranker = get_reranker(request.reranker_type, request.model_name_or_path, request.batch_size)
        scores = reranker.get_scores(request.query, request.passages)
        device = "unknown"
        if hasattr(reranker, 'device'):
            device = str(reranker.device)
        return RerankResponse(
            scores=scores,
            model_used=request.model_name_or_path,
            device=device
        )
    except Exception as e:
        logger.error(f"Reranking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Solace-AI Remote Reranker Service", "docs": "/docs"}

if __name__ == "__main__":
    logger.info(f"Starting Solace-AI Remote Reranker Service on {host}:{port}...")
    uvicorn.run(app, host=host, port=port, log_level="info")
