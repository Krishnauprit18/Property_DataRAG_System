"""
Test script to reproduce filter error
"""

import sys
sys.path.append('backend')

from vector_store import PropertyVectorStore

# Test filters
test_cases = [
    {
        "name": "No filters",
        "filters": None
    },
    {
        "name": "Empty dict",
        "filters": {}
    },
    {
        "name": "Only min_price",
        "filters": {"min_price": 1000}
    },
    {
        "name": "Only max_price",
        "filters": {"max_price": 2000}
    },
    {
        "name": "Price range",
        "filters": {"min_price": 1000, "max_price": 2000}
    },
    {
        "name": "Bedrooms filter",
        "filters": {"bedrooms": 2}
    },
    {
        "name": "Bathrooms filter",
        "filters": {"bathrooms": 1}
    },
    {
        "name": "All filters",
        "filters": {"min_price": 1000, "max_price": 3000, "bedrooms": 3, "bathrooms": 2}
    },
    {
        "name": "Bedrooms = 0 (Studio)",
        "filters": {"bedrooms": 0}
    }
]

print("Testing Vector Store Filters...")
print("=" * 60)

vs = PropertyVectorStore(persist_directory='./backend/chroma_db')
vs.create_collection()

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"Filters: {test['filters']}")
    
    try:
        results = vs.search(
            query="3 bedroom apartment",
            n_results=5,
            filters=test['filters']
        )
        
        print(f"✓ Success - Found {len(results['metadatas'])} properties")
        
        # Show first result if available
        if results['metadatas']:
            prop = results['metadatas'][0]
            print(f"  Sample: {prop.get('bedrooms')} bed, £{prop.get('price')}, {prop.get('address')}")
    
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Filter testing complete!")
