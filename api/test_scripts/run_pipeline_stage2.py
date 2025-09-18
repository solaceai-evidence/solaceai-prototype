#!/usr/bin/env python3
"""
Pipeline Stage 2: Paper Retrieval Process

This script demonstrates the complete retrieval workflow:
1. Query Decomposition - Parses user query and extracts search filters  
2. Paper Retrieval - Finds relevant papers using semantic and keyword search
3. Results Processing - Deduplicates and presents top results

Features:
- Automatic Python virtual environment setup
- Dynamic parameter extraction and display
- Comprehensive retrieval results with relevance scores
- Clean, user-friendly output formatting
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import atexit
import inspect

# Setup paths
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
api_dir = project_root / "api"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd: str) -> subprocess.CompletedProcess:
    """Execute a shell command and return the result"""
    logger.debug(f"Executing command: {cmd}")
    return subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)


def discover_search_filter_parameters():
    """
    Discover and display all available search parameters in the retrieval system
    """
    print("COMPREHENSIVE PARAMETER DISCOVERY")
    print("="*50)
    
    try:
        # Add the API directory to the path temporarily
        api_path = str(api_dir)
        if api_path not in sys.path:
            sys.path.insert(0, api_path)
        
        print("1. DecomposedQuery Model Fields:")
        print("-" * 35)
        
        try:
            from scholarqa.preprocess.query_preprocessor import LLMProcessedQuery
            # LLMProcessedQuery is a namedtuple, show its fields
            print("  LLMProcessedQuery fields:")
            for field in LLMProcessedQuery._fields:
                print(f"    • {field}")
        except Exception as e:
            print(f"  Could not analyze LLMProcessedQuery: {e}")
        
        print()
        print("2. Search Filter Parameters (from query preprocessor):")
        print("-" * 55)
        
        # These are the actual parameters used in query_preprocessor.py
        search_params = {
            'year': 'Constructed from earliest_search_year + latest_search_year',
            'venue': 'Mapped from venues field',  
            'fieldsOfStudy': 'Mapped from field_of_study field',
            'authors': 'Mapped from authors field (list or string)',
            'limit': 'Maximum results limit for retrieval'
        }
        
        for param, description in search_params.items():
            print(f"    • {param:15} → {description}")
        
        print()
        print("3. Retrieval System Parameters:")
        print("-" * 35)
        
        # Additional parameters that might be used by the retrieval system
        retrieval_params = {
            'query': 'Main search query string',
            'fields': 'Specific paper fields to retrieve',
            'offset': 'Result pagination offset',
            'sort': 'Result sorting criteria',
            'minCitationCount': 'Minimum citation threshold',
            'publicationTypes': 'Paper type filters',
            'openAccessPdf': 'Open access availability filter'
        }
        
        for param, description in retrieval_params.items():
            print(f"    • {param:18} → {description}")
            
        print()
        
    except Exception as e:
        print(f"Discovery failed: {e}")
        print("Using known parameters:")
        print("  • year, venue, fieldsOfStudy, authors, limit")
        print()


def setup_python_environment():
    """Setup Python virtual environment with required dependencies"""
    venv_dir = script_dir / "venv_solaceai"
    
    print(f"\n{'='*70}")
    print("SETTING UP PYTHON VIRTUAL ENVIRONMENT")
    print(f"{'='*70}")
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print(f"Creating virtual environment at {venv_dir}...")
        run_command(f"python -m venv {venv_dir}")
        print("✓ Virtual environment created")
    else:
        print(f"Virtual environment already exists at {venv_dir}")
    
    # Get the python executable path
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    # Install requirements
    requirements_file = api_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"Installing requirements from {requirements_file}...")
        run_command(f"{pip_exe} install -r {requirements_file}")
        print("✓ Requirements installed")
    else:
        logger.warning(f"Requirements file not found: {requirements_file}")
    
    return python_exe


def setup_environment_variables():
    """Setup environment variables from .env file"""
    env_vars = {}
    
    print(f"\n{'='*70}")
    print("SETTING UP ENVIRONMENT VARIABLES")
    print(f"{'='*70}")
    
    # Look for .env file in project root
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"Found .env file at: {env_file}")
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
                    print(f"  ✓ {key} (loaded)")
        
        print(f"Loaded {len(env_vars)} environment variables")
    else:
        logger.warning(f"No .env file found at: {env_file}")
        print("No environment variables loaded")
    
    return env_vars


def run_pipeline_stage2(python_exe: Path, query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Run the retrieval pipeline directly with the virtual environment
    """
    print(f"\n{'='*70}")
    print("RUNNING RETRIEVAL PIPELINE")
    print(f"{'='*70}")
    
    # Import modules with environment variables set
    env = os.environ.copy()
    env['PYTHONPATH'] = str(api_dir)
    
    # Run the retrieval pipeline
    script_content = f'''
import sys
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

sys.path.insert(0, "{api_dir}")

from scholarqa.scholar_qa import ScholarQA
from scholarqa.preprocess.query_preprocessor import decompose_query
from scholarqa.llms.constants import CLAUDE_4_SONNET
from scholarqa.rag.retrieval import PaperFinder
from scholarqa.rag.retriever_base import FullTextRetriever

def main():
    query = "{query}"
    max_results = {max_results}
    
    print(f"Original Query: {{query}}")
    print()
    
    # Step 1: Query Decomposition
    print("="*50)
    print("STEP 1: QUERY DECOMPOSITION")
    print("="*50)
    
    decomposed_query, _ = decompose_query(query, CLAUDE_4_SONNET)
    
    print(f"Rewritten Query: {{decomposed_query.rewritten_query}}")
    print(f"Keyword Query: {{decomposed_query.keyword_query}}")
    print()
    
    # Display all search parameters (both used and unused)
    print("Search Parameters Analysis:")
    print("-" * 40)
    
    # Define all possible search parameters based on the query preprocessor
    all_params = {{
        'year': 'Time range filter (earliest_search_year-latest_search_year)',
        'venue': 'Publication venue filter (conferences, journals)',
        'fieldsOfStudy': 'Academic field filter (Computer Science, etc.)',
        'authors': 'Author name filter (comma-separated)',
        'limit': 'Maximum number of results to retrieve',
    }}
    
    # Get actual search filters
    search_filters = getattr(decomposed_query, 'search_filters', {{}})
    
    print("Available Parameters:")
    for param, description in all_params.items():
        value = search_filters.get(param, 'Not specified')
        status = "✓ USED" if (param in search_filters and search_filters[param]) else "○ Available"
        print(f"  {{status:12}} {{param:15}} → {{value}}")
        print(f"               {{' ' * 15}}   ({{description}})")
    
    print()
    print("Raw Decomposition Fields (from LLM output):")
    print("-" * 45)
    
    # Show all available attributes from decomposed_query
    print("  Decomposed Query Object Attributes:")
    for attr in sorted(dir(decomposed_query)):
        if not attr.startswith('_'):  # Skip private attributes
            try:
                value = getattr(decomposed_query, attr, None)
                if not callable(value):  # Skip methods
                    status = "✓" if value else "○"
                    display_value = str(value) if value else "Not set"
                    print(f"    {{status}} {{attr:25}} → {{display_value}}")
            except:
                pass
    
    print()
    
    print("Filter Mapping Process:")
    print("-" * 25)
    print("  How raw fields become search filters:")
    
    mapping_info = [
        ("earliest_search_year + latest_search_year", "→", "year filter"),
        ("venues", "→", "venue filter"), 
        ("field_of_study", "→", "fieldsOfStudy filter"),
        ("authors (list/string)", "→", "authors filter"),
    ]
    
    for source, arrow, target in mapping_info:
        print(f"    {{source:35}} {{arrow}} {{target}}")
    
    print()
    
    # Step 2: Paper Retrieval
    print("="*50)
    print("STEP 2: PAPER RETRIEVAL")
    print("="*50)
    
    # Initialize retrieval components
    retriever = FullTextRetriever()
    paper_finder = PaperFinder(retriever=retriever)
    qa_system = ScholarQA(paper_finder=paper_finder)
    
    print(f"Running retrieval with limit={max_results}...")
    
    # Retrieve papers using the ScholarQA system
    snippet_results, search_api_results = qa_system.find_relevant_papers(
        decomposed_query, 
        limit=max_results
    )
    
    print(f"Retrieved {{len(snippet_results)}} passage results")
    print(f"Retrieved {{len(search_api_results)}} additional papers from keyword search")
    
    # Step 3: Results Processing
    print("\\n" + "="*50)
    print("STEP 3: RESULTS")
    print("="*50)
    
    # Combine results and deduplicate by corpus_id
    all_results = snippet_results + search_api_results
    papers_by_id = {{}}
    for item in all_results:
        corpus_id = item.get('corpus_id')
        if corpus_id and corpus_id not in papers_by_id:
            papers_by_id[corpus_id] = item
    
    unique_papers = list(papers_by_id.values())
    print(f"Total unique papers: {{len(unique_papers)}}")
    
    # Display comprehensive results with all available fields
    print(f"\\nTop {{min(max_results, len(unique_papers))}} Results:")
    print("=" * 80)
    
    for i, paper in enumerate(unique_papers[:max_results], 1):
        print(f"\\nPAPER {{i}}")
        print("-" * 20)
        
        # Core identification
        corpus_id = paper.get('corpus_id', 'N/A')
        title = paper.get('title', 'No title available')
        print(f"Corpus ID: {{corpus_id}}")
        print(f"Title: {{title}}")
        
        # Publication details
        year = paper.get('year', 'Unknown')
        venue = paper.get('venue', 'Unknown')
        print(f"Year: {{year}}")
        print(f"Venue: {{venue}}")
        
        # Author information
        authors = paper.get('authors', [])
        if authors:
            if isinstance(authors, list) and len(authors) > 0:
                if isinstance(authors[0], dict):
                    # Authors as objects with names
                    author_names = [a.get('name', 'Unknown') for a in authors[:5]]
                    print(f"Authors ({{len(authors)}} total): {{', '.join(author_names)}}{{'...' if len(authors) > 5 else ''}}")
                else:
                    # Authors as simple strings
                    print(f"Authors: {{', '.join(authors[:5])}}{{'...' if len(authors) > 5 else ''}}")
            else:
                print(f"Authors: {{authors}}")
        else:
            print("Authors: Not available")
        
        # Citation metrics
        citation_count = paper.get('citation_count', paper.get('citationCount', 'N/A'))
        reference_count = paper.get('reference_count', paper.get('referenceCount', 'N/A'))
        influential_citations = paper.get('influential_citation_count', paper.get('influentialCitationCount', 'N/A'))
        print(f"Citations: {{citation_count}}")
        print(f"References: {{reference_count}}")
        print(f"Influential Citations: {{influential_citations}}")
        
        # Access and content info
        is_open_access = paper.get('isOpenAccess', paper.get('is_open_access', 'N/A'))
        print(f"Open Access: {{is_open_access}}")
        
        # Relevance and retrieval info
        if 'score' in paper:
            print(f"Relevance Score: {{paper['score']:.4f}}")
        if 'relevance_judgement' in paper:
            print(f"Relevance Judgment: {{paper['relevance_judgement']:.4f}}")
        
        # Fields of study
        fields_of_study = paper.get('fieldsOfStudy', paper.get('fields_of_study', []))
        if fields_of_study:
            if isinstance(fields_of_study, list):
                print(f"Fields of Study: {{', '.join(fields_of_study[:3])}}{{'...' if len(fields_of_study) > 3 else ''}}")
            else:
                print(f"Fields of Study: {{fields_of_study}}")
        
        # URLs and DOI
        doi = paper.get('doi', 'N/A')
        url = paper.get('url', paper.get('externalIds', {{}}).get('DOI', 'N/A'))
        if doi != 'N/A':
            print(f"DOI: {{doi}}")
        if url != 'N/A' and url != doi:
            print(f"URL: {{url}}")
        
        # Abstract preview
        abstract = paper.get('abstract', '')
        if abstract:
            abstract_preview = abstract[:300] + "..." if len(abstract) > 300 else abstract
            print(f"Abstract: {{abstract_preview}}")
        
        # Additional metadata if available
        paper_id = paper.get('paperId', paper.get('paper_id', ''))
        if paper_id:
            print(f"Paper ID: {{paper_id}}")
        
        # Show any additional fields that might be present
        common_fields = {{
            'corpus_id', 'title', 'year', 'venue', 'authors', 'citation_count', 
            'citationCount', 'reference_count', 'referenceCount', 'influential_citation_count',
            'influentialCitationCount', 'isOpenAccess', 'is_open_access', 'score', 
            'relevance_judgement', 'fieldsOfStudy', 'fields_of_study', 'doi', 'url', 
            'abstract', 'paperId', 'paper_id', 'externalIds'
        }}
        
        additional_fields = {{k: v for k, v in paper.items() if k not in common_fields and v}}
        if additional_fields:
            print(f"Additional Fields: {{list(additional_fields.keys())}}")
        
        print("-" * 80)
    
    if len(unique_papers) > max_results:
        remaining = len(unique_papers) - max_results
        print(f"\\n... and {{remaining}} more papers available")
        
    # Summary of available fields across all papers
    print(f"\\nFIELD AVAILABILITY SUMMARY")
    print("=" * 50)
    all_fields = set()
    field_counts = {{}}
    
    for paper in unique_papers[:10]:  # Check first 10 papers for field availability
        for field in paper.keys():
            all_fields.add(field)
            if paper.get(field):  # Only count non-empty fields
                field_counts[field] = field_counts.get(field, 0) + 1
    
    print(f"Fields found across papers (in first 10 results):")
    for field in sorted(all_fields):
        count = field_counts.get(field, 0)
        percentage = (count / min(10, len(unique_papers)) * 100) if unique_papers else 0
        availability = "✓" if count > 5 else "○" if count > 0 else "✗"
        print(f"  {{availability}} {{field:25}} → Available in {{count}}/{{min(10, len(unique_papers))}} papers ({{percentage:.0f}}%)")
    
    print()

if __name__ == "__main__":
    main()
'''
    
    # Execute the script using the virtual environment Python
    result = subprocess.run(
        [str(python_exe), '-c', script_content],
        env=env,
        capture_output=False,
        text=True,
        cwd=str(api_dir)
    )
    
    if result.returncode != 0:
        logger.error(f"Pipeline execution failed with return code {result.returncode}")
        raise subprocess.CalledProcessError(result.returncode, "retrieval pipeline")
    
    return {"status": "completed"}


def cleanup_handler():
    """Cleanup function to run on exit"""
    print(f"\n{'='*70}")
    print("CLEANUP COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test ScholarQA Pipeline Stage 2: Retrieval Process"
    )
    parser.add_argument("--query", type=str, help="optional predefined query")
    parser.add_argument("--max-results", type=int, default=3, help="Max results to display in detail (default: 3)")
    parser.add_argument("--skip-setup", action="store_true", help="Skip environment setup")

    args = parser.parse_args()
    
    # Register cleanup handler
    atexit.register(cleanup_handler)

    try:
        if not args.skip_setup:
            # Setup Python virtual environment
            python_exe = setup_python_environment()
        else:
            python_exe = Path(sys.executable)
            print("Skipping environment setup (using current Python environment)")

        # Setup environment variables
        env_vars = setup_environment_variables()
        
        if not env_vars.get('S2_API_KEY'):
            logger.error("S2_API_KEY not found in environment variables")
            print("\nPlease ensure your .env file contains:")
            print("S2_API_KEY=your_semantic_scholar_api_key")
            sys.exit(1)

        # Get query from user if not provided
        query = args.query
        if not query:
            print("\nPlease enter your research query:")
            query = input("Query: ").strip()
            
        if not query:
            print("Error: No query provided. Exiting.")
            sys.exit(1)

        print(f"\n{'='*70}")
        print("PIPELINE STAGE 2: RETRIEVAL PROCESS")
        print(f"{'='*70}")

        # First show available parameters
        discover_search_filter_parameters()

        # Run pipeline stage 2
        success = run_pipeline_stage2(python_exe, query, args.max_results)
        
        if success:
            print(f"\n{'='*70}")
            print("PIPELINE STAGE 2 COMPLETED SUCCESSFULLY")
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print("PIPELINE STAGE 2 FAILED")
            print(f"{'='*70}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)