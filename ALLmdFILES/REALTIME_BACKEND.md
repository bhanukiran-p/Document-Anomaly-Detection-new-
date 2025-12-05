# Real-Time Fraud Analysis Backend

Complete documentation for the real-time transaction fraud detection backend with GPT-4 powered AI analysis.

## Overview

The real-time analysis backend provides:
- CSV transaction data processing
- ML-based fraud detection
- GPT-4 powered AI insights and recommendations
- Statistical analysis and pattern detection
- Interactive visualizations

## Architecture

```
Backend/
├── real_time/
│   ├── csv_processor.py          # CSV file processing
│   ├── fraud_detector.py         # ML fraud detection
│   ├── insights_generator.py    # Statistical insights
│   ├── plot_generator.py        # Visualization generation
│   ├── realtime_agent.py        # GPT-4 LLM agent
│   ├── agent_tools.py           # LangChain tools
│   ├── agent_prompts.py         # GPT-4 prompts
│   └── agent_endpoint.py        # Agent service layer
└── api_server.py                # Main API server
```

## API Endpoint

### Analyze Transactions
- **Endpoint**: `POST /api/real-time/analyze`
- **Description**: Analyzes CSV transaction data for fraud detection
- **Request**: Multipart form data with CSV file
- **Response**: Complete analysis including fraud detection, insights, AI analysis, and plots

## CSV Format

Required columns (case-insensitive):
- `transaction_id` or `id`
- `amount` or `value`
- `merchant` or `store` or `vendor`
- `category` (optional)
- `timestamp` or `date` or `time`

Example CSV:
```csv
transaction_id,amount,merchant,category,timestamp
TXN001,150.00,Amazon,shopping,2024-01-15 14:30:00
TXN002,2500.00,Casino Royal,gambling,2024-01-15 02:15:00
TXN003,45.50,Starbucks,food,2024-01-15 08:00:00
```

## Features

### 1. Fraud Detection
- **ML Model**: Random Forest classifier
- **Features**: Amount, category, time patterns, merchant history
- **Output**: Fraud probability (0-1) and fraud flag per transaction

### 2. Statistical Insights
- Total transaction count and amounts
- Fraud rate and fraud amount percentages
- Top fraud cases with reasons
- Fraud patterns (high-value, night-time, category concentration)

### 3. GPT-4 AI Analysis

Powered by OpenAI GPT-4, provides:

#### Top Suspicious Transactions
- Detailed analysis of top 3 most fraudulent transactions
- Explanation of fraud indicators
- Risk assessment

#### Key Insights
- Natural language analysis of fraud trends
- Context-aware pattern identification
- Financial impact assessment

#### Fraud Patterns
- Deep explanation of detected patterns
- Risk prioritization
- Interconnection analysis

#### AI Recommendations
- Immediate action items (24-48 hours)
- Short-term measures (1-2 weeks)
- Long-term strategies (1-3 months)
- Monitoring KPIs and thresholds

### 4. Visualizations
- Transaction amount distribution
- Fraud vs legitimate comparison
- Time-based patterns
- Category analysis
- High-risk merchant identification

## Configuration

### Environment Variables

Required in `Backend/.env`:

```env
# OpenAI Configuration for GPT-4 AI Analysis
OPENAI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4

# Optional
SECRET_KEY=your-secret-key-for-flask
```

### Dependencies

Install required packages:

```bash
cd Backend
pip install -r requirements.txt
```

Key dependencies:
- `flask` - API server
- `pandas` - Data processing
- `scikit-learn` - ML models
- `matplotlib` - Visualizations
- `langchain` - LLM framework
- `langchain-openai` - OpenAI integration
- `openai` - OpenAI API client

## Usage

### 1. Start Backend Server

```bash
cd Backend
python api_server.py
```

Server runs on `http://localhost:5001`

You should see:
```
INFO:real_time.realtime_agent:LangChain loaded successfully - GPT-4 mode enabled
INFO:real_time.realtime_agent:Initialized LangChain agent with gpt-4 - GPT-4 mode active!
```

### 2. Upload CSV via Frontend

Navigate to Real-Time Analysis page: `/real-time-analysis`

1. Upload CSV file (drag & drop or click)
2. Click "Analyze Transactions"
3. View fraud detection results
4. Click "Show Insights & Plots" for AI analysis

### 3. API Response Structure

```json
{
  "success": true,
  "csv_info": {
    "total_count": 1000,
    "columns": [...],
    "file_name": "transactions.csv"
  },
  "fraud_detection": {
    "fraud_count": 45,
    "fraud_percentage": 4.5,
    "total_amount": 125000.00,
    "total_fraud_amount": 8500.00
  },
  "transactions": [
    {
      "transaction_id": "TXN001",
      "amount": 150.00,
      "is_fraud": 1,
      "fraud_probability": 0.89,
      "fraud_reason": "High-value unusual transaction"
    }
  ],
  "insights": {
    "top_fraud_cases": [...],
    "fraud_patterns": {...},
    "plots": [...]
  },
  "agent_analysis": {
    "top_transactions": {...},
    "detailed_insights": "GPT-4 generated insights...",
    "fraud_patterns": "GPT-4 pattern analysis...",
    "recommendations": [
      "Immediate action items...",
      "Enhanced monitoring suggestions..."
    ],
    "analysis_type": "llm",
    "model_used": "gpt-4"
  }
}
```

## GPT-4 AI Agent

### How It Works

1. **Data Collection**: Extracts transaction statistics and patterns
2. **Context Building**: Creates structured prompts with fraud data
3. **LLM Analysis**: GPT-4 analyzes data using specialized prompts
4. **Response Parsing**: Extracts insights and recommendations
5. **Fallback Mode**: Uses rule-based analysis if GPT-4 unavailable

### LangChain Tools

The agent has access to 6 specialized tools:

1. `get_top_transactions` - Retrieve most fraudulent transactions
2. `get_transaction_statistics` - Overall fraud statistics
3. `get_fraud_patterns` - Detected pattern information
4. `get_csv_features` - Dataset structure and features
5. `get_time_based_analysis` - Temporal fraud patterns
6. `get_category_based_analysis` - Category distributions

### Prompts

Specialized prompts for different analyses:
- `INSIGHTS_PROMPT` - Overall fraud insights
- `FRAUD_PATTERNS_PROMPT` - Pattern explanations
- `RECOMMENDATIONS_PROMPT` - Actionable recommendations
- `PLOT_EXPLANATION_PROMPT` - Visualization context

## Fraud Detection Logic

### Features Used
- Transaction amount (normalized)
- Merchant risk score
- Category risk score
- Time of day (hour)
- Day of week
- Amount percentile
- Historical merchant fraud rate

### Fraud Probability Thresholds
- **High Risk** (>0.7): Immediate review required
- **Medium Risk** (0.4-0.7): Enhanced monitoring
- **Low Risk** (<0.4): Standard monitoring

### Pattern Detection

#### High-Value Transactions
- Threshold: 95th percentile of amounts
- Indicates: Unusual large purchases

#### Night-Time Fraud
- Hours: 22:00 - 06:00
- Indicates: Off-hours suspicious activity

#### Category Concentration
- Threshold: >30% fraud in one category
- Indicates: Targeted fraud in specific merchants

## Performance

### Processing Times
- CSV Upload: <1s for files up to 10MB
- Fraud Detection: 2-5s for 1000 transactions
- GPT-4 Analysis: 5-10s per analysis
- Total: ~15-20s for complete analysis

### Costs
- GPT-4 API: ~$0.03-0.10 per analysis
- Depends on dataset size and complexity

## Error Handling

### Common Issues

#### "LangChain not installed"
**Solution**: Install LangChain dependencies
```bash
pip install langchain langchain-openai openai
```

#### "OpenAI API key not found"
**Solution**: Add to `Backend/.env`
```env
OPENAI_API_KEY=your_key_here
```

#### "Invalid CSV format"
**Solution**: Ensure required columns present (transaction_id, amount, merchant, timestamp)

#### "Fraud detection failed"
**Solution**: Check CSV has valid numeric amounts and dates

## Testing

### Test with Sample Data

```bash
curl -X POST http://localhost:5001/api/real-time/analyze \
  -F "file=@sample_transactions.csv"
```

### Verify GPT-4 Mode

Check server logs for:
```
INFO:real_time.realtime_agent:LangChain loaded successfully - GPT-4 mode enabled
```

## Production Considerations

1. **API Rate Limits**: OpenAI has rate limits on GPT-4
2. **Costs**: Monitor GPT-4 usage for cost control
3. **Caching**: Cache analysis for duplicate datasets
4. **Async Processing**: For large files, use background jobs
5. **Security**: Sanitize CSV inputs, validate file sizes
6. **Monitoring**: Log API errors and response times

## Troubleshooting

### GPT-4 Not Working
1. Check `OPENAI_API_KEY` in `.env`
2. Verify LangChain installed: `pip list | grep langchain`
3. Check server logs for errors
4. System falls back to rule-based if GPT-4 fails

### Slow Analysis
1. Large datasets take longer
2. GPT-4 API calls add 5-10s
3. Consider pagination for >10,000 transactions

### Memory Issues
1. Large CSV files can use significant memory
2. Process in chunks if memory errors occur
3. Recommended: <50MB CSV files

## Model Training

The fraud detection model is pre-trained but can be retrained:

```bash
cd Backend/real_time
python fraud_detector.py --train --data training_data.csv
```

See `TRAINING_INSTRUCTIONS.md` for details.
