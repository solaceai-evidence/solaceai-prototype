# Solace-AI with Modal AI — Setup Guide

A step-by-step guide to deploy and run the Solace-AI prototype using Modal AI's cloud GPU for reranking.

For local/native reranker setup, see `SETUP_GUIDE.md`. For full system documentation, see `README.md`.

---

## 1) Prerequisites

- macOS or Linux with Docker Desktop running
- Git
- **Conda (recommended) or Python 3.11+:**
  - **Conda (recommended):** Download Miniconda from https://docs.conda.io/en/latest/miniconda.html or Anaconda from https://www.anaconda.com/download
    ```bash
    # Install Miniconda (example for macOS/Linux)
    curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh  # macOS Intel
    # or: Miniconda3-latest-MacOSX-arm64.sh for Apple Silicon
    # or: Miniconda3-latest-Linux-x86_64.sh for Linux
    bash Miniconda3-latest-*.sh
    ```
  - **Python 3.11+ with venv:** If not using Conda, install Python 3.11 or higher:
    - macOS: `brew install python@3.11`
    - Linux: `sudo apt install python3.11 python3.11-venv` (Debian/Ubuntu) or `sudo yum install python311` (RHEL/CentOS)
- Modal account (sign up at https://modal.com)
- API keys:
  - Semantic Scholar: `S2_API_KEY`
  - Anthropic: `ANTHROPIC_API_KEY`
  - OpenAI (optional): `OPENAI_API_KEY`
  - Modal: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`

---

## 2) Get Modal credentials

### Create Modal account and get tokens

1. Sign up at https://modal.com
2. Install Modal CLI:
   ```bash
   pip install modal
   ```
3. Authenticate and generate tokens:
   ```bash
   modal token new
   ```
   This will:
   - Open a browser for authentication
   - Create tokens and save them to `~/.modal.toml`
4. View your credentials:
   ```bash
   modal config show
   ```
   Look for `token_id` (starts with `ak-`) and `token_secret` (starts with `as-`).

---

## 3) Clone repo and configure environment

```bash
git clone <your-repo-url> solaceai-prototype
cd solaceai-prototype
cp .env.example .env
```

Edit `.env` and add all required keys:

```bash
# Semantic Scholar
S2_API_KEY=your_s2_key

# LLM providers
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key  # optional

# Modal AI credentials (from step 2)
MODAL_TOKEN_ID=ak-...
MODAL_TOKEN_SECRET=as-...
```

---

## 4) Create Python environment (Conda or Venv)

```bash
# Conda (recommended)
conda create -n solaceai python=3.11 -y
conda activate solaceai

# or venv
python3 -m venv venv
source venv/bin/activate
```

---

## 5) Deploy reranker to Modal AI

### Choose your model

Edit `api/solaceai/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py`:

```python
# Line ~15-20
APP_NAME = "solaceai-reranker"  # Must match config in step 6
MODEL_NAME = "mixedbread-ai/mxbai-rerank-large-v1"  # Or choose smaller model
```

**Model options:**
- `mixedbread-ai/mxbai-rerank-large-v1` (default; ~1.3B params; best quality)
- `BAAI/bge-reranker-base` (~335M; good balance)
- `cross-encoder/ms-marco-MiniLM-L-6-v2` (~110M; fastest/cheapest)

### Deploy to Modal

```bash
cd api/solaceai/rag/reranker/modal_deploy
modal deploy ai2-scholar-qa-reranker.py
```

**What happens:**
- Modal creates a serverless GPU app
- Downloads model weights (~3GB for default model)
- Compiles model with `torch.compile()` for faster inference
- Takes 10-15 minutes on first deployment

### Test the deployment

```bash
modal run ai2-scholar-qa-reranker.py
```

Expected output:
```
Running inference_api.remote(...)
Scores: [0.136, 0.000427, 0.949]
```

### Verify deployment

```bash
# List your Modal apps
modal app list

# View logs
modal app logs solaceai-reranker

# Get function details
modal function get solaceai-reranker::inference_api
```

---

## 6) Configure system to use Modal

Edit `api/run_configs/default.json`:

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

**Important:** `app_name` here must match `APP_NAME` in the deployment script (step 5).

---

## 7) Start the system

From repo root:

```bash
chmod +x start_hybrid.sh
./start_hybrid.sh
```

**What the script does:**
- Automatically detects or creates conda/venv environment (no manual activation needed!)
- Detects Modal configuration in `default.json`
- Installs Modal SDK (skips PyTorch/heavy ML dependencies)
- Verifies Modal deployment exists
- Starts Docker services (API + UI)
- Uses Modal cloud GPU for all reranking

---

## 8) Health checks and testing

```bash
# Check API health
curl -s http://localhost:8000/health && echo "API ready"

# Open web interface
open http://localhost:8080

# Test a query through the UI
# Example: "What are effective interventions for mental health in displaced populations?"
```

---

## 9) Monitor Modal usage

```bash
# Follow real-time logs
modal app logs solaceai-reranker --follow

# View function stats
modal function get solaceai-reranker::inference_api

# Check costs (Modal dashboard)
# https://modal.com/apps
```

**Cost estimates (approximate):**
- L4 GPU: ~$0.60/hour
- Typical query: 1-3 seconds of GPU time
- ~1000 queries: $0.50-$2.00

---

## 10) Changing the model (Modal)

To deploy a different reranker model:

1. Edit `api/solaceai/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py`:
   ```python
   MODEL_NAME = "BAAI/bge-reranker-base"  # smaller model
   ```

2. Redeploy:
   ```bash
   cd api/solaceai/rag/reranker/modal_deploy
   modal deploy ai2-scholar-qa-reranker.py
   ```

3. Restart system:
   ```bash
   cd -  # back to repo root
   ./start_hybrid.sh
   ```

**No changes to `default.json` needed** unless you change `APP_NAME`.

---

## 11) Troubleshooting

### Authentication errors

**Error:** `Token missing. Could not authenticate client.`

**Fix:**
1. Verify `.env` has correct values:
   ```bash
   cat .env | grep MODAL
   ```
2. Regenerate tokens:
   ```bash
   modal token new
   ```
3. Update `.env` with new values
4. Restart:
   ```bash
   docker-compose down
   ./start_hybrid.sh
   ```

### Deployment errors

**Error:** `Function not found` or `App not found`

**Fix:**
1. Verify deployment succeeded:
   ```bash
   modal app list
   ```
2. Check `app_name` matches in both:
   - `api/run_configs/default.json` → `"app_name"`
   - `modal_deploy/ai2-scholar-qa-reranker.py` → `APP_NAME`
3. Redeploy if needed

### Modal SDK version errors

**Error:** `_Object._hydrate() missing arguments`

**Fix:**
```bash
pip install --upgrade modal
docker-compose down
docker-compose up -d --build
```

### Slow first request

**Expected:** First request takes ~30 seconds (cold start)
- Modal spins up container
- Loads model into GPU memory
- Compiles model

Subsequent requests: ~200ms

---

## 12) Advanced configuration

### GPU selection

Edit `modal_deploy/ai2-scholar-qa-reranker.py`:

```python
# Line ~25
@app.function(
    gpu="L4:1",  # Options: "T4", "L4", "A10G", "A100"
    ...
)
```

**GPU comparison:**
- T4: Cheapest, slowest (~$0.20/hr)
- L4: Balanced (default, ~$0.60/hr)
- A10G: Faster (~$1.10/hr)
- A100: Fastest, most expensive (~$3.00/hr)

### Container settings

```python
@app.function(
    container_idle_timeout=300,  # Keep warm for 5 min
    timeout=600,  # Max execution time
    ...
)
```

### Batch size tuning

In `default.json`:
```json
"batch_size": 256  // Increase for throughput, decrease for lower latency
```

---

## 13) Useful commands

```bash
# View all Modal apps
modal app list

# Stop a Modal app
modal app stop solaceai-reranker

# View function logs
modal app logs solaceai-reranker --follow

# Deploy with different profile
modal deploy ai2-scholar-qa-reranker.py --env staging

# Run a test locally
modal run ai2-scholar-qa-reranker.py

# Restart local system
docker-compose restart api
```

---

## 14) Switching back to local reranker

If you want to switch to local/native GPU reranking:

1. Edit `api/run_configs/default.json`:
   ```json
   "reranker_service": "local_service",
   "reranker_args": {
     "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1",
     "batch_size": 32
   }
   ```

2. Restart:
   ```bash
   ./start_hybrid.sh
   ```

The script will automatically install PyTorch and start local reranker service.

---

## Summary: Quick start checklist

- [ ] Sign up for Modal account at https://modal.com
- [ ] Run `modal token new` and get credentials
- [ ] Clone repo and copy `.env.example` to `.env`
- [ ] Add all API keys to `.env` (S2, Anthropic, Modal)
- [ ] Create conda/venv environment
- [ ] Deploy reranker: `modal deploy ai2-scholar-qa-reranker.py`
- [ ] Test deployment: `modal run ai2-scholar-qa-reranker.py`
- [ ] Configure `default.json` with `"reranker_service": "modal"`
- [ ] Start system: `./start_hybrid.sh`
- [ ] Test at http://localhost:8080

For local/native reranker setup, see `SETUP_GUIDE.md`.