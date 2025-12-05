# Solace-AI with Large Reranker (Mixedbread mxbai-rerank-large-v1)

A step-by-step guide to set up and run the Solace-AI prototype with the **Mixedbread mxbai-rerank-large-v1** reranker model running locally on your GPU.

**Model specifications:**
- Size: ~1.3B parameters
- Quality: Best accuracy and ranking performance
- Requirements: 16GB+ GPU VRAM or 32GB+ system RAM (Apple Silicon)
- Best for: Production workloads, highest quality results

For other reranker options, see `SETUP_BASE_RERANKER.md` or `SETUP_SMALL_RERANKER.md`. For Modal cloud deployment, see `SETUP_MODAL_AI.md`.

---

## 1) Prerequisites

- macOS (16GB+ RAM, preferably Apple Silicon) or Linux with NVIDIA GPU (16GB+ VRAM)
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
- **Apple Silicon (M1/M2/M3):** 32GB+ unified memory recommended
- **NVIDIA GPU:** RTX 3090/4090 (24GB VRAM) or A5000/A6000
- **CPU fallback:** Not recommended (very slow; use smaller model instead)

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

## 3) Configure for large reranker model

Edit `api/run_configs/default.json`:

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

**Batch size tuning:**
- **32** (default): Good balance for most systems
- **16**: Use if you have 16GB GPU VRAM or experience OOM errors
- **64**: Use if you have 24GB+ VRAM and want higher throughput

---

## 4) Start the system

From repo root:

```bash
chmod +x start_hybrid.sh
./start_hybrid.sh
```

**What the script does:**
- Automatically detects or creates conda/venv environment (no manual activation needed!)
- Installs PyTorch optimized for your system (CUDA for NVIDIA, MPS for Apple Silicon)
- Downloads the large reranker model (~3GB) on first run
- Installs reranker dependencies (transformers, sentence-transformers, etc.)
- Starts local reranker service on port 10001
- Starts Docker services (API + UI)

**First-time startup:**
- Model download: ~5-10 minutes (3GB model weights)
- Model loading: ~30-60 seconds
- Total first startup: ~10-15 minutes

**Subsequent startups:**
- Model already cached, starts in ~30 seconds

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
  "model": "mixedbread-ai/mxbai-rerank-large-v1",
  "device": "cuda:0",  // or "mps" for Apple Silicon
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

**Expected behavior with large model:**
- Initial query: ~10-15 seconds (includes paper retrieval + reranking)
- Reranking step: ~2-3 seconds for 1000 passages
- High-quality ranking with good separation between relevant and irrelevant papers
- Consistent table generation for structured data

### Monitor reranker logs

```bash
# View reranker logs
tail -f logs/reranker_service.log

# Or check startup log
cat startup.log | grep -A 10 "reranker"
```

Look for:
```
INFO - Initialized CrossEncoderReranker: mixedbread-ai/mxbai-rerank-large-v1
INFO - Model loaded successfully on device: cuda:0
INFO - Starting Solace-AI Local Reranker Service on 0.0.0.0:10001
```

---

## 7) Performance tuning

### GPU memory optimization

If you encounter CUDA OOM errors:

1. **Reduce batch size** in `default.json`:
   ```json
   "batch_size": 16  // down from 32
   ```

2. **Monitor GPU usage:**
   ```bash
   # NVIDIA
   nvidia-smi -l 1
   
   # Apple Silicon
   sudo powermetrics --samplers gpu_power -i 1000
   ```

3. **Expected GPU memory usage:**
   - Model weights: ~3GB
   - Working memory (batch 32): ~6-8GB
   - Total: ~10-12GB peak

### Throughput optimization

For higher throughput (if you have VRAM headroom):

```json
"batch_size": 64  // or even 128 with 24GB+ VRAM
```

**Benchmarks (approximate):**
- Batch 16: ~500 passages/sec on RTX 4090
- Batch 32: ~800 passages/sec
- Batch 64: ~1200 passages/sec

---

## 8) Troubleshooting

### Out of memory errors

**Error:** `RuntimeError: CUDA out of memory`

**Fix:**
1. Lower batch size to 16 or 8
2. Restart system: `docker-compose down && ./start_hybrid.sh`

### Model not loading

**Error:** `Failed to load model` or takes too long

**Fix:**
1. Check internet connection (model downloads from Hugging Face)
2. Manually download:
   ```bash
   python -c "from sentence_transformers import CrossEncoder; CrossEncoder('mixedbread-ai/mxbai-rerank-large-v1')"
   ```
3. Check disk space (need ~5GB free)

### Slow inference

**Issue:** Reranking takes > 10 seconds

**Check:**
1. Verify GPU is being used:
   ```bash
   curl -s http://localhost:10001/health | grep device
   # Should show "cuda:0" or "mps", not "cpu"
   ```
2. If on CPU, check PyTorch installation:
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"  # Should be True
   ```

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

The large model provides:
- **High precision:** Top-ranked papers are highly relevant
- **Good recall:** Relevant papers consistently ranked in top 50
- **Score separation:** Clear distinction between relevant (0.7+) and irrelevant (< 0.3) papers
- **Consistent output:** Same query produces similar rankings across runs

### Comparison with other models

vs. **Base model** (BAAI/bge-reranker-base):
- ~15% better accuracy on ranking benchmarks
- Better at nuanced semantic understanding
- More consistent table generation

vs. **Small model** (cross-encoder/ms-marco-MiniLM-L-6):
- ~25% better accuracy
- Much better at domain-specific queries (medical, scientific)
- More reliable for production use

---

## 10) Switching to a different model

If you want to use a smaller model (laptop constraints):

1. Stop the system:
   ```bash
   docker-compose down
   pkill -f reranker_service.py
   ```

2. Edit `api/run_configs/default.json`:
   ```json
   "model_name_or_path": "BAAI/bge-reranker-base",  // or small model
   "batch_size": 64  // can increase with smaller model
   ```

3. Restart:
   ```bash
   ./start_hybrid.sh
   ```

See `SETUP_BASE_RERANKER.md` or `SETUP_SMALL_RERANKER.md` for model-specific guides.

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

# Check GPU usage (NVIDIA)
watch -n 1 nvidia-smi

# Check memory usage (Apple Silicon)
sudo powermetrics --samplers gpu_power -i 1000 | grep -A 10 "GPU Power"
```

---

## Summary: Quick start checklist

- [ ] Verify hardware: 16GB+ GPU VRAM or 32GB+ RAM (Apple Silicon)
- [ ] Clone repo and copy `.env.example` to `.env`
- [ ] Add API keys to `.env` (S2, Anthropic)
- [ ] Configure `default.json` with large reranker model
- [ ] Run `./start_hybrid.sh` (first run takes ~10-15 min)
- [ ] Verify health endpoints
- [ ] Test query through web UI
- [ ] Monitor performance and adjust batch size if needed

For smaller models or cloud deployment, see other setup guides.
