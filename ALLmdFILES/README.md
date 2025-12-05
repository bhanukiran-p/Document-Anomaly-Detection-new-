# XFORIA DAD - Document Analysis & Fraud Detection

AI-powered fraud detection system for document analysis and real-time transaction monitoring.

## Features

### On-Demand Document Analysis
- **Check Analysis** - Validate checks and detect alterations
- **Paystub Analysis** - Verify employment and income documents
- **Bank Statement Analysis** - Extract and analyze transaction history
- **Money Order Analysis** - Authenticate money orders

### Real-Time Fraud Detection
- **CSV Transaction Analysis** - Upload and analyze transaction data
- **ML-Based Detection** - Random Forest fraud classification
- **GPT-4 AI Insights** - Natural language fraud analysis and recommendations
- **Interactive Visualizations** - Charts and graphs for pattern identification

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- OpenAI API key (for GPT-4 analysis)
- Mindee API key (for document extraction)

### 1. Clone Repository
\`\`\`bash
git clone <repository-url>
cd "DAD New"
\`\`\`

### 2. Backend Setup

\`\`\`bash
cd Backend

# Install dependencies
pip install -r requirements.txt

# Configure environment  
# Create .env file with required keys

# Start server
python api_server.py
\`\`\`

Backend runs on \`http://localhost:5001\`

### 3. Frontend Setup

\`\`\`bash
cd Frontend

# Install dependencies
npm install

# Configure environment
echo "REACT_APP_API_URL=http://localhost:5001/api" > .env

# Start app
npm start
\`\`\`

Frontend runs on \`http://localhost:3000\`

## Documentation

- **[ONDEMAND_ANALYSIS.md](ONDEMAND_ANALYSIS.md)** - Check, paystub, bank statement, money order analysis
- **[REALTIME_BACKEND.md](REALTIME_BACKEND.md)** - Real-time fraud detection backend
- **[FRONTEND.md](FRONTEND.md)** - Frontend application guide

## Technologies

### Backend
- Flask, pandas, scikit-learn
- LangChain, OpenAI GPT-4
- Mindee API, matplotlib

### Frontend
- React, React Router
- Recharts, Axios, React Icons

## License

Proprietary

## Version

1.0.0
