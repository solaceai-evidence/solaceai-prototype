#!/usr/bin/env python3
"""
Script to demonstrate pipeline Stage 5: Section Generation
Shows configuration, settings, and data structures for section generation.
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


def test_section_generation_stage5(query: Optional[str] = None):
    """Display section generation configuration and data structures"""

    # Input handling
    if not query:
        print("\nEnter query for section generation testing:")
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
    print("PIPELINE STAGE 5: SECTION GENERATION")
    print("=" * 70)
    print(f"\nOriginal Query: '{query}'")

    # Show prerequisite stages
    print("\n" + "=" * 70)
    print("PREREQUISITE STAGES")
    print("=" * 70)
    print("""
Stage 5 builds upon outputs from previous stages:
   Stage 1: Query Decomposition → Rewritten query and search filters
   Stage 2: Retrieval → Retrieved paper passages
   Stage 3: Reranking → Aggregated and scored papers
   Stage 4: Evidence Extraction → Quote summaries per paper
""")

    # Show LLM prompts used
    print("=" * 70)
    print("LLM PROMPTS USED IN STAGE 5")
    print("=" * 70)
    print("""
This stage uses THREE LLM prompts from solaceai.llms.prompts:

1. SYSTEM_PROMPT_QUOTE_PER_PAPER
   Stage: Evidence Extraction (Stage 4 output used as input)
   Purpose: Extracts relevant evidence quotes from each paper
   Input: Paper content + query
   Output: Direct text excerpts that answer the query

2. SYSTEM_PROMPT_QUOTE_CLUSTER
   Stage: Quote Clustering (Stage 5 sub-step)
   Purpose: Groups quotes into thematic dimensions/sections
   Input: All extracted quotes from multiple papers
   Output: Structured plan with section names and quote assignments
   Example dimensions: "Interventions", "Outcomes", "Barriers"

3. PROMPT_ASSEMBLE_SUMMARY
   Stage: Section Writing (Stage 5 sub-step)
   Purpose: Generates narrative text for each section
   Input: Section plan + assigned quotes + paper metadata
   Output: Written section with proper citations
""")

    # Show configuration
    print("=" * 70)
    print("SECTION GENERATION CONFIGURATION")
    print("=" * 70)
    print("""
System Configuration:
   LLM Model:              anthropic/claude-sonnet-4-20250514
   Pipeline Workers:       3 (parallel processing)
   Max Tokens per Request: 25,000
   State Management:       LocalStateMgrClient (logs/ directory)
   Cost Tracking:          Enabled for all LLM calls

Processing Strategy:
   1. Quote Clustering:
      - Input: per_paper_summaries (dict of reference → quote)
      - Method: LLM analyzes all quotes to identify themes
      - Output: plan_json (dict of section_name → list of quotes)

   2. Citation Extraction:
      - Method: extract_quote_citations()
      - Links quotes to paper metadata (title, authors, year)
      - Builds per_paper_summaries_extd with full citation info

   3. Section Generation:
      - Method: generate_iterative_summary() - generator function
      - Processes each section in the plan iteratively
      - For each section:
        * Receives section name and assigned quotes
        * LLM synthesizes quotes into narrative text
        * Adds proper citations [corpus_id | authors | year]
      - Output: Section objects with title, text, citations

Rate Limiting:
   - LLM calls are rate-limited via litellm_helper
   - Respects RATE_LIMIT_OTPM environment variable
   - Semantic Scholar API calls handled by retriever (not in this stage)
""")

    # Show data structures
    print("=" * 70)
    print("SECTION GENERATION DATA STRUCTURES")
    print("=" * 70)
    print("""
INPUT (from Stage 4):
   per_paper_summaries.result (dict):
      Key: reference_string [corpus_id | authors | year | citations]
      Value: quote (str) - extracted evidence text

INTERMEDIATE (Stage 5 processing):
   cluster_result (list):
      [{"dimensions": [
          {"name": str, "format": str, "quotes": [ref_strings]}
      ]}]

   plan_json (dict):
      {"Section Title (format)": [list of reference_strings]}

   per_paper_summaries_extd (dict):
      Extended summaries with full citation metadata

OUTPUT (Stage 5):
   generated_sections (list of Section objects):
      section.title:     str - Section heading
      section.text:      str - Full narrative text
      section.citations: list[str] - Reference strings cited

   Statistics tracked:
      - Word count per section
      - Citation count per section
      - Papers cited per section
      - Total token usage (input/output)
      - Total API cost
""")

    # Show KEY CONCEPT
    print("=" * 70)
    print("KEY CONCEPT")
    print("=" * 70)
    print("""
Section generation transforms extracted evidence quotes into coherent
narrative sections using a two-step LLM process:

Step 1 - CLUSTERING:
   LLM analyzes all quotes and groups them by theme
   Creates a plan with section titles and quote assignments
   Example: Groups quotes about "interventions", "outcomes", "barriers"

Step 2 - SYNTHESIS:
   For each planned section:
      - LLM receives the section theme and relevant quotes
      - Generates narrative text weaving quotes together
      - Adds proper citations for each referenced paper
      - Ensures coherent flow and academic writing style

The result is a structured document with multiple thematic sections,
each synthesizing evidence from relevant papers with full citations.
""")

    # Show example flow
    print("=" * 70)
    print("EXAMPLE DATA FLOW")
    print("=" * 70)
    print("""
Input (Stage 4 Evidence):
   {
     "[279023164 | Birhan et al. | 2025 | Citations: 1]":
        "Suicidal behavior prevalence was 23.4%...",
     "[276925840 | Melkam et al. | 2025 | Citations: 0]":
        "PTSD was significantly associated..."
   }

After Clustering:
   {
     "Mental Health Challenges (paragraph)": [
        "[279023164 | Birhan et al. | 2025 | Citations: 1]",
        "[276925840 | Melkam et al. | 2025 | Citations: 0]"
     ],
     "Intervention Approaches (paragraph)": [...]
   }

Generated Section:
   Section(
     title="Mental Health Challenges",
     text="Research in conflict-affected areas shows high rates
           of mental health issues. Birhan et al. (2025) found
           suicidal behavior prevalence of 23.4%...",
     citations=["[279023164 | Birhan et al. | 2025 | Citations: 1]",
                "[276925840 | Melkam et al. | 2025 | Citations: 0]"]
   )
""")

    print("\n" + "=" * 70)
    print("STAGE 5 CONFIGURATION DISPLAY COMPLETE")
    print("=" * 70)
    print("""
Note: This script shows the configuration and data structures.
To run the full pipeline including API calls, use the ScholarQA system
which handles rate limiting and caching appropriately.
""")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Display Stage 5 configuration and data structures",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--query", type=str, help="Research query to display")

    args = parser.parse_args()
    test_section_generation_stage5(args.query)
