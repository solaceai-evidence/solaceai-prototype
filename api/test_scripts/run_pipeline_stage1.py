#!/usr/bin/env python3
"""
Script to demonstrate the query decomposition step of the pipeline (stage 1 of ScholarQA)
"""
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
import atexit
import tempfile
import shutil

# Setup paths
script_dir = Path(__file__).parent
api_dir = script_dir.parent
project_root = api_dir.parent

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_command(cmd, shell=True, check=True, capture_output=True):
    """Run a shell command and return the result"""
    logger.info(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=shell, 
            check=check, 
            capture_output=capture_output, 
            text=True,
            cwd=project_root
        )
        if result.stdout and capture_output:
            logger.debug(f"Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        raise


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
    """Setup environment variables by linking to .env file"""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        logger.warning(f".env file not found at {env_file}")
        print("\nPlease create a .env file in the project root with:")
        print("S2_API_KEY=your_semantic_scholar_api_key")
        print("ANTHROPIC_API_KEY=your_anthropic_api_key")
        return {}
    
    # Load .env variables
    env_vars = {}
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
        
        print(f"Loaded {len(env_vars)} environment variables from .env")
        
        # Check required variables
        required_vars = ['S2_API_KEY']
        missing_vars = [var for var in required_vars if not env_vars.get(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return {}
            
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return {}
    
    return env_vars

def suppress_async_warnings():
    """Setup warning suppression for cleaner output"""
    import warnings
    
    # Suppress all warnings related to async issues
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending.*")
    warnings.filterwarnings("ignore", message=".*was never awaited.*")
    
    # Redirect stderr to suppress async warnings
    class StdErrFilter:
        def __init__(self, original_stderr):
            self.original_stderr = original_stderr
            
        def write(self, text):
            # Filter out specific warning messages
            if any(phrase in text for phrase in [
                "Task was destroyed but it is pending",
                "was never awaited", 
                "RuntimeWarning: coroutine",
                "RuntimeWarning: Enable tracemalloc"
            ]):
                return
            self.original_stderr.write(text)
            
        def flush(self):
            self.original_stderr.flush()

    # Install the filter
    sys.stderr = StdErrFilter(sys.stderr)


def discover_search_filter_parameters():
    """Dynamically discover available search filter parameters from the codebase"""
    try:
        # Import within the function to avoid issues if modules aren't available yet
        from scholarqa.preprocess.query_preprocessor import DecomposedQuery, decompose_query
        import inspect
        
        discovered_params = {}
        
        # Get parameters from DecomposedQuery model
        model_fields = DecomposedQuery.__fields__
        
        # Map model field names to likely search filter names based on decompose_query logic
        field_mappings = {}
        
        # Read the decompose_query source to understand the mapping
        try:
            source = inspect.getsource(decompose_query)
            
            # Extract search filter mappings from the source
            lines = source.split('\n')
            for line in lines:
                line = line.strip()
                if 'search_filters[' in line and '=' in line:
                    # Extract patterns like: search_filters["year"] = f"{...}"
                    if 'search_filters["' in line:
                        filter_name = line.split('search_filters["')[1].split('"]')[0]
                        # Find what field it's using
                        for field_name in model_fields.keys():
                            if field_name in line or field_name.replace('_', '') in line:
                                field_mappings[field_name] = filter_name
                                break
                        if filter_name not in field_mappings.values():
                            field_mappings[f"unknown_{filter_name}"] = filter_name
            
            # Add any fields we know about but didn't find in mappings
            if 'earliest_search_year' in model_fields or 'latest_search_year' in model_fields:
                field_mappings['year_range'] = 'year'
            if 'venues' in model_fields:
                field_mappings['venues'] = 'venue'  
            if 'field_of_study' in model_fields:
                field_mappings['field_of_study'] = 'fieldsOfStudy'
            if 'authors' in model_fields:
                field_mappings['authors'] = 'authors'
                
        except Exception as e:
            # Fallback to known mappings if inspection fails
            field_mappings = {
                'year_range': 'year',
                'venues': 'venue',
                'field_of_study': 'fieldsOfStudy', 
                'authors': 'authors'
            }
        
        # Build parameter info
        for model_field, filter_name in field_mappings.items():
            if model_field in model_fields:
                field_info = model_fields[model_field]
                discovered_params[filter_name] = {
                    'model_field': model_field,
                    'description': field_info.field_info.description if hasattr(field_info.field_info, 'description') else f"Filter for {model_field}"
                }
            else:
                discovered_params[filter_name] = {
                    'model_field': model_field,
                    'description': f"Search filter: {filter_name}"
                }
        
        return discovered_params
    
    except Exception as e:
        # Ultimate fallback
        return {
            'year': {'model_field': 'year_range', 'description': 'Year range filter'},
            'venue': {'model_field': 'venues', 'description': 'Venue filter'},
            'fieldsOfStudy': {'model_field': 'field_of_study', 'description': 'Field of study filter'},
            'authors': {'model_field': 'authors', 'description': 'Authors filter'}
        }


def run_pipeline_stage_1(query: Optional[str] = None, python_exe: str = None, env_vars: dict = None):
    """Test the query processing and decomposition step of the pipeline

    Args:
        query: Optional pre-defined query for testing
        python_exe: Path to the Python executable in the virtual environment
        env_vars: Dictionary of environment variables
    """
    if not query:
        # Ask for input query via terminal
        print("\nEnter a query for decomposition (press Enter when done):")
        query = input("solace-ai> ").strip()

    if not query:
        logger.error("Query cannot be empty. Exiting")
        print("No query provided. Exiting.")
        return False

    # Setup environment variables
    if env_vars:
        for key, value in env_vars.items():
            os.environ[key] = value

    # Add the API directory to Python path
    if str(api_dir) not in sys.path:
        sys.path.insert(0, str(api_dir))

    try:
        # Setup warning suppression
        suppress_async_warnings()
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv(project_root / ".env")
        except ImportError:
            print("Warning: python-dotenv not available, skipping .env file loading")

        # Import required modules
        from scholarqa.llms.constants import CLAUDE_4_SONNET
        from scholarqa.preprocess.query_preprocessor import decompose_query

        print(f"\n{'='*70}")
        print("PIPELINE STAGE 1: QUERY DECOMPOSITION")
        print(f"{'='*70}")
        print(f"Input Query: '{query}'")
        print(f"LLM Model: {CLAUDE_4_SONNET}")
        print(f"{'='*70}")

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
        print(f"  Rewritten Query:         '{decomposed_query.rewritten_query or '[Not generated]'}'")
        print(f"  Keyword Query:           '{decomposed_query.keyword_query or '[Not generated]'}'")
        
        # Dynamically discover and display all search filter parameters
        print("\nSEARCH FILTERS:")
        filters = decomposed_query.search_filters
        discovered_params = discover_search_filter_parameters()
        
        # Display all known parameters, whether they have values or not
        for filter_name, param_info in discovered_params.items():
            display_name = filter_name.replace('_', ' ').title()
            if filter_name == 'fieldsOfStudy':
                display_name = 'Fields of Study'
            elif filter_name == 'year':
                display_name = 'Year Range'
            
            value = filters.get(filter_name, '[Not specified]')
            print(f"  {display_name:<20} {value}")
        
        # Show any additional filters that weren't in our discovered parameters
        unknown_filters = {k: v for k, v in filters.items() if k not in discovered_params}
        if unknown_filters:
            print("\n  ADDITIONAL FILTERS:")
            for filter_name, value in unknown_filters.items():
                display_name = filter_name.replace('_', ' ').title()
                print(f"    {display_name:<18} {value}")
        
        # LLM execution details
        print(f"\nEXECUTION DETAILS:")
        print(f"  Model Used:              {completion_result.model}")
        print(f"  Input Tokens:            {completion_result.input_tokens}")
        print(f"  Output Tokens:           {completion_result.output_tokens}")
        print(f"  Total Tokens:            {completion_result.total_tokens}")
        print(f"  Cost:                    ${completion_result.cost:.4f}")
        
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"\nERROR DURING DECOMPOSITION:")
        print(f"  {str(e)}")
        print("-" * 70)
        import traceback
        traceback.print_exc()
        return False


def cleanup_handler():
    """Cleanup function to run on exit"""
    print(f"\n{'='*70}")
    print("CLEANUP COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test ScholarQA Pipeline Stage 1: Query Decomposition"
    )
    parser.add_argument("--query", type=str, help="optional predefined query")
    parser.add_argument("--skip-setup", action="store_true", help="Skip conda environment setup")

    args = parser.parse_args()
    
    # Register cleanup handler
    atexit.register(cleanup_handler)

    try:
        if not args.skip_setup:
            # Setup Python virtual environment
            python_exe = setup_python_environment()
        else:
            python_exe = sys.executable
            print("Skipping environment setup (using current Python environment)")

        # Setup environment variables
        env_vars = setup_environment_variables()
        
        if not env_vars.get('S2_API_KEY'):
            logger.error("S2_API_KEY not found in environment variables")
            print("\nPlease ensure your .env file contains:")
            print("S2_API_KEY=your_semantic_scholar_api_key")
            sys.exit(1)

        print(f"\n{'='*70}")
        print("RUNNING PIPELINE STAGE 1")
        print(f"{'='*70}")

        # Run pipeline stage 1
        success = run_pipeline_stage_1(args.query, python_exe, env_vars)
        
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
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
