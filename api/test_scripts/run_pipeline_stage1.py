#!/usr/bin/env python3
"""
Simple test to demonstrate query decomposition step of the pipeline
"""
import os
import sys
from pathlib import Path
import logging
from typing import Optional

from venv_utils import managed_venv

# Add the API directory to Python path
api_dir = str(Path(__file__).parent.parent)
project_root = str(Path(api_dir).parent)
if api_dir not in sys.path:
    sys.path.append(api_dir)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Check for required environment variables
if not os.getenv("S2_API_KEY"):
    logger.error("Missing S2_API_KEY in environment variables")
    sys.exit(1)

from scholarqa.preprocess.query_preprocessor import decompose_query
from scholarqa.llms.constants import CLAUDE_4_SONNET


def test_pipeline_stage_1(query: Optional[str] = None):
    """Test the query processing and decomposition step of the pipeline

    Args:
        query: Optional pre-defined query for testing
    Returns:
        LLMProcessedQuery containing decomposition results
    """
    if not query:
        # Ask for input query via terminal
        print("\nEnter a query for decomposition (press Enter when done):")
        query = input("solace-ai> ").strip()

    if not query:
        logger.error("Query cannot be empty. Exiting")
        print("No query provided. Exiting.")
        return

    logger.info("Testing Pipeline Stage 1: Query Decomposition")
    logger.info("=" * 50)
    logger.info(f"Input Query: '{query}'")
    logger.info("=" * 50)

    try:
        # Run the decomposition step
        decomposed_query, completion_result = decompose_query(
            query=query, decomposer_llm_model=CLAUDE_4_SONNET
        )

        # Display the LLMProcessedQuery results
        logger.info("\n-" * 50)
        logger.info("\nDecomposition Results:")
        print(f"Original Query: {query}")
        print(f"Rewritten Query: {decomposed_query.rewritten_query}")
        print(f"Keyword Query: {decomposed_query.keyword_query}")
        print(f"Search Filters: {decomposed_query.search_filters}")
        print(f"LLM Cost: ${completion_result.cost:.4f}")

        return decomposed_query
    except Exception as e:
        logger.error(f"Error during decomposition: {str(e)}")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test ScholarQA Pipeline Stage 1: Query Decomposition"
    )
    parser.add_argument("--query", type=str, help="optional predefined query")

    args = parser.parse_args()

    # Use managed virtual environment
    with managed_venv(__file__, ["requirements.txt"]):
        from dotenv import load_dotenv
        from scholarqa.preprocess.query_preprocessor import decompose_query
        from scholarqa.llms.constants import CLAUDE_4_SONNET

        # Load environment variables from .env file
        load_dotenv(Path(project_root) / ".env")

        # Check for required environment variables
        if not os.getenv("S2_API_KEY"):
            logger.error("Missing S2_API_KEY in environment variables")
            sys.exit(1)

        test_pipeline_stage_1(args.query)
