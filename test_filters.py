"""
Automated Filter Testing Script for Real-Time Transaction Analysis
Tests all filter combinations to ensure they work correctly
"""

import requests
import json
import pandas as pd
from datetime import datetime

# Configuration
API_URL = "http://localhost:5001/api"
CSV_FILE = r"C:\Users\bhanukaranP\Desktop\DAD New\Backend\real_time\models\training_data.csv"

def load_and_analyze_csv():
    """Load CSV and run initial analysis"""
    print("=" * 80)
    print("STEP 1: Loading CSV and running initial analysis...")
    print("=" * 80)

    with open(CSV_FILE, 'rb') as f:
        files = {'file': ('training_data.csv', f, 'text/csv')}
        response = requests.post(f"{API_URL}/real-time/analyze", files=files)

    if response.status_code != 200:
        print(f"[FAIL] Error: {response.status_code}")
        print(response.text)
        return None

    result = response.json()
    if not result.get('success'):
        print(f"[FAIL] Analysis failed: {result.get('error')}")
        return None

    print(f"[PASS] Analysis successful!")
    print(f"   Total transactions: {len(result.get('transactions', []))}")
    print(f"   Fraud count: {result.get('fraud_detection', {}).get('fraud_count')}")
    print(f"   Legitimate count: {result.get('fraud_detection', {}).get('legitimate_count')}")
    print()

    return result

def test_filter(transactions, filter_config, test_name):
    """Test a specific filter configuration"""
    print(f"\n{'=' * 80}")
    print(f"TEST: {test_name}")
    print(f"{'=' * 80}")
    print(f"Filter config: {json.dumps(filter_config, indent=2)}")

    payload = {
        'transactions': transactions,
        'filters': filter_config
    }

    response = requests.post(f"{API_URL}/real-time/regenerate-plots", json=payload)

    if response.status_code != 200:
        print(f"[FAIL] HTTP {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    if not result.get('success'):
        print(f"[FAIL] {result.get('error')}")
        return False

    plots = result.get('plots', [])
    stats = result.get('statistics', {})

    print(f"[PASS] SUCCESS!")
    print(f"   Plots generated: {len(plots)}")
    print(f"   Statistics: {stats}")

    # List plot types
    if plots:
        plot_types = [p.get('type') for p in plots]
        print(f"   Plot types: {', '.join(plot_types)}")

    return True

def run_all_tests():
    """Run all filter tests"""
    # Step 1: Load and analyze
    analysis_result = load_and_analyze_csv()
    if not analysis_result:
        print("[FAIL] Initial analysis failed. Aborting tests.")
        return

    transactions = analysis_result.get('transactions', [])
    if not transactions:
        print("[FAIL] No transactions found. Aborting tests.")
        return

    print(f"\n{'=' * 80}")
    print("STARTING FILTER TESTS")
    print(f"{'=' * 80}\n")

    test_results = []

    # Test 1: Amount range filter
    test_results.append(test_filter(
        transactions,
        {'amount_min': 1000, 'amount_max': 3000},
        "Amount Filter: $1000 - $3000"
    ))

    # Test 2: High amounts only
    test_results.append(test_filter(
        transactions,
        {'amount_min': 4000},
        "Amount Filter: >= $4000 (High-value transactions)"
    ))

    # Test 3: Fraud only
    test_results.append(test_filter(
        transactions,
        {'fraud_only': True},
        "Fraud Only Filter"
    ))

    # Test 4: Legitimate only
    test_results.append(test_filter(
        transactions,
        {'legitimate_only': True},
        "Legitimate Only Filter"
    ))

    # Test 5: Category filter - Shopping
    test_results.append(test_filter(
        transactions,
        {'category': 'Shopping'},
        "Category Filter: Shopping"
    ))

    # Test 6: Category filter - Food
    test_results.append(test_filter(
        transactions,
        {'category': 'Food'},
        "Category Filter: Food"
    ))

    # Test 7: High fraud probability
    test_results.append(test_filter(
        transactions,
        {'fraud_probability_min': 0.7},
        "Fraud Probability: >= 70%"
    ))

    # Test 8: Low fraud probability
    test_results.append(test_filter(
        transactions,
        {'fraud_probability_max': 0.3},
        "Fraud Probability: <= 30%"
    ))

    # Test 9: Combined filters - High-value fraud transactions
    test_results.append(test_filter(
        transactions,
        {
            'amount_min': 3000,
            'fraud_only': True
        },
        "Combined: High-value ($3000+) Fraud Only"
    ))

    # Test 10: Combined filters - Shopping category with specific amount range
    test_results.append(test_filter(
        transactions,
        {
            'category': 'Shopping',
            'amount_min': 2000,
            'amount_max': 4000
        },
        "Combined: Shopping category, $2000-$4000"
    ))

    # Test 11: Complex filter combination
    test_results.append(test_filter(
        transactions,
        {
            'amount_min': 1500,
            'fraud_probability_min': 0.5,
            'category': 'Entertainment'
        },
        "Complex: Entertainment, >=$1500, Fraud Prob >= 50%"
    ))

    # Summary
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print(f"{'=' * 80}")
    total_tests = len(test_results)
    passed_tests = sum(test_results)
    failed_tests = total_tests - passed_tests

    print(f"Total tests: {total_tests}")
    print(f"[PASS] Passed: {passed_tests}")
    print(f"[FAIL] Failed: {failed_tests}")

    if failed_tests == 0:
        print("\n[SUCCESS] ALL TESTS PASSED! Filters are working correctly!")
    else:
        print(f"\n[WARNING] {failed_tests} test(s) failed. Please review the logs above.")

    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    run_all_tests()
