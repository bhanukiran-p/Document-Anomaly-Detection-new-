"""
CSV Duplicate Detection Guardrail
Detects duplicate CSV file uploads using file hash and content fingerprinting
"""

import hashlib
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class CSVDuplicateDetector:
    """
    Detects duplicate CSV file uploads using multiple strategies:
    1. File hash (MD5) - Exact file match
    2. Content fingerprint - Same data with different formatting
    3. Transaction signature - Same transactions in different order
    """

    def __init__(self, cache_file: str = None, cache_ttl_hours: int = 24):
        """
        Initialize duplicate detector

        Args:
            cache_file: Path to JSON cache file for storing upload history
            cache_ttl_hours: How long to keep upload history (default: 24 hours)
        """
        if cache_file is None:
            # Default to real_time/models directory
            base_dir = Path(__file__).parent / 'models'
            base_dir.mkdir(exist_ok=True)
            cache_file = str(base_dir / 'csv_upload_cache.json')

        self.cache_file = cache_file
        self.cache_ttl_hours = cache_ttl_hours
        self.upload_cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load upload cache from file"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    # Clean expired entries
                    cache = self._clean_expired_entries(cache)
                    logger.info(f"Loaded {len(cache)} cached CSV uploads")
                    return cache
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

        return {}

    def _save_cache(self):
        """Save upload cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.upload_cache, f, indent=2)
            logger.debug(f"Saved {len(self.upload_cache)} entries to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _clean_expired_entries(self, cache: Dict) -> Dict:
        """Remove entries older than TTL"""
        cutoff_time = datetime.now() - timedelta(hours=self.cache_ttl_hours)
        cutoff_timestamp = cutoff_time.isoformat()

        cleaned = {
            key: value
            for key, value in cache.items()
            if value.get('timestamp', '') > cutoff_timestamp
        }

        removed = len(cache) - len(cleaned)
        if removed > 0:
            logger.info(f"Removed {removed} expired cache entries")

        return cleaned

    def compute_file_hash(self, filepath: str) -> str:
        """
        Compute MD5 hash of file

        Args:
            filepath: Path to CSV file

        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute file hash: {e}")
            return None

    def compute_content_fingerprint(self, filepath: str) -> Optional[str]:
        """
        Compute content fingerprint based on data values (ignores column order, formatting)

        Args:
            filepath: Path to CSV file

        Returns:
            Content fingerprint hash or None if failed
        """
        try:
            df = pd.read_csv(filepath)

            # Create fingerprint based on:
            # 1. Row count
            # 2. Column names (sorted)
            # 3. Hash of all values (sorted)

            row_count = len(df)
            col_signature = '|'.join(sorted(df.columns.tolist()))

            # Convert all data to strings and create sorted signature
            all_values = []
            for col in df.columns:
                values = df[col].astype(str).tolist()
                all_values.extend(values)

            # Sort all values for order-independent fingerprint
            all_values.sort()
            values_signature = '|'.join(all_values[:1000])  # Use first 1000 for performance

            # Combine into fingerprint
            fingerprint_data = f"{row_count}|{col_signature}|{values_signature}"
            fingerprint_hash = hashlib.md5(fingerprint_data.encode()).hexdigest()

            return fingerprint_hash

        except Exception as e:
            logger.error(f"Failed to compute content fingerprint: {e}")
            return None

    def compute_transaction_signature(self, filepath: str) -> Optional[str]:
        """
        Compute signature based on transaction identifiers (amount, merchant, date)

        Args:
            filepath: Path to CSV file

        Returns:
            Transaction signature hash or None if failed
        """
        try:
            df = pd.read_csv(filepath)

            # Look for key transaction fields (handle different column name variations)
            amount_cols = ['amount', 'transaction_amount', 'amt']
            merchant_cols = ['merchant', 'merchant_name', 'store', 'vendor']
            date_cols = ['date', 'transaction_date', 'timestamp', 'datetime']

            # Find which columns exist
            amount_col = next((c for c in amount_cols if c in df.columns), None)
            merchant_col = next((c for c in merchant_cols if c in df.columns), None)

            if not amount_col:
                logger.warning("No amount column found for transaction signature")
                return None

            # Create signature from key fields
            signatures = []
            for _, row in df.iterrows():
                sig_parts = [str(row[amount_col])]
                if merchant_col:
                    sig_parts.append(str(row[merchant_col]))
                signatures.append('|'.join(sig_parts))

            # Sort for order independence
            signatures.sort()
            signature_data = '||'.join(signatures[:1000])  # Use first 1000 for performance
            signature_hash = hashlib.md5(signature_data.encode()).hexdigest()

            return signature_hash

        except Exception as e:
            logger.error(f"Failed to compute transaction signature: {e}")
            return None

    def check_duplicate(
        self,
        filepath: str,
        filename: str,
        check_file_hash: bool = True,
        check_content: bool = True,
        check_transactions: bool = True
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Check if CSV file is a duplicate

        Args:
            filepath: Path to CSV file
            filename: Original filename
            check_file_hash: Check exact file match (default: True)
            check_content: Check content fingerprint match (default: True)
            check_transactions: Check transaction signature match (default: True)

        Returns:
            Tuple of (is_duplicate, duplicate_type, previous_upload_info)
            - is_duplicate: True if duplicate detected
            - duplicate_type: 'exact_file', 'same_content', 'same_transactions', or 'none'
            - previous_upload_info: Info about previous upload if duplicate
        """
        file_hash = None
        content_fp = None
        txn_sig = None

        # Compute hashes based on enabled checks
        if check_file_hash:
            file_hash = self.compute_file_hash(filepath)

        if check_content:
            content_fp = self.compute_content_fingerprint(filepath)

        if check_transactions:
            txn_sig = self.compute_transaction_signature(filepath)

        # Check cache for matches
        for cache_key, cache_entry in self.upload_cache.items():
            # Check exact file match
            if file_hash and cache_entry.get('file_hash') == file_hash:
                logger.warning(f"DUPLICATE DETECTED: Exact file match - {filename}")
                return True, 'exact_file', cache_entry

            # Check content fingerprint match
            if content_fp and cache_entry.get('content_fingerprint') == content_fp:
                logger.warning(f"DUPLICATE DETECTED: Same content - {filename}")
                return True, 'same_content', cache_entry

            # Check transaction signature match
            if txn_sig and cache_entry.get('transaction_signature') == txn_sig:
                logger.warning(f"DUPLICATE DETECTED: Same transactions - {filename}")
                return True, 'same_transactions', cache_entry

        # Not a duplicate - add to cache
        cache_key = file_hash or content_fp or txn_sig or filename
        self.upload_cache[cache_key] = {
            'filename': filename,
            'file_hash': file_hash,
            'content_fingerprint': content_fp,
            'transaction_signature': txn_sig,
            'timestamp': datetime.now().isoformat(),
            'filepath': filepath,
            'analysis_result': None  # Will be populated after first analysis
        }

        self._save_cache()
        logger.info(f"New CSV file cached: {filename}")

        return False, 'none', None

    def cache_analysis_result(self, filepath: str, analysis_result: Dict):
        """
        Cache analysis result for a file to enable fast retrieval on duplicates

        Args:
            filepath: Path to CSV file
            analysis_result: Complete analysis result dictionary
        """
        file_hash = self.compute_file_hash(filepath)

        # Find matching cache entry and store result
        for cache_key, cache_entry in self.upload_cache.items():
            if cache_entry.get('file_hash') == file_hash:
                cache_entry['analysis_result'] = analysis_result
                self._save_cache()
                logger.info(f"Cached analysis result for {cache_entry['filename']}")
                return

        logger.warning(f"Could not find cache entry to store analysis result")

    def get_cached_analysis(self, filepath: str) -> Optional[Dict]:
        """
        Get cached analysis result for a file

        Args:
            filepath: Path to CSV file

        Returns:
            Cached analysis result or None if not available
        """
        file_hash = self.compute_file_hash(filepath)

        for cache_entry in self.upload_cache.values():
            if cache_entry.get('file_hash') == file_hash:
                result = cache_entry.get('analysis_result')
                if result:
                    logger.info(f"Retrieved cached analysis for {cache_entry['filename']}")
                return result

        return None

    def get_upload_stats(self) -> Dict:
        """
        Get statistics about cached uploads

        Returns:
            Dictionary with upload statistics
        """
        return {
            'total_uploads': len(self.upload_cache),
            'cache_file': self.cache_file,
            'cache_ttl_hours': self.cache_ttl_hours,
            'oldest_upload': min(
                (entry['timestamp'] for entry in self.upload_cache.values()),
                default=None
            ),
            'newest_upload': max(
                (entry['timestamp'] for entry in self.upload_cache.values()),
                default=None
            )
        }

    def clear_cache(self):
        """Clear all cached uploads"""
        self.upload_cache = {}
        self._save_cache()
        logger.info("Upload cache cleared")


# Singleton instance
_detector_instance = None


def get_duplicate_detector() -> CSVDuplicateDetector:
    """
    Get singleton instance of duplicate detector

    Returns:
        CSVDuplicateDetector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CSVDuplicateDetector()
    return _detector_instance
