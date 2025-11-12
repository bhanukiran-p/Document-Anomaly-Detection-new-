# XFORIA DAD - Backend API Server

## Overview
Flask API server providing document extraction endpoints for the React frontend.

## Files Structure

```
Backend/
├── api_server.py                              (Main Flask API server)
├── production_google_vision-extractor.py      (Check extraction logic)
├── pages/
│   └── paystub_extractor.py                   (Paystub extraction logic)
├── check-ocr-project-469619-d18e1cdc414d.json (Google Cloud credentials)
├── requirements.txt                            (Python dependencies)
└── temp_uploads/                               (Temporary file storage)
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

✅ PDF to image conversion (PyMuPDF)
✅ Google Vision API integration
✅ Improved confidence scoring
✅ CORS enabled for React frontend
✅ Automatic file cleanup
✅ Error handling
✅ Debug mode for development

## Dependencies

- Flask - Web framework
- Flask-CORS - CORS support
- google-cloud-vision - OCR API
- PyMuPDF (fitz) - PDF processing
- Pillow - Image processing

Install all: `pip install -r requirements.txt`

## Environment

- Python 3.13
- Google Cloud Vision API credentials required
- Credentials file must be in Backend directory

