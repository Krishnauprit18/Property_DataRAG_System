"""
Load a SAMPLE of property data for quick testing (1000 records)
For production, use load_data_simple.py with full dataset
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "backend"))

from data_ingestion import PropertyDataLoader
from vector_store import PropertyVectorStore
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    csv_path = Path(__file__).parent.parent / "Property_data.csv"
    db_path = Path(__file__).parent.parent / "backend" / "chroma_db"

    print("\n" + "=" * 60)
    print("Loading SAMPLE Property Data (1000 records for testing)")
    print("=" * 60)

    # Load data
    loader = PropertyDataLoader(str(csv_path))
    df = loader.load_data()

    # Take sample
    df = df.head(1000)
    loader.df = df
    print(f"✓ Using {len(df):,} sample records")

    # Clean
    df = loader.clean_data()
    print(f"✓ Cleaned: {len(df):,} records")

    # Create documents
    documents = loader.create_document_texts()
    print(f"✓ Created {len(documents):,} documents")

    # Load to vector store
    print("✓ Loading to ChromaDB...")
    vector_store = PropertyVectorStore(persist_directory=str(db_path))

    try:
        vector_store.delete_collection()
    except:
        pass

    vector_store.create_collection()
    vector_store.add_documents(documents, batch_size=100)

    stats = vector_store.get_collection_stats()
    print(f"\n✓ Loaded {stats['total_documents']:,} properties to ChromaDB")
    print("\n" + "=" * 60)
    print("✓ Sample data loaded successfully!")
    print("=" * 60)
    print("\nStart backend: cd backend && python main.py")
    print("Start frontend: streamlit run frontend/app.py\n")

if __name__ == "__main__":
    main()
