# ScholarQA Pipeline Test Scripts

Test scripts for each stage of the ScholarQA pipeline. Each script creates its own virtual environment for dependencies and cleanup.

## Pipeline Stages

1. **Query Decomposition**: Process raw queries and extract search filters
2. Retrieval: Fetch relevant papers
3. Reranking: Score and aggregate results
4. Evidence Extraction: Extract relevant quotes
5. Section Generation: Generate structured sections
6. Table Generation: Create comparison tables

## Scripts

### Stage 1: Query Decomposition

The `run_pipeline_stage1.py` script demonstrates query processing with automatic environment setup and comprehensive parameter display.

**Features:**

- Automatic conda environment creation and management
- Complete parameter visibility (year ranges, venues, authors, fields of study)
- Environment variable loading from `.env` file
- Clean output with cost tracking

**Usage:**

```bash
# Interactive mode
python run_pipeline_stage1.py

# With specific query
python run_pipeline_stage1.py --query "your research question"

# Skip environment setup (for repeated runs)
python run_pipeline_stage1.py --query "your query" --skip-setup
```

**Example:**

```bash
python run_pipeline_stage1.py --query "What are recent developments in transformer architectures by Attention Is All You Need authors?"
```

### Other Pipeline Stages

- `run_pipeline_stage2.py`

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

- Conda or Miniconda installed
- Semantic Scholar API key
- Anthropic API key (for Claude models)

## Setup

Create a `.env` file in the project root directory with your API keys:

```bash
S2_API_KEY=your_semantic_scholar_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

The scripts automatically handle environment setup and dependency installation.

## Notes

- Run scripts from the `api` directory to resolve imports.
- Retrieval uses both snippet search and keyword-based paper expansion.
- Evidence extraction reports token usage and cost; benign asyncio warnings are suppressed.

## Troubleshooting

- Import errors: confirm you are in the `api` directory and the package is installed.
- API errors: validate `S2_API_KEY` and network access.
- Rate limits/provider overload: re-run with fewer results or retry later.
