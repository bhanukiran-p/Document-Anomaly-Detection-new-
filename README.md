# XFORIA DAD - Document Analysis & Detection Platform

![License](https://img.shields.io/badge/license-Proprietary-blue.svg)
![React](https://img.shields.io/badge/React-18.2.0-61dafb?logo=react)
![Flask](https://img.shields.io/badge/Flask-3.1.1-000000?logo=flask)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?logo=python)
![Node](https://img.shields.io/badge/Node.js-16+-339933?logo=nodedotjs)

**Your Guardian Against Fraud** - AI-Powered Financial Document Analysis Platform

---

## Overview

XFORIA DAD (Document Analysis & Detection) is an enterprise-grade fraud detection platform that combines AI-powered document extraction, machine learning fraud detection, and advanced analytics to protect financial institutions from fraudulent transactions.

### Key Capabilities

- **Multi-Document Analysis**: Checks, Money Orders, Paystubs, Bank Statements
- **ML Fraud Detection**: Ensemble models (Random Forest + XGBoost) with 85%+ accuracy
- **AI-Powered Analysis**: GPT-4 integration for contextual fraud assessment
- **Real-time Processing**: Instant document analysis with confidence scoring
- **Data Export**: JSON and CSV formats for dashboards and reporting
- **User Authentication**: Secure login and user management system

---

## Features

### Document Processing
- AI-powered OCR via Mindee API
- Support for JPG, PNG, and PDF formats (up to 16MB)
- Automatic PDF to image conversion
- Field-level confidence scoring
- Multi-language document support

### Fraud Detection
- 50+ feature extraction points per document
- Ensemble ML models (Random Forest + XGBoost)
- Risk scoring: LOW, MEDIUM, HIGH, CRITICAL
- GPT-4 powered contextual analysis
- Historical pattern matching
- Anomaly detection and flagging

### Analytics & Export
- Real-time analysis dashboards
- JSON export with complete metadata
- CSV export optimized for BI tools
- Filtered anomaly reporting
- Downloadable analysis reports

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        XFORIA DAD Platform                        │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────┐                    ┌──────────────────────┐
│   React Frontend    │                    │    Flask Backend     │
│   (Port 3000)       │      REST API      │    (Port 5001)       │
│                     │ ◄─────────────────►│                      │
│  - Authentication   │                    │  - Document Upload   │
│  - File Upload      │                    │  - OCR Extraction    │
│  - Results Display  │                    │  - ML Processing     │
│  - Data Export      │                    │  - AI Analysis       │
└─────────────────────┘                    └──────────────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────┐
                    │                                 │                     │
            ┌───────▼────────┐           ┌───────────▼────────┐   ┌────────▼────────┐
            │  Mindee API    │           │   ML Models        │   │   OpenAI GPT-4  │
            │  (OCR)         │           │   (Fraud Detect)   │   │   (AI Analysis) │
            └────────────────┘           └────────────────────┘   └─────────────────┘
```

---

## Technology Stack

### Frontend
- **React 18.2**: Modern UI framework with Hooks and Context
- **React Router 6**: Client-side routing
- **Axios**: HTTP client for API calls
- **React Dropzone**: Drag-and-drop file uploads
- **React Icons**: Icon library

### Backend
- **Flask 3.x**: Python web framework
- **Mindee API**: AI-powered document extraction
- **scikit-learn**: Random Forest classifier
- **XGBoost**: Gradient boosting models
- **LangChain**: AI agent framework
- **OpenAI GPT-4**: Advanced fraud analysis

### Database (Optional)
- **Supabase**: PostgreSQL cloud database
- **JSON Storage**: Fallback authentication

---

## Quick Start

### Prerequisites

```bash
# System Requirements
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- Poppler (for PDF processing)
```

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "DAD New"
   ```

2. **Backend Setup**
   ```bash
   cd Backend
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd Frontend
   npm install
   ```

4. **Environment Configuration**

   Create `Backend/.env`:
   ```env
   MINDEE_API_KEY=your_mindee_api_key
   OPENAI_API_KEY=your_openai_api_key
   PORT=5001
   ```

   Create `Frontend/.env`:
   ```env
   REACT_APP_API_URL=http://localhost:5001/api
   ```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd Backend
python api_server.py
```
Server runs on: `http://localhost:5001`

**Terminal 2 - Frontend:**
```bash
cd Frontend
npm start
```
App opens at: `http://localhost:3000`

---

## Project Structure

```
DAD New/
├── Frontend/                      # React Application
│   ├── public/                   # Static assets
│   │   ├── index.html
│   │   ├── DAD_red_white.png
│   │   └── New_FD.png
│   ├── src/
│   │   ├── components/           # Reusable components
│   │   │   ├── Header.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── pages/                # Page components
│   │   │   ├── LandingPage.jsx
│   │   │   ├── HomePage.jsx
│   │   │   ├── CheckAnalysis.jsx
│   │   │   ├── MoneyOrderAnalysis.jsx
│   │   │   ├── PaystubAnalysis.jsx
│   │   │   └── BankStatementAnalysis.jsx
│   │   ├── context/              # State management
│   │   │   └── AuthContext.js
│   │   ├── services/             # API integration
│   │   │   └── api.js
│   │   ├── styles/               # Styling
│   │   │   ├── colors.js
│   │   │   └── GlobalStyles.css
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── README.md                 # Frontend documentation
│
├── Backend/                       # Flask API Server
│   ├── api_server.py             # Main API server
│   ├── check/                    # Check analysis module
│   │   └── extractor.py
│   ├── money_order/              # Money order module
│   │   └── extractor.py
│   ├── paystub/                  # Paystub module
│   │   └── extractor.py
│   ├── bank_statement/           # Bank statement module
│   │   └── extractor.py
│   ├── ml_models/                # Machine learning models
│   │   ├── fraud_detector.py
│   │   ├── feature_extractor.py
│   │   └── advanced_features.py
│   ├── langchain_agent/          # AI analysis agent
│   │   ├── fraud_analysis_agent.py
│   │   ├── tools.py
│   │   └── result_storage.py
│   ├── database/                 # Database layer
│   │   ├── connection.py
│   │   └── models.py
│   ├── auth/                     # Authentication
│   │   ├── middleware.py
│   │   └── utils.py
│   ├── normalization/            # Data normalization
│   │   └── normalizer.py
│   ├── risk/                     # Risk scoring
│   │   └── ml_risk_scorer.py
│   ├── users.json                # User database
│   ├── requirements.txt
│   └── README.md                 # Backend documentation
│
└── README.md                      # This file
```

---

## API Documentation

### Endpoints

#### Health Check
```http
GET /api/health

Response:
{
  "status": "healthy",
  "service": "XFORIA DAD API",
  "version": "1.0.0"
}
```

#### Document Analysis Endpoints

All analysis endpoints follow the same pattern:

```http
POST /api/{document-type}/analyze
Content-Type: multipart/form-data

Parameters:
  - file: Document file (JPG, PNG, PDF)

Response:
{
  "success": true,
  "data": {
    "extracted_data": {...},
    "ml_analysis": {
      "fraud_risk_score": 0.23,
      "risk_level": "LOW",
      "model_confidence": 0.87
    },
    "ai_analysis": {
      "recommendation": "APPROVE",
      "confidence": 0.92,
      "summary": "..."
    },
    "anomalies": [],
    "confidence_score": 0.85
  }
}
```

**Available Endpoints:**
- `/api/check/analyze` - Check analysis
- `/api/money-order/analyze` - Money order analysis
- `/api/paystub/analyze` - Paystub analysis
- `/api/bank-statement/analyze` - Bank statement analysis

---

## Features in Detail

### 1. Check Analysis
- Extract bank name, check number, amount, date
- Verify payee and payer information
- Detect signature presence
- Account/routing number extraction
- MICR line validation

### 2. Money Order Analysis
- Issuer and serial number extraction
- Purchaser and payee identification
- Amount validation (numeric + written)
- Date and location verification
- Fraud pattern detection

### 3. Paystub Analysis
- Employer and employee details
- Pay period and payment date
- Gross/net pay calculation validation
- Tax withholdings (Federal, State, FICA)
- YTD totals verification

### 4. Bank Statement Analysis
- Account holder and account number
- Opening/closing balance reconciliation
- Transaction history extraction
- Credit/debit total calculation
- Unusual pattern detection

---

## Fraud Detection Pipeline

### Stage 1: Document Extraction
- Mindee API OCR processing
- Field-level confidence scoring
- Raw text capture for analysis

### Stage 2: ML Analysis
- 50+ feature extraction
- Random Forest classification
- XGBoost prediction
- Ensemble voting for final score

### Stage 3: AI Analysis
- GPT-4 contextual review
- Historical pattern matching
- Risk factor identification
- Recommendation generation

### Stage 4: Anomaly Detection
- Missing field detection
- Value range validation
- Consistency checks
- Pattern anomalies

---

## Data Export

### JSON Export
Complete analysis results including:
- All extracted fields
- ML model scores
- AI analysis details
- Confidence metrics
- Anomaly list
- Timestamp

### CSV Export
Dashboard-optimized format with:
- Document metadata
- Key extracted fields
- Fraud risk metrics
- AI recommendation
- Top anomalies (filtered)
- Export timestamp

---

## Security & Privacy

### Data Security
- Temporary file storage only
- Automatic file cleanup
- No permanent document storage
- Encrypted API communication (HTTPS in production)

### Authentication
- Secure user registration and login
- Password hashing
- Session management
- Protected routes
- JWT tokens (future)

### API Security
- CORS configuration
- Request validation
- File size limits (16MB)
- File type validation
- Error handling

---

## Performance

### Response Times
- Document upload: < 1 second
- OCR extraction: 2-5 seconds
- ML analysis: 1-2 seconds
- AI analysis: 3-5 seconds
- **Total**: 6-13 seconds per document

### Scalability
- Stateless API design
- Horizontal scaling ready
- Async processing capable
- CDN for frontend
- Database connection pooling

---

## Deployment

### Production Checklist

**Backend:**
- [ ] Set debug=False in Flask
- [ ] Configure production database
- [ ] Set up HTTPS/SSL
- [ ] Configure environment variables
- [ ] Set up logging
- [ ] Configure CORS for production domain

**Frontend:**
- [ ] Update API_URL to production
- [ ] Build production bundle
- [ ] Configure CDN
- [ ] Set up error tracking
- [ ] Enable gzip compression
- [ ] Configure caching

### Deployment Options

**Backend:**
- AWS EC2 / Elastic Beanstalk
- Google Cloud Run
- Heroku
- DigitalOcean

**Frontend:**
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

---

## Monitoring & Maintenance

### Logging
- API request/response logging
- Error tracking and reporting
- Performance metrics
- User activity logs

### Health Checks
- `/api/health` endpoint
- Database connectivity
- External API status
- System resource monitoring

---

## Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check Python version (3.8+)
   - Verify all dependencies installed
   - Check port 5001 availability
   - Verify environment variables

2. **Frontend build fails**
   - Delete `node_modules` and `package-lock.json`
   - Run `npm install` again
   - Check Node version (16+)

3. **API connection errors**
   - Verify backend is running
   - Check CORS configuration
   - Verify API URL in frontend .env

4. **File upload fails**
   - Check file size (max 16MB)
   - Verify file format (JPG, PNG, PDF)
   - Check backend temp folder permissions

For detailed troubleshooting, see:
- [Backend README](Backend/README.md)
- [Frontend README](Frontend/README.md)

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

Copyright © 2024 XFORIA. All rights reserved.

This is proprietary software. Unauthorized copying, distribution, or modification is strictly prohibited.

---

## Support

For technical support or inquiries:
- **Email**: support@xforia.com
- **Documentation**: https://docs.xforia.com
- **Website**: https://xforia.com

---

## Acknowledgments

- **Mindee**: AI-powered document OCR
- **OpenAI**: GPT-4 for fraud analysis
- **React Community**: Frontend framework
- **Flask Community**: Backend framework
- **scikit-learn & XGBoost**: ML models

---

## Roadmap

### Version 1.1 (Planned)
- [ ] Real-time collaboration features
- [ ] Advanced reporting dashboard
- [ ] API rate limiting
- [ ] Webhook support
- [ ] Mobile app (React Native)

### Version 2.0 (Future)
- [ ] Multi-tenancy support
- [ ] Advanced fraud detection models
- [ ] Blockchain verification
- [ ] Integration with banking APIs
- [ ] Real-time fraud alerts

---

**Where Innovation Meets Security | Zero Tolerance for Fraud**

© 2024 XFORIA DAD. All rights reserved.
