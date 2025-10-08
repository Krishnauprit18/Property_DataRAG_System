"""
Vector Store Module using ChromaDB
Handles embedding storage and retrieval
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyVectorStore:
    """ChromaDB vector store for property embeddings"""

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = Path(persist_directory)
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB at {self.persist_directory}")

        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"✅ ChromaDB client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            raise

        # Initialize Sentence-Transformer embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Get or create collection
        self.collection = None
        logger.info(f"Vector store initialized at {self.persist_directory}")

    def create_collection(self, collection_name: str = "property_listings"):
        """Create or get collection"""
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"✅ Collection '{collection_name}' ready with {self.collection.count()} documents")
        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            raise

    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """Add documents to vector store in batches"""
        if not self.collection:
            raise ValueError("Collection not initialized. Call create_collection() first")

        logger.info(f"Adding {len(documents)} documents to vector store...")

        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            ids = [doc['metadata']['id'] for doc in batch]
            texts = [doc['text'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]

            try:
                self.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Added batch {i // batch_size + 1}/{(len(documents) - 1) // batch_size + 1}")
            except Exception as e:
                logger.error(f"Error adding batch: {e}")
                raise

        logger.info(f"Successfully added {len(documents)} documents")

    def search(self, query: str, n_results: int = 5, filters: Dict = None) -> Dict[str, Any]:
        """Search for similar properties"""
        if not self.collection:
            raise ValueError("Collection not initialized")

        try:
            # Build where clause for filtering
            where_clause = None
            if filters:
                where_clause = {}
                if 'min_price' in filters:
                    where_clause['price'] = {'$gte': filters['min_price']}
                if 'max_price' in filters:
                    if 'price' in where_clause:
                        where_clause['price']['$lte'] = filters['max_price']
                    else:
                        where_clause['price'] = {'$lte': filters['max_price']}
                if 'bedrooms' in filters:
                    where_clause['bedrooms'] = filters['bedrooms']
                if 'bathrooms' in filters:
                    where_clause['bathrooms'] = {'$gte': filters['bathrooms']}

            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None
            )

            return {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0]
            }
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.collection:
            return {}

        count = self.collection.count()
        return {
            'total_documents': count,
            'collection_name': self.collection.name
        }

    def delete_collection(self, collection_name: str = "property_listings"):
        """Delete collection"""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")


if __name__ == "__main__":
    # Test vector store
    vector_store = PropertyVectorStore()
    vector_store.create_collection()

    # Test document
    test_docs = [{
        'text': "2 bedroom apartment in London, £2000/month",
        'metadata': {
            'id': 'test_1',
            'type': 'apartment',
            'bedrooms': 2,
            'price': 2000.0,
            'address': 'London'
        }
    }]

    vector_store.add_documents(test_docs)
    print("Collection stats:", vector_store.get_collection_stats())

    # Test search
    results = vector_store.search("affordable 2 bedroom apartment")
    print("\nSearch results:", results)
