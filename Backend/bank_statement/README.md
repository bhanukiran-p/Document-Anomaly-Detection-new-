# Bank Statement Analysis Module

Complete self-contained module for bank statement fraud detection and analysis.

## Structure

```
bank_statement/
├── __init__.py
├── bank_statement_extractor.py      # Main orchestrator
├── normalization/                   # Normalization layer
│   ├── __init__.py
│   ├── bank_statement_schema.py    # NormalizedBankStatement schema
│   ├── bank_statement_base_normalizer.py
│   ├── bank_of_america.py
│   ├── chase.py
│   └── bank_statement_normalizer_factory.py
├── ml/                              # ML fraud detection
│   ├── __init__.py
│   ├── bank_statement_feature_extractor.py
│   └── bank_statement_fraud_detector.py
├── ai/                              # AI analysis
│   ├── __init__.py
│   ├── bank_statement_fraud_analysis_agent.py
│   ├── bank_statement_prompts.py
│   └── bank_statement_tools.py
├── database/                        # Database storage
│   ├── __init__.py
│   └── bank_statement_customer_storage.py
└── utils/                           # Utilities
    ├── __init__.py
    └── bank_statement_fraud_indicators.py
```

## Mindee Fields Extracted

Based on Mindee Data Schema (17 fields):

1. **Bank Name** (Text)
2. **Account Type** (Text)
3. **Currency** (Text)
4. **Account Holder Names** (Array)
5. **Account Number** (Text)
6. **Statement Period Start Date** (Date)
7. **Statement Period End Date** (Date)
8. **Statement Date** (Date)
9. **Beginning Balance** (Number)
10. **Ending Balance** (Number)
11. **Total Credits** (Number)
12. **Total Debits** (Number)
13. **List of Transactions** (Nested object, Array)
    - Date (Date)
    - Description (Text)
    - Amount (Number)
14. **Bank Address** (Nested object)
    - Address (Text)
    - Street (Text)
    - City (Text)
    - State (Text)
    - Postal Code (Text)
    - Country (Text)

## Flow

1. **Mindee Extraction** → Extract all 17 fields from bank statement
2. **Normalization** → Standardize to NormalizedBankStatement schema
3. **ML Fraud Detection** → Calculate fraud risk score
4. **AI Analysis** → Intelligent decision-making with LangChain + GPT-4
5. **Database Storage** → Store results and update customer history
6. **Frontend Display** → Show analysis results

## No Dependencies

This module is completely self-contained and does NOT reuse logic from:
- Money Order analysis
- Check analysis
- Paystub analysis

All components are bank statement-specific.

