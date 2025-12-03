"""
Test script to demonstrate enhanced signature detection.
"""
from utils.signature_detector import SignatureDetector

def test_signature_detection():
    detector = SignatureDetector()

    # Test Case 1: Check with signature field present
    print("=" * 60)
    print("Test 1: Check with signature field")
    print("=" * 60)
    data1 = {
        'signature_detected': True,
        'payer_name': 'Sophie B. Micah',
        'bank_name': 'Bank of America'
    }
    raw_text1 = "Bank of America\nPay to Sample Check $347.00\nthree hundred and forty-seven\nAuthorized Signature: Sophie B. Micah"

    is_present, confidence, method = detector.detect_signature(data1, raw_text1)
    print(f"Result: Present={is_present}, Confidence={confidence:.2f}, Method={method}")
    print()

    # Test Case 2: Check without signature field but with name
    print("=" * 60)
    print("Test 2: No signature field but has signer name")
    print("=" * 60)
    data2 = {
        'payer_name': 'John Doe',
        'bank_name': 'Chase Bank'
    }
    raw_text2 = "Chase Bank\nPay to order of Jane Smith\n$500.00\nJohn Doe\nX___________________"

    is_present, confidence, method = detector.detect_signature(data2, raw_text2)
    print(f"Result: Present={is_present}, Confidence={confidence:.2f}, Method={method}")
    print()

    # Test Case 3: Check with no signature indicators
    print("=" * 60)
    print("Test 3: No signature indicators")
    print("=" * 60)
    data3 = {
        'bank_name': 'Wells Fargo'
    }
    raw_text3 = "Wells Fargo\nPay to order of ABC Corp\n$1000.00"

    is_present, confidence, method = detector.detect_signature(data3, raw_text3)
    print(f"Result: Present={is_present}, Confidence={confidence:.2f}, Method={method}")
    print()

    # Test Case 4: Check with signature keyword in text
    print("=" * 60)
    print("Test 4: Signature keyword in OCR text")
    print("=" * 60)
    data4 = {
        'payer_name': 'Alice Smith',
        'bank_name': 'Citibank'
    }
    raw_text4 = "Citibank\nPay to Bob Jones $250.00\nSignature: Alice Smith\n111000025"

    is_present, confidence, method = detector.detect_signature(data4, raw_text4)
    print(f"Result: Present={is_present}, Confidence={confidence:.2f}, Method={method}")
    print()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_signature_detection()
