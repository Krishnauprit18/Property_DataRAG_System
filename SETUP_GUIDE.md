# Setup Guide - Property RAG System

Complete step-by-step setup instructions for the Property RAG System.

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- 2GB free disk space
- Internet connection (for downloading models and API)

## 🔧 Step-by-Step Setup

### Step 1: Verify Python Installation

```bash
python --version
# Should show Python 3.8 or higher
```

If Python is not installed, download from: https://www.python.org/downloads/

### Step 2: Navigate to Project Directory

```bash
cd /home/krishna/Music/Property_DataRAG_System
```

### Step 3: Create Virtual Environment

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI & Uvicorn (Backend server)
- ChromaDB (Vector database)
- Sentence-Transformers (Embeddings)
- Google Generative AI (LLM)
- Streamlit (Frontend)
- Pandas, NumPy (Data processing)

**Installation time:** ~5-10 minutes

### Step 5: Configure Environment Variables

1. Copy the example env file:
```bash
cp .env.example .env
```

2. Edit `.env` file:
```bash
nano .env  # or use any text editor
```

3. Add your Google Gemini API key (optional but recommended):
```env
GEMINI_API_KEY=your_api_key_here
BACKEND_HOST=localhost
BACKEND_PORT=8000
```

**Get Free Gemini API Key:**
- Visit: https://makersuite.google.com/app/apikey
- Sign in with Google account
- Click "Create API Key"
- Copy and paste into `.env` file

**Note:** System works without API key but with limited features (rule-based responses only)

### Step 6: Load Property Data

This is a **one-time operation** to load data into the vector database:

```bash
python scripts/load_data.py
```

**What this does:**
1. Loads 147,667 property records from CSV
2. Cleans and preprocesses data
3. Generates vector embeddings using Sentence-Transformers
4. Stores in ChromaDB vector database

**Expected output:**
```
============================================================
Property Data Loading Script
============================================================

[1/4] Loading CSV data...
✓ Loaded 147,667 records

[2/4] Cleaning data...
✓ Cleaned data: 147,667 records

[3/4] Creating document embeddings...
✓ Created 147,667 documents

[4/4] Loading into ChromaDB vector store...
This may take several minutes for large datasets...
✓ Successfully loaded 147,667 properties into vector store

============================================================
✓ Data loading complete!
============================================================
```

**Time:** ~10-15 minutes for full dataset

**Troubleshooting:**
- If memory error occurs, the script uses batching (100 docs at a time)
- Check `backend/chroma_db/` directory is created
- Verify CSV file exists: `Property_data.csv`

### Step 7: Verify Installation

Check if all components are ready:

```bash
# Check vector database
ls -lh backend/chroma_db/

# Check backend files
ls backend/*.py

# Check frontend
ls frontend/app.py
```

## 🚀 Running the Application

### Method 1: Using Shell Scripts (Recommended)

**Terminal 1 - Start Backend:**
```bash
bash scripts/start_backend.sh
```

**Terminal 2 - Start Frontend:**
```bash
bash scripts/start_frontend.sh
```

### Method 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/app.py
```

### Access the Application

- **Frontend (User Interface):** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## ✅ Testing the System

### Test 1: Backend Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "vector_store": "connected",
  "total_properties": 147667
}
```

### Test 2: Simple Query via API

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the average price of 2 bedroom apartments?",
    "n_results": 5
  }'
```

### Test 3: Frontend Interface

1. Open http://localhost:8501
2. Try example query: "What's the average price of 3 bedroom homes?"
3. Click "Search"
4. Verify results appear

## 🎯 Sample Queries to Try

1. **Price Analysis:**
   - "What's the average price of 3 bedroom homes?"
   - "Find the cheapest properties"
   - "What are the most expensive properties in London?"

2. **Filtered Search:**
   - "Find properties under £1000 with 2+ bathrooms"
   - "Show me 2 bedroom apartments"
   - "Properties with 4 bedrooms and low crime score"

3. **Comparative Analysis:**
   - "Compare prices between studio and 2 bed homes"
   - "Which property type is most expensive?"
   - "Difference between terraced and detached houses"

4. **Location-Based:**
   - "Which area has the highest crime score?"
   - "Properties in Southampton"
   - "Safest areas to live"

5. **Risk Assessment:**
   - "Find properties with low flood risk"
   - "Properties with crime score below 3"
   - "Safest properties under £2000"

## 🔍 Project Structure Overview

```
Property_DataRAG_System/
│
├── backend/                    # Backend API
│   ├── main.py                # FastAPI server entry point
│   ├── data_ingestion.py      # Data loading & cleaning
│   ├── vector_store.py        # ChromaDB operations
│   ├── llm_handler.py         # Gemini LLM integration
│   ├── rag_pipeline.py        # RAG orchestration
│   └── chroma_db/             # Vector database (created after load)
│
├── frontend/                   # Streamlit web interface
│   └── app.py                 # Main UI application
│
├── scripts/                    # Utility scripts
│   ├── load_data.py           # One-time data loading
│   ├── start_backend.sh       # Backend startup script
│   └── start_frontend.sh      # Frontend startup script
│
├── Property_data.csv           # Property dataset (147K records)
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── .env                       # Your environment config (create this)
├── README.md                  # Main documentation
└── SETUP_GUIDE.md            # This file
```

## 🐛 Common Issues & Solutions

### Issue 1: "ModuleNotFoundError"
**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 2: "Port 8000 already in use"
**Solution:**
```bash
# Find process using port
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

### Issue 3: "Backend not running" in Frontend
**Solution:**
- Ensure backend is started first
- Check if backend is on http://localhost:8000
- Verify with: `curl http://localhost:8000/health`

### Issue 4: Data loading fails
**Solution:**
```bash
# Check CSV file exists
ls -lh Property_data.csv

# Check permissions
chmod 644 Property_data.csv

# Try loading again
python scripts/load_data.py
```

### Issue 5: LLM not generating responses
**Solution:**
- Check `.env` file has `GEMINI_API_KEY`
- Verify API key at https://makersuite.google.com
- System works without API key (uses fallback)

### Issue 6: Slow performance
**Solution:**
- Reduce `n_results` in queries (default: 5)
- Close other applications
- Check system has 2GB+ free RAM
- Consider using smaller batch sizes

## 📊 System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 2GB free
- OS: Linux, macOS, Windows 10+

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 5GB free
- SSD for faster loading

## 🔐 Security Notes

- Never commit `.env` file to git (already in .gitignore)
- Keep API keys secret
- Backend accepts all origins (CORS) - restrict for production
- Use environment variables for sensitive config

## 📚 Next Steps

After setup:
1. ✅ Read the main README.md
2. ✅ Try sample queries
3. ✅ Explore API documentation at http://localhost:8000/docs
4. ✅ Experiment with filters in frontend
5. ✅ Check dataset statistics

## 🆘 Getting Help

If you encounter issues:
1. Check this guide
2. Review error messages carefully
3. Check logs in terminal
4. Verify all prerequisites are met
5. Try restarting both backend and frontend

## ✨ Tips for Best Results

1. **Be specific in queries**: "2 bedroom apartments under £2000" works better than "cheap homes"
2. **Use filters**: Combine natural language with sidebar filters
3. **Try different phrasings**: System understands various question formats
4. **Check statistics**: Use /stats endpoint to understand data distribution
5. **Experiment**: Try edge cases and complex queries

---

**Setup complete! You're ready to use the Property RAG System.**

For technical details, see README.md
