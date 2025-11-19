#!/usr/bin/env python3
"""
Test script to verify ML integration in fraud detection
"""
import logging
import sys
from fraud_detection_service import FraudDetectionService

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s:%(levelname)s:%(message)s'
)
logger = logging.getLogger(__name__)

def test_ml_integration():
    """Test ML integration with a real PDF"""

    pdf_path = "/Users/vikramramanathan/Desktop/Document-Anomaly-Detection-new-/Backend/temp_uploads/Paystub_from_Xforia_Mail.pdf"

    print("=" * 70)
    print("Testing ML Integration in Fraud Detection")
    print("=" * 70)
    print(f"\nPDF File: {pdf_path}\n")

    try:
        # Initialize fraud detection service
        service = FraudDetectionService()

        # Check if models are loaded
        print(f"XGBoost Model loaded: {service.xgb_model is not None}")
        print(f"Random Forest Model loaded: {service.rf_model is not None}")
        print()

        # Run validation with ML enabled
        print("Running validation with ML enabled...\n")
        result = service.validate_statement_pdf(pdf_path, use_ml=True)

        print("\n" + "=" * 70)
        print("RESULTS:")
        print("=" * 70)
        print(f"PDF Path: {result.pdf_path}")
        print(f"Risk Score: {result.risk_score}")
        print(f"Verdict: {result.verdict}")
        print(f"Is Suspicious: {result.is_suspicious}")
        print(f"\nSuspicious Indicators:")
        for indicator in result.suspicious_indicators:
            print(f"  - {indicator}")

        print(f"\nWarnings:")
        if result.warnings:
            for warning in result.warnings:
                print(f"  - {warning}")
        else:
            print("  (None)")

        # Check if ML indicators are present
        ml_indicators = [ind for ind in result.suspicious_indicators if "[ML Model]" in ind]
        if ml_indicators:
            print(f"\n✓ ML Model indicators found: {len(ml_indicators)}")
        else:
            print(f"\n✗ NO ML Model indicators found - ML may not be running")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_ml_integration()
    sys.exit(0 if success else 1)
