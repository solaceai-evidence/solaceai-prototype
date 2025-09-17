#!/usr/bin/env python3
"""
Exhaustive test for ScholarQA Pipeline Stage 5: Section Generation
Shows all parameters and decision points in section generation for transparency.
Displays details of Stage 1 (query decomposition) and Stage 4 (evidence extraction),
then provides comprehensive visibility into Stage 5 (section generation).
"""
import contextlib
import io
import os
import sys
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd
from scholarqa.llms.constants import CLAUDE_4_SONNET, CostReportingArgs
from scholarqa.llms.prompts import (
    PROMPT_ASSEMBLE_SUMMARY,
    SYSTEM_PROMPT_QUOTE_CLUSTER,
    SYSTEM_PROMPT_QUOTE_PER_PAPER,
)
from scholarqa.postprocess.json_output_utils import get_json_summary
from scholarqa.preprocess.query_preprocessor import decompose_query
from scholarqa.rag.retrieval import PaperFinder
from scholarqa.rag.retriever_base import FullTextRetriever
from scholarqa.scholar_qa import ScholarQA
from scholarqa.state_mgmt.local_state_mgr import LocalStateMgrClient

# Suppress noisy runtime warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Setup paths and environment
api_dir = str(Path(__file__).parent.parent)
sys.path.append(api_dir)

# Load environment variables
env_file = Path(api_dir).parent / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)
    except ImportError:
        pass

# Verify required environment variables
if not os.getenv("S2_API_KEY"):
    sys.exit("Error: Missing S2_API_KEY in environment variables")

from scholarqa.llms.constants import CLAUDE_4_SONNET, CostReportingArgs
from scholarqa.llms.prompts import (
    PROMPT_ASSEMBLE_NO_QUOTES_SUMMARY,
    PROMPT_ASSEMBLE_SUMMARY,
    SYSTEM_PROMPT_QUOTE_CLUSTER,
    SYSTEM_PROMPT_QUOTE_PER_PAPER,
)
from scholarqa.preprocess.query_preprocessor import decompose_query
from scholarqa.rag.retrieval import PaperFinder
from scholarqa.rag.retriever_base import FullTextRetriever
from scholarqa.scholar_qa import ScholarQA
from scholarqa.state_mgmt.local_state_mgr import LocalStateMgrClient


def test_section_generation_stage(query: Optional[str] = None, max_results: int = 2):
    """Exhaustive test of section generation stage - shows ALL data and parameters"""

    # Input handling
    if not query:
        query = input("\nEnter query for section generation testing: ").strip()
    if not query:
        print("Error: No query provided. Exiting.")
        return

    print("\nTESTING SECTION GENERATION STAGE")
    print(f"Input Query: '{query}'")
    print("=" * 70)

    try:
        # Initialize ScholarQA with full pipeline setup
        logs_dir = "logs"
        retriever = FullTextRetriever(n_retrieval=256, n_keyword_srch=20)
        paper_finder = PaperFinder(retriever=retriever)
        scholar_qa = ScholarQA(
            paper_finder=paper_finder,
            llm_model=CLAUDE_4_SONNET,
            state_mgr_client=LocalStateMgrClient(logs_dir),
        )

        # STAGE 1: Query Decomposition
        print("\nSTAGE 1: QUERY DECOMPOSITION")
        print("=" * 50)

        print("Running query decomposition...")
        decomposition_result, _ = decompose_query(query, CLAUDE_4_SONNET)

        print("\nDECOMPOSITION RESULTS:")
        print(f"   Original Query: {query}")
        print(f"   Rewritten Query: {decomposition_result.rewritten_query}")
        if decomposition_result.keyword_query:
            print(f"   Keyword Query: {decomposition_result.keyword_query}")
        if decomposition_result.search_filters:
            print(f"   Search Filters: {decomposition_result.search_filters}")

        # STAGES 2-3: Run retrieval and reranking (minimal output)
        print("\nRunning retrieval and reranking stages...")

        # Redirect output during intermediate stages
        _stderr_buf = io.StringIO()
        with contextlib.redirect_stderr(_stderr_buf):
            # Get papers through retrieval
            snippet_results = paper_finder.retrieve_passages(
                query=decomposition_result.rewritten_query,
                **decomposition_result.search_filters,
            )

            # Collect all candidates including keyword search results
            all_retrieved_candidates = list(snippet_results)
            if decomposition_result.keyword_query:
                raw_results = paper_finder.retrieve_additional_papers(
                    decomposition_result.keyword_query,
                    **decomposition_result.search_filters,
                )
                all_retrieved_candidates.extend(raw_results)

            # Build simplified paper metadata from candidates
            paper_metadata = {}
            for s in all_retrieved_candidates:
                if "corpus_id" in s:
                    corpus_id = s["corpus_id"]
                    if corpus_id not in paper_metadata:
                        paper_metadata[corpus_id] = {
                            "corpus_id": corpus_id,
                            "title": s["title"],
                            "abstract": s.get("text", "")[:500],  # First 500 chars
                            "year": s.get("year", ""),
                            "citationCount": 0,
                            "referenceCount": 0,
                            "influentialCitationCount": 0,
                            "venue": "",
                            "authors": [{"name": "Unknown Author"}],
                            "sentences": [],
                        }
                    paper_metadata[corpus_id]["sentences"].append(s)

            # Rerank candidates
            reranked_candidates = paper_finder.rerank(query, all_retrieved_candidates)
            print(f"   Total papers after reranking: {len(reranked_candidates)}")
            print(
                "   First reranked candidate:",
                reranked_candidates[0] if reranked_candidates else "No results",
            )

            if paper_metadata:
                # Create DataFrame with required schema
                df = pd.DataFrame(
                    [
                        {
                            "corpus_id": str(doc["corpus_id"]),
                            "corpusId": str(doc["corpus_id"]),
                            **paper_metadata[doc["corpus_id"]],
                            "relevance_judgement": doc["score"],
                        }
                        for doc in reranked_candidates
                        if doc["corpus_id"] in paper_metadata
                    ]
                )

                print("\nDEBUG - Initial DataFrame columns:", list(df.columns))
                print(
                    "\nDEBUG - First paper metadata:",
                    next(iter(paper_metadata.values())),
                )
                print(
                    "DEBUG - First aggregated candidate:",
                    reranked_candidates[0] if reranked_candidates else None,
                )

                papers_df = paper_finder.format_retrieval_response(
                    df.to_dict("records")
                )

        print("   Retrieved and reranked papers successfully.")
        print(f"   Total papers in pipeline: {len(papers_df)}")

        # STAGE 4: Evidence Extraction
        print("\nSTAGE 4: EVIDENCE EXTRACTION")
        print("=" * 50)

        # Set up cost tracking for evidence extraction
        cost_args_extraction = CostReportingArgs(
            task_id="test_extraction",
            user_id="test_user",
            msg_id="test_message",
            description="Test Evidence Extraction",
            model=CLAUDE_4_SONNET,
        )

        print("Extracting evidence from papers...")
        evidence_result = scholar_qa.step_select_quotes(
            query=query,
            scored_df=papers_df,
            cost_args=cost_args_extraction,
            sys_prompt=SYSTEM_PROMPT_QUOTE_PER_PAPER,
        )

        print("\nEVIDENCE EXTRACTION RESULTS:")
        print(f"   Total Papers with Quotes: {len(evidence_result.result)}")
        print(f"   Total Cost: ${evidence_result.tot_cost:.4f}")
        print(f"   Input Tokens: {evidence_result.tokens.input:,}")
        print(f"   Output Tokens: {evidence_result.tokens.output:,}")
        print(f"   Total Tokens: {evidence_result.tokens.total:,}")

        # Show sample quotes
        if evidence_result.result and len(evidence_result.result) > 0:
            print("\nSample Quotes (first 2 papers):")
            for ref_string, quote in list(evidence_result.result.items())[:2]:
                print(f"\n   Paper: {ref_string}")
                preview = quote[:200] + "..." if len(quote) > 200 else quote
                print(f"   Quote: {preview}")

        # STAGE 5: SECTION GENERATION
        print("\nSECTION GENERATION PARAMETERS")
        print("=" * 50)

        # Show section generation config
        print("\nSTEP 5A: SYSTEM CONFIGURATION")
        print("   Model: CLAUDE_4_SONNET")
        print("   Prompts Used:")
        print("      - SYSTEM_PROMPT_QUOTE_CLUSTER for theme grouping")
        print("      - PROMPT_ASSEMBLE_SUMMARY for section writing")
        print(f"   Evidence Papers: {len(evidence_result.result)}")
        print("   Quote Grouping: By section theme and relevance")

        # Show section generation parameters
        print("\nSTEP 5B: GENERATION PARAMETERS")
        print("   Maximum Output Tokens:", os.getenv("RATE_LIMIT_OTPM", 4096 * 4))
        print("   Pipeline Workers:", os.getenv("MAX_LLM_WORKERS", 20))
        print("   Evidence Selection: By relevance score and section coverage")

        # Create cost reporting args
        cost_args = CostReportingArgs(
            task_id="test_section_generation",
            user_id="test_user",
            msg_id="test_message",
            description="Test Section Generation",
            model=CLAUDE_4_SONNET,
        )

        # Step 2: Cluster quotes
        print("\nSTEP 5B: CLUSTERING QUOTES")
        cluster_result = scholar_qa.step_clustering(
            query=query,
            per_paper_summaries=evidence_result.result,
            cost_args=cost_args,
            sys_prompt=SYSTEM_PROMPT_QUOTE_CLUSTER,
        )

        # Get plan from clustering
        plan_json = {
            f'{dim["name"]} ({dim["format"]})': dim["quotes"]
            for dim in cluster_result[0]["dimensions"]
        }

        # Show clustering results
        print("\nCLUSTERING RESULTS:")
        print(f"   Number of Dimensions: {len(plan_json)}")
        for title, quotes in plan_json.items():
            print(f"   {title}: {len(quotes)} quotes")

        # Step 3: Generate sections
        print("\nSTEP 5C: GENERATING SECTIONS")

        # Extract quotes metadata
        per_paper_summaries_extd, quotes_metadata = scholar_qa.extract_quote_citations(
            papers_df, evidence_result.result, plan_json, paper_metadata
        )

        # Generate sections using iterative summary
        # Set up section generation
        section_generator = scholar_qa.generate_iterative_summary(
            query=query,
            per_paper_summaries_extd=per_paper_summaries_extd,
            plan=plan_json,
            sys_prompt=PROMPT_ASSEMBLE_SUMMARY,
            cost_args=cost_args,
        )

        # Generate sections iteratively
        generated_sections = []
        total_tokens = {"input": 0, "output": 0, "total": 0}
        total_cost = 0

        print("\nGENERATING SECTIONS ITERATIVELY:")
        try:
            for idx, result in enumerate(section_generator, 1):
                if result is None:
                    print(f"   Section {idx} generation failed")
                    continue

                print(f"   Section {idx} generated successfully")
                # Update totals
                total_tokens = {
                    k: total_tokens[k] + getattr(result.tokens, k) for k in total_tokens
                }
                total_cost += result.tot_cost

                # Parse section JSON and store
                section_json = get_json_summary(
                    scholar_qa.multi_step_pipeline.llm_model,
                    [result.content],
                    per_paper_summaries_extd,
                    paper_metadata,
                    {},
                    True,
                )[0]
                generated_sections.append(
                    scholar_qa.get_gen_sections_from_json(section_json)
                )
        except StopIteration:
            print("Section generation completed")
        except Exception as e:
            print(f"Error during section generation: {e}")
            raise e

        # Show generation results
        print("\nSECTION GENERATION RESULTS")
        print("=" * 70)

        if not generated_sections:
            print("No sections were generated.")
            return None

        def preview_text(text, limit=200):
            """Helper to create preview of long text"""
            return f"{text[:limit]}..." if len(text) > limit else text

        # Section structure and content
        print("\nSECTION STRUCTURE")
        for i, section in enumerate(generated_sections, 1):
            print(f"\nSECTION {i}")
            print(f"   Title: {section.title}")
            print(f"   Word Count: {len(section.text.split())}")
            print(f"   Citations: {len(section.citations)}")
            if section.citations:
                print("   Referenced Papers:")
                print("      - " + "\n      - ".join(section.citations))
            print("   Content Preview:")
            for line in preview_text(section.text).split("\n"):
                print(f"      {line}")

        # Analysis
        print("\nSECTION GENERATION ANALYSIS")
        n_sections = len(generated_sections)
        print(f"   Total Sections: {n_sections}")

        # Calculate averages
        word_counts = [len(s.text.split()) for s in generated_sections]
        citation_counts = [len(s.citations) for s in generated_sections]
        print(f"   Average Words per Section: {sum(word_counts) / n_sections:.1f}")
        print(
            f"   Average Citations per Section: {sum(citation_counts) / n_sections:.1f}"
        )

        # Citation analysis
        papers_per_section = {
            section.title: set(section.citations) for section in generated_sections
        }
        print("\nPAPER USAGE ANALYSIS")
        print("   Papers Cited by Section:")
        for title, papers in papers_per_section.items():
            print(f"      {title}: {len(papers)} papers")

        # Show cost analysis
        print("\nCOST ANALYSIS")
        print(f"   Total Cost: ${total_cost:.4f}")
        print("   Token Usage:")
        print(f"      Input Tokens: {total_tokens['input']:,}")
        print(f"      Output Tokens: {total_tokens['output']:,}")
        print(f"      Total Tokens: {total_tokens['total']:,}")

        if generated_sections:
            cost_per_section = total_cost / len(generated_sections)
            print(f"   Average Cost per Section: ${cost_per_section:.4f}")

        print("\nSECTION GENERATION STAGE COMPLETE")
        print(f"Final Output: {len(generated_sections)} sections generated")

        # Return a TaskResult-like object
        class Result:
            def __init__(self, result, tot_cost, tokens):
                self.result = result
                self.tot_cost = tot_cost
                self.tokens = type(
                    "Tokens",
                    (),
                    {
                        "input": tokens["input"],
                        "output": tokens["output"],
                        "total": tokens["total"],
                    },
                )()

        return Result(generated_sections, total_cost, total_tokens)

    except Exception as e:
        print(f"Error during section generation: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test the ScholarQA Pipeline's section generation stage",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--query", type=str, help="Research query to process")
    parser.add_argument(
        "--max-results", type=int, default=2, help="Maximum number of papers to use"
    )

    test_section_generation_stage(**vars(parser.parse_args()))
