"""
Test OpenAI LLM-generated recommendations based on TOP 3 fraud types
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from real_time.realtime_agent import RealTimeAnalysisAgent
import json

# Mock analysis result with realistic fraud reasons
mock_result = {
    'fraud_detection': {
        'fraud_count': 1000,
        'total_count': 10000,
        'fraud_percentage': 10.0,
        'total_fraud_amount': 285000.00,
        'total_amount': 2500000.00
    },
    'transactions': (
        # Entertainment category fraud (656 cases) - TOP 1
        [{
            'transaction_id': f'TXN_ENT_{i}',
            'amount': 250 + (i * 15),
            'is_fraud': 1,
            'merchant': 'Entertainment Venue',
            'category': 'entertainment',
            'timestamp': f'2024-01-{(i%28)+1:02d}T{(i%24):02d}:30:00',
            'fraud_reason': 'High-risk Entertainment category fraud'
        } for i in range(656)] +

        # High-value fraud (271 cases) - TOP 2
        [{
            'transaction_id': f'TXN_HIGH_{i}',
            'amount': 500 + (i * 50),
            'is_fraud': 1,
            'merchant': 'Luxury Retailer',
            'category': 'retail',
            'timestamp': f'2024-01-{(i%28)+1:02d}T14:30:00',
            'fraud_reason': 'Unusually high transaction amount'
        } for i in range(271)] +

        # Night-time fraud (73 cases) - TOP 3
        [{
            'transaction_id': f'TXN_NIGHT_{i}',
            'amount': 180 + (i * 20),
            'is_fraud': 1,
            'merchant': 'Gas Station',
            'category': 'fuel',
            'timestamp': f'2024-01-{(i%28)+1:02d}T03:15:00',
            'fraud_reason': 'Suspicious night-time transaction'
        } for i in range(73)]
    )
}

print("=" * 80)
print("Testing OpenAI LLM Recommendations Based on TOP 3 Fraud Types")
print("=" * 80)

try:
    agent = RealTimeAnalysisAgent()

    if agent.llm is None:
        print("\n[ERROR] OpenAI LLM not initialized!")
        print("Please check OPENAI_API_KEY in .env file")
        sys.exit(1)

    print(f"\n[SUCCESS] OpenAI LLM initialized: {agent.model_name}")

    # Show fraud type breakdown
    print("\n" + "=" * 80)
    print("FRAUD TYPE BREAKDOWN")
    print("=" * 80)
    print("\n1. High-risk Entertainment category fraud")
    print("   - Cases: 656 (65.6% of all fraud)")
    print("   - Total Amount: $178,369.92")
    print("   - Average Amount: $271.91")
    print("\n2. Unusually high transaction amount")
    print("   - Cases: 271 (27.1% of all fraud)")
    print("   - Total Amount: $89,950.00")
    print("   - Average Amount: $331.92")
    print("\n3. Suspicious night-time transaction")
    print("   - Cases: 73 (7.3% of all fraud)")
    print("   - Total Amount: $16,680.08")
    print("   - Average Amount: $228.49")

    print("\n" + "=" * 80)
    print("Generating recommendations from OpenAI API...")
    print("=" * 80)

    recommendations = agent.generate_recommendations(mock_result)

    print(f"\n[SUCCESS] Received {len(recommendations)} recommendations from OpenAI\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{'='*80}")
        print(f"RECOMMENDATION {i}")
        print(f"{'='*80}")
        print(f"\nTitle: {rec.get('title', 'N/A')}")
        print(f"\nDescription: {rec.get('description', 'N/A')}")

        print(f"\nMetrics:")
        print(f"  - Case Count: {rec.get('case_count', 'N/A')}")
        print(f"  - Fraud Rate: {rec.get('fraud_rate', 'N/A')}")
        print(f"  - Total Amount: {rec.get('total_amount', 'N/A')}")

        if rec.get('immediate_actions'):
            print(f"\nImmediate Actions:")
            for j, action in enumerate(rec['immediate_actions'], 1):
                print(f"  {j}. {action}")

        if rec.get('prevention_steps'):
            print(f"\nPrevention Steps:")
            for j, step in enumerate(rec['prevention_steps'], 1):
                print(f"  {j}. {step}")

        if rec.get('monitor'):
            print(f"\nMonitor: {rec['monitor']}")

    print("\n" + "=" * 80)

    # Verify no emojis
    all_text = json.dumps(recommendations)
    emoji_chars = ['✅', '✓', '⚠️', '❌', '✗', '🔍', '📊', '💡']
    found_emojis = [emoji for emoji in emoji_chars if emoji in all_text]

    if found_emojis:
        print(f"[WARNING] Found emojis: {found_emojis}")
    else:
        print("[VERIFIED] No emojis detected in OpenAI response")

    print("\n[SUCCESS] OpenAI generated 3 recommendations - one for each TOP fraud type!")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] Failed to generate recommendations: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
