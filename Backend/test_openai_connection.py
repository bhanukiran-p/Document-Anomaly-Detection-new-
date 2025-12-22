"""
Test OpenAI API connection and real-time agent
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("OpenAI API Connection Test")
print("=" * 60)

# Check API key
api_key = os.getenv('OPENAI_API_KEY')
print(f"\n1. API Key Status:")
if api_key:
    print(f"   ✅ OPENAI_API_KEY is set ({api_key[:10]}...{api_key[-4:]})")
else:
    print(f"   ❌ OPENAI_API_KEY is NOT set")
    sys.exit(1)

# Check model
model = os.getenv('AI_MODEL', 'gpt-4o-mini')
print(f"\n2. Model Configuration:")
print(f"   Model: {model}")

# Try importing LangChain
print(f"\n3. Testing LangChain Import:")
try:
    from langchain_openai import ChatOpenAI
    print(f"   ✅ LangChain installed correctly")
except ImportError as e:
    print(f"   ❌ LangChain import failed: {e}")
    sys.exit(1)

# Initialize LangChain
print(f"\n4. Initializing ChatOpenAI:")
try:
    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        temperature=0.3,
        max_tokens=100,
        request_timeout=30
    )
    print(f"   ✅ ChatOpenAI initialized")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    sys.exit(1)

# Test API call
print(f"\n5. Testing API Call:")
try:
    from langchain_core.messages import HumanMessage

    messages = [HumanMessage(content="Say 'Hello' if you can read this.")]
    response = llm.invoke(messages)

    print(f"   ✅ API call successful")
    print(f"   Response: {response.content}")
except Exception as e:
    print(f"   ❌ API call failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    sys.exit(1)

# Test real-time agent
print(f"\n6. Testing Real-Time Agent:")
try:
    from real_time.realtime_agent import RealTimeAnalysisAgent

    agent = RealTimeAnalysisAgent(api_key=api_key, model=model)

    print(f"   ✅ Agent initialized")
    print(f"   LLM available: {agent.llm is not None}")
    print(f"   Model: {agent.model_name}")
    print(f"   Guardrails enabled: {agent.enable_guardrails}")

except Exception as e:
    print(f"   ❌ Agent initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test recommendation generation with minimal data
print(f"\n7. Testing Recommendation Generation:")
try:
    # Create minimal analysis result
    test_analysis = {
        'fraud_detection': {
            'fraud_count': 5,
            'fraud_percentage': 10.0,
            'total_amount': 10000.0,
            'total_fraud_amount': 1000.0,
            'fraud_reason_breakdown': [
                {'fraud_reason': 'High-Risk Merchant', 'count': 3},
                {'fraud_reason': 'Unusual Amount', 'count': 2}
            ]
        },
        'transactions': []
    }

    recommendations = agent.generate_recommendations(test_analysis)

    print(f"   ✅ Recommendations generated")
    print(f"   Count: {len(recommendations)}")

    if recommendations:
        print(f"\n   First recommendation:")
        print(f"     Title: {recommendations[0].get('title', 'N/A')}")
        print(f"     Description: {recommendations[0].get('description', 'N/A')[:100]}...")

except Exception as e:
    print(f"   ❌ Recommendation generation failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - OpenAI Integration Working!")
print("=" * 60)
print("\nIf you're still not seeing recommendations:")
print("1. Check Backend logs for errors during CSV upload")
print("2. Look for 'AI analysis failed' or 'LLM call failed' messages")
print("3. Check frontend console for API response")
print("=" * 60)
