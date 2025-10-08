"""
Query Analytics and Monitoring System
Tracks queries, performance, and provides insights
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
import threading


class QueryAnalytics:
    """Track and analyze query patterns and performance"""

    def __init__(self, log_file: str = "analytics/query_log.jsonl"):
        self.log_file = log_file
        self.lock = threading.Lock()

        # Ensure analytics directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory stats
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_response_time': 0.0,
            'query_categories': Counter(),
            'popular_filters': Counter(),
            'error_types': Counter()
        }

    def log_query(
        self,
        query: str,
        response_time: float,
        success: bool,
        num_results: int = 0,
        filters: Dict = None,
        error: str = None
    ):
        """Log a query with its metadata"""

        with self.lock:
            # Create log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'response_time': response_time,
                'success': success,
                'num_results': num_results,
                'filters': filters or {},
                'error': error
            }

            # Append to log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            # Update in-memory stats
            self.stats['total_queries'] += 1

            if success:
                self.stats['successful_queries'] += 1
                self.stats['total_response_time'] += response_time
            else:
                self.stats['failed_queries'] += 1
                if error:
                    self.stats['error_types'][error] += 1

            # Track filters used
            if filters:
                for key in filters.keys():
                    self.stats['popular_filters'][key] += 1

            # Categorize query
            category = self._categorize_query(query)
            self.stats['query_categories'][category] += 1

    def _categorize_query(self, query: str) -> str:
        """Categorize query based on content"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['average', 'mean', 'avg']):
            return 'price_statistics'
        elif any(word in query_lower for word in ['find', 'show', 'search']):
            return 'filtered_search'
        elif any(word in query_lower for word in ['compare', 'difference', 'vs']):
            return 'comparative'
        elif any(word in query_lower for word in ['where', 'which area', 'location']):
            return 'location_based'
        elif any(word in query_lower for word in ['crime', 'safety', 'safe']):
            return 'crime_analysis'
        elif any(word in query_lower for word in ['cheap', 'expensive', 'most', 'least']):
            return 'extremes'
        else:
            return 'general'

    def get_stats(self) -> Dict[str, Any]:
        """Get current analytics statistics"""
        with self.lock:
            avg_response_time = 0
            if self.stats['successful_queries'] > 0:
                avg_response_time = (
                    self.stats['total_response_time'] /
                    self.stats['successful_queries']
                )

            return {
                'total_queries': self.stats['total_queries'],
                'successful_queries': self.stats['successful_queries'],
                'failed_queries': self.stats['failed_queries'],
                'success_rate': (
                    self.stats['successful_queries'] / self.stats['total_queries'] * 100
                    if self.stats['total_queries'] > 0 else 0
                ),
                'avg_response_time': avg_response_time,
                'query_categories': dict(self.stats['query_categories']),
                'popular_filters': dict(self.stats['popular_filters']),
                'error_types': dict(self.stats['error_types'])
            }

    def get_recent_queries(self, limit: int = 20) -> List[Dict]:
        """Get recent queries from log"""
        queries = []

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    queries.append(json.loads(line))

            # Return most recent
            return queries[-limit:][::-1]  # Reverse to show newest first

        except FileNotFoundError:
            return []

    def get_slow_queries(self, threshold: float = 3.0, limit: int = 10) -> List[Dict]:
        """Get queries that took longer than threshold"""
        slow_queries = []

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get('response_time', 0) > threshold:
                        slow_queries.append(entry)

            # Sort by response time, descending
            slow_queries.sort(key=lambda x: x['response_time'], reverse=True)
            return slow_queries[:limit]

        except FileNotFoundError:
            return []

    def get_failed_queries(self, limit: int = 10) -> List[Dict]:
        """Get recent failed queries"""
        failed = []

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    if not entry.get('success', False):
                        failed.append(entry)

            return failed[-limit:][::-1]

        except FileNotFoundError:
            return []

    def generate_report(self) -> str:
        """Generate analytics report"""
        stats = self.get_stats()

        report = f"""
# Query Analytics Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

- **Total Queries:** {stats['total_queries']}
- **Successful:** {stats['successful_queries']}
- **Failed:** {stats['failed_queries']}
- **Success Rate:** {stats['success_rate']:.1f}%
- **Avg Response Time:** {stats['avg_response_time']:.3f}s

## Query Categories

"""
        for category, count in sorted(
            stats['query_categories'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            percentage = (count / stats['total_queries'] * 100) if stats['total_queries'] > 0 else 0
            report += f"- **{category}:** {count} ({percentage:.1f}%)\n"

        report += "\n## Popular Filters\n\n"

        if stats['popular_filters']:
            for filter_name, count in sorted(
                stats['popular_filters'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                report += f"- **{filter_name}:** {count} times\n"
        else:
            report += "- No filters used yet\n"

        if stats['error_types']:
            report += "\n## Error Analysis\n\n"
            for error_type, count in sorted(
                stats['error_types'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                report += f"- **{error_type}:** {count} occurrences\n"

        # Recent slow queries
        slow_queries = self.get_slow_queries(threshold=3.0, limit=5)
        if slow_queries:
            report += "\n## Slow Queries (>3s)\n\n"
            for sq in slow_queries:
                report += f"- `{sq['query'][:60]}...` - {sq['response_time']:.2f}s\n"

        return report


class PerformanceMonitor:
    """Monitor system performance metrics"""

    def __init__(self):
        self.metrics = {
            'requests_per_minute': [],
            'response_times': [],
            'error_rate': []
        }
        self.start_time = time.time()

    def record_request(self, response_time: float, success: bool):
        """Record a request for monitoring"""
        current_time = time.time()

        self.metrics['response_times'].append({
            'time': current_time,
            'value': response_time
        })

        if not success:
            self.metrics['error_rate'].append({
                'time': current_time,
                'error': True
            })

    def get_current_metrics(self) -> Dict:
        """Get current performance metrics"""
        current_time = time.time()
        window = 60  # 1 minute window

        # Calculate requests per minute
        recent_requests = [
            r for r in self.metrics['response_times']
            if current_time - r['time'] < window
        ]
        rpm = len(recent_requests)

        # Calculate average response time
        if recent_requests:
            avg_response = sum(r['value'] for r in recent_requests) / len(recent_requests)
        else:
            avg_response = 0

        # Calculate error rate
        recent_errors = [
            e for e in self.metrics['error_rate']
            if current_time - e['time'] < window
        ]
        error_rate = (len(recent_errors) / len(recent_requests) * 100) if recent_requests else 0

        return {
            'requests_per_minute': rpm,
            'avg_response_time': avg_response,
            'error_rate': error_rate,
            'uptime': current_time - self.start_time
        }


# Global instances
analytics = QueryAnalytics()
monitor = PerformanceMonitor()


if __name__ == "__main__":
    # Example usage
    analytics.log_query(
        query="2 bedroom apartments in London",
        response_time=1.5,
        success=True,
        num_results=5,
        filters={'bedrooms': 2}
    )

    print(analytics.generate_report())
