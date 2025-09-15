# ScholarQA Pipeline Test Scripts

This directory contains comprehensive test scripts for each stage of the ScholarQA pipeline, designed for transparency and detailed parameter inspection.

## Overview

The ScholarQA pipeline consists of three main stages:

1. **Query Decomposition** - Processes raw queries into structured search parameters
2. **Retrieval** - Fetches relevant academic papers and snippets from Semantic Scholar
3. **Reranking & Aggregation** - Reranks results and aggregates passages to paper level

## Test Scripts

### 1. test_query_decomposition.py

**Purpose**: Test Stage 1 - Query decomposition and preprocessing

**Usage**:

```bash
python test_scripts/test_query_decomposition.py --query "your query here"
```

**Features**:

- Shows original vs. rewritten queries
- Displays keyword queries for different search types
- Shows search filters and field restrictions
- Uses LiteLLM with CLAUDE_4_SONNET for query processing

**Sample Output**:

```
🔄 TESTING QUERY DECOMPOSITION STAGE
📝 Input Query: 'machine learning healthcare'
✅ Decomposed Query Object Created
📋 Rewritten Query: 'Machine learning applications in healthcare.'
🔍 Keyword Query: 'machine learning healthcare applications medical'
🎯 Search Filters: {'fieldsOfStudy': 'Computer Science,Medicine'}
```

### 2. test_retrieval.py

**Purpose**: Test Stage 2 - Comprehensive retrieval process with exhaustive parameter display

**Usage**:

```bash
python test_scripts/test_retrieval.py --query "your query here" [--max-results N]
```

**Features**:

- Shows ALL retrieval parameters and configurations
- Displays detailed search statistics
- Shows deduplication process
- Includes paper metadata fetching
- Suppresses async warnings for clean output

**Sample Output**:

```
🔄 TESTING RETRIEVAL STAGE
📝 Input Query: 'machine learning healthcare'
📊 EXHAUSTIVE RETRIEVAL PARAMETERS:
   🎯 Query (snippet): 'Machine learning in healthcare.'
   🔍 Keyword Query: 'machine learning healthcare applications'
   📏 Limit: 256
   🏷️ Fields of Study: 'Computer Science,Medicine'
   📋 API Fields: 'snippet.text,snippet.snippetKind,...'
✅ Retrieved 222 snippets from 13 unique papers
📈 Score Range: 0.123 - 0.987
```

### 3. test_reranking.py

**Purpose**: Test Stage 3 - Reranking and aggregation with complete transparency

**Usage**:

```bash
python test_scripts/test_reranking.py --query "your query here" [--max-results N]
```

**Features**:

- Shows reranking process parameters
- Displays aggregation to paper-level DataFrame
- Provides exhaustive DataFrame structure analysis
- Shows top papers with complete metadata
- Includes aggregation statistics

**Sample Output**:

```
🔄 TESTING RERANKING & AGGREGATION STAGE
📝 Input Query: 'machine learning healthcare'
🎯 STEP 3A: RERANKING
   📊 Input Candidates: 235 items
   ✅ Reranked Candidates: 235 items
   📈 Score Range After Reranking: 0.000 - 0.939
📊 STEP 3B: AGGREGATION TO PAPER LEVEL
   📝 Input: 235 passages
   ✅ Aggregated DataFrame: 178 papers
```

## Requirements

All scripts require:

- Python environment with ScholarQA dependencies
- S2_API_KEY environment variable for Semantic Scholar API
- LiteLLM configuration for language model access

## Installation

From the api directory:

```bash
pip install -e .
# or
pip install -r requirements.txt
```

## Environment Setup

Set your Semantic Scholar API key:

```bash
export S2_API_KEY="your_api_key_here"
```

## Design Philosophy

These test scripts prioritize:

- **Transparency**: Every parameter and intermediate result is displayed
- **Completeness**: Exhaustive coverage of all pipeline stages
- **Clarity**: Clean, emoji-enhanced output for easy reading
- **Debugging**: Detailed information for troubleshooting pipeline issues

## Common Parameters

All scripts support:

- `--query`: The search query to test
- `--max-results`: Maximum number of results to display (default varies by script)

## Output Interpretation

Each script provides:

1. **Input Parameters**: What goes into each stage
2. **Processing Details**: How the stage transforms the data
3. **Output Metrics**: Statistics about the results
4. **Sample Results**: Formatted examples of the output

## Troubleshooting

- **Import Errors**: Ensure you're running from the api directory
- **API Errors**: Check your S2_API_KEY environment variable
- **Async Warnings**: These are suppressed in retrieval script but may appear in others
- **Debug Output**: Some debug messages from retriever_base.py are expected

## Next Steps

After running these tests, you can:

1. Identify bottlenecks in specific pipeline stages
2. Validate parameter configurations
3. Debug retrieval quality issues
4. Understand the complete data flow through the pipeline

These scripts serve as both testing tools and documentation for the ScholarQA pipeline architecture.
