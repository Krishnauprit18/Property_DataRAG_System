# Property Data RAG System

A Retrieval-Augmented Generation (RAG) system for intelligent property search and question answering using real estate data.

## 🎯 Project Overview

This system allows users to query property listings using natural language and receive intelligent, context-aware responses. Built with:

- **Backend**: FastAPI
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2)
- **LLM**: Google Gemini API
- **Frontend**: Streamlit

## 📋 Features

- ✅ Natural language queries about properties
- ✅ Vector similarity search for relevant property retrieval
- ✅ LLM-powered response generation with citations
- ✅ Advanced filtering (price, bedrooms, bathrooms)
- ✅ Interactive web interface
- ✅ 147,000+ property records
- ✅ Real-time statistics and analytics

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone or navigate to the project directory**
```bash
cd /home/krishna/Music/Property_DataRAG_System
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` file and add your Google Gemini API key (optional but recommended):
```env
GEMINI_API_KEY=your_api_key_here
```

Get free API key from: https://makersuite.google.com/app/apikey

### Initial Data Load

**Run this once to load property data into the vector database:**

```bash
python scripts/load_data.py
```

This will:
- Load and clean 147,000+ property records
- Generate embeddings using Sentence-Transformers
- Store in ChromaDB vector database
- Takes ~10-15 minutes for full dataset

### Running the Application

**Terminal 1 - Start Backend Server:**
```bash
cd backend
python main.py
```

Backend will run on: http://localhost:8000

**Terminal 2 - Start Frontend:**
```bash
streamlit run frontend/app.py
```

Frontend will open automatically at: http://localhost:8501

## 📊 Sample Queries

Try these example queries:

- "What's the average price of 3 bedroom homes?"
- "Find properties under £1000 with 2+ bathrooms"
- "Which area has the highest crime score?"
- "Show me the cheapest studio apartments"
- "Compare prices between terraced and detached houses"
- "What are the most expensive properties in London?"
- "Find 2 bedroom apartments with low flood risk"

## 🏗️ Project Structure

```
Property_DataRAG_System/
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── data_ingestion.py       # Data loading & preprocessing
│   ├── vector_store.py         # ChromaDB vector database
│   ├── llm_handler.py          # Gemini LLM integration
│   ├── rag_pipeline.py         # RAG orchestration
│   └── chroma_db/              # Vector database storage
├── frontend/
│   └── app.py                  # Streamlit web interface
├── scripts/
│   └── load_data.py            # Data loading script
├── Property_data.csv           # Property dataset (147K records)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## 🔧 API Endpoints

### Backend API (http://localhost:8000)

- `GET /` - API information
- `GET /health` - Health check
- `GET /stats` - Database statistics
- `POST /query` - Query properties (main endpoint)
- `GET /search?q=query` - Simple search

### Example API Request

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find 2 bedroom apartments under £2000",
    "n_results": 5,
    "max_price": 2000,
    "bedrooms": 2
  }'
```

## 📈 Dataset Information

The dataset contains **147,667 property records** with:

**Required Fields:**
- Address
- Price (monthly rent in GBP)
- Bedrooms
- Bathrooms
- Property type
- Listing date
- Description

**Optional Fields:**
- Crime score (1-10)
- Flood risk
- New home status
- Local authority code

## 🔍 How It Works

1. **Data Ingestion**: CSV data is loaded, cleaned, and enriched
2. **Embedding Generation**: Property descriptions converted to vectors using Sentence-Transformers
3. **Vector Storage**: Embeddings stored in ChromaDB with metadata
4. **Query Processing**: User queries converted to embeddings
5. **Retrieval**: Similar properties found using cosine similarity
6. **Response Generation**: LLM generates natural language answer using retrieved data

## 🎓 Technical Details

### RAG Pipeline

```
User Query → Embedding → Vector Search → Top-K Properties → LLM → Response
```

### Embedding Model
- **Model**: all-MiniLM-L6-v2
- **Dimension**: 384
- **Speed**: ~14,000 sentences/sec
- **Quality**: High quality for semantic search

### LLM Integration
- **Primary**: Google Gemini Pro (free tier: 15 req/min)
- **Fallback**: Rule-based responses (no API key needed)

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000
# Kill process if needed
kill -9 <PID>
```

### Frontend shows "Backend not running"
- Ensure backend is running on port 8000
- Check firewall settings
- Verify BACKEND_URL in .env

### Data loading takes too long
- Normal for 147K records (~10-15 min)
- Reduce batch_size in load_data.py if memory issues
- Monitor with: `watch -n 1 'ls -lh backend/chroma_db'`

### LLM not generating responses
- Check GEMINI_API_KEY in .env
- Verify API key at https://makersuite.google.com
- System falls back to rule-based responses if no API key

## 📦 Dependencies

See `requirements.txt` for full list. Key packages:

- fastapi==0.104.1
- chromadb==0.4.18
- sentence-transformers==2.2.2
- google-generativeai==0.3.1
- streamlit==1.28.2
- pandas==2.1.3

## 🤝 Contributing

This is a recruitment project for Simplyphi.

## 📝 License

This project is created for educational and recruitment purposes.

## 👨‍💻 Author

Created as part of Simplyphi recruitment process.

## 🙏 Acknowledgments

- Dataset: Property listings from various UK sources
- Embeddings: Sentence-Transformers by UKPLab
- Vector DB: ChromaDB
- LLM: Google Gemini

---

**Note**: Make sure to run `python scripts/load_data.py` before starting the application for the first time!
