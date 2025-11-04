#!/usr/bin/env python3
"""
Script to test Pipeline Stage 1: Query Decomposition

Prerequisites:
    pip install -e ../
"""
import argparse
import os
import sys
from pathlib import Path

# Setup paths
script_dir = Path(__file__).parent
api_dir = script_dir.parent
project_root = api_dir.parent

# Add API directory to path
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Load environment variables from .env file (no external dependencies needed)
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

# Check for required environment variables
if not os.getenv("S2_API_KEY"):
    print("\nError: Missing S2_API_KEY environment variable")
    print("Create a .env file in project root with:")
    print("  S2_API_KEY=your_key")
    print("  ANTHROPIC_API_KEY=your_key")
    sys.exit(1)


def discover_search_filter_parameters():
    """Discover and display all available search filter parameters"""
    # Known search filter parameters based on query_preprocessor
    discovered_params = {
        "year": {
            "model_field": "year_range",
            "description": (
                "Time range for publications. LLM interprets terms like 'recent' (2022-2025), "
                "'last decade' (2015-2025), or specific years mentioned in the query."
            ),
        },
        "venue": {
            "model_field": "venues",
            "description": (
                "Specific journals or conferences mentioned in the query "
                "(e.g., 'Nature', 'NeurIPS', 'ACL'). Comma-separated list."
            ),
        },
        "fieldsOfStudy": {
            "model_field": "field_of_study",
            "description": (
                "Academic disciplines detected from query content. LLM maps topics to 23 predefined fields "
                "(e.g., 'mental health' → Psychology, 'climate' → Environmental Science)."
            ),
        },
        "authors": {
            "model_field": "authors",
            "description": (
                "Specific researcher names mentioned in the query. "
                "LLM extracts author names explicitly requested by the user."
            ),
        },
        "limit": {
            "model_field": "limit",
            "description": (
                "Maximum number of results. LLM infers from phrases like 'top 10 papers' "
                "or 'a few examples'. Default is system-defined if not specified."
            ),
        },
    }
    return discovered_params


def run_query_decomposition(query: str):
    """Run query decomposition and display comprehensive results"""

    try:
        from solaceai.llms.constants import CLAUDE_4_SONNET
        from solaceai.preprocess.query_preprocessor import decompose_query
    except ImportError as e:
        print(f"\nError importing solaceai: {e}")
        print("Please install: cd api/ && pip install -e .")
        sys.exit(1)

    print(f"\n{'='*70}")
    print("PIPELINE STAGE 1: QUERY DECOMPOSITION")
    print(f"{'='*70}")
    print(f"Input Query: '{query}'")
    print(f"LLM Model: {CLAUDE_4_SONNET}")
    print(f"{'='*70}")

    try:
        # Run the decomposition step
        decomposed_query, completion_result = decompose_query(
            query=query, decomposer_llm_model=CLAUDE_4_SONNET
        )

        # Display comprehensive results overview
        print("\nDECOMPOSITION RESULTS:")
        print("-" * 70)

        # Original vs processed queries
        print("\nQUERY PROCESSING:")
        print(f"  Original Query:          '{query}'")
        print(
            f"  Rewritten Query:         '{decomposed_query.rewritten_query or '[Not generated]'}'"
        )
        print(
            f"  Keyword Query:           '{decomposed_query.keyword_query or '[Not generated]'}'"
        )

        # Display all search filter parameters
        print("\nSEARCH FILTERS:")
        filters = decomposed_query.search_filters
        discovered_params = discover_search_filter_parameters()

        # Display all known parameters, whether they have values or not
        for filter_name, param_info in discovered_params.items():
            display_name = filter_name.replace("_", " ").title()
            if filter_name == "fieldsOfStudy":
                display_name = "Fields of Study"
            elif filter_name == "year":
                display_name = "Year Range"

            value = filters.get(filter_name, "[Not specified]")
            description = param_info.get("description", "")
            print(f"  {display_name:<20} {value}")
            print(f"    → {description}")

        # Show any additional filters that weren't in our discovered parameters
        unknown_filters = {
            k: v for k, v in filters.items() if k not in discovered_params
        }
        if unknown_filters:
            print("\n  ADDITIONAL FILTERS:")
            for filter_name, value in unknown_filters.items():
                display_name = filter_name.replace("_", " ").title()
                print(f"    {display_name:<18} {value}")

        # LLM Prompts Used
        print("\nLLM PROMPTS USED:")
        print("  QUERY_DECOMPOSER_PROMPT")
        print("     Purpose: Analyzes query and extracts structured search parameters")
        print("     Outputs: Rewritten query, keyword query, and search filters")

        # LLM execution details
        print("\nEXECUTION DETAILS:")
        print(f"  Model Used:              {completion_result.model}")
        print(f"  Input Tokens:            {completion_result.input_tokens}")
        print(f"  Output Tokens:           {completion_result.output_tokens}")
        print(f"  Total Tokens:            {completion_result.total_tokens}")
        print(f"  Cost:                    ${completion_result.cost:.4f}")

        print("-" * 70)

        return True

    except Exception as e:
        print("\nERROR DURING DECOMPOSITION:")
        print(f"  {str(e)}")
        print("-" * 70)
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test ScholarQA Pipeline Stage 1: Query Decomposition"
    )
    parser.add_argument("--query", type=str, help="optional predefined query")
    args = parser.parse_args()

    try:
        query = args.query
        if not query:
            # Ask for input query via terminal
            print("\nEnter a query for decomposition (press Enter when done):")
            print("(Press Enter without typing to use default query)")
            query = input("solace-ai> ").strip()

        if not query:
            # Use default query if none provided
            query = "how can we improve mental health outcomes and reduce substance misuse among displaced communities in Ethiopia"
            print(f"\nUsing default query: {query}")

        print(f"\n{'='*70}")
        print("RUNNING PIPELINE STAGE 1")
        print(f"{'='*70}")

        # Run pipeline stage 1
        success = run_query_decomposition(query)

        if success:
            print(f"\n{'='*70}")
            print("PIPELINE STAGE 1 COMPLETED SUCCESSFULLY")
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print("PIPELINE STAGE 1 FAILED")
            print(f"{'='*70}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
