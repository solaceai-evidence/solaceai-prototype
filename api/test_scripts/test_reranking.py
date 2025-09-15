#!/usr/bin/env python3
"""
Exhaustive test for ScholarQA Pipeline Stage 3: Reranking and Aggregation
Shows all data and metadata returned by the reranking stage for transparency
"""
import os
import sys
import warnings
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

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

try:
    from dotenv import load_dotenv

    load_dotenv(Path(project_root) / ".env")
except ImportError:
    print("⚠️  dotenv not available, skipping .env file loading")

if not os.getenv("S2_API_KEY"):
    print("❌ Missing S2_API_KEY in environment variables")
    sys.exit(1)

from scholarqa.preprocess.query_preprocessor import decompose_query
from scholarqa.rag.retriever_base import FullTextRetriever
from scholarqa.rag.retrieval import PaperFinder
from scholarqa.utils import get_paper_metadata
from scholarqa.llms.constants import CLAUDE_4_SONNET


def test_reranking_stage(query: Optional[str] = None, max_results: int = 3):
    """Exhaustive test of reranking stage - shows ALL data and metadata returned"""

    # Input handling
    if not query:
        query = input("\nEnter query for reranking testing: ").strip()
    if not query:
        print("❌ No query provided. Exiting.")
        return

    print(f"\n🔄 TESTING RERANKING & AGGREGATION STAGE")
    print(f"📝 Input Query: '{query}'")
    print("=" * 70)

    try:
        # PREREQUISITE: Run retrieval stages first
        print("\n📋 PREREQUISITE STAGES (1-2): Retrieval Process")

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

        print(f"   ✓ Query decomposed and retriever configured")

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
            f"   ✓ Retrieved {len(snippet_results)} snippets + {len(search_api_results)} papers"
        )
        print(f"   ✓ Fetched metadata for {len(paper_metadata)} papers")

        # STAGE 3: RERANKING AND AGGREGATION
        print(f"\n3️⃣ RERANKING & AGGREGATION STAGE")
        print("=" * 50)

        # Step 3a: Reranking
        print(f"\n🎯 STEP 3A: RERANKING")
        print(f"   🔍 Rerank Query: '{query}'")
        print(f"   📊 Input Candidates: {len(all_retrieved_candidates)} items")
        print(f"   🎛️ Rerank Method: {type(paper_finder).__name__}")
        print(f"   🎚️ Rerank Limit: {paper_finder.n_rerank}")

        reranked_candidates = paper_finder.rerank(query, all_retrieved_candidates)
        print(f"   ✅ Reranked Candidates: {len(reranked_candidates)} items")

        # Show reranking score changes
        if reranked_candidates:
            rerank_scores = [
                item.get("rerank_score", item.get("score", 0))
                for item in reranked_candidates
            ]
            if rerank_scores:
                print(
                    f"   📈 Score Range After Reranking: {min(rerank_scores):.3f} - {max(rerank_scores):.3f}"
                )

        # Step 3b: Aggregation to paper level
        print(f"\n📊 STEP 3B: AGGREGATION TO PAPER LEVEL")
        print(f"   🔧 Context Threshold: {paper_finder.context_threshold}")
        print(f"   📝 Input: {len(reranked_candidates)} passages")

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
            print(f"   🔄 Fetched additional metadata for {len(missing_ids)} papers")

        # Perform aggregation
        aggregated_df = paper_finder.aggregate_into_dataframe(
            reranked_candidates, final_paper_metadata
        )

        print(f"   ✅ Aggregated DataFrame: {len(aggregated_df)} papers")
        if not aggregated_df.empty:
            relevance_scores = (
                aggregated_df["relevance_judgement"].tolist()
                if "relevance_judgement" in aggregated_df.columns
                else []
            )
            if relevance_scores:
                print(
                    f"   📈 Relevance Score Range: {min(relevance_scores):.3f} - {max(relevance_scores):.3f}"
                )

        # RESULTS: Exhaustive display of reranking stage output
        print(f"\n📋 EXHAUSTIVE RERANKING STAGE RESULTS")
        print("=" * 70)

        # Show DataFrame structure and columns
        print(f"\n📊 AGGREGATED DATAFRAME STRUCTURE")
        print(
            f"   📏 Shape: {aggregated_df.shape[0]} rows x {aggregated_df.shape[1]} columns"
        )
        if not aggregated_df.empty:
            print(f"   📋 Columns: {list(aggregated_df.columns)}")
            print(f"   🔢 Data Types:")
            for col, dtype in aggregated_df.dtypes.items():
                print(f"      {col}: {dtype}")

        # Show top aggregated papers with ALL metadata
        print(
            f"\n📄 TOP AGGREGATED PAPERS (Top {min(max_results, len(aggregated_df))})"
        )

        for i, (idx, paper) in enumerate(aggregated_df.head(max_results).iterrows()):
            print(
                f"\n   📋 Paper {i+1} [Relevance: {paper.get('relevance_judgement', 'N/A'):.4f}]"
            )
            print(f"   📎 Corpus ID: {paper.get('corpus_id', 'N/A')}")
            print(f"   📰 Title: {paper.get('title', 'N/A')}")
            print(f"   📊 Year: {paper.get('year', 'N/A')}")
            print(f"   👥 Authors: {len(paper.get('authors', []))} authors")
            if paper.get("authors") and len(paper["authors"]) > 0:
                author_names = [a.get("name", "Unknown") for a in paper["authors"][:3]]
                print(f"   ✍️ Author Names: {', '.join(author_names)}")
            print(f"   📈 Citations: {paper.get('citation_count', 'N/A')}")
            print(f"   📚 References: {paper.get('reference_count', 'N/A')}")
            print(
                f"   🌟 Influential Citations: {paper.get('influential_citation_count', 'N/A')}"
            )
            print(f"   🏛️ Venue: {paper.get('venue', 'N/A')}")
            print(f"   🔓 Open Access: {paper.get('isOpenAccess', 'N/A')}")

            # Show aggregated sentences information
            sentences = paper.get("sentences", [])
            print(f"   📝 Aggregated Sentences: {len(sentences)} passages")

            if sentences:
                sections = {}
                for sentence in sentences:
                    section = sentence.get("section_title", "unknown")
                    sections[section] = sections.get(section, 0) + 1
                print(f"   📑 Section Distribution: {dict(sections)}")

                # Show snippet scores within this paper
                snippet_scores = [
                    s.get("rerank_score", s.get("score", 0)) for s in sentences
                ]
                if snippet_scores:
                    print(
                        f"   📊 Snippet Score Range: {min(snippet_scores):.3f} - {max(snippet_scores):.3f}"
                    )

            # Show formatted content
            if "relevance_judgment_input_expanded" in paper:
                content_length = len(str(paper["relevance_judgment_input_expanded"]))
                print(f"   📄 Formatted Content: {content_length} characters")
                # Show preview of formatted content
                content_preview = str(paper["relevance_judgment_input_expanded"])[:200]
                print(
                    f"   👁️ Content Preview: {content_preview.replace(chr(10), ' ')}..."
                )

            if "reference_string" in paper:
                print(f"   📖 Reference String: {paper['reference_string']}")

            # Show abstract
            abstract = paper.get("abstract", "")
            if abstract:
                print(f"   📜 Abstract ({len(abstract)} chars): {abstract[:150]}...")

        # Show aggregation statistics
        print(f"\n📊 AGGREGATION STATISTICS")
        if not aggregated_df.empty:
            print(f"   📏 Total Papers After Aggregation: {len(aggregated_df)}")
            print(
                f"   🎯 Papers Above Context Threshold: {len(aggregated_df[aggregated_df['relevance_judgement'] >= paper_finder.context_threshold])}"
            )

            # Show distribution of papers by year
            if "year" in aggregated_df.columns:
                year_dist = aggregated_df["year"].value_counts().head(5)
                print(f"   📅 Top Years: {dict(year_dist)}")

            # Show venue distribution
            if "venue" in aggregated_df.columns:
                venue_dist = aggregated_df["venue"].value_counts().head(3)
                print(f"   🏛️ Top Venues: {dict(venue_dist)}")

        print(f"\n✅ RERANKING & AGGREGATION STAGE COMPLETE")
        print(
            f"📊 Final Output: DataFrame with {len(aggregated_df)} papers ready for next stage"
        )

        return aggregated_df, final_paper_metadata, reranked_candidates

    except Exception as e:
        print(f"❌ Error during reranking: {e}")
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
    test_reranking_stage(args.query, args.max_results)
