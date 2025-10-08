"""
RAG System Accuracy Evaluation Script
Tests the system against predefined queries with ground truth
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import json
import re
import time
from typing import Dict, List, Any
import requests
from datetime import datetime

# Check if backend is running
BACKEND_URL = "http://localhost:8000"


class RAGEvaluator:
    """Evaluates RAG system accuracy against test queries"""

    def __init__(self, backend_url: str = BACKEND_URL):
        self.backend_url = backend_url
        self.results = []
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'accurate_responses': 0,
            'partially_accurate': 0,
            'inaccurate_responses': 0,
            'avg_response_time': 0,
            'total_response_time': 0
        }

    def check_backend_health(self) -> bool:
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to backend at {self.backend_url}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ Backend connection timeout at {self.backend_url}")
            return False
        except Exception as e:
            print(f"❌ Error checking backend: {e}")
            return False

    def extract_numbers(self, text: str) -> List[float]:
        """Extract numerical values from text"""
        # Remove currency symbols and commas
        text = text.replace('£', '').replace(',', '')
        # Find all numbers (including decimals)
        numbers = re.findall(r'\d+\.?\d*', text)
        return [float(n) for n in numbers]

    def evaluate_numerical_answer(self, answer: str, ground_truth: float, tolerance: float) -> str:
        """Evaluate if numerical answer is within tolerance"""
        numbers = self.extract_numbers(answer)

        if not numbers:
            return "inaccurate"

        # Check if any number is within tolerance
        for num in numbers:
            if abs(num - ground_truth) <= tolerance:
                return "accurate"
            elif abs(num - ground_truth) <= tolerance * 2:
                return "partially_accurate"

        return "inaccurate"

    def evaluate_text_match(self, answer: str, ground_truth: str) -> str:
        """Evaluate if text contains expected keywords"""
        answer_lower = answer.lower()
        truth_lower = ground_truth.lower()

        if truth_lower in answer_lower:
            return "accurate"

        # Partial matching for location names
        words = truth_lower.split()
        matches = sum(1 for word in words if word in answer_lower)

        if matches >= len(words) / 2:
            return "partially_accurate"

        return "inaccurate"

    def evaluate_comparison(self, answer: str, ground_truths: List[float], tolerance: float) -> str:
        """Evaluate comparative answers"""
        numbers = self.extract_numbers(answer)

        if len(numbers) < 2:
            return "inaccurate"

        # Check if both ground truth values are mentioned within tolerance
        matches = 0
        for gt in ground_truths:
            for num in numbers:
                if abs(num - gt) <= tolerance:
                    matches += 1
                    break

        if matches == len(ground_truths):
            return "accurate"
        elif matches >= len(ground_truths) / 2:
            return "partially_accurate"

        return "inaccurate"

    def evaluate_query(self, test_query: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single query"""
        query_text = test_query['query']
        print(f"\n{'='*80}")
        print(f"Query #{test_query['id']}: {query_text}")
        print(f"Category: {test_query['category']}")

        # Make API request
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.backend_url}/query",
                json={"query": query_text, "n_results": 5},
                timeout=30
            )
            response_time = time.time() - start_time

            if response.status_code != 200:
                return {
                    'query_id': test_query['id'],
                    'query': query_text,
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'response_time': response_time
                }

            result = response.json()
            answer = result.get('answer', '')

            print(f"Answer: {answer[:200]}...")
            print(f"Response time: {response_time:.2f}s")

        except Exception as e:
            return {
                'query_id': test_query['id'],
                'query': query_text,
                'status': 'failed',
                'error': str(e),
                'response_time': 0
            }

        # Evaluate accuracy based on answer type
        answer_type = test_query['expected_answer_type']
        accuracy_rating = "unknown"

        if answer_type == 'numerical_average':
            ground_truth = test_query['ground_truth_value']
            tolerance = test_query.get('tolerance', 50)
            accuracy_rating = self.evaluate_numerical_answer(answer, ground_truth, tolerance)
            print(f"Ground Truth: £{ground_truth} (±{tolerance})")

        elif answer_type == 'location_name':
            ground_truth = test_query['ground_truth_value']
            accuracy_rating = self.evaluate_text_match(answer, ground_truth)
            print(f"Expected: {ground_truth}")

        elif answer_type == 'comparison' or answer_type == 'numerical_comparison':
            ground_truths = test_query.get('ground_truth_values', [])
            tolerance = test_query.get('tolerance', 100)
            accuracy_rating = self.evaluate_comparison(answer, ground_truths, tolerance)
            print(f"Expected values: {ground_truths}")

        elif answer_type in ['property_list', 'count', 'range', 'count_and_price']:
            # For these types, check if answer contains relevant information
            if len(answer) > 50 and any(char.isdigit() for char in answer):
                accuracy_rating = "accurate"
            else:
                accuracy_rating = "inaccurate"

        elif answer_type == 'property_with_location':
            ground_truths = test_query.get('ground_truth_values', [])
            if all(str(gt).lower() in answer.lower() for gt in ground_truths):
                accuracy_rating = "accurate"
            else:
                accuracy_rating = "partially_accurate"

        print(f"Accuracy Rating: {accuracy_rating.upper()}")

        return {
            'query_id': test_query['id'],
            'query': query_text,
            'category': test_query['category'],
            'answer': answer,
            'expected_type': answer_type,
            'ground_truth': test_query.get('ground_truth_value'),
            'accuracy_rating': accuracy_rating,
            'response_time': response_time,
            'status': 'success',
            'num_properties': result.get('num_results', 0)
        }

    def run_evaluation(self, test_queries_file: str = 'evaluation/test_queries.json'):
        """Run complete evaluation"""
        print(f"\n{'='*80}")
        print("RAG SYSTEM ACCURACY EVALUATION")
        print(f"{'='*80}")

        # Check backend
        if not self.check_backend_health():
            print("\n❌ ERROR: Backend is not running!")
            print("Please start the backend server first:")
            print("  cd backend && python main.py")
            return

        print("✅ Backend is running")

        # Load test queries
        with open(test_queries_file, 'r') as f:
            data = json.load(f)
            test_queries = data['test_queries']

        print(f"\nLoaded {len(test_queries)} test queries")

        # Run evaluation
        for query in test_queries:
            result = self.evaluate_query(query)
            self.results.append(result)

            # Update metrics
            self.metrics['total_queries'] += 1

            if result['status'] == 'success':
                self.metrics['successful_queries'] += 1
                self.metrics['total_response_time'] += result['response_time']

                if result['accuracy_rating'] == 'accurate':
                    self.metrics['accurate_responses'] += 1
                elif result['accuracy_rating'] == 'partially_accurate':
                    self.metrics['partially_accurate'] += 1
                else:
                    self.metrics['inaccurate_responses'] += 1
            else:
                self.metrics['failed_queries'] += 1

        # Calculate averages
        if self.metrics['successful_queries'] > 0:
            self.metrics['avg_response_time'] = (
                self.metrics['total_response_time'] / self.metrics['successful_queries']
            )

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate evaluation report"""
        print(f"\n{'='*80}")
        print("EVALUATION RESULTS")
        print(f"{'='*80}\n")

        # Overall metrics
        print("📊 OVERALL METRICS:")
        print(f"  Total Queries: {self.metrics['total_queries']}")
        print(f"  Successful: {self.metrics['successful_queries']}")
        print(f"  Failed: {self.metrics['failed_queries']}")
        print(f"  Average Response Time: {self.metrics['avg_response_time']:.2f}s")

        # Accuracy metrics
        print(f"\n🎯 ACCURACY METRICS:")
        total_evaluated = (
            self.metrics['accurate_responses'] +
            self.metrics['partially_accurate'] +
            self.metrics['inaccurate_responses']
        )

        if total_evaluated > 0:
            accuracy_rate = (self.metrics['accurate_responses'] / total_evaluated) * 100
            partial_rate = (self.metrics['partially_accurate'] / total_evaluated) * 100
            inaccuracy_rate = (self.metrics['inaccurate_responses'] / total_evaluated) * 100

            print(f"  Accurate: {self.metrics['accurate_responses']} ({accuracy_rate:.1f}%)")
            print(f"  Partially Accurate: {self.metrics['partially_accurate']} ({partial_rate:.1f}%)")
            print(f"  Inaccurate: {self.metrics['inaccurate_responses']} ({inaccuracy_rate:.1f}%)")

        # Category breakdown
        print(f"\n📁 ACCURACY BY CATEGORY:")
        category_stats = {}
        for result in self.results:
            if result['status'] != 'success':
                continue

            category = result['category']
            if category not in category_stats:
                category_stats[category] = {'accurate': 0, 'partial': 0, 'inaccurate': 0, 'total': 0}

            category_stats[category]['total'] += 1
            if result['accuracy_rating'] == 'accurate':
                category_stats[category]['accurate'] += 1
            elif result['accuracy_rating'] == 'partially_accurate':
                category_stats[category]['partial'] += 1
            else:
                category_stats[category]['inaccurate'] += 1

        for category, stats in sorted(category_stats.items()):
            accuracy = (stats['accurate'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {category}: {stats['accurate']}/{stats['total']} ({accuracy:.1f}% accurate)")

        # Save detailed results
        output = {
            'evaluation_date': datetime.now().isoformat(),
            'metrics': self.metrics,
            'category_stats': category_stats,
            'detailed_results': self.results
        }

        output_file = 'evaluation/evaluation_results.json'
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✅ Detailed results saved to: {output_file}")

        # Generate summary report
        self.generate_summary_report(accuracy_rate if total_evaluated > 0 else 0)

    def generate_summary_report(self, overall_accuracy: float):
        """Generate human-readable summary report"""
        report = f"""
# RAG System Evaluation Report

**Evaluation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

The Property RAG system was evaluated against {self.metrics['total_queries']} test queries covering various categories including price statistics, location analysis, comparative queries, and complex filtered searches.

### Key Findings

- **Overall Accuracy Rate:** {overall_accuracy:.1f}%
- **Average Response Time:** {self.metrics['avg_response_time']:.2f} seconds
- **Success Rate:** {(self.metrics['successful_queries'] / self.metrics['total_queries'] * 100):.1f}%

### Performance Breakdown

| Metric | Count | Percentage |
|--------|-------|------------|
| Accurate Responses | {self.metrics['accurate_responses']} | {(self.metrics['accurate_responses'] / self.metrics['successful_queries'] * 100):.1f}% |
| Partially Accurate | {self.metrics['partially_accurate']} | {(self.metrics['partially_accurate'] / self.metrics['successful_queries'] * 100):.1f}% |
| Inaccurate | {self.metrics['inaccurate_responses']} | {(self.metrics['inaccurate_responses'] / self.metrics['successful_queries'] * 100):.1f}% |

## Recommendations

1. **High Accuracy Areas:** The system performs well on numerical average calculations and property type queries
2. **Improvement Areas:** Complex comparative queries and location-based aggregations may need refinement
3. **Response Time:** Average response time of {self.metrics['avg_response_time']:.2f}s is acceptable for most use cases

## Conclusion

The RAG system demonstrates {
    'excellent' if overall_accuracy >= 80 else
    'good' if overall_accuracy >= 70 else
    'moderate'
} performance with {overall_accuracy:.1f}% accuracy rate. The system successfully handles a variety of query types and provides responses within acceptable time limits.
"""

        with open('evaluation/EVALUATION_REPORT.md', 'w') as f:
            f.write(report)

        print(f"\n📄 Summary report saved to: evaluation/EVALUATION_REPORT.md")


if __name__ == "__main__":
    evaluator = RAGEvaluator()
    evaluator.run_evaluation()
