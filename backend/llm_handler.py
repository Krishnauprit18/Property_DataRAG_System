"""
LLM Handler Module
Handles interaction with Google Gemini API for response generation
"""

import google.generativeai as genai
import os
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMHandler:
    """Handles LLM-based response generation using Google Gemini"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key or self.api_key.strip() == "":
            logger.warning("⚠️ No GEMINI_API_KEY found or key is empty. Using fallback responses.")
            logger.warning("   To enable AI responses, add your API key to .env file")
            logger.warning("   Get free key from: https://makersuite.google.com/app/apikey")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✅ Gemini LLM initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini: {e}")
                logger.warning("   Falling back to rule-based responses")
                self.model = None

    def generate_response(
        self,
        query: str,
        retrieved_properties: List[Dict[str, Any]],
        context_stats: Dict[str, Any] = None
    ) -> str:
        """Generate a response using retrieved property data"""

        if not self.model:
            # Fallback response without LLM
            return self._generate_fallback_response(query, retrieved_properties)

        # Build context from retrieved properties
        context = self._build_context(retrieved_properties, context_stats)

        # Create prompt
        prompt = f"""You are a helpful real estate assistant. Answer the user's question based on the provided property data.

User Question: {query}

Property Data Context:
{context}

Instructions:
- Answer the question accurately based on the data provided
- Include specific property details and prices when relevant
- If calculating averages or comparisons, show your reasoning
- Cite specific properties by their location when making examples
- If the data doesn't contain enough information, acknowledge it
- Keep responses clear and concise

Answer:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(query, retrieved_properties)

    def _build_context(self, properties: List[Dict[str, Any]], stats: Dict = None) -> str:
        """Build context string from retrieved properties"""
        context_parts = []

        # Add overall statistics if available
        if stats:
            context_parts.append("=== Overall Dataset Statistics ===")
            context_parts.append(f"Total Properties: {stats.get('total_documents', 'N/A')}")
            context_parts.append("")

        # Add retrieved properties
        context_parts.append("=== Most Relevant Properties ===")
        for i, prop in enumerate(properties[:5], 1):
            metadata = prop if isinstance(prop, dict) and 'bedrooms' in prop else prop.get('metadata', {})

            context_parts.append(f"\nProperty {i}:")
            context_parts.append(f"  Location: {metadata.get('address', 'N/A')}")
            context_parts.append(f"  Type: {metadata.get('type', 'N/A')}")
            context_parts.append(f"  Price: £{metadata.get('price', 0):,.0f}/month")
            context_parts.append(f"  Bedrooms: {metadata.get('bedrooms', 'N/A')}")
            context_parts.append(f"  Bathrooms: {metadata.get('bathrooms', 'N/A')}")
            context_parts.append(f"  Crime Score: {metadata.get('crime_score', 'N/A')}/10")

        return "\n".join(context_parts)

    def _generate_fallback_response(self, query: str, properties: List[Dict[str, Any]]) -> str:
        """Generate a simple response without LLM"""
        if not properties:
            return "I couldn't find any properties matching your query. Please try different search criteria."

        response_parts = [f"Found {len(properties)} relevant properties:\n"]

        for i, prop in enumerate(properties[:5], 1):
            metadata = prop if isinstance(prop, dict) and 'bedrooms' in prop else prop.get('metadata', {})

            response_parts.append(
                f"{i}. {metadata.get('type', 'Property')} in {metadata.get('address', 'Unknown')} - "
                f"£{metadata.get('price', 0):,.0f}/month, "
                f"{metadata.get('bedrooms', 0)} bed, {metadata.get('bathrooms', 0)} bath"
            )

        # Calculate average if multiple properties
        if len(properties) > 1:
            avg_price = sum(
                (p.get('metadata', p) if not isinstance(p, dict) or 'price' not in p else p).get('price', 0)
                for p in properties
            ) / len(properties)
            response_parts.append(f"\nAverage price: £{avg_price:,.0f}/month")

        return "\n".join(response_parts)


if __name__ == "__main__":
    # Test LLM handler
    handler = LLMHandler()

    test_properties = [{
        'metadata': {
            'address': 'London',
            'type': 'apartment',
            'price': 2000.0,
            'bedrooms': 2,
            'bathrooms': 1,
            'crime_score': 5
        }
    }]

    response = handler.generate_response(
        "What's the average price?",
        test_properties
    )
    print(response)
