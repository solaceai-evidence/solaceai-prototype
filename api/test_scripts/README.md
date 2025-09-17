# ScholarQA Pipeline Test Scripts

Test scripts for each stage of the ScholarQA pipeline. Each script creates its own virtual environment for dependencies and cleanup.

## Pipeline Stages

1. Query Decomposition: Process raw queries
2. Retrieval: Fetch relevant papers
3. Reranking: Score and aggregate results
4. Evidence Extraction: Extract relevant quotes
5. Section Generation: Generate structured sections
6. Table Generation: Create comparison tables

## Scripts

Each script automatically sets up a virtual environment with required dependencies and cleans up after execution.

- `run_pipeline_stage1.py`

  ```bash
  python test_scripts/run_pipeline_stage1.py --query "your query"
  ```

- `run_pipeline_stage2.py`

  Parameters:
  - `query`: Research query to process
  - `max-results`: Maximum number of papers to use (default: 2)

  ```bash
  python test_scripts/run_pipeline_stage2.py --query "your query" [--max-results N]
  ```

- `run_pipeline_stage3.py`

  ```bash
  python test_scripts/run_pipeline_stage3.py --query "your query" [--max-results N]
  ```

- `run_pipeline_stage4.py`

  ```bash
  python test_scripts/run_pipeline_stage4.py --query "your query" [--max-results N]
  ```

- `run_pipeline_stage5.py`

  ```bash
  python test_scripts/run_pipeline_stage5.py --query "your query" [--max-results N]
  ```

- `run_pipeline_stage6.py`

  ```bash
  python test_scripts/run_pipeline_stage6.py --query "your query"
  ```

## Requirements

- Python 3.11+ environment with project dependencies.
- Semantic Scholar API key via `S2_API_KEY`.
- LLM access configured via LiteLLM (e.g., `CLAUDE_4_SONNET`).

## Installation

From the `api` directory:

```bash
pip install -e .
# or
pip install -r requirements.txt
```

## Environment

Set your Semantic Scholar API key:

```bash
export S2_API_KEY="your_api_key_here"
```

Recommended: place credentials in a `.env` file at the repository root (loaded by the scripts if `python-dotenv` is available).

## Notes

- Run scripts from the `api` directory to resolve imports.
- Retrieval uses both snippet search and keyword-based paper expansion.
- Evidence extraction reports token usage and cost; benign asyncio warnings are suppressed.

## Troubleshooting

- Import errors: confirm you are in the `api` directory and the package is installed.
- API errors: validate `S2_API_KEY` and network access.
- Rate limits/provider overload: re-run with fewer results or retry later.
