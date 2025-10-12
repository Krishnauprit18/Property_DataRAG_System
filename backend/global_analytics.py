"""
Global Analytics Module
Provides exact, dataset-wide aggregations for queries like averages,
crime by area, and comparisons between property types.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
import pandas as pd

# Reuse the existing loader for consistent cleaning
from data_ingestion import PropertyDataLoader

logger = logging.getLogger(__name__)


class GlobalAnalytics:
    """In-memory analytics over the full dataset using Pandas."""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df: Optional[pd.DataFrame] = None

        if not self.csv_path.exists():
            raise FileNotFoundError(f"GlobalAnalytics: CSV not found at {self.csv_path}")

        try:
            loader = PropertyDataLoader(str(self.csv_path))
            df = loader.load_data()
            self.df = loader.clean_data()
            logger.info(
                f"GlobalAnalytics initialized with {len(self.df):,} cleaned records from {self.csv_path}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize GlobalAnalytics: {e}")
            raise

    def _apply_common_filters(
        self,
        df: pd.DataFrame,
        *,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bedrooms: Optional[int] = None,
        bathrooms_gte: Optional[int] = None,
        property_type_substr: Optional[str] = None,
        location_substr: Optional[str] = None,
    ) -> pd.DataFrame:
        """Apply common filters to a DataFrame and return filtered DataFrame."""
        result = df
        if min_price is not None:
            result = result[result['price'] >= float(min_price)]
        if max_price is not None:
            result = result[result['price'] <= float(max_price)]
        if bedrooms is not None:
            result = result[result['bedrooms'].astype(int) == int(bedrooms)]
        if bathrooms_gte is not None:
            result = result[result['bathrooms'].astype(int) >= int(bathrooms_gte)]
        if property_type_substr:
            s = property_type_substr.strip().lower()
            result = result[result['type'].astype(str).str.lower().str.contains(s, na=False)]
        if location_substr:
            s = location_substr.strip().lower()
            result = result[result['address'].astype(str).str.lower().str.contains(s, na=False)]
        return result

    def average_price(
        self,
        *,
        bedrooms: Optional[int] = None,
        property_type_substr: Optional[str] = None,
        location_substr: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        bathrooms_gte: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute exact average price for the filtered dataset."""
        df = self._apply_common_filters(
            self.df,
            min_price=min_price,
            max_price=max_price,
            bedrooms=bedrooms,
            bathrooms_gte=bathrooms_gte,
            property_type_substr=property_type_substr,
            location_substr=location_substr,
        )
        count = len(df)
        avg = float(df['price'].mean()) if count > 0 else None
        return {
            'metric': 'average_price',
            'filters': {
                'bedrooms': bedrooms,
                'property_type': property_type_substr,
                'location': location_substr,
                'min_price': min_price,
                'max_price': max_price,
                'bathrooms_gte': bathrooms_gte,
            },
            'count': int(count),
            'average_price': avg,
        }

    def top_crime_areas(
        self,
        *,
        by: str = 'address',
        top_n: int = 5,
        min_listings: int = 10,
    ) -> Dict[str, Any]:
        """Return areas with the highest average crime score.

        Args:
            by: column to group by ('address' or 'laua')
            top_n: number of areas to return
            min_listings: only include groups with at least this many listings to reduce noise
        """
        group_col = by if by in self.df.columns else 'address'
        grouped = (
            self.df.groupby(group_col)['crime_score_weight']
            .agg(['mean', 'count'])
            .rename(columns={'mean': 'avg_crime', 'count': 'listings'})
        )
        filtered = grouped[grouped['listings'] >= int(min_listings)]
        top = filtered.sort_values('avg_crime', ascending=False).head(top_n)
        items = [
            {
                'area': idx,
                'avg_crime_score': float(row['avg_crime']),
                'listings': int(row['listings']),
            }
            for idx, row in top.iterrows()
        ]
        return {
            'metric': 'top_crime_areas',
            'group_by': group_col,
            'top_n': top_n,
            'min_listings': min_listings,
            'results': items,
        }

    def compare_type_prices(
        self,
        type_a_substr: str,
        type_b_substr: str,
        *,
        bedrooms: Optional[int] = None,
        location_substr: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare average prices between two property types (substring matching)."""
        a_df = self._apply_common_filters(
            self.df,
            bedrooms=bedrooms,
            location_substr=location_substr,
            property_type_substr=type_a_substr,
        )
        b_df = self._apply_common_filters(
            self.df,
            bedrooms=bedrooms,
            location_substr=location_substr,
            property_type_substr=type_b_substr,
        )

        a_avg = float(a_df['price'].mean()) if len(a_df) > 0 else None
        b_avg = float(b_df['price'].mean()) if len(b_df) > 0 else None

        return {
            'metric': 'compare_type_prices',
            'types': [type_a_substr, type_b_substr],
            'bedrooms': bedrooms,
            'location': location_substr,
            'counts': {'a': int(len(a_df)), 'b': int(len(b_df))},
            'averages': {'a': a_avg, 'b': b_avg},
        }

    @staticmethod
    def summarize(result: Dict[str, Any]) -> str:
        """Human-readable summary for inclusion in prompts/answers."""
        metric = result.get('metric')
        if metric == 'average_price':
            count = result.get('count', 0)
            avg = result.get('average_price')
            filters = result.get('filters', {})
            desc_parts = []
            if filters.get('bedrooms') is not None:
                desc_parts.append(f"{filters['bedrooms']}-bedroom")
            if filters.get('property_type'):
                desc_parts.append(filters['property_type'])
            if filters.get('location'):
                desc_parts.append(f"in {filters['location']}")
            desc = " ".join(desc_parts) if desc_parts else "all properties"
            if avg is None:
                return f"No matching properties found for {desc}."
            return (
                f"Exact average price for {desc}: £{avg:,.0f}/month based on {count:,} listings."
            )
        elif metric == 'top_crime_areas':
            items = result.get('results', [])
            if not items:
                return "No sufficient data to determine highest crime areas."
            lines = ["Areas with highest average crime score:"]
            for i, item in enumerate(items, 1):
                lines.append(
                    f"{i}. {item['area']} — avg {item['avg_crime_score']:.2f} (n={item['listings']})"
                )
            return "\n".join(lines)
        elif metric == 'compare_type_prices':
            types = result.get('types', ["Type A", "Type B"])  # type: ignore
            avgs = result.get('averages', {})
            counts = result.get('counts', {})
            a_avg = avgs.get('a')
            b_avg = avgs.get('b')
            a_desc = types[0]
            b_desc = types[1] if len(types) > 1 else "Other"
            a_part = (
                f"{a_desc}: £{a_avg:,.0f} (n={counts.get('a', 0):,})" if a_avg is not None else f"{a_desc}: N/A"
            )
            b_part = (
                f"{b_desc}: £{b_avg:,.0f} (n={counts.get('b', 0):,})" if b_avg is not None else f"{b_desc}: N/A"
            )
            return f"Average prices — {a_part}; {b_part}."
        else:
            return ""
