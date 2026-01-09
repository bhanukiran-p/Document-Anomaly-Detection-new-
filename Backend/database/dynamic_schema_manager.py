"""
Dynamic Schema Manager
Automatically detects new fields in extracted document data and adds them as columns to database tables.
"""

import logging
import json
import re
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import requests
from database.supabase_client import get_supabase
import os

logger = logging.getLogger(__name__)


class DynamicSchemaManager:
    """Manages dynamic schema evolution for document tables"""
    
    # Map document types to their table names
    TABLE_MAPPING = {
        'check': 'checks',
        'paystub': 'paystubs',
        'bank_statement': 'bank_statements',
        'money_order': 'money_orders'
    }
    
    # Fields that should be excluded from auto-column addition
    # These are either handled specially or are metadata fields
    EXCLUDED_FIELDS = {
        'raw_ocr_text', 'raw_text', 'raw_fields', 'status', 'timestamp',
        'document_id', 'user_id', 'file_name', 'created_at', 'updated_at',
        'extracted_data', 'ml_analysis', 'ai_analysis', 'anomalies',
        'normalized_data', 'normalization_completeness'
    }
    
    # Fields that map to existing columns (don't add as new columns)
    FIELD_MAPPINGS = {
        'check': {
            'date': 'check_date',
            'amount_numeric': 'amount',
            'pay_to': 'payee_name',
            'word_amount': 'amount_words',
            'signature': 'signature_detected'
        },
        'paystub': {},
        'bank_statement': {
            'account_holder': 'account_holder_name',
            'ending_balance': 'closing_balance',
            'beginning_balance': 'opening_balance',
            'statement_period_start_date': 'statement_period_start_date',
            'statement_period_end_date': 'statement_period_end_date'
        },
        'money_order': {
            'serial_number': 'money_order_number',
            'amount': 'amount'
        }
    }
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the Dynamic Schema Manager
        
        Args:
            enabled: Whether automatic column addition is enabled
        """
        self.enabled = enabled
        self.supabase = get_supabase()
        self._column_cache: Dict[str, Set[str]] = {}  # Cache table columns
        
    def _get_supabase_service_key(self) -> Optional[str]:
        """Get Supabase service role key for admin operations"""
        return os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    def _get_supabase_url(self) -> Optional[str]:
        """Get Supabase URL"""
        return os.getenv('SUPABASE_URL')
    
    def _extract_db_connection_info(self) -> Optional[Dict[str, str]]:
        """
        Extract database connection info from Supabase URL and environment variables
        
        Returns:
            Dict with db_host, db_name, db_user, db_password, db_port or None
        """
        supabase_url = self._get_supabase_url()
        if not supabase_url:
            return None
        
        try:
            # Extract project ID from URL: https://xxxx.supabase.co -> xxxx
            project_id = supabase_url.split('//')[1].split('.')[0]
            db_host = f"{project_id}.db.supabase.co"
        except Exception:
            return None
        
        # Get database password (must be set separately - not the service role key)
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        if not db_password:
            return None
        
        return {
            'db_host': db_host,
            'db_name': os.getenv('SUPABASE_DB_NAME', 'postgres'),
            'db_user': os.getenv('SUPABASE_DB_USER', 'postgres'),
            'db_password': db_password,
            'db_port': os.getenv('SUPABASE_DB_PORT', '5432')
        }
    
    def _execute_sql(self, sql: str) -> bool:
        """
        Execute SQL statement using direct database connection or Supabase RPC
        
        Args:
            sql: SQL statement to execute
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        # Try method 1: Direct PostgreSQL connection (psycopg2)
        try:
            import psycopg2
            
            # Get database connection info
            db_info = self._extract_db_connection_info()
            
            if db_info:
                # Try direct connection with SSL
                try:
                    conn = psycopg2.connect(
                        host=db_info['db_host'],
                        database=db_info['db_name'],
                        user=db_info['db_user'],
                        password=db_info['db_password'],
                        port=db_info['db_port'],
                        sslmode='require',
                        connect_timeout=10
                    )
                    conn.autocommit = True
                    cursor = conn.cursor()
                    cursor.execute(sql)
                    cursor.close()
                    conn.close()
                    logger.info(f"Successfully executed SQL: {sql[:100]}...")
                    return True
                except psycopg2.OperationalError as e:
                    # Try connection pooling endpoint (port 6543)
                    logger.debug(f"Direct connection failed: {e}, trying connection pooler...")
                    try:
                        conn = psycopg2.connect(
                            host=db_info['db_host'],
                            database=db_info['db_name'],
                            user=db_info['db_user'],
                            password=db_info['db_password'],
                            port=6543,  # Connection pooler port
                            sslmode='require',
                            connect_timeout=10
                        )
                        conn.autocommit = True
                        cursor = conn.cursor()
                        cursor.execute(sql)
                        cursor.close()
                        conn.close()
                        logger.info(f"Successfully executed SQL via pooler: {sql[:100]}...")
                        return True
                    except Exception as e2:
                        logger.debug(f"Pooler connection also failed: {e2}")
                        raise e  # Raise original error
        except ImportError:
            logger.debug("psycopg2 not available, trying alternative methods")
        except Exception as e:
            logger.debug(f"Direct DB connection failed: {e}, trying alternative methods")
        
        # Try method 2: Supabase RPC function (if exists)
        try:
            # Try to call a custom RPC function that executes SQL
            # This requires creating the function in Supabase first
            response = self.supabase.rpc('execute_sql', {'sql_query': sql}).execute()
            if response.data:
                logger.info(f"Successfully executed SQL via RPC")
                return True
        except Exception as e:
            logger.debug(f"RPC execution failed: {e}")
        
        # Try method 2b: Use Supabase REST API with service role key to execute SQL
        # Note: This requires the execute_sql RPC function to be created
        try:
            service_key = self._get_supabase_service_key()
            supabase_url = self._get_supabase_url()
            if service_key and supabase_url:
                import requests
                headers = {
                    'apikey': service_key,
                    'Authorization': f'Bearer {service_key}',
                    'Content-Type': 'application/json'
                }
                # Try calling execute_sql RPC
                response = requests.post(
                    f"{supabase_url}/rest/v1/rpc/execute_sql",
                    headers=headers,
                    json={'sql_query': sql},
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"Successfully executed SQL via REST API RPC")
                    return True
        except Exception as e:
            logger.debug(f"REST API RPC execution failed: {e}")
        
        # Method 3: Log SQL for manual execution
        logger.warning(f"Could not auto-execute SQL. Please run manually in Supabase SQL Editor:")
        logger.warning(f"{sql}")
        return False
    
    def _get_table_columns(self, table_name: str, use_cache: bool = True) -> Set[str]:
        """
        Get existing columns for a table
        
        Args:
            table_name: Name of the table
            use_cache: Whether to use cached column list
            
        Returns:
            Set of column names
        """
        if use_cache and table_name in self._column_cache:
            return self._column_cache[table_name]
        
        columns = set()
        
        try:
            # Method 1: Direct PostgreSQL connection (most reliable)
            try:
                import psycopg2
                
                db_info = self._extract_db_connection_info()
                
                if db_info:
                    # Try direct connection with SSL
                    try:
                        conn = psycopg2.connect(
                            host=db_info['db_host'],
                            database=db_info['db_name'],
                            user=db_info['db_user'],
                            password=db_info['db_password'],
                            port=db_info['db_port'],
                            sslmode='require',
                            connect_timeout=10
                        )
                    except psycopg2.OperationalError:
                        # Try connection pooler port
                        conn = psycopg2.connect(
                            host=db_info['db_host'],
                            database=db_info['db_name'],
                            user=db_info['db_user'],
                            password=db_info['db_password'],
                            port=6543,  # Connection pooler port
                            sslmode='require',
                            connect_timeout=10
                        )
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        AND table_schema = 'public'
                        ORDER BY ordinal_position;
                    """, (table_name,))
                    columns = {row[0] for row in cursor.fetchall()}
                    cursor.close()
                    conn.close()
                    logger.debug(f"Retrieved {len(columns)} columns for {table_name} via direct DB connection")
                    self._column_cache[table_name] = columns
                    return columns
            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"Direct DB connection failed: {e}")
            
            # Method 2: Try RPC function (if exists in Supabase)
            try:
                response = self.supabase.rpc('get_table_columns', {'table_name': table_name}).execute()
                if response.data:
                    # Response might be list of strings or list of dicts
                    if isinstance(response.data, list):
                        if len(response.data) > 0:
                            if isinstance(response.data[0], dict):
                                columns = {row.get('column_name', '') for row in response.data if row.get('column_name')}
                            else:
                                columns = set(response.data)
                    if columns:
                        self._column_cache[table_name] = columns
                        return columns
            except Exception as e:
                logger.debug(f"RPC function not available: {e}")
            
            # Method 3: Infer from sample query (fallback)
            try:
                response = self.supabase.table(table_name).select('*').limit(1).execute()
                if response.data and len(response.data) > 0:
                    columns = set(response.data[0].keys())
                    logger.debug(f"Inferred {len(columns)} columns for {table_name} from sample query")
                    self._column_cache[table_name] = columns
                    return columns
            except Exception as e:
                logger.debug(f"Could not infer columns from table query: {e}")
            
            # If we couldn't determine columns, log warning but continue
            if not columns:
                logger.warning(f"Could not determine columns for table {table_name}. Will attempt to add columns and catch errors.")
            
            self._column_cache[table_name] = columns
            return columns
            
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {e}")
            return set()
    
    def _infer_column_type(self, value: Any, field_name: str) -> str:
        """
        Infer PostgreSQL column type from Python value
        
        Args:
            value: The value to infer type from
            field_name: Name of the field (for context)
            
        Returns:
            PostgreSQL column type string
        """
        if value is None:
            return 'TEXT'  # Default to TEXT for nullable columns
        
        # Check for common patterns in field names
        if 'date' in field_name.lower():
            return 'DATE'
        if 'amount' in field_name.lower() or 'price' in field_name.lower() or 'balance' in field_name.lower():
            return 'NUMERIC'
        if 'count' in field_name.lower() or 'number' in field_name.lower():
            # Could be INTEGER or NUMERIC, check value
            if isinstance(value, int):
                return 'INTEGER'
            return 'NUMERIC'
        if 'id' in field_name.lower() and isinstance(value, (str, int)):
            return 'TEXT'  # IDs are usually TEXT in this system
        
        # Type-based inference
        if isinstance(value, bool):
            return 'BOOLEAN'
        if isinstance(value, int):
            return 'INTEGER'
        if isinstance(value, float):
            return 'NUMERIC'
        if isinstance(value, (list, dict)):
            return 'JSONB'
        if isinstance(value, str):
            # Check if it's a date string
            if self._is_date_string(value):
                return 'DATE'
            # Check if it's a number string
            if self._is_numeric_string(value):
                return 'NUMERIC'
            # Long strings go to TEXT
            if len(value) > 255:
                return 'TEXT'
            return 'TEXT'
        
        return 'TEXT'  # Default
    
    def _is_date_string(self, value: str) -> bool:
        """Check if string looks like a date"""
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
        return False
    
    def _is_numeric_string(self, value: str) -> bool:
        """Check if string is numeric"""
        try:
            float(value.replace('$', '').replace(',', '').strip())
            return True
        except ValueError:
            return False
    
    def _normalize_field_name(self, field_name: str) -> str:
        """
        Normalize field name to valid PostgreSQL column name
        
        Args:
            field_name: Original field name
            
        Returns:
            Normalized column name
        """
        # Replace spaces and special chars with underscores
        normalized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Ensure it starts with a letter
        if normalized and normalized[0].isdigit():
            normalized = 'col_' + normalized
        # Convert to lowercase
        normalized = normalized.lower()
        # Ensure it's not a reserved word
        reserved_words = {'select', 'insert', 'update', 'delete', 'where', 'from', 'table', 'column'}
        if normalized in reserved_words:
            normalized = normalized + '_field'
        return normalized
    
    def _should_exclude_field(self, field_name: str, document_type: str) -> bool:
        """
        Check if a field should be excluded from auto-column addition
        
        Args:
            field_name: Name of the field
            document_type: Type of document
            
        Returns:
            True if field should be excluded
        """
        # Check excluded fields
        if field_name.lower() in self.EXCLUDED_FIELDS:
            return True
        
        # Check if field maps to existing column
        mappings = self.FIELD_MAPPINGS.get(document_type, {})
        if field_name.lower() in mappings:
            return True
        
        return False
    
    def ensure_columns_exist(self, document_type: str, extracted_data: Dict[str, Any]) -> List[str]:
        """
        Ensure all fields in extracted_data have corresponding columns in the database table.
        Adds missing columns automatically.
        
        Args:
            document_type: Type of document (check, paystub, bank_statement, money_order)
            extracted_data: Dictionary of extracted field data
            
        Returns:
            List of column names that were added (or attempted to be added)
        """
        if not self.enabled:
            return []
        
        table_name = self.TABLE_MAPPING.get(document_type)
        if not table_name:
            logger.warning(f"Unknown document type: {document_type}")
            return []
        
        # Get existing columns
        existing_columns = self._get_table_columns(table_name)
        
        # Flatten extracted_data if it's nested
        flat_data = self._flatten_dict(extracted_data)
        
        # Find missing columns
        missing_columns = []
        added_columns = []
        
        for field_name, value in flat_data.items():
            # Normalize field name
            normalized_name = self._normalize_field_name(field_name)
            
            # Check if should exclude
            if self._should_exclude_field(field_name, document_type):
                continue
            
            # Check if maps to existing column
            mappings = self.FIELD_MAPPINGS.get(document_type, {})
            mapped_name = mappings.get(field_name.lower())
            if mapped_name and mapped_name.lower() in existing_columns:
                continue
            
            # Check if column already exists
            if normalized_name in existing_columns:
                continue
            
            # Infer column type
            column_type = self._infer_column_type(value, field_name)
            
            # Add column
            sql = f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS {normalized_name} {column_type} DEFAULT NULL;
            """
            
            logger.info(f"Adding column {normalized_name} ({column_type}) to table {table_name}")
            
            # Try to execute SQL
            if self._execute_sql(sql):
                added_columns.append(normalized_name)
                existing_columns.add(normalized_name)  # Update cache
            else:
                # Log SQL for manual execution
                logger.warning(f"Could not auto-add column. Please run manually:\n{sql}")
                missing_columns.append((normalized_name, column_type, sql))
        
        # Log summary
        if added_columns:
            logger.info(f"Successfully added {len(added_columns)} columns to {table_name}: {added_columns}")
        
        if missing_columns:
            logger.warning(f"Could not auto-add {len(missing_columns)} columns. SQL statements logged above.")
        
        return added_columns
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """
        Flatten nested dictionary
        
        Args:
            data: Dictionary to flatten
            parent_key: Parent key prefix
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                # For lists of dicts, just use the key name (don't flatten further)
                items.append((new_key, v))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def clear_cache(self, table_name: Optional[str] = None):
        """
        Clear column cache
        
        Args:
            table_name: Specific table to clear cache for, or None to clear all
        """
        if table_name:
            self._column_cache.pop(table_name, None)
        else:
            self._column_cache.clear()


# Global instance
_schema_manager: Optional[DynamicSchemaManager] = None


def get_schema_manager(enabled: Optional[bool] = None) -> DynamicSchemaManager:
    """
    Get or create the global schema manager instance
    
    Args:
        enabled: Whether to enable auto-column addition (uses config if None)
        
    Returns:
        DynamicSchemaManager instance
    """
    global _schema_manager
    
    if enabled is None:
        # Check config
        enabled = os.getenv('ENABLE_AUTO_COLUMN_ADDITION', 'true').lower() == 'true'
    
    if _schema_manager is None:
        _schema_manager = DynamicSchemaManager(enabled=enabled)
    elif enabled != _schema_manager.enabled:
        _schema_manager.enabled = enabled
    
    return _schema_manager

