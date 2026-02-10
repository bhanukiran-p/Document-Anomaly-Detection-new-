"""
Test script for Real-Time Transaction Analysis Agent
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from real_time.agent_endpoint import AgentAnalysisService
from real_time.agent_tools import TransactionAnalysisTools
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_agent_with_mock_data():
    """Test the agent with mock transaction data"""

    # Mock analysis result
    mock_analysis_result = {
        'csv_info': {
            'total_count': 100,
            'date_range': {
                'start': '2024-01-01T00:00:00',
                'end': '2024-01-31T23:59:59'
            },
            'summary': {
                'total_transactions': 100,
                'total_amount': 250000.00,
                'average_amount': 2500.00
            },
            'columns': [
                {
                    'name': 'transaction_id',
                    'type': 'object',
                    'non_null_count': 100,
                    'null_count': 0,
                    'unique_values': 100
                },
                {
                    'name': 'amount',
                    'type': 'float64',
                    'non_null_count': 100,
                    'null_count': 0,
                    'unique_values': 95,
                    'min': 10.0,
                    'max': 9500.0,
                    'mean': 2500.0
                },
                {
                    'name': 'merchant',
                    'type': 'object',
                    'non_null_count': 100,
                    'null_count': 0,
                    'unique_values': 50
                },
                {
                    'name': 'category',
                    'type': 'object',
                    'non_null_count': 100,
                    'null_count': 0,
                    'unique_values': 8
                },
                {
                    'name': 'timestamp',
                    'type': 'datetime64[ns]',
                    'non_null_count': 100,
                    'null_count': 0,
                    'unique_values': 100
                }
            ]
        },
        'fraud_detection': {
            'fraud_count': 15,
            'legitimate_count': 85,
            'fraud_percentage': 15.0,
            'legitimate_percentage': 85.0,
            'total_fraud_amount': 45000.00,
            'total_legitimate_amount': 205000.00,
            'total_amount': 250000.00,
            'average_fraud_probability': 0.25,
            'model_type': 'ml_ensemble'
        },
        'transactions': [
            {
                'transaction_id': 'TXN_001',
                'customer_id': 'CUST_123',
                'amount': 9500.00,
                'merchant': 'Unknown Merchant',
                'category': 'gambling',
                'timestamp': '2024-01-15T02:30:00',
                'is_fraud': 1,
                'fraud_probability': 0.95,
                'fraud_reason': 'ML Fraud Detection (95% confidence) | High-risk category | Night-time transaction'
            },
            {
                'transaction_id': 'TXN_002',
                'customer_id': 'CUST_456',
                'amount': 7500.00,
                'merchant': 'Crypto Exchange',
                'category': 'cryptocurrency',
                'timestamp': '2024-01-20T23:45:00',
                'is_fraud': 1,
                'fraud_probability': 0.92,
                'fraud_reason': 'ML Fraud Detection (92% confidence) | High-risk category | Unusual amount'
            },
            {
                'transaction_id': 'TXN_003',
                'customer_id': 'CUST_789',
                'amount': 6800.00,
                'merchant': 'Wire Transfer Service',
                'category': 'wire_transfer',
                'timestamp': '2024-01-25T03:15:00',
                'is_fraud': 1,
                'fraud_probability': 0.88,
                'fraud_reason': 'ML Fraud Detection (88% confidence) | High-risk category | Night-time transaction'
            },
            {
                'transaction_id': 'TXN_004',
                'customer_id': 'CUST_101',
                'amount': 150.00,
                'merchant': 'Grocery Store',
                'category': 'retail',
                'timestamp': '2024-01-10T14:30:00',
                'is_fraud': 0,
                'fraud_probability': 0.05,
                'fraud_reason': 'Legitimate transaction (ML confidence: 95%)'
            }
        ] * 25,  # Repeat to make 100 transactions
        'insights': {
            'success': True,
            'statistics': {},
            'plots': [],
            'fraud_patterns': {
                'total_patterns_detected': 3,
                'patterns': [
                    {
                        'type': 'high_value_transactions',
                        'count': 8,
                        'description': '8 high-value fraudulent transactions detected'
                    },
                    {
                        'type': 'night_time_fraud',
                        'count': 6,
                        'description': '6 fraudulent transactions during night hours'
                    },
                    {
                        'type': 'category_concentration',
                        'category': 'gambling',
                        'count': 5,
                        'description': "Most fraud in 'gambling' category (5 cases)"
                    }
                ]
            },
            'recommendations': [
                '[WARNING] MEDIUM ALERT: 15% fraud rate detected',
                '[ACTION] Enhanced monitoring recommended for high-value transactions',
                '[REVIEW] Review gambling and cryptocurrency categories'
            ]
        }
    }

    print("=" * 80)
    print("Testing Real-Time Transaction Analysis Agent")
    print("=" * 80)

    try:
        # Test 1: Create agent service
        print("\n[TEST 1] Creating agent service...")
        agent_service = AgentAnalysisService()
        print("[SUCCESS] Agent service created successfully")

        # Test 2: Create analysis tools
        print("\n[TEST 2] Creating analysis tools...")
        tools = TransactionAnalysisTools(mock_analysis_result)
        print("[SUCCESS] Analysis tools created successfully")

        # Test 3: Get transaction statistics
        print("\n[TEST 3] Getting transaction statistics...")
        stats = tools.get_transaction_statistics()
        print(f"[SUCCESS] Statistics retrieved:")
        print(f"  - Total: {stats['total_transactions']}")
        print(f"  - Fraud: {stats['fraud_count']} ({stats['fraud_percentage']:.2f}%)")
        print(f"  - Fraud Amount: ${stats['fraud_amount']:,.2f}")

        # Test 4: Get top transactions
        print("\n[TEST 4] Getting top fraudulent transactions...")
        top_txns = tools.get_top_transactions(limit=3, fraud_only=True)
        print(f"[SUCCESS] Retrieved {len(top_txns)} top fraudulent transactions")
        for i, txn in enumerate(top_txns, 1):
            print(f"  {i}. ${txn['amount']:,.2f} - {txn['fraud_probability']*100:.1f}% probability")

        # Test 5: Get fraud patterns
        print("\n[TEST 5] Getting fraud patterns...")
        patterns = tools.get_fraud_patterns()
        print(f"[SUCCESS] Detected {patterns['total_patterns']} fraud patterns")
        for pattern in patterns['patterns']:
            print(f"  - {pattern['description']}")

        # Test 6: Get CSV features
        print("\n[TEST 6] Getting CSV features...")
        csv_features = tools.get_csv_features()
        print(f"[SUCCESS] Dataset has {len(csv_features.get('columns', []))} columns")

        # Test 7: Generate comprehensive analysis (without LLM)
        print("\n[TEST 7] Generating comprehensive analysis (fallback mode)...")
        analysis = agent_service.generate_comprehensive_analysis(mock_analysis_result)

        if analysis['success']:
            print("[SUCCESS] Comprehensive analysis generated successfully")
            agent_analysis = analysis['agent_analysis']

            print(f"\n  Top Transactions: {agent_analysis['top_transactions']['count']} analyzed")
            print(f"  CSV Features: {agent_analysis['csv_features']['total_columns']} columns")
            print(f"  Recommendations: {len(agent_analysis['recommendations'])} generated")
            print(f"  Analysis Type: {agent_analysis['analysis_type']}")

            print("\n  Sample Recommendations:")
            for i, rec in enumerate(agent_analysis['recommendations'][:3], 1):
                # Check if structured recommendation
                if isinstance(rec, dict):
                    print(f"\n    [{i}] {rec.get('title', 'N/A')}")
                    print(f"        Description: {rec.get('description', 'N/A')}")
                    if rec.get('immediate_actions'):
                        print(f"        Actions: {len(rec.get('immediate_actions', []))} items")
                    if rec.get('prevention_steps'):
                        print(f"        Prevention: {len(rec.get('prevention_steps', []))} steps")
                else:
                    print(f"    [{i}] {rec}")
        else:
            print(f"[ERROR] Analysis failed: {analysis.get('error')}")

        print("\n" + "=" * 80)
        print("All tests completed successfully!")
        print("=" * 80)

        print("\n[NOTE] To test with LLM capabilities:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Install langchain: pip install langchain langchain-openai")
        print("3. Rerun this test script")

    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        logger.error("Test failed", exc_info=True)
        return False

    return True


if __name__ == '__main__':
    success = test_agent_with_mock_data()
    sys.exit(0 if success else 1)
