"""
Database operations for storing analyzed real-time transactions
Handles inserting and retrieving analyzed transaction data from Supabase
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from .supabase_client import get_supabase

logger = logging.getLogger(__name__)


def save_analyzed_transactions(
    transactions: List[Dict],
    batch_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    model_type: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Save analyzed transactions to the analyzed_real_time_trn table in Supabase.

    Args:
        transactions: List of transaction dictionaries with fraud analysis results
        batch_id: Optional identifier for batch processing
        analysis_id: Optional identifier for the analysis session
        model_type: Optional identifier for which ML model was used

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        if not transactions:
            logger.warning("No transactions provided to save")
            return False, "No transactions to save"

        supabase = get_supabase()

        # Prepare the data for insertion
        records_to_insert = []
        for txn in transactions:
            record = {
                # Core transaction fields (from CSV)
                'transaction_id': str(txn.get('transaction_id', '')),
                'customer_id': str(txn.get('customer_id', '')) or None,
                'amount': float(txn.get('amount', 0)) if txn.get('amount') else None,
                'merchant': str(txn.get('merchant', '')) or None,
                'category': str(txn.get('category', '')) or None,
                'timestamp': txn.get('timestamp'),  # Should be ISO format datetime
                'location': str(txn.get('location', '')) or None,
                'account_balance': float(txn.get('account_balance', 0)) if txn.get('account_balance') else None,
                'card_type': str(txn.get('card_type', '')) or None,
                'is_fraud': int(txn.get('is_fraud', 0)),
                'added_at': txn.get('added_at'),

                # Customer demographic fields
                'first_name': str(txn.get('first_name', '')) or None,
                'last_name': str(txn.get('last_name', '')) or None,
                'gender': str(txn.get('gender', '')) or None,

                # Location fields
                'home_city': str(txn.get('home_city', '')) or None,
                'home_country': str(txn.get('home_country', '')) or None,
                'transaction_city': str(txn.get('transaction_city', '')) or None,
                'transaction_country': str(txn.get('transaction_country', '')) or None,
                'login_city': str(txn.get('login_city', '')) or None,
                'login_country': str(txn.get('login_country', '')) or None,

                # Transaction detail fields
                'transaction_type': str(txn.get('transaction_type', '')) or None,
                'currency': str(txn.get('currency', '')) or None,
                'description': str(txn.get('description', '')) or None,
                'is_by_check': txn.get('is_by_check'),  # Keep as boolean

                # Banking fields
                'account_number': float(txn.get('account_number')) if txn.get('account_number') else None,
                'swift_bic': str(txn.get('swift_bic', '')) or None,
                'receiveraccount': float(txn.get('receiveraccount')) if txn.get('receiveraccount') else None,
                'receiverswift': str(txn.get('receiverswift', '')) or None,
                'balanceafter': float(txn.get('balanceafter')) if txn.get('balanceafter') else None,
                'avgdailybalance': float(txn.get('avgdailybalance')) if txn.get('avgdailybalance') else None,

                # Analysis fields
                'fraud_probability': float(txn.get('fraud_probability', 0)) if txn.get('fraud_probability') else None,
                'fraud_reason': str(txn.get('fraud_reason', '')) or None,
                'fraud_reason_detail': str(txn.get('fraud_reason_detail', '')) or None,
                'analysis_date': datetime.utcnow().isoformat(),
                'analysis_id': analysis_id,
                'batch_id': batch_id,
                'model_type': model_type,
                'confidence_score': float(txn.get('confidence_score', txn.get('fraud_probability', 0))) if txn.get('confidence_score') or txn.get('fraud_probability') else None
            }
            records_to_insert.append(record)

        # Insert records in batches to avoid timeout issues
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(records_to_insert), batch_size):
            batch = records_to_insert[i:i + batch_size]
            try:
                response = supabase.table('analyzed_real_time_trn').insert(batch).execute()
                total_inserted += len(batch)
                logger.info(f"Successfully inserted batch {i // batch_size + 1} ({len(batch)} records)")
            except Exception as e:
                error_msg = f"Error inserting batch {i // batch_size + 1}: {str(e)}"
                logger.error(error_msg)
                return False, error_msg

        logger.info(f"Successfully saved {total_inserted} analyzed transactions to database")
        return True, None

    except Exception as e:
        error_msg = f"Error saving analyzed transactions: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_analyzed_transactions(
    batch_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    limit: int = 1000,
    is_fraud_only: bool = False
) -> Tuple[List[Dict], Optional[str]]:
    """
    Retrieve analyzed transactions from the database.

    Args:
        batch_id: Filter by batch ID
        analysis_id: Filter by analysis ID
        limit: Maximum number of records to retrieve
        is_fraud_only: Only return fraudulent transactions

    Returns:
        Tuple of (transactions: List[Dict], error_message: Optional[str])
    """
    try:
        supabase = get_supabase()

        query = supabase.table('analyzed_real_time_trn').select('*')

        if batch_id:
            query = query.eq('batch_id', batch_id)

        if analysis_id:
            query = query.eq('analysis_id', analysis_id)

        if is_fraud_only:
            query = query.eq('is_fraud', 1)

        response = query.order('created_at', desc=True).limit(limit).execute()

        logger.info(f"Retrieved {len(response.data)} transactions from database")
        return response.data, None

    except Exception as e:
        error_msg = f"Error retrieving analyzed transactions: {str(e)}"
        logger.error(error_msg)
        return [], error_msg


def get_transaction_statistics(batch_id: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get statistics for analyzed transactions.

    Args:
        batch_id: Optional filter by batch ID

    Returns:
        Tuple of (statistics: Optional[Dict], error_message: Optional[str])
    """
    try:
        supabase = get_supabase()

        query = supabase.table('analyzed_real_time_trn').select('*')

        if batch_id:
            query = query.eq('batch_id', batch_id)

        response = query.execute()
        transactions = response.data

        if not transactions:
            return {}, None

        # Calculate statistics
        total_count = len(transactions)
        fraud_count = sum(1 for t in transactions if t.get('is_fraud') == 1)
        legitimate_count = total_count - fraud_count

        total_amount = sum(float(t.get('amount', 0)) for t in transactions)
        fraud_amount = sum(float(t.get('amount', 0)) for t in transactions if t.get('is_fraud') == 1)
        legitimate_amount = total_amount - fraud_amount

        avg_fraud_probability = sum(float(t.get('fraud_probability', 0)) for t in transactions) / total_count if total_count > 0 else 0

        statistics = {
            'total_transactions': total_count,
            'fraud_count': fraud_count,
            'legitimate_count': legitimate_count,
            'fraud_percentage': (fraud_count / total_count * 100) if total_count > 0 else 0,
            'legitimate_percentage': (legitimate_count / total_count * 100) if total_count > 0 else 0,
            'total_amount': total_amount,
            'fraud_amount': fraud_amount,
            'legitimate_amount': legitimate_amount,
            'average_fraud_probability': avg_fraud_probability
        }

        logger.info(f"Generated statistics for {total_count} transactions")
        return statistics, None

    except Exception as e:
        error_msg = f"Error generating transaction statistics: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def delete_analyzed_transactions(batch_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete analyzed transactions by batch ID.

    Args:
        batch_id: Batch ID to delete

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        supabase = get_supabase()

        response = supabase.table('analyzed_real_time_trn').delete().eq('batch_id', batch_id).execute()

        logger.info(f"Deleted transactions for batch {batch_id}")
        return True, None

    except Exception as e:
        error_msg = f"Error deleting analyzed transactions: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_training_data_from_database(
    limit: int = 10000,
    min_samples: int = 100,
    use_recent: bool = True
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Fetch transaction data from database for model training.
    
    Args:
        limit: Maximum number of records to fetch (default: 10000)
        min_samples: Minimum number of samples required (default: 100)
        use_recent: If True, fetch most recent records first (default: True)
    
    Returns:
        Tuple of (transactions: Optional[List[Dict]], error_message: Optional[str])
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table('analyzed_real_time_trn').select('*')
        
        # Order by most recent first if requested
        if use_recent:
            query = query.order('created_at', desc=True)
        else:
            query = query.order('created_at', desc=False)
        
        # Fetch data
        response = query.limit(limit).execute()
        
        if not response.data:
            logger.warning("No training data found in database")
            return None, "No training data available in database"
        
        transactions = response.data
        
        if len(transactions) < min_samples:
            logger.warning(f"Insufficient training data: {len(transactions)} samples (minimum: {min_samples})")
            return None, f"Insufficient training data: {len(transactions)} samples (minimum: {min_samples})"
        
        # Check if we have fraud labels
        fraud_count = sum(1 for t in transactions if t.get('is_fraud') == 1)
        legitimate_count = len(transactions) - fraud_count
        
        logger.info(f"Fetched {len(transactions)} transactions for training: {fraud_count} fraud, {legitimate_count} legitimate")
        
        return transactions, None
        
    except Exception as e:
        error_msg = f"Error fetching training data from database: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
