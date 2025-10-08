"""
Data Ingestion Module for Property RAG System
Handles loading, cleaning, and preprocessing property data
"""

import pandas as pd
import logging
from typing import List, Dict, Any
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropertyDataLoader:
    """Loads and preprocesses property data from CSV"""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None

    def load_data(self) -> pd.DataFrame:
        """Load CSV data into DataFrame"""
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"CSV file not found at {self.csv_path}\n"
                f"Please ensure Property_data.csv is in the correct location."
            )
        
        logger.info(f"Loading data from {self.csv_path}")
        try:
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.df)} records")
            return self.df
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

    def clean_data(self) -> pd.DataFrame:
        """Clean and standardize data"""
        logger.info("Cleaning data...")

        # Handle NULL/None values
        self.df['property_type_full_description'] = self.df['property_type_full_description'].fillna(
            self.df['type'].astype(str) + ' with ' +
            self.df['bedrooms'].astype(str) + ' bedroom(s)'
        )

        # Standardize property type
        self.df['type'] = self.df['type'].str.lower().str.strip()

        # Fill missing flood_risk with 'Unknown'
        self.df['flood_risk'] = self.df['flood_risk'].fillna('Unknown')

        # Convert price to numeric
        self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')

        # Drop rows with missing critical fields
        self.df = self.df.dropna(subset=['price', 'bedrooms', 'bathrooms', 'address'])

        # Reset index
        self.df = self.df.reset_index(drop=True)

        logger.info(f"Cleaned data: {len(self.df)} records remaining")
        return self.df

    def create_document_texts(self) -> List[Dict[str, Any]]:
        """Create enriched text documents for embedding"""
        logger.info("Creating document texts for embedding...")

        documents = []

        for idx, row in self.df.iterrows():
            try:
                # Safely convert to int, default to 0 if NaN
                bedrooms = int(row['bedrooms']) if pd.notna(row['bedrooms']) else 0
                bathrooms = int(row['bathrooms']) if pd.notna(row['bathrooms']) else 0
                crime_score = int(row['crime_score_weight']) if pd.notna(row['crime_score_weight']) else 0

                # Create rich text representation
                text = f"""
Property Type: {row['property_type_full_description']}
Location: {row['address']}
Price: £{row['price']:,.0f} per month
Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Flood Risk: {row['flood_risk']}
Crime Score: {crime_score}/10
New Home: {'Yes' if row['is_new_home'] else 'No'}
Listed Date: {row['listing_update_date']}
            """.strip()

                # Create metadata
                metadata = {
                    'id': str(idx),
                    'type': str(row['type']),
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms,
                    'price': float(row['price']),
                    'address': str(row['address']),
                    'crime_score': crime_score,
                    'flood_risk': str(row['flood_risk']),
                    'listing_date': str(row['listing_update_date'])
                }
            except Exception as e:
                logger.warning(f"Skipping row {idx} due to error: {e}")
                continue

            documents.append({
                'text': text,
                'metadata': metadata
            })

        logger.info(f"Created {len(documents)} document texts")
        return documents

    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        if self.df is None:
            return {}

        stats = {
            'total_properties': len(self.df),
            'avg_price': float(self.df['price'].mean()),
            'median_price': float(self.df['price'].median()),
            'min_price': float(self.df['price'].min()),
            'max_price': float(self.df['price'].max()),
            'property_types': self.df['type'].value_counts().to_dict(),
            'avg_bedrooms': float(self.df['bedrooms'].mean()),
            'avg_bathrooms': float(self.df['bathrooms'].mean()),
            'locations': self.df['address'].nunique()
        }

        return stats


if __name__ == "__main__":
    # Test the data loader
    loader = PropertyDataLoader("../Property_data.csv")
    df = loader.load_data()
    df = loader.clean_data()

    print("\n=== Dataset Statistics ===")
    stats = loader.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n=== Sample Documents ===")
    docs = loader.create_document_texts()
    print(docs[0]['text'])
    print("\nMetadata:", docs[0]['metadata'])
