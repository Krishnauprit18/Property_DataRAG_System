"""
Calculate ground truth values for evaluation
Analyzes the dataset to get accurate statistics for test queries
"""

import pandas as pd
import numpy as np
from collections import Counter
import json

def calculate_ground_truth():
    """Calculate ground truth statistics from the dataset"""

    print("Loading dataset...")
    df = pd.read_csv('Property_data.csv')

    print(f"Total records: {len(df)}")

    # Clean data
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['bedrooms'] = pd.to_numeric(df['bedrooms'], errors='coerce')
    df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')
    df['crime_score_weight'] = pd.to_numeric(df['crime_score_weight'], errors='coerce')
    df['type'] = df['type'].str.lower().str.strip()

    # Remove invalid rows
    df = df.dropna(subset=['price', 'bedrooms', 'bathrooms'])

    print(f"Valid records after cleaning: {len(df)}")

    ground_truth = {}

    # 1. Average price calculations
    print("\n=== PRICE STATISTICS ===")
    ground_truth['overall_avg_price'] = round(df['price'].mean(), 2)
    print(f"Overall average price: £{ground_truth['overall_avg_price']}")

    # By bedrooms
    for beds in [0, 1, 2, 3, 4]:
        subset = df[df['bedrooms'] == beds]
        if len(subset) > 0:
            avg = round(subset['price'].mean(), 2)
            ground_truth[f'{beds}_bed_avg_price'] = avg
            print(f"{beds} bedroom avg price: £{avg} (n={len(subset)})")

    # 2. Property type statistics
    print("\n=== PROPERTY TYPE STATISTICS ===")
    type_counts = df['type'].value_counts()
    for prop_type in type_counts.head(10).index:
        subset = df[df['type'] == prop_type]
        avg = round(subset['price'].mean(), 2)
        ground_truth[f'{prop_type}_avg_price'] = avg
        ground_truth[f'{prop_type}_count'] = len(subset)
        print(f"{prop_type}: avg £{avg}, count={len(subset)}")

    # 3. Crime score analysis
    print("\n=== CRIME SCORE ANALYSIS ===")
    crime_by_area = df.groupby('address')['crime_score_weight'].mean().sort_values(ascending=False)
    ground_truth['highest_crime_area'] = crime_by_area.index[0]
    ground_truth['highest_crime_score'] = round(crime_by_area.iloc[0], 2)
    print(f"Highest crime area: {crime_by_area.index[0]} (score: {crime_by_area.iloc[0]:.2f})")

    ground_truth['lowest_crime_area'] = crime_by_area.index[-1]
    ground_truth['lowest_crime_score'] = round(crime_by_area.iloc[-1], 2)
    print(f"Lowest crime area: {crime_by_area.index[-1]} (score: {crime_by_area.iloc[-1]:.2f})")

    # 4. Price range queries
    print("\n=== FILTERED QUERIES ===")
    under_1000 = df[df['price'] < 1000]
    ground_truth['properties_under_1000'] = len(under_1000)
    print(f"Properties under £1000: {len(under_1000)}")

    under_1000_2bath = df[(df['price'] < 1000) & (df['bathrooms'] >= 2)]
    ground_truth['under_1000_2bath'] = len(under_1000_2bath)
    print(f"Properties under £1000 with 2+ bathrooms: {len(under_1000_2bath)}")

    # 5. Studio apartments
    studios = df[df['bedrooms'] == 0]
    ground_truth['studio_count'] = len(studios)
    ground_truth['studio_avg_price'] = round(studios['price'].mean(), 2)
    ground_truth['cheapest_studio_price'] = round(studios['price'].min(), 2)
    ground_truth['most_expensive_studio_price'] = round(studios['price'].max(), 2)
    print(f"Studios: count={len(studios)}, avg=£{studios['price'].mean():.2f}, min=£{studios['price'].min():.2f}, max=£{studios['price'].max():.2f}")

    # 6. Comparative analysis
    print("\n=== COMPARATIVE ANALYSIS ===")
    terraced = df[df['type'] == 'terraced']
    detached = df[df['type'] == 'detached']

    if len(terraced) > 0:
        ground_truth['terraced_avg_price'] = round(terraced['price'].mean(), 2)
        print(f"Terraced avg: £{terraced['price'].mean():.2f}")

    if len(detached) > 0:
        ground_truth['detached_avg_price'] = round(detached['price'].mean(), 2)
        print(f"Detached avg: £{detached['price'].mean():.2f}")

    # 7. Flood risk analysis
    print("\n=== FLOOD RISK ANALYSIS ===")
    flood_counts = df['flood_risk'].value_counts()
    print(flood_counts)

    # 8. Price extremes
    print("\n=== PRICE EXTREMES ===")
    most_expensive = df.nlargest(1, 'price').iloc[0]
    cheapest = df.nsmallest(1, 'price').iloc[0]

    ground_truth['most_expensive_price'] = round(most_expensive['price'], 2)
    ground_truth['most_expensive_location'] = most_expensive['address']
    ground_truth['cheapest_price'] = round(cheapest['price'], 2)
    ground_truth['cheapest_location'] = cheapest['address']

    print(f"Most expensive: £{most_expensive['price']} in {most_expensive['address']}")
    print(f"Cheapest: £{cheapest['price']} in {cheapest['address']}")

    # 9. Bathroom statistics
    print("\n=== BATHROOM STATISTICS ===")
    for baths in [1, 2, 3, 4]:
        subset = df[df['bathrooms'] == baths]
        if len(subset) > 0:
            avg = round(subset['price'].mean(), 2)
            ground_truth[f'{baths}_bath_avg_price'] = avg
            ground_truth[f'{baths}_bath_count'] = len(subset)
            print(f"{baths} bathroom: avg £{avg}, count={len(subset)}")

    # 10. Location statistics
    print("\n=== TOP LOCATIONS ===")
    location_counts = df['address'].value_counts().head(10)
    for loc in location_counts.index[:5]:
        subset = df[df['address'] == loc]
        avg = round(subset['price'].mean(), 2)
        ground_truth[f'{loc}_avg_price'] = avg
        ground_truth[f'{loc}_count'] = len(subset)
        print(f"{loc}: avg £{avg}, count={len(subset)}")

    # Convert numpy types to Python native types for JSON serialization
    def convert_to_native(obj):
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif pd.isna(obj):
            return None
        return obj

    ground_truth_cleaned = {k: convert_to_native(v) for k, v in ground_truth.items()}

    # Save to JSON
    output_file = 'ground_truth.json'
    with open(output_file, 'w') as f:
        json.dump(ground_truth_cleaned, f, indent=2)

    print(f"\n✅ Ground truth saved to {output_file}")
    print(f"Total metrics calculated: {len(ground_truth)}")

    return ground_truth

if __name__ == "__main__":
    ground_truth = calculate_ground_truth()
