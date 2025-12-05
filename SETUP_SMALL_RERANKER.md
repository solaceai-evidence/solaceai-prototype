# Solace-AI with Small Reranker (cross-encoder/ms-marco-MiniLM-L-6-v2)

A step-by-step guide to set up and run the Solace-AI prototype with the **cross-encoder/ms-marco-MiniLM-L-6-v2** reranker model running locally.

**Model specifications:**
- Size: ~110M parameters (very small)
- Quality: Reasonable accuracy for basic ranking tasks
- Requirements: 4GB+ GPU VRAM or 8GB+ system RAM
- Best for: Laptops with limited resources, rapid prototyping, demos

For better quality, see `SETUP_BASE_RERANKER.md` or `SETUP_LARGE_RERANKER.md`. For Modal cloud deployment, see `SETUP_MODAL_AI.md`.

---

## 1) Prerequisites

- macOS (8GB+ RAM) or Linux with NVIDIA GPU (4GB+ VRAM) or CPU
- Docker Desktop running
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
- API keys:
  - Semantic Scholar: `S2_API_KEY`
  - Anthropic: `ANTHROPIC_API_KEY`
  - OpenAI (optional): `OPENAI_API_KEY`

**Hardware recommendations:**
- **Laptops:** Works on most modern laptops (8GB RAM minimum)
- **Apple Silicon (M1/M2/M3):** 8GB+ unified memory
- **NVIDIA GPU:** Any GPU with 4GB+ VRAM (even GTX 1050)
- **CPU fallback:** Works reasonably well (only ~3x slower than GPU)

---

## 2) Clone repo and configure environment

```bash
git clone <your-repo-url> solaceai-prototype
cd solaceai-prototype
cp .env.example .env
```

Edit `.env` and add required keys:

```bash
# Semantic Scholar
S2_API_KEY=your_s2_key

# LLM providers
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key  # optional

# Local reranker service (defaults are fine)
RERANKER_HOST=0.0.0.0
RERANKER_PORT=10001
```

---

## 3) Configure for small reranker model

Edit `api/run_configs/default.json`:

```json
{
  "run_config": {
    "reranker_service": "local_service",
    "reranker_args": {
      "model_name_or_path": "cross-encoder/ms-marco-MiniLM-L-6-v2",
      "batch_size": 128
    }
  }
}
```

**Batch size tuning:**
- **128** (recommended): Good balance for most laptops
- **64**: Use if you have limited RAM (< 8GB)
- **256**: Use if you have 16GB+ RAM and want faster processing

**Note:** This small model uses so little memory that batch size mainly affects CPU/GPU utilization, not memory.

---

## 4) Start the system

From repo root:

```bash
chmod +x start_hybrid.sh
./start_hybrid.sh
```

**What the script does:**
- Automatically detects or creates conda/venv environment (no manual activation needed!)
- Installs PyTorch optimized for your system (CUDA for NVIDIA, MPS for Apple Silicon, or CPU)
- Downloads the small reranker model (~300MB) on first run
- Installs reranker dependencies (transformers, sentence-transformers, etc.)
- Starts local reranker service on port 10001
- Starts Docker services (API + UI)

**First-time startup:**
- Model download: ~1 minute (300MB model weights)
- Model loading: ~5 seconds
- Total first startup: ~3 minutes

**Subsequent startups:**
- Model already cached, starts in ~10 seconds

---

## 5) Health checks

```bash
# Check API
curl -s http://localhost:8000/health && echo "✓ API ready"

# Check reranker service
curl -s http://localhost:10001/health && echo "✓ Reranker ready"

# Open web interface
open http://localhost:8080
```

**Expected reranker response:**
```json
{
  "status": "healthy",
  "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
  "device": "cuda:0",  // or "mps" for Apple Silicon, or "cpu"
  "uptime_seconds": 123
}
```

---

## 6) Testing and validation

### Test query

Through the web UI (http://localhost:8080), try:

```
What are effective interventions for mental health in displaced populations?
```

**Expected behavior with small model:**
- Initial query: ~8-10 seconds (includes paper retrieval + reranking)
- Reranking step: ~0.5-1 second for 1000 passages (on GPU)
- Decent ranking quality for straightforward queries
- May produce narratives instead of tables for complex queries (see note below)

### Monitor reranker logs

```bash
# View reranker logs
tail -f logs/reranker_service.log

# Or check startup log
cat startup.log | grep -A 10 "reranker"
```

Look for:
```
INFO - Initialized CrossEncoderReranker: cross-encoder/ms-marco-MiniLM-L-6-v2
INFO - Model loaded successfully on device: cuda:0
INFO - Starting Solace-AI Local Reranker Service on 0.0.0.0:10001
```

---

## 7) Performance tuning

### Memory optimization

This model uses very little memory (~1GB), so OOM errors are rare.

**Expected memory usage:**
- Model weights: ~300MB
- Working memory (batch 128): ~1-2GB
- Total: ~2GB peak

### Throughput optimization

For maximum speed on powerful hardware:

```json
"batch_size": 256  // or even 512
```

**Benchmarks (approximate):**
- CPU (8-core): ~300-400 passages/sec (batch 128)
- Apple M1: ~800 passages/sec (batch 128)
- RTX 3060: ~2000+ passages/sec (batch 256)

### CPU usage optimization

If running on CPU and want to use all cores:

```bash
# Set environment variable before starting
export OMP_NUM_THREADS=8  # or number of CPU cores
./start_hybrid.sh
```

---

## 8) Troubleshooting

### Slow inference on CPU

**Issue:** Reranking takes > 10 seconds on CPU

**This is expected.** The small model runs on CPU but is still slower than GPU. Consider:
- Using a cloud instance with GPU
- Deploying to Modal (see `SETUP_MODAL_AI.md`)
- Accepting the slower speed for development

### Model not loading

**Error:** `Failed to load model`

**Fix:**
1. Check internet connection (model downloads from Hugging Face)
2. Manually download:
   ```bash
   python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"
   ```
3. Check disk space (need ~500MB free)

### Port conflicts

**Error:** `Address already in use: 10001`

**Fix:**
1. Find process using port:
   ```bash
   lsof -i :10001
   ```
2. Kill it: `kill <PID>`
3. Or change port in `.env`:
   ```bash
   RERANKER_PORT=10002
   ```

---

## 9) Model quality expectations

### Ranking quality

The small model provides:
- **Basic precision:** Top-ranked papers are usually relevant for simple queries
- **Limited recall:** May miss some relevant papers in top 100
- **Weak score separation:** Scores may be compressed (e.g., 0.3-0.6 range instead of 0-1)
- **Variable output:** May produce different content types (narrative vs. table) compared to larger models

### Known limitations

**Score distribution issue:**
- Small model produces less calibrated scores
- Top papers may score 0.5 instead of 0.8+
- This can affect downstream filtering (fewer papers pass the 0.6 threshold)

**Workaround:** If you see narratives instead of tables:

1. Edit `api/run_configs/default.json` and lower the threshold:
   ```json
   {
     "run_config": {
       "reranker_service": "local_service",
       "reranker_args": { ... },
       "top_k_config": {
         "top_score_threshold": 0.3,  // lowered from 0.6
         "top_k": 200
       }
     }
   }
   ```

2. Restart: `docker-compose down && ./start_hybrid.sh`

### Comparison with other models

vs. **Base model** (BAAI/bge-reranker-base):
- ~75% of base model's accuracy
- ~2x faster inference
- Uses ~1/3 of the memory

vs. **Large model** (mixedbread-ai/mxbai-rerank-large-v1):
- ~60% of large model's accuracy
- ~4x faster inference
- Uses ~1/10 of the memory

**When to use small model:**
- Laptops with 8GB RAM
- Development on weak hardware
- Demos and prototypes
- Budget constraints (low cloud GPU costs)
- When speed matters more than accuracy

---

## 10) Upgrading to a better model

When you're ready for better quality:

1. Stop the system:
   ```bash
   docker-compose down
   pkill -f reranker_service.py
   ```

2. Edit `api/run_configs/default.json`:
   ```json
   "model_name_or_path": "BAAI/bge-reranker-base",
   "batch_size": 64,  // adjust for new model
   "top_k_config": {
     "top_score_threshold": 0.6  // restore default
   }
   ```

3. Restart:
   ```bash
   ./start_hybrid.sh
   ```

See `SETUP_BASE_RERANKER.md` or `SETUP_LARGE_RERANKER.md` for detailed guides.

---

## 11) Useful commands

```bash
# Restart just the reranker
pkill -f reranker_service.py
python reranker_service.py &

# Restart just the API
docker-compose restart api

# View all logs
tail -f logs/reranker_service.log
docker-compose logs -f api

# Check system resource usage
htop  # or top on macOS

# Monitor CPU usage during reranking
ps aux | grep python
```

---

## Summary: Quick start checklist

- [ ] Verify hardware: 8GB+ RAM (no GPU required)
- [ ] Clone repo and copy `.env.example` to `.env`
- [ ] Add API keys to `.env` (S2, Anthropic)
- [ ] Configure `default.json` with small reranker model
- [ ] Optional: Lower `top_score_threshold` to 0.3 for better table generation
- [ ] Run `./start_hybrid.sh` (first run takes ~3 min)
- [ ] Verify health endpoints
- [ ] Test query through web UI
- [ ] Consider upgrading to base/large model for production use

For better quality or cloud deployment, see other setup guides.
