#!/usr/bin/env python3
"""
Unit test to verify mandatory signature validation logic
Tests the AI agent's signature check without requiring OCR
"""
import sys
import os

# Add Backend to path
sys.path.insert(0, os.path.dirname(__file__))

from money_order.ai.fraud_analysis_agent import FraudAnalysisAgent
from money_order.ai.tools import DataAccessTools

print("=" * 80)
print("UNIT TEST: Mandatory Signature Validation")
print("=" * 80)

# Initialize AI agent
openai_key = os.getenv('OPENAI_API_KEY')
if not openai_key:
    print("\n❌ ERROR: OPENAI_API_KEY not set")
    print("   Skipping AI agent test")
    sys.exit(1)

agent = FraudAnalysisAgent(
    api_key=openai_key,
    model=os.getenv('AI_MODEL', 'gpt-4o-mini'),
    data_tools=None
)

# Test Case 1: Missing signature (should REJECT)
print("\n" + "-" * 80)
print("TEST CASE 1: Money Order with Missing Signature")
print("-" * 80)

ml_analysis = {
    'fraud_risk_score': 0.15,  # Low fraud score from other factors
    'risk_level': 'LOW',
    'model_confidence': 0.85,
    'model_scores': {
        'random_forest': 0.14,
        'xgboost': 0.16,
        'ensemble': 0.15
    },
    'feature_importance': ['Missing signature'],
    'prediction_type': 'mock'
}

extracted_data = {
    'issuer': 'USPS',
    'serial_number': '12345678901',
    'amount': '$500.00',
    'amount_in_words': 'FIVE HUNDRED AND 00/100 DOLLARS',
    'payee': 'John Doe',
    'purchaser': 'Jane Smith',
    'date': '12/08/2024',
    'location': 'New York, NY',
    'signature': None  # ⚠️ Missing signature
}

try:
    result = agent.analyze_fraud(
        ml_analysis=ml_analysis,
        extracted_data=extracted_data,
        customer_id=None,
        is_repeat_customer=False,
        customer_fraud_history=None
    )
    
    print(f"\nRecommendation: {result.get('recommendation')}")
    print(f"Confidence: {result.get('confidence_score', 0):.1%}")
    print(f"Summary: {result.get('summary')}")
    print(f"\nReasoning:")
    for reason in result.get('reasoning', []):
        print(f"  - {reason}")
    
    # Verify result
    if result.get('recommendation') == 'REJECT':
        print("\n✅ TEST PASSED: Missing signature correctly triggered REJECT")
    else:
        print(f"\n❌ TEST FAILED: Expected REJECT, got {result.get('recommendation')}")
        
except Exception as e:
    print(f"\n❌ TEST FAILED with exception: {e}")
    import traceback
    traceback.print_exc()

# Test Case 2: Valid signature (should NOT auto-reject)
print("\n" + "-" * 80)
print("TEST CASE 2: Money Order with Valid Signature")
print("-" * 80)

extracted_data_with_sig = extracted_data.copy()
extracted_data_with_sig['signature'] = 'John Smith'  # ✅ Has signature

try:
    result = agent.analyze_fraud(
        ml_analysis=ml_analysis,
        extracted_data=extracted_data_with_sig,
        customer_id=None,
        is_repeat_customer=False,
        customer_fraud_history=None
    )
    
    print(f"\nRecommendation: {result.get('recommendation')}")
    print(f"Confidence: {result.get('confidence_score', 0):.1%}")
    print(f"Summary: {result.get('summary')}")
    
    # Verify result - should NOT be rejected for signature
    if result.get('recommendation') != 'REJECT' or 'signature' not in result.get('summary', '').lower():
        print("\n✅ TEST PASSED: Valid signature did not trigger auto-reject")
    else:
        print(f"\n❌ TEST FAILED: Valid signature should not trigger auto-reject")
        
except Exception as e:
    print(f"\n❌ TEST FAILED with exception: {e}")
    import traceback
    traceback.print_exc()

# Test Case 3: Empty string signature (should REJECT)
print("\n" + "-" * 80)
print("TEST CASE 3: Money Order with Empty String Signature")
print("-" * 80)

extracted_data_empty_sig = extracted_data.copy()
extracted_data_empty_sig['signature'] = ''  # ⚠️ Empty string

try:
    result = agent.analyze_fraud(
        ml_analysis=ml_analysis,
        extracted_data=extracted_data_empty_sig,
        customer_id=None,
        is_repeat_customer=False,
        customer_fraud_history=None
    )
    
    print(f"\nRecommendation: {result.get('recommendation')}")
    print(f"Confidence: {result.get('confidence_score', 0):.1%}")
    
    # Verify result
    if result.get('recommendation') == 'REJECT':
        print("\n✅ TEST PASSED: Empty signature correctly triggered REJECT")
    else:
        print(f"\n❌ TEST FAILED: Expected REJECT, got {result.get('recommendation')}")
        
except Exception as e:
    print(f"\n❌ TEST FAILED with exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("\nAll tests completed. Review results above.")
print("=" * 80)
