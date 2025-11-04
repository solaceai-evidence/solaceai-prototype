#!/usr/bin/env python3
"""
Test for ScholarQA Pipeline Stage 3: Reranking and Aggregation
Shows all data and metadata returned by the reranking stage for transparency
"""
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Optional

# Suppress warnings and async logging issues
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("LiteLLM Proxy").setLevel(logging.ERROR)
logging.getLogger("LiteLLM Router").setLevel(logging.ERROR)

# Setup
api_dir = str(Path(__file__).parent.parent)
project_root = str(Path(api_dir).parent)
if api_dir not in sys.path:
    sys.path.append(api_dir)

# Load environment variables from .env file (no external dependencies needed)
env_file = Path(project_root) / ".env"
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

from solaceai.llms.constants import CLAUDE_4_SONNET
from solaceai.preprocess.query_preprocessor import decompose_query
from solaceai.rag.retrieval import PaperFinder
from solaceai.rag.retriever_base import FullTextRetriever
from solaceai.utils import get_paper_metadata


def run_reranking_stage3(query: Optional[str] = None, max_results: int = 3):
    """Exhaustive test of reranking stage - shows ALL data and metadata returned"""

    # Input handling
    if not query:
        print("\nEnter query for reranking testing:")
        print("(Press Enter without typing to use default query)")
        query = input("Query: ").strip()
    if not query:
        # Use default query if none provided
        query = "how can we improve mental health outcomes and reduce substance misuse among displaced communities in Ethiopia"
        print(f"\nUsing default query: {query}")

    print("\nTESTING RERANKING & AGGREGATION STAGE")
    print(f"Input Query: '{query}'")
    print("=" * 70)

    print("\nNOTE: Stage 3 uses no LLM prompts")
    print("   This stage performs pure algorithmic reranking and aggregation")
    print("   LLM was only used in Stage 1 (QUERY_DECOMPOSER_PROMPT)")

    try:
        # PREREQUISITE: Run retrieval stages first
        print("\nPREREQUISITE STAGES (1-2): Retrieval Process")

        # Stage 1: Query Decomposition
        import contextlib
        import io

        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            decomposed_query, _ = decompose_query(
                query=query, decomposer_llm_model=CLAUDE_4_SONNET
            )

        # Stage 2: Retrieval Setup and Execution
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

        # Combine all retrieved candidates
        all_retrieved_candidates = snippet_results + search_api_results
        all_corpus_ids = {item["corpus_id"] for item in all_retrieved_candidates}
        paper_metadata = get_paper_metadata(all_corpus_ids)

        print(
            f"   Retrieved {len(snippet_results)} snippets + {len(search_api_results)} papers"
        )
        print(f"   Fetched metadata for {len(paper_metadata)} papers")

        # STAGE 3: RERANKING AND AGGREGATION
        print("\nRERANKING & AGGREGATION STAGE")
        print("=" * 50)

        # Step 3a: Reranking
        print("\nSTEP 3A: RERANKING")
        print(f"   Rerank Query: '{query}'")
        print(f"   Input Candidates: {len(all_retrieved_candidates)} items")
        print(f"   Rerank Method: {type(paper_finder).__name__}")
        print(f"   Rerank Limit: {paper_finder.n_rerank}")

        reranked_candidates = paper_finder.rerank(query, all_retrieved_candidates)
        print(f"   Reranked Candidates: {len(reranked_candidates)} items")

        # Show reranking score changes
        if reranked_candidates:
            rerank_scores = [
                item.get("rerank_score", item.get("score", 0))
                for item in reranked_candidates
            ]
            if rerank_scores:
                print(
                    f"   Score Range After Reranking: {min(rerank_scores):.3f} - {max(rerank_scores):.3f}"
                )

        # Step 3b: Aggregation to paper level
        print("\nSTEP 3B: AGGREGATION TO PAPER LEVEL")
        print(f"   Context Threshold: {paper_finder.context_threshold}")
        print(f"   Input: {len(reranked_candidates)} passages")

        # Get additional metadata if needed
        final_paper_metadata = paper_metadata.copy()
        missing_ids = {
            snippet["corpus_id"]
            for snippet in reranked_candidates
            if snippet["corpus_id"] not in final_paper_metadata
        }
        if missing_ids:
            additional_metadata = get_paper_metadata(missing_ids)
            final_paper_metadata.update(additional_metadata)
            print(f"   Fetched additional metadata for {len(missing_ids)} papers")

        # Perform aggregation
        aggregated_df = paper_finder.aggregate_into_dataframe(
            reranked_candidates, final_paper_metadata
        )

        print(f"   Aggregated DataFrame: {len(aggregated_df)} papers")
        if not aggregated_df.empty:
            relevance_scores = (
                aggregated_df["relevance_judgement"].tolist()
                if "relevance_judgement" in aggregated_df.columns
                else []
            )
            if relevance_scores:
                print(
                    f"   Relevance Score Range: {min(relevance_scores):.3f} - {max(relevance_scores):.3f}"
                )

        # RESULTS: Exhaustive display of reranking stage output
        print("\nEXHAUSTIVE RERANKING STAGE RESULTS")
        print("=" * 70)

        # Show DataFrame structure and columns
        print("\nAGGREGATED DATAFRAME STRUCTURE")
        print(
            f"   Shape: {aggregated_df.shape[0]} rows x {aggregated_df.shape[1]} columns"
        )
        if not aggregated_df.empty:
            print(f"   Columns: {list(aggregated_df.columns)}")
            print("   Data Types:")
            for col, dtype in aggregated_df.dtypes.items():
                print(f"      {col}: {dtype}")

        # Explain key aggregated fields
        print("\nAGGREGATED FIELD DESCRIPTIONS")
        print("=" * 70)
        print("Understanding the aggregated data (paper-level view):\n")

        field_descriptions = {
            "corpus_id": "Unique identifier for the paper",
            "title": "Full title of the research paper",
            "relevance_judgement": (
                "Aggregated relevance score (0-1) based on all retrieved passages from this paper"
            ),
            "sentences": "List of all retrieved passages/snippets from this paper",
            "reference_string": (
                "Formatted citation string for this paper [ID | Authors | Year | Citations]"
            ),
            "relevance_judgment_input_expanded": (
                "Formatted content combining title, abstract, and retrieved passages for LLM processing"
            ),
            "year": "Publication year",
            "authors": "List of paper authors with metadata",
            "citation_count": "Number of times this paper has been cited",
            "influential_citation_count": "Number of highly influential citations",
            "venue": "Publication venue (journal/conference name)",
            "abstract": "Paper abstract text",
            "isOpenAccess": "Whether the paper is freely available",
        }

        for field, description in field_descriptions.items():
            print(f"  {field:35} → {description}")

        print(f"\n{'='*70}")
        print("KEY CONCEPT: Aggregation combines multiple passages from the same paper")
        print("into a single paper-level record with an aggregated relevance score.")
        print(f"{'='*70}")

        # Show top aggregated papers with ALL metadata
        print(f"\nTOP AGGREGATED PAPERS (Top {min(max_results, len(aggregated_df))})")

        for i, (idx, paper) in enumerate(aggregated_df.head(max_results).iterrows()):
            print(
                f"\n   Paper {i+1} [Relevance: {paper.get('relevance_judgement', 'N/A'):.4f}]"
            )
            print(f"   Corpus ID: {paper.get('corpus_id', 'N/A')}")
            print(f"   Title: {paper.get('title', 'N/A')}")
            print(f"   Year: {paper.get('year', 'N/A')}")
            print(f"   Authors: {len(paper.get('authors', []))} authors")
            if paper.get("authors") and len(paper["authors"]) > 0:
                author_names = [a.get("name", "Unknown") for a in paper["authors"][:3]]
                print(f"   Author Names: {', '.join(author_names)}")
            print(f"   Citations: {paper.get('citation_count', 'N/A')}")
            print(f"   References: {paper.get('reference_count', 'N/A')}")
            print(
                f"   Influential Citations: {paper.get('influential_citation_count', 'N/A')}"
            )
            print(f"   Venue: {paper.get('venue', 'N/A')}")
            print(f"   Open Access: {paper.get('isOpenAccess', 'N/A')}")

            # Show aggregated sentences information
            sentences = paper.get("sentences", [])
            print(f"   Aggregated Sentences: {len(sentences)} passages")

            if sentences:
                sections: dict[str, int] = {}
                for sentence in sentences:
                    section = sentence.get("section_title", "unknown")
                    sections[section] = sections.get(section, 0) + 1
                print(f"   Section Distribution: {dict(sections)}")

                # Show snippet scores within this paper
                snippet_scores = [
                    s.get("rerank_score", s.get("score", 0)) for s in sentences
                ]
                if snippet_scores:
                    print(
                        f"   Snippet Score Range: {min(snippet_scores):.3f} - {max(snippet_scores):.3f}"
                    )

            # Show formatted content
            if "relevance_judgment_input_expanded" in paper:
                content_length = len(str(paper["relevance_judgment_input_expanded"]))
                print(f"   Formatted Content: {content_length} characters")
                # Show preview of formatted content
                content_preview = str(paper["relevance_judgment_input_expanded"])[:200]
                print(f"   Content Preview: {content_preview.replace(chr(10), ' ')}...")

            if "reference_string" in paper:
                print(f"   Reference String: {paper['reference_string']}")

            # Show abstract
            abstract = paper.get("abstract", "")
            if abstract:
                print(f"   Abstract ({len(abstract)} chars): {abstract[:150]}...")

        # Show aggregation statistics
        print("\nAGGREGATION STATISTICS")
        if not aggregated_df.empty:
            print(f"   Total Papers After Aggregation: {len(aggregated_df)}")
            print(
                f"   Papers Above Context Threshold: {len(aggregated_df[aggregated_df['relevance_judgement'] >= paper_finder.context_threshold])}"
            )

            # Show distribution of papers by year
            if "year" in aggregated_df.columns:
                year_dist = aggregated_df["year"].value_counts().head(5)
                print(f"   Top Years: {dict(year_dist)}")

            # Show venue distribution
            if "venue" in aggregated_df.columns:
                venue_dist = aggregated_df["venue"].value_counts().head(3)
                print(f"   Top Venues: {dict(venue_dist)}")

        print("\nRERANKING & AGGREGATION STAGE COMPLETE")
        print(
            f"Final Output: DataFrame with {len(aggregated_df)} papers ready for next stage"
        )

        return aggregated_df, final_paper_metadata, reranked_candidates

    except Exception as e:
        print(f"Error during reranking: {e}")
        import traceback

        traceback.print_exc()
        return None, None, None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Exhaustive test of ScholarQA Pipeline Stage 3: Reranking & Aggregation"
    )
    parser.add_argument("--query", type=str, help="Query to test (optional)")
    parser.add_argument(
        "--max-results", type=int, default=3, help="Max results to display (default: 3)"
    )

    args = parser.parse_args()
    run_reranking_stage3(args.query, args.max_results)
