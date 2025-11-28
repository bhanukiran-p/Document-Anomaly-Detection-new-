"""
CSV Transaction Processor
Handles CSV file parsing and transaction data extraction
"""
import pandas as pd
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def process_transaction_csv(file_path: str) -> Dict[str, Any]:
    """
    Process CSV file containing transaction data.

    Expected CSV columns:
    - transaction_id: Unique identifier
    - customer_id: Customer identifier
    - amount: Transaction amount
    - merchant: Merchant name
    - category: Transaction category
    - timestamp: Transaction timestamp
    - location: Transaction location
    - account_balance: Account balance (optional)
    - card_type: Card type (optional)

    Args:
        file_path: Path to CSV file

    Returns:
        Dictionary containing:
            - transactions: List of transaction dictionaries
            - total_count: Total number of transactions
            - date_range: Date range of transactions
            - summary: Summary statistics
    """
    try:
        logger.info(f"Processing CSV file: {file_path}")

        # Read CSV file
        df = pd.read_csv(file_path)

        # Standardize column names first (this will map variations to standard names)
        df = _standardize_columns(df)

        # Validate required columns (only 'amount' is truly required)
        if 'amount' not in df.columns:
            raise ValueError(f"Missing required column: 'amount'. Found columns: {list(df.columns)}")

        # Clean and validate data
        df = _clean_data(df)

        # Convert to list of dictionaries
        transactions = df.to_dict('records')

        # Calculate summary statistics
        summary = _calculate_summary(df)

        # Get date range
        date_range = _get_date_range(df)

        result = {
            'success': True,
            'transactions': transactions,
            'total_count': len(transactions),
            'date_range': date_range,
            'summary': summary,
            'columns': list(df.columns),
            'processed_at': datetime.now().isoformat()
        }

        logger.info(f"Successfully processed {len(transactions)} transactions")
        return result

    except Exception as e:
        logger.error(f"CSV processing failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to process CSV file'
        }


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names to lowercase and remove spaces."""
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

    # Map common column name variations to standard names
    column_mappings = {
        'merchant_name': 'merchant',
        'merchantname': 'merchant',
        'vendor': 'merchant',
        'shop': 'merchant',
        'store': 'merchant',

        'transaction_date': 'timestamp',
        'date': 'timestamp',
        'datetime': 'timestamp',
        'trans_date': 'timestamp',
        'txn_date': 'timestamp',

        'customer': 'customer_id',
        'cust_id': 'customer_id',
        'user_id': 'customer_id',
        'account_number': 'customer_id',

        'txn_id': 'transaction_id',
        'trans_id': 'transaction_id',
        'id': 'transaction_id',

        'balance_after': 'account_balance',
        'balance': 'account_balance',
        'ending_balance': 'account_balance',

        'type': 'category',
        'transaction_type': 'category',
        'cat': 'category',
        'transaction_description': 'description',
        'desc': 'description',
        'description': 'description',
    }

    # Apply mappings
    for old_col, new_col in column_mappings.items():
        if old_col in df.columns and new_col not in df.columns:
            df = df.rename(columns={old_col: new_col})
            logger.info(f"Mapped column '{old_col}' to '{new_col}'")

    return df


def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate transaction data."""
    # Remove rows with missing critical fields
    df = df.dropna(subset=['amount'])

    # Convert amount to float
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['amount'])

    # Ensure transaction_id exists
    if 'transaction_id' not in df.columns:
        df['transaction_id'] = [f"TXN_{i}" for i in range(len(df))]

    # Ensure customer_id exists
    if 'customer_id' not in df.columns:
        df['customer_id'] = 'UNKNOWN'

    # Parse timestamp if exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Fill missing merchant
    if 'merchant' not in df.columns:
        df['merchant'] = 'Unknown Merchant'
    else:
        df['merchant'] = df['merchant'].fillna('Unknown Merchant')

    # Fill missing category
    if 'category' not in df.columns:
        df['category'] = 'general'
    else:
        df['category'] = df['category'].fillna('general')

    return df


def _calculate_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate summary statistics from transaction data."""
    summary = {
        'total_transactions': len(df),
        'total_amount': float(df['amount'].sum()),
        'average_amount': float(df['amount'].mean()),
        'min_amount': float(df['amount'].min()),
        'max_amount': float(df['amount'].max()),
        'median_amount': float(df['amount'].median()),
    }

    # Unique customers
    if 'customer_id' in df.columns:
        summary['unique_customers'] = int(df['customer_id'].nunique())

    # Unique merchants
    if 'merchant' in df.columns:
        summary['unique_merchants'] = int(df['merchant'].nunique())

    # Category distribution
    if 'category' in df.columns:
        summary['categories'] = df['category'].value_counts().to_dict()

    return summary


def _get_date_range(df: pd.DataFrame) -> Dict[str, str]:
    """Get date range of transactions."""
    if 'timestamp' in df.columns:
        df_with_dates = df.dropna(subset=['timestamp'])
        if len(df_with_dates) > 0:
            return {
                'start': df_with_dates['timestamp'].min().isoformat(),
                'end': df_with_dates['timestamp'].max().isoformat()
            }

    return {
        'start': None,
        'end': None
    }


def validate_csv_format(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate CSV format and return validation results.

    Args:
        df: Pandas DataFrame

    Returns:
        Validation result dictionary
    """
    issues = []
    warnings = []

    # Check for required columns
    required = ['amount', 'merchant']
    for col in required:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")

    # Check for recommended columns
    recommended = ['customer_id', 'timestamp', 'category']
    for col in recommended:
        if col not in df.columns:
            warnings.append(f"Missing recommended column: {col}")

    # Check for data quality
    if 'amount' in df.columns:
        negative_amounts = df['amount'] < 0
        if negative_amounts.any():
            warnings.append(f"Found {negative_amounts.sum()} negative amounts")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings
    }
