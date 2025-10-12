#!/bin/bash
# Quick start script for video demo

echo "=================================="
echo "Starting Property RAG System"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python -m venv backend/venv"
    exit 1
fi

echo ""
echo "📋 Pre-flight checks..."
echo ""

# Check data
if [ ! -f "Property_data.csv" ]; then
    echo "❌ Property_data.csv not found!"
    exit 1
fi
echo "✅ Property data file found"

# Check ChromaDB
if [ -d "backend/chroma_db" ]; then
    SIZE=$(du -sh backend/chroma_db | cut -f1)
    echo "✅ ChromaDB found ($SIZE)"
else
    echo "⚠️  ChromaDB not found - run: python scripts/load_data.py"
fi

# Check .env
if [ -f ".env" ]; then
    echo "✅ .env file found"
else
    echo "⚠️  .env file not found - create it with GROQ_API_KEY"
fi

echo ""
echo "🚀 Starting services..."
echo ""
echo "Backend will start on: http://localhost:8000"
echo "Frontend will start on: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=================================="

# Start backend in background
cd backend
source venv/bin/activate
echo "Starting backend..."
python main.py
