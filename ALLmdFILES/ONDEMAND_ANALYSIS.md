# On-Demand Document Analysis

Documentation for analyzing checks, paystubs, bank statements, and money orders using Mindee API.

## Features

- **Check Analysis**: Extract and validate check information
- **Paystub Analysis**: Parse paystub data and verify employment details
- **Bank Statement Analysis**: Extract transaction history and account information
- **Money Order Analysis**: Validate money order authenticity

## API Endpoints

### Check Analysis
- **Endpoint**: `POST /api/check/analyze`
- **Description**: Analyzes check images for fraud detection
- **Request**: Multipart form data with check image
- **Response**: Extracted data including amount, date, payee, account numbers

### Paystub Analysis
- **Endpoint**: `POST /api/paystub/analyze`
- **Description**: Analyzes paystub documents
- **Request**: Multipart form data with paystub image/PDF
- **Response**: Employee details, income information, deductions

### Bank Statement Analysis
- **Endpoint**: `POST /api/bank-statement/analyze`
- **Description**: Extracts transaction data from bank statements
- **Request**: Multipart form data with statement PDF/image
- **Response**: Account details, transaction history, balances

### Money Order Analysis
- **Endpoint**: `POST /api/money-order/analyze`
- **Description**: Validates money order documents
- **Request**: Multipart form data with money order image
- **Response**: Amount, issuer, serial number, validation status

## Backend Configuration

### Mindee API Setup

Required environment variables in `Backend/.env`:

```env
MINDEE_API_KEY=your_mindee_api_key
MINDEE_MODEL_ID_CHECK=your_check_model_id
MINDEE_MODEL_ID_PAYSTUB=your_paystub_model_id
MINDEE_MODEL_ID_BANK_STATEMENT=your_bank_statement_model_id
MINDEE_MODEL_ID_MONEY_ORDER=your_money_order_model_id
```

### File Structure

```
Backend/
├── mindee_extractors/
│   ├── check_extractor.py       # Check document extraction
│   ├── paystub_extractor.py     # Paystub extraction
│   ├── bank_statement_extractor.py  # Bank statement extraction
│   └── money_order_extractor.py # Money order extraction
└── api_server.py                # Main API server
```

## Usage

### 1. Start Backend Server

```bash
cd Backend
python api_server.py
```

Server runs on `http://localhost:5001`

### 2. Upload Document via Frontend

Navigate to the respective analysis page:
- Check Analysis: `/check-analysis`
- Paystub Analysis: `/paystub-analysis`
- Bank Statement Analysis: `/bank-statement-analysis`
- Money Order Analysis: `/money-order-analysis`

### 3. Upload and Analyze

1. Click "Upload Document" or drag & drop
2. Supported formats: JPG, PNG, PDF
3. Click "Analyze Document"
4. View extracted information and fraud indicators

## Response Format

All endpoints return JSON with the following structure:

```json
{
  "success": true,
  "extracted_data": {
    // Document-specific fields
  },
  "fraud_indicators": [
    // List of detected fraud patterns
  ],
  "confidence_score": 0.95,
  "processing_time": "2.3s"
}
```

## Error Handling

Common error codes:
- `400` - Invalid file format or missing file
- `401` - Invalid Mindee API key
- `500` - Processing error

## Fraud Detection

Each document type includes specific fraud checks:

### Check Fraud Indicators
- Altered amounts
- Mismatched signatures
- Invalid MICR codes
- Date inconsistencies

### Paystub Fraud Indicators
- Inconsistent calculations
- Suspicious employer details
- Unusual pay patterns
- Missing required fields

### Bank Statement Fraud Indicators
- Altered balances
- Inconsistent transactions
- Modified dates
- Font/formatting anomalies

### Money Order Fraud Indicators
- Invalid serial numbers
- Altered amounts
- Counterfeit watermarks
- Suspicious issuer details

## Testing

Test the endpoints using sample documents:

```bash
curl -X POST http://localhost:5001/api/check/analyze \
  -F "file=@sample_check.jpg"
```

## Troubleshooting

### Issue: "Mindee API key not found"
**Solution**: Check `Backend/.env` has valid `MINDEE_API_KEY`

### Issue: "Model ID not configured"
**Solution**: Verify all `MINDEE_MODEL_ID_*` variables are set

### Issue: "File upload failed"
**Solution**: Ensure file size < 10MB and format is supported

## Production Considerations

1. **Rate Limiting**: Mindee API has rate limits
2. **File Size**: Large PDFs may take longer to process
3. **Security**: Never commit `.env` files
4. **Caching**: Consider caching results for duplicate documents
