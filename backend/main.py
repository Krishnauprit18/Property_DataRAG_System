"""
FastAPI Backend Server
Exposes REST API endpoints for the Property RAG System
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

from vector_store import PropertyVectorStore
from llm_handler import LLMHandler
from rag_pipeline import PropertyRAGPipeline
from query_analytics import analytics, monitor

# Load environment variables from project root
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
vector_store = None
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global vector_store, rag_pipeline

    # Startup
    logger.info("Starting Property RAG System...")

    # Initialize vector store
    vector_store = PropertyVectorStore(persist_directory="./chroma_db")
    vector_store.create_collection()

    # Initialize LLM handler
    llm_handler = LLMHandler()

    # Initialize RAG pipeline
    rag_pipeline = PropertyRAGPipeline(vector_store, llm_handler)

    logger.info("System ready!")

    yield

    # Shutdown (if needed)
    logger.info("Shutting down Property RAG System...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Property RAG System API",
    description="RAG-based property search and question answering system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = None
rag_pipeline = None


class QueryRequest(BaseModel):
    """Request model for property queries"""
    query: str = Field(..., description="Natural language query about properties")
    n_results: int = Field(5, description="Number of results to retrieve", ge=1, le=20)
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms filter")
    bathrooms: Optional[int] = Field(None, description="Minimum bathrooms filter")


class QueryResponse(BaseModel):
    """Response model for property queries"""
    answer: str
    properties: List[Dict[str, Any]]
    num_results: int
    filters_applied: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global vector_store, rag_pipeline

    logger.info("🚀 Starting Property RAG System...")

    # Initialize vector store
    vector_store = PropertyVectorStore(persist_directory="./chroma_db")
    vector_store.create_collection()
    
    # Check if database has data
    stats = vector_store.get_collection_stats()
    doc_count = stats.get('total_documents', 0)
    
    if doc_count == 0:
        logger.warning("⚠️" + "="*60)
        logger.warning("⚠️ WARNING: Vector database is EMPTY!")
        logger.warning("⚠️ Please run the data loading script first:")
        logger.warning("⚠️   python scripts/load_data.py")
        logger.warning("⚠️" + "="*60)
    else:
        logger.info(f"✅ Loaded vector database with {doc_count:,} properties")

    # Initialize LLM handler
    llm_handler = LLMHandler()

    # Initialize RAG pipeline
    rag_pipeline = PropertyRAGPipeline(vector_store, llm_handler)

    logger.info("✅ System ready!")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Property RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "POST - Query the property database",
            "/stats": "GET - Get database statistics",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if vector_store is None or rag_pipeline is None:
        raise HTTPException(status_code=503, detail="System not initialized")

    stats = vector_store.get_collection_stats()

    return {
        "status": "healthy",
        "vector_store": "connected",
        "total_properties": stats.get('total_documents', 0)
    }


@app.get("/stats")
async def get_statistics():
    """Get database statistics"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    try:
        stats = vector_store.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_properties(request: QueryRequest):
    """
    Query the property database using natural language

    Examples:
    - "What's the average price of 3 bedroom homes?"
    - "Find properties under £1000 with 2+ bathrooms"
    - "Which area has the most crime?"
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")

    import time
    start_time = time.time()
    success = False
    error_msg = None

    try:
        # Build filters
        filters = {}
        if request.min_price is not None:
            filters['min_price'] = request.min_price
        if request.max_price is not None:
            filters['max_price'] = request.max_price
        if request.bedrooms is not None:
            filters['bedrooms'] = request.bedrooms
        if request.bathrooms is not None:
            filters['bathrooms'] = request.bathrooms

        # Execute query
        result = rag_pipeline.query(
            user_query=request.query,
            n_results=request.n_results,
            filters=filters if filters else None
        )

        success = True
        response_time = time.time() - start_time

        # Log analytics
        analytics.log_query(
            query=request.query,
            response_time=response_time,
            success=True,
            num_results=result.get('num_results', 0),
            filters=filters if filters else None
        )

        monitor.record_request(response_time, success=True)

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        response_time = time.time() - start_time
        error_msg = str(e)

        # Log failed query
        analytics.log_query(
            query=request.query,
            response_time=response_time,
            success=False,
            error=error_msg
        )

        monitor.record_request(response_time, success=False)

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics")
async def get_analytics():
    """Get query analytics and statistics"""
    try:
        stats = analytics.get_stats()
        performance = monitor.get_current_metrics()

        return {
            "query_analytics": stats,
            "performance_metrics": performance
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def simple_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Number of results", ge=1, le=20)
):
    """Simple search endpoint (GET request)"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    try:
        results = vector_store.search(query=q, n_results=limit)
        return {
            "query": q,
            "results": results['metadatas'],
            "count": len(results['metadatas'])
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")

    uvicorn.run(app, host=host, port=port)
