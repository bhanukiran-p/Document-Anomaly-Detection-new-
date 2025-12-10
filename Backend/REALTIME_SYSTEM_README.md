# Real-Time Fraud Detection System - Technical Documentation

## Overview

The Real-Time Fraud Detection System is an AI-powered transaction analysis platform that detects fraudulent transactions in real-time using machine learning and provides actionable fraud prevention recommendations.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│                  RealTimeAnalysis.jsx                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ POST /api/real-time/analyze
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Server (Flask)                           │
│                    api_server.py                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Real-Time Processing Pipeline                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ CSV Processor│─▶│Fraud Detector│─▶│  AI Agent    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure and Connections

### Core Files

```
Backend/real_time/
├── api_server.py                 # Main API endpoint
├── csv_processor.py              # CSV parsing and validation
├── fraud_detector.py             # ML-based fraud detection
├── realtime_agent.py             # OpenAI/LangChain agent
├── agent_endpoint.py             # Agent orchestration
├── agent_tools.py                # Analysis tools for agent
├── agent_prompts.py              # LLM prompt templates
├── fraud_recommendations.py      # Fraud prevention strategies
└── database.py                   # Database operations
```

---

## Detailed File Descriptions

### 1. `api_server.py` - Main API Endpoint

**Purpose**: Flask API server that handles real-time transaction analysis requests

**Key Functions**:
- `analyze_real_time()`: Main endpoint for CSV file upload and analysis
- Handles file upload, processing, fraud detection, and AI analysis

**API Endpoint**:
```python
POST /api/real-time/analyze
Content-Type: multipart/form-data
Body: file=<csv_file>
```

**Response Structure**:
```json
{
  "success": true,
  "transactions": [...],
  "fraud_detection": {
    "fraud_count": 150,
    "fraud_percentage": 15.5,
    "fraud_reason_breakdown": [...]
  },
  "agent_analysis": {
    "top_transactions": [...],
    "detailed_insights": "...",
    "fraud_patterns": "...",
    "pattern_recommendations": [...]
  },
  "date_range": {
    "start": "2024-06-05T18:43:00",
    "end": "2024-07-11T16:01:00"
  }
}
```

**Connections**:
- Calls `csv_processor.process_csv()` → CSV parsing
- Calls `fraud_detector.detect_fraud()` → Fraud detection
- Calls `agent_endpoint.generate_comprehensive_analysis()` → AI analysis

---

### 2. `csv_processor.py` - CSV Data Processing

**Purpose**: Parses, validates, and structures CSV transaction data

**Key Functions**:

```python
def process_csv(file_path: str) -> Dict[str, Any]:
    """
    Process uploaded CSV file

    Returns:
        - transactions: List of transaction records
        - total_count: Number of transactions
        - date_range: {start, end} timestamps
        - columns: Column metadata
    """
```

**Helper Functions**:
- `_get_date_range(df)`: Extracts min/max timestamps from entire dataset
- `_get_column_info(df)`: Analyzes column types and statistics
- `_calculate_summary(df)`: Calculates transaction summaries

**Tools Used**:
- `pandas`: DataFrame operations
- `numpy`: Numerical computations

**Connections**:
- Called by `api_server.py`
- Output fed to `fraud_detector.py`

---

### 3. `fraud_detector.py` - ML Fraud Detection Engine

**Purpose**: Detects fraudulent transactions using machine learning algorithms

**Key Functions**:

```python
def detect_fraud(transactions: List[Dict]) -> Dict[str, Any]:
    """
    Detect fraud using ML models

    Returns:
        - fraud_count: Number of fraudulent transactions
        - fraud_percentage: Percentage of fraud
        - fraud_reason_breakdown: Top fraud patterns
        - total_fraud_amount: Total fraudulent amount
    """
```

**Fraud Patterns Detected** (15 types):

1. **Authentication & Account Security**
   - Suspicious login
   - Account takeover
   - Unusual device

2. **Geographic & Location**
   - Unusual location
   - Cross-border anomaly

3. **Transaction Velocity**
   - Velocity abuse
   - Transaction burst
   - New payee spike

4. **Amount & Merchant**
   - Unusual amount
   - High-risk merchant
   - Round-dollar pattern

5. **Card Fraud**
   - Card-not-present risk

6. **Money Laundering**
   - Money mule pattern
   - Structuring/smurfing
   - Night-time activity

**ML Algorithms Used**:
- Isolation Forest (anomaly detection)
- Random Forest Classifier
- Statistical analysis (Z-scores, velocity checks)

**Tools Used**:
- `scikit-learn`: ML models
- `pandas`: Data manipulation
- `numpy`: Statistical calculations

**Connections**:
- Called by `api_server.py`
- Output sent to `agent_endpoint.py`

---

### 4. `realtime_agent.py` - OpenAI LangChain Agent

**Purpose**: AI-powered analysis agent using OpenAI GPT models

**Key Functions**:

```python
def generate_comprehensive_insights(analysis_result: Dict) -> Dict:
    """Generate AI insights about fraud patterns"""

def explain_fraud_patterns(analysis_result: Dict) -> Dict:
    """Explain detected fraud patterns in detail"""

def generate_recommendations(analysis_result: Dict) -> List[Dict]:
    """Generate structured fraud prevention recommendations"""
```

**AI Models Used**:
- Default: `gpt-4o-mini` (fast, cost-effective)
- Alternative: `gpt-3.5-turbo`, `gpt-4`

**LangChain Components**:
- `ChatOpenAI`: OpenAI model interface
- `ChatPromptTemplate`: Prompt management
- `SystemMessagePromptTemplate`: System context
- `HumanMessagePromptTemplate`: User queries

**Tools Used**:
- `langchain-openai`: OpenAI integration
- `langchain-core`: Core LangChain components
- `json`, `re`: Response parsing

**Connections**:
- Called by `agent_endpoint.py`
- Uses prompts from `agent_prompts.py`
- Uses tools from `agent_tools.py`

---

### 5. `agent_endpoint.py` - Agent Orchestration Layer

**Purpose**: Orchestrates the AI agent analysis workflow

**Key Class**:

```python
class AgentAnalysisService:
    def __init__(self, api_key: Optional[str] = None):
        self.agent = RealTimeAnalysisAgent(api_key=api_key)

    def generate_comprehensive_analysis(analysis_result: Dict) -> Dict:
        """
        Orchestrates complete AI analysis:
        1. Top transactions analysis
        2. CSV features analysis
        3. Detailed insights (from LLM)
        4. Fraud patterns explanation (from LLM)
        5. Prevention recommendations (from LLM)
        """
```

**Functions**:
- `_analyze_top_transactions()`: Extract top 3 fraudulent transactions
- `_analyze_csv_features()`: Analyze dataset features
- `get_agent_service()`: Singleton service instance

**Connections**:
- Called by `api_server.py`
- Uses `realtime_agent.py` for AI operations
- Uses `agent_tools.py` for data analysis

---

### 6. `agent_tools.py` - Analysis Tools

**Purpose**: Provides data analysis tools for the AI agent

**Key Class**:

```python
class TransactionAnalysisTools:
    def __init__(self, analysis_result: Dict):
        self.analysis_result = analysis_result

    def get_top_transactions(limit=3, fraud_only=True) -> List[Dict]:
        """Get top fraudulent transactions"""

    def get_transaction_statistics() -> Dict:
        """Get overall statistics"""

    def get_fraud_patterns() -> Dict:
        """Get fraud pattern breakdown"""

    def get_csv_features() -> Dict:
        """Get CSV column information"""
```

**Connections**:
- Used by `agent_endpoint.py`
- Processes data from `fraud_detector.py`

---

### 7. `agent_prompts.py` - LLM Prompt Templates

**Purpose**: Contains all LLM prompt templates for AI analysis

**Key Prompts**:

```python
SYSTEM_PROMPT = """You are an expert fraud analyst..."""

INSIGHTS_PROMPT = """Analyze this real-time transaction dataset..."""

FRAUD_PATTERNS_PROMPT = """Analyze the fraud patterns detected..."""

RECOMMENDATIONS_PROMPT = """
Based on the fraud analysis below, generate structured fraud prevention
recommendations for the TOP 3 most significant fraud patterns detected...

Return JSON array with structure:
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "pattern_type": "Suspicious login",
  "immediate_actions": [...],
  "prevention_steps": [...],
  "monitoring": "..."
}
"""
```

**Connections**:
- Used by `realtime_agent.py`
- Defines how the LLM generates responses

---

### 8. `fraud_recommendations.py` - Fraud Prevention Strategies

**Purpose**: Hardcoded fraud prevention strategies (currently not used - replaced by LLM)

**Note**: This file contains comprehensive prevention strategies for all 15 fraud types but is currently bypassed in favor of LLM-generated recommendations.

**Key Class**:

```python
class FraudRecommendationEngine:
    FRAUD_PREVENTION_STRATEGIES = {
        'Suspicious login': {
            'severity': 'HIGH',
            'category': 'Authentication Security',
            'prevention_steps': [...],
            'immediate_actions': [...],
            'monitoring': '...'
        },
        # ... 14 more fraud types
    }
```

**Connections**:
- Previously called by `agent_endpoint.py`
- Now replaced by LLM recommendations from `realtime_agent.py`

---

### 9. `database.py` - Database Operations

**Purpose**: Saves analyzed transactions to MySQL database

**Key Functions**:

```python
def save_to_database(transactions: List[Dict], table_name: str) -> Dict:
    """
    Save transactions to database

    Table: analyzed_real_time_trn
    """
```

**Database Schema**:
```sql
CREATE TABLE analyzed_real_time_trn (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(255),
    customer_id VARCHAR(255),
    amount DECIMAL(10,2),
    merchant VARCHAR(255),
    category VARCHAR(255),
    timestamp DATETIME,
    is_fraud TINYINT,
    fraud_probability DECIMAL(5,4),
    fraud_reason VARCHAR(500),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Tools Used**:
- `mysql-connector-python`: MySQL database connector

**Connections**:
- Called by `api_server.py` after analysis

---

## Data Flow Diagram

```
1. User uploads CSV file
   ↓
2. api_server.py receives file
   ↓
3. csv_processor.py parses CSV → Returns transactions + metadata
   ↓
4. fraud_detector.py analyzes transactions → Returns fraud detection results
   ↓
5. agent_endpoint.py orchestrates AI analysis
   ├─→ agent_tools.py extracts top transactions
   └─→ realtime_agent.py calls OpenAI
       ├─→ Uses agent_prompts.py templates
       ├─→ Generates insights
       ├─→ Explains fraud patterns
       └─→ Generates recommendations (JSON format)
   ↓
6. database.py saves results to MySQL
   ↓
7. api_server.py returns complete analysis to frontend
```

---

## Key Technologies & Tools

### Python Libraries

**Data Processing**:
- `pandas`: DataFrame operations, CSV parsing
- `numpy`: Numerical computations, statistical analysis

**Machine Learning**:
- `scikit-learn`: Isolation Forest, Random Forest, StandardScaler
- Feature engineering and anomaly detection

**AI/LLM**:
- `langchain-openai`: OpenAI GPT integration
- `langchain-core`: LangChain framework components
- `openai`: Direct OpenAI API access

**Web Framework**:
- `Flask`: REST API server
- `Flask-CORS`: Cross-origin resource sharing

**Database**:
- `mysql-connector-python`: MySQL database operations

**Utilities**:
- `python-dotenv`: Environment variable management
- `logging`: Application logging
- `json`, `re`: Data parsing

---

## Environment Variables

Required in `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini

# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fraud_detection
DB_PORT=3306
```

---

## API Request/Response Examples

### Request

```bash
curl -X POST http://localhost:5001/api/real-time/analyze \
  -F "file=@transactions.csv"
```

### Response

```json
{
  "success": true,
  "transactions": [
    {
      "transaction_id": "TXN001",
      "amount": 5000.0,
      "is_fraud": 1,
      "fraud_probability": 0.95,
      "fraud_reason": "Suspicious login"
    }
  ],
  "fraud_detection": {
    "fraud_count": 150,
    "fraud_percentage": 15.5,
    "fraud_reason_breakdown": [
      {
        "type": "Suspicious login",
        "count": 45,
        "percentage": 30.0,
        "total_amount": 25000.0
      }
    ]
  },
  "agent_analysis": {
    "detailed_insights": "AI-generated insights...",
    "fraud_patterns": "AI-generated pattern analysis...",
    "pattern_recommendations": [
      {
        "severity": "HIGH",
        "pattern_type": "Suspicious login",
        "title": "Suspicious login Detected",
        "description": "Detected 45 cases...",
        "immediate_actions": [
          "Review recent login history",
          "Force password reset"
        ],
        "prevention_steps": [
          "Implement MFA",
          "Enable device fingerprinting"
        ],
        "monitoring": "Track login attempts..."
      }
    ]
  },
  "date_range": {
    "start": "2024-06-05T18:43:00",
    "end": "2024-07-11T16:01:00"
  },
  "database_status": "saved"
}
```

---

## Fraud Detection Logic

### 1. Feature Engineering

```python
# Extract features from transactions
features = [
    'amount',
    'hour_of_day',
    'day_of_week',
    'transaction_velocity',
    'amount_deviation',
    'merchant_risk_score',
    'location_distance'
]
```

### 2. Anomaly Detection

```python
# Isolation Forest for outlier detection
model = IsolationForest(contamination=0.1, random_state=42)
anomaly_scores = model.fit_predict(features)
```

### 3. Fraud Reason Classification

```python
# Rule-based classification
if anomaly_score < -0.5:
    if login_unusual:
        fraud_reason = "Suspicious login"
    elif amount > 3 * std_dev:
        fraud_reason = "Unusual amount"
    elif is_cross_border:
        fraud_reason = "Cross-border anomaly"
    # ... 12 more patterns
```

---

## AI Recommendation System

### How LLM Generates Recommendations

1. **Context Building**:
   ```python
   context = f"""
   Fraud Overview:
   - Fraud Rate: {fraud_percentage}%
   - Fraudulent Transactions: {fraud_count}
   - Fraud Pattern Breakdown:
     - Suspicious login: 45 cases (30% of fraud)
     - Unusual amount: 35 cases (23% of fraud)
   """
   ```

2. **LLM Prompt**:
   - Uses `RECOMMENDATIONS_PROMPT` template
   - Instructs LLM to return JSON array with 3 recommendations
   - Specifies exact structure with severity, actions, prevention steps

3. **Response Parsing**:
   ```python
   # Extract JSON from LLM response
   json_match = re.search(r'\[[\s\S]*\]', response_text)
   recommendations = json.loads(json_match.group(0))
   ```

4. **Validation**:
   - Ensures proper JSON structure
   - Validates required fields
   - Limits to top 3 recommendations

---

## Performance Metrics

- **CSV Processing**: < 1 second for 5,000 rows
- **Fraud Detection**: < 2 seconds for 5,000 transactions
- **AI Analysis**: 10-15 seconds (OpenAI API call)
- **Total End-to-End**: 12-18 seconds

---

## Error Handling

### Common Errors

1. **CSV Format Invalid**
   ```json
   {"success": false, "error": "Invalid CSV format"}
   ```

2. **OpenAI API Error**
   ```json
   {
     "success": false,
     "error": "AI Analysis unavailable: API key invalid"
   }
   ```

3. **Database Error**
   ```json
   {
     "success": true,
     "database_status": "error",
     "database_error": "Connection failed"
   }
   ```

---

## Testing

### Run Unit Tests

```bash
cd Backend
python -m pytest real_time/
```

### Test Recommendation Source

```bash
python test_recommendation_source.py
```

Expected output:
```
✓ LLM is AVAILABLE (gpt-4o-mini)
✓ Generated 3 recommendations
✓ Recommendations are STRUCTURED OBJECTS (FROM AI)
CONCLUSION: ✓ RECOMMENDATIONS ARE FROM OPENAI/LLM
```

---

## Deployment Checklist

- [ ] Set `OPENAI_API_KEY` in environment
- [ ] Configure MySQL database connection
- [ ] Install all dependencies: `pip install -r requirements.txt`
- [ ] Test CSV upload functionality
- [ ] Verify AI recommendations are working
- [ ] Check database saves are successful
- [ ] Monitor API response times
- [ ] Set up logging and error tracking

---

## Troubleshooting

### Issue: No AI recommendations generated

**Solution**: Check OpenAI API key and model configuration

```bash
# Verify API key
echo $OPENAI_API_KEY

# Check logs
tail -f logs/api_server.log
```

### Issue: Slow response times

**Solution**: Consider upgrading to faster OpenAI model or caching

```python
# In .env
AI_MODEL=gpt-4o-mini  # Fastest option
```

### Issue: Database connection failed

**Solution**: Verify MySQL credentials and connection

```bash
mysql -u root -p -h localhost -e "SHOW DATABASES;"
```

---

## Future Enhancements

1. **Model Improvements**
   - Train custom ML models on historical data
   - Implement ensemble methods

2. **Real-Time Streaming**
   - Add support for live transaction streams
   - WebSocket integration

3. **Advanced Analytics**
   - Network analysis for money laundering detection
   - Time-series forecasting

4. **Performance Optimization**
   - Cache frequent LLM responses
   - Async processing for large datasets

---

## Support & Documentation

For questions or issues:
- Review this documentation
- Check code comments in each file
- Examine log files in `logs/` directory
- Test with sample data in `sample_data/`

---

**Last Updated**: December 2024
**Version**: 2.0
**Author**: DAD Fraud Detection Team
