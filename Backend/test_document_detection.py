#!/usr/bin/env python3
"""
Test script for document type detection
Helps verify the detection logic works correctly with your bank statements
"""

from api_server import detect_document_type


def test_detection():
    """Test document detection with various samples"""

    test_cases = [
        {
            'name': 'Bank Statement - Chase',
            'text': '''
            ACCOUNT STATEMENT
            Account Number: 1234567890
            Statement Period: 01/01/2024 - 01/31/2024
            Previous Balance: $5,000.00
            Total Deposits: $2,500.00
            Total Withdrawals: $1,200.00
            Ending Balance: $6,300.00

            TRANSACTION DETAILS:
            01/02/2024 - Check 1001 - $500.00
            01/05/2024 - ACH Transfer - $300.00
            01/10/2024 - Wire Transfer - $2,200.00
            Daily Balance on 01/31/2024: $6,300.00
            ''',
            'expected': 'bank_statement'
        },
        {
            'name': 'Paystub - Sample',
            'text': '''
            PAYCHECK STUB
            Employee ID: EMP001
            Pay Period: 01/01/2024 - 01/15/2024
            Gross Pay: $3,000.00
            Net Pay: $2,250.00
            Federal Withholding: $450.00
            State Withholding: $150.00
            Social Security: $186.00
            Medicare: $43.50
            YTD Gross: $6,000.00
            ''',
            'expected': 'paystub'
        },
        {
            'name': 'Check Sample',
            'text': '''
            PAY TO THE ORDER OF: John Doe
            $1,500.00
            Routing Number: 123456789
            Account Number: 9876543210
            Memo: Invoice Payment
            Check Number: 1001
            Dollars: One Thousand Five Hundred
            ''',
            'expected': 'check'
        },
        {
            'name': 'Bank Statement - Generic',
            'text': '''
            ACCOUNT SUMMARY
            Opening Balance: $10,000.00
            Checking Summary
            Deposits: $5,000.00
            Withdrawals: $3,000.00
            Closing Balance: $12,000.00
            Transaction History:
            Check Number 505
            Wire Transfer Posted
            Daily Balance as of date: $12,000.00
            ''',
            'expected': 'bank_statement'
        },
    ]

    print("=" * 70)
    print("DOCUMENT TYPE DETECTION TEST")
    print("=" * 70)

    passed = 0
    failed = 0

    for test in test_cases:
        result = detect_document_type(test['text'])
        status = "✓ PASS" if result == test['expected'] else "✗ FAIL"

        if result == test['expected']:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}")
        print(f"Test: {test['name']}")
        print(f"Expected: {test['expected']}")
        print(f"Got: {result}")

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)

    return failed == 0


def test_with_custom_text():
    """Test with custom text input"""
    print("\n\nTEST WITH CUSTOM TEXT")
    print("=" * 70)
    print("Paste your bank statement text below (press Ctrl+D when done):")
    print("-" * 70)

    try:
        lines = []
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    custom_text = "\n".join(lines)

    if custom_text.strip():
        result = detect_document_type(custom_text)
        print(f"\nDetected document type: {result}")
    else:
        print("No text provided")


if __name__ == '__main__':
    # Run standard tests
    all_passed = test_detection()

    # Ask if user wants to test with custom text
    try:
        response = input("\n\nWould you like to test with custom text? (y/n): ").lower()
        if response == 'y':
            test_with_custom_text()
    except EOFError:
        print("Skipping custom text test")
