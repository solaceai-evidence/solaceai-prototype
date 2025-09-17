"""Utility functions for managing virtual environments in run_pipeline_* scripts."""

import os
import shutil
import subprocess
import sys
import venv
from contextlib import contextmanager
from pathlib import Path


def get_venv_path(script_path: str) -> Path:
    """Get the virtual environment path for a script."""
    script_name = os.path.splitext(os.path.basename(script_path))[0]
    return Path(os.path.dirname(script_path)) / f".venv_{script_name}"


def create_venv(venv_path: Path) -> None:
    """Create a virtual environment at the specified path."""
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)


def install_dependencies(venv_path: Path, requirements_files: list[str]) -> None:
    """Install dependencies in the virtual environment."""
    pip_path = venv_path / "bin" / "pip"
    for req_file in requirements_files:
        print(f"Installing dependencies from {req_file}...")
        subprocess.check_call([str(pip_path), "install", "-r", req_file])


def cleanup_venv(venv_path: Path) -> None:
    """Remove the virtual environment directory."""
    if venv_path.exists():
        print(f"Cleaning up virtual environment at {venv_path}...")
        shutil.rmtree(venv_path)


@contextmanager
def managed_venv(script_path: str, requirements_files: list[str]):
    """Context manager for creating, using, and cleaning up a virtual environment.

    Usage:
        with managed_venv(__file__, ['requirements.txt']):
            # Your script code here
            pass
    """
    venv_path = get_venv_path(script_path)
    try:
        # Create and activate venv
        create_venv(venv_path)
        # Install dependencies
        install_dependencies(venv_path, requirements_files)
        yield
    finally:
        # Clean up venv
        cleanup_venv(venv_path)
