# Solace-AI with Base Reranker (BAAI/bge-reranker-base)

A step-by-step guide to set up and run the Solace-AI prototype with the **BAAI/bge-reranker-base** reranker model running locally on your GPU.

**Model specifications:**
- Size: ~335M parameters
- Quality: Good balance between speed and accuracy
- Requirements: 8GB+ GPU VRAM or 16GB+ system RAM (Apple Silicon)
- Best for: Development, testing, laptops with moderate specs

For the highest quality, see `SETUP_LARGE_RERANKER.md`. For minimal hardware, see `SETUP_SMALL_RERANKER.md`. For Modal cloud deployment, see `SETUP_MODAL_AI.md`.

---

## 1) Prerequisites

- macOS (16GB+ RAM) or Linux with NVIDIA GPU (8GB+ VRAM)
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
- **Apple Silicon (M1/M2/M3):** 16GB+ unified memory
- **NVIDIA GPU:** GTX 1080 Ti / RTX 2060 (8GB VRAM) or better
- **CPU fallback:** Works but slower (~5-10x); consider small model instead

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

## 3) Configure for base reranker model

Edit `api/run_configs/default.json`:

```json
{
  "run_config": {
    "reranker_service": "local_service",
    "reranker_args": {
      "model_name_or_path": "BAAI/bge-reranker-base",
      "batch_size": 64
    }
  }
}
```

**Batch size tuning:**
- **64** (recommended): Good balance for 8-16GB VRAM
- **32**: Use if you have 8GB VRAM and want safer memory usage
- **128**: Use if you have 16GB+ VRAM and want higher throughput

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
- Downloads the base reranker model (~1GB) on first run
- Installs reranker dependencies (transformers, sentence-transformers, etc.)
- Starts local reranker service on port 10001
- Starts Docker services (API + UI)

**First-time startup:**
- Model download: ~2-3 minutes (1GB model weights)
- Model loading: ~10-15 seconds
- Total first startup: ~5 minutes

**Subsequent startups:**
- Model already cached, starts in ~15 seconds

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
  "model": "BAAI/bge-reranker-base",
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

**Expected behavior with base model:**
- Initial query: ~8-12 seconds (includes paper retrieval + reranking)
- Reranking step: ~1-2 seconds for 1000 passages
- Good ranking quality with reasonable separation between relevant and irrelevant papers
- Reliable table generation for most queries

### Monitor reranker logs

```bash
# View reranker logs
tail -f logs/reranker_service.log

# Or check startup log
cat startup.log | grep -A 10 "reranker"
```

Look for:
```
INFO - Initialized CrossEncoderReranker: BAAI/bge-reranker-base
INFO - Model loaded successfully on device: cuda:0
INFO - Starting Solace-AI Local Reranker Service on 0.0.0.0:10001
```

---

## 7) Performance tuning

### GPU memory optimization

If you encounter CUDA OOM errors:

1. **Reduce batch size** in `default.json`:
   ```json
   "batch_size": 32  // down from 64
   ```

2. **Monitor GPU usage:**
   ```bash
   # NVIDIA
   nvidia-smi -l 1
   
   # Apple Silicon
   sudo powermetrics --samplers gpu_power -i 1000
   ```

3. **Expected GPU memory usage:**
   - Model weights: ~1GB
   - Working memory (batch 64): ~3-4GB
   - Total: ~5GB peak

### Throughput optimization

For higher throughput (if you have VRAM headroom):

```json
"batch_size": 128  // or even 256 with 16GB+ VRAM
```

**Benchmarks (approximate):**
- Batch 32: ~600 passages/sec on RTX 3060
- Batch 64: ~1000 passages/sec
- Batch 128: ~1500 passages/sec

---

## 8) Troubleshooting

### Out of memory errors

**Error:** `RuntimeError: CUDA out of memory`

**Fix:**
1. Lower batch size to 32 or 16
2. Restart system: `docker-compose down && ./start_hybrid.sh`

### Model not loading

**Error:** `Failed to load model` or takes too long

**Fix:**
1. Check internet connection (model downloads from Hugging Face)
2. Manually download:
   ```bash
   python -c "from sentence_transformers import CrossEncoder; CrossEncoder('BAAI/bge-reranker-base')"
   ```
3. Check disk space (need ~2GB free)

### Slow inference

**Issue:** Reranking takes > 5 seconds

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

The base model provides:
- **Good precision:** Top-ranked papers are generally relevant
- **Decent recall:** Most relevant papers ranked in top 100
- **Moderate score separation:** Clear distinction between very relevant (0.6+) and irrelevant (< 0.2) papers
- **Consistent output:** Same query produces similar rankings

### Comparison with other models

vs. **Large model** (mixedbread-ai/mxbai-rerank-large-v1):
- ~85% of large model's accuracy
- 2-3x faster inference
- Uses ~1/3 of the GPU memory

vs. **Small model** (cross-encoder/ms-marco-MiniLM-L-6):
- ~10-15% better accuracy
- Similar speed (small model slightly faster)
- Better at complex scientific queries

**When to use base model:**
- Development and testing environments
- Laptops with 16-32GB RAM
- Cost-conscious production deployments
- Good balance between quality and performance

---

## 10) Switching to a different model

If you want higher quality (and have more GPU/RAM):

1. Stop the system:
   ```bash
   docker-compose down
   pkill -f reranker_service.py
   ```

2. Edit `api/run_configs/default.json`:
   ```json
   "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1",
   "batch_size": 32  // lower for larger model
   ```

3. Restart:
   ```bash
   ./start_hybrid.sh
   ```

See `SETUP_LARGE_RERANKER.md` for the large model guide, or `SETUP_SMALL_RERANKER.md` for minimal hardware.

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

- [ ] Verify hardware: 8GB+ GPU VRAM or 16GB+ RAM (Apple Silicon)
- [ ] Clone repo and copy `.env.example` to `.env`
- [ ] Add API keys to `.env` (S2, Anthropic)
- [ ] Configure `default.json` with base reranker model
- [ ] Run `./start_hybrid.sh` (first run takes ~5 min)
- [ ] Verify health endpoints
- [ ] Test query through web UI
- [ ] Adjust batch size for your hardware if needed

For highest quality or minimal hardware, see other setup guides.
