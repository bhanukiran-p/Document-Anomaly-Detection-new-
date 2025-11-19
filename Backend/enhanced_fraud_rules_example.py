"""
Example Usage of Enhanced Fraud Detection Rules Engine

This demonstrates how to use the enhanced rule engine with real data.
"""

from enhanced_fraud_rules import EnhancedFraudRuleEngine
import json


def example_legitimate_statement():
    """Example: Legitimate bank statement."""
    engine = EnhancedFraudRuleEngine()

    # Metadata
    metadata = {
        '/Creator': 'Bank Application v1.0',
        '/Producer': 'System Generated PDF',
        '/CreationDate': '20240119000000',
        '/ModDate': '20240119000000',
    }

    # Sample transactions (normal pattern)
    transactions = [
        {'date': '01/15/2024', 'description': 'Direct Deposit - EMPLOYER', 'amount': 3500, 'type': 'credit', 'balance': 6500},
        {'date': '01/16/2024', 'description': 'WALMART SUPERCENTER', 'amount': 125.50, 'type': 'debit', 'balance': 6374.50},
        {'date': '01/17/2024', 'description': 'ELECTRIC UTILITY CO', 'amount': 85.20, 'type': 'debit', 'balance': 6289.30},
        {'date': '01/18/2024', 'description': 'AMAZON.COM', 'amount': 45.99, 'type': 'debit', 'balance': 6243.31},
        {'date': '01/20/2024', 'description': 'NETFLIX SUBSCRIPTION', 'amount': 15.99, 'type': 'debit', 'balance': 6227.32},
    ]

    # Balances
    balances = {
        'opening_balance': 3000,
        'credits': 3500,
        'debits': 272.68,
        'closing_balance': 6227.32
    }

    # Text content
    text_content = """
    Chase Bank Statement
    Account: ****5678
    Statement Period: January 1-31, 2024

    Beginning Balance: $3,000.00
    Credits: $3,500.00
    Debits: $272.68
    Ending Balance: $6,227.32
    """

    fonts = ['Helvetica']

    # Run analysis
    results = engine.run_all_checks(metadata, text_content, transactions, balances, fonts)

    print("=" * 70)
    print("EXAMPLE 1: LEGITIMATE STATEMENT")
    print("=" * 70)
    print(results['summary'])
    print(f"\nDetailed Results:")
    print(json.dumps(results['details'], indent=2))
    print()


def example_suspicious_statement():
    """Example: Suspicious statement with fraud indicators."""
    engine = EnhancedFraudRuleEngine()

    # Metadata (edited with Photoshop!)
    metadata = {
        '/Creator': 'Adobe Photoshop 2024',
        '/Producer': 'PDF Expert - Edited',
        '/CreationDate': '20250215000000',  # Future date!
        '/ModDate': '20250216000000',
    }

    # Suspicious transactions
    transactions = [
        {'date': '01/15/2024', 'description': 'International Wire Transfer', 'amount': 25000, 'type': 'debit', 'balance': -5000},
        {'date': '01/16/2024', 'description': 'BITCOIN PURCHASE', 'amount': 5000, 'type': 'debit', 'balance': -10000},
        {'date': '01/17/2024', 'description': 'Withdrawal', 'amount': 1000, 'type': 'debit', 'balance': -11000},
        {'date': '01/17/2024', 'description': 'Withdrawal', 'amount': 1000, 'type': 'debit', 'balance': -12000},
        {'date': '01/17/2024', 'description': 'Withdrawal', 'amount': 1000, 'type': 'debit', 'balance': -13000},
        {'date': '01/18/2024', 'description': 'Withdrawal', 'amount': 5000, 'type': 'debit', 'balance': -18000},
        {'date': '01/19/2024', 'description': 'WESTERN UNION', 'amount': 2500, 'type': 'debit', 'balance': -20500},
        {'date': '01/20/2024', 'description': 'OFFSHORE ACCOUNT TRANSFER', 'amount': 10000, 'type': 'debit', 'balance': -30500},
    ]

    # Balance mismatch (intentional error)
    balances = {
        'opening_balance': 10000,
        'credits': 5000,
        'debits': 50000,
        'closing_balance': -35000,  # Wrong calculation
    }

    # Text content with fraud keywords
    text_content = """
    Bank Statement
    International Wire Transfer: $25,000
    BITCOIN PURCHASE: $5,000
    Multiple structured withdrawals: $1,000
    WESTERN UNION: $2,500
    OFFSHORE ACCOUNT TRANSFER: $10,000
    CRYPTO TRANSACTION
    DARK WEB MARKETPLACE PURCHASE
    """

    fonts = ['Helvetica', 'Arial', 'Times New Roman', 'Courier', 'Symbol']

    # Run analysis
    results = engine.run_all_checks(metadata, text_content, transactions, balances, fonts)

    print("=" * 70)
    print("EXAMPLE 2: SUSPICIOUS STATEMENT (MULTIPLE FRAUD INDICATORS)")
    print("=" * 70)
    print(results['summary'])
    print(f"\nTriggered Rules ({len(results['rules_triggered'])} total):")
    for i, rule in enumerate(results['rules_triggered'], 1):
        print(f"\n  Rule {i}: {rule['rule_id']}")
        print(f"    Severity: {rule['severity'].upper()}")
        print(f"    Explanation: {rule['explanation']}")
        if rule['evidence']:
            print(f"    Evidence: {rule['evidence'][:2]}")
    print()


def example_edited_statement():
    """Example: Legitimate statement that was edited."""
    engine = EnhancedFraudRuleEngine()

    metadata = {
        '/Creator': 'PDF Expert',
        '/Producer': 'SmallPDF - Edited',
        '/CreationDate': '20240101000000',
        '/ModDate': '20240115000000',  # Recently modified
    }

    transactions = [
        {'date': '01/01/2024', 'description': 'Opening Balance', 'amount': 5000, 'type': 'credit', 'balance': 5000},
        {'date': '01/05/2024', 'description': 'Deposit', 'amount': 3000, 'type': 'credit', 'balance': 8000},
        {'date': '01/10/2024', 'description': 'Withdrawal', 'amount': 2000, 'type': 'debit', 'balance': 6000},
        {'date': '01/10/2024', 'description': 'Withdrawal', 'amount': 2000, 'type': 'debit', 'balance': 4000},
        {'date': '01/10/2024', 'description': 'Withdrawal', 'amount': 2000, 'type': 'debit', 'balance': 2000},
        {'date': '01/10/2024', 'description': 'Withdrawal', 'amount': 1000, 'type': 'debit', 'balance': 1000},
    ]

    balances = {
        'opening_balance': 5000,
        'credits': 3000,
        'debits': 7000,
        'closing_balance': 1000
    }

    text_content = """
    Statement Details
    Multiple withdrawals detected
    Unusual spacing in transaction details:          Withdrawal 1
                                                     Withdrawal 2
                                                     Withdrawal 3
    """

    fonts = ['Helvetica', 'Times']

    results = engine.run_all_checks(metadata, text_content, transactions, balances, fonts)

    print("=" * 70)
    print("EXAMPLE 3: EDITED STATEMENT (PROBABLE MODIFICATION)")
    print("=" * 70)
    print(results['summary'])
    print(f"\nDetailed Analysis:")
    print(json.dumps({
        'fraud_score': results['fraud_score'],
        'fraud_level': results['fraud_level'],
        'rules_triggered': len(results['rules_triggered']),
        'categories_affected': results['details']['categories_affected']
    }, indent=2))
    print()


if __name__ == '__main__':
    example_legitimate_statement()
    example_suspicious_statement()
    example_edited_statement()

    print("=" * 70)
    print("RULE ENGINE CAPABILITIES SUMMARY")
    print("=" * 70)
    print("""
✅ BEHAVIORAL CHECKS:
   - Transaction sequence anomalies (deposit → rapid withdrawals)
   - Transaction velocity detection (50+ transactions = suspicious)
   - Round-amount pattern detection (structuring indicator)
   - Late-night/weekend activity monitoring
   - Fraud keyword detection (crypto, wire transfer, etc.)

✅ STRUCTURAL CHECKS:
   - Balance consistency verification (opening + credits - debits = closing)
   - Impossible negative balance detection
   - Duplicate transaction row detection (copy-paste fraud)

✅ METADATA CHECKS:
   - Suspicious creator/editor tool detection (Photoshop, PDF Expert, etc.)
   - Metadata completeness validation
   - Impossible future date detection
   - Modification tracking

✅ FORMATTING CHECKS:
   - Font consistency analysis
   - Line spacing anomaly detection
   - Text alignment shift detection

✅ SCORING & REPORTING:
   - Weighted scoring system (0-100 scale)
   - Category-based analysis
   - Human-readable explanations
   - Evidence-based findings
   - JSON-structured output
    """)
