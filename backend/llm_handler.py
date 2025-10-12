"""
LLM Handler Module
Handles interaction with Google Gemini API for response generation
"""

import google.generativeai as genai
import os
from typing import List, Dict, Any, Optional
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
        context_stats: Dict[str, Any] = None,
        conversation_history: List[Dict[str, str]] = None,
        conversation_context: Dict[str, Any] = None,
        analytics_summary: Optional[str] = None,
        citations: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate a response using retrieved property data with conversation context
        
        Args:
            query: Current user query
            retrieved_properties: Properties retrieved from vector search
            context_stats: Database statistics
            conversation_history: Previous messages in conversation
            conversation_context: Extracted context from previous interactions
        """

        if not self.model:
            # Fallback response without LLM
            base = self._generate_fallback_response(query, retrieved_properties)
            return self._append_citations(base, citations)

        # Build context from retrieved properties
        context = self._build_context(retrieved_properties, context_stats)

        # Build conversation context
        conv_context = self._build_conversation_context(
            conversation_history,
            conversation_context
        )

        # Create enhanced prompt with conversation awareness
        analytics_text = f"\n=== Global Analytics ===\n{analytics_summary}\n" if analytics_summary else ""
        prompt = f"""You are a helpful real estate assistant engaged in a conversation with a user. Answer the user's question based on the provided property data and conversation history.

{conv_context}

Current Question: {query}

Property Data Context:
{context}

{analytics_text}

Instructions:
- Consider the conversation history when answering
- If the user refers to "those properties" or "the previous ones", use context from earlier messages
- If the user asks follow-up questions like "what about cheaper ones?", understand they're refining their previous query
- Answer naturally as if continuing a conversation
- Include specific property details and prices when relevant
- If calculating averages or comparisons, show your reasoning
- Cite specific properties by their location when making examples
- If the data doesn't contain enough information, acknowledge it
- Keep responses clear, concise, and conversational

Answer:"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            return self._append_citations(text, citations)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            base = self._generate_fallback_response(query, retrieved_properties)
            return self._append_citations(base, citations)

    def _build_conversation_context(
        self,
        conversation_history: List[Dict[str, str]] = None,
        conversation_context: Dict[str, Any] = None
    ) -> str:
        """Build conversation context section for prompt"""
        if not conversation_history or not conversation_context:
            return ""

        context_parts = ["=== Conversation Context ==="]

        # Add previous exchanges
        if conversation_history:
            context_parts.append("\nRecent Conversation:")
            # Only include last 3-4 exchanges to keep prompt manageable
            recent = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            for msg in recent:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content'][:150]  # Truncate long messages
                context_parts.append(f"{role}: {content}")

        # Add extracted context
        if conversation_context and conversation_context.get('has_history'):
            prev_ctx = conversation_context.get('previous_context', {})

            if prev_ctx.get('mentioned_filters'):
                context_parts.append(f"\nPrevious filters used: {prev_ctx['mentioned_filters']}")

            if prev_ctx.get('mentioned_locations'):
                context_parts.append(f"Locations discussed: {', '.join(set(prev_ctx['mentioned_locations']))}")

            if prev_ctx.get('mentioned_types'):
                context_parts.append(f"Property types discussed: {', '.join(set(prev_ctx['mentioned_types']))}")

        context_parts.append("")  # Empty line separator
        return "\n".join(context_parts)

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

    def _append_citations(self, text: str, citations: Optional[List[Dict[str, Any]]]) -> str:
        """Append a citation list and inject a few inline markers like [#]."""
        if not citations:
            return text

        # Try to add 2-3 inline markers for the first properties if not already present
        inline = text
        for c in citations[:3]:
            marker = f"[{c['index']}]"
            # If address appears in text, append marker once
            addr = c.get('address')
            if addr and addr in inline and marker not in inline:
                inline = inline.replace(addr, f"{addr} {marker}", 1)

        # Append citation block
        lines = [inline, "", "Sources:"]
        for c in citations:
            addr = c.get('address', 'Unknown')
            price = c.get('price', 0)
            typ = c.get('type', 'Property')
            lines.append(f"[{c['index']}] {typ.title()} – {addr} — £{price:,.0f}/month")
        return "\n".join(lines)


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
