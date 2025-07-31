"""
Simple, accuracy-focused reranker service using Optimum ONNX.
No quantization - preserves full accuracy for literature review.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import torch
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Literature Review Reranker", version="1.0.0")


class RerankRequest(BaseModel):
    query: str
    passages: List[str]  # Use 'passages' to match RemoteReranker interface
    documents: Optional[List[str]] = None  # Keep 'documents' for backward compatibility
    batch_size: Optional[int] = 32
    top_k: Optional[int] = None


class RerankResponse(BaseModel):
    results: List[Dict[str, Any]]
    scores: List[float]  # Add scores for RemoteReranker compatibility
    processing_time: float


class AccuracyFocusedReranker:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load the Optimum ONNX model."""
        try:
            from optimum.onnxruntime import ORTModelForSequenceClassification
            from transformers import AutoTokenizer

            # Try multiple possible paths for the ONNX model
            possible_paths = [
                "onnx_model",  # If running from reranker_service/
                "reranker_service/onnx_model",  # If running from project root
                os.path.join(
                    os.path.dirname(__file__), "onnx_model"
                ),  # Relative to this file
            ]

            model_dir = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_dir = path
                    break

            if model_dir is None:
                raise FileNotFoundError(
                    "ONNX model not found in any expected location. Run convert_simple.py first."
                )

            logger.info("📖 Loading accuracy-focused ONNX model...")

            self.model = ORTModelForSequenceClassification.from_pretrained(
                model_dir, provider="CPUExecutionProvider"
            )

            self.tokenizer = AutoTokenizer.from_pretrained(model_dir)

            logger.info("✅ Model loaded successfully - ready for literature review!")

        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            # Fallback to CrossEncoder if ONNX fails
            self._load_crossencoder_fallback()

    def _load_crossencoder_fallback(self):
        """Fallback to CrossEncoder if ONNX fails."""
        try:
            from sentence_transformers import CrossEncoder

            logger.info("🔄 Loading CrossEncoder fallback...")

            self.model = CrossEncoder(
                "mixedbread-ai/mxbai-rerank-large-v1",
                device="cpu",
                model_kwargs={
                    "torch_dtype": torch.float32,  # Keep FP32 for accuracy
                    "low_cpu_mem_usage": True,
                },
            )

            logger.info("✅ CrossEncoder fallback loaded")

        except Exception as e:
            raise RuntimeError(f"Both ONNX and CrossEncoder failed: {e}")

    def rerank(self, query: str, documents: List[str], top_k: Optional[int] = None):
        """Rerank documents for literature review accuracy."""
        import time

        start_time = time.time()

        if hasattr(self.model, "predict"):
            # CrossEncoder fallback
            pairs = [(query, doc) for doc in documents]
            scores = self.model.predict(pairs)
        else:
            # Optimum ONNX model
            scores = []
            for doc in documents:
                inputs = self.tokenizer(
                    query,
                    doc,
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                )

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    score = outputs.logits.squeeze().item()
                    scores.append(score)

        # Create results
        results = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            results.append({"document": doc, "score": float(score), "rank": i})

        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Update ranks after sorting
        for i, result in enumerate(results):
            result["rank"] = i

        # Apply top_k if specified
        if top_k:
            results = results[:top_k]

        processing_time = time.time() - start_time

        return results, processing_time


# Global reranker instance
reranker = AccuracyFocusedReranker()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": "mixedbread-ai/mxbai-rerank-large-v1",
        "backend": (
            "optimum_onnx" if hasattr(reranker.model, "session") else "crossencoder"
        ),
        "accuracy_mode": "full_precision",
    }


@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """Rerank documents for literature review."""
    try:
        # Support both 'passages' (RemoteReranker) and 'documents' (backward compatibility)
        documents = request.passages or request.documents or []

        if not documents:
            raise HTTPException(
                status_code=400,
                detail="Either 'passages' or 'documents' must be provided",
            )

        results, processing_time = reranker.rerank(
            query=request.query, documents=documents, top_k=request.top_k
        )

        # Extract scores for RemoteReranker compatibility
        scores = [result["score"] for result in results]

        return RerankResponse(
            results=results, scores=scores, processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"❌ Reranking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8002"))  # Use 8002 for container compatibility
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"🚀 Starting Literature Review Reranker on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
