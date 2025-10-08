#!/bin/bash

# Start Backend Script
echo "========================================"
echo "Starting Property RAG Backend Server"
echo "========================================"

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Activate virtual environment if exists
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Error: Dependencies not installed!"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Check if vector database exists
if [ ! -d "chroma_db" ]; then
    echo "Warning: Vector database not found!"
    echo "Please run: python scripts/load_data.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the server
echo "Starting FastAPI server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python main.py
