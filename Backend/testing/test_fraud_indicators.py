"""
Test script to demonstrate check fraud indicators.
"""
from utils.check_fraud_indicators import detect_check_fraud_indicators

def test_fraud_indicators():
    print("=" * 80)
    print("Check Fraud Indicators Test")
    print("=" * 80)
    print()

    # Test Case 1: Future dated check with check #0001
    print("Test 1: Future Dated Check with MICR Mismatch")
    print("-" * 80)
    data1 = {
        'check_number': '0150',
        'date': 'November 27, 2025',
        'bank_name': 'Bank of America',
        'payer_name': 'Michael A. Johnson',
        'signature_detected': 'Michael A. Johnson',
        'amount_numeric': 950.25
    }
    raw_text1 = """Michael A. Johnson
456 Maple Avenue
Anytown, USA 67890
Bank of America
November 27, 2025
PAY TO THE ORDER OF John Smith Construction $950.25
Nine hundred fifty and 25/100 DOLLARS
MEMO Testing 123
Michael A. Johnson
111000025 000123456789 0001"""

    indicators1 = detect_check_fraud_indicators(data1, raw_text1)
    print("Detected Indicators:")
    for i, indicator in enumerate(indicators1, 1):
        print(f"{i}. {indicator}")
    print()

    # Test Case 2: Check #0001 (first check)
    print("Test 2: First Check in Checkbook (#0001)")
    print("-" * 80)
    data2 = {
        'check_number': '0001',
        'date': '2025-11-26',
        'bank_name': 'Chase Bank',
        'payer_name': 'John Doe',
        'amount_numeric': 500.00
    }
    raw_text2 = "Chase Bank\nPay to Jane Smith\n$500.00\n021000021 123456789 0001"

    indicators2 = detect_check_fraud_indicators(data2, raw_text2)
    print("Detected Indicators:")
    for i, indicator in enumerate(indicators2, 1):
        print(f"{i}. {indicator}")
    print()

    # Test Case 3: Legitimate check (no fraud indicators)
    print("Test 3: Legitimate Check")
    print("-" * 80)
    data3 = {
        'check_number': '1234',
        'date': '2025-11-20',
        'bank_name': 'Wells Fargo',
        'payer_name': 'Alice Smith',
        'amount_numeric': 250.00
    }
    raw_text3 = "Wells Fargo\nPay to Bob Jones\n$250.00\n111000025 987654321 1234"

    indicators3 = detect_check_fraud_indicators(data3, raw_text3)
    print("Detected Indicators:")
    if indicators3:
        for i, indicator in enumerate(indicators3, 1):
            print(f"{i}. {indicator}")
    else:
        print("No fraud indicators detected - check appears legitimate")
    print()

    print("=" * 80)
    print("Test completed!")
    print("=" * 80)

if __name__ == "__main__":
    test_fraud_indicators()
