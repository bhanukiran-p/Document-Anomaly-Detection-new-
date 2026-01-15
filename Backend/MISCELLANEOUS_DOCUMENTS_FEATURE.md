# Miscellaneous Documents Feature

## Overview
A feature that allows uploading multiple documents and automatically detecting their type, then analyzing them accordingly. Each document is processed through the appropriate extractor based on automatic type detection.

## Implementation Details

### Backend Endpoint
- **Route**: `/api/miscellaneous/analyze`
- **Method**: POST
- **Accepts**: Multiple files via `files[]` or `file` form fields
- **Process**:
  1. Extracts text using Mindee global model
  2. Detects document type using `detect_document_type()` function
  3. Analyzes only as the detected type (check, paystub, bank_statement, or money_order)
  4. Updates customer fraud status (same as individual endpoints)
  5. Returns results for each file with detected type and analysis

### Frontend Component
- **File**: `Frontend/src/pages/MiscellaneousDocuments.jsx`
- **Route**: `/miscellaneous-documents`
- **Features**:
  - Multiple file upload with drag-and-drop
  - File previews and remove functionality
  - Results display showing detected type and analysis for each file
  - Download JSON for each successful analysis

### API Service Method
- **File**: `Frontend/src/services/api.js`
- **Function**: `analyzeMiscellaneous(files)`
- **Handles**: Both single file and array of files

### Key Features
1. **Automatic Type Detection**: Uses text analysis to detect document type
2. **Single Analysis Per File**: Only analyzes as detected type (not all 4 types)
3. **Customer History Tracking**: Updates customer fraud status for proper escalation handling
4. **Fallback Logic**: If detection fails, tries all types and uses best match with priority scoring

### Detection Logic
- Prioritizes paystub detection (often confused with checks)
- Uses keyword matching and strong indicators
- Validates extractor results before selecting best match

### Customer Fraud Status Updates
- **Check**: Updates via `CheckCustomerStorage.update_customer_fraud_status()`
- **Paystub**: Updates via `PaystubCustomerStorage.update_employee_fraud_status()`
- **Bank Statement**: Updates via `BankStatementCustomerStorage.update_customer_fraud_status()`
- **Money Order**: Automatically updated via `store_money_order_analysis()`

## To Re-enable
1. Restore backend endpoint in `api_server.py` (around line 924)
2. Restore frontend component `MiscellaneousDocuments.jsx`
3. Add route in `App.js`: `/miscellaneous-documents`
4. Add navigation card in `HomePage.jsx`
5. Restore API service method `analyzeMiscellaneous()` in `api.js`

