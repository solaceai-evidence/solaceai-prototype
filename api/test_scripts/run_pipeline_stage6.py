#!/usr/bin/env python3
"""
Test for ScholarQA Pipeline Stage 6: Table Generation

Shows key steps in table generation process using semantic search and LLM
"""
import os
import sys
from pathlib import Path
from typing import Optional

from venv_utils import managed_venv

# Add the API directory to Python path
api_dir = str(Path(__file__).parent.parent)
project_root = str(Path(api_dir).parent)
if api_dir not in sys.path:
    sys.path.append(api_dir)


def test_table_generation(query: Optional[str] = None) -> None:
    """
    Test the table generation stage of the ScholarQA pipeline.
    Shows column generation and table cell population using LLM.

    Args:
        query: Optional predefined query string
    """
    if not query:
        query = input("\nEnter query for table generation testing: ").strip()
    if not query:
        print("Error: No query provided. Exiting.")
        return

    print("\nTESTING TABLE GENERATION STAGE")
    print(f"Input Query: '{query}'\n")

    try:
        # Initialize ScholarQA with full pipeline setup
        retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
        paper_finder = PaperFinder(retriever=retriever)
        scholar_qa = ScholarQA(
            paper_finder=paper_finder,
            llm_model=CLAUDE_4_SONNET,
            state_mgr_client=LocalStateMgrClient("logs"),
            validate=False,  # Skip validation to avoid rate limits
        )

        # Stage 1-5: Get evidence through ScholarQA pipeline
        print(
            "Running prerequisite stages (query processing, retrieval and evidence collection)..."
        )

        # Step 0: Query preprocessing
        cost_args = CostReportingArgs(
            task_id="test_table_generation",
            user_id="test_user",
            description="Step 0: Query decomposition",
            model=CLAUDE_4_SONNET,
            msg_id="test_message",
        )
        llm_processed_query = scholar_qa.preprocess_query(query, cost_args)

        # Step 1: Paper retrieval
        snippet_srch_res, s2_srch_res = scholar_qa.find_relevant_papers(
            llm_processed_query.result
        )
        retrieved_candidates = snippet_srch_res + s2_srch_res
        if not retrieved_candidates:
            print("No relevant papers found in initial retrieval. Exiting.")
            return

        # Step 2: Reranking
        s2_srch_metadata = [
            {
                k: v
                for k, v in paper.items()
                if k == "corpus_id"
                or k in NUMERIC_META_FIELDS
                or k in CATEGORICAL_META_FIELDS
            }
            for paper in s2_srch_res
        ]
        reranked_df, paper_metadata = scholar_qa.rerank_and_aggregate(
            query,
            retrieved_candidates,
            {str(paper["corpus_id"]): paper for paper in s2_srch_metadata},
        )
        if reranked_df.empty:
            print("No relevant papers found after reranking. Exiting.")
            return

        # Step 3: Quote extraction
        per_paper_summaries = scholar_qa.step_select_quotes(
            query, reranked_df, cost_args
        )
        if not per_paper_summaries.result:
            print("No relevant quotes extracted. Exiting.")
            return

        # Step 4: Clustering and planning
        cluster_json = scholar_qa.step_clustering(
            query, per_paper_summaries.result, cost_args
        )
        plan_json = {
            f'{dim["name"]} ({dim["format"]})': dim["quotes"]
            for dim in cluster_json.result["dimensions"]
        }
        if not any([len(d) for d in plan_json.values()]):
            print("Planning step failed to cluster documents. Exiting.")
            return

        # Step 5: Extract inline citations
        per_paper_summaries_extd, quotes_metadata = scholar_qa.extract_quote_citations(
            reranked_df, per_paper_summaries.result, plan_json, paper_metadata
        )

        # Use these results for table generation
        evidence_result = cluster_json.result

        # Stage 6a: Generate column suggestions
        print("\nGENERATING TABLE COLUMNS")
        print("=" * 50)

        # Set up cost tracking
        cost_args = CostReportingArgs(
            task_id="test_table_generation",
            user_id="test_user",
            msg_id="test_message",
            description="Test Table Generation",
            model=CLAUDE_4_SONNET,
        )

        # Generate column suggestions
        attribute_result = generate_attribute_suggestions(
            query=query,
            evidence=evidence_result.result,
            n_attributes=5,
            model=CLAUDE_4_SONNET,
            llm_caller=CostAwareLLMCaller(),
            cost_args=cost_args,
        )

        # Show column generation results
        print("\nCOLUMN GENERATION RESULTS:")
        print(f"   Total Cost: ${attribute_result['cost'].get('cost_value', 0):.4f}")
        print(f"   Columns: {len(attribute_result.get('columns', []))}")

        # Stage 6b: Generate table
        print("\nGENERATING TABLE CELLS")
        print("=" * 50)

        # Set up table generator
        table_generator = TableGenerator(
            paper_finder=paper_finder,
            llm_caller=CostAwareLLMCaller(),
            max_threads=3,
        )

        # Generate table
        table_result, costs = table_generator.run_table_generation(
            thread_id="test",
            user_id="test_user",
            original_query=query,
            section_title="Main Approaches to Quantum Computing",
            corpus_ids=[x["corpusId"] for x in evidence_result.result],
            column_num=5,
            run_subselection=True,
            column_model=CLAUDE_4_SONNET,
            value_model=CLAUDE_4_SONNET,
        )

        # Show table structure
        print("\nTABLE GENERATION RESULTS:")
        print("\nTable Structure:")
        print(f"   Columns: {len(table_result.columns)}")
        print(f"   Rows: {len(table_result.rows)}")
        print(f"   Total Cells: {len(table_result.cells)}")

        total_cost = (
            evidence_result.tot_cost
            + attribute_result["cost"]["cost_value"]
            + sum(cost.get("cost_value", 0) for cost in costs["cell_cost"])
        )

        print("\nTABLE GENERATION COMPLETE")
        print(f"Total Pipeline Cost: ${total_cost:.4f}")

    except Exception as e:
        print(f"Error during table generation: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test ScholarQA Pipeline Stage 6: Table Generation"
    )
    parser.add_argument("--query", help="Research query to process")
    args = parser.parse_args()

    # Use managed virtual environment
    api_requirements = Path(api_dir) / "requirements.txt"
    reranker_requirements = Path(api_dir) / "reranker_requirements.txt"

    with managed_venv(__file__, [str(api_requirements), str(reranker_requirements)]):
        from dotenv import load_dotenv
        from scholarqa.llms.constants import CLAUDE_4_SONNET, CostReportingArgs
        from scholarqa.llms.litellm_helper import CostAwareLLMCaller
        from scholarqa.models import GeneratedSection, TaskResult
        from scholarqa.scholar_qa import ScholarQA
        from scholarqa.state_mgmt.local_state_mgr import LocalStateMgrClient
        from scholarqa.rag.retrieval import PaperFinder
        from scholarqa.rag.retriever_base import FullTextRetriever
        from scholarqa.table_generation.column_suggestion import (
            generate_attribute_suggestions,
        )
        from scholarqa.table_generation.table_generator import TableGenerator
        from scholarqa.utils import (
            get_paper_metadata,
            NUMERIC_META_FIELDS,
            CATEGORICAL_META_FIELDS,
            get_ref_author_str,
            make_int,
        )

        # Load environment variables from .env file
        load_dotenv(Path(project_root) / ".env")

        # Check for required environment variables
        if not os.getenv("S2_API_KEY"):
            sys.exit("Error: Missing S2_API_KEY in environment variables")

        test_table_generation(args.query)
