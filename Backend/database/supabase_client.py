"""
Supabase Client Module
Handles connection to Supabase database
"""

import os
import logging
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from Backend/.env regardless of working directory
BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BACKEND_ROOT / ".env", override=True)

logger = logging.getLogger(__name__)

# Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
supabase_client: Client = None


def initialize_supabase() -> Client:
    """
    Initialize and return the Supabase client.
    Prefer service role key for backend server operations.
    Fallback to SUPABASE_KEY/SUPABASE_ANON_KEY when needed.
    """
    global supabase_client

    if supabase_client is not None:
        return supabase_client

    selected_key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY or SUPABASE_ANON_KEY
    selected_key_name = (
        "SUPABASE_SERVICE_ROLE_KEY"
        if SUPABASE_SERVICE_ROLE_KEY
        else "SUPABASE_KEY"
        if SUPABASE_KEY
        else "SUPABASE_ANON_KEY"
        if SUPABASE_ANON_KEY
        else None
    )

    if not SUPABASE_URL or not selected_key:
        raise ValueError(
            "SUPABASE_URL and one of SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY/SUPABASE_ANON_KEY must be set in environment variables"
        )

    try:
        supabase_client = create_client(SUPABASE_URL, selected_key)
        logger.info(
            "Successfully initialized Supabase client using %s",
            selected_key_name
        )
        return supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise


def get_supabase() -> Client:
    """
    Get the Supabase client instance.
    Initializes if not already done.
    """
    global supabase_client

    if supabase_client is None:
        supabase_client = initialize_supabase()

    return supabase_client


def check_connection() -> dict:
    """
    Test the connection to Supabase.
    Returns connection status and basic info.
    """
    try:
        client = get_supabase()
        # Test connection by checking auth status
        response = client.auth.get_session()
        return {
            "status": "connected",
            "message": "Successfully connected to Supabase",
            "url": SUPABASE_URL
        }
    except Exception as e:
        logger.error(f"Supabase connection failed: {str(e)}")
        return {
            "status": "disconnected",
            "message": f"Failed to connect to Supabase: {str(e)}",
            "url": SUPABASE_URL
        }
