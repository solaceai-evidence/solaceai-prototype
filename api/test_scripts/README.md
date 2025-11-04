# Solace-ai Pipeline Test Scripts

Test scripts for each stage of the Solace-ai pipeline. Each script demonstrates a specific pipeline stage with detailed explanations of configuration, prompts, and data structures.

## Quick Start

1. **Install the solaceai package:**
   ```bash
   cd api/
   pip install -e .
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root (`solaceai-prototype/`) with:
   ```
   S2_API_KEY=your_semantic_scholar_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

3. **Run a test script:**
   ```bash
   cd test_scripts/
   python3 run_pipeline_stage1.py
   ```
   Or press Enter to use the default query:
   ```
   "how can we improve mental health outcomes and reduce substance misuse among displaced communities in Ethiopia"
   ```

## Pipeline Stages

Each stage builds upon the previous one:

1. **Query Decomposition** - Analyzes query and extracts search parameters
2. **Retrieval** - Fetches relevant paper passages from Semantic Scholar
3. **Reranking & Aggregation** - Scores passages and aggregates to paper level
4. **Evidence Extraction** - Extracts relevant quotes using LLM
5. **Section Generation** - Synthesizes quotes into narrative sections
6. **Table Generation** - Creates structured comparison tables

## Available Scripts

### Stage 1: Query Decomposition
**Script:** `run_pipeline_stage1.py`

**What it does:**
- Processes your research question using LLM (QUERY_DECOMPOSER_PROMPT)
- Extracts search filters: year range, venues, fields of study, authors, limit
- Shows how LLM interprets natural language into structured parameters

**Output includes:**
- Original and rewritten query
- Keyword query for search
- Detected search filters with descriptions
- LLM prompt information
- Token usage and cost

**Usage:**
```bash
# Interactive mode (press Enter for default query)
python run_pipeline_stage1.py

# Direct question input
python run_pipeline_stage1.py --query "your research question"
```

### Stage 2: Document Retrieval
**Script:** `run_pipeline_stage2.py`

**What it does:**
- Uses Stage 1 results to search Semantic Scholar
- Retrieves relevant paper passages
- Shows 10 data fields for each retrieved passage

**Output includes:**
- Query decomposition results
- Search parameters used
- Retrieved passages with metadata
- Field descriptions (corpus_id, title, text, score, section_title, etc.)
- Field availability summary

**Usage:**
```bash
# Interactive mode
python run_pipeline_stage2.py

# With specific query
python run_pipeline_stage2.py --query "your research question"
```

### Stage 3: Reranking & Aggregation
**Script:** `run_pipeline_stage3.py`

**What it does:**
- Reranks retrieved passages using PaperFinder algorithm
- Aggregates multiple passages from same paper
- No LLM used (pure algorithmic processing)

**Output includes:**
- Reranking statistics
- Aggregated paper-level data (13 fields)
- KEY CONCEPT: Explains aggregation process
- Top papers with relevance scores

**Usage:**
```bash
python run_pipeline_stage3.py
```

### Stage 4: Evidence Extraction
**Script:** `run_pipeline_stage4.py`

**What it does:**
- Uses LLM (SYSTEM_PROMPT_QUOTE_PER_PAPER) to extract evidence
- Selects relevant quotes from each paper
- Tracks extraction statistics and costs

**Output includes:**
- Evidence extraction data structure (7 fields)
- Extraction statistics (quote lengths, model usage)
- Top extracted evidence with quotes
- Cost analysis (tokens, API costs)
- KEY CONCEPT: Explains evidence extraction process

**Usage:**
```bash
python run_pipeline_stage4.py
```

### Stage 5: Section Generation
**Script:** `run_pipeline_stage5.py`

**What it shows:**
- Configuration and settings for section generation
- Three LLM prompts used (SYSTEM_PROMPT_QUOTE_PER_PAPER, SYSTEM_PROMPT_QUOTE_CLUSTER, PROMPT_ASSEMBLE_SUMMARY)
- Processing strategy: clustering → citation extraction → section writing
- Data structures (input, intermediate, output)
- **Note:** This is an informational display - no API calls made

**Output includes:**
- Prerequisite stages summary
- LLM prompts with purposes
- System configuration (workers, tokens, rate limiting)
- Section generation data structures
- KEY CONCEPT: Two-step LLM process
- Example data flow

**Usage:**
```bash
python run_pipeline_stage5.py
```

### Stage 6: Table Generation
**Script:** `run_pipeline_stage6.py`

**What it shows:**
- Configuration and settings for table generation
- Three LLM prompts (ATTRIBUTE_PROMPT, VALUE_GENERATION_FROM_ABSTRACT, VALUE_CONSISTENCY_PROMPT_ZS)
- Processing strategy: column identification → cell extraction → standardization
- Data structures for tables
- **Note:** This is an informational display - no API calls made

**Output includes:**
- Prerequisite stages summary
- LLM prompts with purposes
- Table generation configuration (threads, rate limiting)
- Table data structures (columns, rows, cells)
- KEY CONCEPT: Three-step process
- Example table structure

**Usage:**
```bash
python run_pipeline_stage6.py
```

## Requirements

- **Python:** 3.11 or higher (3.13 recommended)
- **API Keys:**
  - Semantic Scholar API key (S2_API_KEY)
  - Anthropic API key (ANTHROPIC_API_KEY)

## Default Query

All scripts use the same default query when you press Enter without typing:
```
"how can we improve mental health outcomes and reduce substance misuse among displaced communities in Ethiopia"
```

This ensures consistent testing across all pipeline stages.

## Understanding the Output

Each script is designed to be educational and shows:

1. **LLM Prompts Used** - Names and purposes of prompts
2. **Data Field Descriptions** - Explains each field in the data structures
3. **KEY CONCEPT Boxes** - Highlights important transformations
4. **Configuration Details** - Shows all settings and parameters
5. **Statistics** - Tokens, costs, processing details

This transparency helps team members understand:
- How each stage processes data
- What LLM prompts are used and why
- What data structures are created
- How stages connect in the pipeline

## Running the Scripts

**From the test_scripts directory:**
```bash
cd api/test_scripts/

# Stage 1-4: Run full pipeline with API calls
python3 run_pipeline_stage1.py  # Query decomposition
python3 run_pipeline_stage2.py  # Retrieval
python3 run_pipeline_stage3.py  # Reranking
python3 run_pipeline_stage4.py  # Evidence extraction

# Stage 5-6: Configuration display only (no API calls)
python3 run_pipeline_stage5.py  # Section generation config
python3 run_pipeline_stage6.py  # Table generation config
```

**All scripts:**
- Load API keys from `.env` file automatically
- Support interactive mode (press Enter for default query)
- Support `--query` parameter for direct input
- Display comprehensive educational output

## Troubleshooting

**Import errors:**
```bash
cd api/
pip install -e .
```

**Missing environment variables:**
- Ensure `.env` file exists in project root (`solaceai-prototype/`)
- Check that both S2_API_KEY and ANTHROPIC_API_KEY are set

**API rate limits:**
- Stages 1-4 make API calls and may hit rate limits
- Stages 5-6 are informational only (no API calls)
- The solaceai system handles rate limiting via litellm_helper
- Wait a few minutes if you hit limits, then retry

**Python version issues:**
- Use Python 3.13 or higher (Homebrew: `/opt/homebrew/bin/python3.13`)
- System Python 3.9 may not be compatible

## Documentation

For detailed prompt documentation, see:
- `PROMPT_DOCUMENTATION.md` - Comprehensive guide to all LLM prompts by stage
