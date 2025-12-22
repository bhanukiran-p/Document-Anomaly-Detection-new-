"""
Quick test for structured recommendations
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from real_time.realtime_agent import RealTimeAnalysisAgent
import json

# Mock analysis result
mock_result = {
    'fraud_detection': {
        'fraud_count': 450,
        'total_count': 500,
        'fraud_percentage': 90.0,
        'total_fraud_amount': 125000.00,
        'total_amount': 150000.00
    },
    'transactions': []
}

print("=" * 80)
print("Testing Structured Recommendations (NO emojis)")
print("=" * 80)

agent = RealTimeAnalysisAgent()
recommendations = agent.generate_recommendations(mock_result)

print(f"\nGenerated {len(recommendations)} structured recommendations:\n")

for i, rec in enumerate(recommendations, 1):
    print(f"\n[RECOMMENDATION {i}]")
    print(f"Title: {rec.get('title', 'N/A')}")
    print(f"Description: {rec.get('description', 'N/A')}")
    print(f"Case Count: {rec.get('case_count', 'N/A')}")
    print(f"Fraud Rate: {rec.get('fraud_rate', 'N/A')}")
    print(f"Total Amount: {rec.get('total_amount', 'N/A')}")

    if rec.get('immediate_actions'):
        print(f"\nImmediate Actions ({len(rec['immediate_actions'])} items):")
        for action in rec['immediate_actions']:
            print(f"  - {action}")

    if rec.get('prevention_steps'):
        print(f"\nPrevention Steps ({len(rec['prevention_steps'])} items):")
        for step in rec['prevention_steps']:
            print(f"  - {step}")

    if rec.get('monitor'):
        print(f"\nMonitor: {rec['monitor']}")

    print("\n" + "-" * 80)

print("\n[SUCCESS] All recommendations generated without emojis!")
print("=" * 80)

# Verify no emojis in output
all_text = json.dumps(recommendations)
emoji_chars = ['✅', '✓', '⚠️', '❌', '✗', '🔍', '📊', '💡']
found_emojis = [emoji for emoji in emoji_chars if emoji in all_text]

if found_emojis:
    print(f"\n[ERROR] Found emojis: {found_emojis}")
else:
    print("\n[VERIFIED] No emojis detected in recommendations")
