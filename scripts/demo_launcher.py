#!/usr/bin/env python
"""
Demo launcher for the educational assistant.

This script provides convenient ways to launch different interfaces for the assistant.
"""

import argparse
import subprocess
from pathlib import Path

from app.config import settings

# Define project root
PROJECT_ROOT = Path(__file__).parent.parent


def check_environment():
    """Check that the environment is properly set up."""
    if not settings.GEMINI_API_KEY:
        print("\n⚠️  Gemini API key not found! ⚠️")
        print(
            "Please set your GEMINI_API_KEY in the .env file or as an environment variable."
        )
        print("Example:")
        print("    export GEMINI_API_KEY=your_api_key_here\n")
        return False

    # Check for knowledge base file
    if not settings.knowledge_base_path.exists():
        print(
            f"\n⚠️  Knowledge base file not found at: {settings.knowledge_base_path} ⚠️"
        )
        print("Please make sure the file exists before running the assistant.\n")
        return False

    return True


def run_cli():
    """Run the command-line interface."""
    print("\n🚀 Starting CLI interface...")
    if not check_environment():
        return

    # Import and run the CLI main loop
    import asyncio

    from app.main import main_loop

    asyncio.run(main_loop())


def run_streamlit():
    """Run the Streamlit interface."""
    print("\n🚀 Starting Streamlit interface...")
    if not check_environment():
        return

    streamlit_path = PROJECT_ROOT / "ui" / "streamlit_app.py"

    # Launch Streamlit as a subprocess
    cmd = ["streamlit", "run", str(streamlit_path), "--server.headless", "true"]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Streamlit server...")
    except FileNotFoundError:
        print("\n❌ Streamlit not found! Please install streamlit:")
        print("    pip install streamlit\n")


def main():
    """Parse arguments and run the appropriate interface."""
    parser = argparse.ArgumentParser(
        description="Launch the educational assistant in different interfaces."
    )
    parser.add_argument(
        "--ui",
        choices=["cli", "streamlit"],
        default="streamlit",
        help="Interface to launch (default: streamlit)",
    )

    args = parser.parse_args()

    if args.ui == "cli":
        run_cli()
    else:
        run_streamlit()


if __name__ == "__main__":
    main()
