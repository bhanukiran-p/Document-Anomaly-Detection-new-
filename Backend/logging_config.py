"""
Centralized Logging Configuration
Provides consistent logging setup across all modules
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime


class LoggerSetup:
    """
    Centralized logger setup for the entire application
    Provides consistent logging configuration with file rotation
    """

    _loggers_configured = set()
    _root_configured = False

    @classmethod
    def setup_logger(
        cls,
        name: str,
        log_dir: str = 'logs',
        log_level: str = 'INFO',
        log_to_file: bool = True,
        log_to_console: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        format_string: Optional[str] = None
    ) -> logging.Logger:
        """
        Setup and return a logger with consistent configuration

        Args:
            name: Logger name (usually __name__)
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
            max_bytes: Maximum size of each log file before rotation
            backup_count: Number of backup files to keep
            format_string: Custom format string (uses default if None)

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)

        # Avoid reconfiguring the same logger
        if name in cls._loggers_configured:
            return logger

        # Clear any existing handlers
        logger.handlers = []
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Default format
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        formatter = logging.Formatter(format_string)

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler with rotation
        if log_to_file:
            # Create log directory if it doesn't exist
            os.makedirs(log_dir, exist_ok=True)

            # Create log file path
            log_filename = cls._get_log_filename(name)
            log_path = os.path.join(log_dir, log_filename)

            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

        # Mark as configured
        cls._loggers_configured.add(name)

        return logger

    @classmethod
    def setup_root_logger(
        cls,
        log_dir: str = 'logs',
        log_level: str = 'INFO',
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ):
        """
        Setup root logger (affects all loggers that don't have explicit handlers)

        Args:
            log_dir: Directory for log files
            log_level: Logging level
            max_bytes: Maximum size of each log file before rotation
            backup_count: Number of backup files to keep
        """
        if cls._root_configured:
            return

        # Create log directory
        os.makedirs(log_dir, exist_ok=True)

        # Format
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)

        # Root logger file handler
        root_log_path = os.path.join(log_dir, 'application.log')
        file_handler = RotatingFileHandler(
            root_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format=log_format,
            handlers=[file_handler, console_handler]
        )

        cls._root_configured = True

    @staticmethod
    def _get_log_filename(logger_name: str) -> str:
        """
        Generate log filename from logger name

        Args:
            logger_name: Name of the logger

        Returns:
            Log filename
        """
        # Convert module name to filename
        # e.g., 'check.check_extractor' -> 'check_extractor.log'
        if '.' in logger_name:
            filename = logger_name.split('.')[-1]
        else:
            filename = logger_name

        # Handle special cases
        if filename == '__main__':
            filename = 'main'

        return f"{filename}.log"

    @classmethod
    def get_logger(
        cls,
        name: str,
        log_dir: str = 'logs',
        log_level: str = 'INFO'
    ) -> logging.Logger:
        """
        Convenience method to get a configured logger

        Args:
            name: Logger name (usually __name__)
            log_dir: Directory for log files
            log_level: Logging level

        Returns:
            Configured logger instance
        """
        return cls.setup_logger(name, log_dir=log_dir, log_level=log_level)


# Convenience function for easy import
def get_logger(name: str, log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
    """
    Get a configured logger instance

    Usage:
        from logging_config import get_logger
        logger = get_logger(__name__)

    Args:
        name: Logger name (usually __name__)
        log_dir: Directory for log files
        log_level: Logging level

    Returns:
        Configured logger instance
    """
    return LoggerSetup.get_logger(name, log_dir=log_dir, log_level=log_level)


def setup_application_logging(log_dir: str = 'logs', log_level: str = 'INFO'):
    """
    Setup logging for the entire application
    Call this once at application startup

    Args:
        log_dir: Directory for log files
        log_level: Logging level
    """
    LoggerSetup.setup_root_logger(log_dir=log_dir, log_level=log_level)


# Module-specific logger configurations
class ModuleLoggers:
    """Pre-configured loggers for specific modules"""

    @staticmethod
    def get_api_logger(log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
        """Get logger for API server"""
        return LoggerSetup.setup_logger(
            'api_server',
            log_dir=log_dir,
            log_level=log_level
        )

    @staticmethod
    def get_check_logger(log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
        """Get logger for check processing"""
        return LoggerSetup.setup_logger(
            'check_processor',
            log_dir=log_dir,
            log_level=log_level
        )

    @staticmethod
    def get_bank_statement_logger(log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
        """Get logger for bank statement processing"""
        return LoggerSetup.setup_logger(
            'bank_statement_processor',
            log_dir=log_dir,
            log_level=log_level
        )

    @staticmethod
    def get_paystub_logger(log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
        """Get logger for paystub processing"""
        return LoggerSetup.setup_logger(
            'paystub_processor',
            log_dir=log_dir,
            log_level=log_level
        )

    @staticmethod
    def get_money_order_logger(log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
        """Get logger for money order processing"""
        return LoggerSetup.setup_logger(
            'money_order_processor',
            log_dir=log_dir,
            log_level=log_level
        )

    @staticmethod
    def get_ml_logger(log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
        """Get logger for ML operations"""
        return LoggerSetup.setup_logger(
            'ml_operations',
            log_dir=log_dir,
            log_level=log_level
        )

    @staticmethod
    def get_database_logger(log_dir: str = 'logs', log_level: str = 'INFO') -> logging.Logger:
        """Get logger for database operations"""
        return LoggerSetup.setup_logger(
            'database_operations',
            log_dir=log_dir,
            log_level=log_level
        )
