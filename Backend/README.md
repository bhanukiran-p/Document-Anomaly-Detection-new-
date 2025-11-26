# XFORIA DAD - Backend API Server

## Overview

The XFORIA Document Analysis & Detection (DAD) Backend is a Flask-based REST API that provides intelligent fraud detection and document analysis capabilities for financial documents including checks, money orders, paystubs, and bank statements.

## Architecture

### Core Components

```
Backend/
├── api_server.py              # Main Flask application entry point
├── check/                     # Check analysis module
│   └── extractor.py          # Mindee-based check extraction
├── money_order/              # Money order analysis module
│   └── extractor.py          # Mindee-based money order extraction
├── paystub/                  # Paystub analysis module
│   └── extractor.py          # Mindee-based paystub extraction
├── bank_statement/           # Bank statement analysis module
│   └── extractor.py          # Mindee-based bank statement extraction
├── ml_models/                # Machine Learning fraud detection
│   ├── fraud_detector.py     # Ensemble ML fraud detection (Random Forest, XGBoost)
│   ├── feature_extractor.py  # Feature engineering for ML models
│   └── advanced_features.py  # Advanced feature extraction
├── langchain_agent/          # AI-powered fraud analysis
│   ├── fraud_analysis_agent.py  # LangChain-based AI agent
│   ├── tools.py              # Data access tools for AI agent
│   └── result_storage.py     # Analysis result storage
├── database/                 # Database management
│   ├── connection.py         # Supabase connection
│   └── models.py            # Database models
├── auth/                     # Authentication & authorization
│   ├── middleware.py         # Auth middleware
│   └── utils.py             # Auth utilities
├── normalization/            # Data normalization utilities
│   └── normalizer.py        # Field normalization
└── risk/                     # Risk scoring
    └── ml_risk_scorer.py    # ML-based risk scoring
```

## Technology Stack

### Core Framework
- **Flask**: Web framework and REST API
- **Flask-CORS**: Cross-origin resource sharing
- **Python 3.8+**: Programming language

### Document Processing
- **Mindee API**: AI-powered OCR and document extraction
- **pdf2image**: PDF to image conversion
- **Pillow (PIL)**: Image processing

### Machine Learning
- **scikit-learn**: Random Forest classifier
- **XGBoost**: Gradient boosting classifier
- **pandas**: Data manipulation
- **numpy**: Numerical computing

### AI Analysis
- **LangChain**: AI agent framework
- **OpenAI GPT-4**: Large language model for fraud analysis
- **CSV-based data tools**: Historical fraud data analysis

### Database
- **Supabase**: PostgreSQL database (optional)
- **JSON-based storage**: User authentication fallback

## Installation

### Prerequisites

1. Python 3.8 or higher
2. pip package manager
3. Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   cd Backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Poppler (for PDF processing)**

   **Windows:**
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases/
   - Add to PATH environment variable

   **macOS:**
   ```bash
   brew install poppler
   ```

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install poppler-utils
   ```

5. **Configure environment variables**

   Create a `.env` file in the Backend directory:
   ```env
   # Mindee API Configuration
   MINDEE_API_KEY=your_mindee_api_key_here
   MINDEE_MODEL_ID_CHECK=046edc76-e8a4-4e11-a9a3-bb8632250446
   MINDEE_MODEL_ID_MONEY_ORDER=your_money_order_model_id
   MINDEE_MODEL_ID_PAYSTUB=your_paystub_model_id

   # OpenAI Configuration (for AI fraud analysis)
   OPENAI_API_KEY=your_openai_api_key_here
   AI_MODEL=gpt-4

   # ML Model Configuration
   ML_MODEL_DIR=ml_models
   ML_SCORES_CSV=ml_models/mock_data/ml_scores.csv
   CUSTOMER_HISTORY_CSV=ml_models/mock_data/customer_history.csv
   FRAUD_CASES_CSV=ml_models/mock_data/fraud_cases.csv

   # Database Configuration (Optional - Supabase)
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key

   # Server Configuration
   FLASK_ENV=development
   FLASK_DEBUG=False
   PORT=5001
   ```

## Running the Server

### Development Mode

```bash
python api_server.py
```

The server will start on `http://localhost:5001`

### Production Mode

```bash
# Using Gunicorn (Linux/macOS)
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app

# Using Waitress (Windows)
waitress-serve --host=0.0.0.0 --port=5001 api_server:app
```

## API Endpoints

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "XFORIA DAD API",
  "version": "1.0.0",
  "database": {
    "supabase": "connected" | "disconnected"
  }
}
```

### Check Analysis

```http
POST /api/check/analyze
Content-Type: multipart/form-data
```

**Parameters:**
- `file`: Check image (JPG, PNG, PDF)

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "success",
    "extracted_data": {
      "bank_name": "Chase Bank",
      "check_number": "1234",
      "amount_numeric": 1500.00,
      "amount": "$1,500.00",
      "date": "2024-01-15",
      "payee_name": "John Doe",
      "payer_name": "Jane Smith",
      "routing_number": "123456789",
      "account_number": "987654321",
      "signature_detected": true
    },
    "ml_analysis": {
      "fraud_risk_score": 0.23,
      "risk_level": "LOW",
      "model_confidence": 0.87,
      "feature_importance": [...],
      "model_scores": {
        "random_forest": 0.21,
        "xgboost": 0.25,
        "ensemble": 0.23
      }
    },
    "ai_analysis": {
      "recommendation": "APPROVE",
      "confidence": 0.92,
      "summary": "Check appears legitimate...",
      "reasoning": "All required fields present...",
      "risk_factors": []
    },
    "anomalies": [],
    "confidence_score": 0.85,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### Money Order Analysis

```http
POST /api/money-order/analyze
Content-Type: multipart/form-data
```

**Parameters:**
- `file`: Money order image (JPG, PNG, PDF)

**Response:** Similar structure to check analysis

### Paystub Analysis

```http
POST /api/paystub/analyze
Content-Type: multipart/form-data
```

**Parameters:**
- `file`: Paystub document (JPG, PNG, PDF)

**Response:**
```json
{
  "success": true,
  "data": {
    "company_name": "Tech Corp",
    "employee_name": "John Doe",
    "employee_id": "EMP001",
    "pay_period_start": "2024-01-01",
    "pay_period_end": "2024-01-15",
    "pay_date": "2024-01-20",
    "gross_pay": "$5,000.00",
    "net_pay": "$3,750.00",
    "ytd_gross": "$15,000.00",
    "ytd_net": "$11,250.00",
    "federal_tax": "$750.00",
    "state_tax": "$250.00",
    "social_security": "$150.00",
    "medicare": "$100.00",
    "ml_analysis": {...},
    "ai_analysis": {...},
    "anomalies": [],
    "confidence_score": 0.88
  }
}
```

### Bank Statement Analysis

```http
POST /api/bank-statement/analyze
Content-Type: multipart/form-data
```

**Parameters:**
- `file`: Bank statement (JPG, PNG, PDF)

**Response:**
```json
{
  "success": true,
  "data": {
    "bank_name": "Wells Fargo",
    "account_holder": "John Doe",
    "account_number": "****1234",
    "statement_period": "Jan 1 - Jan 31, 2024",
    "balances": {
      "opening_balance": "$10,000.00",
      "ending_balance": "$12,500.00",
      "available_balance": "$12,500.00"
    },
    "summary": {
      "transaction_count": 45,
      "total_credits": "$8,500.00",
      "total_debits": "$6,000.00",
      "net_activity": "$2,500.00"
    },
    "transactions": [...],
    "ml_analysis": {...},
    "ai_analysis": {...}
  }
}
```

## Fraud Detection Pipeline

### 1. Document Extraction (Mindee API)
- OCR and field extraction
- Confidence scoring for each field
- Raw text capture for additional analysis

### 2. ML Fraud Detection
- **Feature Engineering**: 50+ features extracted per document
- **Random Forest Classifier**: Tree-based ensemble model
- **XGBoost Classifier**: Gradient boosting model
- **Ensemble Voting**: Combines both models for final score
- **Risk Levels**: LOW, MEDIUM, HIGH, CRITICAL

### 3. AI-Powered Analysis (GPT-4)
- Contextual fraud analysis
- Historical pattern matching
- Natural language reasoning
- Recommendations: APPROVE, REVIEW, REJECT

### 4. Anomaly Detection
- Missing required fields
- Inconsistent data patterns
- Out-of-range values
- Signature verification failures

## ML Model Details

### Feature Categories

1. **Document Completeness** (15 features)
   - Missing fields count
   - Field confidence scores
   - Data quality metrics

2. **Amount Analysis** (12 features)
   - Amount range validation
   - Unusual amount patterns
   - Amount-words mismatch

3. **Date Validation** (8 features)
   - Date format consistency
   - Future date detection
   - Date logic validation

4. **Text Analysis** (10 features)
   - OCR quality score
   - Text pattern analysis
   - Character distribution

5. **Metadata Features** (5 features)
   - Document type
   - Processing confidence
   - Data source reliability

### Model Performance Metrics

- **Accuracy**: ~85-92% on test data
- **Precision**: ~88% (fraud detection)
- **Recall**: ~82% (fraud detection)
- **F1 Score**: ~85%

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error type",
  "message": "Detailed error message",
  "details": {
    "field": "Additional context"
  }
}
```

### Common Error Codes

- `400 Bad Request`: Missing or invalid file
- `413 Payload Too Large`: File size exceeds limit (16MB)
- `415 Unsupported Media Type`: Invalid file format
- `500 Internal Server Error`: Processing failure
- `503 Service Unavailable`: External API failure

## File Upload Limits

- **Maximum file size**: 16MB
- **Supported formats**: JPG, JPEG, PNG, PDF
- **PDF conversion**: Automatic conversion to PNG for processing

## Security

### Authentication (Future Implementation)
- JWT-based authentication
- API key authentication
- Role-based access control

### Data Protection
- Temporary file cleanup after processing
- No permanent storage of uploaded documents
- Encrypted API communication (HTTPS in production)

## Troubleshooting

### Common Issues

1. **Mindee API Key Invalid**
   ```
   Solution: Verify MINDEE_API_KEY in .env file
   ```

2. **PDF Conversion Fails**
   ```
   Solution: Install Poppler and add to PATH
   Windows: Download from releases and add bin/ to PATH
   ```

3. **ML Models Not Loading**
   ```
   Solution: Ensure scikit-learn and xgboost are installed
   pip install scikit-learn xgboost
   ```

4. **Port Already in Use**
   ```
   Solution: Change PORT in .env or kill process on port 5001
   Windows: netstat -ano | findstr :5001
   Linux/Mac: lsof -ti:5001 | xargs kill
   ```

## Dependencies

### Core Requirements
```
Flask>=2.3.0
Flask-CORS>=4.0.0
python-dotenv>=1.0.0
mindee>=3.0.0
pdf2image>=1.16.0
Pillow>=10.0.0
```

### ML Requirements
```
scikit-learn>=1.3.0
xgboost>=1.7.0
pandas>=2.0.0
numpy>=1.24.0
```

### AI Requirements
```
langchain>=0.1.0
openai>=1.0.0
```

## License

Copyright © 2024 XFORIA. All rights reserved.

## Support

For technical support or questions:
- Email: support@xforia.com
- Documentation: https://docs.xforia.com

## Version History

### v1.0.0 (Current)
- Initial release
- Check, Money Order, Paystub, Bank Statement analysis
- ML fraud detection with ensemble models
- AI-powered fraud analysis with GPT-4
- CSV and JSON export functionality
