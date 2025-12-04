"""
Bank List Loader
Fetches supported banks from database and provides case-insensitive matching
"""

import logging
from typing import List, Set, Optional
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Cache for bank names (to avoid repeated database calls)
_bank_names_cache: Optional[Set[str]] = None


def get_supported_bank_names() -> Set[str]:
    """
    Fetch all bank names from database and return as a set for case-insensitive matching.
    Tries 'bank_dictionary' table first, then 'financial_institutions' as fallback.
    
    Returns:
        Set of bank names (lowercased for case-insensitive matching)
    """
    global _bank_names_cache
    
    # Return cached value if available
    if _bank_names_cache is not None:
        return _bank_names_cache
    
    try:
        supabase = get_supabase()
        bank_names = set()
        
        # Try bank_dictionary table first (as per user's data)
        try:
            response = supabase.table('bank_dictionary').select('bank_name').execute()
            if response.data:
                for bank in response.data:
                    bank_name = bank.get('bank_name')
                    if bank_name:
                        # Store lowercase for case-insensitive matching
                        bank_names.add(bank_name.lower().strip())
                logger.info(f"Loaded {len(bank_names)} banks from bank_dictionary table")
        except Exception as e:
            logger.warning(f"Could not fetch from bank_dictionary table: {e}")
        
        # Fallback to financial_institutions table if bank_dictionary didn't work
        if not bank_names:
            try:
                response = supabase.table('financial_institutions').select('name').execute()
                if response.data:
                    for institution in response.data:
                        bank_name = institution.get('name')
                        if bank_name:
                            bank_names.add(bank_name.lower().strip())
                    logger.info(f"Loaded {len(bank_names)} banks from financial_institutions table")
            except Exception as e:
                logger.warning(f"Could not fetch from financial_institutions table: {e}")
        
        # If still no banks, use default list as fallback
        if not bank_names:
            logger.warning("No banks found in database, using default list")
            default_banks = [
                'Bank of America', 'Chase', 'Wells Fargo', 'Citibank',
                'U.S. Bank', 'PNC Bank', 'TD Bank', 'Capital One',
                'JPMorgan Chase Bank', 'TD Bank USA', 'Capital One Bank'
            ]
            bank_names = {bank.lower().strip() for bank in default_banks}
        
        # Cache the result
        _bank_names_cache = bank_names
        logger.info(f"Total supported banks loaded: {len(bank_names)}")
        return bank_names
        
    except Exception as e:
        logger.error(f"Error loading banks from database: {e}")
        # Return default list on error
        default_banks = [
            'Bank of America', 'Chase', 'Wells Fargo', 'Citibank',
            'U.S. Bank', 'PNC Bank', 'TD Bank', 'Capital One',
            'JPMorgan Chase Bank', 'TD Bank USA', 'Capital One Bank'
        ]
        return {bank.lower().strip() for bank in default_banks}


def is_supported_bank(bank_name: Optional[str]) -> bool:
    """
    Check if a bank name is supported (case-insensitive)
    
    Args:
        bank_name: Bank name to check
        
    Returns:
        True if bank is supported, False otherwise
    """
    if not bank_name:
        return False
    
    supported_banks = get_supported_bank_names()
    bank_name_lower = bank_name.lower().strip()
    
    return bank_name_lower in supported_banks


def clear_cache():
    """Clear the bank names cache (useful for testing or when banks are updated)"""
    global _bank_names_cache
    _bank_names_cache = None
    logger.info("Bank names cache cleared")

