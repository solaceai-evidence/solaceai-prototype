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

# Use existing reranker infrastructure - no code duplication
from scholarqa.rag.reranker.reranker_base import RERANKER_MAPPING

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class RerankRequest(BaseModel):
    query: str
    passages: List[str]
    model_name_or_path: str = "mixedbread-ai/mxbai-rerank-large-v1"
    reranker_type: str = "crossencoder"

class RerankResponse(BaseModel):
    scores: List[float]
    model_used: str
    device: str

class HealthResponse(BaseModel):
    status: str
    service: str
    available_rerankers: List[str]

# FastAPI app
app = FastAPI(title="Solace AI Reranker Service", version="1.0.0")

# Global reranker instances - lazy loading
_reranker_cache = {}

def get_reranker(reranker_type: str, model_name_or_path: str):
    """Get or create reranker instance with caching"""
    cache_key = f"{reranker_type}:{model_name_or_path}"
    
    if cache_key not in _reranker_cache:
        if reranker_type not in RERANKER_MAPPING:
            raise ValueError(f"Unknown reranker type: {reranker_type}")
        
        logger.info(f"🔄 Initializing {reranker_type} with {model_name_or_path}")
        
        # Use existing reranker classes
        reranker_class = RERANKER_MAPPING[reranker_type]
        reranker = reranker_class(model_name_or_path=model_name_or_path)
        
        _reranker_cache[cache_key] = reranker
        logger.info(f" Cached reranker: {cache_key}")
    
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
        # Get reranker instance
        reranker = get_reranker(request.reranker_type, request.model_name_or_path)
        
        # Get scores using existing infrastructure
        scores = reranker.get_scores(request.query, request.passages)
        
        # Detect device info if available
        device = "unknown"
        if hasattr(reranker, 'device'):
            device = str(reranker.device)
        
        return RerankResponse(
            scores=scores,
            model_used=request.model_name_or_path,
            device=device
        )
        
    except Exception as e:
        logger.error(f" Reranking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Solace AI Reranker Service", "docs": "/docs"}

if __name__ == "__main__":
    logger.info(" Starting Solace AI Reranker Service")
    
    # Run the service
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info"
    )
import logging
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Reuse existing reranker infrastructure
from scholarqa.rag.reranker.reranker_base import RERANKER_MAPPING

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Native Reranker Service", version="1.0.0")

# Global reranker instance (lazy loaded)
_reranker = None
_current_config = None

class RerankRequest(BaseModel):
    query: str
    passages: List[str]
    model_name_or_path: str = "mixedbread-ai/mxbai-rerank-large-v1"
    reranker_type: str = "crossencoder"

class RerankResponse(BaseModel):
    scores: List[float]

def get_reranker(reranker_type: str, model_name_or_path: str):
    """Get or create reranker instance (reuse existing if same config)"""
    global _reranker, _current_config
    
    config = (reranker_type, model_name_or_path)
    if _reranker is None or _current_config != config:
        logger.info(f"Initializing {reranker_type} reranker with model: {model_name_or_path}")
        
        reranker_class = RERANKER_MAPPING.get(reranker_type)
        if not reranker_class:
            raise ValueError(f"Unknown reranker type: {reranker_type}")
        
        _reranker = reranker_class(model_name_or_path)
        _current_config = config
        logger.info("Reranker initialized successfully")
    
    return _reranker

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "native-reranker", "has_model": _reranker is not None}

@app.post("/rerank", response_model=RerankResponse)
async def rerank_passages(request: RerankRequest):
    try:
        reranker = get_reranker(request.reranker_type, request.model_name_or_path)
        scores = reranker.get_scores(request.query, request.passages)
        
        logger.info(f"Reranked {len(request.passages)} passages")
        return RerankResponse(scores=scores)
        
    except Exception as e:
        logger.error(f"Reranking error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reranking failed: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Native Reranker Service on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
