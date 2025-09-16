# ScholarQA Pipeline Test Scripts

Concise test drivers for each stage of the ScholarQA pipeline. Outputs are text-only (no emojis) and emphasize transparency of parameters and intermediate results.

## Pipeline Stages

1. Query Decomposition: Rewrite and structure a raw query.
2. Retrieval: Fetch relevant snippets and additional papers from Semantic Scholar.
3. Reranking & Aggregation: Rerank candidates and aggregate to paper-level.
4. Evidence Extraction: Select quotes per paper and report usage/costs.

## Scripts

- `test_query_decomposition.py`
   - Purpose: Stage 1 — query decomposition and preprocessing.
   - Usage:

      ```bash
      python test_scripts/test_query_decomposition.py --query "your query"
      ```

- `test_retrieval.py`
   - Purpose: Stage 2 — end-to-end retrieval with complete parameter display.
   - Usage:

      ```bash
      python test_scripts/test_retrieval.py --query "your query" [--max-results N]
      ```

   - Notes: Shows all request parameters, deduplication behavior, score ranges, and fetched metadata.

- `test_reranking.py`
   - Purpose: Stage 3 — reranking and aggregation with DataFrame inspection.
   - Usage:

      ```bash
      python test_scripts/test_reranking.py --query "your query" [--max-results N]
      ```

   - Notes: Prints DataFrame columns, example entries, and aggregation stats.

- `test_evidence_extraction.py`
   - Purpose: Stage 4 — quote selection with model usage and cost reporting.
   - Usage:

      ```bash
      python test_scripts/test_evidence_extraction.py --query "your query" [--max-results N]
      ```

   - Notes: Displays papers processed, quotes found, token usage, total cost, and concise evidence previews. Async shutdown noise can be suppressed for readability using `--quiet` (default) or shown using `--no-quiet`.

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
