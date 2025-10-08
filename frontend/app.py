"""
Streamlit Frontend for Property RAG System
Interactive web interface for querying property data
"""

import streamlit as st
import requests
import os
from dotenv import load_dotenv

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


def query_properties(query, n_results=5, filters=None):
    """Query the backend API"""
    try:
        payload = {
            "query": query,
            "n_results": n_results
        }

        if filters:
            payload.update(filters)

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


# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">🏠 Property Search RAG System</h1>', unsafe_allow_html=True)

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
    st.markdown("### 💬 Ask me anything about properties!")

    # Example queries
    with st.expander("📝 Example Queries"):
        st.markdown("""
        - What's the average price of 3 bedroom homes?
        - Find properties under £1000 with 2+ bathrooms
        - Which area has the highest crime score?
        - Show me the cheapest studio apartments
        - Compare prices between terraced and detached houses
        - What are the most expensive properties in London?
        - Find 2 bedroom apartments with low flood risk
        """)

    # Query input
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., What's the average price of 2 bedroom apartments?",
        key="query_input"
    )

    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔍 Search", type="primary", use_container_width=True):
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

                    # Execute query
                    result = query_properties(query, n_results, filters if filters else None)

                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.session_state['last_result'] = result
            else:
                st.warning("Please enter a query first!")

    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.clear()
            st.rerun()

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
        "Property RAG System | Powered by ChromaDB, Sentence-Transformers & Google Gemini"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
