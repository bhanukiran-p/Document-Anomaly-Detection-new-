#!/usr/bin/env python3
"""
Test script to verify Google Vision fallback integration for fraud detection
"""

import logging
from pathlib import Path
from google.cloud import vision
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def test_vision_fallback():
    """Test Vision API fallback in fraud detection"""

    print("=" * 70)
    print("TESTING GOOGLE VISION FALLBACK FOR FRAUD DETECTION")
    print("=" * 70)

    # Get credentials path
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
    if not CREDENTIALS_PATH:
        CREDENTIALS_PATH = os.path.join(BASE_DIR, 'google-credentials.json')

    # Initialize Vision client
    try:
        if os.path.exists(CREDENTIALS_PATH):
            vision_client = vision.ImageAnnotatorClient.from_service_account_file(CREDENTIALS_PATH)
            print("✓ Vision API client initialized")
        else:
            print("⚠️  Credentials file not found, Vision fallback won't be available")
            vision_client = None
    except Exception as e:
        print(f"✗ Failed to initialize Vision API: {e}")
        vision_client = None

    # Test PDFStatementValidator with Vision client
    try:
        from pdf_statement_validator import PDFStatementValidator

        # Test PDF path
        test_pdf = Path("/Users/vikramramanathan/Desktop/Document-Anomaly-Detection-new-/sample bank statement/Bank Fraud Detection Test.pdf")

        if not test_pdf.exists():
            print(f"\n⚠️  Test PDF not found: {test_pdf}")
            print("   Skipping validator test")
            return False

        print(f"\n📄 Testing with: {test_pdf.name}")

        # Create validator WITH Vision client
        validator_with_vision = PDFStatementValidator(str(test_pdf), vision_client=vision_client)
        print(f"✓ Validator initialized with Vision client")

        # Load and validate
        if validator_with_vision.load_pdf():
            print(f"✓ PDF loaded")
            validator_with_vision.extract_text()
            print(f"✓ Text extracted ({len(validator_with_vision.text_content)} pages)")

            if validator_with_vision.vision_used:
                print(f"✓ Vision API was used for text extraction (scanned PDF detected)")
            else:
                print(f"✓ Direct text extraction was successful (no Vision API needed)")

        # Test FraudDetectionService with Vision client
        from fraud_detection_service import FraudDetectionService

        service = FraudDetectionService(vision_client=vision_client)
        print(f"\n✓ FraudDetectionService initialized with Vision client")

        result = service.validate_statement_pdf(str(test_pdf))
        print(f"\n📊 Fraud Detection Results:")
        print(f"   Risk Score: {result.risk_score}/1.0")
        print(f"   Verdict: {result.verdict}")
        print(f"   Is Suspicious: {result.is_suspicious}")

        if result.suspicious_indicators:
            print(f"\n🚫 Suspicious Indicators ({len(result.suspicious_indicators)}):")
            for indicator in result.suspicious_indicators[:5]:
                print(f"   • {indicator}")

        print(f"\n✓ Vision fallback integration test PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print()
    success = test_vision_fallback()
    print("\n" + "=" * 70)
    if success:
        print("✅ VISION FALLBACK INTEGRATION SUCCESSFUL")
    else:
        print("❌ VISION FALLBACK INTEGRATION TEST FAILED")
    print("=" * 70 + "\n")
