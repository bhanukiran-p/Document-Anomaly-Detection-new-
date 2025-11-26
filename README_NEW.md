# XFORIA DAD Backend

Flask-based API that ingests financial documents (checks, paystubs, money orders, and bank statements), extracts structured data via Google Vision + Tesseract fallbacks, and runs ML fraud-risk scoring (XGBoost/RandomForest ensemble with optional Gradient Boosting / Logistic Regression when present).  
The backend also logs every successful extraction into CSV datasets to bootstrap OCR/model retraining.

---

## Repository Layout

| Path | Purpose |
| --- | --- |
| `api_server.py` | Main Flask app & REST endpoints |
| `check/check_extractor.py` | Tuned check extractor (Vision + Tesseract) |
| `paystub/paystub_extractor.py` | Paystub OCR/extraction helpers |
| `money_order/money_order_extractor.py` | Money order parsing heuristics |
| `bank/bank_statement_extractor.py` | Statement OCR with Vision->Tesseract fallback & reconciliation |
| `auth/` | Local JWT auth + optional Supabase helpers |
| `ml/fraud_detection_service.py` | ML ensemble inference + rule validation |
| `ml/train_fraud_models.py` | Model training pipeline (XGBoost, RF, GB, LR) |
| `data_logger.py` | Appends extraction samples into `logs/extractions/*.csv` |
| `logs/extractions/` | Rolling CSV logs per document type |
| `trained_models/` | Serialized `.pkl` models + label encoders |
| `temp_uploads/` | Runtime scratch space for uploads / pdf->png conversions |

---

## Prerequisites

1. **Python** ≥ 3.11 (current dev box: 3.13).  
2. **Pip** + virtualenv recommended.  
3. **Tesseract OCR** installed locally and discoverable via PATH (Windows installer).  
4. **Google Vision credentials** JSON file (place at `Backend/google-credentials.json` or set `GOOGLE_CREDENTIALS_PATH`).  
5. Optional: Node/NPM for the React frontend (`Frontend/`).

---

## Installation & Environment

```powershell
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Windows – ensure Vision credentials available:
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\google-credentials.json"

# Optional: disable Flask reloader (recommended in this repo)
$env:FLASK_DEBUG="0"
python api_server.py
```

Server listens on `http://localhost:5001`. The React frontend expects that base URL (or set `REACT_APP_API_URL`).

---

## Document Processing Pipeline

### Checks
1. Uploaded via `/api/check/analyze`.  
2. `ProductionCheckExtractor` uses Vision API primary, Tesseract fallback for key fields.  
3. Fields normalized (routing/account numbers, amounts, payee, etc.).  
4. Fraud risk: `ml.fraud_detection_service.validate_check` → transaction-style vectors → ML ensemble.  
5. Response includes `data` (fields) + `risk_assessment`.  
6. Snapshot logged through `append_extraction_record('check', ...)`.

### Paystubs
1. `paystub/paystub_extractor.PaystubExtractor` handles both PDF/image input.  
2. Complex regex/context search to fill pay date, employee info, earnings/deductions.  
3. Fraud evaluation mixes heuristics (missing fields, amounts) + ML ensemble.  
4. Logged to `logs/extractions/paystub_extractions.csv`.

### Money Orders
1. Generic Vision text detection, then `money_order/money_order_extractor.MoneyOrderExtractor` pattern-matches payee/purchaser/serial/amount.  
2. Fraud scoring uses money-order→transaction feature conversion.  
3. Logged to `money_order_extractions.csv`.

### Bank Statements
1. PDF→PNG via PyMuPDF if needed.  
2. `bank/bank_statement_extractor.BankStatementExtractor` runs Vision, falls back to Tesseract when required fields missing, merges results, infers balances, composes transaction list.  
3. Fraud service either validates original PDF (`validate_statement_pdf`) or uses extracted summary.  
4. Logged to `bank_statement_extractions.csv`.

---

## Fraud Detection Service

- Loads serialized models from `trained_models/` (`xgboost_model.pkl`, `random_forest_model.pkl`, and optional `gradient_boosting_model.pkl`, `logistic_regression_model.pkl`, plus `label_encoders.pkl`).  
- `FraudDetectionService._has_trained_models()` ensures at least one estimator is available.  
- `predict_transaction_fraud()` supports explicit `model_type` or the default “ensemble” (averages probabilities from all loaded models).  
- Additional helpers:
  - `validate_check`, `validate_paystub`, `validate_money_order`, `evaluate_statement_details`
  - `validate_statement_pdf()` for full-rule & ML-based PDF scanning.

### Training Models

```powershell
cd Backend
python ml/train_fraud_models.py
```

The trainer:
1. Loads dataset `Database/staement_fraud_5000.csv` (custom path via CLI edit).  
2. Encodes categorical features, handles NaNs, splits train/test.  
3. Trains XGBoost, RandomForest, Gradient Boosting, Logistic Regression.  
4. Saves models + encoders into `trained_models/`.  
5. Prints per-model metrics; use `compare_models(metrics)` output to gauge improvements.

---

## Dataset Logging

`data_logger.append_extraction_record()` writes every successful API response into a CSV per document type.  
Each row contains:
- Timestamp, document type, original filename.  
- Truncated raw OCR text (up to 2k chars).  
- `flat_fields` JSON (key primitives for quick filtering).  
- `full_payload` (entire extractor output).  
- Risk score/verdict snapshot when available.

These CSVs can be stitched into larger training corpora for supervised learning, OCR regression tests, or analytics dashboards.

---

## REST API Summary

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/health` | GET | Health probe + Supabase connectivity info |
| `/api/check/analyze` | POST (multipart) | Analyze check image/pdf, return fields + ML risk |
| `/api/paystub/analyze` | POST | Paystub analysis |
| `/api/money-order/analyze` | POST | Money order analysis |
| `/api/bank-statement/analyze` | POST | Bank statement extraction & risk |
| `/api/fraud/models-status` | GET | Report which ML models are loaded |
| `/api/fraud/transaction-predict` | POST (JSON) | Predict fraud for provided transaction vector |
| `/api/fraud/validate-pdf` | POST (multipart) | Raw PDF validation |
| `/api/fraud/assess` | POST (JSON) | Combined transaction + PDF assessment |
| `/api/fraud/batch-predict` | POST (CSV upload) | Bulk fraud predictions |

Errors follow `{ success: False, error: "...", message: "..."} `. Network failures return helpful instructions on the frontend (see `Frontend/src/services/api.js`).

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Frontend shows “Network error: Unable to connect to server” | Ensure backend is running on port 5001 without auto-reloader (`FLASK_DEBUG=0`). |
| Flask restarts repeatedly mentioning `pickle.py` | Caused by debug reloader noticing sklearn warnings; disable reloader (as above). |
| Vision credential errors | Set `GOOGLE_APPLICATION_CREDENTIALS` env var or place JSON at `Backend/google-credentials.json`. |
| Missing Gradient Boosting / Logistic Regression warnings | Re-run `ml/train_fraud_models.py` to regenerate latest pickles. |
| Tesseract not found | Install Windows Tesseract (e.g., via Chocolatey) and ensure `tesseract.exe` is in PATH. |

---

## Frontend Pairing

React app (port 3002) consumes these APIs via `Frontend/src/services/api.js`.  
Environment override: `REACT_APP_API_URL=http://<host>:5001/api`.  
Start frontend with `npm start` after `npm install`.

---

## Cleaned Files

Legacy `api_server_vision_backup.py` (unused Mindee-era backup) has been removed to avoid confusion.

---

## Next Steps

- Harvest logged CSV data to expand labeled datasets.  
- Experiment with new estimators by extending `ml.fraud_detection_service._load_models`.  
- Deploy behind a production WSGI server (Gunicorn/Uvicorn) once ready.

For questions or more instrumentation, open an issue or extend this README.
# XFORIA DAD - Backend API Server

## Overview
Flask API server providing document extraction endpoints for the React frontend.

## Files Structure

```
Backend/
├── api_server.py                              (Main Flask API server)
├── auth/                                      (Local & Supabase auth helpers)
├── Database/
│   ├── staement_fraud_5000.csv                (Fraud-model training dataset)
│   └── users.json                             (Local auth store)
├── check/
│   └── check_extractor.py                     (Check extraction logic)
├── paystub/
│   └── paystub_extractor.py                   (Paystub extraction logic)
├── money_order/
│   └── money_order_extractor.py               (Money order parsing)
├── bank/
│   ├── bank_statement_extractor.py            (Bank statement OCR)
│   └── pdf_statement_validator.py             (PDF tamper checks)
├── ml/
│   ├── fraud_detection_service.py             (ML inference service)
│   ├── train_fraud_models.py                  (Training pipeline)
│   └── tests/                                 (ML regression tests)
├── logs/
│   └── extractions/                           (CSV snapshots per document type)
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

