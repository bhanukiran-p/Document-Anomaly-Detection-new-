"""
Run Automated Retraining
Main entry point to run automated retraining for all enabled document types.
"""

import sys
import os
import logging
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.paystub_model_retrainer import PaystubModelRetrainer
from training.check_model_retrainer import CheckModelRetrainer
from training.money_order_model_retrainer import MoneyOrderModelRetrainer
from training.bank_statement_model_retrainer import BankStatementModelRetrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'retraining_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

RETRAINER_MAP = {
    'paystub': PaystubModelRetrainer,
    'check': CheckModelRetrainer,
    'money_order': MoneyOrderModelRetrainer,
    'bank_statement': BankStatementModelRetrainer
}

def main():
    logger.info("Starting system-wide automated retraining...")
    
    # Load config to see what's enabled
    config_path = os.path.join(os.path.dirname(__file__), 'retraining_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    doc_types = config.get('document_types', {})
    
    results = {}
    
    for doc_type, settings in doc_types.items():
        if not settings.get('enabled', False):
            logger.info(f"Skipping {doc_type} (disabled in config)")
            continue
            
        logger.info(f"Processing {doc_type}...")
        
        retrainer_class = RETRAINER_MAP.get(doc_type)
        if not retrainer_class:
            logger.error(f"No retrainer class found for {doc_type}")
            continue
            
        try:
            retrainer = retrainer_class()
            result = retrainer.retrain()
            results[doc_type] = result
            
            status = "SUCCESS" if result.get('success') else "FAILED"
            logger.info(f"Finished {doc_type}: {status}")
            
        except Exception as e:
            logger.error(f"Error running retrainer for {doc_type}: {e}", exc_info=True)
            results[doc_type] = {'success': False, 'error': str(e)}

    # Summary
    logger.info("="*50)
    logger.info("RETRAINING SUMMARY")
    logger.info("="*50)
    for doc_type, res in results.items():
        status = "✅ Success" if res.get('success') else "❌ Failed"
        activated = "Activated" if res.get('activated') else "Not Activated"
        logger.info(f"{doc_type.ljust(15)}: {status} ({activated})")
        
    logger.info("Done.")

if __name__ == "__main__":
    main()
