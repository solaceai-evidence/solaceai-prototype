#!/usr/bin/env python3
"""
Exhaustive test for ScholarQA Pipeline Stage 2: Retrieval Process
Shows every argument, parameter, and result from the retrieval stage before reranking
"""
import os
import sys
import warnings
import logging
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


def test_retrieval_stage(query: Optional[str] = None, max_results: int = 3):
    """Exhaustive test of retrieval stage - shows ALL arguments and parameters"""

    # Input handling
    if not query:
        query = input("\nEnter query for retrieval testing: ").strip()
    if not query:
        print("Error: No query provided. Exiting.")
        return

    print("\nTESTING RETRIEVAL STAGE")
    print(f"Input Query: '{query}'")
    print("=" * 60)

    try:
        # STAGE 1: Query Decomposition (prerequisite)
        print("\n1) QUERY DECOMPOSITION")

        # Suppress async warnings during LLM call
        import contextlib
        import io

        # Capture stderr to suppress async warnings
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            decomposed_query, _ = decompose_query(
                query=query, decomposer_llm_model=CLAUDE_4_SONNET
            )

        print(f"   Rewritten Query: '{decomposed_query.rewritten_query}'")
        print(f"   Keyword Query: '{decomposed_query.keyword_query}'")
        print(f"   Search Filters: {decomposed_query.search_filters}")

        # STAGE 2: Retriever Setup
        print("\n2) RETRIEVER CONFIGURATION")
        retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
        paper_finder = PaperFinder(retriever=retriever)

        print(f"   Max Snippet Retrieval: {retriever.n_retrieval}")
        print(f"   Max Keyword Search: {retriever.n_keyword_srch}")
        print(f"   Context Threshold: {paper_finder.context_threshold}")
        print(f"   Rerank Limit: {paper_finder.n_rerank}")

        # STAGE 3: Snippet Retrieval (Full-text search)
        print("\n3) SNIPPET RETRIEVAL (Full-text Search)")
        print(f"   Query: '{decomposed_query.rewritten_query}'")
        print(f"   Filters Applied: {decomposed_query.search_filters}")

        # Note: The following line may show debug output from retriever_base.py
        snippet_results = paper_finder.retrieve_passages(
            query=decomposed_query.rewritten_query, **decomposed_query.search_filters
        )
        snippet_results = sorted(
            snippet_results, key=lambda x: x.get("score", 0), reverse=True
        )
        snippet_corpus_ids = {snippet["corpus_id"] for snippet in snippet_results}

        print(f"   Retrieved: {len(snippet_results)} snippets")
        if snippet_results:
            scores = [s.get("score", 0) for s in snippet_results]
            print(f"   Score Range: {min(scores):.3f} - {max(scores):.3f}")

        # STAGE 4: Keyword Search (Additional papers)
        print("\n4) KEYWORD SEARCH (Additional Papers)")
        search_api_results = []

        if decomposed_query.keyword_query:
            print(f"   Query: '{decomposed_query.keyword_query}'")
            print(f"   Filters Applied: {decomposed_query.search_filters}")

            raw_results = paper_finder.retrieve_additional_papers(
                decomposed_query.keyword_query, **decomposed_query.search_filters
            )
            search_api_results = [
                item
                for item in raw_results
                if item["corpus_id"] not in snippet_corpus_ids
            ]

            print(f"   Raw Results: {len(raw_results)} papers")
            print(f"   After Deduplication: {len(search_api_results)} papers")
        else:
            print("   Note: No keyword query generated")

        # STAGE 5: Metadata Retrieval
        print("\n5) METADATA RETRIEVAL")
        all_corpus_ids = snippet_corpus_ids.union(
            {item["corpus_id"] for item in search_api_results}
        )
        paper_metadata = get_paper_metadata(all_corpus_ids)
        print(f"   Fetched metadata for {len(paper_metadata)} papers")

        # RESULTS: Exhaustive display of all parameters
        print("\nEXHAUSTIVE RETRIEVAL RESULTS")
        print("=" * 60)

        # Show top snippets with ALL parameters
        print(f"\nSNIPPET RESULTS (Top {min(max_results, len(snippet_results))})")
        for i, snippet in enumerate(snippet_results[:max_results]):
            print(f"\n   Snippet {i+1} [Score: {snippet.get('score', 'N/A'):.4f}]")
            print(f"   Corpus ID: {snippet['corpus_id']}")
            print(f"   Title: {snippet.get('title', 'N/A')}")
            print(f"   Section: {snippet.get('section_title', 'N/A')}")
            print(f"   Source Type: {snippet.get('stype', 'N/A')}")
            print(f"   Char Offset: {snippet.get('char_start_offset', 'N/A')}")
            print(f"   Sentences: {len(snippet.get('sentence_offsets', []))}")
            print(f"   References: {len(snippet.get('ref_mentions', []))}")
            print(
                f"   Text ({len(snippet.get('text', ''))} chars): {snippet['text'][:150]}..."
            )

            # Show corresponding metadata
            corpus_id = snippet["corpus_id"]
            if corpus_id in paper_metadata:
                meta = paper_metadata[corpus_id]
                print(f"   Year: {meta.get('year', 'N/A')}")
                print(f"   Authors: {len(meta.get('authors', []))} authors")
                print(f"   Citations: {meta.get('citationCount', 'N/A')}")
                print(f"   Venue: {meta.get('venue', 'N/A')}")
                print(f"   Open Access: {meta.get('isOpenAccess', 'N/A')}")

        # Show keyword search results with ALL parameters
        if search_api_results:
            print(
                f"\nKEYWORD SEARCH RESULTS (Top {min(max_results, len(search_api_results))})"
            )
            for i, paper in enumerate(search_api_results[:max_results]):
                print(f"\n   Paper {i+1}")
                print(f"   Corpus ID: {paper['corpus_id']}")
                print(f"   Title: {paper.get('title', 'N/A')}")
                print(f"   Year: {paper.get('year', 'N/A')}")
                print(f"   Citations: {paper.get('citationCount', 'N/A')}")
                print(f"   Authors: {len(paper.get('authors', []))} authors")
                print(f"   Venue: {paper.get('venue', 'N/A')}")
                print(f"   Open Access: {paper.get('isOpenAccess', 'N/A')}")
                print(
                    f"   Abstract ({len(paper.get('abstract', ''))} chars): {paper.get('abstract', 'N/A')[:150]}..."
                )

        print("\nRETRIEVAL STAGE COMPLETE")
        print(
            f"Total Results: {len(snippet_results)} snippets + {len(search_api_results)} papers"
        )

        return snippet_results, search_api_results, paper_metadata

    except Exception as e:
        print(f"Error during retrieval: {e}")
        return None, None, None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Exhaustive test of ScholarQA Pipeline Stage 2: Retrieval Process"
    )
    parser.add_argument("--query", type=str, help="Query to test (optional)")
    parser.add_argument(
        "--max-results", type=int, default=3, help="Max results to display (default: 3)"
    )

    args = parser.parse_args()
    test_retrieval_stage(args.query, args.max_results)
