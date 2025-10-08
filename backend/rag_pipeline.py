"""
RAG Pipeline - Orchestrates the complete RAG workflow
Combines vector search + LLM generation
"""

from typing import Dict, Any, List
import logging
from vector_store import PropertyVectorStore
from llm_handler import LLMHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyRAGPipeline:
    """Complete RAG pipeline for property queries"""

    def __init__(self, vector_store: PropertyVectorStore, llm_handler: LLMHandler):
        self.vector_store = vector_store
        self.llm_handler = llm_handler
        logger.info("RAG Pipeline initialized")

    def query(
        self,
        user_query: str,
        n_results: int = 5,
        filters: Dict = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete RAG pipeline

        Args:
            user_query: Natural language query from user
            n_results: Number of similar properties to retrieve
            filters: Optional filters (min_price, max_price, bedrooms, etc.)

        Returns:
            Dict with generated response and retrieved properties
        """
        logger.info(f"Processing query: {user_query}")

        # Step 1: Retrieve relevant properties using vector search
        try:
            search_results = self.vector_store.search(
                query=user_query,
                n_results=n_results,
                filters=filters
            )

            retrieved_properties = search_results['metadatas']
            logger.info(f"Retrieved {len(retrieved_properties)} properties")

        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return {
                'answer': "Sorry, I encountered an error while searching for properties.",
                'properties': [],
                'error': str(e)
            }

        # Step 2: Get collection statistics for context
        try:
            stats = self.vector_store.get_collection_stats()
        except Exception as e:
            logger.warning(f"Could not fetch stats: {e}")
            stats = {}

        # Step 3: Generate response using LLM
        try:
            answer = self.llm_handler.generate_response(
                query=user_query,
                retrieved_properties=retrieved_properties,
                context_stats=stats
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            answer = "Sorry, I encountered an error while generating the response."

        # Step 4: Return complete response
        return {
            'answer': answer,
            'properties': retrieved_properties,
            'num_results': len(retrieved_properties),
            'filters_applied': filters or {}
        }

    def answer_query(self, query: str, **kwargs) -> str:
        """Simplified interface - just return the answer text"""
        result = self.query(query, **kwargs)
        return result['answer']


if __name__ == "__main__":
    # Test RAG pipeline
    vector_store = PropertyVectorStore()
    vector_store.create_collection()

    llm_handler = LLMHandler()

    pipeline = PropertyRAGPipeline(vector_store, llm_handler)

    # Test query
    test_query = "What's the average price of 2 bedroom apartments?"
    result = pipeline.query(test_query)

    print("Query:", test_query)
    print("\nAnswer:", result['answer'])
    print(f"\nBased on {result['num_results']} properties")
