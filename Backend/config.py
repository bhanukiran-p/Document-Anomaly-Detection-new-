"""
Centralized Configuration Management
Loads all configuration from environment variables with validation and defaults
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with all application settings"""

    # ==================== PATHS ====================
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    LOG_DIR = os.getenv('LOG_DIR', str(BASE_DIR / 'logs'))

    # ==================== FLASK SETTINGS ====================
    SECRET_KEY = os.getenv('SECRET_KEY', 'check-extractor-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size (for large CSV files)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    # ==================== API KEYS ====================
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')
    LANGCHAIN_TRACING_V2 = os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'

    # ==================== MINDEE API CONFIGURATION ====================
    MINDEE_API_KEY = os.getenv('MINDEE_API_KEY')
    MINDEE_MODEL_ID_GLOBAL = os.getenv('MINDEE_MODEL_ID_GLOBAL', '7aacafab-160c-4a4e-8e35-bf46997f1a25')
    MINDEE_MODEL_ID_CHECK = os.getenv('MINDEE_MODEL_ID_CHECK', '7aacafab-160c-4a4e-8e35-bf46997f1a25')
    MINDEE_MODEL_ID_PAYSTUB = os.getenv('MINDEE_MODEL_ID_PAYSTUB', '15fab31e-ac0e-4ccc-83ed-39b9f65bb791')
    MINDEE_MODEL_ID_BANK_STATEMENT = os.getenv('MINDEE_MODEL_ID_BANK_STATEMENT', '1b63fd3d-72b4-4e00-9bab-bbd875338dea')
    MINDEE_MODEL_ID_MONEY_ORDER = os.getenv('MINDEE_MODEL_ID_MONEY_ORDER', '2bc6b632-9695-4e1a-bd3b-2dfaedf0844d')
    BANK_STATEMENT_MODEL_ID = os.getenv('BANK_STATEMENT_MODEL_ID', '1b63fd3d-72b4-4e00-9bab-bbd875338dea')

    # ==================== GOOGLE CLOUD CONFIGURATION ====================
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    # ==================== DATABASE CONFIGURATION ====================
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    # Database tables
    DB_TABLE_BANK_DICTIONARY = os.getenv('DB_TABLE_BANK_DICTIONARY', 'bank_dictionary')
    DB_TABLE_FINANCIAL_INSTITUTIONS = os.getenv('DB_TABLE_FINANCIAL_INSTITUTIONS', 'financial_institutions')
    DB_TABLE_ANALYZED_TRANSACTIONS = os.getenv('DB_TABLE_ANALYZED_TRANSACTIONS', 'analyzed_transactions')
    DB_TABLE_DOCUMENTS = os.getenv('DB_TABLE_DOCUMENTS', 'documents')
    DB_TABLE_CHECK_CUSTOMERS = os.getenv('DB_TABLE_CHECK_CUSTOMERS', 'check_customers')

    # ==================== ML MODEL CONFIGURATION ====================
    ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', str(BASE_DIR / 'ml_models' / 'trained_model.pkl'))
    USE_MOCK_ML_SCORES = os.getenv('USE_MOCK_ML_SCORES', 'true').lower() == 'true'

    # Mock data paths for development/testing
    ML_SCORES_CSV = os.getenv('ML_SCORES_CSV', str(BASE_DIR / 'ml_models' / 'mock_data' / 'ml_scores.csv'))
    CUSTOMER_HISTORY_CSV = os.getenv('CUSTOMER_HISTORY_CSV', str(BASE_DIR / 'ml_models' / 'mock_data' / 'customer_history.csv'))
    FRAUD_CASES_CSV = os.getenv('FRAUD_CASES_CSV', str(BASE_DIR / 'ml_models' / 'mock_data' / 'fraud_cases.csv'))

    # ==================== FRAUD DETECTION SETTINGS ====================
    FRAUD_THRESHOLD_HIGH = float(os.getenv('FRAUD_THRESHOLD_HIGH', '0.7'))
    FRAUD_THRESHOLD_MEDIUM = float(os.getenv('FRAUD_THRESHOLD_MEDIUM', '0.4'))
    FRAUD_THRESHOLD_LOW = float(os.getenv('FRAUD_THRESHOLD_LOW', '0.2'))

    # ==================== LOGGING CONFIGURATION ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE_MAX_BYTES = int(os.getenv('LOG_FILE_MAX_BYTES', str(10 * 1024 * 1024)))  # 10MB
    LOG_FILE_BACKUP_COUNT = int(os.getenv('LOG_FILE_BACKUP_COUNT', '5'))

    # ==================== FEATURE FLAGS ====================
    ENABLE_SIGNATURE_DETECTION = os.getenv('ENABLE_SIGNATURE_DETECTION', 'true').lower() == 'true'
    ENABLE_BANK_VALIDATION = os.getenv('ENABLE_BANK_VALIDATION', 'true').lower() == 'true'
    ENABLE_REAL_TIME_ANALYSIS = os.getenv('ENABLE_REAL_TIME_ANALYSIS', 'true').lower() == 'true'
    ENABLE_AUTOMATED_RETRAINING = os.getenv('ENABLE_AUTOMATED_RETRAINING', 'true').lower() == 'true'

    # ==================== AUTOMATED RETRAINING CONFIGURATION ====================
    RETRAINING_CONFIG_PATH = os.getenv('RETRAINING_CONFIG_PATH', str(BASE_DIR / 'training' / 'retraining_config.json'))

    # ==================== CORS SETTINGS ====================
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    @classmethod
    def validate(cls) -> list:
        """
        Validate critical configuration values
        Returns list of missing/invalid configurations
        """
        errors = []

        # Check critical API keys
        if not cls.MINDEE_API_KEY:
            errors.append("MINDEE_API_KEY is not set")

        # Check database configuration
        if not cls.SUPABASE_URL:
            errors.append("SUPABASE_URL is not set")
        if not cls.SUPABASE_KEY:
            errors.append("SUPABASE_KEY is not set")

        # Warn about development settings in production
        if cls.FLASK_ENV == 'production':
            if cls.SECRET_KEY == 'check-extractor-secret-key-change-in-production':
                errors.append("SECRET_KEY should be changed in production")
            if cls.FLASK_DEBUG:
                errors.append("FLASK_DEBUG should be False in production")

        return errors

    @classmethod
    def get_mindee_model_id(cls, document_type: str) -> Optional[str]:
        """
        Get Mindee model ID for a specific document type

        Args:
            document_type: Type of document (check, bank_statement, paystub, money_order)

        Returns:
            Model ID or None if not found
        """
        model_mapping = {
            'check': cls.MINDEE_MODEL_ID_CHECK,
            'bank_statement': cls.MINDEE_MODEL_ID_BANK_STATEMENT,
            'paystub': cls.MINDEE_MODEL_ID_PAYSTUB,
            'money_order': cls.MINDEE_MODEL_ID_MONEY_ORDER,
            'global': cls.MINDEE_MODEL_ID_GLOBAL
        }
        return model_mapping.get(document_type.lower())

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.ML_MODEL_PATH), exist_ok=True)

    @classmethod
    def setup_logging(cls):
        """
        Setup application-wide logging using centralized logging config
        Call this once at application startup
        """
        from logging_config import setup_application_logging
        setup_application_logging(
            log_dir=cls.LOG_DIR,
            log_level=cls.LOG_LEVEL
        )

    @classmethod
    def get_logger(cls, name: str):
        """
        Get a configured logger instance for a module

        Args:
            name: Module name (usually __name__)

        Returns:
            Configured logger instance

        Usage:
            from config import Config
            logger = Config.get_logger(__name__)
        """
        from logging_config import get_logger
        return get_logger(
            name,
            log_dir=cls.LOG_DIR,
            log_level=cls.LOG_LEVEL
        )


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production-specific configuration"""
    FLASK_ENV = 'production'
    FLASK_DEBUG = False
    LOG_LEVEL = 'WARNING'
    USE_MOCK_ML_SCORES = False


class TestingConfig(Config):
    """Testing-specific configuration"""
    FLASK_ENV = 'testing'
    FLASK_DEBUG = True
    USE_MOCK_ML_SCORES = True
    LOG_LEVEL = 'DEBUG'


# Configuration dictionary for easy access
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env_name: Optional[str] = None) -> Config:
    """
    Get configuration based on environment name

    Args:
        env_name: Environment name (development, production, testing)
        If None, uses FLASK_ENV environment variable

    Returns:
        Configuration class instance
    """
    if env_name is None:
        env_name = os.getenv('FLASK_ENV', 'development')

    return config_by_name.get(env_name, DevelopmentConfig)


# Export the current configuration
current_config = get_config()
