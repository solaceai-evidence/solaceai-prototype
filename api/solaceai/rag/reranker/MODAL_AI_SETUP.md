# Modal AI Setup for Remote Crossencoder Reranking

This guide explains how to deploy and use the crossencoder reranker on Modal AI cloud platform instead of running it locally on your laptop.

## Overview

Modal AI allows you to run the computationally expensive crossencoder model remotely on cloud GPUs, reducing the load on your laptop and improving performance.


## Prerequisites

1. **Modal AI Account**
   - Sign up at https://modal.com/
   - Get your API credentials from the Modal dashboard

2. **Modal CLI**
   ```bash
   pip install modal
   ```

3. **Modal Authentication**
   ```bash
   modal token new
   ```
   This will open a browser for you to authenticate with Modal.

## Setup Steps

### 1. Configure Environment Variables

Add your Modal credentials to `.env` file in the project root:

```bash
# Modal cloud platform credentials
MODAL_TOKEN=your_modal_token_here
MODAL_TOKEN_SECRET=your_modal_secret_here
```

You can find these credentials in your Modal dashboard under Settings → API Keys.

### 2. Update Modal App Name

Edit `api/solaceai/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py`:

```python
# Change this to your desired Modal app name
APP_NAME = "solaceai-reranker"  # or any unique name you prefer
```

### 3. Deploy to Modal

Deploy the reranker to Modal AI:

```bash
cd api/solaceai/rag/reranker/modal_deploy
modal deploy ai2-scholar-qa-reranker.py
```

This will:
- Build a container image with the model weights pre-downloaded
- Deploy the reranker as a Modal function
- Create the `inference_api` endpoint

**Note:** Initial deployment takes ~10-15 minutes as it downloads the model weights (mixedbread-ai/mxbai-rerank-large-v1).

### 4. Verify Deployment

Test the deployed function:

```bash
modal run ai2-scholar-qa-reranker.py
```

This runs the `main()` local entrypoint which sends a test query to your deployed reranker.

### 5. Configure SolaceAI to Use Modal

Update `api/run_configs/default.json`:

```json
{
  "run_config": {
    "reranker_service": "modal",
    "reranker_args": {
      "app_name": "solaceai-reranker",
      "api_name": "inference_api",
      "batch_size": 256
    }
  }
}
```

**Configuration Parameters:**
- `app_name`: Must match the APP_NAME in your deployment script
- `api_name`: The Modal function name (default: "inference_api")
- `batch_size`: Number of passages to process in parallel (default: 256)

## Architecture

### Modal Deployment (`ai2-scholar-qa-reranker.py`)

**Components:**

1. **Model Class** (`@app.cls`)
   - Loads the crossencoder model on GPU
   - Compiles the model with torch.compile() for faster inference
   - Caches model in memory across invocations
   - GPU: L4:1 (NVIDIA L4 GPU)
   - Timeout: 20 minutes
   - Min containers: 2 (for high availability)

2. **Inference API** (`@app.function`)
   - FastAPI-style endpoint
   - Handles concurrent requests (max 20)
   - Proxies requests to the Model class
   - Timeout: 10 minutes

3. **get_scores Method**
   - Input: query (str), passages (List[str]), batch_size (int)
   - Output: List[float] of relevance scores
   - Automatically compiles model after first use

### Client Integration (`modal_engine.py`)

**ModalReranker Class:**
- Implements `AbstractReranker` interface
- Uses `ModalEngine` to communicate with deployed function
- Authenticates with Modal credentials from environment

**ModalEngine Class:**
- Creates Modal client with your credentials
- Looks up remote functions by name
- Invokes remote functions via `fn.remote()`
- Supports streaming and non-streaming modes

## Usage

### Using in Pipeline

The pipeline automatically uses Modal when `reranker_service: "modal"` is set:

```python
from solaceai import SolaceAI
from solaceai.rag.retrieval import PaperFinderWithReranker
from solaceai.rag.retriever_base import FullTextRetriever

# Configuration is loaded from default.json
retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
# Reranker is automatically initialized as ModalReranker
solace_ai = SolaceAI(...)
```

### Direct Usage

You can also use `ModalReranker` directly:

```python
from solaceai.rag.reranker.modal_engine import ModalReranker

reranker = ModalReranker(
    app_name="solaceai-reranker",
    api_name="inference_api",
    batch_size=256,
)

scores = reranker.get_scores(
    query="What is mental health?",
    documents=[
        "Mental health refers to cognitive, behavioral, and emotional well-being.",
        "Python is a programming language.",
        "The sky is blue."
    ]
)
print(scores)  # [0.95, 0.12, 0.08]
```

## Performance Optimization

### Model Compilation

The deployment script uses `torch.compile()` for faster inference:
- First request: ~500ms (uses uncompiled model + starts compilation in background)
- Subsequent requests: ~200ms (uses compiled model)
- Compilation happens automatically after the first batch

### Cold Start Optimization

- Model weights are baked into the container image (~3GB)
- No download needed on container startup
- Cold start time: ~30 seconds
- Minimum 2 containers kept warm to reduce cold starts

### Batch Processing

Configure `batch_size` based on your needs:
- Larger batches (256-512): Better throughput, higher latency
- Smaller batches (32-64): Lower latency, reduced throughput
- Default: 256 (good balance for most use cases)

## Monitoring and Debugging

### View Logs

Monitor your deployment in real-time:

```bash
modal app logs solaceai-reranker
```

### Check Status

See running containers and costs:

```bash
modal app list
```

### Function Details

Get information about your deployed function:

```bash
modal function get solaceai-reranker::inference_api
```

## Cost Estimation

Modal charges for:
- GPU time (L4 GPU: ~$0.60/hour)
- CPU time
- Container memory
- Data egress

**Typical costs:**
- 1000 reranking requests: ~$0.05-0.10
- Always-on (2 min containers): ~$1.20/hour
- Recommended: Use scaledown_window to reduce costs when idle

## Troubleshooting

### Authentication Errors

```
Error: Failed to authenticate with Modal
```

**Solution:**
1. Check that MODAL_TOKEN and MODAL_TOKEN_SECRET are set in `.env`
2. Verify credentials in Modal dashboard
3. Run `modal token new` to re-authenticate

### App Not Found

```
Error: No app named 'solaceai-reranker' found
```

**Solution:**
1. Ensure you've deployed: `modal deploy ai2-scholar-qa-reranker.py`
2. Check APP_NAME matches in both deployment script and config
3. Run `modal app list` to see available apps

### Function Not Found

```
Error: No function named 'inference_api' in app 'solaceai-reranker'
```

**Solution:**
1. Verify api_name in config matches the function name
2. Check deployment was successful
3. Run `modal function list solaceai-reranker` to see available functions

### Cold Start Timeout

```
Error: Function timed out during cold start
```

**Solution:**
1. Increase timeout in deployment script
2. Check if model download succeeded
3. Ensure sufficient GPU memory (L4 has 24GB)

### Out of Memory

```
Error: CUDA out of memory
```

**Solution:**
1. Reduce batch_size in config
2. Use smaller model or different GPU
3. Check if multiple requests are running concurrently

## Alternative: Local Reranking

To switch back to local reranking, update `default.json`:

```json
{
  "run_config": {
    "reranker_service": "crossencoder",
    "reranker_args": {
      "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1",
      "batch_size": 32
    }
  }
}
```

Or use the local reranker service (separate service):

```json
{
  "run_config": {
    "reranker_service": "local_service",
    "reranker_args": {
      "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1",
      "batch_size": 32
    }
  }
}
```

## Updating the Model

To use a different crossencoder model:

1. Update MODEL_NAME in `ai2-scholar-qa-reranker.py`:
   ```python
   MODEL_NAME = "jinaai/jina-reranker-v2-base-multilingual"
   ```

2. Redeploy:
   ```bash
   modal deploy ai2-scholar-qa-reranker.py
   ```

## References

- Modal Documentation: https://modal.com/docs
- Modal GPU Options: https://modal.com/docs/guide/gpu
- Mixedbread AI Reranker: https://huggingface.co/mixedbread-ai/mxbai-rerank-large-v1
- Sentence Transformers: https://www.sbert.net/docs/pretrained_cross-encoders.html
