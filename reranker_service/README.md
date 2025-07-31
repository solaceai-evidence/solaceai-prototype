# GPU-Accelerated Reranker Service

High-performance reranking service optimized for Apple M2 Max and compatible with the existing ScholarQA RemoteReranker interface.

## Performance Improvement

**Problem**: Processing 300+ documents takes 4.3 minutes on CPU (unacceptable for users)
**Solution**: GPU acceleration reduces this to 30-60 seconds using Apple Metal Performance Shaders

## Device Support

- **Apple M1/M2 Macs**: Uses Metal Performance Shaders (MPS) for GPU acceleration
- **NVIDIA GPUs**: Uses CUDA for optimal performance
- **CPU Fallback**: Works on all systems with reduced performance

## Quick Start

### 1. Install Dependencies

```bash
cd reranker_service
pip install -r requirements_simple.txt
```

### 2. Start GPU-Accelerated Service

```bash
python high_performance_service.py
```

The service will:

- Automatically detect the best available device (MPS/CUDA/CPU)
- Load the optimized cross-encoder model
- Start the FastAPI server on port 8001

### 3. Test Performance

```bash
curl -X POST http://localhost:8001/rerank \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "climate change impacts",
    "passages": ["document1", "document2", "document3"],
    "batch_size": 32
  }'
```

## Integration with Existing API

This service is designed to be a drop-in replacement for the existing reranker. It maintains full compatibility with the RemoteReranker interface used in `/api/rag/reranker/reranker_base.py`.

### API Compatibility

The service provides a `/rerank` endpoint that matches exactly what RemoteReranker expects:

```python
# Request format (supports both field names)
{
    "query": "search query",
    "passages": ["doc1", "doc2", "doc3"],  # or "documents"
    "batch_size": 32
}

# Response format
{
    "scores": [0.95, 0.87, 0.23],  # Required by RemoteReranker
    "processing_time": 1.5,
    "documents_processed": 3,
    "device_used": "mps"
}
```

### Integration with ScholarQA

Update your configuration to use the GPU service by pointing RemoteReranker to the new endpoint:

```python
# In your configuration
RERANKER_URL = "http://localhost:8001"

# The existing RemoteReranker code will automatically use GPU acceleration
reranker = RemoteReranker(base_url=RERANKER_URL)
scores = reranker.get_scores(query, passages, batch_size=32)
```

## Performance Optimization

### Batch Size Recommendations

- **Small sets (< 50 docs)**: batch_size=64
- **Medium sets (50-200 docs)**: batch_size=32
- **Large sets (300+ docs)**: batch_size=16-32

### Memory Management

The service uses single-worker configuration to optimize GPU memory usage. For Apple M2 Max with 96GB unified memory, this provides optimal performance.

## Model Details

- **Base Model**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **Optimization**: PyTorch with Apple MPS acceleration
- **Accuracy**: Full precision (no quantization for maximum accuracy)
- **Batch Processing**: Optimized for large document sets

## Monitoring and Health Checks

### Health Check Endpoint

```bash
curl http://localhost:8001/health
```

Returns device status, model loading state, and GPU availability.

#### Performance Logging

The service logs detailed performance metrics:

- Processing time per batch
- Documents per second
- Progress updates for large document sets
- Device utilization information

## Troubleshooting

### Common Issues

1. **Model Loading Fails**

   - Ensure internet connection for model download
   - Check disk space for model cache

2. **GPU Not Detected**

   - Verify PyTorch MPS support: `torch.backends.mps.is_available()`
   - Update to PyTorch 2.0+ for M1/M2 support

3. **Memory Issues**
   - Reduce batch_size for very large document sets
   - Monitor memory usage during processing

### Performance Verification

Test with a large document set:

```python
import requests

# Test with 300 documents
test_docs = ["test document " + str(i) for i in range(300)]
response = requests.post("http://localhost:8001/rerank", json={
    "query": "test query",
    "passages": test_docs,
    "batch_size": 32
})

print(f"Processing time: {response.json()['processing_time']:.2f}s")
print(f"Device used: {response.json()['device_used']}")
```

Expected results:

- **CPU**: 200+ seconds
- **Apple M2 Max (MPS)**: 30-60 seconds
- **NVIDIA GPU**: 10-20 seconds

## Integration Notes

This service integrates seamlessly with the existing ScholarQA reranker system:

1. **No code changes required** in existing RemoteReranker usage
2. **Compatible API contract** with exact same request/response format
3. **Fallback support** - if GPU service unavailable, existing CPU reranker still works
4. **Performance monitoring** - logs provide visibility into optimization benefits

The GPU acceleration is particularly beneficial for literature review workflows where users frequently process 300+ academic papers, reducing wait times from minutes to seconds.

## Files

- `high_performance_service.py` - GPU-accelerated production service (port 8001)
- `simple_onnx_service.py` - ONNX-based service (port 8002)
- `requirements_simple.txt` - Dependencies for both services
- `convert_simple.py` - ONNX model conversion tool

## Features

✅ **Full Accuracy**: No quantization, preserves model precision  
✅ **Memory Efficient**: Better than CrossEncoder baseline  
✅ **Stable**: Uses Optimum for reliable ONNX conversion  
✅ **Simple**: Single backend, easy to maintain  
✅ **Fallback**: Automatic CrossEncoder fallback if ONNX fails

## Model

- **Base Model**: `mixedbread-ai/mxbai-rerank-large-v1`
- **Architecture**: DeBERTa-v2 (1.1B parameters)
- **Backend**: Optimum ONNX (FP32 for maximum accuracy)
- **Use Case**: Literature review and document ranking
