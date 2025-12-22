"""
Test recommendation generation directly
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Force the correct API key BEFORE importing anything else
os.environ['OPENAI_API_KEY'] = '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'

print("=" * 60)
print("Testing AI Recommendation Generation")
print("=" * 60)

# Now import after setting the key
from real_time.realtime_agent import RealTimeAnalysisAgent
import logging

# Enable debug logging
logging.basicConfig(level=logging.INFO)

print("\n1. Initializing agent...")
agent = RealTimeAnalysisAgent(enable_guardrails=True)

print(f"   LLM initialized: {agent.llm is not None}")
print(f"   Model: {agent.model_name}")
print(f"   Guardrails enabled: {agent.enable_guardrails}")

# Create test data
print("\n2. Creating test fraud data...")
test_data = {
    'fraud_detection': {
        'fraud_count': 300,
        'fraud_percentage': 10.0,
        'total_amount': 1000000,
        'total_fraud_amount': 100000,
        'fraud_reason_breakdown': [
            {'fraud_reason': 'Account Takeover', 'count': 150, 'total_amount': 50000},
            {'fraud_reason': 'Card-not-present risk', 'count': 100, 'total_amount': 30000},
            {'fraud_reason': 'Transaction burst', 'count': 50, 'total_amount': 20000}
        ]
    },
    'transactions': []
}

print(f"   Fraud patterns: {len(test_data['fraud_detection']['fraud_reason_breakdown'])}")

print("\n3. Generating recommendations...")
print("   (This may take 30-60 seconds...)")

try:
    recommendations = agent.generate_recommendations(test_data)

    print(f"\n✅ SUCCESS: Generated {len(recommendations)} recommendations")

    print("\n4. Recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"\n   {i}. {rec.get('title', 'No title')}")
        print(f"      Description: {rec.get('description', 'No description')[:100]}...")
        print(f"      Actions: {len(rec.get('immediate_actions', []))} immediate actions")
        print(f"      Prevention: {len(rec.get('prevention_steps', []))} prevention steps")

    if len(recommendations) > 3:
        print(f"\n   ... and {len(recommendations) - 3} more recommendations")

except Exception as e:
    print(f"\n❌ FAILED: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
