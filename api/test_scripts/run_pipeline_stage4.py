#!/usr/bin/env python3
"""
Exhaustive test for ScholarQA Pipeline Stage 4: Evidence Extraction (Quote Selection)
Shows all data and metadata returned by the evidence extraction stage for transparency
"""
import os
import sys
import warnings
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Suppress noisy runtime warnings (functional logs controlled by --quiet)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Setup
api_dir = str(Path(__file__).parent.parent)
project_root = str(Path(api_dir).parent)
if api_dir not in sys.path:
    sys.path.append(api_dir)

try:
    from dotenv import load_dotenv

    load_dotenv(Path(project_root) / ".env")
except ImportError:
    print("Warning: python-dotenv not available, skipping .env file loading")

if not os.getenv("S2_API_KEY"):
    print("Error: Missing S2_API_KEY in environment variables")
    sys.exit(1)

from scholarqa.preprocess.query_preprocessor import decompose_query
from scholarqa.rag.retriever_base import FullTextRetriever
from scholarqa.rag.retrieval import PaperFinder
from scholarqa.utils import get_paper_metadata
from scholarqa.llms.constants import CLAUDE_4_SONNET
from scholarqa.scholar_qa import ScholarQA
from scholarqa.llms.prompts import SYSTEM_PROMPT_QUOTE_PER_PAPER
from scholarqa.state_mgmt.local_state_mgr import LocalStateMgrClient


def test_evidence_extraction_stage(
    query: Optional[str] = None,
    max_results: int = 3,
    quiet: Optional[bool] = True,
):
    """Exhaustive test of evidence extraction stage - shows ALL data and metadata returned"""

    # Configure log suppression based on quiet flag
    if quiet:
        logging.getLogger("LiteLLM").setLevel(logging.ERROR)
        logging.getLogger("LiteLLM Proxy").setLevel(logging.ERROR)
        logging.getLogger("LiteLLM Router").setLevel(logging.ERROR)
        logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    # Input handling
    if not query:
        query = input("\nEnter query for evidence extraction testing: ").strip()
    if not query:
        print("Error: No query provided. Exiting.")
        return

    print("\nTESTING EVIDENCE EXTRACTION STAGE")
    print(f"Input Query: '{query}'")
    print("=" * 70)

    try:
        # PREREQUISITE: Run stages 1-3 to get the aggregated DataFrame
        print("\nPREREQUISITE STAGES (1-3): Getting Aggregated DataFrame")

        # Stage 1: Query Decomposition
        import contextlib
        import io

        if quiet:
            stderr_capture = io.StringIO()
            with contextlib.redirect_stderr(stderr_capture):
                decomposed_query, _ = decompose_query(
                    query=query, decomposer_llm_model=CLAUDE_4_SONNET
                )
        else:
            decomposed_query, _ = decompose_query(
                query=query, decomposer_llm_model=CLAUDE_4_SONNET
            )

        # Stage 2-3: Retrieval, Reranking & Aggregation
        retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
        paper_finder = PaperFinder(retriever=retriever)

        print("   Query decomposed and retriever configured")

        # Get raw retrieval results
        snippet_results = paper_finder.retrieve_passages(
            query=decomposed_query.rewritten_query, **decomposed_query.search_filters
        )
        search_api_results = []
        if decomposed_query.keyword_query:
            raw_results = paper_finder.retrieve_additional_papers(
                decomposed_query.keyword_query, **decomposed_query.search_filters
            )
            snippet_corpus_ids = {snippet["corpus_id"] for snippet in snippet_results}
            search_api_results = [
                item
                for item in raw_results
                if item["corpus_id"] not in snippet_corpus_ids
            ]

        # Combine and rerank
        all_retrieved_candidates = snippet_results + search_api_results
        reranked_candidates = paper_finder.rerank(query, all_retrieved_candidates)

        # Get paper metadata and aggregate
        all_corpus_ids = {item["corpus_id"] for item in reranked_candidates}
        paper_metadata = get_paper_metadata(all_corpus_ids)
        aggregated_df = paper_finder.aggregate_into_dataframe(
            reranked_candidates, paper_metadata
        )

        print(
            f"   Retrieved and aggregated: {len(aggregated_df)} papers ready for evidence extraction"
        )

        # STAGE 4: EVIDENCE EXTRACTION (Quote Selection)
        print("\nEVIDENCE EXTRACTION STAGE")
        print("=" * 50)

        # Initialize ScholarQA for evidence extraction
        logs_dir = "logs"  # Default logs directory
        state_mgr = LocalStateMgrClient(logs_dir)
        scholar_qa = ScholarQA(
            paper_finder=paper_finder,
            llm_model=CLAUDE_4_SONNET,
            state_mgr_client=state_mgr,
        )

        # Show input DataFrame structure
        print("\nSTEP 4A: INPUT DATAFRAME ANALYSIS")
        print(f"   Input Papers: {len(aggregated_df)} papers")
        print(f"   DataFrame Columns: {list(aggregated_df.columns)}")
        print(f"   Context Threshold: {paper_finder.context_threshold}")

        if not aggregated_df.empty:
            # Show relevance score distribution
            relevance_scores = (
                aggregated_df["relevance_judgement"].tolist()
                if "relevance_judgement" in aggregated_df.columns
                else []
            )
            if relevance_scores:
                print(
                    f"   Relevance Score Range: {min(relevance_scores):.3f} - {max(relevance_scores):.3f}"
                )

            # Show papers above threshold
            above_threshold = (
                aggregated_df[
                    aggregated_df["relevance_judgement"]
                    >= paper_finder.context_threshold
                ]
                if "relevance_judgement" in aggregated_df.columns
                else aggregated_df
            )
            print(f"   Papers Above Threshold: {len(above_threshold)}")

        # Show evidence extraction parameters
        print("\nSTEP 4B: EVIDENCE EXTRACTION PARAMETERS")
        print(f"   LLM Model: {CLAUDE_4_SONNET}")
        print("   System Prompt: Quote Per Paper (SYSTEM_PROMPT_QUOTE_PER_PAPER)")
        print(f"   Extraction Query: '{query}'")
        print("   Batch Processing: Multi-threaded LLM calls")

        # Extract quotes/evidence
        print("\nSTEP 4C: EXECUTING EVIDENCE EXTRACTION")
        print(f"   Processing {len(aggregated_df)} papers for quote extraction...")

        # Create cost reporting args for the evidence extraction
        from scholarqa.llms.constants import CostReportingArgs

        cost_args = CostReportingArgs(
            task_id="test_evidence_extraction",
            user_id="test_user",
            msg_id="test_message",
            description="Test Evidence Extraction",
            model=CLAUDE_4_SONNET,
        )

        # Suppress asyncio stderr noise during LLM calls
        import contextlib
        import io

        if quiet:
            _stderr_buf = io.StringIO()
            with contextlib.redirect_stderr(_stderr_buf):
                per_paper_summaries = scholar_qa.step_select_quotes(
                    query=query,
                    scored_df=aggregated_df,
                    cost_args=cost_args,
                    sys_prompt=SYSTEM_PROMPT_QUOTE_PER_PAPER,
                )
        else:
            per_paper_summaries = scholar_qa.step_select_quotes(
                query=query,
                scored_df=aggregated_df,
                cost_args=cost_args,
                sys_prompt=SYSTEM_PROMPT_QUOTE_PER_PAPER,
            )

        print("   Evidence extraction completed")
        print(f"   Total Cost: ${per_paper_summaries.tot_cost:.4f}")
        print(f"   Input Tokens: {per_paper_summaries.tokens.input}")
        print(f"   Output Tokens: {per_paper_summaries.tokens.output}")
        print(f"   Papers with Extracted Quotes: {len(per_paper_summaries.result)}")

        # RESULTS: Exhaustive display of evidence extraction stage output
        print("\nEXHAUSTIVE EVIDENCE EXTRACTION RESULTS")
        print("=" * 70)

        # Show extraction statistics
        print("\nEXTRACTION STATISTICS")
        if per_paper_summaries.result:
            print(f"   Total Papers with Quotes: {len(per_paper_summaries.result)}")

            # Calculate quote lengths
            quote_lengths = [
                len(quote) for quote in per_paper_summaries.result.values()
            ]
            if quote_lengths:
                print(
                    f"   Quote Length Range: {min(quote_lengths)} - {max(quote_lengths)} characters"
                )
                print(
                    f"   Average Quote Length: {sum(quote_lengths) / len(quote_lengths):.1f} characters"
                )

            # Show model usage breakdown
            print(f"   Models Used: {len(per_paper_summaries.models)} LLM calls")

            # Analyze reference strings
            ref_strings = list(per_paper_summaries.result.keys())
            corpus_ids_in_quotes = set()
            for ref_str in ref_strings:
                # Extract corpus ID from reference string [corpus_id | author | year | citations]
                try:
                    corpus_id = ref_str.split(" | ")[0][1:]  # Remove leading '['
                    corpus_ids_in_quotes.add(corpus_id)
                except:
                    pass

            print(f"   Unique Papers Referenced: {len(corpus_ids_in_quotes)}")

            # Show years distribution of papers with quotes
            years_with_quotes = []
            for ref_str in ref_strings:
                try:
                    year = ref_str.split(" | ")[2]
                    years_with_quotes.append(int(year))
                except:
                    pass

            if years_with_quotes:
                from collections import Counter

                year_dist = Counter(years_with_quotes).most_common(5)
                print(f"   Top Years in Extracted Quotes: {dict(year_dist)}")

        # Show detailed results for top papers
        print(
            f"\nTOP EXTRACTED EVIDENCE (Top {min(max_results, len(per_paper_summaries.result))})"
        )

        for i, (ref_string, quote) in enumerate(
            list(per_paper_summaries.result.items())[:max_results]
        ):
            print(f"\n   Evidence {i+1}")
            print(f"   Reference String: {ref_string}")

            # Parse reference string for details
            try:
                parts = ref_string.split(" | ")
                corpus_id = parts[0][1:]  # Remove leading '['
                author_info = parts[1]
                year = parts[2]
                citations = parts[3].split(": ")[1][:-1]  # Remove trailing ']'

                print(f"   Corpus ID: {corpus_id}")
                print(f"   Authors: {author_info}")
                print(f"   Year: {year}")
                print(f"   Citations: {citations}")
            except:
                print("   Warning: Could not parse reference string details")

            # Show quote details
            print(f"   Quote Length: {len(quote)} characters")
            print(f"   Quote Segments: {quote.count('...') + 1} parts")

            # Show quote content with formatting
            print("   EXTRACTED QUOTE:")
            quote_lines = quote.split("...")
            for j, segment in enumerate(quote_lines):
                segment = segment.strip()
                if segment:
                    print(
                        f"      Segment {j+1}: {segment[:200]}{'...' if len(segment) > 200 else ''}"
                    )

            # Check if corresponding paper is in aggregated_df for additional metadata
            try:
                matching_paper = aggregated_df[
                    aggregated_df["corpus_id"] == int(corpus_id)
                ]
                if not matching_paper.empty:
                    paper = matching_paper.iloc[0]
                    print(f"   Paper Title: {paper.get('title', 'N/A')}")
                    print(f"   Venue: {paper.get('venue', 'N/A')}")
                    print(
                        f"   Relevance Score: {paper.get('relevance_judgement', 'N/A'):.4f}"
                    )

                    # Show source sections if available
                    sentences = paper.get("sentences", [])
                    if sentences:
                        sections = set()
                        for sentence in sentences:
                            section = sentence.get("section_title", "unknown")
                            sections.add(section)
                        print(f"   Source Sections: {list(sections)}")

            except Exception as e:
                print(f"   Warning: Could not match with aggregated paper data: {e}")

        # Show extraction methodology details
        print("\nEXTRACTION METHODOLOGY DETAILS")
        print("   System Prompt Strategy: Extract exact text from paper content")
        print("   Target: Direct answers to user query from paper snippets")
        print("   Quote Format: Use '...' to indicate gaps between selected text")
        print(
            "   Citation Handling: Include all references contiguous with selected text"
        )
        print(
            "   Filtering: Papers returning 'None' or short quotes (<10 chars) are excluded"
        )
        print("   Processing: Parallel LLM calls for efficiency")

        # Show cost breakdown
        print("\nCOST ANALYSIS")
        print(f"   Total Cost: ${per_paper_summaries.tot_cost:.4f}")
        print("   Token Usage:")
        print(f"      Input Tokens: {per_paper_summaries.tokens.input:,}")
        print(f"      Output Tokens: {per_paper_summaries.tokens.output:,}")
        print(f"      Total Tokens: {per_paper_summaries.tokens.total:,}")

        if len(per_paper_summaries.result) > 0:
            cost_per_paper = per_paper_summaries.tot_cost / len(
                per_paper_summaries.result
            )
            print(f"   Average Cost per Paper with Quote: ${cost_per_paper:.4f}")

        print("\nEVIDENCE EXTRACTION STAGE COMPLETE")
        print(
            f"Final Output: {len(per_paper_summaries.result)} papers with extracted evidence ready for clustering stage"
        )

        return per_paper_summaries, aggregated_df

    except Exception as e:
        print(f"Error during evidence extraction: {e}")
        import traceback

        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Exhaustive test of ScholarQA Pipeline Stage 4: Evidence Extraction"
    )
    parser.add_argument("--query", type=str, help="Query to test (optional)")
    parser.add_argument(
        "--max-results", type=int, default=3, help="Max results to display (default: 3)"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--quiet",
        dest="quiet",
        action="store_true",
        help="Suppress asyncio/logging noise (default)",
    )
    group.add_argument(
        "--no-quiet",
        dest="quiet",
        action="store_false",
        help="Show asyncio/logging output",
    )
    parser.set_defaults(quiet=True)

    args = parser.parse_args()
    test_evidence_extraction_stage(args.query, args.max_results, args.quiet)
