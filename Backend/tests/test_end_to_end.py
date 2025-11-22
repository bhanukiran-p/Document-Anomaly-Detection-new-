#!/usr/bin/env python3
"""
End-to-end test of fraud detection system
"""
import requests
import json
import sys
from pathlib import Path

API_BASE_URL = "http://localhost:5001/api"

def test_fraud_detection():
    """Test fraud detection with PDF"""

    pdf_path = Path("/Users/vikramramanathan/Desktop/Document-Anomaly-Detection-new-/sample bank statement/Bank Fraud Detection Test.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return False

    print("=" * 70)
    print("END-TO-END FRAUD DETECTION TEST")
    print("=" * 70)
    print(f"\n📄 Testing with: {pdf_path.name}\n")

    # Check if backend is responding
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✓ Backend API is responding")
        else:
            print(f"❌ Backend returned status {health.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

    # Test fraud detection endpoint
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}

            print("\n📤 Uploading PDF to fraud detection endpoint...")
            response = requests.post(
                f"{API_BASE_URL}/fraud/validate-pdf",
                files=files,
                timeout=30
            )

        if response.status_code != 200:
            print(f"❌ API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False

        result = response.json()

        print("\n" + "=" * 70)
        print("FRAUD DETECTION RESULTS")
        print("=" * 70)

        # Display results
        data = result.get('data', {})
        print(f"\n📊 Verdict: {data.get('verdict', 'N/A')}")
        print(f"📈 Risk Score: {data.get('risk_score', 'N/A')} / 1.000")
        print(f"⚠️  Suspicious: {data.get('is_suspicious', False)}")

        # Display suspicious indicators
        indicators = data.get('suspicious_indicators', [])
        if indicators:
            print(f"\n🚫 Suspicious Indicators ({len(indicators)}):")
            for indicator in indicators:
                print(f"  • {indicator}")

        # Display warnings
        warnings = data.get('warnings', [])
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning}")

        # Check if ML indicators are present
        ml_indicators = [ind for ind in indicators if "[ML Model]" in ind]
        rule_indicators = [ind for ind in indicators if "[Behavioral]" in ind]

        print(f"\n📊 Detection Method Breakdown:")
        print(f"  • Rule-based (Behavioral): {len(rule_indicators)} indicators")
        print(f"  • ML-based (Ensemble): {len(ml_indicators)} indicators")

        if ml_indicators and rule_indicators:
            print("\n✓ SUCCESS: Both rule-based and ML-based detection are working!")
            return True
        elif rule_indicators:
            print("\n⚠️  PARTIAL: Only rule-based detection working (ML not showing)")
            return False
        else:
            print("\n❌ FAILURE: No fraud indicators detected")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ API request timed out")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Starting fraud detection system test...\n")
    success = test_fraud_detection()
    print("\n" + "=" * 70)
    if success:
        print("✅ TEST PASSED - Fraud detection is fully operational")
    else:
        print("❌ TEST FAILED - Check the output above for details")
    print("=" * 70 + "\n")
    sys.exit(0 if success else 1)
