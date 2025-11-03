#!/bin/bash

# Local RAG CLI wrapper script
# This script sets up the environment and launches the Local RAG CLI

# Exit on any error
set -e

# Detect Python version dynamically
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "3.11")

# Set Python path to include the installed package
export PYTHONPATH="/usr/lib/python${PYTHON_VERSION}/site-packages:${PYTHONPATH:-}"

# Change to the application data directory
cd /var/lib/local-rag

# Execute the CLI module with all provided arguments
exec python3 -m guide.cli "$@"