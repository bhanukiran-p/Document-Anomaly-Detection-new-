
This document provides a complete guide to implementing the Checks Insights page with CSV upload, database integration, graphs, and analytics. Use this as a reference to replicate the functionality in other branches.
# Complete Documentation: Checks Insights Page Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Frontend Implementation](#frontend-implementation)
3. [Backend API Endpoints](#backend-api-endpoints)
4. [Database Setup](#database-setup)
5. [Data Processing Logic](#data-processing-logic)
6. [Graphs and Charts](#graphs-and-charts)
7. [CSV Format Requirements](#csv-format-requirements)
8. [Integration Steps](#integration-steps)

---

## Overview

The Checks Insights page provides:
- **CSV Upload**: Upload CSV files with check analysis data for bulk insights
- **Database Integration**: Connect directly to database to fetch and analyze checks
- **Visual Analytics**: Multiple charts showing risk distribution, recommendations, and bank analysis
- **Search & Filter**: Search by payer name and filter by date ranges
- **Real-time Metrics**: Summary cards showing totals, averages, and decision breakdowns

**Key Features:**
- Dual input modes (CSV upload or API/database connection)
- Date filtering (Last 30/60/90 days, Older)
- Search functionality by payer name
- Interactive charts using Recharts library
- Automatic data processing and visualization

---

## Frontend Implementation

### 1. Component Structure

**File:** `Frontend/src/components/CheckInsights.jsx`

**Key Dependencies:**
```javascript
import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { FaUpload, FaCog } from 'react-icons/fa';
```

**Required npm packages:**
```json
{
  "react-dropzone": "^14.2.3",
  "recharts": "^3.5.1",
  "react-icons": "^5.5.0"
}
```

### 2. Component State Management

```javascript
const [csvData, setCsvData] = useState(null);           // Processed chart data
const [loading, setLoading] = useState(false);          // CSV processing state
const [error, setError] = useState(null);               // Error messages
const [inputMode, setInputMode] = useState('upload');  // 'upload' or 'api'
const [checksList, setChecksList] = useState([]);      // Database checks list
const [loadingChecksList, setLoadingChecksList] = useState(false);
const [selectedCheckId, setSelectedCheckId] = useState(null);
const [searchQuery, setSearchQuery] = useState('');
const [dateFilter, setDateFilter] = useState(null);     // null, 'last_30', 'last_60', 'last_90', 'older'
const [totalRecords, setTotalRecords] = useState(0);
```

### 3. CSV Parsing Function

```javascript
const parseCSV = (text) => {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map(h => h.trim());
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Handle quoted CSV values
    const values = [];
    let current = '';
    let inQuotes = false;

    for (let j = 0; j < line.length; j++) {
      const char = line[j];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());

    const row = {};
    headers.forEach((header, idx) => {
      row[header] = values[idx] || '';
    });
    rows.push(row);
  }

  return rows;
};
```

### 4. Data Processing Function

This function transforms raw CSV rows or database records into chart-ready data:

```javascript
const processData = (rows) => {
  if (!rows.length) return null;

  // Helper to parse float values
  const parseFloat_ = (val) => {
    const num = parseFloat(val);
    return isNaN(num) ? 0 : num;
  };

  // 1. Fraud Risk Distribution (0-25%, 25-50%, 50-75%, 75-100%)
  const riskScores = rows.map(r => parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0));
  const riskScoresPercent = riskScores.map(s => s * 100);
  const riskDistribution = [
    { range: '0-25%', count: riskScoresPercent.filter(s => s < 25).length },
    { range: '25-50%', count: riskScoresPercent.filter(s => s >= 25 && s < 50).length },
    { range: '50-75%', count: riskScoresPercent.filter(s => s >= 50 && s < 75).length },
    { range: '75-100%', count: riskScoresPercent.filter(s => s >= 75).length },
  ];

  // 2. AI Recommendation Distribution (APPROVE/REJECT/ESCALATE)
  const recommendations = rows.map(r => (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
  const recommendationData = [
    { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
    { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
    { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
  ].filter(item => item.value > 0);

  // 3. Risk by Bank (Average risk score per bank)
  const bankRisks = {};
  rows.forEach(r => {
    const bank = r['BankName'] || r['bank_name'] || 'Unknown';
    if (!bankRisks[bank]) {
      bankRisks[bank] = { count: 0, totalRisk: 0 };
    }
    bankRisks[bank].count++;
    bankRisks[bank].totalRisk += parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
  });
  const riskByBankData = Object.entries(bankRisks)
    .map(([name, data]) => ({
      name,
      avgRisk: ((data.totalRisk / data.count) * 100).toFixed(1),
      count: data.count
    }))
    .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
    .slice(0, 10); // Top 10 banks

  // 4. Summary Metrics
  const totalChecks = rows.length;
  const avgRiskScore = (riskScores.reduce((a, b) => a + b, 0) / riskScores.length * 100).toFixed(1);
  const approveCount = recommendations.filter(d => d === 'APPROVE').length;
  const rejectCount = recommendations.filter(d => d === 'REJECT').length;
  const escalateCount = recommendations.filter(d => d === 'ESCALATE').length;

  return {
    riskDistribution,
    recommendationData: recommendationData.length > 0 ? recommendationData : [
      { name: 'No Data', value: rows.length }
    ],
    riskByBankData,
    metrics: {
      totalChecks,
      avgRiskScore,
      approveCount,
      rejectCount,
      escalateCount
    }
  };
};
```

### 5. API Integration Functions

**Fetch Checks List (with date filtering):**
```javascript
const fetchChecksList = async (filter = null) => {
  setLoadingChecksList(true);
  setError(null);
  setCsvData(null);
  try {
    const url = filter
      ? `http://localhost:5001/api/checks/list?date_filter=${filter}`
      : 'http://localhost:5001/api/checks/list';
    const response = await fetch(url);
    const data = await response.json();
    if (data.success) {
      setChecksList(data.data);
      setTotalRecords(data.total_records || data.count);
      setDateFilter(filter);
      // Auto-load all checks as insights if data exists
      if (data.data && data.data.length > 0) {
        loadCheckData(data.data);
      } else {
        setError('No checks found for the selected date range');
      }
    } else {
      setError(data.message || 'Failed to fetch checks');
      setCsvData(null);
    }
  } catch (err) {
    setError('Failed to fetch checks from database');
    console.error('Error fetching checks:', err);
    setCsvData(null);
  } finally {
    setLoadingChecksList(false);
  }
};
```

**Search Checks by Payer Name:**
```javascript
const handleSearchChecks = async (query) => {
  if (!query) {
    fetchChecksList();
    return;
  }
  setLoadingChecksList(true);
  setError(null);
  setCsvData(null);
  try {
    const response = await fetch(`http://localhost:5001/api/checks/search?q=${encodeURIComponent(query)}&limit=20`);
    const data = await response.json();
    if (data.success) {
      setChecksList(data.data);
      if (data.data && data.data.length > 0) {
        loadCheckData(data.data);
      } else {
        setError('No checks found matching your search');
      }
    } else {
      setError(data.message || 'Search failed');
      setCsvData(null);
    }
  } catch (err) {
    setError('Failed to search checks');
    console.error('Error searching checks:', err);
    setCsvData(null);
  } finally {
    setLoadingChecksList(false);
  }
};
```

**Load Check Data for Visualization:**
```javascript
const loadCheckData = async (checks) => {
  if (!checks || checks.length === 0) {
    setError('No checks selected');
    return;
  }

  try {
    // Transform database records to format expected by processData
    const rows = checks.map(check => ({
      'fraud_risk_score': check.fraud_risk_score || 0,
      'ai_recommendation': check.ai_recommendation || 'UNKNOWN',
      'bank_name': check.bank_name || 'Unknown',
      'check_number': check.check_number || 'N/A',
      'amount': check.amount || 0,
    }));

    const processed = processData(rows);
    setCsvData(processed);
    setError(null);
    // Auto-scroll to metrics section
    setTimeout(() => {
      document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  } catch (err) {
    setError(`Error processing checks: ${err.message}`);
  }
};
```

### 6. CSV File Upload Handler

```javascript
const onDrop = useCallback((acceptedFiles) => {
  const file = acceptedFiles[0];
  if (!file) return;

  setLoading(true);
  setError(null);

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const text = e.target.result;
      const rows = parseCSV(text);

      if (rows.length === 0) {
        setError('No valid data found in CSV');
        setLoading(false);
        return;
      }

      const processed = processData(rows);
      setCsvData(processed);
      setError(null);
    } catch (err) {
      setError(`Error parsing CSV: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  reader.onerror = () => {
    setError('Error reading file');
    setLoading(false);
  };

  reader.readAsText(file);
}, []);

const { getRootProps, getInputProps, isDragActive } = useDropzone({
  onDrop,
  accept: {
    'text/csv': ['.csv']
  },
  multiple: false
});
```

### 7. UI Components

**Input Mode Toggle:**
- Two buttons: "Upload CSV" and "Connect API"
- Toggle between CSV upload and database connection modes

**CSV Upload Section:**
- Drag-and-drop zone using `react-dropzone`
- Accepts `.csv` files only
- Shows loading state during processing

**API/Database Section:**
- Search input for payer name
- Date filter buttons: All Records, Last 30 Days, 31-60 Days, 61-90 Days, Older (90+)
- Scrollable list of checks with selection
- Shows check details: payer name, check number, amount, risk score

**Metrics Cards:**
- Total Checks
- Avg Risk Score (%)
- APPROVE count
- REJECT count
- ESCALATE count

**Charts:**
1. **Risk Score Distribution** (Bar Chart)
2. **AI Decision Breakdown** (Pie Chart)
3. **Risk Level by Bank** (Bar Chart with dual bars)

---

## Backend API Endpoints

### 1. Get Checks List (with Date Filtering)

**Endpoint:** `GET /api/checks/list`

**Query Parameters:**
- `date_filter` (optional): `'last_30'`, `'last_60'`, `'last_90'`, `'older'`, or `null` for all

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "check_id": "uuid",
      "document_id": "uuid",
      "check_number": "12345",
      "amount": "1000.00",
      "check_date": "2024-01-15",
      "payer_name": "John Doe",
      "payee_name": "Jane Smith",
      "bank_name": "Chase Bank",
      "fraud_risk_score": 0.65,
      "model_confidence": 0.85,
      "ai_recommendation": "ESCALATE",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 150,
  "total_records": 500,
  "date_filter": "last_30"
}
```

**Implementation:**
```python
@app.route('/api/checks/list', methods=['GET'])
def get_checks_list():
    """Fetch list of checks from database view with optional date filtering"""
    try:
        from datetime import datetime, timedelta
        supabase = get_supabase()

        # Get all records - explicitly request large count to bypass Supabase default limit of 1000
        response = supabase.table('v_checks_analysis').select('*', count='exact').order('created_at', desc=True).execute()
        data = response.data or []
        total_available = response.count if hasattr(response, 'count') else len(data)

        # Optional date filtering
        date_filter = request.args.get('date_filter', default=None)  # 'last_30', 'last_60', 'last_90', 'older'

        if date_filter:
            now = datetime.utcnow()
            filtered_data = []

            for record in data:
                created_at_str = record.get('created_at')
                if not created_at_str:
                    continue

                # Parse created_at timestamp
                try:
                    # Handle ISO format timestamps with or without microseconds
                    if 'T' in created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00').split('+')[0])
                    else:
                        created_at = datetime.fromisoformat(created_at_str)
                except:
                    continue

                days_old = (now - created_at).days

                if date_filter == 'last_30' and days_old <= 30:
                    filtered_data.append(record)
                elif date_filter == 'last_60' and 31 <= days_old <= 60:
                    filtered_data.append(record)
                elif date_filter == 'last_90' and 61 <= days_old <= 90:
                    filtered_data.append(record)
                elif date_filter == 'older' and days_old > 90:
                    filtered_data.append(record)

            data = filtered_data

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'total_records': total_available if not date_filter else None,
            'date_filter': date_filter
        })
    except Exception as e:
        logger.error(f"Failed to fetch checks list: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch checks list'
        }), 500
```

### 2. Search Checks by Payer Name

**Endpoint:** `GET /api/checks/search`

**Query Parameters:**
- `q` (required): Search query string
- `limit` (optional, default: 20): Maximum number of results

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "check_id": "uuid",
      "payer_name": "John Doe",
      "check_number": "12345",
      "amount": "1000.00",
      "fraud_risk_score": 0.65,
      "ai_recommendation": "ESCALATE",
      "bank_name": "Chase Bank"
    }
  ],
  "count": 5
}
```

**Implementation:**
```python
@app.route('/api/checks/search', methods=['GET'])
def search_checks():
    """Search checks by payer name from view"""
    try:
        supabase = get_supabase()
        query = request.args.get('q', default='', type=str)
        limit = request.args.get('limit', default=20, type=int)
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required',
                'message': 'Please provide a search query'
            }), 400
        response = supabase.table('v_checks_analysis').select('*').ilike('payer_name', f'%{query}%').limit(limit).execute()
        return jsonify({
            'success': True,
            'data': response.data,
            'count': len(response.data)
        })
    except Exception as e:
        logger.error(f"Failed to search checks: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to search checks'
        }), 500
```

### 3. Get Check Details (Optional)

**Endpoint:** `GET /api/checks/<check_id>`

**Response:**
```json
{
  "success": true,
  "data": {
    "check_id": "uuid",
    "payer_name": "John Doe",
    // ... all check fields
  }
}
```

---

## Database Setup

### 1. Database View Creation

**File:** `Backend/database/create_checks_analysis_view.sql`

```sql
-- Drop existing v_checks_analysis view and recreate with ai_recommendation
DROP VIEW IF EXISTS v_checks_analysis CASCADE;

-- Create v_checks_analysis view with selected columns including ai_recommendation
CREATE VIEW v_checks_analysis AS
SELECT
  c.check_id,
  c.document_id,
  c.check_number,
  c.amount,
  c.check_date,
  c.payer_name,
  c.payee_name,
  c.bank_name,
  c.fraud_risk_score,
  c.model_confidence,
  c.ai_recommendation,
  c.created_at,
  c.timestamp
FROM
  checks c
ORDER BY
  c.timestamp DESC;
```

**Required Columns in `checks` table:**
- `check_id` (UUID, primary key)
- `document_id` (UUID)
- `check_number` (TEXT)
- `amount` (NUMERIC or TEXT)
- `check_date` (DATE or TEXT)
- `payer_name` (TEXT)
- `payee_name` (TEXT)
- `bank_name` (TEXT)
- `fraud_risk_score` (NUMERIC, 0.0 to 1.0)
- `model_confidence` (NUMERIC, 0.0 to 1.0)
- `ai_recommendation` (TEXT: 'APPROVE', 'REJECT', 'ESCALATE')
- `created_at` (TIMESTAMP)
- `timestamp` (TIMESTAMP)

### 2. Ensure AI Columns Exist

**File:** `Backend/database/add_ai_columns.sql`

```sql
-- Add AI analysis columns to checks table
ALTER TABLE checks
ADD COLUMN IF NOT EXISTS ai_recommendation TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS fraud_risk_score NUMERIC DEFAULT NULL,
ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS model_confidence NUMERIC DEFAULT NULL,
ADD COLUMN IF NOT EXISTS anomaly_count INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS top_anomalies JSONB DEFAULT NULL;
```

---

## Data Processing Logic

### CSV Column Mapping

The frontend expects CSV files with these column names (case-insensitive):

**Required Columns:**
- `RiskScore` or `fraud_risk_score` - Numeric (0.0 to 1.0) or percentage (0-100)
- `Decision` or `ai_recommendation` - Text: 'APPROVE', 'REJECT', 'ESCALATE'
- `BankName` or `bank_name` - Text

**Optional Columns:**
- `CheckNumber` or `check_number`
- `Amount` or `amount`
- `PayerName` or `payer_name`
- `PayeeName` or `payee_name`

### Database Record Mapping

When loading from database, the frontend maps:
- `check.fraud_risk_score` → `fraud_risk_score` (0.0 to 1.0)
- `check.ai_recommendation` → `ai_recommendation` ('APPROVE'/'REJECT'/'ESCALATE')
- `check.bank_name` → `bank_name`
- `check.check_number` → `check_number`
- `check.amount` → `amount`

---

## Graphs and Charts

### 1. Risk Score Distribution (Bar Chart)

**Data Structure:**
```javascript
[
  { range: '0-25%', count: 45 },
  { range: '25-50%', count: 30 },
  { range: '50-75%', count: 20 },
  { range: '75-100%', count: 5 }
]
```

**Implementation:**
```javascript
<ResponsiveContainer width="100%" height={300}>
  <BarChart data={csvData.riskDistribution}>
    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
    <XAxis dataKey="range" stroke={colors.mutedForeground} />
    <YAxis stroke={colors.mutedForeground} />
    <Tooltip
      contentStyle={{
        backgroundColor: colors.card,
        border: `1px solid ${colors.border}`,
        color: colors.foreground
      }}
    />
    <Bar dataKey="count" fill={primary} />
  </BarChart>
</ResponsiveContainer>
```

### 2. AI Decision Breakdown (Pie Chart)

**Data Structure:**
```javascript
[
  { name: 'APPROVE', value: 60 },
  { name: 'REJECT', value: 25 },
  { name: 'ESCALATE', value: 15 }
]
```

**Implementation:**
```javascript
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

<ResponsiveContainer width="100%" height={300}>
  <PieChart>
    <Pie
      data={csvData.recommendationData}
      cx="50%"
      cy="50%"
      labelLine={false}
      label={({ name, value }) => `${name}: ${value}`}
      outerRadius={80}
      fill="#8884d8"
      dataKey="value"
    >
      {csvData.recommendationData.map((_, index) => (
        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
      ))}
    </Pie>
    <Tooltip
      contentStyle={{
        backgroundColor: colors.card,
        border: `1px solid ${colors.border}`,
        color: colors.foreground
      }}
    />
  </PieChart>
</ResponsiveContainer>
```

### 3. Risk Level by Bank (Dual Bar Chart)

**Data Structure:**
```javascript
[
  { name: 'Chase Bank', avgRisk: '45.2', count: 25 },
  { name: 'Bank of America', avgRisk: '38.7', count: 18 },
  { name: 'Wells Fargo', avgRisk: '52.1', count: 12 }
]
```

**Implementation:**
```javascript
<ResponsiveContainer width="100%" height={300}>
  <BarChart data={csvData.riskByBankData}>
    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
    <XAxis dataKey="name" stroke={colors.mutedForeground} />
    <YAxis stroke={colors.mutedForeground} />
    <Tooltip
      contentStyle={{
        backgroundColor: colors.card,
        border: `1px solid ${colors.border}`,
        color: colors.foreground
      }}
    />
    <Legend />
    <Bar dataKey="avgRisk" fill={colors.status.warning} name="Avg Risk Score (%)" />
    <Bar dataKey="count" fill={colors.status.success} name="Check Count" />
  </BarChart>
</ResponsiveContainer>
```

---

## CSV Format Requirements

### Sample CSV File

```csv
RiskScore,Decision,BankName,CheckNumber,Amount,PayerName,PayeeName
0.65,ESCALATE,Chase Bank,12345,1000.00,John Doe,Jane Smith
0.25,APPROVE,Bank of America,67890,500.00,Jane Smith,Bob Johnson
0.85,REJECT,Wells Fargo,11111,2500.00,Bob Johnson,John Doe
0.45,APPROVE,Chase Bank,22222,750.00,Alice Brown,Charlie Wilson
```

**Alternative Column Names (also supported):**
- `fraud_risk_score` instead of `RiskScore`
- `ai_recommendation` instead of `Decision`
- `bank_name` instead of `BankName`
- `check_number` instead of `CheckNumber`
- `payer_name` instead of `PayerName`
- `payee_name` instead of `PayeeName`

**Notes:**
- Risk scores can be 0.0-1.0 (decimal) or 0-100 (percentage)
- Decisions must be: `APPROVE`, `REJECT`, or `ESCALATE` (case-insensitive)
- All other columns are optional

---

## Integration Steps

### Step 1: Add Component to Page

**File:** `Frontend/src/pages/CheckAnalysis.jsx`

```javascript
import CheckInsights from '../components/CheckInsights';

// In the component, add tab navigation:
const [activeTab, setActiveTab] = useState('analyze');

// Add tabs:
<div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
  <button onClick={() => setActiveTab('analyze')}>Single Check Analysis</button>
  <button onClick={() => setActiveTab('insights')}>CSV Insights</button>
</div>

// Render CheckInsights in insights tab:
{activeTab === 'insights' && <CheckInsights />}
```

### Step 2: Create Backend Endpoints

Add the three endpoints to `Backend/api_server.py`:
1. `GET /api/checks/list` - List all checks with date filtering
2. `GET /api/checks/search` - Search checks by payer name
3. `GET /api/checks/<check_id>` - Get single check details (optional)

### Step 3: Create Database View

Run the SQL script to create `v_checks_analysis` view:
```bash
psql -U your_user -d your_database -f Backend/database/create_checks_analysis_view.sql
```

Or execute via Supabase dashboard SQL editor.

### Step 4: Install Frontend Dependencies

```bash
cd Frontend
npm install recharts react-dropzone react-icons
```

### Step 5: Update API Base URL

If your backend runs on a different port, update the API URLs in `CheckInsights.jsx`:
- Change `http://localhost:5001` to your backend URL
- Or use environment variables: `process.env.REACT_APP_API_URL || 'http://localhost:5001'`

### Step 6: Test the Implementation

1. **Test CSV Upload:**
   - Create a sample CSV file with the required columns
   - Upload via the "Upload CSV" tab
   - Verify charts render correctly

2. **Test Database Connection:**
   - Switch to "Connect API" tab
   - Click "All Records" or a date filter
   - Verify checks list loads
   - Verify charts render from database data

3. **Test Search:**
   - Enter a payer name in search box
   - Verify filtered results appear
   - Verify charts update

---

## Styling and Colors

The component uses a centralized color system from `Frontend/src/styles/colors.js`:

```javascript
const primary = colors.primaryColor || colors.accent?.red || '#E53935';
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
```

**Key Style Objects:**
- `containerStyle` - Main container
- `cardStyle` - Card containers
- `dropzoneStyle` - CSV upload area
- `chartContainerStyle` - Chart wrapper
- `metricsGridStyle` - Metrics cards grid
- `metricCardStyle` - Individual metric card

---

## Error Handling

The component handles:
- Invalid CSV format
- Empty CSV files
- Missing required columns
- API connection errors
- Database query failures
- Empty search results
- Date filter edge cases

All errors are displayed in red error boxes with descriptive messages.

---

## Performance Considerations

1. **Large Datasets:**
   - Date filtering happens server-side for better performance
   - Search results are limited to 20 by default
   - Charts only show top 10 banks

2. **CSV Processing:**
   - Parsing happens client-side (suitable for files < 10MB)
   - For larger files, consider server-side processing

3. **Database Queries:**
   - Use pagination for very large datasets
   - Consider caching frequently accessed data

---

## Troubleshooting

**Charts not rendering:**
- Check browser console for errors
- Verify `recharts` is installed
- Ensure data structure matches expected format

**API calls failing:**
- Verify backend is running on correct port
- Check CORS settings in Flask
- Verify database connection

**CSV parsing errors:**
- Ensure CSV uses comma delimiters
- Check for proper quote escaping
- Verify column names match expected format

**Database view not found:**
- Run the SQL script to create the view
- Verify view name is `v_checks_analysis`
- Check Supabase permissions

---

## Summary

This implementation provides:
✅ CSV file upload and processing
✅ Database integration with search and filtering
✅ Three interactive charts (Bar, Pie, Dual Bar)
✅ Real-time metrics calculation
✅ Responsive design with proper error handling
✅ Easy integration into existing pages

**Key Files:**
- `Frontend/src/components/CheckInsights.jsx` - Main component
- `Backend/api_server.py` - API endpoints (lines 687-800)
- `Backend/database/create_checks_analysis_view.sql` - Database view

**Dependencies:**
- Frontend: `recharts`, `react-dropzone`, `react-icons`
- Backend: Flask, Supabase client
- Database: PostgreSQL with Supabase

Use this documentation as a complete reference to replicate the Checks Insights functionality in other branches or for other document types (Money Orders, Paystubs, Bank Statements).

