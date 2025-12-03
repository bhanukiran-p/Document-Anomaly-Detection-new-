"""
Migration script to add AI analysis columns to all document tables
"""
import os
import sys
import logging
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing Supabase credentials")
    sys.exit(1)

# Create client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL migration statements
migrations = [
    # Add to money_orders table
    """
    ALTER TABLE money_orders
    ADD COLUMN IF NOT EXISTS ai_confidence NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
    """,
    # Add to checks table
    """
    ALTER TABLE checks
    ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
    """,
    # Add to bank_statements table
    """
    ALTER TABLE bank_statements
    ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
    """,
    # Add to paystubs table
    """
    ALTER TABLE paystubs
    ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
    """
]

try:
    logger.info("Running migrations...")
    for i, migration in enumerate(migrations, 1):
        logger.info(f"Executing migration {i}/{len(migrations)}...")
        try:
            # Execute via RPC since we don't have direct SQL execution
            # We'll need to use a different approach
            logger.info(f"Migration {i}: Skipping direct SQL (would need RPC function)")
        except Exception as e:
            logger.error(f"Error in migration {i}: {e}")

    logger.info("Note: Direct SQL execution not available via Supabase client.")
    logger.info("Please run the SQL migrations manually in the Supabase SQL editor:")
    logger.info("1. Go to Supabase dashboard")
    logger.info("2. Open SQL Editor")
    logger.info("3. Paste the contents of Backend/database/add_ai_columns.sql")
    logger.info("4. Execute")

except Exception as e:
    logger.error(f"Migration failed: {e}")
    sys.exit(1)

logger.info("Migration script completed!")
