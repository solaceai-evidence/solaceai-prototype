#!/usr/bin/env python3
"""
Script to demonstrate the query decomposition step of the pipeline (stage 1 of ScholarQA)

This script automatically:
1. Creates/activates a conda environment named 'solaceai'
2. Installs required dependencies
3. Links to the project .env file
4. Runs the pipeline stage 1 test
5. Deactivates the environment when done
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


def setup_conda_environment():
    """Setup conda environment with required dependencies"""
    env_name = "solaceai"
    
    print(f"\n{'='*70}")
    print("SETTING UP CONDA ENVIRONMENT")
    print(f"{'='*70}")
    
    # Check if conda is available
    try:
        run_command("conda --version")
        print("✓ Conda is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Conda is not installed or not in PATH")
        print("Please install conda or miniconda first:")
        print("https://docs.conda.io/en/latest/miniconda.html")
        sys.exit(1)
    
    # Check if environment exists
    try:
        result = run_command(f"conda env list | grep {env_name}")
        if env_name in result.stdout:
            print(f"Environment '{env_name}' already exists")
        else:
            raise subprocess.CalledProcessError(1, "env not found")
    except subprocess.CalledProcessError:
        print(f"Creating conda environment '{env_name}'...")
        run_command(f"conda create -n {env_name} python=3.11 -y")
        print(f"✓ Created environment '{env_name}'")
    
    # Install pip in the environment if needed
    print(f"Ensuring pip is available in '{env_name}'...")
    run_command(f"conda run -n {env_name} python -m ensurepip --upgrade")
    
    # Install requirements
    requirements_file = api_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"Installing requirements from {requirements_file}...")
        run_command(f"conda run -n {env_name} pip install -r {requirements_file}")
        print("✓ Requirements installed")
    else:
        logger.warning(f"Requirements file not found: {requirements_file}")
    
    return env_name


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

def run_pipeline_stage_1(query: Optional[str] = None, env_name: str = "solaceai", env_vars: dict = None):
    """Test the query processing and decomposition step of the pipeline

    Args:
        query: Optional pre-defined query for testing
        env_name: Name of the conda environment to use
        env_vars: Dictionary of environment variables
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

    # Create environment setup script
    env_setup = []
    if env_vars:
        for key, value in env_vars.items():
            env_setup.append(f"export {key}='{value}'")
    
    # Create a temporary script to run in conda environment
    script_content = f'''
import sys
sys.path.insert(0, "{api_dir}")

# Suppress async warnings from LiteLLM
import warnings
import asyncio
import logging
import os

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

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path("{project_root}") / ".env")

from scholarqa.llms.constants import CLAUDE_4_SONNET
from scholarqa.preprocess.query_preprocessor import decompose_query

query = """{query}"""

print("\\n" + "=" * 70)
print("PIPELINE STAGE 1: QUERY DECOMPOSITION")
print("=" * 70)
print(f"Input Query: '{{query}}'")
print(f"LLM Model: {{CLAUDE_4_SONNET}}")
print("=" * 70)

try:
    # Run the decomposition step
    decomposed_query, completion_result = decompose_query(
        query=query, decomposer_llm_model=CLAUDE_4_SONNET
    )

    # Display comprehensive results overview
    print("\\nDECOMPOSITION RESULTS:")
    print("-" * 70)
    
    # Original vs processed queries
    print("\\nQUERY PROCESSING:")
    print(f"  Original Query:          '{{query}}'")
    print(f"  Rewritten Query:         '{{decomposed_query.rewritten_query or '[Not generated]'}}'")
    print(f"  Keyword Query:           '{{decomposed_query.keyword_query or '[Not generated]'}}'")
    
    # All search filter parameters (show whether they have values or not)
    print("\\nSEARCH FILTERS:")
    filters = decomposed_query.search_filters
    print(f"  Year Range:              {{filters.get('year', '[Not specified]')}}")
    print(f"  Venues:                  {{filters.get('venue', '[Not specified]')}}")
    print(f"  Fields of Study:         {{filters.get('fieldsOfStudy', '[Not specified]')}}")
    print(f"  Authors:                 {{filters.get('authors', '[Not specified]')}}")
    
    # LLM execution details
    print(f"\\nEXECUTION DETAILS:")
    print(f"  Model Used:              {{completion_result.model}}")
    print(f"  Input Tokens:            {{completion_result.input_tokens}}")
    print(f"  Output Tokens:           {{completion_result.output_tokens}}")
    print(f"  Total Tokens:            {{completion_result.total_tokens}}")
    print(f"  Cost:                    ${{completion_result.cost:.4f}}")
    
    print("-" * 70)
    
except Exception as e:
    print(f"\\nERROR DURING DECOMPOSITION:")
    print(f"  {{str(e)}}")
    print("-" * 70)
    import traceback
    traceback.print_exc()
'''

    # Write temporary script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        temp_script = f.name
    
    try:
        # Run the script in conda environment
        env_cmd = " && ".join(env_setup) + " && " if env_setup else ""
        cmd = f"{env_cmd}conda run -n {env_name} python {temp_script}"
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=project_root,
            text=True
        )
        
        return result.returncode == 0
        
    finally:
        # Cleanup temporary script
        if os.path.exists(temp_script):
            os.unlink(temp_script)


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
            # Setup conda environment
            env_name = setup_conda_environment()
        else:
            env_name = "solaceai"
            print("Skipping environment setup (using existing 'solaceai' environment)")

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
        success = run_pipeline_stage_1(args.query, env_name, env_vars)
        
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
