#!/usr/bin/env python3
"""
Pipeline Stage 2: Paper Retrieval Process

This script demonstrates the retrieval workflow:
1. Query Decomposition - Parses user query and extracts search filters
2. Paper Retrieval - Finds relevant papers using semantic and keyword search
3. Results Processing - Deduplicates and presents top results

Prerequisites:
- Install solaceai package: cd .. && pip3 install -e .
- Create .env file in project root with: S2_API_KEY=your_key
"""
import argparse
import os
import sys
from pathlib import Path

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
api_dir = project_root / "api"

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

# Import solaceai modules
from solaceai.llms.constants import CLAUDE_4_SONNET
from solaceai.preprocess.query_preprocessor import decompose_query
from solaceai.rag.retrieval import PaperFinder
from solaceai.rag.retriever_base import FullTextRetriever
from solaceai.solace_ai import SolaceAI


def run_retrieval_pipeline(query: str, max_results: int = 5):
    """
    Run the complete retrieval pipeline: decompose query, retrieve papers, display results
    """
    print(f"\n{'='*70}")
    print("PIPELINE STAGE 2: RETRIEVAL PROCESS")
    print(f"{'='*70}")
    print(f"\nOriginal Query: {query}")

    # Step 1: Query Decomposition
    print(f"\n{'='*50}")
    print("STEP 1: QUERY DECOMPOSITION")
    print(f"{'='*50}")
    print("\nLLM Prompt: QUERY_DECOMPOSER_PROMPT (from solaceai.llms.prompts)")

    decomposed_query, _ = decompose_query(query, CLAUDE_4_SONNET)

    print(f"Rewritten Query: {decomposed_query.rewritten_query}")
    print(f"Keyword Query: {decomposed_query.keyword_query}")

    # Display search parameters
    print("\nSearch Parameters Analysis:")
    print("-" * 40)

    all_params = {
        "year": "Time range filter (earliest_search_year-latest_search_year)",
        "venue": "Publication venue filter (conferences, journals)",
        "fieldsOfStudy": "Academic field filter (Computer Science, etc.)",
        "authors": "Author name filter (comma-separated)",
        "limit": "Maximum number of results to retrieve",
    }

    search_filters = getattr(decomposed_query, "search_filters", {})

    print("Available Parameters:")
    for param, description in all_params.items():
        value = search_filters.get(param, "Not specified")
        status = (
            "✓ USED"
            if (param in search_filters and search_filters[param])
            else "○ Available"
        )
        print(f"  {status:12} {param:15} → {value}")
        print(f"               {' ' * 15}   ({description})")

    # Step 2: Paper Retrieval
    print(f"\n{'='*50}")
    print("STEP 2: PAPER RETRIEVAL")
    print(f"{'='*50}")

    # Initialize retrieval components
    retriever = FullTextRetriever()
    paper_finder = PaperFinder(retriever=retriever)
    qa_system = SolaceAI(paper_finder=paper_finder)

    print(f"Running retrieval with limit={max_results}...")

    # Retrieve papers using the SolaceAI system
    snippet_results, search_api_results = qa_system.find_relevant_papers(
        decomposed_query, limit=max_results
    )

    print(f"Retrieved {len(snippet_results)} passage results")
    print(f"Retrieved {len(search_api_results)} additional papers from keyword search")

    # Step 3: Results Processing
    print(f"\n{'='*50}")
    print("STEP 3: RESULTS")
    print(f"{'='*50}")

    # Combine results and deduplicate by corpus_id
    all_results = snippet_results + search_api_results
    papers_by_id = {}
    for item in all_results:
        corpus_id = item.get("corpus_id")
        if corpus_id and corpus_id not in papers_by_id:
            papers_by_id[corpus_id] = item

    unique_papers = list(papers_by_id.values())
    print(f"Total unique papers: {len(unique_papers)}")

    # Display comprehensive results with all available fields
    print(f"\nTop {min(max_results, len(unique_papers))} Results:")
    print("=" * 80)

    for i, paper in enumerate(unique_papers[:max_results], 1):
        print(f"\nPAPER {i}")
        print("-" * 20)

        # Core identification
        corpus_id = paper.get("corpus_id", "N/A")
        title = paper.get("title", "No title available")
        print(f"Corpus ID: {corpus_id}")
        print(f"Title: {title}")

        # Publication details
        year = paper.get("year", "Unknown")
        venue = paper.get("venue", "Unknown")
        print(f"Year: {year}")
        print(f"Venue: {venue}")

        # Author information
        authors = paper.get("authors", [])
        if authors:
            if isinstance(authors, list) and len(authors) > 0:
                if isinstance(authors[0], dict):
                    author_names = [a.get("name", "Unknown") for a in authors[:5]]
                    print(
                        f"Authors ({len(authors)} total): {', '.join(author_names)}{'...' if len(authors) > 5 else ''}"
                    )
                else:
                    print(
                        f"Authors: {', '.join(authors[:5])}{'...' if len(authors) > 5 else ''}"
                    )
            else:
                print(f"Authors: {authors}")
        else:
            print("Authors: Not available")

        # Citation metrics
        citation_count = paper.get("citation_count", paper.get("citationCount", "N/A"))
        reference_count = paper.get(
            "reference_count", paper.get("referenceCount", "N/A")
        )
        influential_citations = paper.get(
            "influential_citation_count", paper.get("influentialCitationCount", "N/A")
        )
        print(f"Citations: {citation_count}")
        print(f"References: {reference_count}")
        print(f"Influential Citations: {influential_citations}")

        # Access and content info
        is_open_access = paper.get("isOpenAccess", paper.get("is_open_access", "N/A"))
        print(f"Open Access: {is_open_access}")

        # Relevance and retrieval info
        if "score" in paper:
            print(f"Relevance Score: {paper['score']:.4f}")
        if "relevance_judgement" in paper:
            print(f"Relevance Judgment: {paper['relevance_judgement']:.4f}")

        # Fields of study
        fields_of_study = paper.get("fieldsOfStudy", paper.get("fields_of_study", []))
        if fields_of_study:
            if isinstance(fields_of_study, list):
                print(
                    f"Fields of Study: {', '.join(fields_of_study[:3])}{'...' if len(fields_of_study) > 3 else ''}"
                )
            else:
                print(f"Fields of Study: {fields_of_study}")

        # URLs and DOI
        doi = paper.get("doi", "N/A")
        url = paper.get("url", paper.get("externalIds", {}).get("DOI", "N/A"))
        if doi != "N/A":
            print(f"DOI: {doi}")
        if url != "N/A" and url != doi:
            print(f"URL: {url}")

        # Abstract preview
        abstract = paper.get("abstract", "")
        if abstract:
            abstract_preview = (
                abstract[:300] + "..." if len(abstract) > 300 else abstract
            )
            print(f"Abstract: {abstract_preview}")

        print("-" * 80)

    if len(unique_papers) > max_results:
        remaining = len(unique_papers) - max_results
        print(f"\n... and {remaining} more papers available")

    # Field descriptions
    print("\nRETRIEVED FIELD DESCRIPTIONS")
    print("=" * 50)
    print("Understanding the data fields returned for each paper:\n")

    field_descriptions = {
        "corpus_id": "Unique identifier for the paper in Semantic Scholar database",
        "title": "Full title of the research paper",
        "text": "Retrieved text snippet/passage content from the paper",
        "score": (
            "Relevance score (0-1) indicating how well the passage matches the query"
        ),
        "section_title": (
            "Section name where the passage was found (e.g., Abstract, Methods, Results)"
        ),
        "stype": (
            "Snippet type - indicates the kind of text retrieved (e.g., abstract, body text)"
        ),
        "char_start_offset": (
            "Character position where the snippet starts in the original document"
        ),
        "sentence_offsets": (
            "Start/end positions of sentences within the retrieved snippet"
        ),
        "ref_mentions": (
            "Citations and references mentioned within the retrieved passage"
        ),
        "pdf_hash": "Hash identifier for the paper's PDF file (if available)",
    }

    for field, description in field_descriptions.items():
        print(f"  {field:25} → {description}")

    # Summary of available fields
    print("\nFIELD AVAILABILITY SUMMARY")
    print("=" * 50)
    all_fields = set()
    field_counts = {}

    for paper in unique_papers[:10]:
        for field in paper.keys():
            all_fields.add(field)
            if paper.get(field):
                field_counts[field] = field_counts.get(field, 0) + 1

    print("Fields found across papers (in first 10 results):")
    for field in sorted(all_fields):
        count = field_counts.get(field, 0)
        percentage = (count / min(10, len(unique_papers)) * 100) if unique_papers else 0
        availability = "✓" if count > 5 else "○" if count > 0 else "✗"
        print(
            f"  {availability} {field:25} → Available in {count}/{min(10, len(unique_papers))} papers ({percentage:.0f}%)"
        )

    print(f"\n{'='*70}")
    print("PIPELINE STAGE 2 COMPLETED SUCCESSFULLY")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test ScholarQA Pipeline Stage 2: Retrieval Process"
    )
    parser.add_argument("--query", type=str, help="Research query to process")
    parser.add_argument(
        "--max-results",
        type=int,
        default=3,
        help="Max results to display in detail (default: 3)",
    )

    args = parser.parse_args()

    # Get query from user if not provided
    query = args.query
    if not query:
        print("\nPlease enter your research query:")
        print("(Press Enter without typing to use default query)")
        query = input("Query: ").strip()

    if not query:
        # Use default query if none provided
        query = "how can we improve mental health outcomes and reduce substance misuse among displaced communities in Ethiopia"
        print(f"\nUsing default query: {query}")

    try:
        run_retrieval_pipeline(query, args.max_results)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
