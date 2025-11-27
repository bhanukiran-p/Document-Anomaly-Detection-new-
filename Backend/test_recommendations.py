import sys
import os
from pprint import pprint

# Add Backend to path
sys.path.append(os.path.abspath('/Users/hareenedla/Hareen/Xforia/Document-Anomaly-Detection-new-/Backend'))

from langchain_agent.fraud_analysis_agent import FraudAnalysisAgent

def test_fallback_recommendations():
    print("Testing Fallback Recommendations...")
    agent = FraudAnalysisAgent(api_key="mock_key") # Will fallback because LangChain might not be installed or key is invalid
    
    # Test Low Risk
    print("\n--- Low Risk Case ---")
    low_risk_analysis = agent._fallback_analysis(
        ml_analysis={'fraud_risk_score': 0.1, 'risk_level': 'LOW', 'model_confidence': 0.9},
        extracted_data={}
    )
    pprint(low_risk_analysis['actionable_recommendations'])
    assert len(low_risk_analysis['actionable_recommendations']) == 3
    assert "Proceed with transaction processing" in low_risk_analysis['actionable_recommendations']

    # Test High Risk
    print("\n--- High Risk Case ---")
    high_risk_analysis = agent._fallback_analysis(
        ml_analysis={'fraud_risk_score': 0.9, 'risk_level': 'CRITICAL', 'model_confidence': 0.9},
        extracted_data={}
    )
    pprint(high_risk_analysis['actionable_recommendations'])
    assert len(high_risk_analysis['actionable_recommendations']) == 3
    assert "Decline transaction immediately" in high_risk_analysis['actionable_recommendations']

    # Test Moderate Risk
    print("\n--- Moderate Risk Case ---")
    mod_risk_analysis = agent._fallback_analysis(
        ml_analysis={'fraud_risk_score': 0.5, 'risk_level': 'MEDIUM', 'model_confidence': 0.7},
        extracted_data={}
    )
    pprint(mod_risk_analysis['actionable_recommendations'])
    assert len(mod_risk_analysis['actionable_recommendations']) == 3
    assert "Request secondary form of identification" in mod_risk_analysis['actionable_recommendations']

def test_llm_parsing():
    print("\nTesting LLM Response Parsing...")
    agent = FraudAnalysisAgent(api_key="mock_key")
    
    mock_response = """
    RECOMMENDATION: APPROVE
    CONFIDENCE: 90%
    SUMMARY: Low risk transaction.
    REASONING: No anomalies found.
    KEY_INDICATORS:
    - Valid serial number
    VERIFICATION_NOTES: None.
    ACTIONABLE_RECOMMENDATIONS:
    - Verify customer ID
    - Check watermark
    - Validate amount
    TRAINING_INSIGHTS: Consistent with legitimate patterns.
    HISTORICAL_COMPARISON: Similar to past approved cases.
    """
    
    parsed = agent._parse_llm_response(mock_response, {})
    print("\n--- Parsed Recommendations ---")
    pprint(parsed['actionable_recommendations'])
    
    assert len(parsed['actionable_recommendations']) == 3
    assert "Verify customer ID" in parsed['actionable_recommendations']
    assert "Check watermark" in parsed['actionable_recommendations']

if __name__ == "__main__":
    try:
        test_fallback_recommendations()
        test_llm_parsing()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
