"""
Bank statement parsing utilities.
"""
import re
import logging

logger = logging.getLogger(__name__)


def safe_parse_currency(value):
    """
    Convert currency-like values to float.

    Args:
        value: Currency value to parse

    Returns:
        float or None: Parsed value or None if parsing fails
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    negative = False
    if '(' in text and ')' in text:
        negative = True

    text = text.replace('(', '').replace(')', '')
    text = text.replace('CR', '').replace('DR', '').replace('cr', '').replace('dr', '')
    text = text.replace('$', '').replace(',', '').strip()

    if not text:
        return None

    try:
        number = float(text)
        if negative:
            number = -abs(number)
        return number
    except ValueError:
        return None


def format_currency(value):
    """
    Return a currency string or None.

    Args:
        value: Numeric value to format

    Returns:
        str or None: Formatted currency string
    """
    if value is None:
        return None
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return None


def mask_account_number(number):
    """
    Mask account number showing only last 4 digits.

    Args:
        number: Account number to mask

    Returns:
        str or None: Masked account number
    """
    if not number:
        return None
    digits = re.sub(r'\D', '', str(number))
    if len(digits) < 4:
        return number
    return f"****{digits[-4:]}"


def extract_transactions(raw_text):
    """
    Extract transactions from raw OCR text.

    Args:
        raw_text: Raw text from bank statement

    Returns:
        list: List of transaction dictionaries
    """
    transactions = []
    if not raw_text:
        return transactions

    pattern = re.compile(
        r'(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+(?P<desc>.+?)\s+(?P<amount>[-\(\)\$0-9,\.]+)(?:\s+(?P<balance>[-\(\)\$0-9,\.]+))?$'
    )

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if match:
            amount_value = safe_parse_currency(match.group('amount'))
            balance_value = safe_parse_currency(match.group('balance')) if match.group('balance') else None

            transactions.append({
                'date': match.group('date'),
                'description': match.group('desc').strip(),
                'amount': format_currency(amount_value) if amount_value is not None else match.group('amount'),
                'amount_value': amount_value if amount_value is not None else 0.0,
                'balance': format_currency(balance_value) if balance_value is not None else match.group('balance')
            })

    return transactions


def parse_bank_statement_text(raw_text):
    """
    Parse bank statement text to extract structured data.

    Args:
        raw_text: Raw OCR text from bank statement

    Returns:
        dict: Structured bank statement data
    """
    data = {
        'bank_name': None,
        'account_holder': None,
        'account_number': None,
        'statement_period': None,
        'balances': {
            'opening_balance': None,
            'ending_balance': None,
            'available_balance': None,
            'current_balance': None
        },
        'summary': {
            'transaction_count': 0,
            'total_credits': 0.0,
            'total_debits': 0.0,
            'net_activity': 0.0,
            'confidence': 40.0
        },
        'transactions': []
    }

    if not raw_text:
        return data

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Extract bank name (first line)
    if lines:
        data['bank_name'] = lines[0][:80]

    # Extract account holder
    holder_match = re.search(r'account holder[:\s]+([A-Z][\w\s,\.-]+)', raw_text, re.IGNORECASE)
    if holder_match:
        data['account_holder'] = holder_match.group(1).strip()

    # Extract account number
    acct_match = re.search(r'account\s+(?:number|no\.|#)[:\s\-]*([\*\dxX]{4,})', raw_text, re.IGNORECASE)
    if acct_match:
        data['account_number'] = mask_account_number(acct_match.group(1))

    # Extract statement period
    period_match = re.search(r'statement\s+period[:\s]+([^\n]+)', raw_text, re.IGNORECASE)
    if period_match:
        data['statement_period'] = period_match.group(1).strip()

    # Extract balances
    opening_match = re.search(r'(?:beginning|opening)\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)
    ending_match = re.search(r'(?:ending|closing)\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)
    available_match = re.search(r'available\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)
    current_match = re.search(r'current\s+balance[:\s]+([-\(\)\$0-9,\.]+)', raw_text, re.IGNORECASE)

    balances = data['balances']
    balances['opening_balance'] = format_currency(safe_parse_currency(opening_match.group(1))) if opening_match else None
    balances['ending_balance'] = format_currency(safe_parse_currency(ending_match.group(1))) if ending_match else None
    balances['available_balance'] = format_currency(safe_parse_currency(available_match.group(1))) if available_match else None
    balances['current_balance'] = format_currency(safe_parse_currency(current_match.group(1))) if current_match else None

    # Extract transactions
    transactions = extract_transactions(raw_text)
    data['transactions'] = transactions

    # Calculate summary
    if transactions:
        total_credits = sum(t['amount_value'] for t in transactions if t['amount_value'] > 0)
        total_debits = sum(-t['amount_value'] for t in transactions if t['amount_value'] < 0)
        net_activity = sum(t['amount_value'] for t in transactions)

        data['summary'].update({
            'transaction_count': len(transactions),
            'total_credits': total_credits,
            'total_debits': total_debits,
            'net_activity': net_activity,
            'confidence': min(95.0, 55.0 + len(transactions) * 2.0)
        })

    data['raw_text'] = raw_text
    return data


def merge_bank_statement_data(primary, fallback):
    """
    Merge primary (Mindee) data with fallback (parsed) data.

    Args:
        primary: Primary data source (Mindee extraction)
        fallback: Fallback data source (text parsing)

    Returns:
        dict: Merged data
    """
    if not isinstance(primary, dict):
        primary = {}

    merged = {}
    merged['bank_name'] = primary.get('bank_name') or fallback.get('bank_name')
    merged['account_holder'] = primary.get('account_holder') or fallback.get('account_holder')
    merged['account_number'] = primary.get('account_number') or fallback.get('account_number')
    merged['statement_period'] = primary.get('statement_period') or fallback.get('statement_period')
    merged['summary'] = primary.get('summary') or fallback.get('summary')

    balances = fallback.get('balances', {})
    balances_primary = primary.get('balances', {})
    merged['balances'] = {
        'opening_balance': balances_primary.get('opening_balance') or balances.get('opening_balance'),
        'ending_balance': balances_primary.get('ending_balance') or balances.get('ending_balance'),
        'available_balance': balances_primary.get('available_balance') or balances.get('available_balance'),
        'current_balance': balances_primary.get('current_balance') or balances.get('current_balance'),
    }

    merged['transactions'] = primary.get('transactions') or fallback.get('transactions') or []
    merged['raw_text'] = primary.get('raw_text') or fallback.get('raw_text')

    return merged


def format_statement_period(start, end):
    """
    Format statement period from start and end dates.

    Args:
        start: Start date
        end: End date

    Returns:
        str or None: Formatted period
    """
    if start and end:
        return f"{start} to {end}"
    return start or end


def normalize_mindee_transactions(transactions):
    """
    Normalize Mindee transaction format to standard format.

    Args:
        transactions: List of Mindee transactions

    Returns:
        list: Normalized transactions
    """
    normalized = []
    if not transactions:
        return normalized

    for txn in transactions:
        if isinstance(txn, dict):
            date = txn.get('date') or txn.get('transaction_date')
            description = txn.get('description') or txn.get('details') or txn.get('label')
            amount_value = safe_parse_currency(txn.get('amount') or txn.get('value'))
            balance_value = safe_parse_currency(txn.get('balance'))

            normalized.append({
                'date': date,
                'description': description or 'Transaction',
                'amount': format_currency(amount_value) if amount_value is not None else txn.get('amount'),
                'amount_value': amount_value if amount_value is not None else 0.0,
                'balance': format_currency(balance_value) if balance_value is not None else txn.get('balance')
            })

    return normalized
