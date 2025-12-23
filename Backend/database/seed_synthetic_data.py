"""
Database Seeder for Mock Bank Synthetic Data
Populates the database with generated synthetic data
"""

import sys
import os
import logging
from typing import Dict, List, Any

# Ensure we're in the Backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from supabase_client import get_supabase
from real_time.bank_api.synthetic_data_generator import generate_all_synthetic_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database(
    num_customers: int = 100,
    accounts_per_customer: int = 2,
    transactions_per_account: int = 50,
    clear_existing: bool = False
):
    """
    Seed database with synthetic data
    
    Args:
        num_customers: Number of customers to generate
        accounts_per_customer: Accounts per customer
        transactions_per_account: Transactions per account
        clear_existing: Whether to clear existing data first
    """
    try:
        logger.info("🌱 Starting database seeding...")
        
        # Get Supabase client
        supabase = get_supabase()
        
        # Clear existing data if requested
        if clear_existing:
            logger.warning("⚠️  Clearing existing synthetic data...")
            supabase.table('mock_bank_connections').delete().neq('connection_id', '00000000-0000-0000-0000-000000000000').execute()
            supabase.table('synthetic_transactions').delete().neq('transaction_id', 'dummy').execute()
            supabase.table('synthetic_accounts').delete().neq('account_id', 'dummy').execute()
            supabase.table('synthetic_customers').delete().neq('customer_id', 'dummy').execute()
            logger.info("✅ Existing data cleared")
        
        # Generate synthetic data
        data = generate_all_synthetic_data(
            num_customers=num_customers,
            accounts_per_customer=accounts_per_customer,
            transactions_per_account=transactions_per_account
        )
        
        # Insert customers
        logger.info("\n📥 Inserting customers...")
        batch_size = 100
        customers = data['customers']
        for i in range(0, len(customers), batch_size):
            batch = customers[i:i+batch_size]
            # Convert datetime to string for Supabase
            for customer in batch:
                customer['created_at'] = customer['created_at'].isoformat()
            
            supabase.table('synthetic_customers').insert(batch).execute()
            logger.info(f"   Inserted {min(i+batch_size, len(customers))}/{len(customers)} customers")
        
        # Insert accounts
        logger.info("\n📥 Inserting accounts...")
        accounts = data['accounts']
        for i in range(0, len(accounts), batch_size):
            batch = accounts[i:i+batch_size]
            # Convert datetime to string for Supabase
            for account in batch:
                account['created_at'] = account['created_at'].isoformat()
            
            supabase.table('synthetic_accounts').insert(batch).execute()
            logger.info(f"   Inserted {min(i+batch_size, len(accounts))}/{len(accounts)} accounts")
        
        # Insert transactions
        logger.info("\n📥 Inserting transactions...")
        transactions = data['transactions']
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i+batch_size]
            # Convert datetime to string for Supabase
            for txn in batch:
                txn['timestamp'] = txn['timestamp'].isoformat()
                txn['created_at'] = txn['created_at'].isoformat()
            
            supabase.table('synthetic_transactions').insert(batch).execute()
            logger.info(f"   Inserted {min(i+batch_size, len(transactions))}/{len(transactions)} transactions")
        
        logger.info("\n🎉 Database seeding completed successfully!")
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Total Customers: {len(customers)}")
        logger.info(f"   Total Accounts: {len(accounts)}")
        logger.info(f"   Total Transactions: {len(transactions)}")
        logger.info(f"   Note: ~8% have suspicious patterns for ML testing")
        
        return {
            'success': True,
            'customers': len(customers),
            'accounts': len(accounts),
            'transactions': len(transactions)
        }
        
    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed database with synthetic bank data')
    parser.add_argument('--customers', type=int, default=100, help='Number of customers')
    parser.add_argument('--accounts', type=int, default=2, help='Accounts per customer')
    parser.add_argument('--transactions', type=int, default=50, help='Transactions per account')
    parser.add_argument('--clear', action='store_true', help='Clear existing data first')
    
    args = parser.parse_args()
    
    result = seed_database(
        num_customers=args.customers,
        accounts_per_customer=args.accounts,
        transactions_per_account=args.transactions,
        clear_existing=args.clear
    )
    
    if not result['success']:
        sys.exit(1)
