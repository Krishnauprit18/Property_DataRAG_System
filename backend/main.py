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
from global_analytics import GlobalAnalytics
from query_analytics import analytics, monitor
from conversation_manager import conversation_manager

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
global_analytics = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global vector_store, rag_pipeline, global_analytics

    # Startup
    logger.info("Starting Property RAG System...")

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

    # Initialize Global Analytics
    try:
        csv_path = str((Path(__file__).parent.parent / "Property_data.csv").resolve())
        global_analytics = GlobalAnalytics(csv_path)
        logger.info("✅ Global analytics initialized")
    except Exception as e:
        logger.warning(f"⚠️ Global analytics unavailable: {e}")
        global_analytics = None

    # Initialize RAG pipeline
    rag_pipeline = PropertyRAGPipeline(vector_store, llm_handler, analytics=global_analytics)

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
    """Request model for property queries with conversation support"""
    query: str = Field(..., description="Natural language query about properties")
    n_results: int = Field(5, description="Number of results to retrieve", ge=1, le=20)
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms filter")
    bathrooms: Optional[int] = Field(None, description="Minimum bathrooms filter")
    session_id: Optional[str] = Field(None, description="Conversation session ID for context")


class QueryResponse(BaseModel):
    """Response model for property queries with conversation support"""
    answer: str
    properties: List[Dict[str, Any]]
    num_results: int
    filters_applied: Dict[str, Any]
    session_id: str
    has_conversation_context: bool = False


# Removed deprecated on_event startup handler in favor of lifespan


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
        "total_properties": stats.get('total_documents', 0),
        "analytics": "ready" if global_analytics is not None else "unavailable"
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
    Query the property database using natural language with conversation memory

    Examples:
    - "What's the average price of 3 bedroom homes?"
    - "Find properties under £1000 with 2+ bathrooms"
    - "Which area has the most crime?"
    
    Follow-up queries with session_id:
    - "What about cheaper ones?" (continues previous context)
    - "Show me those in London" (references previous results)
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")

    import time
    start_time = time.time()
    success = False
    error_msg = None

    try:
        # Get or create conversation session
        session_id, session = conversation_manager.get_or_create_session(request.session_id)
        logger.info(f"Using session: {session_id}")

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

        # Get conversation context
        try:
            conversation_context = conversation_manager.get_session_context(session_id)
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting session context: {e}")
        
        try:
            conversation_history = conversation_manager.get_conversation_history(session_id, limit=10)
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting conversation history: {e}")

        # Add user message to conversation
        try:
            conversation_manager.add_message_to_session(
                session_id,
                'user',
                request.query,
                metadata={
                    'filters': filters if filters else {},
                    'n_results': request.n_results
                }
            )
        except Exception as e:
            logger.error(f"Error adding user message: {e}")
            raise HTTPException(status_code=500, detail=f"Error adding user message: {e}")

        # Execute query with conversation context
        result = rag_pipeline.query(
            user_query=request.query,
            n_results=request.n_results,
            filters=filters if filters else None,
            conversation_history=conversation_history,
            conversation_context=conversation_context
        )

        # Add assistant response to conversation
        conversation_manager.add_message_to_session(
            session_id,
            'assistant',
            result['answer'],
            metadata={
                'num_results': result.get('num_results', 0),
                'filters_applied': result.get('filters_applied', {})
            }
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

        # Build response
        response = QueryResponse(
            **result,
            session_id=session_id,
            has_conversation_context=conversation_context.get('has_history', False)
        )

        return response

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


@app.get("/analytics/global")
async def get_global_analytics_preview():
    """Preview of global analytics to confirm availability"""
    if global_analytics is None:
        raise HTTPException(status_code=503, detail="Global analytics unavailable")
    try:
        sample = {
            "avg_price_all": global_analytics.average_price(),
            "top_crime_areas": global_analytics.top_crime_areas(top_n=3, min_listings=50),
            "compare_studio_vs_2bed": global_analytics.compare_type_prices("studio", "2", bedrooms=None),
        }
        return sample
    except Exception as e:
        logger.error(f"Global analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: int = Query(10, description="Number of messages to return", ge=1, le=50)
):
    """Get conversation history for a session"""
    try:
        history = conversation_manager.get_conversation_history(session_id, limit=limit)
        
        if not history:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        return {
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversation/new")
async def create_new_conversation():
    """Create a new conversation session"""
    try:
        session_id = conversation_manager.create_session()
        return {
            "session_id": session_id,
            "message": "New conversation session created"
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear a conversation session"""
    try:
        success = conversation_manager.clear_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "message": "Conversation cleared successfully",
            "session_id": session_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/stats")
async def get_conversation_stats():
    """Get statistics about all conversation sessions"""
    try:
        stats = conversation_manager.get_session_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching conversation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{session_id}/context")
async def get_session_context(session_id: str):
    """Get context information for a session"""
    try:
        context = conversation_manager.get_session_context(session_id)
        
        if not context.get('has_history'):
            raise HTTPException(status_code=404, detail="Session not found or has no history")
        
        return {
            "session_id": session_id,
            "context": context
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session context: {e}")
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
