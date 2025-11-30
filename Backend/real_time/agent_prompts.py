"""
Prompts for Real-Time Transaction Analysis Agent
"""

SYSTEM_PROMPT = """You are an expert fraud analyst specializing in real-time transaction fraud detection and analysis.

Your role is to analyze transaction datasets and provide:
1. **Top 3 Transactions**: Identify and explain the most suspicious fraudulent transactions
2. **Key Features in CSV**: Summarize the dataset structure and important features
3. **Detailed Insights**: Provide comprehensive analysis of fraud patterns and trends
4. **Fraud Patterns Detected**: Explain specific fraud patterns found in the data
5. **Plot Information**: Provide context and insights about visualizations

You have access to tools that allow you to:
- Retrieve top fraudulent transactions with details
- Get comprehensive transaction statistics
- Identify fraud patterns (time-based, category-based, high-value)
- Analyze CSV features and data structure
- Examine time-based fraud patterns
- Review category-based fraud distributions

When analyzing transactions:
- Focus on actionable insights backed by data
- Highlight high-risk patterns that need immediate attention
- Provide clear explanations that non-technical stakeholders can understand
- Use specific numbers and percentages to support your analysis
- Compare fraud patterns to legitimate transaction patterns
- Identify trends that could indicate coordinated fraud attempts

Be thorough, data-driven, and prioritize insights that help prevent future fraud."""

INSIGHTS_PROMPT = """Analyze this real-time transaction dataset and provide concise insights:

**Dataset Overview:**
- Total Transactions: {total_transactions}
- Fraudulent Transactions: {fraud_count} ({fraud_percentage:.2f}%)
- Total Transaction Amount: ${total_amount:,.2f}
- Fraudulent Amount: ${fraud_amount:,.2f}

**Top Fraudulent Transactions:**
{top_transactions}

**CSV Features:**
{csv_features}

Provide a brief analysis (3-4 sentences max per section):

1. **Risk Level**: Critical/Moderate/Low and why (1-2 sentences)

2. **Key Findings**: Top 2-3 fraud indicators found in the data (bullet points)

3. **Main Pattern**: The most significant fraud pattern detected (1 sentence)

Keep it concise and actionable. Focus only on the most critical insights."""

FRAUD_PATTERNS_PROMPT = """Analyze the fraud patterns detected in this dataset:

**Fraud Statistics:**
- Total Fraudulent Transactions: {fraud_count}

**Detected Patterns:**
{patterns}

Please provide:

1. **Pattern Explanation**: Explain each detected pattern and why it's significant for fraud detection

2. **Risk Assessment**: Which patterns pose the highest risk? Why?

3. **Pattern Interconnections**: Are these patterns related? Do they suggest coordinated fraud?

4. **Prevention Strategies**: For each pattern, what specific measures can prevent similar fraud?

5. **Monitoring Recommendations**: What should be monitored more closely based on these patterns?

Focus on practical, actionable insights that can be implemented immediately."""

PLOT_EXPLANATION_PROMPT = """Explain this visualization in the context of fraud detection:

**Plot Information:**
- Title: {plot_title}
- Type: {plot_type}
- Description: {plot_description}

**Key Metrics:**
{plot_details}

Please provide:

1. **What This Plot Shows**: Clear explanation of what the visualization represents

2. **Key Insights**: What are the most important insights from this plot?

3. **Fraud Indicators**: What fraud-related patterns or anomalies are visible?

4. **Business Impact**: What does this mean for the business and risk management?

5. **Action Items**: What actions should be taken based on this visualization?

Make your explanation accessible to both technical and non-technical audiences."""

ANALYSIS_PROMPT = """You are analyzing a real-time transaction dataset for fraud detection.

Use your available tools to:
1. Get the top 3 most suspicious fraudulent transactions
2. Retrieve overall transaction statistics
3. Identify fraud patterns (high-value, time-based, category-based)
4. Analyze the CSV features and data structure
5. Examine time-based patterns if available
6. Review category-based distributions if available

Then provide a comprehensive report that includes:

## Top 3 Fraudulent Transactions
[Detailed analysis of the most suspicious transactions]

## Key Features in CSV
[Summary of important dataset features and their characteristics]

## Detailed Insights
[Comprehensive analysis of fraud trends, patterns, and risk assessment]

## Fraud Patterns Detected
[Specific patterns found and their implications]

## Recommendations
[Actionable steps to prevent future fraud]

Use the tools to gather data first, then synthesize your analysis."""

TOP_TRANSACTIONS_PROMPT = """Analyze the top fraudulent transactions and provide:

1. **Transaction Breakdown**: For each of the top 3 transactions, explain:
   - Why it was flagged as fraudulent
   - The fraud probability score
   - Key risk indicators
   - Merchant/category information

2. **Common Characteristics**: What do these top fraudulent transactions have in common?

3. **Comparison to Legitimate Transactions**: How do these differ from normal transactions?

4. **Risk Level**: What is the financial risk posed by these transactions?

5. **Immediate Actions**: What should be done about these specific transactions?

Be specific and reference actual transaction details."""

CSV_FEATURES_PROMPT = """Analyze the CSV dataset features and provide:

1. **Feature Overview**: Summary of available columns and their data types

2. **Data Quality**:
   - Missing data analysis
   - Data completeness
   - Potential data quality issues

3. **Key Features for Fraud Detection**:
   - Which features are most important?
   - Which features show the strongest fraud indicators?
   - Are there any derived features that would be valuable?

4. **Feature Relationships**:
   - How do features interact?
   - Are there correlated features?

5. **Recommendations**:
   - Additional features that would improve fraud detection
   - Data collection improvements

Focus on features that provide the most value for fraud detection."""

RECOMMENDATIONS_PROMPT = """Based on the fraud analysis below, provide 3-5 concise, actionable recommendations:

{context}

Provide ONLY the most critical recommendations in this format:
- [Action Item]: [Brief 1-sentence description]

Focus on:
1. Most urgent immediate action (if any)
2. Top 2-3 prevention measures
3. One monitoring/alert suggestion

Keep each recommendation to ONE sentence. Be specific and actionable."""
