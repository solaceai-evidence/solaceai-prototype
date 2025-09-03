# Solace-AI (ScholarQA) System

## Overview

The Solace-AI System provides intelligent question-answering capabilities over a large corpus of online scientific literature, aiming to create real-time evidence synthesis to support policy and humanitarian responses to climate-change health emergencies. The system supports multiple deployment architectures to accommodate different performance requirements and infrastructure constraints.

## Supported Architectures

### 1. Hybrid Architecture (Local Development with GPU Optimization)

The hybrid architecture combines containerized API services with a native reranker service to leverage GPU acceleration for optimal local development performance.

**Components:**

- Containerized main API (Docker)
- Native reranker service with GPU acceleration
- Web UI (containerized)

**Prerequisites:**

- Docker Desktop
- Python 3.11+ with PyTorch GPU support
- Conda or virtual environment
- GPU-capable hardware (NVIDIA CUDA, Apple Silicon MPS, or CPU fallback)

**Setup:**

1. **Environment Configuration:**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

   **Required Environment Variables:**

   ```bash
   # API key for Semantic Scholar - used to retrieve paper passages, search results, and metadata
   S2_API_KEY=your_semantic_scholar_api_key

   # API key for Anthropic Claude models - primary LLM for content generation and analysis
   ANTHROPIC_API_KEY=your_anthropic_api_key

   # API key for OpenAI models - used as fallback LLM and for content moderation/validation
   OPENAI_API_KEY=your_openai_api_key

   # Modal cloud platform credentials - required when using Modal for remote model deployment
   MODAL_TOKEN=your_modal_token
   MODAL_TOKEN_SECRET=your_modal_secret

   # Remote reranker service configuration
   # Configure these when using a standalone reranker service (not Modal or Docker)
   # Host address for the remote reranker service
   RERANKER_HOST=0.0.0.0
   # Port number for the remote reranker service
   RERANKER_PORT=10001

   # LLM concurrency and rate limiting configuration
   # Maximum number of concurrent LLM workers for parallel processing
   MAX_LLM_WORKERS=3

   # Maximum API requests per minute - set according to your LLM provider quota
   RATE_LIMIT_RPM=50

   # Maximum input tokens per minute across all LLM requests - prevents quota overrun
   RATE_LIMIT_ITPM=30000

   # Maximum output tokens per minute across all LLM requests - controls generation limits
   RATE_LIMIT_OTPM=8000

   # Reranker service timeout and concurrency settings
   # Client timeout in seconds when communicating with remote reranker
   RERANKER_CLIENT_TIMEOUT=120

   # Maximum concurrent reranker requests - controls resource usage
   MAX_CONCURRENCY=1

   # Request processing timeout in milliseconds for reranker operations
   RERANKER_TIMEOUT_MS=120000

   # Queue wait timeout in milliseconds before rejecting reranker requests
   RERANKER_QUEUE_TIMEOUT_MS=10000
   ```

2. **Install Native Dependencies (Reranker Service Only):**

   The API dependencies are automatically installed via Docker. You only need to install dependencies for the native reranker service:

   ```bash
   # Create conda environment
   conda create -n solaceai python=3.11
   conda activate solaceai

   # Install PyTorch with appropriate GPU support
   # For NVIDIA GPUs:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

   # For Apple Silicon (M1/M2/M3):
   pip install torch torchvision torchaudio

   # For CPU-only:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

   ```

3. **Start Hybrid Architecture:**
   ```bash
   chmod +x start_hybrid.sh
   ./start_hybrid.sh
   ```

**Device Detection:**
The system automatically detects and uses the best available device:

- NVIDIA CUDA GPUs (preferred)
- Apple Silicon MPS (Apple M1/M2/M3)
- CPU (fallback)

**Configuration:**
The configuration can be modified by tuning the .env file. Below are the default parameters.

- **Web Application**: `http://localhost:8080` (Nginx Proxy - Main Entry Point)
- Main API: `http://localhost:8000`
- Native Reranker: `http://0.0.0.0:10001`
- Web UI: `http://localhost:3000` (Direct UI access)

The hybrid approach provides:

- GPU acceleration for reranking operations
- Reduced latency through native service communication

### 2. Modal Cloud Architecture

Deploy the system using Modal's serverless GPU infrastructure for production-scale workloads.

**Setup:**

```bash
# Install Modal CLI
pip install modal-client

# Deploy reranker service
modal deploy api/scholarqa/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py

# Configure for Modal
cp api/run_configs/modal.json api/run_configs/default.json
```

**Configuration:**

```json
{
  "reranker_service": "modal",
  "reranker_args": {
    "app_name": "ai2-scholar-qa",
    "api_name": "inference_api",
    "batch_size": 256
  }
}
```

### 3. HTTP Microservice Architecture

Full containerized deployment with dedicated reranker microservices and load balancing.

**Setup:**

```bash
# Deploy with scaling configuration
docker-compose -f docker-compose.scale.yaml up -d

# Scale API instances
docker-compose -f docker-compose.scale.yaml up -d --scale api=3
```

**Configuration:**

```json
{
  "reranker_service": "http",
  "reranker_args": {
    "service_url": "http://reranker:8001",
    "batch_size": 64,
    "timeout": 300
  }
}
```

## Configuration Management

### Reranker Service Configuration

The system supports multiple reranker backends through configuration:

```json
{
  "reranker_service": "remote|modal|http|crossencoder",
  "reranker_args": {
    "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1",
    "batch_size": 32
  }
}
```

**Reranker Options:**

- `remote`: Native service with GPU acceleration (hybrid architecture)
- `modal`: Modal cloud deployment
- `http`: Containerized microservice
- `crossencoder`: Local in-process reranker

**Environment Variables:**

Environment variables are configured in the `.env` file as detailed in the setup section above.

## Usage

The rate limiter is automatically enabled when the environment variables are configured. It operates transparently within the LLM pipeline to ensure API calls remain within configured limits.

If rate limiting is disabled (variables not set or set to -1), the system will operate without rate limiting controls.

## Development Workflow

### Local Development (Hybrid)

1. Start hybrid architecture: `./start_hybrid.sh`
2. Access UI: `http://localhost:8080`
3. Monitor reranker logs: `tail -f api/logs/reranker_service.log`
4. Stop services: `Ctrl+C` in terminal

### Testing Reranker Service

```bash
# Health check
curl http://localhost:8001/health

# Test reranking
curl -X POST "http://localhost:10001/rerank" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "passages": ["Deep learning networks", "Weather forecast"],
    "batch_size": 64
  }'
```

### Platform-Specific Commands

**Linux/macOS:**

```bash
# Check GPU availability
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('MPS:', torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False)"

# Start services
./start_hybrid.sh
```

**Windows:**

```cmd
# Check GPU availability
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Start services (use Git Bash or WSL for shell scripts)
bash start_hybrid.sh
```

## Troubleshooting

### Common Issues

**GPU Not Available:**

- **NVIDIA**: Verify CUDA installation and PyTorch CUDA support
- **Apple Silicon**: Ensure PyTorch version supports MPS
- **Check**: `python -c "import torch; print(torch.cuda.is_available(), torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False)"`

**Rate Limiting Errors:**

- Reduce `max_workers` in configuration
- Increase `request_timeout` values
- Monitor API usage quotas

**Docker Issues:**

- Ensure Docker Desktop is running
- Check port availability:
  - Linux/macOS: `lsof -i :8000,10001,8080`
  - Windows: `netstat -an | findstr :8000`
- Rebuild containers: `docker-compose down && docker-compose up --build`

**Performance Issues:**

- Monitor system resources during reranking
- Adjust `batch_size` based on available memory
- Consider switching to Modal for high-throughput requirements

**Platform-Specific Issues:**

**Apple Silicon:**

- Ensure Rosetta 2 is installed if needed: `softwareupdate --install-rosetta`

  **What is Rosetta 2?** Apple's translation layer that allows Intel-based (x86_64) applications to run on Apple Silicon (M1/M2/M3) processors. Some Docker images and Python packages may still be Intel-only and require Rosetta 2 for compatibility.

- Use native ARM64 Docker images when possible

## Production Deployment

For production deployments, consider:

1. **Modal Architecture**: Best for variable workloads with automatic scaling
2. **HTTP Microservice**: Best for consistent workloads with predictable traffic
3. **Hybrid Architecture**: Recommended only for development and local testing

Configure appropriate monitoring, logging, and error handling for production environments.

## API Documentation

Once services are running, access interactive API documentation:

- Main API: `http://localhost:8000/docs`
- Reranker Service: `http://localhost:10001/docs`

### Install TypeScript Types (if using TypeScript)

If you see TypeScript errors about missing React types, install them with:

```bash
yarn add --dev @types/react @types/react-dom
```
