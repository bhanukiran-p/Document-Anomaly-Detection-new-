"""
Bank API Client
Fetches and enriches bank data from webhook endpoints with caching
"""
import requests
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cachetools import TTLCache
import hashlib

logger = logging.getLogger(__name__)

# Simple TTL cache - 5 minutes (300 seconds)
# Stores up to 100 different cache entries
cache = TTLCache(maxsize=100, ttl=300)


class BankAPIClient:
    """
    Client for fetching bank data from mock webhook endpoints.
    Includes caching, filtering, and data enrichment capabilities.
    """
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        """
        Initialize Bank API Client
        
        Args:
            base_url: Base URL of the webhook endpoints
        """
        self.base_url = base_url
        self.customers_url = f"{base_url}/webhook/bank/customers"
        self.accounts_url = f"{base_url}/webhook/bank/accounts"
        self.transactions_url = f"{base_url}/webhook/bank/transactions"
        
        logger.info(f"BankAPIClient initialized with base URL: {base_url}")
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and parameters"""
        key_string = f"{endpoint}_{str(sorted(params.items()))}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _fetch_with_cache(self, url: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Fetch data with caching support
        
        Args:
            url: Endpoint URL
            params: Query parameters
            
        Returns:
            List of records
        """
        params = params or {}
        cache_key = self._get_cache_key(url, params)
        
        # Check cache
        if cache_key in cache:
            logger.info(f"Cache hit for {url}")
            return cache[cache_key]
        
        # Fetch from API
        logger.info(f"Cache miss - fetching from {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Store in cache
            cache[cache_key] = data
            logger.info(f"Cached {len(data)} records from {url}")
            
            return data
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from {url}: {e}")
            raise
    
    def get_customers(self) -> pd.DataFrame:
        """
        Fetch all customers
        
        Returns:
            DataFrame with customer data
        """
        logger.info("Fetching customers...")
        response = self._fetch_with_cache(self.customers_url)
        # Extract customers array from response
        data = response.get('customers', []) if isinstance(response, dict) else response
        df = pd.DataFrame(data)
        logger.info(f"Retrieved {len(df)} customers")
        return df
    
    def get_accounts(self) -> pd.DataFrame:
        """
        Fetch all accounts
        
        Returns:
            DataFrame with account data
        """
        logger.info("Fetching accounts...")
        response = self._fetch_with_cache(self.accounts_url)
        # Extract accounts array from response
        data = response.get('accounts', []) if isinstance(response, dict) else response
        df = pd.DataFrame(data)
        logger.info(f"Retrieved {len(df)} accounts")
        return df
    
    def get_transactions(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch transactions with optional filters
        
        Args:
            date_from: Start date (YYYY-MM-DD format)
            date_to: End date (YYYY-MM-DD format)
            limit: Maximum number of transactions
            
        Returns:
            DataFrame with transaction data
        """
        logger.info(f"Fetching transactions (date_from={date_from}, date_to={date_to}, limit={limit})")
        
        # Build parameters for caching
        params = {}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        if limit:
            params['limit'] = limit
        
        # Fetch all transactions (filtering will be done in Python for now)
        response = self._fetch_with_cache(self.transactions_url, params)
        # Extract transactions array from response
        data = response.get('transactions', []) if isinstance(response, dict) else response
        df = pd.DataFrame(data)
        
        # Apply filters
        if date_from and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[df['timestamp'] >= pd.to_datetime(date_from)]
        
        if date_to and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[df['timestamp'] <= pd.to_datetime(date_to)]
        
        if limit:
            df = df.head(limit)
        
        logger.info(f"Retrieved {len(df)} transactions after filtering")
        return df
    
    def get_enriched_transactions(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch and enrich transactions with customer and account data
        
        This performs a JOIN of:
        - transactions
        - customers (on customer_id)
        - accounts (on account_id)
        
        Args:
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum transactions
            
        Returns:
            Enriched DataFrame with all data combined
        """
        start_time = datetime.now()
        logger.info("Fetching enriched transactions...")
        
        # Fetch all three datasets
        transactions = self.get_transactions(date_from, date_to, limit)
        customers = self.get_customers()
        accounts = self.get_accounts()
        
        # JOIN transactions with customers
        enriched = transactions.merge(
            customers,
            on='customer_id',
            how='left',
            suffixes=('', '_customer')
        )
        
        # JOIN with accounts
        enriched = enriched.merge(
            accounts,
            on='account_id',
            how='left',
            suffixes=('', '_account')
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Enriched {len(enriched)} transactions in {elapsed:.2f}s")
        
        return enriched
    
    def clear_cache(self):
        """Clear all cached data"""
        cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(cache),
            'maxsize': cache.maxsize,
            'ttl_seconds': cache.ttl,
            'currsize': cache.currsize
        }
