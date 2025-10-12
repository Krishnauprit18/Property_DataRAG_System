"""
Streamlit Frontend for Property RAG System
Interactive web interface with conversational memory
"""

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from project root
from pathlib import Path
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Property Search RAG System",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .property-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .stat-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)


def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
        return False
    except Exception as e:
        print(f"Error checking backend: {e}")
        return False


def get_stats():
    """Get database statistics"""
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stats: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def query_properties(query, n_results=5, filters=None, session_id=None):
    """Query the backend API with conversation support"""
    try:
        payload = {
            "query": query,
            "n_results": n_results
        }

        if filters:
            payload.update(filters)
        
        if session_id:
            payload["session_id"] = session_id

        response = requests.post(
            f"{BACKEND_URL}/query",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def get_conversation_history(session_id):
    """Get conversation history for a session"""
    try:
        response = requests.get(
            f"{BACKEND_URL}/conversation/{session_id}/history",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching history: {e}")
        return None


def create_new_conversation():
    """Create a new conversation session"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/conversation/new",
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("session_id")
        return None
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None


def clear_conversation(session_id):
    """Clear a conversation session"""
    try:
        response = requests.delete(
            f"{BACKEND_URL}/conversation/{session_id}",
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error clearing conversation: {e}")
        return False


# Main app
def main():
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = None
    
    if 'conversation_history' not in st.session_state:
        st.session_state['conversation_history'] = []
    
    if 'query_count' not in st.session_state:
        st.session_state['query_count'] = 0

    # Header
    st.markdown('<h1 class="main-header">🏠 Property Search RAG System</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">💬 Now with Conversational Memory!</p>', unsafe_allow_html=True)

    # Check backend health
    if not check_backend_health():
        st.error("⚠️ **Backend server is not running!**")
        st.warning("Please start the FastAPI backend first:")
        st.code("cd backend && python main.py", language="bash")
        st.info(f"Expected backend URL: {BACKEND_URL}")
        st.markdown("---")
        st.markdown("### 🔧 Troubleshooting:")
        st.markdown("""
        1. **Check if backend is running:** Open another terminal and run the backend
        2. **Verify port 8000 is free:** `lsof -i :8000` (on Linux/Mac)
        3. **Check backend URL:** Make sure BACKEND_URL in .env is correct
        4. **View backend logs:** Check terminal where backend is running for errors
        """)
        return

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Conversation Management
        st.markdown("### 💬 Conversation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 New Chat", use_container_width=True):
                # Create new conversation
                new_session_id = create_new_conversation()
                if new_session_id:
                    st.session_state['session_id'] = new_session_id
                    st.session_state['conversation_history'] = []
                    st.session_state['query_count'] = 0
                    if 'last_result' in st.session_state:
                        del st.session_state['last_result']
                    st.success("Started new conversation!")
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                if st.session_state.get('session_id'):
                    if clear_conversation(st.session_state['session_id']):
                        st.session_state['session_id'] = None
                        st.session_state['conversation_history'] = []
                        st.session_state['query_count'] = 0
                        if 'last_result' in st.session_state:
                            del st.session_state['last_result']
                        st.success("Conversation cleared!")
                        st.rerun()

        # Show conversation status
        if st.session_state.get('session_id'):
            st.info(f"🔗 Active Session\n\n{st.session_state['query_count']} messages")
        else:
            st.warning("No active conversation")

        st.markdown("---")

        # Number of results
        n_results = st.slider("Number of results", min_value=1, max_value=20, value=5)

        st.markdown("---")
        st.header("🔍 Filters (Optional)")

        # Price filters
        price_filter = st.checkbox("Filter by Price")
        min_price = None
        max_price = None
        if price_filter:
            col1, col2 = st.columns(2)
            with col1:
                min_price = st.number_input("Min Price (£)", min_value=0, value=0, step=100)
            with col2:
                max_price = st.number_input("Max Price (£)", min_value=0, value=5000, step=100)

        # Bedroom filter
        bedroom_filter = st.checkbox("Filter by Bedrooms")
        bedrooms = None
        if bedroom_filter:
            bedrooms = st.selectbox("Bedrooms", [0, 1, 2, 3, 4, 5])

        # Bathroom filter
        bathroom_filter = st.checkbox("Filter by Bathrooms")
        bathrooms = None
        if bathroom_filter:
            bathrooms = st.selectbox("Min Bathrooms", [1, 2, 3, 4])

        st.markdown("---")

        # Statistics
        st.header("📊 Database Stats")
        stats = get_stats()
        if stats:
            st.metric("Total Properties", f"{stats.get('total_documents', 0):,}")

    # Main content
    st.markdown("### 💬 Chat with the Property Assistant")
    
    # Show conversation history in an expander
    if st.session_state.get('conversation_history'):
        with st.expander(f"📜 Conversation History ({len(st.session_state['conversation_history'])} messages)", expanded=False):
            for msg in st.session_state['conversation_history']:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                if role == 'user':
                    st.markdown(f"**👤 You:** {content}")
                else:
                    st.markdown(f"**🤖 Assistant:** {content}")
                st.markdown("---")

    # Example queries
    with st.expander("📝 Example Queries & Follow-ups"):
        st.markdown("""
        **Initial Queries:**
        - What's the average price of 3 bedroom homes?
        - Find properties under £1000 with 2+ bathrooms
        - Show me studio apartments in London
        
        **Follow-up Queries (with context):**
        - What about cheaper ones? *(continues previous query)*
        - Show me those in Manchester instead *(references previous results)*
        - How about 2 bedrooms? *(refines previous search)*
        - Which of those have the lowest crime score? *(analyzes previous results)*
        """)

    # Query input
    query = st.text_input(
        "Ask me anything about properties:",
        placeholder="e.g., What's the average price of 2 bedroom apartments?",
        key="query_input"
    )

    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    with col2:
        if st.button("📜 View History", use_container_width=True):
            if st.session_state.get('session_id'):
                history_data = get_conversation_history(st.session_state['session_id'])
                if history_data:
                    st.session_state['show_history'] = True

    if search_button:
        if query:
            with st.spinner("Searching properties..."):
                # Build filters
                filters = {}
                if price_filter and min_price is not None:
                    filters['min_price'] = min_price
                if price_filter and max_price is not None:
                    filters['max_price'] = max_price
                if bedroom_filter and bedrooms is not None:
                    filters['bedrooms'] = bedrooms
                if bathroom_filter and bathrooms is not None:
                    filters['bathrooms'] = bathrooms

                # Execute query with session ID
                result = query_properties(
                    query, 
                    n_results, 
                    filters if filters else None,
                    session_id=st.session_state.get('session_id')
                )

                if "error" in result:
                    st.error(f"Error: {result['error']}")
                else:
                    # Update session info
                    st.session_state['session_id'] = result.get('session_id')
                    st.session_state['query_count'] += 2  # User + assistant
                    
                    # Add to local history
                    st.session_state['conversation_history'].append({
                        'role': 'user',
                        'content': query
                    })
                    st.session_state['conversation_history'].append({
                        'role': 'assistant',
                        'content': result.get('answer', 'No answer')
                    })
                    
                    st.session_state['last_result'] = result
                    
                    # Show context indicator
                    if result.get('has_conversation_context'):
                        st.info("💡 Using conversation context from previous messages")
                    
                    st.rerun()
        else:
            st.warning("Please enter a query first!")

    # Display results
    if 'last_result' in st.session_state:
        result = st.session_state['last_result']

        st.markdown("---")

        # Answer section
        st.markdown("### 🤖 Answer")
        st.markdown(f"**{result.get('answer', 'No answer generated')}**")

        st.markdown("---")

        # Properties section
        st.markdown(f"### 🏠 Found {result.get('num_results', 0)} Relevant Properties")

        properties = result.get('properties', [])

        if properties:
            # Display as cards
            for i, prop in enumerate(properties, 1):
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown(f"**{i}. {prop.get('type', 'Property').title()} in {prop.get('address', 'Unknown')}**")
                        st.caption(f"Listed: {prop.get('listing_date', 'N/A')}")

                    with col2:
                        st.metric("Price", f"£{prop.get('price', 0):,.0f}/mo")

                    with col3:
                        st.write(f"🛏️ {prop.get('bedrooms', 0)} bed | 🚿 {prop.get('bathrooms', 0)} bath")

                    # Additional details
                    details_col1, details_col2, details_col3 = st.columns(3)
                    with details_col1:
                        st.caption(f"🚨 Crime Score: {prop.get('crime_score', 'N/A')}/10")
                    with details_col2:
                        st.caption(f"🌊 Flood Risk: {prop.get('flood_risk', 'Unknown')}")
                    with details_col3:
                        st.caption(f"ID: {prop.get('id', 'N/A')}")

                    st.markdown("---")
        else:
            st.info("No properties found matching your criteria.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Property RAG System v2.0 | 💬 With Conversational Memory | "
        "Powered by ChromaDB, Sentence-Transformers & Google Gemini"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
