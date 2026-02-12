# XFORIA Document Anomaly Detection (DAD)

**AI-Powered Fraud Detection System for Financial Documents**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18.2.0-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [API Documentation](#api-documentation)
7. [ML Models Architecture](#ml-models-architecture)
8. [AI Fraud Analysis Agents](#ai-fraud-analysis-agents)
9. [Database Schema](#database-schema)
10. [Frontend Architecture](#frontend-architecture)
11. [Processing Pipeline](#processing-pipeline)
12. [Deployment](#deployment)
13. [Development Guide](#development-guide)
14. [Testing](#testing)
15. [Troubleshooting](#troubleshooting)
16. [Performance Metrics](#performance-metrics)
17. [Security](#security)

---

## 🎯 Overview

XFORIA DAD is a comprehensive fraud detection system that analyzes financial documents (checks, paystubs, money orders, and bank statements) using a combination of:

- **Machine Learning**: Ensemble models (Random Forest + XGBoost) for fraud risk scoring
- **AI Analysis**: GPT-4 powered contextual fraud analysis
- **OCR Extraction**: Mindee API for document field extraction
- **Real-Time Processing**: Transaction monitoring and fraud detection

### Key Features

- ✅ **Multi-Document Support**: Checks, Paystubs, Money Orders, Bank Statements
- ✅ **Hybrid ML/AI Detection**: Ensemble ML models + GPT-4 analysis
- ✅ **Customer History Tracking**: Repeat offender detection
- ✅ **Real-Time Analytics**: Transaction monitoring dashboards
- ✅ **Comprehensive Insights**: Fraud trends, risk distributions, geographic analysis
- ✅ **RESTful API**: Complete API for integration
- ✅ **Modern UI**: React-based dashboard with interactive visualizations

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  Port: 3002 | React 18.2.0 | React Router | Recharts       │
│  • Analysis Pages    • Insights Dashboards                   │
│  • Real-Time Monitoring  • Authentication                    │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND API SERVER (Flask)                  │
│  Port: 5001 | Flask 3.0.0 | CORS Enabled | JWT Auth        │
├─────────────────────────────────────────────────────────────┤
│  Document Processors:                                       │
│  • CheckExtractor      • PaystubExtractor                    │
│  • MoneyOrderExtractor • BankStatementExtractor              │
│  • RealTimeProcessor                                         │
└─────────────────────────────────────────────────────────────┘
                            ↕ API Calls
┌─────────────────────────────────────────────────────────────┐
│              PROCESSING PIPELINE (10 Stages)                 │
│  1. OCR (Mindee)     2. Normalization   3. Validation       │
│  4. ML Detection     5. Customer History  6. AI Analysis    │
│  7. Anomaly Gen      8. Confidence     9. Decision           │
│  10. Response Build                                          │
└─────────────────────────────────────────────────────────────┘
                            ↕ External APIs
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES                              │
│  • Mindee OCR API    • OpenAI GPT-4    • Google Vision      │
│  • Supabase (PostgreSQL)                                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

**Backend Structure:**
```
Backend/
├── api_server.py              # Main Flask API server
├── config.py                  # Centralized configuration
├── check/                     # Check analysis module
│   ├── check_extractor.py    # Main orchestrator
│   ├── ml/                   # ML fraud detection
│   ├── ai/                   # AI analysis agent
│   ├── normalization/        # Bank-specific normalizers
│   └── database/             # Customer storage
├── paystub/                  # Paystub analysis module
├── money_order/              # Money order analysis module
├── bank_statement/           # Bank statement analysis module
├── real_time/                # Real-time transaction processing
├── training/                 # Model training scripts
├── database/                 # Database utilities
└── utils/                    # Shared utilities
```

**Frontend Structure:**
```
Frontend/
├── src/
│   ├── App.js                # Main app component
│   ├── pages/                # Analysis pages
│   ├── components/           # Reusable components
│   ├── context/              # React Context (Auth)
│   └── utils/                # Frontend utilities
├── public/                   # Static assets
└── package.json              # Dependencies
```

---

## 🛠️ Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| **Web Framework** | Flask | 3.0.0 |
| **Language** | Python | 3.12+ |
| **CORS** | Flask-CORS | 4.0.0 |
| **ML Framework** | scikit-learn | 1.4.2 |
| **Gradient Boosting** | XGBoost | 2.0.3 |
| **LightGBM** | LightGBM | 4.1.0 |
| **AI/LLM** | OpenAI | 1.6.1 |
| **LangChain** | LangChain | 0.1.0 |
| **OCR** | Mindee API | 4.31.0+ |
| **Database** | Supabase (PostgreSQL) | 2.10.0 |
| **Auth** | PyJWT | 2.10.1 |
| **PDF Processing** | PyMuPDF | 1.23.26 |
| **Image Processing** | Pillow | 10.3.0 |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | React | 18.2.0 |
| **Router** | React Router | 6.20.0 |
| **Charts** | Recharts | 3.5.1 |
| **Charts** | ECharts | 6.0.0 |
| **HTTP Client** | Axios | 1.6.2 |
| **File Upload** | React Dropzone | 14.2.3 |
| **Icons** | React Icons | 5.5.0 |

### External Services

- **Mindee API**: Document OCR and field extraction
- **OpenAI GPT-4**: Fraud analysis and recommendations
- **Google Cloud Vision**: Fallback OCR
- **Supabase**: PostgreSQL database and authentication

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.12 or higher
- Node.js 18+ and npm
- PostgreSQL (via Supabase)
- Mindee API account
- OpenAI API account
- Google Cloud Vision API credentials (optional)

### Backend Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Document-Anomaly-Detection-new-
```

2. **Create virtual environment:**
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
Create a `.env` file in the `Backend/` directory:
```bash
# Required API Keys
MINDEE_API_KEY=your_mindee_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Google Cloud Vision (Optional)
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json

# Mindee Model IDs (Optional - defaults provided)
MINDEE_MODEL_ID_CHECK=your_check_model_id
MINDEE_MODEL_ID_PAYSTUB=your_paystub_model_id
MINDEE_MODEL_ID_BANK_STATEMENT=your_bank_statement_model_id
MINDEE_MODEL_ID_MONEY_ORDER=your_money_order_model_id

# AI Model Configuration
AI_MODEL=gpt-4-mini

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3002,http://localhost:3000
```

5. **Initialize database:**
```bash
# Run database migrations
python database/run_migration.py

# Create views
psql -h your-supabase-host -U postgres -d postgres -f database/create_checks_analysis_view.sql
psql -h your-supabase-host -U postgres -d postgres -f database/create_money_orders_analysis_view.sql
```

6. **Train ML models (optional):**
```bash
# Train all models
python training/retrain_check_models_30features.py
python training/train_paystub_models.py
python training/train_money_order_models.py
python training/train_risk_model.py
```

7. **Start the API server:**
```bash
python api_server.py
# Server runs on http://localhost:5001
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd Frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure API endpoint:**
Update `package.json` proxy or create `.env`:
```bash
REACT_APP_API_URL=http://localhost:5001
```

4. **Start development server:**
```bash
npm start
# App runs on http://localhost:3002
```

---

## ⚙️ Configuration

### Environment Variables

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MINDEE_API_KEY` | Mindee API key for OCR | `abc123...` |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | `sk-...` |
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJ...` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MINDEE_MODEL_ID_CHECK` | Mindee check model ID | Auto-detected |
| `MINDEE_MODEL_ID_PAYSTUB` | Mindee paystub model ID | Auto-detected |
| `AI_MODEL` | OpenAI model name | `gpt-4-mini` |
| `FLASK_ENV` | Flask environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | `52428800` (50MB) |

### Configuration File (`Backend/config.py`)

The `Config` class centralizes all configuration:

```python
from config import Config

# Access configuration
api_key = Config.OPENAI_API_KEY
upload_folder = Config.UPLOAD_FOLDER
log_level = Config.LOG_LEVEL
```

**Key Configuration Sections:**
- **Paths**: Upload folders, log directories, model paths
- **Flask Settings**: Secret key, CORS origins, max content length
- **API Keys**: Mindee, OpenAI, Google Cloud
- **Database**: Supabase connection settings
- **ML Settings**: Fraud thresholds, model paths
- **Feature Flags**: Enable/disable features

---

## 📡 API Documentation

### Base URL

```
http://localhost:5001/api
```

### Authentication

Most endpoints require JWT authentication. Include token in header:
```
Authorization: Bearer <JWT_TOKEN>
```

### Document Analysis Endpoints

#### POST `/api/check/analyze`

Analyze a check image for fraud.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Check image file (PNG, JPG, PDF)
  - `user_id`: (optional) User ID

**Response:**
```json
{
  "success": true,
  "fraud_risk_score": 0.75,
  "risk_level": "HIGH",
  "model_confidence": 0.89,
  "fraud_type": "SIGNATURE_FORGERY",
  "fraud_type_label": "Signature Forgery",
  "fraud_explanations": [
    {
      "type": "SIGNATURE_FORGERY",
      "reasons": ["Missing signature detected"]
    }
  ],
  "ai_recommendation": "REJECT",
  "ai_confidence": 0.92,
  "summary": "Check analysis indicates missing signature...",
  "key_indicators": ["Missing signature", "High fraud risk"],
  "document_id": "uuid-here",
  "data": {
    "extracted_data": {...},
    "normalized_data": {...},
    "ml_analysis": {...},
    "ai_analysis": {...}
  }
}
```

**Processing Time:** 5-15 seconds

#### POST `/api/paystub/analyze`

Analyze a paystub document.

**Request:** Same as check analysis

**Response:** Similar structure with paystub-specific fields

#### POST `/api/money-order/analyze`

Analyze a money order document.

**Request:** Same as check analysis

**Response:** Similar structure with money order-specific fields

#### POST `/api/bank-statement/analyze`

Analyze a bank statement document.

**Request:** Same as check analysis

**Response:** Similar structure with bank statement-specific fields

### Data Retrieval Endpoints

#### GET `/api/checks/list`

Get list of analyzed checks.

**Query Parameters:**
- `date_filter`: `last_30`, `last_60`, `last_90`, `older`
- `limit`: Number of records (default: 1000)

**Response:**
```json
{
  "success": true,
  "data": [...],
  "count": 150,
  "total_records": 1500
}
```

#### GET `/api/checks/<check_id>`

Get detailed check information.

#### GET `/api/checks/search?q=<query>&limit=20`

Search checks by payer name.

#### GET `/api/documents/list`

Get all documents with optional filters.

**Query Parameters:**
- `date_filter`: Date range filter
- `document_type`: Filter by type
- `risk_level`: Filter by risk level
- `status`: Filter by status

### Real-Time Analysis Endpoints

#### POST `/api/real-time/analyze`

Analyze CSV file with transactions.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: CSV file with transactions

**Response:**
```json
{
  "success": true,
  "transactions": [...],
  "insights": {
    "total_transactions": 1000,
    "high_risk_count": 45,
    "avg_risk_score": 0.23
  },
  "ai_analysis": {
    "summary": "Analysis of 1000 transactions...",
    "recommendations": [...]
  }
}
```

### Authentication Endpoints

#### POST `/api/auth/login`

Login user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "JWT_TOKEN_HERE",
  "user": {
    "id": "user-id",
    "email": "user@example.com"
  }
}
```

#### POST `/api/auth/register`

Register new user.

**Request:** Same as login

**Response:** Same as login

---

## 🤖 ML Models Architecture

### Model Summary

| Document Type | Architecture | Ensemble | Features | Model Files |
|--------------|-------------|----------|-----------|-------------|
| **Checks** | RF + XGBoost | 40% RF + 60% XGB | 30 | `check_random_forest.pkl`<br>`check_xgboost.pkl` |
| **Money Orders** | RF + XGBoost | 40% RF + 60% XGB | 30 | `money_order_random_forest.pkl`<br>`money_order_xgboost.pkl` |
| **Paystubs** | RF + XGBoost | 40% RF + 60% XGB | 18 | `paystub_random_forest.pkl`<br>`paystub_xgboost.pkl` |
| **Bank Statements** | RF + XGBoost | 40% RF + 60% XGB | 35 | `bank_statement_random_forest.pkl`<br>`bank_statement_xgboost.pkl` |
| **Real-Time** | XGBoost | Single | 50+ | `transaction_fraud_model.pkl` |

### Feature Engineering

#### Common Features (All Documents)

**Amount Features:**
- `amount_normalized`: Normalized to 0-1 scale
- `amount_log`: Logarithmic transformation
- `amount_rounded`: Boolean if round number
- `amount_zscore`: Statistical deviation

**Date Features:**
- `day_of_week`: 0-6 (Monday-Sunday)
- `month`: 1-12
- `is_weekend`: Boolean
- `days_since_epoch`: Days since Unix epoch
- `date_age_days`: Age of document in days

**Text Quality Features:**
- `payer_name_length`: Character count
- `payee_name_length`: Character count
- `text_quality_score`: OCR confidence (0-1)
- `field_completeness`: Percentage of fields filled (0-1)

**Missing Field Indicators:**
- `missing_payer`: Boolean
- `missing_payee`: Boolean
- `missing_amount`: Boolean
- `missing_date`: Boolean
- `signature_present`: Boolean

**Customer Behavior Features:**
- `total_submissions`: Count of previous submissions
- `high_risk_count`: Count of high-risk submissions
- `avg_previous_risk`: Average risk score (0-1)
- `is_repeat_customer`: Boolean
- `escalate_count`: Count of escalations

#### Document-Specific Features

**Checks (30 features):**
- `bank_validity`: Bank name validation (0-1)
- `routing_number_valid`: Routing number format check
- `account_number_length`: Length of account number
- `check_number_valid`: Check number format check
- `amount_matching`: Numeric vs written amount match (0-1)
- `signature_detected`: Signature presence
- `stale_check`: Boolean (date_age_days > 180)

**Paystubs (18 features):**
- `gross_pay`: Normalized gross pay
- `net_pay`: Normalized net pay
- `gross_net_ratio`: Ratio of gross to net
- `federal_tax`: Normalized federal tax
- `state_tax`: Normalized state tax
- `social_security`: Normalized SS tax
- `medicare`: Normalized Medicare tax
- `tax_deduction_ratio`: Total deductions ratio
- `pay_period_valid`: Pay period validation

**Money Orders (30 features):**
- `issuer_valid`: Issuer validation (0-1)
- `serial_format_valid`: Serial number format check
- `exact_amount_match`: Numeric vs written match (0-1)
- `signature_present`: Signature presence
- `amount_within_limit`: Amount within issuer limit

**Bank Statements (35 features):**
- `balance_consistency`: Balance calculation consistency (0-1)
- `transaction_count`: Number of transactions
- `avg_transaction_amount`: Average transaction amount
- `high_value_transaction_count`: Count of high-value transactions
- `negative_balance_detected`: Boolean
- `transaction_pattern_anomaly`: Boolean

**Real-Time Transactions (50+ features):**
- `amount_zscore`: Statistical deviation
- `customer_txn_count`: Transaction velocity
- `amount_deviation`: Amount deviation from mean
- `country_mismatch`: Geographic anomaly
- `is_night`: Night-time transaction
- `is_foreign_currency`: Foreign currency flag
- `high_risk_category`: High-risk merchant category
- `is_transfer`: Transfer transaction flag
- `amount_to_balance_ratio`: Amount relative to balance
- `login_transaction_mismatch`: Account takeover indicator

### Model Training

**Training Scripts:**
- Checks: `Backend/training/retrain_check_models_30features.py`
- Paystubs: `Backend/training/train_paystub_models.py`
- Money Orders: `Backend/training/train_money_order_models.py`
- Bank Statements: `Backend/training/train_risk_model.py`

**Training Process:**
1. Generate synthetic training data (2000 samples)
2. Split train/test (80/20)
3. Handle imbalanced data with SMOTE
4. Train Random Forest and XGBoost separately
5. Hyperparameter tuning with GridSearchCV
6. Evaluate on test set
7. Save models to `.pkl` files

**Hyperparameters:**

Random Forest:
- `n_estimators`: 100
- `max_depth`: 10
- `min_samples_split`: 5

XGBoost:
- `max_depth`: 6
- `learning_rate`: 0.1
- `n_estimators`: 100
- `subsample`: 0.8
- `colsample_bytree`: 0.8

**Ensemble Scoring:**
```python
ensemble_score = (0.4 * rf_score) + (0.6 * xgb_score)
```

---

## 🧠 AI Fraud Analysis Agents

### Architecture

Each document type has a dedicated AI agent:

- `CheckFraudAnalysisAgent` (`Backend/check/ai/check_fraud_analysis_agent.py`)
- `PaystubFraudAnalysisAgent` (`Backend/paystub/ai/paystub_fraud_analysis_agent.py`)
- `MoneyOrderFraudAnalysisAgent` (`Backend/money_order/ai/fraud_analysis_agent.py`)
- `BankStatementFraudAnalysisAgent` (`Backend/bank_statement/ai/bank_statement_fraud_analysis_agent.py`)

### AI Agent Flow

```
1. Initialize OpenAI Client (GPT-4)
2. Load System Prompts (fraud detection rules)
3. Initialize Data Access Tools (database queries)
4. Build Context:
   • Extracted document data
   • ML fraud risk score & confidence
   • Customer history (new vs repeat)
   • Validation issues
5. Generate GPT-4 Prompt
6. Call OpenAI API
7. Parse AI Response:
   • recommendation (APPROVE/REJECT/ESCALATE)
   • confidence_score (0.0-1.0)
   • summary (natural language)
   • key_indicators (list)
   • fraud_types (if REJECT/ESCALATE)
   • fraud_explanations (structured)
8. Return Analysis Dict
```

### Fraud Type Taxonomy

#### Checks (5 fraud types)

1. **SIGNATURE_FORGERY**: Missing or forged signature
   - Trigger: `signature_detected == 0`
   - Logic: 1st time = ESCALATE, 2nd time = REJECT

2. **AMOUNT_ALTERATION**: Amount mismatch or suspicious patterns
   - Trigger: `amount_matching < 0.5`, `suspicious_amount == 1`

3. **COUNTERFEIT_CHECK**: Fake or tampered document
   - Trigger: `text_quality < 0.5`, document tampering evidence

4. **REPEAT_OFFENDER**: Payer with fraud history
   - Trigger: `fraud_count > 0`

5. **STALE_CHECK**: Check older than 180 days or future-dated
   - Trigger: `date_age_days > 180` or `future_date == 1`

#### Money Orders (4 fraud types)

1. **REPEAT_OFFENDER**: Payer with escalation history
2. **COUNTERFEIT_FORGERY**: Fake or counterfeit money order
3. **AMOUNT_ALTERATION**: Amount mismatch or spelling errors
4. **SIGNATURE_FORGERY**: Missing signature (mandatory REJECT)

### Decision Logic Rules

**Checks:**
- Missing signature: 1st time = ESCALATE, 2nd time = REJECT
- Future-dated check: REJECT (STALE_CHECK)
- Stale check (>180 days): REJECT (STALE_CHECK)
- High fraud score (≥95%): REJECT
- Repeat offender (fraud_count > 0): REJECT

**Money Orders:**
- Missing signature: REJECT (mandatory)
- Amount spelling errors: REJECT (AMOUNT_ALTERATION)
- Repeat offender (escalate_count > 0 AND fraud_risk ≥ 30%): REJECT
- High fraud score (≥95%): REJECT

**Paystubs:**
- Repeat offender (escalate_count > 0 AND fraud_risk ≥ 20%): REJECT
- Zero withholding suspicious: ESCALATE/REJECT based on ML score

**Bank Statements:**
- New customers: Never show fraud types (even if REJECT)
- Repeat customers: Show fraud types only for REJECT/ESCALATE

### Prompt Engineering

**System Prompt Structure:**
```
You are an expert fraud analyst specializing in [document type] verification.

Your role is to analyze [document] data and provide detailed fraud risk assessments.

You have access to:
1. ML model fraud scores (Random Forest + XGBoost ensemble)
2. Extracted document data
3. Customer transaction history
4. Database of known fraud patterns

CRITICAL INSTRUCTIONS - FRAUD TYPE TAXONOMY:
[Lists all fraud types with triggers]

CRITICAL INSTRUCTIONS - DECISION RULES:
[Lists mandatory decision rules]

Always provide:
1. recommendation: APPROVE/REJECT/ESCALATE
2. confidence_score: 0.0-1.0
3. summary: Natural language explanation
4. key_indicators: List of fraud indicators
5. fraud_types: List (only for REJECT/ESCALATE)
6. fraud_explanations: Structured explanations
```

---

## 🗄️ Database Schema

### Core Tables

#### Documents (Master Table)
```sql
CREATE TABLE documents (
  document_id UUID PRIMARY KEY,
  file_name VARCHAR,
  document_type VARCHAR, -- 'check', 'paystub', 'money_order', 'bank_statement'
  upload_date TIMESTAMP,
  user_id VARCHAR,
  status VARCHAR -- 'pending', 'analyzed', 'rejected'
);
```

#### Checks Table
```sql
CREATE TABLE checks (
  check_id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(document_id),
  check_number VARCHAR,
  amount DECIMAL,
  check_date DATE,
  payer_name VARCHAR,
  payee_name VARCHAR,
  bank_name VARCHAR,
  routing_number VARCHAR,
  account_number VARCHAR,
  fraud_risk_score DECIMAL(5,4), -- 0.0000-1.0000
  model_confidence DECIMAL(5,4),
  ai_recommendation VARCHAR, -- 'APPROVE', 'REJECT', 'ESCALATE'
  fraud_type VARCHAR, -- Single fraud type
  fraud_types JSONB, -- Array of fraud types
  fraud_explanations JSONB, -- Structured explanations
  created_at TIMESTAMP,
  timestamp TIMESTAMP
);
```

#### Paystubs Table
```sql
CREATE TABLE paystubs (
  paystub_id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(document_id),
  employee_name VARCHAR,
  employer_name VARCHAR,
  gross_pay DECIMAL,
  net_pay DECIMAL,
  pay_period_start DATE,
  pay_period_end DATE,
  fraud_risk_score DECIMAL(5,4),
  ai_recommendation VARCHAR,
  fraud_type VARCHAR,
  created_at TIMESTAMP
);
```

#### Money Orders Table
```sql
CREATE TABLE money_orders (
  money_order_id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(document_id),
  purchaser_name VARCHAR,
  payee_name VARCHAR,
  amount DECIMAL,
  money_order_number VARCHAR,
  issuer VARCHAR,
  serial_number VARCHAR,
  fraud_risk_score DECIMAL(5,4),
  ai_recommendation VARCHAR,
  fraud_type VARCHAR,
  created_at TIMESTAMP
);
```

#### Bank Statements Table
```sql
CREATE TABLE bank_statements (
  statement_id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(document_id),
  account_holder VARCHAR,
  bank_name VARCHAR,
  account_number VARCHAR,
  statement_period_start DATE,
  statement_period_end DATE,
  beginning_balance DECIMAL,
  ending_balance DECIMAL,
  fraud_risk_score DECIMAL(5,4),
  ai_recommendation VARCHAR,
  fraud_type VARCHAR,
  created_at TIMESTAMP
);
```

### Customer Tracking Tables

#### Check Customers
```sql
CREATE TABLE check_customers (
  customer_id UUID PRIMARY KEY,
  payer_name VARCHAR UNIQUE,
  payee_name VARCHAR,
  address TEXT,
  total_submissions INTEGER,
  high_risk_count INTEGER,
  fraud_count INTEGER,
  escalate_count INTEGER,
  last_submission_date TIMESTAMP,
  fraud_status VARCHAR -- 'APPROVE', 'REJECT', 'ESCALATE'
);
```

Similar tables exist for:
- `paystub_customers`
- `money_order_customers`
- `bank_statement_customers`

### Database Views

- `v_checks_analysis`: Aggregated check data with recommendations
- `v_money_orders_analysis`: Aggregated money order data
- `v_documents_with_risk`: All documents with risk scores
- `v_paystub_insights_clean`: Paystub insights for dashboards

---

## 🎨 Frontend Architecture

### Component Structure

**Main App (`Frontend/src/App.js`):**
- `AuthProvider` (Context) - Global auth state
- `Router` (React Router) - Route management
- Conditional layout (header/footer for authenticated pages)

**Analysis Pages:**
- `CheckAnalysis.jsx` - Check upload and results
- `PaystubAnalysis.jsx` - Paystub upload and results
- `MoneyOrderAnalysis.jsx` - Money order upload and results
- `BankStatementAnalysis.jsx` - Bank statement upload and results
- `RealTimeAnalysis.jsx` - CSV upload and transaction analysis

**Insights Dashboards:**
- `CheckInsights.jsx` - Check analytics
- `PaystubInsights.jsx` - Paystub analytics
- `BankStatementInsights.jsx` - Bank statement analytics
- `RealTimeInsights.jsx` - Transaction analytics

### State Management

**AuthContext:**
```javascript
const { user, token, login, logout } = useAuth();
```

**Analysis Page State:**
- `selectedFile`: Uploaded file
- `analysisResult`: API response
- `loading`: Loading state
- `error`: Error message

### Data Visualization

**Charts:**
- Pie Chart: AI recommendation distribution
- Bar Chart: Risk distribution
- Line Chart: Fraud trend over time
- Geographic Map: Transaction locations

---

## ⚙️ Processing Pipeline

### 10-Stage Pipeline

**Stage 1: OCR Extraction (Mindee API)**
- Call Mindee ClientV2 API
- Extract fields: payer, payee, amount, dates, etc.
- Return `extracted_data` dict + `raw_text`

**Stage 2: Data Normalization**
- Detect bank name
- Use bank-specific normalizer
- Normalize amounts, dates, names
- Calculate `completeness_score`

**Stage 3: Validation Rules**
- Check missing signature
- Validate critical fields
- Check duplicates
- Collect `validation_issues`

**Stage 4: ML Fraud Detection**
- Extract 30+ features
- Run Random Forest + XGBoost
- Calculate ensemble score
- Determine `risk_level`

**Stage 5: Customer History**
- Query customer table
- Get submission history
- Check for duplicates

**Stage 6: AI Fraud Analysis**
- Build GPT-4 prompt
- Call OpenAI API
- Parse response

**Stage 7: Anomaly Generation**
- Combine ML + AI anomalies
- Add validation issues

**Stage 8: Confidence Calculation**
- Weighted average of completeness, ML confidence, AI confidence

**Stage 9: Final Decision**
- Apply decision rules
- Return APPROVE/REJECT/ESCALATE

**Stage 10: Build Response**
- Combine all results
- Format response

---

## 🚀 Deployment

### Production Deployment

**Backend:**
```bash
# Use production WSGI server
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

**Frontend:**
```bash
# Build production bundle
npm run build

# Serve with nginx or similar
```

**Environment Variables:**
Set all required environment variables in production environment.

**Database:**
Ensure Supabase is configured with proper security settings.

---

## 👨‍💻 Development Guide

### Adding a New Document Type

1. Create document module in `Backend/<document_type>/`
2. Implement extractor class
3. Create ML detector in `ml/` subdirectory
4. Create AI agent in `ai/` subdirectory
5. Add normalization logic
6. Add API endpoint in `api_server.py`
7. Create frontend page
8. Add database table and views

### Code Style

- Python: Follow PEP 8
- JavaScript: Follow ESLint rules
- Use type hints in Python
- Document all functions

---

## 🧪 Testing

### Backend Tests

```bash
# Run tests
python -m pytest Backend/tests/

# Test specific module
python Backend/real_time/test_guardrails.py
```

### Frontend Tests

```bash
cd Frontend
npm test
```

---

## 🔧 Troubleshooting

### Common Issues

**ML Models Not Loading:**
- Check model files exist in `Backend/<document_type>/ml/models/`
- Train models if missing: `python training/train_<type>_models.py`

**API Errors:**
- Check environment variables are set
- Verify API keys are valid
- Check logs in `Backend/logs/`

**Database Connection Issues:**
- Verify Supabase credentials
- Check network connectivity
- Verify table schemas exist

---

## 📊 Performance Metrics

### Processing Times
- Check Analysis: 5-15 seconds
- Paystub Analysis: 5-12 seconds
- Money Order Analysis: 6-15 seconds
- Bank Statement Analysis: 8-20 seconds
- Real-Time CSV (1000 transactions): 30-60 seconds

### Model Performance
- ML Model Accuracy: ~85-90%
- AI Recommendation Accuracy: ~90-95%
- Ensemble Model Confidence: 0.7-0.95

---

## 🔒 Security

- JWT Authentication
- Password hashing (bcrypt)
- CORS protection
- File upload validation
- SQL injection prevention
- API key encryption

---

## 📚 Document-Specific Logic & Decision Rules

### Check Analysis Logic

#### Processing Flow

**Stage 1: OCR Extraction (Mindee API)**
- Uses Mindee ClientV2 API with check-specific model ID
- Extracts fields: `payer_name`, `payee_name`, `amount_numeric`, `amount_written`, `check_number`, `bank_name`, `routing_number`, `account_number`, `check_date`, `signature_detected`
- Field mapping: Maps Mindee field names to standardized schema
- Returns `extracted_data` dict + `raw_text` string

**Stage 2: Bank-Specific Normalization**
- Detects bank name from extracted data
- Uses `CheckNormalizerFactory` to get bank-specific normalizer:
  - Bank of America → `BOACheckNormalizer`
  - Chase → `ChaseCheckNormalizer`
  - Wells Fargo → `WellsFargoCheckNormalizer`
  - Default → `GenericCheckNormalizer`
- Normalizes amounts (removes $, commas, parses to float)
- Normalizes dates (converts to ISO format)
- Normalizes names (title case, removes extra spaces)
- Calculates `completeness_score` (0-1)
- Validates against `bank_dictionary` table (case-insensitive)
- Returns `normalized_data` with validation flags

**Stage 3: Validation Rules**
- **Signature Check**: `signature_detected == False` → Adds issue (AI handles escalation logic)
- **Critical Fields**: Checks for missing `check_number`, `payer_name`, `payee_name`
- **Same Payer/Payee**: Payer and payee cannot be the same → Adds issue
- **High Amount**: Amount > $10,000 → Adds issue (requires verification)
- **Too Many Missing Fields**: ≥3 critical fields missing → Adds issue
- **No Early Exits**: All issues collected, pipeline continues

**Stage 4: ML Fraud Detection**
- Extracts 30 features using `CheckFeatureExtractor`
- Scales features using pre-trained scaler
- Runs Random Forest → `rf_score`
- Runs XGBoost → `xgb_score`
- Calculates ensemble: `(0.4 * rf_score) + (0.6 * xgb_score)`
- Applies validation rule adjustments:
  - Missing signature: +0.3 to score
  - Duplicate check: Score = 1.0 (automatic reject)
  - Critical issues: +0.2 to score
- Determines `risk_level`: LOW/MEDIUM/HIGH/CRITICAL
- Generates anomalies list

**Stage 5: Customer History**
- Queries `check_customers` table for `payer_name`
- Gets: `total_submissions`, `high_risk_count`, `fraud_count`, `escalate_count`, `last_submission_date`
- Checks for duplicate: `check_number` + `payer_name` combination
- Returns `customer_info` dict

**Stage 6: AI Fraud Analysis**
- Builds comprehensive prompt with:
  - Extracted check data
  - ML analysis results
  - Customer history
  - Validation issues
- Calls GPT-4 API
- Parses response:
  - `recommendation`: APPROVE/REJECT/ESCALATE
  - `confidence_score`: 0.0-1.0
  - `summary`: Natural language explanation
  - `key_indicators`: List of fraud indicators
  - `fraud_types`: List (only for REJECT)
  - `fraud_explanations`: Structured explanations

**Stage 7: Anomaly Generation**
- Combines ML anomalies + AI key_indicators
- Adds validation issues
- Removes duplicates
- Sorts by severity

**Stage 8: Confidence Calculation**
- Weighted average:
  - 30% data completeness score
  - 30% ML model confidence
  - 40% AI confidence score

**Stage 9: Final Decision Logic**
```python
# Priority order:
1. REJECT if critical validation issues (unsupported bank, missing check number, etc.)
2. REJECT if duplicate check detected
3. Defer to AI recommendation (AI handles missing signature with escalation logic)
4. Fallback to ML score thresholds:
   - fraud_score >= 0.7 → REJECT
   - fraud_score >= 0.3 → ESCALATE
   - fraud_score < 0.3 → APPROVE
```

**Stage 10: Response Building**
- Combines all analysis results
- Includes validation issues, anomalies, confidence score
- Flags duplicate detection
- Returns complete response dict

#### Check-Specific Decision Rules

**Missing Signature:**
- **1st Time**: ESCALATE (AI recommendation)
- **2nd Time** (escalate_count > 0): REJECT (AI recommendation)
- Not an automatic rejection - evaluated based on customer history

**Future-Dated Check:**
- Automatically REJECT (STALE_CHECK fraud type)
- Trigger: `check_date` is in the future

**Stale Check (>180 days):**
- Automatically REJECT (STALE_CHECK fraud type)
- Trigger: `date_age_days > 180`

**High Fraud Score (≥95%):**
- Automatically REJECT
- ML ensemble detected critical fraud indicators

**Repeat Offender:**
- Trigger: `fraud_count > 0`
- Automatically REJECT (REPEAT_OFFENDER fraud type)

**Duplicate Check:**
- Trigger: Same `check_number` + `payer_name` already exists
- Automatically REJECT

**Critical Validation Issues:**
- Missing check number → REJECT
- Missing payer name → REJECT
- Missing payee name → REJECT
- Unsupported bank → REJECT (if not in bank_dictionary)
- Too many critical fields missing (≥3) → REJECT

---

### Paystub Analysis Logic

#### Processing Flow

**Stage 1: OCR Extraction (Mindee API)**
- Uses Mindee ClientV2 API with paystub-specific model ID
- Extracts fields: `first_name`, `last_name`, `employee_name`, `employer_name`, `gross_pay`, `net_pay`, `pay_period_start_date`, `pay_period_end_date`, `deductions` (array), `taxes` (array)
- Processes deductions/taxes arrays to extract:
  - `federal_tax`
  - `state_tax`
  - `social_security`
  - `medicare`
- Combines `first_name` + `last_name` → `employee_name`
- Returns `extracted_data` dict + `raw_text`

**Stage 2: Normalization**
- Uses `PaystubNormalizerFactory` to get normalizer
- Normalizes amounts (removes $, commas, parses to float)
- Normalizes dates (converts to ISO format)
- Validates pay period dates
- Calculates tax deduction ratios
- Returns `normalized_data`

**Stage 3: Validation Rules**
- **Critical Fields**: Checks for missing `company_name`, `employee_name`, `gross_pay`, `net_pay`, `pay_period`
- **Impossible Values**: Net pay > Gross pay → CRITICAL issue
- **Missing Pay Period**: Both start and end dates missing → Issue

**Stage 4: ML Fraud Detection**
- Extracts 18 features
- Runs Random Forest + XGBoost ensemble
- Calculates fraud risk score
- **REQUIRED**: ML models must be loaded (no fallback)

**Stage 5: Employee History**
- Queries `paystub_customers` table for `employee_name`
- Gets: `total_submissions`, `escalate_count`, `fraud_count`
- Checks for duplicate: `employee_name` + `pay_period_start` + `pay_date`

**Stage 6: AI Fraud Analysis**
- Builds prompt with paystub data, ML results, employee history
- Calls GPT-4 API
- **Post-AI Validation Override**:
  - If `fraud_count > 0` AND `fraud_risk_score >= 0.5` (50%):
    - Override AI recommendation to REJECT
    - Add reasoning: "Repeat fraud offender detected"
  - Previous escalations (escalate_count) do NOT trigger auto-rejection
  - Only documented fraud history triggers override

**Stage 7: Anomaly Generation**
- Combines ML feature importance + AI key indicators

**Stage 8: Confidence Calculation**
- Weighted average: 40% ML confidence + 60% AI confidence

**Stage 9: Final Decision Logic**
```python
# Priority order:
1. Defer to AI recommendation (with post-validation override)
2. Fallback to ML score thresholds:
   - fraud_score >= 0.85 → REJECT
   - fraud_score >= 0.5 → ESCALATE
   - fraud_score < 0.5 → APPROVE
```

**Stage 10: Response Building**
- Includes employee info, validation issues, anomalies
- Returns complete response

#### Paystub-Specific Decision Rules

**Repeat Fraud Offender:**
- Trigger: `fraud_count > 0` AND `fraud_risk_score >= 0.5` (50%)
- Action: Override AI recommendation to REJECT
- Logic: Only documented fraud history triggers override (not escalations)

**Zero Withholding Suspicious:**
- Trigger: Federal/state tax = 0 but gross pay > threshold
- Action: ESCALATE or REJECT based on ML score

**Net Pay > Gross Pay:**
- Trigger: Impossible value detected
- Action: CRITICAL validation issue → REJECT

**Duplicate Paystub:**
- Trigger: Same `employee_name` + `pay_period_start` already exists
- Action: Adds validation issue

**Missing Critical Fields:**
- Trigger: Missing `company_name`, `employee_name`, `gross_pay`, `net_pay`, or `pay_period`
- Action: Adds validation issue

---

### Money Order Analysis Logic

#### Processing Flow

**Stage 1: OCR Extraction (Google Vision API)**
- Uses Google Cloud Vision API for text extraction
- Extracts fields using regex patterns:
  - `issuer`: Western Union, MoneyGram, USPS, etc.
  - `serial_number`: Primary serial number
  - `serial_secondary`: Secondary serial (if present)
  - `amount`: Numeric amount
  - `amount_in_words`: Written amount
  - `payee`: Payee name
  - `purchaser`: Purchaser name
  - `date`: Issue date
  - `location`: Issue location
  - `signature`: Signature detection

**Stage 2: Normalization**
- Uses `MoneyOrderNormalizerFactory` to get issuer-specific normalizer
- Normalizes amounts, dates, names
- Validates serial number format against issuer patterns
- Calculates completeness score

**Stage 3: Validation Rules**
- **Missing Signature**: CRITICAL → Mandatory REJECT
- **Amount Mismatch**: Numeric ≠ Written amount → Issue
- **Invalid Issuer**: Issuer not recognized → Issue
- **Serial Format Invalid**: Serial doesn't match issuer pattern → Issue

**Stage 4: ML Fraud Detection**
- Extracts 30 features
- Runs Random Forest + XGBoost ensemble
- Calculates fraud risk score

**Stage 5: Customer History**
- Queries `money_order_customers` table for `purchaser_name`
- Gets: `total_submissions`, `escalate_count`
- Checks for duplicate: `serial_number` + `purchaser_name`

**Stage 6: AI Fraud Analysis**
- Builds prompt with money order data, ML results, customer history
- Calls GPT-4 API
- **Mandatory Signature Check**:
  - If `signature_present == False`:
    - Return ESCALATE (1st time) or REJECT (2nd time)
    - Skip normal fraud analysis
- **Repeat Offender Check**:
  - If `escalate_count > 0` AND `fraud_risk_score >= 0.3` (30%):
    - Override to REJECT
    - Add REPEAT_OFFENDER fraud type

**Stage 7: Anomaly Generation**
- Combines ML anomalies + AI key indicators
- Adds validation issues

**Stage 8: Confidence Calculation**
- Weighted average of completeness, ML confidence, AI confidence

**Stage 9: Final Decision Logic**
```python
# Priority order:
1. REJECT if missing signature (mandatory)
2. REJECT if repeat offender (escalate_count > 0 AND fraud_risk >= 30%)
3. REJECT if high fraud score (≥95%)
4. Defer to AI recommendation
5. Fallback to ML score thresholds
```

**Stage 10: Response Building**
- Includes all analysis results
- Returns complete response

#### Money Order-Specific Decision Rules

**Missing Signature (MANDATORY):**
- Trigger: `signature_present == False`
- Action: **AUTOMATIC REJECT** (highest priority)
- Logic: No exceptions - all money orders require signature

**Amount Spelling Errors:**
- Trigger: Written amount contains misspellings in OCR text (e.g., "FOUN" instead of "FOUR")
- Action: REJECT (AMOUNT_ALTERATION fraud type)
- Logic: OCR auto-corrects, but raw text must be manually checked

**Amount Mismatch:**
- Trigger: `exact_amount_match == 0` (numeric ≠ written)
- Action: REJECT (AMOUNT_ALTERATION fraud type)
- Priority: Takes precedence over weak signature detection

**Repeat Offender:**
- Trigger: `escalate_count > 0` AND `fraud_risk_score >= 0.3` (30%)
- Action: REJECT (REPEAT_OFFENDER fraud type)
- Logic: Lower threshold than paystubs (30% vs 50%)

**Invalid Issuer/Serial:**
- Trigger: `issuer_valid < 1.0` OR `serial_format_valid == 0`
- Action: REJECT (COUNTERFEIT_FORGERY fraud type)

**High Fraud Score (≥95%):**
- Trigger: ML ensemble score ≥ 0.95
- Action: REJECT
- Logic: ML detected critical fraud indicators

---

### Bank Statement Analysis Logic

#### Processing Flow

**Stage 1: OCR Extraction (Mindee API)**
- Uses Mindee ClientV2 API with bank statement-specific model ID
- Extracts fields: `account_holder`, `bank_name`, `account_number`, `statement_period_start`, `statement_period_end`, `beginning_balance`, `ending_balance`, `transactions` (array)
- Processes transaction arrays
- Returns `extracted_data` dict + `raw_text`

**Stage 2: Normalization**
- Normalizes bank name using `financial_institutions` table (case-insensitive)
- Uses `BankStatementNormalizerFactory` to get bank-specific normalizer
- Normalizes balances, dates, transaction amounts
- Validates balance consistency
- Calculates transaction statistics

**Stage 3: Validation Rules**
- **Balance Consistency**: Beginning balance + transactions = Ending balance
- **Missing Critical Fields**: Account holder, bank name, statement period
- **Negative Balance**: Ending balance < 0 → Issue
- **Transaction Pattern Anomalies**: Unusual transaction patterns → Issue

**Stage 4: ML Fraud Detection**
- Extracts 35 features
- Runs Random Forest + XGBoost ensemble
- Calculates fraud risk score
- **REQUIRED**: ML models must be loaded (no fallback)

**Stage 5: Customer History**
- Queries `bank_statement_customers` table for `account_holder_name`
- Gets: `total_submissions`, `high_risk_count`
- Checks for duplicate: `account_holder_name` + `statement_period_start`

**Stage 6: AI Fraud Analysis**
- Builds prompt with bank statement data, ML results, customer history
- Calls GPT-4 API
- **New Customer Policy**:
  - If `is_new_customer == True`:
    - Never show fraud types (even if REJECT)
    - Fraud types remain empty
- **Repeat Customer Policy**:
  - Show fraud types only for REJECT/ESCALATE
  - Never show fraud types for APPROVE

**Stage 7: Anomaly Generation**
- Combines ML anomalies + AI key indicators
- Adds validation issues

**Stage 8: Confidence Calculation**
- Weighted average of completeness, ML confidence, AI confidence

**Stage 9: Final Decision Logic**
```python
# Priority order:
1. Defer to AI recommendation
2. Fallback to ML score thresholds:
   - fraud_score >= 0.7 → REJECT
   - fraud_score >= 0.3 → ESCALATE
   - fraud_score < 0.3 → APPROVE
```

**Stage 10: Response Building**
- Includes customer info, validation issues, anomalies
- Returns complete response

#### Bank Statement-Specific Decision Rules

**New Customer Policy:**
- Trigger: `is_new_customer == True`
- Action: Never show fraud types (even if REJECT recommendation)
- Logic: New customers may have data quality issues, not fraud

**Repeat Customer Fraud Types:**
- Trigger: `is_new_customer == False` AND recommendation is REJECT/ESCALATE
- Action: Show fraud types from AI analysis
- Logic: Only repeat customers with confirmed fraud patterns show types

**Balance Consistency Violation:**
- Trigger: Beginning balance + transactions ≠ Ending balance
- Action: REJECT (BALANCE_CONSISTENCY_VIOLATION fraud type)

**Transaction Pattern Anomalies:**
- Trigger: Unusual transaction patterns detected by ML
- Action: ESCALATE or REJECT based on ML score

**Negative Balance:**
- Trigger: Ending balance < 0
- Action: Adds validation issue

**Missing Critical Fields:**
- Trigger: Missing `account_holder`, `bank_name`, or `statement_period`
- Action: Adds validation issue

---

### Real-Time Transaction Analysis Logic

#### Processing Flow

**Stage 1: CSV Processing**
- Reads CSV file with pandas
- Validates required columns: `transaction_id`, `timestamp`, `amount`, `merchant`, `customer_id`, `location`, `transaction_type`
- Parses data types and validates formats
- Returns transactions list

**Stage 2: Feature Extraction**
- Extracts 50+ features per transaction:
  - Amount features: `amount_zscore`, `amount_deviation`, `amount_rounded`
  - Time features: `hour`, `day_of_week`, `is_night`, `is_weekend`
  - Location features: `country_mismatch`, `is_foreign_currency`
  - Customer features: `customer_txn_count`, `amount_to_balance_ratio`
  - Merchant features: `high_risk_category`, `is_transfer`
  - Pattern features: `velocity_abuse`, `money_mule_pattern`

**Stage 3: ML Fraud Detection**
- Scales features using pre-trained scaler
- Runs XGBoost model (single model, not ensemble)
- Calculates fraud risk score per transaction
- Determines risk level: LOW/MEDIUM/HIGH/CRITICAL

**Stage 4: Fraud Reason Assignment**
- Normalizes fraud reasons based on feature patterns:
  - Velocity abuse: `customer_txn_count >= 3` AND `amount_deviation > 2`
  - Account takeover: `country_mismatch == 1` OR `login_transaction_mismatch == 1`
  - Unusual location: `country_mismatch == 1`
  - Night-time activity: `is_night == 1` AND `amount_zscore > 1.5`
  - High-risk merchant: `high_risk_category == 1`
  - Card-not-present risk: `is_foreign_currency == 1` OR `is_transfer == 1`
  - Money mule pattern: Transfer + `amount_to_balance_ratio > 0.9` + foreign currency

**Stage 5: Insights Generation**
- Calculates summary metrics:
  - Total transactions
  - High-risk count
  - Average risk score
  - Total amount
- Generates risk distribution (0-30%, 30-70%, 70-100%)
- Generates geographic heatmap data
- Generates time-series data
- Identifies top high-risk transactions

**Stage 6: AI Analysis**
- Builds comprehensive prompt with:
  - Summary metrics
  - High-risk transactions
  - Pattern analysis
- Calls GPT-4 for natural language summary
- Returns AI analysis with recommendations

**Stage 7: Response Building**
- Combines all analysis results
- Returns complete response with transactions, insights, AI analysis

#### Real-Time Transaction Decision Rules

**Velocity Abuse:**
- Trigger: `customer_txn_count >= 3` AND `amount_deviation > 2`
- Action: Flag as high-risk, assign "Velocity abuse" reason

**Account Takeover:**
- Trigger: `country_mismatch == 1` OR `login_transaction_mismatch == 1`
- Action: Flag as high-risk, assign "Account takeover" reason

**Money Mule Pattern:**
- Trigger: Transfer transaction + `amount_to_balance_ratio > 0.9` + foreign currency + first-time payee
- Action: Flag as high-risk, assign "Money mule pattern" reason

**High-Risk Merchant:**
- Trigger: Merchant category in blacklist (Western Union, MoneyGram, crypto, gambling, etc.)
- Action: Flag as high-risk, assign "High-risk merchant" reason

**Night-Time Activity:**
- Trigger: `is_night == 1` AND `amount_zscore > 1.5`
- Action: Flag as medium-risk, assign "Night-time activity" reason

**Round Dollar Pattern:**
- Trigger: Amount is round number (ends in .00) AND multiple of 100
- Action: Flag as suspicious, assign "Round-dollar pattern" reason

---

## 📝 License

Proprietary - All Rights Reserved

---

## 👥 Contributors

- Development Team
- ML/AI Team
- QA Team

---

## 📞 Support

For issues and questions, contact the development team.

---

**Last Updated:** December 2024
**Version:** 1.0.0

