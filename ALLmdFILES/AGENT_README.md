# Real-Time Transaction Analysis LangChain Agent

## Overview

This module provides an AI-powered LangChain agent for comprehensive real-time transaction fraud analysis. The agent leverages OpenAI's GPT-4 to provide detailed insights, explanations, and recommendations.

## Features

The agent provides the following analysis capabilities:

### 1. **Top 3 Transactions Analysis**
- Identifies the most suspicious fraudulent transactions
- Provides detailed explanations for why each transaction was flagged
- Includes fraud probability scores, merchant information, and risk indicators

### 2. **Key Features in CSV**
- Analyzes the dataset structure and identifies important features
- Evaluates data quality and completeness
- Highlights features most relevant for fraud detection

### 3. **Detailed Insights**
- Comprehensive analysis of fraud trends and patterns
- Risk assessment and financial impact analysis
- Comparison to industry standards
- Identification of unusual patterns in amounts, categories, or timing

### 4. **Fraud Patterns Detected**
- Explains specific fraud patterns found in the data:
  - High-value transaction patterns
  - Time-based patterns (night-time, weekend fraud)
  - Category concentration patterns
- Provides context and significance for each pattern
- Suggests prevention strategies

### 5. **Plot Explanations**
- Generates detailed explanations for visualizations
- Highlights key insights and fraud indicators
- Provides business impact analysis

### 6. **Actionable Recommendations**
- Immediate actions (next 24-48 hours)
- Short-term measures (1-2 weeks)
- Long-term strategies (1-3 months)
- Monitoring KPIs and alert thresholds

## Architecture

### Components

1. **RealTimeAnalysisAgent** (`realtime_agent.py`)
   - Main agent class that interfaces with OpenAI GPT-4
   - Generates insights, patterns, and recommendations
   - Handles fallback to rule-based analysis if LLM is unavailable

2. **TransactionAnalysisTools** (`agent_tools.py`)
   - Provides LangChain-compatible tools for data access
   - Tools include:
     - `get_top_fraudulent_transactions`: Top fraud cases
     - `get_transaction_statistics`: Overall statistics
     - `get_detected_fraud_patterns`: Pattern analysis
     - `get_csv_features_info`: Dataset structure
     - `get_time_based_analysis`: Temporal patterns
     - `get_category_based_analysis`: Category distributions

3. **Agent Prompts** (`agent_prompts.py`)
   - Specialized prompts for different analysis types
   - Includes system prompts, analysis templates, and guidelines

4. **AgentAnalysisService** (`agent_endpoint.py`)
   - Service layer for generating comprehensive analysis
   - Orchestrates different analysis components
   - Provides API-friendly interface

## Usage

### Basic Usage

```python
from real_time import get_agent_service

# Get agent service (singleton)
agent_service = get_agent_service()

# Generate comprehensive analysis
result = agent_service.generate_comprehensive_analysis(analysis_result)

# Access different components
top_transactions = result['agent_analysis']['top_transactions']
csv_features = result['agent_analysis']['csv_features']
detailed_insights = result['agent_analysis']['detailed_insights']
fraud_patterns = result['agent_analysis']['fraud_patterns']
recommendations = result['agent_analysis']['recommendations']
```

### API Endpoint

**Endpoint:** `POST /api/real-time/agent-analysis`

**Request Body:**
```json
{
  "analysis_result": {
    "csv_info": {...},
    "fraud_detection": {...},
    "transactions": [...],
    "insights": {...}
  }
}
```

**Response:**
```json
{
  "success": true,
  "agent_analysis": {
    "top_transactions": {
      "count": 3,
      "transactions": [
        {
          "rank": 1,
          "amount": 5000.00,
          "fraud_probability": 0.95,
          "merchant": "Unknown Merchant",
          "category": "gambling",
          "reason": "ML Fraud Detection (95% confidence) | High transaction-to-balance ratio"
        }
      ]
    },
    "csv_features": {
      "total_columns": 10,
      "key_features": [...]
    },
    "detailed_insights": "Comprehensive AI-generated analysis...",
    "fraud_patterns": "Pattern explanations...",
    "recommendations": [
      "🚨 CRITICAL: Immediate security review required...",
      "🔒 Implement additional transaction verification..."
    ],
    "analysis_type": "llm",
    "model_used": "gpt-4"
  }
}
```

## Configuration

### Environment Variables

```bash
# OpenAI API Key (required for LLM analysis)
OPENAI_API_KEY=your_openai_api_key_here
```

### Model Selection

By default, the agent uses GPT-4. You can specify a different model:

```python
from real_time.realtime_agent import RealTimeAnalysisAgent

agent = RealTimeAnalysisAgent(
    api_key='your_api_key',
    model='gpt-3.5-turbo'  # or 'gpt-4', 'gpt-4-turbo', etc.
)
```

## Fallback Behavior

If OpenAI API is unavailable or the API key is not configured, the agent automatically falls back to rule-based analysis. This ensures the system continues to function even without LLM capabilities.

### Fallback Features:
- Basic fraud pattern detection
- Rule-based recommendations
- Statistical insights
- All core functionality remains available

## Dependencies

```bash
# Install required packages
pip install langchain langchain-openai openai python-dotenv pandas numpy
```

## Tools Available to the Agent

The agent has access to 6 specialized tools:

1. **get_top_fraudulent_transactions**: Retrieve top fraud cases with details
2. **get_transaction_statistics**: Overall dataset statistics
3. **get_detected_fraud_patterns**: Pattern analysis (high-value, time-based, category)
4. **get_csv_features_info**: Dataset structure and data quality
5. **get_time_based_analysis**: Temporal fraud patterns
6. **get_category_based_analysis**: Category-wise fraud distribution

## Example Workflow

```python
# 1. Process CSV file
csv_result = process_transaction_csv('transactions.csv')

# 2. Detect fraud
fraud_result = detect_fraud_in_transactions(
    csv_result['transactions'],
    auto_train=True
)

# 3. Generate insights
insights_result = generate_insights(fraud_result)

# 4. Combine results
analysis_result = {
    'csv_info': csv_result,
    'fraud_detection': fraud_result,
    'transactions': fraud_result['transactions'],
    'insights': insights_result
}

# 5. Generate AI analysis
agent_service = get_agent_service()
agent_analysis = agent_service.generate_comprehensive_analysis(analysis_result)

# 6. Access results
print(agent_analysis['agent_analysis']['detailed_insights'])
print(agent_analysis['agent_analysis']['recommendations'])
```

## Performance Considerations

- **LLM calls**: The agent makes 2-3 LLM calls per comprehensive analysis
- **Average response time**: 3-8 seconds (depending on dataset size and OpenAI API latency)
- **Caching**: Consider implementing caching for repeated analyses of the same dataset
- **Cost**: Using GPT-4 costs approximately $0.03-0.10 per analysis depending on dataset size

## Error Handling

The agent includes comprehensive error handling:
- Graceful fallback if LLM is unavailable
- Detailed error messages for debugging
- Logging at each step of the analysis process

## Future Enhancements

Planned features:
- [ ] Memory/context persistence across analyses
- [ ] Multi-language support
- [ ] Custom tool integration
- [ ] Streaming responses for real-time feedback
- [ ] Batch analysis capabilities
- [ ] Integration with vector databases for historical pattern matching

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Ensure OpenAI API key is properly configured
3. Verify all dependencies are installed
4. Review the fallback analysis if LLM is unavailable

## License

This module is part of the XFORIA DAD system.
