# Solace-ai Pipeline Test Scripts

Test scripts for each stage of the Solace-ai pipeline. Each script automatically sets up its own environment and handles all dependencies.

## Pipeline Stages

1. Query Decomposition: Process raw queries and extract search filters
2. Retrieval: Fetch relevant passages from semantic scholar database
3. Reranking: Score and aggregate results
4. Evidence Extraction: Extract relevant quotes
5. Section Generation: Generate structured sections
6. Table Generation: Create comparison tables

## Scripts

### Stage 1: Query Decomposition

The `run_pipeline_stage1.py` script processes your research question and shows what search parameters it extracted.

**What it does:**

- Breaks down your question into search terms
- Shows all available search options (years, journals, authors, research areas)
- Displays which filters were found in your question
- Handles environment setup automatically

**Output**
Each script shows detailed information about what it's doing, including:

- Which search parameters were found in your question
- How many papers were retrieved
- What information is available in the results
- Processing time and costs (prototype)

**Usage:**

```bash
# Interactive mode (asks for your question)
python run_pipeline_stage1.py

# Direct question input
python run_pipeline_stage1.py --query "your research question"

# Skip setup for faster repeat runs
python run_pipeline_stage1.py --query "your research question" --skip-setup
```

**Example:**

```bash
python run_pipeline_stage1.py --query "What are recent developments in health interventions for addressing mental health issues in displaced communities?"
# Solace-ai Pipeline Test Scripts

Test scripts for each stage of the Solace-ai pipeline. Each script automatically sets up its own environment and handles all dependencies.

## Pipeline Stages

1. Query Decomposition: Process raw queries and extract search filters
2. Retrieval: Fetch relevant passages from semantic scholar database
3. Reranking: Score and aggregate results
4. Evidence Extraction: Extract relevant quotes
5. Section Generation: Generate structured sections
6. Table Generation: Create comparison tables


### Stage 2: Document Retrieval

The `run_pipeline_stage2.py` script finds academic papers related to your question and shows detailed search information.

**What it does:**

- Uses the processed query to search for relevant papers
- Shows all search parameters being used
- Displays comprehensive information about found papers
- Reports statistics about the search results

**Usage:**

```bash
# Basic search
python run_pipeline_stage2.py --query "your research question"

# Limit number of papers
python run_pipeline_stage2.py --query "your research question" --max-results 5

# Skip setup for faster repeat runs
python run_pipeline_stage2.py --query "your research question" --skip-setup
```

**Example:**

```bash
python run_pipeline_stage2.py --query "Papers by Elyas Abdulahi on Environmental Science" --max-results 3

python run_pipeline_stage2.py --query "What are recent developments in health interventions for addressing mental health issues in displaced communities?" --max-results 5
```

### Other Pipeline Stages

Additional pipeline stages are available with similar usage patterns:

- **Stage 3 (Reranking)**: `run_pipeline_stage3.py`
- **Stage 4 (Evidence Extraction)**: `run_pipeline_stage4.py`
- **Stage 5 (Section Generation)**: `run_pipeline_stage5.py`
- **Stage 6 (Table Generation)**: `run_pipeline_stage6.py`

Each stage accepts these parameters:

- `--query`: Your research question
- `--max-results`: Number of papers to process (default: 2)
- `--skip-setup`: Skip environment setup for faster repeat runs

**Basic usage for any stage:**

```bash
python run_pipeline_stageX.py --query "your research question" --max-results 3
```

## Requirements

- Python 3.11 or higher
- Semantic Scholar API key
- Anthropic API key (for Claude models)

## Setup

Create a `.env` file in the project root directory with your API keys:

```bash
S2_API_KEY=your_semantic_scholar_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

The scripts automatically handle all environment setup and dependency installation using Python virtual environments.

## Running the Scripts

Run all scripts from the `api/test_scripts` directory. The scripts will automatically:

- Set up the required Python environment
- Install necessary dependencies
- Load your API keys from the `.env` file
- Process your research question
- Display comprehensive results

## Troubleshooting

**Script won't start:**

- Make sure you're in the `api/test_scripts` directory
- Check that your `.env` file exists in the project root with valid API keys

**API errors:**

- Verify your Semantic Scholar API key is correct
- Check your internet connection
- Some queries may hit rate limits - try running again after a few minutes

**Slow performance:**

- Use `--skip-setup` flag for repeat runs to skip environment setup
- Reduce `--max-results` number for faster processing
