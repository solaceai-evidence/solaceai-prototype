# Solace-AI System

A minimal guide to install, configure, and run the Solace-AI prototype, with instructions for both local (native) and Modal (cloud) reranker options.

For further information, see the full documentation in `README.md`.

## 1) Prerequisites
- macOS or Linux with Docker Desktop running
- Git
- Conda (recommended) or Python 3.11 + venv
- Accounts/keys:
  - Semantic Scholar: `S2_API_KEY`
  - Anthropic: `ANTHROPIC_API_KEY`
  - OpenAI (optional): `OPENAI_API_KEY`
  - Modal (only if using Modal reranker): `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`

## 2) Get the code and env file
```bash
git clone <your-repo-url> solaceai-prototype
cd solaceai-prototype
cp .env.example .env
```
Edit `.env` and fill in the required keys (see above).

## 3) Create and activate Python environment
```bash
# Conda (recommended)
conda create -n solaceai python=3.11 -y
conda activate solaceai
# or venv
python3 -m venv venv
source venv/bin/activate
```

## 4) Choose reranker mode (local vs Modal)
Open `api/run_configs/default.json` and set:
- Local (native) reranker:
  ```json
  "reranker_service": "remote",
  "reranker_args": {
    "model_name_or_path": "mixedbread-ai/mxbai-rerank-large-v1",
    "batch_size": 32
  }
  ```
- Modal (cloud) reranker:
  ```json
  "reranker_service": "modal",
  "reranker_args": {
    "app_name": "solaceai-reranker",
    "api_name": "inference_api",
    "batch_size": 256
  }
  ```
Ensure `.env` has Modal credentials when using Modal.

Model choices for local (remote) mode — pick based on laptop capacity:
- Very small: `cross-encoder/ms-marco-MiniLM-L-6-v2` (fits easiest; lowest memory)
- Small/base: `BAAI/bge-reranker-base` (good for 32GB macOS; balanced quality)
- Default/large: `mixedbread-ai/mxbai-rerank-large-v1` (needs more RAM/GPU)
For weaker laptops, also lower `batch_size` to 8–16.

## 5) (If using Modal) Deploy the reranker once
```bash
pip install modal
cd api/solaceai/rag/reranker/modal_deploy
modal deploy ai2-scholar-qa-reranker.py
modal run ai2-scholar-qa-reranker.py   # quick test
cd -   # back to repo root
```
Keep `app_name` in `default.json` the same as `APP_NAME` in `api/solaceai/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py`.

## 6) Start the system
From the repo root (with env activated):
```bash
chmod +x start_hybrid.sh
./start_hybrid.sh
```
The script will:
- Read `api/run_configs/default.json`
- Install needed deps (PyTorch for local, Modal SDK for cloud)
- Start Docker services (API/UI) and the local reranker if configured

## 7) Health checks
```bash
# API
curl -s http://localhost:8000/health && echo "API ready"

# Local reranker (only when reranker_service = remote)
curl -s http://localhost:10001/health && echo "Reranker ready"
```

## 8) Switching reranker mode
- Edit `api/run_configs/default.json` to set `reranker_service` to `remote` (local) or `modal` (cloud).
- Re-run `./start_hybrid.sh`.

## 9) Troubleshooting (brief)
- Modal auth errors: verify `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`; run `modal token new` if needed.
- SDK errors (Modal): `pip install --upgrade modal`.
- CUDA OOM (local): lower `batch_size` in `default.json`.
- Docker issues: `docker-compose down && docker-compose up -d --build`.


## 10) Choosing a smaller cross-encoder (laptops)

- Use a lighter model if your laptop has limited RAM/GPU.
- Suggested models (Hugging Face IDs):
  - `cross-encoder/ms-marco-MiniLM-L-6-v2` (very small; fits easiest)
  - `BAAI/bge-reranker-base` (good balance for 32GB RAM/macOS)
- Local (native) change: update `model_name_or_path` in `default.json` and reduce `batch_size` (e.g., 8–16), then rerun `./start_hybrid.sh`.
- Modal change: set `MODEL_NAME` in `api/solaceai/rag/reranker/modal_deploy/ai2-scholar-qa-reranker.py`, redeploy (`modal deploy ...`), ensure `app_name` matches, then rerun `./start_hybrid.sh`.

## 11) Useful commands

```bash
# Restart API container
docker-compose restart api

# Modal logs (if using Modal)
modal app logs solaceai-reranker --follow
```
