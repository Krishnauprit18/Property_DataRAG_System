"""
Simple script to load property data into ChromaDB
Handles unique IDs properly
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from data_ingestion import PropertyDataLoader
from vector_store import PropertyVectorStore
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Load property data into vector store"""

    # Paths
    csv_path = Path(__file__).parent.parent / "Property_data.csv"
    db_path = Path(__file__).parent.parent / "backend" / "chroma_db"

    print("=" * 60)
    print("Property Data Loading Script")
    print("=" * 60)

    # Step 1: Load and clean data
    print("\n[1/4] Loading CSV data...")
    loader = PropertyDataLoader(str(csv_path))

    try:
        df = loader.load_data()
        print(f"✓ Loaded {len(df):,} records")
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return

    # Step 2: Clean data
    print("\n[2/4] Cleaning data...")
    try:
        df = loader.clean_data()
        print(f"✓ Cleaned data: {len(df):,} records")
    except Exception as e:
        print(f"✗ Error cleaning data: {e}")
        return

    # Step 3: Create documents
    print("\n[3/4] Creating document embeddings...")
    try:
        documents = loader.create_document_texts()
        print(f"✓ Created {len(documents):,} documents")
    except Exception as e:
        print(f"✗ Error creating documents: {e}")
        return

    # Step 4: Initialize vector store
    print("\n[4/4] Loading into ChromaDB vector store...")
    print("This may take several minutes...")

    try:
        # Delete old collection if exists
        vector_store = PropertyVectorStore(persist_directory=str(db_path))
        try:
            vector_store.delete_collection()
            print("✓ Cleared existing collection")
        except:
            pass

        # Create new collection
        vector_store.create_collection()
        print("✓ Created new collection")

        # Add documents in batches
        print(f"Loading {len(documents):,} properties...")
        vector_store.add_documents(documents, batch_size=100)

        print(f"\n✓ Successfully loaded {len(documents):,} properties!")

        # Show statistics
        stats = vector_store.get_collection_stats()
        print("\n" + "=" * 60)
        print("Database Statistics")
        print("=" * 60)
        print(f"Total documents: {stats.get('total_documents', 0):,}")
        print(f"Collection name: {stats.get('collection_name', 'N/A')}")

        # Show dataset statistics
        print("\n" + "=" * 60)
        print("Dataset Statistics")
        print("=" * 60)
        data_stats = loader.get_statistics()
        print(f"Average price: £{data_stats.get('avg_price', 0):,.2f}/month")
        print(f"Price range: £{data_stats.get('min_price', 0):,.0f} - £{data_stats.get('max_price', 0):,.0f}")
        print(f"Average bedrooms: {data_stats.get('avg_bedrooms', 0):.1f}")
        print(f"Average bathrooms: {data_stats.get('avg_bathrooms', 0):.1f}")
        print(f"Unique locations: {data_stats.get('locations', 0):,}")

        print("\n" + "=" * 60)
        print("✓ Data loading complete!")
        print("=" * 60)
        print("\nYou can now start the backend server:")
        print("  cd backend && python main.py")

    except Exception as e:
        print(f"✗ Error loading into vector store: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
