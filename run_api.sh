#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install dependencies using uv sync from pyproject.toml
if [ -f "pyproject.toml" ]; then
    # Check if uv is installed, if not install it
    if ! command -v uv &> /dev/null; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    echo "Installing dependencies using uv sync..."
    uv sync
fi

# Run the API server
uvicorn api:app --host 0.0.0.0 --port 8000 --reload 