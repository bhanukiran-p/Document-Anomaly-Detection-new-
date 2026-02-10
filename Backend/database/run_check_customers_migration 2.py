"""
Migration script to create check_customers table and update checks table
"""
import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logger.error("Missing Supabase credentials")
    sys.exit(1)

# Extract database connection details from Supabase URL
# URL format: https://xxxx.supabase.co
project_id = SUPABASE_URL.split('//')[1].split('.')[0]
db_host = f"{project_id}.db.supabase.co"
db_port = 5432
db_name = "postgres"
db_user = "postgres"
db_password = SUPABASE_SERVICE_ROLE_KEY

try:
    # Connect to database
    logger.info(f"Connecting to database at {db_host}...")
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        sslmode='require'
    )
    cursor = conn.cursor()
    logger.info("Connected successfully!")
    
    # Read the migration SQL file
    migration_file = os.path.join(os.path.dirname(__file__), 'create_check_customers.sql')
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    logger.info("Executing migration...")
    cursor.execute(migration_sql)
    conn.commit()
    logger.info("Migration completed successfully!")
    
    # Verify table was created
    cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'check_customers');")
    exists = cursor.fetchone()[0]
    if exists:
        logger.info("✅ check_customers table created successfully!")
    else:
        logger.warning("⚠️ Table creation may have failed - table not found after migration")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    logger.error(f"Migration failed: {e}")
    sys.exit(1)
