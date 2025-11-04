#!/usr/bin/env python3
"""
Script to demonstrate Pipeline Stage 6: Table Generation
Shows configuration, settings, and data structures for table generation.
This is an informational display - no API calls are made.
"""
import os
import sys
from pathlib import Path
from typing import Optional

# Setup paths
api_dir = str(Path(__file__).parent.parent)
project_root = str(Path(api_dir).parent)
sys.path.append(api_dir)

# Load environment variables from .env file
env_file = Path(project_root) / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


def test_table_generation6(query: Optional[str] = None):
    """Display table generation configuration and data structures"""

    # Input handling
    if not query:
        print("\nEnter query for table generation testing:")
        print("(Press Enter without typing to use default query)")
        query = input("Query: ").strip()
    if not query:
        # Use default query if none provided
        default_query = (
            "how can we improve mental health outcomes and reduce "
            "substance misuse among displaced communities in Ethiopia"
        )
        query = default_query
        print(f"\nUsing default query: {query}")

    print("\n" + "=" * 70)
    print("PIPELINE STAGE 6: TABLE GENERATION")
    print("=" * 70)
    print(f"\nOriginal Query: '{query}'")

    # Show prerequisite stages
    print("\n" + "=" * 70)
    print("PREREQUISITE STAGES")
    print("=" * 70)
    print("""
Stage 6 builds upon outputs from previous stages:
   Stage 1: Query Decomposition → Rewritten query and search filters
   Stage 2: Retrieval → Retrieved paper passages
   Stage 3: Reranking → Aggregated and scored papers
   Stage 4: Evidence Extraction → Quote summaries per paper
   Stage 5: Section Generation → Clustered evidence dimensions
""")

    # Show LLM prompts used
    print("=" * 70)
    print("LLM PROMPTS USED IN STAGE 6")
    print("=" * 70)
    print("""
This stage uses THREE LLM prompts from solaceai.table_generation.prompts:

1. ATTRIBUTE_PROMPT
   Stage: Column Definition (Stage 6 sub-step)
   Purpose: Identifies attributes for comparing papers
   Input: Query + evidence dimensions + paper corpus
   Output: Column definitions with names and descriptions
   Example columns: "Methodology", "Sample Size", "Key Findings"

2. VALUE_GENERATION_FROM_ABSTRACT
   Stage: Cell Population (Stage 6 sub-step)
   Purpose: Extracts values from paper abstracts for each column
   Input: Paper abstract + column definition
   Output: Brief phrases (<10 words) or 'N/A'
   Format: Concise, factual statements

3. VALUE_CONSISTENCY_PROMPT_ZS
   Stage: Value Standardization (Stage 6 sub-step)
   Purpose: Ensures consistent formatting across table cells
   Input: All values for a column + column definition
   Output: Standardized values in JSON format
   Goal: Uniform terminology and structure
""")

    # Show configuration
    print("=" * 70)
    print("TABLE GENERATION CONFIGURATION")
    print("=" * 70)
    print("""
System Configuration:
   LLM Model:              anthropic/claude-sonnet-4-20250514
   Column Model:           Same as LLM Model
   Value Model:            Same as LLM Model
   Max Threads:            3 (parallel cell generation)
   Cost Tracking:          Enabled for all LLM calls

Processing Strategy:
   1. Column Generation:
      - Input: original_query + evidence dimensions + corpus_ids
      - Method: generate_attribute_suggestions()
      - Parameters: n_attributes (default: 5)
      - Output: List of column definitions

   2. Paper Subselection (if enabled):
      - Method: run_subselection flag
      - Selects most relevant papers for table
      - Balances coverage with table size

   3. Cell Population:
      - Method: TableGenerator.run_table_generation()
      - Multi-threaded parallel processing
      - For each [paper][column]:
        * Fetches paper abstract from Semantic Scholar
        * LLM extracts relevant value
        * Value standardization applied
      - Output: Populated table cells

   4. Table Assembly:
      - Combines columns, rows, and cells
      - Creates structured table object
      - Tracks metadata (costs, tokens, timing)

Rate Limiting:
   - LLM calls are rate-limited via CostAwareLLMCaller
   - Respects API rate limits for both Claude and Semantic Scholar
   - Parallel processing optimizes throughput within limits
   - Caching reduces duplicate API calls
""")

    # Show data structures
    print("=" * 70)
    print("TABLE GENERATION DATA STRUCTURES")
    print("=" * 70)
    print("""
INPUT (from Stage 5):
   cluster_result.result (dict):
      "dimensions": [
          {"name": str, "format": str, "quotes": [ref_strings]}
      ]
      Provides thematic structure for column generation

   corpus_ids (list):
      List of paper IDs to include in table rows

INTERMEDIATE (Stage 6 processing):
   attribute_result (dict):
      {
        "columns": [
            {"name": str, "description": str}
        ],
        "cost": {"cost_value": float}
      }

   table_generator:
      Object handling multi-threaded cell generation
      Tracks costs per cell, column, row

OUTPUT (Stage 6):
   table_result (object):
      table_result.columns: list[Column]
         - column.name: str
         - column.description: str

      table_result.rows: list[Row]
         - row.corpus_id: str
         - row.title: str
         - row.authors: list
         - row.year: int

      table_result.cells: dict[row_id][column_name]
         - cell.value: str (brief phrase or 'N/A')
         - cell.source: str (abstract, full text, etc.)

   costs (dict):
      {
        "cell_cost": [{"cost_value": float}, ...],
        "column_cost": {"cost_value": float},
        "total_cost": float
      }
""")

    # Show KEY CONCEPT
    print("=" * 70)
    print("KEY CONCEPT")
    print("=" * 70)
    print("""
Table generation creates structured comparisons across papers by:

Step 1 - COLUMN IDENTIFICATION:
   LLM analyzes the query and evidence dimensions
   Identifies key attributes that distinguish papers
   Creates column definitions (e.g., "Methodology", "Outcomes")

Step 2 - CELL EXTRACTION:
   For each [paper][column] combination:
      - Fetches paper content (abstract, full text if available)
      - LLM extracts the specific attribute value
      - Formats as brief phrase (<10 words)
      - Returns 'N/A' if attribute not found

Step 3 - STANDARDIZATION:
   Reviews all values within each column
   Ensures consistent terminology and formatting
   Example: "RCT" → "Randomized Controlled Trial"

The result is a structured table enabling quick comparison of papers
across key dimensions relevant to the research query.
""")

    # Show example flow
    print("=" * 70)
    print("EXAMPLE DATA FLOW")
    print("=" * 70)
    print("""
Input (Stage 5 Evidence Dimensions):
   dimensions: [
     {"name": "Mental Health Interventions", "quotes": [...]},
     {"name": "Outcome Measures", "quotes": [...]}
   ]
   corpus_ids: [279023164, 276925840, 232353652]

After Column Generation:
   columns: [
     {"name": "Intervention Type", "description": "Type of mental health intervention used"},
     {"name": "Target Population", "description": "Population group studied"},
     {"name": "Key Outcomes", "description": "Main findings or outcomes"}
   ]

Cell Extraction Example:
   Paper: [279023164 | Birhan et al. | 2025]
   Column: "Intervention Type"
   Abstract: "...cross-sectional study of suicidal behavior..."
   LLM Output: "Cross-sectional observational study"

Final Table Structure:
   | Paper                    | Intervention Type | Target Population | Key Outcomes |
   |--------------------------|-------------------|-------------------|--------------|
   | Birhan et al. (2025)     | Cross-sectional   | War-affected      | 23.4%        |
   |                          | study             | individuals       | prevalence   |
   | Melkam et al. (2025)     | Survey study      | IDPs in NW        | PTSD         |
   |                          |                   | Ethiopia          | association  |
   | Yitbarek et al. (2021)   | Qualitative       | Health extension  | Barriers     |
   |                          | study             | workers           | identified   |
""")

    print("\n" + "=" * 70)
    print("STAGE 6 CONFIGURATION DISPLAY COMPLETE")
    print("=" * 70)
    print("""
Note: This script shows the configuration and data structures.
To run the full pipeline including API calls, use the ScholarQA system
which handles rate limiting and caching appropriately.
""")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Display Stage 6 configuration and data structures",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--query", type=str, help="Research query to display")

    args = parser.parse_args()
    test_table_generation6(args.query)
