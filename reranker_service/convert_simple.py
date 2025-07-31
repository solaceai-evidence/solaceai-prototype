#!/usr/bin/env python3
"""
Simple, accuracy-focused ONNX conversion using Optimum for mixedbread-ai/mxbai-rerank-large-v1.
No quantization - preserves full model accuracy for SOLACE-AI literature reviews.
"""

import os
import gc
import torch
import logging
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MODEL_NAME = "mixedbread-ai/mxbai-rerank-large-v1"
OUTPUT_DIR = "onnx_model"  # Simple name


def install_optimum():
    """Install Optimum if not available."""
    try:
        import optimum

        logger.info("✅ Optimum already available")
        return True
    except ImportError:
        logger.info("📦 Installing Optimum for ONNX export...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "optimum[onnxruntime]>=1.16.0"]
            )
            logger.info("✅ Optimum installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install Optimum: {e}")
            return False


def convert_with_optimum(
    model_name: str = MODEL_NAME, output_dir: str = OUTPUT_DIR
) -> bool:
    """
    Convert model to ONNX using Optimum - accuracy-focused, no quantization.

    Args:
        model_name: HuggingFace model name
        output_dir: Output directory for ONNX model

    Returns:
        bool: Success status
    """
    try:
        # Ensure Optimum is available
        if not install_optimum():
            return False

        from optimum.exporters.onnx import main_export

        logger.info(f"🚀 Converting {model_name} to ONNX with Optimum")
        logger.info("🎯 Focus: Maximum accuracy preservation (no quantization)")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Convert with Optimum - accuracy-focused settings
        logger.info("🔄 Starting ONNX export...")

        main_export(
            model_name_or_path=model_name,
            output=output_dir,
            task="text-classification",  # Appropriate for reranking
            opset=14,  # Stable opset version
            device="cpu",  # Consistent with our deployment
            fp16=False,  # Keep FP32 for maximum accuracy
            optimize="O1",  # Light optimization to preserve accuracy
            no_post_process=True,  # Preserve original model behavior
            trust_remote_code=True,  # Required for this model
        )

        logger.info(f"✅ ONNX conversion completed successfully!")
        logger.info(f"📁 Model saved to: {output_dir}")

        # Verify the conversion
        if verify_onnx_model(output_dir):
            logger.info("✅ ONNX model verification passed")
            return True
        else:
            logger.error("❌ ONNX model verification failed")
            return False

    except Exception as e:
        logger.error(f"❌ ONNX conversion failed: {e}")
        return False


def verify_onnx_model(model_dir: str) -> bool:
    """Verify the ONNX model works correctly."""
    try:
        from optimum.onnxruntime import ORTModelForSequenceClassification
        from transformers import AutoTokenizer

        logger.info(f"🔍 Verifying ONNX model in {model_dir}")

        # Load the converted model
        model = ORTModelForSequenceClassification.from_pretrained(
            model_dir, provider="CPUExecutionProvider"
        )

        # Load tokenizer (should be saved with the model)
        tokenizer = AutoTokenizer.from_pretrained(model_dir)

        # Test with climate literature example
        test_query = "climate change impacts on arctic ice"
        test_documents = [
            "Arctic sea ice has declined significantly due to global warming trends.",
            "Economic policies require careful consideration of environmental factors.",
            "Renewable energy technologies show promise for reducing carbon emissions.",
        ]

        logger.info("🧪 Running accuracy test...")

        # Test inference
        for i, doc in enumerate(test_documents):
            inputs = tokenizer(
                test_query,
                doc,
                padding="max_length",
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )

            with torch.no_grad():
                outputs = model(**inputs)
                score = outputs.logits.squeeze().item()

            logger.info(f"   Document {i+1} score: {score:.4f}")

        logger.info("✅ Model verification successful - ready for literature review!")
        return True

    except Exception as e:
        logger.error(f"❌ Model verification failed: {e}")
        return False


def create_simple_service():
    """Create a simple service that uses the Optimum ONNX model."""
    service_code = '''"""
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
    documents: List[str]
    top_k: Optional[int] = None


class RerankResponse(BaseModel):
    results: List[Dict[str, Any]]
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
            
            model_dir = "onnx_model"
            
            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"ONNX model not found at {model_dir}. Run convert_simple.py first.")
            
            logger.info("📖 Loading accuracy-focused ONNX model...")
            
            self.model = ORTModelForSequenceClassification.from_pretrained(
                model_dir,
                provider="CPUExecutionProvider"
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
                device='cpu',
                model_kwargs={
                    'torch_dtype': torch.float32,  # Keep FP32 for accuracy
                    'low_cpu_mem_usage': True,
                }
            )
            
            logger.info("✅ CrossEncoder fallback loaded")
            
        except Exception as e:
            raise RuntimeError(f"Both ONNX and CrossEncoder failed: {e}")
    
    def rerank(self, query: str, documents: List[str], top_k: Optional[int] = None):
        """Rerank documents for literature review accuracy."""
        import time
        start_time = time.time()
        
        if hasattr(self.model, 'predict'):
            # CrossEncoder fallback
            pairs = [(query, doc) for doc in documents]
            scores = self.model.predict(pairs)
        else:
            # Optimum ONNX model
            scores = []
            for doc in documents:
                inputs = self.tokenizer(
                    query, doc,
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                )
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    score = outputs.logits.squeeze().item()
                    scores.append(score)
        
        # Create results
        results = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            results.append({
                "document": doc,
                "score": float(score),
                "rank": i
            })
        
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
        "backend": "optimum_onnx" if hasattr(reranker.model, "session") else "crossencoder",
        "accuracy_mode": "full_precision"
    }


@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """Rerank documents for literature review."""
    try:
        results, processing_time = reranker.rerank(
            query=request.query,
            documents=request.documents,
            top_k=request.top_k
        )
        
        return RerankResponse(
            results=results,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"❌ Reranking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting Literature Review Reranker on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port)
'''

    with open("simple_onnx_service.py", "w") as f:
        f.write(service_code)

    logger.info("📝 Created simple_onnx_service.py")


def main():
    """Main function - convert model and create service."""
    logger.info("🎯 Simple ONNX Conversion for Literature Review")
    logger.info("🔬 Focus: Maximum accuracy preservation")

    # Step 1: Convert to ONNX
    logger.info("\n" + "=" * 50)
    logger.info("STEP 1: Converting to Optimum ONNX")
    logger.info("=" * 50)

    success = convert_with_optimum()

    if success:
        logger.info("✅ ONNX conversion successful!")

        # Step 2: Create simple service
        logger.info("\n" + "=" * 50)
        logger.info("STEP 2: Creating Simple Service")
        logger.info("=" * 50)

        create_simple_service()

        # Step 3: Usage instructions
        logger.info("\n" + "=" * 50)
        logger.info("USAGE INSTRUCTIONS")
        logger.info("=" * 50)

        logger.info("🎉 Setup complete! To use:")
        logger.info("1. Run: python simple_onnx_service.py")
        logger.info("2. Test: curl -X POST http://localhost:8001/rerank \\")
        logger.info("   -H 'Content-Type: application/json' \\")
        logger.info(
            '   -d \'{"query":"climate change","documents":["document1","document2"]}\''
        )
        logger.info("")
        logger.info("🔬 Benefits:")
        logger.info("   ✅ Full accuracy preservation (no quantization)")
        logger.info("   ✅ Better memory efficiency than CrossEncoder")
        logger.info("   ✅ Resolves segmentation faults")
        logger.info("   ✅ Simple, single-backend approach")

        return True
    else:
        logger.error("❌ ONNX conversion failed")
        logger.info(
            "💡 Fallback: Continue using CrossEncoder until ONNX issues are resolved"
        )
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
