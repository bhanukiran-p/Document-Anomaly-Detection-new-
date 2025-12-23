# Phase 1: Synthetic Data Setup - Complete! ✅

## What Was Created

### 1. Database Schema
**File**: `database/migrations/create_mock_bank_tables.sql`

Creates 4 tables:
- `synthetic_customers` - Customer profiles
- `synthetic_accounts` - Bank accounts  
- `synthetic_transactions` - Transaction history
- `mock_bank_connections` - User-bank connections

### 2. Data Generator
**File**: `real_time/bank_api/synthetic_data_generator.py`

Generates realistic data with **5 fraud patterns**:
1. **Velocity Abuse** - Rapid sequential transactions
2. **Unusual Amount** - Abnormally large amounts ($5K-$15K)
3. **Geographic Anomaly** - Transactions from foreign countries
4. **High-Risk Merchant** - Crypto exchanges, gambling, wire transfers
5. **Night-Time Activity** - Transactions at 2-5 AM

**Features**:
- Uses Faker library for realistic names/emails
- 8% fraud rate (configurable)
- Timestamps spread over last 90 days
- Realistic balance distributions

### 3. Database Seeder
**File**: `database/seed_synthetic_data.py`

Populates database with generated data.

**Usage**:
```bash
# Default: 100 customers, 200 accounts, ~10,000 transactions
python database/seed_synthetic_data.py

# Custom amounts
python database/seed_synthetic_data.py --customers 50 --accounts 2 --transactions 30

# Clear existing data first
python database/seed_synthetic_data.py --clear
```

---

## Next Steps

### Execute Database Setup

1. **Run the SQL migration** (create tables):
   ```bash
   # Connect to Supabase and run the SQL file
   # Or use Supabase dashboard SQL editor
   ```

2. **Seed the database**:
   ```bash
   cd Backend
   python database/seed_synthetic_data.py --clear
   ```

3. **Verify data**:
   - Check Supabase dashboard
   - Should see ~100 customers, ~200 accounts, ~10,000 transactions
   - ~800 transactions marked as fraud

---

## Data Structure

### Sample Customer
```json
{
  "customer_id": "CUST_0001",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "home_city": "New York",
  "home_country": "USA"
}
```

### Sample Account
```json
{
  "account_id": "ACC_0001_1",
  "customer_id": "CUST_0001",
  "account_type": "checking",
  "account_number": "****1234",
  "current_balance": 5420.50
}
```

### Sample Transaction
```json
{
  "transaction_id": "TXN_000001",
  "account_id": "ACC_0001_1",
  "amount": 52.00,
  "merchant": "Starbucks",
  "category": "Food & Dining",
  "timestamp": "2025-12-15T10:34:00Z",
  "is_fraud": false,
  "fraud_type": null
}
```

---

## Ready for Phase 2!

Once data is seeded, proceed to **Phase 2: Mock Bank Webhook** 🎯
