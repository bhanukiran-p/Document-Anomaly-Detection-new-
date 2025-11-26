# XFORIA DAD - Backend API Server

## Overview
Flask API server providing document extraction endpoints for the React frontend.

## Files Structure

```
Backend/
├── api_server.py                     (Main Flask API server)
├── mindee_extractor.py               (Mindee-powered document extraction helpers)
├── fraud_detection_service.py        (ML ensemble + PDF validation)
├── ml_risk_scorer.py                 (Risk scoring helper for documents)
├── models/                           (Serialized scaler/model artifacts)
├── templates/                        (Web demo templates)
├── temp_uploads/                     (Temporary file storage)
├── requirements.txt                  (Python dependencies)
└── README.md
```

## API Endpoints

### Health Check
```
GET /api/health
Response: { "status": "healthy", "service": "XFORIA DAD API" }
```

### Check Analysis
```
POST /api/check/analyze
Content-Type: multipart/form-data
Body: file (JPG, PNG, PDF)

Response: {
  "success": true,
  "data": {
    "bank_name": "...",
    "payee_name": "...",
    "amount_numeric": "...",
    "confidence_score": 85.5,
    ...
  }
}
```

### Paystub Analysis
```
POST /api/paystub/analyze
Content-Type: multipart/form-data
Body: file (JPG, PNG, PDF)

Response: {
  "success": true,
  "data": {
    "company_name": "...",
    "employee_name": "...",
    "gross_pay": "...",
    "confidence_score": 72.3,
    ...
  }
}
```

## Running the Server

```bash
cd Backend
python api_server.py
```

Server will start on: **http://localhost:5000**

## Features

✅ Mindee Document AI extraction for checks, paystubs, money orders, statements
✅ PDF to text extraction with PyMuPDF/pdfplumber fallback
✅ Improved confidence scoring
✅ CORS enabled for React frontend
✅ Automatic file cleanup
✅ Error handling
✅ Debug mode for development

## Dependencies

- Flask / Flask-CORS - REST API + CORS support
- mindee - Document AI extraction SDK
- PyMuPDF (fitz) & pdfplumber - PDF parsing
- Pillow - Image processing utilities

Install all: `pip install -r requirements.txt`

## Environment

- Python 3.13
- `MINDEE_API_KEY` plus optional `MINDEE_MODEL_ID_*` environment variables
- Temp folder write access for upload handling

