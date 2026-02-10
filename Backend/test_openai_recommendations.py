"""
Test OpenAI LLM-generated recommendations
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
    'transactions': [
        {
            'transaction_id': 'TXN001',
            'amount': 5000,
            'is_fraud': 1,
            'merchant': 'Unknown',
            'category': 'gambling',
            'timestamp': '2024-01-15T02:30:00'
        }
    ] * 10  # Mock 10 fraud transactions
}

print("=" * 80)
print("Testing OpenAI LLM Recommendations (NO Fallback)")
print("=" * 80)

try:
    agent = RealTimeAnalysisAgent()

    if agent.llm is None:
        print("\n[ERROR] OpenAI LLM not initialized!")
        print("Please check:")
        print("  1. OPENAI_API_KEY is set in .env file")
        print("  2. LangChain is installed: pip install langchain langchain-openai")
        sys.exit(1)

    print(f"\n[SUCCESS] OpenAI LLM initialized: {agent.model_name}")
    print("\nGenerating recommendations from OpenAI API...")

    recommendations = agent.generate_recommendations(mock_result)

    print(f"\n[SUCCESS] Received {len(recommendations)} recommendations from OpenAI\n")

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{'='*80}")
        print(f"RECOMMENDATION {i}")
        print(f"{'='*80}")
        print(f"Title: {rec.get('title', 'N/A')}")
        print(f"Description: {rec.get('description', 'N/A')}")
        print(f"\nMetrics:")
        print(f"  - Case Count: {rec.get('case_count', 'N/A')}")
        print(f"  - Fraud Rate: {rec.get('fraud_rate', 'N/A')}")
        print(f"  - Total Amount: {rec.get('total_amount', 'N/A')}")

        if rec.get('immediate_actions'):
            print(f"\nImmediate Actions ({len(rec['immediate_actions'])} items):")
            for j, action in enumerate(rec['immediate_actions'], 1):
                print(f"  {j}. {action}")

        if rec.get('prevention_steps'):
            print(f"\nPrevention Steps ({len(rec['prevention_steps'])} items):")
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

    print("\n[SUCCESS] OpenAI LLM recommendations generated successfully!")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] Failed to generate recommendations: {e}")
    print("\nPossible issues:")
    print("  1. OpenAI API key is invalid or expired")
    print("  2. Insufficient credits in OpenAI account")
    print("  3. Network connectivity issues")
    print("  4. OpenAI API rate limits exceeded")
    sys.exit(1)
