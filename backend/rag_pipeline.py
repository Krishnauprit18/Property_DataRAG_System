"""
RAG Pipeline - Orchestrates the complete RAG workflow
Combines vector search + LLM generation with conversation memory
"""

from typing import Dict, Any, List, Optional
import logging
from vector_store import PropertyVectorStore
from llm_handler import LLMHandler
from global_analytics import GlobalAnalytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyRAGPipeline:
    """Complete RAG pipeline for property queries with conversation support"""

    def __init__(self, vector_store: PropertyVectorStore, llm_handler: LLMHandler, analytics: Optional[GlobalAnalytics] = None):
        self.vector_store = vector_store
        self.llm_handler = llm_handler
        self.analytics = analytics
        logger.info("RAG Pipeline initialized with conversation support")

    def query(
        self,
        user_query: str,
        n_results: int = 5,
        filters: Dict = None,
        conversation_history: List[Dict[str, str]] = None,
        conversation_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete RAG pipeline with conversation context

        Args:
            user_query: Natural language query from user
            n_results: Number of similar properties to retrieve
            filters: Optional filters (min_price, max_price, bedrooms, etc.)
            conversation_history: Previous messages in the conversation
            conversation_context: Extracted context from conversation manager

        Returns:
            Dict with generated response and retrieved properties
        """
        logger.info(f"Processing query: {user_query}")

        # Enhance query with conversation context if available
        enhanced_query = self._enhance_query_with_context(
            user_query, 
            conversation_context
        )

        # Merge filters from context if query seems to be a follow-up
        enhanced_filters = self._enhance_filters_with_context(
            filters,
            conversation_context,
            user_query
        )

        # Step 1: (Optional) Run global analytics for exact dataset-wide metrics when intent matches
        analytics_result = None
        try:
            analytics_intent = self._detect_analytics_intent(user_query)
            if self.analytics and analytics_intent:
                analytics_result = self._run_analytics(user_query, analytics_intent, enhanced_filters)
        except Exception as e:
            logger.warning(f"Analytics computation skipped due to error: {e}")

        # Step 2: Retrieve relevant properties using vector search
        try:
            search_results = self.vector_store.search(
                query=enhanced_query,
                n_results=n_results,
                filters=enhanced_filters
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

        # Build inline citation mapping [#] from retrieved properties
        citations = self._build_citations(retrieved_properties)

        # Step 3: Generate response using LLM with conversation context and analytics summary
        try:
            answer = self.llm_handler.generate_response(
                query=user_query,
                retrieved_properties=retrieved_properties,
                context_stats=stats,
                conversation_history=conversation_history,
                conversation_context=conversation_context,
                analytics_summary=(self.analytics.summarize(analytics_result) if analytics_result else None),
                citations=citations
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            answer = "Sorry, I encountered an error while generating the response."

        # Step 4: Return complete response
        return {
            'answer': answer,
            'properties': retrieved_properties,
            'num_results': len(retrieved_properties),
            'filters_applied': enhanced_filters or {},
            'query_enhanced': enhanced_query != user_query,
            'analytics_used': analytics_result is not None,
            'citations': citations
        }

    def _enhance_query_with_context(
        self,
        query: str,
        conversation_context: Dict[str, Any] = None
    ) -> str:
        """Enhance query with conversation context for better retrieval"""
        if not conversation_context or not conversation_context.get('has_history'):
            return query

        query_lower = query.lower()

        # Check if query is a follow-up (references previous context)
        follow_up_indicators = [
            'what about', 'how about', 'show me', 'those', 'these',
            'same', 'similar', 'also', 'instead', 'but', 'cheaper',
            'expensive', 'bigger', 'smaller', 'other', 'more'
        ]

        is_follow_up = any(indicator in query_lower for indicator in follow_up_indicators)

        if is_follow_up:
            prev_ctx = conversation_context.get('previous_context', {})

            # Add context from previous queries
            context_additions = []

            if prev_ctx.get('mentioned_types'):
                types = list(set(prev_ctx['mentioned_types']))[-2:]  # Last 2 types
                if not any(t in query_lower for t in types):
                    context_additions.extend(types)

            if prev_ctx.get('mentioned_locations'):
                locations = list(set(prev_ctx['mentioned_locations']))[-1:]  # Last location
                if not any(loc in query_lower for loc in locations):
                    context_additions.extend(locations)

            if context_additions:
                enhanced = f"{query} {' '.join(context_additions)}"
                logger.info(f"Enhanced query with context: {enhanced}")
                return enhanced

        return query

    def _enhance_filters_with_context(
        self,
        filters: Optional[Dict],
        conversation_context: Dict[str, Any] = None,
        query: str = ""
    ) -> Optional[Dict]:
        """Enhance filters using conversation context"""
        if not conversation_context or not conversation_context.get('has_history'):
            return filters

        query_lower = query.lower()

        # Check if query is asking for refinement
        refinement_indicators = [
            'cheaper', 'more expensive', 'under', 'less than',
            'same but', 'similar but', 'what about'
        ]

        is_refinement = any(indicator in query_lower for indicator in refinement_indicators)

        if is_refinement:
            prev_ctx = conversation_context.get('previous_context', {})
            mentioned_filters = prev_ctx.get('mentioned_filters', {})

            if mentioned_filters and not filters:
                # Use previous filters as base for refinement
                logger.info(f"Using previous filters as base: {mentioned_filters}")
                return mentioned_filters.copy()

            elif mentioned_filters and filters:
                # Merge with previous filters (current filters take precedence)
                merged_filters = mentioned_filters.copy()
                merged_filters.update(filters)
                logger.info(f"Merged filters: {merged_filters}")
                return merged_filters

        return filters

    def answer_query(self, query: str, **kwargs) -> str:
        """Simplified interface - just return the answer text"""
        result = self.query(query, **kwargs)
        return result['answer']

    # --- Analytics helpers ---
    def _detect_analytics_intent(self, query: str) -> Optional[str]:
        """Rudimentary intent detection for analytics-triggering queries."""
        q = query.lower()
        if any(w in q for w in ["average", "avg", "mean"]):
            return "average_price"
        if any(w in q for w in ["which area has the most crime", "highest crime", "most crime"]):
            return "top_crime_areas"
        if any(w in q for w in ["compare", "vs", "versus"]):
            return "compare_type_prices"
        return None

    def _run_analytics(self, query: str, intent: str, filters: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Execute the appropriate analytics query based on the detected intent and filters."""
        if not self.analytics:
            return None

        # Extract simple hints from query
        q = query.lower()
        bedrooms = None
        for n in [0, 1, 2, 3, 4, 5]:
            if f"{n} bedroom" in q or f"{n}-bedroom" in q or f"{n} bed" in q:
                bedrooms = n
                break

        # Property type hints
        property_types = ["studio", "apartment", "flat", "house", "terraced", "detached", "semi-detached", "bungalow"]
        mentioned_types = [t for t in property_types if t in q]

        # Location hint (basic; relies on vector retrieval for more nuanced cases)
        location_hint = None
        # We can improve by using conversation_context if needed.

        if intent == "average_price":
            return self.analytics.average_price(
                bedrooms=bedrooms,
                property_type_substr=mentioned_types[0] if mentioned_types else None,
                location_substr=location_hint,
                min_price=(filters or {}).get('min_price'),
                max_price=(filters or {}).get('max_price'),
                bathrooms_gte=(filters or {}).get('bathrooms'),
            )
        elif intent == "top_crime_areas":
            return self.analytics.top_crime_areas(by='address', top_n=5, min_listings=25)
        elif intent == "compare_type_prices":
            # crude split for comparisons: find two types mentioned; default to studio vs 2 bed
            if len(mentioned_types) >= 2:
                a, b = mentioned_types[0], mentioned_types[1]
            else:
                # try interpreting digits as bed count vs studio
                a, b = "studio", "2 bed"
            return self.analytics.compare_type_prices(
                a, b, bedrooms=bedrooms, location_substr=location_hint
            )
        return None

    def _build_citations(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create a list of citation items mapping [#] -> property metadata."""
        citations: List[Dict[str, Any]] = []
        for i, prop in enumerate(properties[:10], 1):
            meta = prop if isinstance(prop, dict) else {}
            citations.append({
                'index': i,
                'address': meta.get('address'),
                'price': meta.get('price'),
                'bedrooms': meta.get('bedrooms'),
                'bathrooms': meta.get('bathrooms'),
                'type': meta.get('type'),
                'id': meta.get('id')
            })
        return citations


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
