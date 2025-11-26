# Test Scripts

This folder contains test scripts for validating different components of the application.

## Files

- `test_calibration.py` - Test model calibration
- `test_document_detection.py` - Test document type detection
- `test_end_to_end.py` - End-to-end integration tests
- `test_mindee_api.py` - Test Mindee API connection and credentials
- `test_ml_integration.py` - Test ML model integration

## Usage

Run tests from the Backend directory:

```bash
cd Backend
python tests/test_mindee_api.py
python tests/test_document_detection.py
# ... etc
```
