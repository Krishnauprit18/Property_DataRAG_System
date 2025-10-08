#!/bin/bash

# Start Frontend Script
echo "========================================"
echo "Starting Property RAG Frontend"
echo "========================================"

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "Error: Dependencies not installed!"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Warning: Backend server is not running!"
    echo "Please start the backend first:"
    echo "  bash scripts/start_backend.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start Streamlit
echo "Starting Streamlit on http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

streamlit run frontend/app.py
