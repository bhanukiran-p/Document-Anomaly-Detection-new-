"""
Migration script to update existing check fraud_type values
Converts underscore format (SIGNATURE_FORGERY) to space format (Signature Forgery)
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.supabase_client import get_supabase

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of old format to new format
FRAUD_TYPE_MAPPING = {
    'SIGNATURE_FORGERY': 'Signature Forgery',
    'AMOUNT_ALTERATION': 'Amount Alteration',
    'COUNTERFEIT_CHECK': 'Counterfeit Check',
    'REPEAT_OFFENDER': 'Repeat Offender',
    'STALE_CHECK': 'Stale Check'
}

def update_fraud_types():
    """Update existing check fraud_type values in the database"""
    try:
        supabase = get_supabase()
        logger.info("Connected to Supabase")
        
        # Get all checks with fraud_type containing underscores
        logger.info("Fetching checks with underscore-formatted fraud types...")
        response = supabase.table('checks').select('check_id, fraud_type').execute()
        
        if not response.data:
            logger.info("No checks found in database")
            return
        
        updates_count = 0
        for check in response.data:
            fraud_type = check.get('fraud_type')
            if fraud_type and fraud_type in FRAUD_TYPE_MAPPING:
                new_fraud_type = FRAUD_TYPE_MAPPING[fraud_type]
                check_id = check['check_id']
                
                # Update the record
                supabase.table('checks').update({
                    'fraud_type': new_fraud_type
                }).eq('check_id', check_id).execute()
                
                updates_count += 1
                logger.info(f"Updated check {check_id}: {fraud_type} -> {new_fraud_type}")
        
        logger.info(f"✅ Successfully updated {updates_count} check records")
        
        # Verify the update
        logger.info("Verifying update...")
        response = supabase.table('checks').select('fraud_type').not_.is_('fraud_type', 'null').execute()
        unique_types = set(check.get('fraud_type') for check in response.data if check.get('fraud_type'))
        logger.info(f"Current fraud types in database: {sorted(unique_types)}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    logger.info("Starting fraud type format update...")
    update_fraud_types()
    logger.info("Migration completed!")
