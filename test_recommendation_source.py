"""
Test script to verify if fraud recommendations are coming from AI or hardcoded
"""

import os
import sys
import logging

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add Backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Backend'))

from real_time.realtime_agent import RealTimeAnalysisAgent

def test_recommendation_source():
    """Test if recommendations are coming from AI"""

    print("\n" + "="*80)
    print("TESTING FRAUD RECOMMENDATION SOURCE")
    print("="*80)

    # Initialize agent
    agent = RealTimeAnalysisAgent()

    # Check if LLM is available
    if agent.llm is not None:
        print(f"✓ LLM is AVAILABLE")
        print(f"  Model: {agent.model_name}")
        print(f"  API Key: {'Set' if agent.api_key else 'Not Set'}")
    else:
        print(f"✗ LLM is NOT AVAILABLE")
        if not agent.api_key:
            print(f"  Reason: OpenAI API key not set")
        else:
            print(f"  Reason: LangChain not installed or initialization failed")
        return

    # Create sample analysis result
    sample_analysis = {
        'fraud_detection': {
            'fraud_count': 150,
            'fraud_percentage': 15.5,
            'total_amount': 500000.0,
            'total_fraud_amount': 75000.0,
            'fraud_reason_breakdown': [
                {
                    'type': 'Suspicious login',
                    'count': 45,
                    'percentage': 30.0,
                    'total_amount': 25000.0
                },
                {
                    'type': 'Unusual amount',
                    'count': 35,
                    'percentage': 23.3,
                    'total_amount': 30000.0
                },
                {
                    'type': 'Money mule pattern',
                    'count': 25,
                    'percentage': 16.7,
                    'total_amount': 20000.0
                }
            ]
        },
        'transactions': [
            {
                'is_fraud': 1,
                'amount': 5000.0,
                'fraud_probability': 0.95,
                'fraud_reason': 'Suspicious login',
                'merchant': 'Test Merchant',
                'category': 'Online Shopping'
            }
        ],
        'csv_info': {
            'total_count': 1000
        }
    }

    print("\n" + "-"*80)
    print("Generating recommendations from AI...")
    print("-"*80)

    # Generate recommendations
    recommendations = agent.generate_recommendations(sample_analysis)

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if recommendations:
        print(f"✓ Generated {len(recommendations)} recommendations")

        # Check if they are structured objects
        if isinstance(recommendations[0], dict):
            print("✓ Recommendations are STRUCTURED OBJECTS (FROM AI)")
            print(f"\nFirst recommendation:")
            print(f"  Pattern Type: {recommendations[0].get('pattern_type', 'N/A')}")
            print(f"  Severity: {recommendations[0].get('severity', 'N/A')}")
            print(f"  Category: {recommendations[0].get('category', 'N/A')}")
            print(f"  Title: {recommendations[0].get('title', 'N/A')}")
            print(f"  Immediate Actions: {len(recommendations[0].get('immediate_actions', []))} items")
            print(f"  Prevention Steps: {len(recommendations[0].get('prevention_steps', []))} items")
            print(f"\n  Keys in recommendation: {list(recommendations[0].keys())}")

            print("\n" + "="*80)
            print("CONCLUSION: ✓ RECOMMENDATIONS ARE FROM OPENAI/LLM")
            print("="*80)
        elif isinstance(recommendations[0], str):
            print("✗ Recommendations are STRINGS (NOT FROM AI STRUCTURED FORMAT)")
            print(f"\nFirst recommendation:")
            print(f"  {recommendations[0]}")

            print("\n" + "="*80)
            print("CONCLUSION: ✗ RECOMMENDATIONS ARE HARDCODED/FALLBACK")
            print("="*80)
    else:
        print("✗ NO recommendations generated")
        print("\n" + "="*80)
        print("CONCLUSION: ✗ AI RECOMMENDATIONS FAILED")
        print("="*80)

if __name__ == "__main__":
    test_recommendation_source()
