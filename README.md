# Solace-AI System

## Overview

The Solace-AI System provides intelligent question-answering capabilities over a large corpus of online scientific literature, aiming to create real-time evidence synthesis to support policy and humanitarian responses to climate-change health emergencies. The system supports multiple deployment architectures to accommodate different performance requirements and infrastructure constraints.

The Solace-AI system is built on top of the open-source Ai2 Scholar QA architecture kindly shared at <https://github.com/allenai/ai2-scholarqa-lib>

## Supported Architectures

The system supports three deployment architectures. Choose based on your use case:

- **Hybrid Architecture**: Local development with flexible reranker backend (recommended for development)
- **Modal Cloud Architecture**: Production deployment with serverless GPU infrastructure
- **HTTP Microservice Architecture**: Full containerized deployment with dedicated services

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

   **Required Environment Variables (with examples for laptop development):**

   ```bash
   # API key for Semantic Scholar - used to retrieve paper passages, search results, and metadata
   S2_API_KEY=your_semantic_scholar_api_key

   # API key for Anthropic Claude models - primary LLM for content generation and analysis
   ANTHROPIC_API_KEY=your_anthropic_api_key

   # API key for OpenAI models - used as fallback LLM and for content moderation/validation
   OPENAI_API_KEY=your_openai_api_key

   # Modal cloud platform credentials - required when using Modal for remote model deployment
   MODAL_TOKEN_ID=your_modal_token_id
   MODAL_TOKEN_SECRET=your_modal_secret

   # Remote reranker service configuration
   RERANKER_HOST=0.0.0.0
   RERANKER_PORT=10001

   # LLM concurrency and rate limiting configuration
   MAX_LLM_WORKERS=3
   RATE_LIMIT_RPM=120
   RATE_LIMIT_ITPM=100000
   RATE_LIMIT_OTPM=25000

   # Query processing timeout (>=10 minutes for complex queries with table generation when used on laptop)
   QUERY_TIMEOUT_SECONDS=900

   # Reranker service timeout and concurrency settings
   RERANKER_CLIENT_TIMEOUT=270
   MAX_CONCURRENCY=1
   RERANKER_TIMEOUT_MS=270000
   RERANKER_QUEUE_TIMEOUT_MS=15000

   # Query refinement step configuration
   ENABLE_QUERY_REFINEMENT=true
   ```

   **Configuration Notes:**
   - The default settings are optimized for laptop development with Claude 4 Sonnet
   - Rate limits are conservative to ensure stable performance on local hardware
   - Timeout values accommodate complex queries including table generation
   - All settings can be adjusted based on your hardware capabilities and API quotas

2. **Python Environment Setup:**

   The API dependencies are automatically installed via Docker. The startup script handles reranker dependencies automatically, but you need a Python environment:

   ```bash
   # Create conda environment (recommended)
   conda create -n solaceai python=3.11
   conda activate solaceai
   ```

   Or use venv:

   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

   **Note:** The startup script (`start_hybrid.sh`) automatically installs:
   - Modal SDK when `reranker_service` is "modal"
   - PyTorch and reranker dependencies when `reranker_service` is "remote"

   For manual installation of local reranker dependencies:

   ```bash
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

   The startup script automatically:
   - Detects and configures the appropriate Python environment (conda or venv)
   - Reads `api/run_configs/default.json` to determine reranker configuration
   - Installs Modal SDK if `reranker_service` is set to "modal"
   - Installs PyTorch and reranker dependencies if using local reranker
   - Starts only the required services based on configuration

**Device Detection:**
The system automatically detects and uses the best available device:

- NVIDIA CUDA GPUs (preferred)
- Apple Silicon MPS (Apple M1/M2/M3)
- CPU (fallback)

**Service Endpoints:**

- **Web Application**: `http://localhost:8080` (Nginx Proxy - Main Entry Point)
- Main API: `http://localhost:8000`
- Native Reranker: `http://0.0.0.0:10001` (only when `reranker_service` is "remote")
- Web UI: `http://localhost:3000` (Direct UI access)

**Advantages:**

- GPU acceleration for reranking operations
- Reduced latency through native service communication
- Flexible reranker backend (local native, Modal cloud, or HTTP microservice)
- Automatic dependency installation based on configuration

### 2. Modal Cloud Architecture

Deploy the system using Modal's serverless GPU infrastructure for production-scale workloads. Modal AI allows you to run the computationally expensive crossencoder model remotely on cloud GPUs, reducing the load on your local machine and improving performance.

**Prerequisites:**

1. Modal AI account (sign up at https://modal.com/)
2. Modal CLI installed: `pip install modal`
3. Modal authentication: `modal token new`

**Environment Configuration:**

Add Modal credentials to your `.env` file:

```bash
# Modal cloud platform credentials
MODAL_TOKEN_ID=your_modal_token_id_here
MODAL_TOKEN_SECRET=your_modal_secret_here
```

Credentials can be found in your Modal dashboard under Settings → API Keys, or in `~/.modal.toml` after authentication.

**Deployment Steps:**

1. **Configure Application Name**

   Edit `api/solaceai/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py` and set your desired app name:

   ```python
   APP_NAME = "solaceai-reranker"  # or any unique name
   ```

2. **Deploy to Modal**

   ```bash
   cd api/solaceai/rag/reranker/modal_deploy
   modal deploy ai2-scholar-qa-reranker.py
   ```

   Initial deployment takes approximately 10-15 minutes as it downloads model weights (mixedbread-ai/mxbai-rerank-large-v1) and builds the container image.

3. **Verify Deployment**

   ```bash
   modal run ai2-scholar-qa-reranker.py
   ```

   This executes a test query against your deployed reranker to verify functionality.

4. **Configure System for Modal**

   Update `api/run_configs/default.json`:

   ```json
   {
     "reranker_service": "modal",
     "reranker_args": {
       "app_name": "solaceai-reranker",
       "api_name": "inference_api",
       "batch_size": 256
     }
   }
   ```

**Configuration Parameters:**

- `app_name`: Must match APP_NAME in deployment script
- `api_name`: Modal function name (default: "inference_api")
- `batch_size`: Passages processed in parallel (32-512, default: 256)

**Architecture Components:**

- **Model Class**: Loads crossencoder on NVIDIA L4 GPU with torch.compile() optimization
- **Inference API**: FastAPI-style endpoint handling concurrent requests (max: 20)
- **Cold Start Optimization**: Model weights baked into container image (~3GB)
- **High Availability**: Minimum 2 containers maintained for reduced cold starts

**Performance:**

- First request: ~500ms (uncompiled model + background compilation starts)
- Subsequent requests: ~200ms (compiled model)
- Cold start time: ~30 seconds

**Monitoring:**

```bash
# View real-time logs
modal app logs solaceai-reranker

# Check deployment status
modal app list

# View function details
modal function get solaceai-reranker::inference_api
```

**Cost Considerations:**

Modal charges for GPU time (L4: ~$0.60/hour), CPU time, memory, and data egress.

Typical costs:

- 1000 reranking requests: $0.05-0.10
- Always-on (2 minimum containers): ~$1.20/hour

Configure `scaledown_window` to reduce costs during idle periods.

**Troubleshooting:**

- **Authentication errors**: Verify `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` in `.env`, run `modal token new` to re-authenticate
- **App not found**: Confirm deployment succeeded with `modal app list`, verify `app_name` matches deployment script
- **Out of memory**: Reduce `batch_size` in configuration or use different GPU tier
- **Cold start timeout**: Increase timeout in deployment script, verify model download succeeded

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

- `remote`: Native service with GPU acceleration (hybrid architecture, recommended for local development)
- `modal`: Modal cloud deployment with serverless GPU infrastructure (see Modal Cloud Architecture section)
- `http`: Containerized microservice
- `crossencoder`: Local in-process reranker

**Switching Between Reranker Modes:**

To switch reranker backends, update `api/run_configs/default.json` and restart the system with `./start_hybrid.sh`. The startup script automatically installs the appropriate dependencies based on your configuration.

**Environment Variables:**

Environment variables are configured in the `.env` file as detailed in the setup section above.

### Production Scaling Configuration

The system includes concurrency control to prevent resource conflicts when multiple queries run simultaneously.

**Key Settings:**

```bash
# Laptop/Development (recommended)
MAX_CONCURRENT_QUERIES=1          # Sequential execution prevents timeouts
QUERY_TIMEOUT_SECONDS=600          # 10 minutes for table generation

# Production (with adequate resources)
MAX_CONCURRENT_QUERIES=3           # Allow 3 simultaneous queries
QUERY_TIMEOUT_SECONDS=900          # 15 minutes (scaled for concurrency)
RATE_LIMIT_RPM=300                 # Scale rate limits proportionally
```

**Simple Guidelines:**

- **Laptop**: Use `MAX_CONCURRENT_QUERIES=1` for stable performance
- **Production**: Increase to 2-5 with proportional timeout and rate limit scaling
- **High-Performance**: Set to `-1` for unlimited concurrency (requires robust infrastructure)

## Usage

The system automatically loads configuration from the `.env` file on startup. Rate limiting is enabled by default to ensure stable performance and prevent API quota overrun.

**Configuration Management:**

- Default settings optimized for laptop development with Claude 4 Sonnet
- Query concurrency limited to 1 for stable laptop performance
- 10-minute timeout accommodates complex table generation
- All settings configurable via `.env` file without code changes

**Query Processing:**

- Simple queries typically complete in 2-3 minutes
- Complex queries with table generation may take 5-7 minutes
- System provides real-time status updates during processing

## Development Workflow

### Local Development (Hybrid)

1. Start hybrid architecture: `./start_hybrid.sh`
2. Access UI: `http://localhost:8080`
3. Monitor reranker logs: `tail -f api/logs/reranker_service.log`
4. Stop services: `Ctrl+C` in terminal

### Testing Reranker Service

**Local Native Reranker (when `reranker_service` is "remote"):**

```bash
# Health check
curl http://localhost:10001/health

# Test reranking
curl -X POST "http://localhost:10001/rerank" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "passages": ["Deep learning networks", "Weather forecast"],
    "batch_size": 64
  }'
```

**Modal Reranker:**

```bash
# View deployment status
modal app list

# Test via deployed function
modal run api/solaceai/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py
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

- Adjust rate limiting values in .env file: RATE_LIMIT_RPM, RATE_LIMIT_ITPM, RATE_LIMIT_OTPM
- Reduce MAX_LLM_WORKERS if experiencing API rejections
- Increase QUERY_TIMEOUT_SECONDS for complex queries with table generation
- Monitor API usage quotas with your LLM provider

**Query Timeout Issues:**

- **Laptop timeouts**: Ensure `MAX_CONCURRENT_QUERIES=1` to prevent resource conflicts
- **Complex queries**: Increase `QUERY_TIMEOUT_SECONDS` for table generation
- **Production scaling**: Scale timeout proportionally with concurrency (e.g., 900s for 2 queries)
- **Semaphore Deadlocks**: Check logs for "Acquiring/releasing semaphore" messages; restart if queries hang
- **Unlimited Concurrency**: Use MAX_CONCURRENT_QUERIES=-1 only with robust infrastructure

**Docker Issues:**

- Ensure Docker Desktop is running
- Check port availability:
  - Linux/macOS: `lsof -i :8000,10001,8080`
  - Windows: `netstat -an | findstr :8000`
- Rebuild containers: `docker-compose down && docker-compose up --build`

**Performance Issues:**

- Monitor system resources during reranking
- Adjust `batch_size` based on available memory
- Consider switching to Modal cloud deployment for high-throughput requirements (see Modal Cloud Architecture section)

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
