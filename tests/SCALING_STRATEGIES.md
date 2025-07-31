# Production Scaling Strategies for Reranker Service

## Current Performance Analysis

Based on our testing:
- **Small batches (4-15 docs)**: 1.5-3 docs/sec ✅
- **Medium batches (50-100 docs)**: Need to test
- **Large batches (300+ docs)**: **Likely too slow for production**

## Scaling Strategy Options

### Option 1: GPU Acceleration 🚀
**Best Option for Single Instance Performance**

**Setup:**
```yaml
# docker-compose.yaml
services:
  reranker:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

**Expected Improvement:** 5-10x faster (5-15 docs/sec → 25-150 docs/sec)
**Cost:** Requires GPU hardware
**Best for:** High-performance single instance

### Option 2: Horizontal Scaling 📈
**Best Option for High Availability**

**Setup:**
```yaml
# docker-compose.yaml
services:
  reranker:
    deploy:
      replicas: 3
  
  reranker-loadbalancer:
    image: nginx:alpine
    # Load balance across reranker instances
```

**Expected Improvement:** 3x throughput (1.5 docs/sec → 4.5 docs/sec total)
**Cost:** 3x memory/CPU usage
**Best for:** Reliability and distributed load

### Option 3: Faster Model ⚡
**Best Option for Speed Over Accuracy**

**Models to consider:**
- `ms-marco-MiniLM-L-6-v2` (much faster, slightly less accurate)
- `all-MiniLM-L6-v2` (very fast, basic reranking)

**Expected Improvement:** 3-5x faster
**Cost:** Reduced accuracy (trade-off)

### Option 4: Hybrid Approach 🔄
**Best Option for Large Document Sets**

**Strategy:**
1. Pre-filter to top 100 candidates using fast similarity
2. Rerank only top candidates with high-accuracy model
3. Return ranked results

**Expected Improvement:** 10x faster for large sets
**Cost:** Slight accuracy reduction, more complexity

### Option 5: Better ONNX Implementation 🔧
**Revisit ONNX with Proper Optimization**

Our ONNX failed because:
- Wrong runtime provider
- Suboptimal quantization
- Poor batching implementation

**Modern ONNX setup:**
```python
# Use optimized ONNX Runtime
providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
session = onnxruntime.InferenceSession(model_path, providers=providers)

# Proper quantization
from optimum.onnxruntime import ORTQuantizer
quantizer = ORTQuantizer.from_pretrained(model_path)
quantized_model = quantizer.quantize(save_dir=save_dir)
```

## Recommendation Matrix

| Document Count | Best Strategy | Expected Performance | Implementation |
|----------------|---------------|---------------------|----------------|
| < 50 docs | Current CrossEncoder | 2-3 docs/sec | ✅ Already implemented |
| 50-100 docs | GPU + Current | 15-30 docs/sec | Add GPU support |
| 100-200 docs | GPU + Larger batches | 20-40 docs/sec | GPU + batch optimization |
| 300+ docs | Hybrid or Horizontal | 10-50 docs/sec | Pre-filter + rerank |

## Implementation Priority

1. **Test current performance at scale** (300 docs)
2. **If < 2 docs/sec**: Implement GPU acceleration
3. **If still slow**: Consider hybrid approach
4. **For high availability**: Add horizontal scaling

## Code Changes Required

### For GPU Support:
```dockerfile
# Dockerfile
FROM nvidia/cuda:11.8-runtime-ubuntu20.04
# Install CUDA-enabled PyTorch
```

### For Hybrid Approach:
```python
def hybrid_rerank(query, documents, top_k=50):
    # Step 1: Fast pre-filtering
    fast_scores = embedding_similarity(query, documents)
    top_candidates = select_top_k(documents, fast_scores, top_k)
    
    # Step 2: High-accuracy reranking
    final_scores = crossencoder_rerank(query, top_candidates)
    return final_scores
```
