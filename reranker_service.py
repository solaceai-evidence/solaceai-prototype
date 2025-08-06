#!/usr/bin/env python3
"""
Standalone Reranker Service Server
Designed to work alongside containerized main API
"""
import logging
import uvicorn
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import os
import torch
from threading import Lock
import psutil
import gc

# Get host and port 
host = os.getenv("RERANKER_HOST", "0.0.0.0")
port = int(os.getenv("RERANKER_PORT", "8001"))
max_workers = int(os.getenv("MAX_WORKERS", "1"))
log_level = os.getenv("LOG_LEVEL", "INFO")

# Use existing reranker infrastructure 
from api.scholarqa.rag.reranker.reranker_base import RERANKER_MAPPING

# Configure logging
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global reranker instances - thread-safe lazy loading
_reranker_cache: Dict[str, Any] = {}
_cache_lock = Lock()
_request_count = 0
_start_time = time.time()

class RerankRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    passages: List[str] = Field(..., min_items=1, max_items=1000)
    model_name_or_path: str = Field(default="mixedbread-ai/mxbai-rerank-large-v1")
    reranker_type: str = Field(default="crossencoder")
    batch_size: int = Field(default=64, ge=1, le=256)
    top_k: Optional[int] = Field(default=None, ge=1)
    
    @field_validator('passages')
    @classmethod
    def validate_passages(cls, v):
        if any(len(passage.strip()) == 0 for passage in v):
            raise ValueError("All passages must be non-empty")
        return v

class RerankResponse(BaseModel):
    scores: List[float]
    ranked_indices: List[int]
    model_used: str
    device: str
    processing_time_ms: float
    top_k_applied: Optional[int] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: float
    requests_processed: int
    available_rerankers: List[str]
    device_info: Dict[str, Any]
    memory_usage: Dict[str, float]
    cached_models: List[str]

class ModelInfo(BaseModel):
    model_name: str
    reranker_type: str
    device: str
    memory_usage_mb: Optional[float] = None
    last_used: float

def get_device_info() -> Dict[str, Any]:
    """Get device information"""
    info = {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(),
    }
    
    # Check for MPS (Apple Silicon)
    if torch.backends.mps.is_available():
        info["mps_available"] = True
        info["primary_device"] = "mps"
    elif torch.cuda.is_available():
        info["cuda_available"] = True
        info["cuda_device_count"] = torch.cuda.device_count()
        info["primary_device"] = "cuda"
    else:
        info["primary_device"] = "cpu"
    
    return info

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage"""
    memory = psutil.virtual_memory()
    return {
        "total_gb": memory.total / (1024**3),
        "available_gb": memory.available / (1024**3),
        "used_gb": memory.used / (1024**3),
        "percent": memory.percent
    }

def get_reranker(reranker_type: str, model_name_or_path: str, batch_size: int = 64):
    """Get or create reranker instance with thread-safe caching"""
    cache_key = f"{reranker_type}:{model_name_or_path}:{batch_size}"
    
    with _cache_lock:
        if cache_key not in _reranker_cache:
            if reranker_type not in RERANKER_MAPPING:
                raise ValueError(f"Unknown reranker type: {reranker_type}")
            
            logger.info(f"Initializing {reranker_type} with {model_name_or_path}, batch_size: {batch_size}")
            reranker_class = RERANKER_MAPPING[reranker_type]
            
            try:
                # Try with batch_size parameter
                reranker = reranker_class(model_name_or_path=model_name_or_path, batch_size=batch_size)
            except TypeError:
                # Fallback for rerankers that don't support batch_size parameter
                logger.warning(f"Reranker {reranker_type} doesn't support batch_size parameter, using default")
                reranker = reranker_class(model_name_or_path=model_name_or_path)
            
            # Force to MPS if available (for Apple Silicon)
            if hasattr(reranker, 'model') and torch.backends.mps.is_available():
                try:
                    if hasattr(reranker.model, 'to'):
                        reranker.model = reranker.model.to('mps')
                        reranker.device = 'mps'
                        logger.info(f"Moved model to MPS device")
                except Exception as e:
                    logger.warning(f"Could not move model to MPS: {e}")
            
            _reranker_cache[cache_key] = {
                'model': reranker,
                'last_used': time.time(),
                'usage_count': 0
            }
            logger.info(f"Cached reranker: {cache_key}")
        
        # Update usage statistics
        _reranker_cache[cache_key]['last_used'] = time.time()
        _reranker_cache[cache_key]['usage_count'] += 1
        
    return _reranker_cache[cache_key]['model']

async def cleanup_unused_models():
    """Background task to cleanup unused models"""
    current_time = time.time()
    cleanup_threshold = 30 * 60  # 30 minutes
    
    with _cache_lock:
        keys_to_remove = []
        for key, cache_info in _reranker_cache.items():
            if current_time - cache_info['last_used'] > cleanup_threshold:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            logger.info(f"Cleaning up unused model: {key}")
            del _reranker_cache[key]
            gc.collect()  # Force garbage collection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Reranker Service...")
    
    # Startup
    device_info = get_device_info()
    logger.info(f"Device info: {device_info}")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    logger.info("Shutting down Reranker Service...")
    
    # Cleanup all cached models
    with _cache_lock:
        _reranker_cache.clear()
    gc.collect()

async def periodic_cleanup():
    """Periodic cleanup task"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            await cleanup_unused_models()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

# FastAPI app with lifespan management
app = FastAPI(
    title="Solace AI Reranker Service", 
    version="1.1.0",
    description="High-performance reranking service with GPU acceleration",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    global _request_count, _start_time
    
    uptime = time.time() - _start_time
    
    with _cache_lock:
        cached_models = list(_reranker_cache.keys())
    
    return HealthResponse(
        status="healthy",
        service="reranker",
        version="1.1.0",
        uptime_seconds=uptime,
        requests_processed=_request_count,
        available_rerankers=list(RERANKER_MAPPING.keys()),
        device_info=get_device_info(),
        memory_usage=get_memory_usage(),
        cached_models=cached_models
    )

@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest, background_tasks: BackgroundTasks):
    """Rerank documents using specified model"""
    global _request_count
    _request_count += 1
    
    start_time = time.time()
    
    try:
        reranker = get_reranker(request.reranker_type, request.model_name_or_path, request.batch_size)
        
        # Get scores
        scores = reranker.get_scores(request.query, request.passages)
        
        # Create ranked indices (descending order)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        # Apply top_k if specified
        top_k_applied = None
        if request.top_k is not None:
            top_k = min(request.top_k, len(ranked_indices))
            ranked_indices = ranked_indices[:top_k]
            scores = [scores[i] for i in ranked_indices]
            top_k_applied = top_k
        
        # Get device info
        device = "unknown"
        if hasattr(reranker, 'device'):
            device = str(reranker.device)
        elif hasattr(reranker, 'model') and hasattr(reranker.model, 'device'):
            device = str(reranker.model.device)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        logger.info(f"Processed rerank request: {len(request.passages)} passages, "
                   f"{processing_time:.2f}ms, device: {device}")
        
        return RerankResponse(
            scores=scores,
            ranked_indices=ranked_indices,
            model_used=request.model_name_or_path,
            device=device,
            processing_time_ms=processing_time,
            top_k_applied=top_k_applied
        )
        
    except Exception as e:
        logger.error(f"Reranking error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_cached_models():
    """List currently cached models with usage statistics"""
    with _cache_lock:
        models = []
        for key, cache_info in _reranker_cache.items():
            parts = key.split(":")
            reranker_type, model_name = parts[0], parts[1]
            batch_size = parts[2] if len(parts) > 2 else "default"
            
            device = "unknown"
            if hasattr(cache_info['model'], 'device'):
                device = str(cache_info['model'].device)
            
            models.append({
                "cache_key": key,
                "reranker_type": reranker_type,
                "model_name": model_name,
                "batch_size": batch_size,
                "device": device,
                "last_used": cache_info['last_used'],
                "usage_count": cache_info['usage_count']
            })
    
    return {"cached_models": models, "total_count": len(models)}

@app.delete("/models/{cache_key}")
async def remove_cached_model(cache_key: str):
    """Remove a specific cached model"""
    with _cache_lock:
        if cache_key in _reranker_cache:
            del _reranker_cache[cache_key]
            gc.collect()
            logger.info(f"Removed cached model: {cache_key}")
            return {"message": f"Model {cache_key} removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Model not found in cache")

@app.post("/models/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of unused models"""
    await cleanup_unused_models()
    return {"message": "Cleanup completed"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Solace-AI Remote Reranker Service",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    logger.info(f"Starting Solace-AI Remote Reranker Service on {host}:{port}...")
    logger.info(f"Max workers: {max_workers}, Log level: {log_level}")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        log_level=log_level.lower(),
        workers=max_workers,
        # Enable auto-reload in development
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )