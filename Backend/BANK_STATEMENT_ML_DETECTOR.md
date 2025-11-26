# Bank Statement ML-Based Fraud Detector

## Overview

The bank statement analysis system has been upgraded from a simple rule-based scorer to a comprehensive **ML-based fraud detection system** that analyzes transactions, balances, and document patterns to provide intelligent fraud risk assessments.

## Key Components

### 1. **BankStatementFraudDetector** (`bank_statement/fraud_detector.py`)

A specialized fraud detector that extracts meaningful features from bank statements and calculates dynamic fraud risk scores.

#### Features Extracted:

**Field Completeness:**
- Bank name presence
- Account holder presence
- Account number presence
- Statement period presence
- Opening/closing balance presence

**Transaction Analysis:**
- Transaction count
- Large transaction identification (>75th percentile)
- Unusual transaction dates
- Average transaction amount
- Transaction amount variance
- Transaction patterns

**Balance Analysis:**
- Opening and closing balance values
- Balance consistency verification
- Balance volatility calculation
- Credit/debit ratio analysis

**Content Analysis:**
- Suspicious keyword detection (NSF, overdraft, fraud alert, etc.)
- Fraud indicators presence
- Text quality assessment
- Unusual character counting

**Temporal Analysis:**
- Statement period duration
- Unusual period detection
- Activity intensity calculation

#### Fraud Score Calculation:

The detector calculates a 0-100 fraud risk score based on multiple factors:

```
Score Components:
- Missing critical fields: 0-25 points
- Transaction anomalies: 0-25 points
- Balance inconsistencies: 0-20 points
- Credit/debit ratio issues: 0-15 points
- Text quality issues: 0-10 points
- Suspicious keywords: 0-10 points
```

#### Risk Levels:

- **LOW**: Score < 25
- **MEDIUM**: Score 25-50
- **HIGH**: Score 50-75
- **CRITICAL**: Score > 75

### 2. **BankStatementFraudAnalysisAgent** (`langchain_agent/bank_statement_agent.py`)

Optional GPT-4 powered agent for deeper intelligent analysis (requires OpenAI API key).

**Features:**
- Context-aware analysis using GPT-4
- Integration with ML risk scores
- Intelligent recommendations with confidence levels
- Graceful fallback to rule-based analysis when unavailable

### 3. **API Integration** (`api_server.py`)

The `/api/bank-statement/analyze` endpoint now:

1. Extracts bank statement data using Mindee OCR
2. Runs ML-based fraud detection
3. Optionally uses GPT-4 for intelligent analysis
4. Returns comprehensive risk assessment with:
   - Fraud risk score
   - Risk factors
   - Recommendations
   - Confidence levels

## Results Comparison

### Before (Rule-Based Only):
```
All bank statements returned:
- Same base fraud risk score (0.25)
- Limited risk factors (only 5 simple checks)
- Generic recommendations
- Low differentiation between different bank statements
```

### After (ML-Based):
```
Bank statements now return:
- Dynamic fraud risk scores (0-100) based on actual patterns
- Detailed risk factors specific to each document
- Comprehensive transaction pattern analysis
- Balance consistency verification
- Activity intensity measurement
- Confidence scores adjusted based on data quality
```

## Example Analysis Output

```json
{
  "fraud_risk_score": 42,
  "risk_level": "MEDIUM",
  "model_confidence": 0.85,
  "risk_factors": [
    "Unusual transaction dates detected (3)",
    "Unusually high credit/debit ratio (2.45)",
    "High proportion of large transactions (6)",
    "Unusual balance volatility"
  ],
  "prediction_type": "ml_based_detector",
  "ai_analysis": {
    "recommendation": "ESCALATE",
    "confidence": 75,
    "summary": "Medium fraud risk detected",
    "reasoning": "Transaction patterns suggest moderate risk with irregular activity"
  }
}
```

## Technical Details

### Dependencies:
- NumPy (for numerical calculations)
- Standard Python libraries (re, datetime, etc.)
- Optional: LangChain, OpenAI (for GPT-4 analysis)

### Scalability:
- Feature extraction: O(n) complexity where n = number of transactions
- All computations performed in-memory
- No external database calls required for ML scoring

### Accuracy Improvements:
The new system distinguishes between bank statements based on:
1. **Completeness**: Missing critical fields significantly increase risk
2. **Patterns**: Transaction patterns reveal suspicious activity
3. **Consistency**: Mathematical balance verification
4. **Activity**: Unusual transaction intensity flags anomalies
5. **Content**: Explicit fraud indicators and text quality

## Future Enhancements

1. **Trained ML Models**: Integrate with scikit-learn models trained on historical fraud data
2. **Customer Profiling**: Compare statements against customer history
3. **Behavioral Analysis**: Track changes in transaction patterns over time
4. **Network Analysis**: Identify suspicious networks of accounts
5. **Anomaly Detection**: Unsupervised learning for new fraud patterns

## Usage

### Basic Analysis:
```python
from bank_statement.fraud_detector import BankStatementFraudDetector

detector = BankStatementFraudDetector()
features = detector.extract_features(bank_data)
score = detector.calculate_fraud_score(features)
risk_factors = detector.identify_risk_factors(features, score)
risk_level = detector.get_risk_level(score)
```

### With API:
```bash
curl -X POST http://localhost:5001/api/bank-statement/analyze \
  -F "file=@statement.pdf"
```

## Configuration

The detector uses sensible defaults and doesn't require configuration. However, all thresholds can be adjusted:

- Large transaction percentile: 75th (hardcoded, changeable)
- Text quality thresholds: 0.7 (adjustable)
- Activity intensity thresholds: customizable
- Keyword lists: extensible

## Troubleshooting

**All statements getting same score:**
- Check that feature extraction is working: Enable debug logging
- Verify transaction data is being parsed correctly
- Check balance consistency calculation

**Missing risk factors:**
- Ensure raw_text is provided for keyword detection
- Verify transaction data includes amount_value field
- Check date formats are recognized

**Low confidence scores:**
- Add more complete data (bank name, account number, etc.)
- Ensure sufficient transaction count (>3 recommended)
- Check statement period is within normal range (25-35 days)
