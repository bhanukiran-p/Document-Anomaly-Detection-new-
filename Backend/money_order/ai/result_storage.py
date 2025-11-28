"""
Result Storage Module for Analysis Results
Saves and retrieves complete fraud analysis JSON files
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional


class ResultStorage:
    """
    Manage storage and retrieval of fraud analysis results
    """

    def __init__(self, storage_dir: str = 'analysis_results'):
        """
        Initialize result storage

        Args:
            storage_dir: Directory to store analysis JSON files
        """
        self.storage_dir = storage_dir

        # Create directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
            print(f"Created results storage directory: {self.storage_dir}")

    def save_analysis_result(self, analysis_data: Dict, serial_number: str = None) -> str:
        """
        Save complete analysis result to JSON file

        Args:
            analysis_data: Complete analysis dictionary
            serial_number: Money order serial number (for filename)

        Returns:
            analysis_id: Unique ID for this analysis (filename without extension)
        """
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Milliseconds
        serial_clean = self._clean_serial_for_filename(serial_number) if serial_number else 'unknown'
        analysis_id = f"analysis_{timestamp}_{serial_clean}"
        filename = f"{analysis_id}.json"
        filepath = os.path.join(self.storage_dir, filename)

        # Add metadata
        analysis_data['analysis_id'] = analysis_id
        analysis_data['saved_timestamp'] = datetime.now().isoformat()

        # Save to file
        try:
            with open(filepath, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            print(f"✅ Analysis saved: {filepath}")
            return analysis_id
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")
            return None

    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict]:
        """
        Retrieve analysis by ID

        Args:
            analysis_id: Analysis ID (filename without extension)

        Returns:
            Analysis dictionary or None
        """
        filepath = os.path.join(self.storage_dir, f"{analysis_id}.json")

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading analysis {analysis_id}: {e}")
            return None

    def get_all_stored_results(self) -> List[Dict]:
        """
        Load all stored analysis results

        Returns:
            List of analysis dictionaries
        """
        results = []

        if not os.path.exists(self.storage_dir):
            return results

        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        results.append(data)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    continue

        return results

    def get_recent_results(self, limit: int = 10) -> List[Dict]:
        """
        Get N most recent analysis results

        Args:
            limit: Maximum number of results to return

        Returns:
            List of recent analysis dictionaries, sorted by timestamp (newest first)
        """
        all_results = self.get_all_stored_results()

        # Sort by saved_timestamp (newest first)
        sorted_results = sorted(
            all_results,
            key=lambda x: x.get('saved_timestamp', ''),
            reverse=True
        )

        return sorted_results[:limit]

    def search_by_issuer(self, issuer: str, limit: int = 5) -> List[Dict]:
        """
        Search stored results by issuer

        Args:
            issuer: Issuer name to search for
            limit: Maximum results to return

        Returns:
            List of matching analyses
        """
        all_results = self.get_all_stored_results()
        matches = []

        for result in all_results:
            # Check both raw and normalized data
            extracted_issuer = result.get('extracted_data', {}).get('issuer', '')
            normalized_issuer = result.get('normalized_data', {}).get('issuer_name', '')

            if issuer.lower() in extracted_issuer.lower() or issuer.lower() in normalized_issuer.lower():
                matches.append(result)

        # Sort by timestamp (newest first) and limit
        sorted_matches = sorted(
            matches,
            key=lambda x: x.get('saved_timestamp', ''),
            reverse=True
        )

        return sorted_matches[:limit]

    def search_by_amount_range(self, min_amount: float, max_amount: float, limit: int = 5) -> List[Dict]:
        """
        Search stored results by amount range

        Args:
            min_amount: Minimum amount
            max_amount: Maximum amount
            limit: Maximum results

        Returns:
            List of matching analyses
        """
        all_results = self.get_all_stored_results()
        matches = []

        for result in all_results:
            # Try to extract amount
            amount = None

            # From normalized data
            normalized_data = result.get('normalized_data', {})
            if normalized_data:
                amount_obj = normalized_data.get('amount_numeric', {})
                if isinstance(amount_obj, dict):
                    amount = amount_obj.get('value', 0)
                elif isinstance(amount_obj, (int, float)):
                    amount = amount_obj

            # Fallback to extracted data
            if amount is None:
                extracted_data = result.get('extracted_data', {})
                amount_str = extracted_data.get('amount', '').replace('$', '').replace(',', '')
                try:
                    amount = float(amount_str) if amount_str else 0
                except:
                    amount = 0

            # Check if in range
            if min_amount <= amount <= max_amount:
                matches.append(result)

        # Sort and limit
        sorted_matches = sorted(
            matches,
            key=lambda x: x.get('saved_timestamp', ''),
            reverse=True
        )

        return sorted_matches[:limit]

    def _clean_serial_for_filename(self, serial: str) -> str:
        """Clean serial number for use in filename"""
        if not serial:
            return 'unknown'

        # Remove special characters, keep alphanumeric
        cleaned = ''.join(c for c in serial if c.isalnum())
        # Limit length
        return cleaned[:20]


# Convenience functions
def save_analysis_result(analysis_data: Dict, serial_number: str = None, storage_dir: str = 'analysis_results') -> str:
    """
    Save analysis result (convenience function)

    Args:
        analysis_data: Complete analysis dictionary
        serial_number: Money order serial number
        storage_dir: Storage directory path

    Returns:
        analysis_id: Unique ID for this analysis
    """
    storage = ResultStorage(storage_dir)
    return storage.save_analysis_result(analysis_data, serial_number)


def get_recent_analyses(limit: int = 10, storage_dir: str = 'analysis_results') -> List[Dict]:
    """
    Get recent analyses (convenience function)

    Args:
        limit: Number of recent analyses to retrieve
        storage_dir: Storage directory path

    Returns:
        List of recent analysis dictionaries
    """
    storage = ResultStorage(storage_dir)
    return storage.get_recent_results(limit)
