"""
Synthetic Data Generator for Mock Bank API
Generates realistic customer, account, and transaction data with fraud patterns
"""

import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
from faker import Faker

fake = Faker()

# Fraud pattern constants
FRAUD_PERCENTAGE = 0.08  # 8% of transactions are fraudulent
HIGH_RISK_MERCHANTS = [
    'CryptoExchange', 'BitcoinATM', 'Western Union', 'MoneyGram',
    'OnlineGambling', 'CasinoOnline', 'QuickCash', 'PawnShop',
    'WireTransferService', 'UnknownMerchant'
]

LEGITIMATE_MERCHANTS = [
    'Amazon', 'Walmart', 'Target', 'Starbucks', 'McDonalds',
    'Shell Gas', 'Chevron', 'Whole Foods', 'CVS Pharmacy', 'Walgreens',
    'Home Depot', 'Lowes', 'Best Buy', 'Apple Store', 'Netflix',
    'Spotify', 'Uber', 'Lyft', 'DoorDash', 'Grubhub',
    'AT&T', 'Verizon', 'T-Mobile', 'Electric Company', 'Water Utility'
]

CATEGORIES = [
    'Food & Dining', 'Shopping', 'Entertainment', 'Gas & Fuel',
    'Groceries', 'Healthcare', 'Utilities', 'Transportation',
    'Travel', 'Services', 'Transfer', 'Subscription'
]

CITIES = [
    ('New York', 'USA'), ('Los Angeles', 'USA'), ('Chicago', 'USA'),
    ('Houston', 'USA'), ('Phoenix', 'USA'), ('Philadelphia', 'USA'),
    ('San Francisco', 'USA'), ('Seattle', 'USA'), ('Miami', 'USA'),
    ('Boston', 'USA'), ('London', 'UK'), ('Paris', 'France'),
    ('Tokyo', 'Japan'), ('Dubai', 'UAE'), ('Singapore', 'Singapore')
]


def generate_customer_id(index: int) -> str:
    """Generate customer ID"""
    return f"CUST_{str(index + 1).zfill(4)}"


def generate_account_id(customer_index: int, account_index: int) -> str:
    """Generate account ID"""
    return f"ACC_{str(customer_index + 1).zfill(4)}_{account_index + 1}"


def generate_transaction_id(index: int) -> str:
    """Generate transaction ID"""
    return f"TXN_{str(index + 1).zfill(6)}"


def generate_synthetic_customers(count: int = 100) -> List[Dict[str, Any]]:
    """
    Generate synthetic customer profiles
    
    Args:
        count: Number of customers to generate
        
    Returns:
        List of customer dictionaries
    """
    customers = []
    
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        home_city, home_country = random.choice(CITIES)
        
        customer = {
            'customer_id': generate_customer_id(i),
            'first_name': first_name,
            'last_name': last_name,
            'email': f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}",
            'phone': fake.phone_number(),
            'home_city': home_city,
            'home_country': home_country,
            'created_at': datetime.now() - timedelta(days=random.randint(30, 365))
        }
        
        customers.append(customer)
    
    return customers


def generate_synthetic_accounts(customers: List[Dict], accounts_per_customer: int = 2) -> List[Dict[str, Any]]:
    """
    Generate synthetic bank accounts
    
    Args:
        customers: List of customer dictionaries
        accounts_per_customer: Number of accounts per customer
        
    Returns:
        List of account dictionaries
    """
    accounts = []
    account_types = ['checking', 'savings', 'credit']
    
    for customer_idx, customer in enumerate(customers):
        num_accounts = random.randint(1, accounts_per_customer)
        
        for acc_idx in range(num_accounts):
            account_type = random.choice(account_types)
            
            # Generate realistic balances
            if account_type == 'checking':
                balance = round(random.uniform(500, 15000), 2)
            elif account_type == 'savings':
                balance = round(random.uniform(1000, 50000), 2)
            else:  # credit
                balance = round(random.uniform(0, 10000), 2)
            
            # Last 4 digits of account number
            account_mask = ''.join(random.choices(string.digits, k=4))
            
            account = {
                'account_id': generate_account_id(customer_idx, acc_idx),
                'customer_id': customer['customer_id'],
                'account_type': account_type,
                'account_number': f"****{account_mask}",
                'current_balance': balance,
                'available_balance': balance,
                'currency': 'USD',
                'created_at': customer['created_at']
            }
            
            accounts.append(account)
    
    return accounts


def generate_synthetic_transactions(
    accounts: List[Dict],
    customers: List[Dict],
    transactions_per_account: int = 50
) -> List[Dict[str, Any]]:
    """
    Generate synthetic transaction data (realistic bank transactions)
    NO fraud labels - ML/AI will determine fraud patterns
    
    Args:
        accounts: List of account dictionaries
        customers: List of customer dictionaries
        transactions_per_account: Number of transactions per account
        
    Returns:
        List of transaction dictionaries (raw bank data)
    """
    transactions = []
    transaction_idx = 0
    
    # Create customer lookup
    customer_lookup = {c['customer_id']: c for c in customers}
    
    for account in accounts:
        customer = customer_lookup[account['customer_id']]
        num_transactions = random.randint(20, transactions_per_account)
        
        # Generate timestamps (last 90 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        for _ in range(num_transactions):
            # Random timestamp
            timestamp = fake.date_time_between(start_date=start_date, end_date=end_date)
            
            # Generate realistic transaction (mix of normal and suspicious patterns)
            # ML will determine which are fraud - we just create varied data
            txn = _generate_realistic_transaction(
                transaction_idx, account, customer, timestamp
            )
            
            transactions.append(txn)
            transaction_idx += 1
    
    # Sort by timestamp
    transactions.sort(key=lambda x: x['timestamp'])
    
    return transactions


def _generate_realistic_transaction(
    index: int,
    account: Dict,
    customer: Dict,
    timestamp: datetime
) -> Dict[str, Any]:
    """
    Generate a realistic bank transaction
    Creates varied patterns (some normal, some suspicious) - ML will determine fraud
    NO fraud labels included - mimics real bank API behavior
    """
    
    # Create varied transaction patterns (8% will have suspicious characteristics)
    # But we DON'T label them - ML determines this!
    is_suspicious_pattern = random.random() < 0.08
    
    if is_suspicious_pattern:
        # Generate transaction with suspicious characteristics
        pattern_type = random.choice([
            'large_amount', 'foreign_location', 'high_risk_merchant',
            'night_time', 'rapid_succession'
        ])
        
        if pattern_type == 'large_amount':
            amount = round(random.uniform(5000, 15000), 2)
            merchant = random.choice(HIGH_RISK_MERCHANTS)
            category = 'Transfer'
            transaction_city = customer['home_city']
            transaction_country = customer['home_country']
            
        elif pattern_type == 'foreign_location':
            amount = round(random.uniform(100, 2000), 2)
            merchant = random.choice(LEGITIMATE_MERCHANTS)
            category = random.choice(CATEGORIES)
            # Different country
            foreign_cities = [c for c in CITIES if c[1] != customer['home_country']]
            if foreign_cities:
                transaction_city, transaction_country = random.choice(foreign_cities)
            else:
                transaction_city, transaction_country = customer['home_city'], customer['home_country']
                
        elif pattern_type == 'high_risk_merchant':
            amount = round(random.uniform(500, 5000), 2)
            merchant = random.choice(HIGH_RISK_MERCHANTS)
            category = 'Transfer'
            transaction_city = customer['home_city']
            transaction_country = customer['home_country']
            
        elif pattern_type == 'night_time':
            amount = round(random.uniform(100, 1000), 2)
            merchant = random.choice(HIGH_RISK_MERCHANTS)
            category = random.choice(CATEGORIES)
            transaction_city = customer['home_city']
            transaction_country = customer['home_country']
            # Night hours (2-5 AM)
            timestamp = timestamp.replace(hour=random.randint(2, 5))
            
        else:  # rapid_succession
            amount = round(random.uniform(50, 500), 2)
            merchant = random.choice(LEGITIMATE_MERCHANTS)
            category = random.choice(CATEGORIES)
            transaction_city = customer['home_city']
            transaction_country = customer['home_country']
    
    else:
        # Normal transaction
        amount = round(random.uniform(5, 500), 2)
        merchant = random.choice(LEGITIMATE_MERCHANTS)
        category = random.choice(CATEGORIES)
        
        # 95% same city, 5% nearby city (travel)
        if random.random() < 0.95:
            transaction_city = customer['home_city']
            transaction_country = customer['home_country']
        else:
            # Travel within same country
            nearby_cities = [c for c in CITIES if c[1] == customer['home_country']]
            if not nearby_cities:
                nearby_cities = CITIES
            transaction_city, transaction_country = random.choice(nearby_cities)
    
    # Return clean transaction data (NO fraud labels - like real banks!)
    return {
        'transaction_id': generate_transaction_id(index),
        'account_id': account['account_id'],
        'customer_id': account['customer_id'],
        'amount': amount,
        'merchant': merchant,
        'category': category,
        'timestamp': timestamp,
        'transaction_city': transaction_city,
        'transaction_country': transaction_country,
        'login_city': customer['home_city'],
        'login_country': customer['home_country'],
        'created_at': datetime.now()
    }


def generate_all_synthetic_data(
    num_customers: int = 100,
    accounts_per_customer: int = 2,
    transactions_per_account: int = 50
) -> Dict[str, List[Dict]]:
    """
    Generate complete synthetic dataset
    
    Args:
        num_customers: Number of customers
        accounts_per_customer: Accounts per customer
        transactions_per_account: Transactions per account
        
    Returns:
        Dictionary with customers, accounts, and transactions
    """
    print(f"Generating {num_customers} synthetic customers...")
    customers = generate_synthetic_customers(num_customers)
    
    print(f"Generating synthetic accounts...")
    accounts = generate_synthetic_accounts(customers, accounts_per_customer)
    
    print(f"Generating synthetic transactions...")
    transactions = generate_synthetic_transactions(accounts, customers, transactions_per_account)
    
    print(f"\n✅ Synthetic data generated successfully!")
    print(f"   Customers: {len(customers)}")
    print(f"   Accounts: {len(accounts)}")
    print(f"   Transactions: {len(transactions)}")
    print(f"   Note: ~8% have suspicious patterns (ML will determine fraud)")
    
    return {
        'customers': customers,
        'accounts': accounts,
        'transactions': transactions
    }


if __name__ == '__main__':
    # Generate test data
    data = generate_all_synthetic_data(
        num_customers=100,
        accounts_per_customer=2,
        transactions_per_account=50
    )
    
    # Save to CSV for inspection
    pd.DataFrame(data['customers']).to_csv('synthetic_customers.csv', index=False)
    pd.DataFrame(data['accounts']).to_csv('synthetic_accounts.csv', index=False)
    pd.DataFrame(data['transactions']).to_csv('synthetic_transactions.csv', index=False)
    
    print("\n📁 Data saved to CSV files for inspection")
