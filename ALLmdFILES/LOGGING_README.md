# Logging System Documentation

This document explains the centralized logging system implemented in the Document Anomaly Detection backend.

## Overview

The application uses a centralized logging configuration that provides consistent logging across all modules with file rotation and multiple output targets.

## Architecture

### Components

1. **`logging_config.py`** - Centralized logging utility
2. **`config.py`** - Configuration integration for logging
3. **Module-specific loggers** - Each module gets its own log file

### Log Directory Structure

```
Backend/
├── logs/
│   ├── application.log        # Root logger (all logs)
│   ├── application.log.1       # Rotated backup
│   ├── api_server.log          # API server logs
│   ├── check_processor.log     # Check processing logs
│   ├── bank_statement_processor.log
│   ├── paystub_processor.log
│   ├── money_order_processor.log
│   ├── ml_operations.log
│   └── database_operations.log
```

## Usage

### Basic Usage (Recommended)

```python
from config import Config

# At the start of your module
logger = Config.get_logger(__name__)

# Use the logger
logger.info("Processing document")
logger.warning("Missing field detected")
logger.error("Failed to process", exc_info=True)
```

### Alternative: Direct Import

```python
from logging_config import get_logger

logger = get_logger(__name__)
logger.info("Message")
```

### Application Startup

In your main application file (e.g., `api_server.py`):

```python
from config import Config

# Setup logging once at startup
Config.setup_logging()

# Then get logger for this module
logger = Config.get_logger(__name__)
```

## Configuration

### Environment Variables

Configure logging behavior in `.env`:

```env
# Logging Configuration
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs                # Directory for log files
LOG_FILE_MAX_BYTES=10485760 # 10MB per file
LOG_FILE_BACKUP_COUNT=5     # Keep 5 backup files
```

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for unexpected situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical messages for system failures

## Features

### 1. Automatic File Rotation

Log files automatically rotate when they reach `LOG_FILE_MAX_BYTES` (default 10MB).

```
api_server.log      (current file)
api_server.log.1    (oldest backup)
api_server.log.2
...
api_server.log.5    (newest backup)
```

### 2. Multiple Output Targets

- **Console**: Logs to stdout/stderr
- **File**: Logs to individual module files in `logs/` directory
- **Root Logger**: Captures all logs in `application.log`

### 3. Consistent Formatting

All logs use the same format:
```
2025-12-06 17:00:00,123 - module.name - INFO - Your log message here
```

Format: `timestamp - logger_name - log_level - message`

### 4. Per-Module Log Files

Each module automatically gets its own log file based on the logger name:

```python
# In check/check_extractor.py
logger = Config.get_logger(__name__)  # Creates check_extractor.log

# In bank_statement/parser.py
logger = Config.get_logger(__name__)  # Creates parser.log
```

## Module-Specific Loggers

Pre-configured loggers for major components:

```python
from logging_config import ModuleLoggers

api_logger = ModuleLoggers.get_api_logger()
check_logger = ModuleLoggers.get_check_logger()
bank_logger = ModuleLoggers.get_bank_statement_logger()
ml_logger = ModuleLoggers.get_ml_logger()
db_logger = ModuleLoggers.get_database_logger()
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
# DEBUG - Detailed diagnostic information
logger.debug(f"Processing features: {features}")

# INFO - General information about operation flow
logger.info("Started processing document")

# WARNING - Unexpected but handled situations
logger.warning("Missing optional field: signature")

# ERROR - Errors that need attention
logger.error(f"Failed to parse date: {date_str}", exc_info=True)

# CRITICAL - System-level failures
logger.critical("Database connection failed")
```

### 2. Include Context

```python
# Good - includes context
logger.error(f"Failed to process check {check_id}: {error}")

# Bad - no context
logger.error("Processing failed")
```

### 3. Use Exception Info

```python
try:
    process_document()
except Exception as e:
    # Include exc_info=True to log full traceback
    logger.error("Document processing failed", exc_info=True)
```

### 4. Avoid Sensitive Data

```python
# Good - redacted sensitive info
logger.info(f"Processing check for account ****{account[-4:]}")

# Bad - logs full account number
logger.info(f"Processing check for account {account}")
```

### 5. Don't Log in Loops (Performance)

```python
# Bad - logs every iteration
for item in items:
    logger.info(f"Processing {item}")

# Good - log summary
logger.info(f"Processing {len(items)} items")
for item in items:
    process(item)
logger.info("Completed processing all items")
```

## Migration Guide

### For Existing Modules

Replace old logging configuration:

**Old way:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

**New way:**
```python
from config import Config

logger = Config.get_logger(__name__)
```

### For New Modules

Simply import and use:

```python
from config import Config

logger = Config.get_logger(__name__)

def process_data(data):
    logger.info("Starting data processing")
    try:
        # Your code here
        logger.debug(f"Processing {len(data)} items")
        result = do_something(data)
        logger.info("Data processing completed successfully")
        return result
    except Exception as e:
        logger.error("Data processing failed", exc_info=True)
        raise
```

## Troubleshooting

### Logs Not Appearing

1. Check log level in `.env`:
   ```env
   LOG_LEVEL=DEBUG  # Set to DEBUG to see all logs
   ```

2. Verify log directory exists:
   ```python
   Config.ensure_directories()
   ```

3. Check file permissions:
   ```bash
   ls -la logs/
   ```

### Too Many Log Files

Logs are automatically rotated. Adjust retention:

```env
LOG_FILE_BACKUP_COUNT=3  # Keep fewer backups
LOG_FILE_MAX_BYTES=5242880  # 5MB - rotate more frequently
```

### Logs Too Verbose

Set higher log level:

```env
LOG_LEVEL=WARNING  # Only warnings and errors
```

Or adjust per module:

```python
logger = Config.get_logger(__name__)
logger.setLevel(logging.WARNING)
```

## Log Analysis

### View Recent Logs

```bash
# Tail API server logs
tail -f logs/api_server.log

# View last 100 lines
tail -n 100 logs/application.log

# Search for errors
grep "ERROR" logs/*.log

# Search for specific transaction
grep "check_id_123" logs/*.log
```

### Monitor in Real-Time

```bash
# Watch all logs
tail -f logs/application.log

# Watch specific module
tail -f logs/check_processor.log

# Filter by level
tail -f logs/application.log | grep "ERROR"
```

## Production Recommendations

1. **Set appropriate log level:**
   ```env
   LOG_LEVEL=WARNING  # Production
   LOG_LEVEL=INFO     # Staging
   LOG_LEVEL=DEBUG    # Development
   ```

2. **Configure log rotation:**
   ```env
   LOG_FILE_MAX_BYTES=52428800  # 50MB
   LOG_FILE_BACKUP_COUNT=10      # Keep more backups
   ```

3. **Monitor log sizes:**
   ```bash
   du -sh logs/
   ```

4. **Set up log aggregation** (optional):
   - Use tools like ELK Stack, Splunk, or CloudWatch
   - Configure log shipping from `logs/` directory

## Summary

- **Centralized**: All logging configuration in one place
- **Automatic**: Module-specific log files created automatically
- **Rotated**: Files auto-rotate to prevent disk space issues
- **Configurable**: Control via environment variables
- **Consistent**: Same format across all modules

For questions or issues, refer to `logging_config.py` or contact the development team.
