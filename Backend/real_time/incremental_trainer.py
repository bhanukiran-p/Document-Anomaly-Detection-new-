"""
Incremental Model Trainer for Large Datasets
Trains fraud detection model in batches to handle millions of records
"""
import pandas as pd
import numpy as np
import logging
import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_PATH = 'transactions.db'
TABLE_NAME = 'analyzed_transactions'  # Adjust based on your actual table name

# Training configuration
BATCH_SIZE = 5000  # Process 5000 transactions at a time
MAX_TRAINING_SAMPLES = 50000  # Use max 50k most recent transactions for training
MIN_FRAUD_SAMPLES = 100  # Minimum fraud samples needed
MIN_TOTAL_SAMPLES = 500  # Minimum total samples needed


def get_transaction_count(db_path: str = DATABASE_PATH) -> int:
    """Get total count of transactions in database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Try to get count
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        count = cursor.fetchone()[0]

        conn.close()
        return count
    except Exception as e:
        logger.error(f"Failed to get transaction count: {e}")
        return 0


def load_transactions_batch(
    offset: int,
    limit: int,
    db_path: str = DATABASE_PATH
) -> pd.DataFrame:
    """
    Load a batch of transactions from database.

    Args:
        offset: Starting row number
        limit: Number of rows to fetch
        db_path: Path to SQLite database

    Returns:
        DataFrame with transaction batch
    """
    try:
        conn = sqlite3.connect(db_path)

        # Load batch with most recent transactions first
        query = f"""
            SELECT * FROM {TABLE_NAME}
            ORDER BY timestamp DESC
            LIMIT {limit} OFFSET {offset}
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        logger.info(f"Loaded batch: offset={offset}, rows={len(df)}")
        return df

    except Exception as e:
        logger.error(f"Failed to load batch at offset {offset}: {e}")
        return pd.DataFrame()


def sample_balanced_data(
    df: pd.DataFrame,
    max_samples: int = MAX_TRAINING_SAMPLES,
    fraud_ratio: float = 0.3
) -> pd.DataFrame:
    """
    Create a balanced sample from large dataset.
    Ensures good representation of both fraud and legitimate transactions.

    Args:
        df: Full dataframe
        max_samples: Maximum number of samples to use
        fraud_ratio: Target ratio of fraud samples (0.3 = 30% fraud)

    Returns:
        Balanced sample dataframe
    """
    if len(df) <= max_samples:
        return df

    # Check if is_fraud column exists
    if 'is_fraud' not in df.columns:
        # No fraud labels - random sample
        logger.info(f"No fraud labels found, random sampling {max_samples} transactions")
        return df.sample(n=max_samples, random_state=42)

    # Separate fraud and legitimate
    fraud_df = df[df['is_fraud'] == 1]
    legit_df = df[df['is_fraud'] == 0]

    # Calculate target counts
    target_fraud = int(max_samples * fraud_ratio)
    target_legit = max_samples - target_fraud

    # Sample fraud transactions (with replacement if needed)
    if len(fraud_df) > 0:
        if len(fraud_df) >= target_fraud:
            fraud_sample = fraud_df.sample(n=target_fraud, random_state=42)
        else:
            # Not enough fraud - use all and adjust legitimate count
            fraud_sample = fraud_df
            target_legit = max_samples - len(fraud_sample)
    else:
        fraud_sample = pd.DataFrame()
        target_legit = max_samples

    # Sample legitimate transactions
    if len(legit_df) >= target_legit:
        legit_sample = legit_df.sample(n=target_legit, random_state=42)
    else:
        legit_sample = legit_df

    # Combine and shuffle
    balanced_df = pd.concat([fraud_sample, legit_sample], ignore_index=True)
    balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)

    logger.info(f"Created balanced sample: {len(fraud_sample)} fraud + {len(legit_sample)} legit = {len(balanced_df)} total")

    return balanced_df


def train_from_database_incremental(
    db_path: str = DATABASE_PATH,
    max_samples: int = MAX_TRAINING_SAMPLES,
    batch_size: int = BATCH_SIZE
) -> Dict[str, Any]:
    """
    Train fraud detection model incrementally from database.
    Loads data in batches to avoid memory issues.

    Args:
        db_path: Path to SQLite database
        max_samples: Maximum number of transactions to use for training
        batch_size: Number of records to load per batch

    Returns:
        Training result dictionary
    """
    try:
        logger.info("=" * 80)
        logger.info("STARTING INCREMENTAL MODEL TRAINING FROM DATABASE")
        logger.info("=" * 80)

        # Check database exists
        if not os.path.exists(db_path):
            return {
                'success': False,
                'error': f'Database not found at {db_path}'
            }

        # Get total count
        total_count = get_transaction_count(db_path)
        logger.info(f"Total transactions in database: {total_count:,}")

        if total_count < MIN_TOTAL_SAMPLES:
            return {
                'success': False,
                'error': f'Insufficient data. Found {total_count}, need at least {MIN_TOTAL_SAMPLES}'
            }

        # Calculate how many samples to actually load
        samples_to_load = min(total_count, max_samples)
        logger.info(f"Will load up to {samples_to_load:,} most recent transactions")

        # Load data in batches
        all_batches = []
        offset = 0

        while offset < samples_to_load:
            current_batch_size = min(batch_size, samples_to_load - offset)

            logger.info(f"Loading batch {offset // batch_size + 1}: rows {offset} to {offset + current_batch_size}")

            batch_df = load_transactions_batch(offset, current_batch_size, db_path)

            if batch_df.empty:
                logger.warning(f"Empty batch at offset {offset}, stopping")
                break

            all_batches.append(batch_df)
            offset += current_batch_size

            # Log memory usage
            current_rows = sum(len(b) for b in all_batches)
            logger.info(f"Loaded {current_rows:,} rows so far ({len(all_batches)} batches)")

        if not all_batches:
            return {
                'success': False,
                'error': 'No data could be loaded from database'
            }

        # Combine all batches
        logger.info("Combining batches into training dataset...")
        combined_df = pd.concat(all_batches, ignore_index=True)
        logger.info(f"Combined dataset: {len(combined_df):,} transactions")

        # Create balanced sample if needed
        if len(combined_df) > max_samples:
            logger.info(f"Dataset too large ({len(combined_df):,}), creating balanced sample...")
            combined_df = sample_balanced_data(combined_df, max_samples)

        # Check for fraud labels
        fraud_count = 0
        if 'is_fraud' in combined_df.columns:
            fraud_count = combined_df['is_fraud'].sum()
            logger.info(f"Fraud distribution: {fraud_count} fraud ({fraud_count/len(combined_df)*100:.2f}%), {len(combined_df)-fraud_count} legitimate")

            if fraud_count < MIN_FRAUD_SAMPLES:
                logger.warning(f"Only {fraud_count} fraud samples found (minimum {MIN_FRAUD_SAMPLES})")
                logger.warning("Model may not perform well. Consider analyzing more transactions first.")

        # Train model using the standard trainer
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING MODEL ON SAMPLED DATA")
        logger.info("=" * 80)

        from real_time.model_trainer import auto_train_model
        result = auto_train_model(combined_df)

        if result.get('success'):
            logger.info("\n" + "=" * 80)
            logger.info("INCREMENTAL TRAINING SUCCESSFUL!")
            logger.info("=" * 80)
            logger.info(f"Used {len(combined_df):,} transactions from database of {total_count:,} total")

            result['database_stats'] = {
                'total_transactions': total_count,
                'used_for_training': len(combined_df),
                'fraud_count': int(fraud_count),
                'batches_loaded': len(all_batches),
                'trained_at': datetime.now().isoformat()
            }

        return result

    except Exception as e:
        logger.error(f"Incremental training failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_training_status() -> Dict[str, Any]:
    """Get current training status and statistics."""
    try:
        from real_time.model_trainer import MODEL_METADATA_PATH
        import json

        # Check if model exists
        model_exists = os.path.exists(MODEL_METADATA_PATH)

        if not model_exists:
            return {
                'model_trained': False,
                'message': 'No model found - training required'
            }

        # Read metadata
        with open(MODEL_METADATA_PATH, 'r') as f:
            metadata = json.load(f)

        # Get database stats
        db_count = get_transaction_count()

        return {
            'model_trained': True,
            'trained_at': metadata.get('trained_at'),
            'training_samples': metadata.get('training_samples'),
            'database_transactions': db_count,
            'metrics': metadata.get('metrics', {}),
            'needs_retraining': db_count > metadata.get('training_samples', 0) * 2
        }

    except Exception as e:
        return {
            'error': str(e)
        }
