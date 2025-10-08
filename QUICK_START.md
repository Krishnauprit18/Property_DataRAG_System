# Quick Start Guide

## 🚀 Fast Installation & Setup

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install packages (this will take 10-15 minutes)
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** Installing all dependencies (especially torch and transformers) may take 10-15 minutes and requires ~4GB download.

### Step 2: Get Gemini API Key (Optional)

1. Visit: https://makersuite.google.com/app/apikey
2. Create API key (free)
3. Copy `.env.example` to `.env`
4. Add your API key to `.env`:

```env
GEMINI_API_KEY=your_key_here
```

### Step 3: Load Data (One-time - 10-15 minutes)

```bash
python scripts/load_data.py
```

This processes 147K+ properties and creates vector embeddings.

### Step 4: Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/app.py
```

### Step 5: Open & Test

- Frontend: http://localhost:8501
- Try query: "What's the average price of 2 bedroom apartments?"

## ⚡ Troubleshooting

### Installation taking too long?
This is normal. PyTorch (~888MB) and transformers (~12MB) are large packages.

### Out of memory during data loading?
The script uses batching (100 at a time) to handle 147K records efficiently.

### Backend won't start?
```bash
# Check if dependencies installed
python -c "import fastapi, chromadb, sentence_transformers"

# If error, reinstall
pip install fastapi chromadb sentence-transformers
```

### No Gemini API Key?
System works without it but uses fallback responses instead of LLM generation.

## 📖 Full Documentation

- `README.md` - Complete project documentation
- `SETUP_GUIDE.md` - Detailed setup instructions
- API Docs: http://localhost:8000/docs (after starting backend)

## ✅ Verify Installation

```bash
# Test data loading module
python -c "from backend.data_ingestion import PropertyDataLoader; print('✓ Data module OK')"

# Test vector store
python -c "from backend.vector_store import PropertyVectorStore; print('✓ Vector store OK')"

# Test LLM handler
python -c "from backend.llm_handler import LLMHandler; print('✓ LLM module OK')"
```

All should print ✓ if installation successful.
