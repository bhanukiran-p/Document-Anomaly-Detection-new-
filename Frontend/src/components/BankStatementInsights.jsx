import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Sector,
  ComposedChart, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { FaUpload, FaCog } from 'react-icons/fa';

// Custom Tooltip Component
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: '8px',
        padding: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
      }}>
        <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
          {label}
        </p>
        {payload.map((entry, index) => (
          <p key={index} style={{ margin: '4px 0', color: entry.color }}>
            <span style={{ fontWeight: '600' }}>{entry.name || entry.dataKey}:</span> {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const BankStatementInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('upload'); // 'upload' or 'api'
  const [bankStatementsList, setBankStatementsList] = useState([]);
  const [loadingBankStatementsList, setLoadingBankStatementsList] = useState(false);
  const [selectedBankStatementId, setSelectedBankStatementId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'older'
  const [totalRecords, setTotalRecords] = useState(0);
  const [bankFilter, setBankFilter] = useState(null);
  const [availableBanks, setAvailableBanks] = useState([]);
  const [allBankStatementsData, setAllBankStatementsData] = useState([]);
  const [activePieIndex, setActivePieIndex] = useState(null);
  const [activeBarIndex, setActiveBarIndex] = useState(null);

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

  const parseFloat_ = (val) => {
    const num = parseFloat(val);
    return isNaN(num) ? 0 : num;
  };

  const processData = (rows) => {
    if (!rows.length) return null;

    // 1. Fraud Risk Distribution (0-25%, 25-50%, 50-75%, 75-100%)
    const riskScores = rows.map(r => parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0));
    const riskDistribution = [
      { range: '0-25%', count: riskScores.filter(s => s < 25).length },
      { range: '25-50%', count: riskScores.filter(s => s >= 25 && s < 50).length },
      { range: '50-75%', count: riskScores.filter(s => s >= 50 && s < 75).length },
      { range: '75-100%', count: riskScores.filter(s => s >= 75).length },
    ];

    // 2. AI Recommendation Distribution (APPROVE/REJECT/ESCALATE)
    const recommendations = rows.map(r => (r['AI Recommendation'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
    const recommendationData = [
      { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
      { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
      { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
    ].filter(item => item.value > 0);

    // 3. Risk by Bank (Average risk score per bank)
    const bankRisks = {};
    rows.forEach(r => {
      const bank = r['Bank Name'] || r['bank_name'] || 'Unknown';
      if (!bankRisks[bank]) {
        bankRisks[bank] = { count: 0, totalRisk: 0 };
      }
      bankRisks[bank].count++;
      bankRisks[bank].totalRisk += parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
    });
    const riskByBankData = Object.entries(bankRisks)
      .map(([name, data]) => ({
        name,
        avgRisk: parseFloat(((data.totalRisk / data.count) * 100).toFixed(1)),
        count: data.count
      }))
      .sort((a, b) => b.avgRisk - a.avgRisk)
      .map(bank => ({
        ...bank,
        displayName: (() => {
          const name = bank.name.toUpperCase();
          if (name.includes('BANK OF AMERICA') || name.includes('BOFA')) return 'BOFA';
          if (name.includes('CHASE') || name.includes('JPM')) return 'JPMC';
          if (name.includes('WELLS FARGO') || name.includes('WELLS')) return 'WF';
          if (name.includes('CITIBANK') || name.includes('CITI')) return 'CITI';
          if (name.includes('US BANK')) return 'USB';
          if (name.includes('ALLY')) return 'ALLY';
          return bank.name.length > 10 ? bank.name.substring(0, 10) + '...' : bank.name;
        })()
      }));

    // 4. Fraud Type Distribution (classify by actual fraud types)
    const fraudTypeCount = {};
    
    // Track account holders for repeat offender detection
    const accountHolderRiskCount = {};
    
    // Helper function to normalize fraud type name from database
    const normalizeFraudType = (fraudType) => {
      // Explicitly check for null/undefined/empty string
      if (fraudType === null || fraudType === undefined || fraudType === '') {
        return null;
      }
      const normalized = fraudType.toString().trim();
      if (!normalized) return null;
      
      // Map database values to our standard names
      const typeMap = {
        'fabricated document': 'Fabricated Document',
        'altered legitimate document': 'Altered Legitimate Document',
        'suspicious transaction patterns': 'Suspicious Transaction Patterns',
        'balance consistency violation': 'Balance Consistency Violation',
        'unrealistic financial proportion': 'Unrealistic Financial Proportion',
        'unrealistic financial proportion': 'Unrealistic Financial Proportion', // Handle both cases
        'repeat offender': 'Repeat Offender'
      };
      return typeMap[normalized.toLowerCase()] || normalized;
    };
    
    // Helper function to classify fraud type based on anomalies and data
    const classifyFraudType = (row) => {
      const anomalies = row['Top Anomalies'] || row['top_anomalies'] || row['Anomalies'] || row['anomalies'] || '';
      const anomaliesStr = typeof anomalies === 'string' ? anomalies.toLowerCase() : 
                          (Array.isArray(anomalies) ? anomalies.join(' ').toLowerCase() : 
                          (typeof anomalies === 'object' ? JSON.stringify(anomalies).toLowerCase() : ''));
      
      const risk = parseFloat_(row['Fraud Risk Score (%)'] || row['fraud_risk_score'] || 0);
      const confidence = parseFloat_(row['Model Confidence (%)'] || row['model_confidence'] || 0);
      const accountHolder = (row['Account Holder'] || row['account_holder'] || '').toLowerCase().trim();
      
      // 1. Fabricated Document - Low confidence, missing critical fields, or document structure issues
      if (confidence < 50 || 
          anomaliesStr.includes('missing critical fields') ||
          anomaliesStr.includes('document structure') ||
          anomaliesStr.includes('invalid format') ||
          anomaliesStr.includes('poor ocr') ||
          (!row['Bank Name'] && !row['bank_name']) ||
          (!row['Account Number'] && !row['account_number'])) {
        return 'Fabricated Document';
      }
      
      // 2. Altered Legitimate Document - Signs of tampering or modification
      if (anomaliesStr.includes('altered') ||
          anomaliesStr.includes('tampered') ||
          anomaliesStr.includes('modified') ||
          anomaliesStr.includes('inconsistent formatting') ||
          anomaliesStr.includes('font mismatch') ||
          anomaliesStr.includes('date mismatch') ||
          anomaliesStr.includes('signature mismatch')) {
        return 'Altered Legitimate Document';
      }
      
      // 3. Suspicious Transaction Patterns - Unusual transaction activity
      if (anomaliesStr.includes('suspicious transaction') ||
          anomaliesStr.includes('unusual pattern') ||
          anomaliesStr.includes('rapid transactions') ||
          anomaliesStr.includes('round number') ||
          anomaliesStr.includes('odd hours') ||
          anomaliesStr.includes('transaction frequency') ||
          anomaliesStr.includes('unusual amount')) {
        return 'Suspicious Transaction Patterns';
      }
      
      // 4. Balance Consistency Violation - Math doesn't add up
      if (anomaliesStr.includes('balance inconsistent') ||
          anomaliesStr.includes('balance mismatch') ||
          anomaliesStr.includes('amount mismatch') ||
          anomaliesStr.includes('math inconsistent') ||
          anomaliesStr.includes('reconciliation') ||
          anomaliesStr.includes('balance calculation')) {
        return 'Balance Consistency Violation';
      }
      
      // 5. Unrealistic Financial Proportion - Unrealistic amounts or proportions
      if (anomaliesStr.includes('unrealistic') ||
          anomaliesStr.includes('proportion') ||
          anomaliesStr.includes('unusual amount') ||
          anomaliesStr.includes('excessive') ||
          anomaliesStr.includes('improbable') ||
          risk > 70 && confidence > 70) {
        return 'Unrealistic Financial Proportion';
      }
      
      // Default: if high risk but doesn't match above, classify as Suspicious Transaction Patterns
      if (risk >= 75) {
        return 'Suspicious Transaction Patterns';
      }
      
      // If no specific match, use risk-based classification as fallback
      return 'Unrealistic Financial Proportion';
    };
    
    // First pass: track account holders for repeat offender detection
    rows.forEach(r => {
      const accountHolder = (r['Account Holder'] || r['account_holder'] || '').toLowerCase().trim();
      const risk = parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
      if (accountHolder) {
        if (!accountHolderRiskCount[accountHolder]) {
          accountHolderRiskCount[accountHolder] = { count: 0, highRiskCount: 0 };
        }
        accountHolderRiskCount[accountHolder].count++;
        if (risk >= 50) {
          accountHolderRiskCount[accountHolder].highRiskCount++;
        }
      }
    });
    
    // Second pass: classify all statements
    // Priority: 1) Use database fraud_types if available, 2) Otherwise classify from anomalies
    const repeatOffenderThreshold = 2; // 2+ high-risk statements
    const genericFallbackTypes = ['Suspicious Transaction Patterns', 'Unrealistic Financial Proportion'];
    
    rows.forEach(r => {
      const accountHolder = (r['Account Holder'] || r['account_holder'] || '').toLowerCase().trim();
      const risk = parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
      
      // First priority: Use fraud_types from database if available
      // Check all possible field names
      const dbFraudType = r['fraud_types'] !== undefined ? r['fraud_types'] : 
                         (r['Fraud Types'] !== undefined ? r['Fraud Types'] : 
                         (r['fraud_type'] !== undefined ? r['fraud_type'] : 
                         (r['Fraud Type'] !== undefined ? r['Fraud Type'] : null)));
      
      // If database fraud_type is explicitly NULL, undefined, empty string, or the string "null", skip classification
      // This prevents NULL records from being incorrectly classified as "Unrealistic Financial Proportion"
      if (dbFraudType === null || 
          dbFraudType === undefined || 
          dbFraudType === '' || 
          (typeof dbFraudType === 'string' && dbFraudType.toLowerCase() === 'null')) {
        // Skip NULL records - they shouldn't be classified
        return;
      }
      
      let fraudType = normalizeFraudType(dbFraudType);
      
      // If no database fraud type (but not NULL), classify from anomalies
      if (!fraudType) {
        fraudType = classifyFraudType(r);
        
        // Check if this classification was a generic fallback (no specific indicators)
        const anomalies = r['Top Anomalies'] || r['top_anomalies'] || r['Anomalies'] || r['anomalies'] || '';
        const anomaliesStr = typeof anomalies === 'string' ? anomalies.toLowerCase() : 
                            (Array.isArray(anomalies) ? anomalies.join(' ').toLowerCase() : 
                            (typeof anomalies === 'object' ? JSON.stringify(anomalies).toLowerCase() : ''));
        
        // Check if we have specific anomaly indicators
        const hasSpecificIndicators = anomaliesStr.length > 0 && (
          anomaliesStr.includes('missing') ||
          anomaliesStr.includes('altered') ||
          anomaliesStr.includes('tampered') ||
          anomaliesStr.includes('suspicious transaction') ||
          anomaliesStr.includes('balance inconsistent') ||
          anomaliesStr.includes('balance mismatch') ||
          anomaliesStr.includes('amount mismatch') ||
          anomaliesStr.includes('math inconsistent') ||
          anomaliesStr.includes('unrealistic') ||
          anomaliesStr.includes('proportion') ||
          anomaliesStr.includes('document structure') ||
          anomaliesStr.includes('invalid format') ||
          anomaliesStr.includes('poor ocr') ||
          anomaliesStr.includes('inconsistent formatting') ||
          anomaliesStr.includes('font mismatch') ||
          anomaliesStr.includes('date mismatch') ||
          anomaliesStr.includes('signature mismatch')
        );
        
        // Only override with "Repeat Offender" if:
        // 1. The account holder has 2+ high-risk statements AND
        // 2. The current statement is also high-risk (≥50%) AND
        // 3. The classification is a generic fallback (not a specific fraud type) OR no specific indicators found
        if (accountHolder && accountHolderRiskCount[accountHolder]) {
          const holderData = accountHolderRiskCount[accountHolder];
          const isRepeatOffender = holderData.highRiskCount >= repeatOffenderThreshold && holderData.count >= repeatOffenderThreshold;
          const isCurrentHighRisk = risk >= 50;
          
          // Only classify as Repeat Offender if:
          // - It's a repeat offender pattern AND
          // - Current statement is high-risk AND
          // - (No specific indicators found OR it's already classified as a generic fallback)
          if (isRepeatOffender && isCurrentHighRisk && (!hasSpecificIndicators || genericFallbackTypes.includes(fraudType))) {
            fraudType = 'Repeat Offender';
          }
        }
      }
      
      // Only count if we have a valid fraud type
      if (fraudType) {
        if (!fraudTypeCount[fraudType]) {
          fraudTypeCount[fraudType] = 0;
        }
        fraudTypeCount[fraudType]++;
      }
    });

    const fraudTypeData = Object.entries(fraudTypeCount)
      .map(([name, count]) => ({
        name: name.replace(/_/g, ' ').trim(),
        value: count
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);

    // 5. Fraud Trend Over Time
    const fraudOverTime = {};
    rows.forEach(r => {
      const dateStr = r['Timestamp'] || r['timestamp'] || r['Statement Period'] || '';
      if (dateStr) {
        const date = dateStr.split('T')[0].split(' ')[0];
        if (!fraudOverTime[date]) {
          fraudOverTime[date] = { count: 0, highRiskCount: 0, totalRisk: 0 };
        }
        const risk = parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
        fraudOverTime[date].count++;
        fraudOverTime[date].totalRisk += risk;
        if (risk >= 75) {
          fraudOverTime[date].highRiskCount++;
        }
      }
    });
    const fraudTrendData = Object.entries(fraudOverTime)
      .map(([date, data]) => ({
        date,
        avgRisk: (data.totalRisk / data.count).toFixed(1),
        highRiskCount: data.highRiskCount,
        totalCount: data.count
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-30);

    // 6. Summary Metrics
    const totalStatements = rows.length;
    const avgRiskScore = riskScores.length > 0 ? (riskScores.reduce((a, b) => a + b, 0) / riskScores.length).toFixed(1) : '0.0';
    const approveCount = recommendations.filter(d => d === 'APPROVE').length;
    const rejectCount = recommendations.filter(d => d === 'REJECT').length;
    const escalateCount = recommendations.filter(d => d === 'ESCALATE').length;
    const highRiskCount = riskScores.filter(s => s >= 75).length;

    return {
      riskDistribution,
      recommendationData: recommendationData.length > 0 ? recommendationData : [
        { name: 'No Data', value: rows.length }
      ],
      riskByBankData,
      fraudTypeData,
      fraudTrendData,
      metrics: {
        totalStatements,
        avgRiskScore,
        approveCount,
        rejectCount,
        escalateCount,
        highRiskCount
      }
    };
  };

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

  const fetchBankStatementsList = async (filter = null, bank = null) => {
    setLoadingBankStatementsList(true);
    setError(null);
    setCsvData(null);
    try {
      // Use relative URL to leverage proxy in package.json
      const url = filter
        ? `/api/bank-statements/list?date_filter=${filter}`
        : `/api/bank-statements/list`;
      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        const fetchedData = data.data || [];
        setAllBankStatementsData(fetchedData);
        
        // Extract unique banks from the data
        const uniqueBanks = [...new Set(fetchedData.map(bs => bs.bank_name).filter(Boolean))].sort();
        setAvailableBanks(uniqueBanks);
        
        // Apply bank filter if specified
        let filteredData = fetchedData;
        if (bank) {
          filteredData = fetchedData.filter(bs => bs.bank_name === bank);
          setBankFilter(bank);
        } else {
          setBankFilter(null);
        }
        
        setBankStatementsList(filteredData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(filter);
        // Auto-load all bank statements as insights if data exists
        if (filteredData.length > 0) {
          loadBankStatementData(filteredData);
        } else {
          setError('No bank statements found for the selected filters');
        }
      } else {
        setError(data.message || 'Failed to fetch bank statements');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to fetch bank statements from database');
      console.error('Error fetching bank statements:', err);
      setCsvData(null);
    } finally {
      setLoadingBankStatementsList(false);
    }
  };

  const handleSearchBankStatements = async (query) => {
    if (!query) {
      setBankFilter(null);
      fetchBankStatementsList(dateFilter);
      return;
    }
    setLoadingBankStatementsList(true);
    setError(null);
    setCsvData(null);
    try {
      const response = await fetch(`/api/bank-statements/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setBankStatementsList(data.data);
        if (data.data && data.data.length > 0) {
          loadBankStatementData(data.data);
        } else {
          setError('No bank statements found matching your search');
        }
      } else {
        setError(data.message || 'Search failed');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to search bank statements');
      console.error('Error searching bank statements:', err);
      setCsvData(null);
    } finally {
      setLoadingBankStatementsList(false);
    }
  };

  const loadBankStatementData = async (bankStatements) => {
    if (!bankStatements || bankStatements.length === 0) {
      setError('No bank statements selected');
      return;
    }

    try {
      // Transform database records to format expected by processData
      const rows = bankStatements.map(bs => {
        // Parse top_anomalies if it's a JSONB field
        let anomalies = '';
        if (bs.top_anomalies) {
          if (typeof bs.top_anomalies === 'string') {
            try {
              const parsed = JSON.parse(bs.top_anomalies);
              anomalies = Array.isArray(parsed) ? parsed.map(a => 
                typeof a === 'string' ? a : (a.message || a.type || JSON.stringify(a))
              ).join(' | ') : bs.top_anomalies;
            } catch {
              anomalies = bs.top_anomalies;
            }
          } else if (Array.isArray(bs.top_anomalies)) {
            anomalies = bs.top_anomalies.map(a => 
              typeof a === 'string' ? a : (a.message || a.type || JSON.stringify(a))
            ).join(' | ');
          } else {
            anomalies = JSON.stringify(bs.top_anomalies);
          }
        }
        
        return {
          'fraud_risk_score': bs.fraud_risk_score || 0,
          'Fraud Risk Score (%)': (bs.fraud_risk_score || 0) * 100,
          'ai_recommendation': bs.ai_recommendation || 'UNKNOWN',
          'AI Recommendation': bs.ai_recommendation || 'UNKNOWN',
          'bank_name': bs.bank_name || 'Unknown',
          'Bank Name': bs.bank_name || 'Unknown',
          'account_holder': bs.account_holder || '',
          'Account Holder': bs.account_holder || '',
          'account_number': bs.account_number || '',
          'Account Number': bs.account_number || '',
          'statement_period': bs.statement_period || '',
          'Statement Period': bs.statement_period || '',
          'timestamp': bs.timestamp || bs.created_at || '',
          'Timestamp': bs.timestamp || bs.created_at || '',
          'model_confidence': bs.model_confidence || 0,
          'Model Confidence (%)': (bs.model_confidence || 0) * 100,
          'top_anomalies': anomalies,
          'Top Anomalies': anomalies,
          'anomalies': anomalies,
          'Anomalies': anomalies,
          'fraud_types': bs.fraud_types || bs.fraud_type || null,
          'Fraud Types': bs.fraud_types || bs.fraud_type || null,
          'fraud_type': bs.fraud_types || bs.fraud_type || null,
          'Fraud Type': bs.fraud_types || bs.fraud_type || null,
        };
      });

      const processed = processData(rows);
      setCsvData(processed);
      setError(null);
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(`Error processing bank statements: ${err.message}`);
    }
  };

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  const containerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '1.5rem',
    backgroundColor: colors.background,
  };

  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem',
    marginBottom: '2rem',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    border: `1px solid ${colors.border}`,
  };

  const dropzoneStyle = {
    border: `2px dashed ${isDragActive ? primary : colors.border}`,
    borderRadius: '0.75rem',
    padding: '3rem',
    textAlign: 'center',
    backgroundColor: isDragActive ? colors.muted : colors.secondary,
    cursor: 'pointer',
    transition: 'all 0.2s',
  };

  const chartBoxStyle = {
    backgroundColor: colors.card,
    padding: '24px',
    borderRadius: '12px',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    transition: 'all 0.3s ease',
  };

  const chartTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: colors.foreground,
    marginBottom: '20px',
    paddingBottom: '12px',
    borderBottom: `2px solid ${colors.border}`,
  };

  const colorMap = {
    'APPROVE': colors.status.success || '#10b981',
    'REJECT': primary,
    'ESCALATE': colors.status.warning || '#f59e0b'
  };

  return (
    <div style={containerStyle}>
      {/* Mode Selector */}
      <div style={{ marginBottom: '2rem', display: 'flex', gap: '1rem' }}>
        <button
          onClick={() => setInputMode('upload')}
          style={{
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            backgroundColor: inputMode === 'upload' ? primary : colors.secondary,
            color: inputMode === 'upload' ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: inputMode === 'upload' ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          <FaUpload style={{ marginRight: '0.5rem', display: 'inline' }} />
          Upload CSV
        </button>
        <button
          onClick={() => {
            setInputMode('api');
            fetchBankStatementsList();
          }}
          style={{
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            backgroundColor: inputMode === 'api' ? primary : colors.secondary,
            color: inputMode === 'api' ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: inputMode === 'api' ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          <FaCog style={{ marginRight: '0.5rem', display: 'inline' }} />
          Live Data
        </button>
      </div>

      {inputMode === 'upload' && (
        <>
          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            {isDragActive ? (
              <div>
                <FaUpload style={{ fontSize: '3rem', marginBottom: '1rem', color: primary }} />
                <p style={{ color: primary, fontWeight: '500' }}>
                  Drop the CSV file here...
                </p>
              </div>
            ) : (
              <div>
                <p style={{ color: colors.foreground, marginBottom: '0.5rem' }}>
                  Drag and drop your CSV file here, or click to browse
                </p>
                <p style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
                  CSV file with bank statement analysis data
                </p>
              </div>
            )}
          </div>

          {error && inputMode === 'upload' && (
            <div style={{
              backgroundColor: colors.accent.redLight,
              color: colors.accent.red,
              padding: '1rem',
              borderRadius: '8px',
              marginTop: '1rem',
              fontWeight: '500',
            }}>
              {error}
            </div>
          )}

          {loading && inputMode === 'upload' && (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FaCog className="spin" style={{
                fontSize: '2rem',
                color: primary,
              }} />
              <p style={{ marginTop: '0.5rem', color: colors.neutral.gray600 }}>
                Processing CSV...
              </p>
            </div>
          )}
        </>
      )}

      {inputMode === 'api' && (
        <>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="Search bank statements..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  if (e.target.value) {
                    handleSearchBankStatements(e.target.value);
                  } else {
                    fetchBankStatementsList(dateFilter);
                  }
                }}
                style={{
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  border: `1px solid ${colors.border}`,
                  fontSize: '14px',
                  flex: 1,
                  minWidth: '200px',
                  backgroundColor: colors.card,
                  color: colors.foreground
                }}
              />
              {availableBanks.length > 0 && (
                <select
                  value={bankFilter || ''}
                  onChange={(e) => {
                    const bank = e.target.value || null;
                    setBankFilter(bank);
                    fetchBankStatementsList(dateFilter, bank);
                  }}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    border: `1px solid ${colors.border}`,
                    fontSize: '14px',
                    backgroundColor: colors.card,
                    color: colors.foreground,
                    cursor: 'pointer'
                  }}
                >
                  <option value="">All Banks</option>
                  {availableBanks.map(bank => (
                    <option key={bank} value={bank}>{bank}</option>
                  ))}
                </select>
              )}
              <div style={{ fontSize: '12px', color: colors.mutedForeground, whiteSpace: 'nowrap' }}>
                {totalRecords} records
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <button
                onClick={() => fetchBankStatementsList(null, bankFilter)}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  backgroundColor: !dateFilter ? primary : colors.secondary,
                  color: !dateFilter ? colors.primaryForeground : colors.foreground,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                  fontWeight: !dateFilter ? '600' : '500',
                  transition: 'all 0.3s',
                }}
              >
                All Time
              </button>
              <button
                onClick={() => fetchBankStatementsList('last_30', bankFilter)}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  backgroundColor: dateFilter === 'last_30' ? primary : colors.secondary,
                  color: dateFilter === 'last_30' ? colors.primaryForeground : colors.foreground,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                  fontWeight: dateFilter === 'last_30' ? '600' : '500',
                  transition: 'all 0.3s',
                }}
              >
                Last 30
              </button>
              <button
                onClick={() => fetchBankStatementsList('last_60', bankFilter)}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  backgroundColor: dateFilter === 'last_60' ? primary : colors.secondary,
                  color: dateFilter === 'last_60' ? colors.primaryForeground : colors.foreground,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                  fontWeight: dateFilter === 'last_60' ? '600' : '500',
                  transition: 'all 0.3s',
                }}
              >
                Last 60
              </button>
              <button
                onClick={() => fetchBankStatementsList('last_90', bankFilter)}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  backgroundColor: dateFilter === 'last_90' ? primary : colors.secondary,
                  color: dateFilter === 'last_90' ? colors.primaryForeground : colors.foreground,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                  fontWeight: dateFilter === 'last_90' ? '600' : '500',
                  transition: 'all 0.3s',
                }}
              >
                Last 90
              </button>
              <button
                onClick={() => fetchBankStatementsList('older', bankFilter)}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  backgroundColor: dateFilter === 'older' ? primary : colors.secondary,
                  color: dateFilter === 'older' ? colors.primaryForeground : colors.foreground,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                  fontWeight: dateFilter === 'older' ? '600' : '500',
                  transition: 'all 0.3s',
                }}
              >
                Older
              </button>
              {(dateFilter || bankFilter) && (
                <button
                  onClick={() => {
                    setDateFilter(null);
                    setBankFilter(null);
                    setSearchQuery('');
                    fetchBankStatementsList(null, null);
                  }}
                  style={{
                    padding: '0.75rem 1rem',
                    borderRadius: '0.5rem',
                    backgroundColor: colors.accent.redLight || '#fee2e2',
                    color: colors.accent.red || primary,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer',
                    fontWeight: '600',
                    transition: 'all 0.3s',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <span>Reset Filters</span>
                </button>
              )}
            </div>
          </div>

          {loadingBankStatementsList && (
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <FaCog className="spin" style={{
                fontSize: '2rem',
                color: primary,
              }} />
              <p style={{ marginTop: '0.5rem', color: colors.mutedForeground }}>
                Loading bank statements...
              </p>
            </div>
          )}

          {error && inputMode === 'api' && (
            <div style={{
              backgroundColor: colors.accent.redLight,
              color: colors.accent.red,
              padding: '1rem',
              borderRadius: '8px',
              marginTop: '1rem',
              fontWeight: '500',
            }}>
              {error}
            </div>
          )}
        </>
      )}

      {csvData && (
        <div>
          {/* Summary Metrics */}
          <div data-metrics-section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Total Statements
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {csvData.metrics.totalStatements}
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Avg Risk Score
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {csvData.metrics.avgRiskScore}%
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Approve
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.success }}>
                {csvData.metrics.approveCount}
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Reject
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {csvData.metrics.rejectCount}
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Escalate
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.warning }}>
                {csvData.metrics.escalateCount}
              </div>
            </div>
          </div>

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '20px' }}>
            {/* AI Recommendation Breakdown */}
            {csvData.recommendationData && csvData.recommendationData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={csvData.recommendationData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={120}
                      label={false}
                      dataKey="value"
                      stroke={colors.card}
                      strokeWidth={3}
                      startAngle={90}
                      endAngle={-270}
                      activeIndex={activePieIndex}
                      activeShape={(props) => {
                        const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props;
                        return (
                          <Sector
                            cx={cx}
                            cy={cy}
                            innerRadius={innerRadius}
                            outerRadius={outerRadius + 5}
                            startAngle={startAngle}
                            endAngle={endAngle}
                            fill={fill}
                            opacity={0.9}
                          />
                        );
                      }}
                    >
                      {csvData.recommendationData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={colorMap[entry.name] || primary}
                          onMouseEnter={() => setActivePieIndex(index)}
                          onMouseLeave={() => setActivePieIndex(null)}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0];
                          const total = csvData.recommendationData.reduce((sum, item) => sum + item.value, 0);
                          const percentage = total > 0 ? ((data.value / total) * 100).toFixed(1) : 0;
                          return (
                            <div style={{
                              backgroundColor: colors.card,
                              border: `1px solid ${colors.border}`,
                              borderRadius: '8px',
                              padding: '12px',
                              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                            }}>
                              <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                                {data.name}
                              </p>
                              <p style={{ margin: '4px 0', color: data.color }}>
                                <span style={{ fontWeight: '600' }}>Count:</span> {data.value}
                              </p>
                              <p style={{ margin: '4px 0', color: data.color }}>
                                <span style={{ fontWeight: '600' }}>Percentage:</span> {percentage}%
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                      cursor={{ fill: 'transparent' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                  {csvData.recommendationData.map((entry, index) => (
                    <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{
                        width: '12px',
                        height: '12px',
                        borderRadius: '50%',
                        backgroundColor: colorMap[entry.name] || primary
                      }} />
                      <span style={{ fontSize: '0.875rem', color: colors.foreground }}>
                        {entry.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Risk Score Distribution by Range */}
            {csvData.riskDistribution && csvData.riskDistribution.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Score Distribution by Range</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={csvData.riskDistribution} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                    <defs>
                      <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={primary} stopOpacity={1} />
                        <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
                      </linearGradient>
                      <linearGradient id="riskGradientHover" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={primary} stopOpacity={1} />
                        <stop offset="100%" stopColor={primary} stopOpacity={0.9} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                    <XAxis 
                      dataKey="range" 
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      stroke={colors.border}
                    />
                    <YAxis 
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      stroke={colors.border}
                    />
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div style={{
                              backgroundColor: colors.card,
                              border: `1px solid ${colors.border}`,
                              borderRadius: '8px',
                              padding: '12px',
                              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                            }}>
                              <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                                {data.range}
                              </p>
                              <p style={{ margin: '4px 0', color: primary }}>
                                <span style={{ fontWeight: '600' }}>Count:</span> {data.count}
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                      cursor={{ fill: 'transparent' }}
                    />
                    <Bar dataKey="count" fill="url(#riskGradient)" radius={[8, 8, 0, 0]} name="Bank Statement Count">
                      {csvData.riskDistribution.map((entry, index) => {
                        const isActive = activeBarIndex === index;
                        return (
                          <Cell
                            key={`risk-cell-${index}`}
                            fill={isActive ? "url(#riskGradientHover)" : "url(#riskGradient)"}
                            onMouseEnter={() => setActiveBarIndex(index)}
                            onMouseLeave={() => setActiveBarIndex(null)}
                            style={{
                              cursor: 'pointer',
                              transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                              filter: isActive ? 'brightness(1.1)' : 'brightness(1)'
                            }}
                          />
                        );
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Risk Level by Bank (Combined Bar + Line) */}
            {!bankFilter && csvData.riskByBankData && csvData.riskByBankData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Level by Bank</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart 
                    data={csvData.riskByBankData}
                    margin={{ top: 10, right: 30, left: 10, bottom: 60 }}
                    onMouseLeave={() => setActiveBarIndex(null)}
                  >
                    <defs>
                      <linearGradient id="countGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={colors.status.success || '#10b981'} stopOpacity={1} />
                        <stop offset="100%" stopColor={colors.status.success || '#10b981'} stopOpacity={0.7} />
                      </linearGradient>
                      <linearGradient id="countGradientHover" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={colors.status.success || '#10b981'} stopOpacity={1} />
                        <stop offset="100%" stopColor={colors.status.success || '#10b981'} stopOpacity={0.9} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                    <XAxis 
                      dataKey="displayName" 
                      tick={{ fill: colors.foreground, fontSize: 11 }}
                      stroke={colors.border}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      interval={0}
                    />
                    <YAxis 
                      yAxisId="left"
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      stroke={colors.border}
                      label={{ value: 'Statement Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                    />
                    <YAxis 
                      yAxisId="right"
                      orientation="right"
                      domain={[0, 100]}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      stroke={colors.border}
                      label={{ value: 'Avg Risk Score (%)', angle: 90, position: 'insideRight', fill: colors.foreground }}
                    />
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div style={{
                              backgroundColor: colors.card,
                              border: `1px solid ${colors.border}`,
                              borderRadius: '8px',
                              padding: '12px',
                              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                            }}>
                              <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                                {data.name}
                              </p>
                              {payload.map((entry, index) => (
                                <p key={index} style={{ margin: '4px 0', color: entry.color }}>
                                  <span style={{ fontWeight: '600' }}>{entry.name}:</span> {entry.name === 'Avg Risk Score (%)' ? `${entry.value}%` : entry.value}
                                </p>
                              ))}
                            </div>
                          );
                        }
                        return null;
                      }}
                      cursor={{ fill: 'transparent' }}
                    />
                    <Legend />
                    <Bar 
                      yAxisId="left"
                      dataKey="count" 
                      fill="url(#countGradient)"
                      name="Statement Count"
                    >
                      {csvData.riskByBankData.map((entry, index) => {
                        const isActive = activeBarIndex === index;
                        return (
                          <Cell 
                            key={`count-cell-${index}`}
                            fill={isActive ? "url(#countGradientHover)" : "url(#countGradient)"}
                            onMouseEnter={() => setActiveBarIndex(index)}
                            onMouseLeave={() => setActiveBarIndex(null)}
                            style={{
                              cursor: 'pointer',
                              transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                              filter: isActive ? 'brightness(1.1)' : 'brightness(1)'
                            }}
                          />
                        );
                      })}
                    </Bar>
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="avgRisk" 
                      stroke={primary}
                      strokeWidth={3}
                      dot={{ fill: primary, r: 5 }}
                      activeDot={{ r: 7 }}
                      name="Avg Risk Score (%)"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Fraud Type Distribution - Scatter Plot */}
            {csvData.fraudTypeData && csvData.fraudTypeData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Fraud Type Distribution</h3>
              {(() => {
                const total = csvData.fraudTypeData.reduce((sum, item) => sum + item.value, 0);
                const maxValue = Math.max(...csvData.fraudTypeData.map(e => e.value));
                
                // Colors that complement DAD color scheme (red/navy theme)
                const COMPLEMENTARY_COLORS = [
                  '#E53935', // Primary red (DAD)
                  '#14B8A6', // Teal (complements red)
                  '#F97316', // Orange/coral (warm complement)
                  '#8B5CF6', // Purple (complements navy)
                  '#06B6D4', // Cyan (bright complement)
                  '#F59E0B', // Amber (warm accent)
                  '#EC4899', // Pink (vibrant complement)
                  '#10B981'  // Green (fresh complement)
                ];
                
                // Prepare scatter plot data with complementary colors
                const scatterData = csvData.fraudTypeData.map((entry, index) => {
                  const percentage = total > 0 ? ((entry.value / total) * 100) : 0;
                  return {
                    name: entry.name,
                    count: entry.value,
                    percentage: parseFloat(percentage.toFixed(1)),
                    originalPercentage: parseFloat(percentage.toFixed(1)), // Keep original for domain calculation
                    size: entry.value, // For Z-axis (bubble size)
                    color: COMPLEMENTARY_COLORS[index % COMPLEMENTARY_COLORS.length],
                    index: index
                  };
                });
                
                // Add minimal jitter only to count axis to prevent overlapping points
                const processedData = scatterData.map((entry, index) => {
                  // Find other entries with same count and percentage
                  const duplicates = scatterData.filter((e, i) => 
                    i !== index && 
                    e.count === entry.count && 
                    Math.abs(e.percentage - entry.percentage) < 0.1
                  );
                  
                  // Calculate jitter offset based on position among duplicates
                  const duplicateIndex = scatterData.slice(0, index).filter((e) => 
                    e.count === entry.count && 
                    Math.abs(e.percentage - entry.percentage) < 0.1
                  ).length;
                  
                  // Add small offset only to count axis to prevent overlap
                  const jitterRadius = 2; // Small jitter for count axis only
                  const angle = (duplicateIndex * (2 * Math.PI)) / (duplicates.length + 1);
                  const jitterY = duplicateIndex > 0 ? Math.sin(angle) * jitterRadius : 0;
                  
                  return {
                    ...entry,
                    // Keep original percentage - no jitter on x-axis
                    percentage: entry.originalPercentage,
                    count: entry.count + jitterY // Only add jitter to count
                  };
                });
                
                // Use original percentages for domain calculation
                const originalPercentages = scatterData.map(e => e.originalPercentage);
                const minPercentage = Math.min(...originalPercentages);
                const maxPercentage = Math.max(...originalPercentages);
                
                return (
                  <>
                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart
                        margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                        <XAxis
                          type="number"
                          dataKey="percentage"
                          name="Percentage"
                          domain={[Math.max(0, minPercentage - 2), maxPercentage + 2]}
                          tick={{ fill: colors.foreground, fontSize: 12 }}
                          tickFormatter={(value) => `${value.toFixed(1)}%`}
                          tickCount={8}
                          allowDecimals={true}
                          stroke={colors.border}
                          label={{ value: 'Percentage (%)', position: 'insideBottom', offset: -5, fill: colors.foreground, fontSize: 12 }}
                        />
                        <YAxis
                          type="number"
                          dataKey="count"
                          name="Count"
                          domain={[0, 'dataMax + 5']}
                          tick={{ fill: colors.foreground, fontSize: 12 }}
                          stroke={colors.border}
                          label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground, fontSize: 12 }}
                        />
                        <ZAxis
                          type="number"
                          dataKey="size"
                          range={[50, 300]}
                          name="Size"
                        />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div style={{
                                  backgroundColor: colors.card,
                                  border: `2px solid ${primary}`,
                                  borderRadius: '8px',
                                  padding: '12px',
                                  boxShadow: `0 4px 20px rgba(0, 0, 0, 0.8)`,
                                  color: colors.foreground
                                }}>
                                  <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '8px', borderBottom: `1px solid ${colors.border}`, paddingBottom: '4px' }}>
                                    {data.name}
                                  </div>
                                  <div style={{ fontSize: '13px', marginTop: '4px' }}>
                                    <span style={{ color: primary, fontWeight: 'bold' }}>Count:</span> {data.count}
                                  </div>
                                  <div style={{ fontSize: '13px', marginTop: '4px' }}>
                                    <span style={{ color: primary, fontWeight: 'bold' }}>Percentage:</span> {data.originalPercentage.toFixed(1)}%
                                  </div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Scatter
                          name="Fraud Types"
                          data={processedData}
                          fill={primary}
                        >
                          {processedData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                    
                    {/* Custom Legend */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                      gap: '1rem',
                      marginTop: '1rem',
                      padding: '1rem',
                      backgroundColor: colors.card,
                      borderRadius: '8px',
                      border: `1px solid ${colors.border}`
                    }}>
                      {scatterData.map((entry, index) => (
                        <div
                          key={`legend-${index}`}
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '0.75rem',
                            padding: '0.5rem',
                            borderRadius: '6px',
                            transition: 'all 0.2s ease',
                            cursor: 'pointer'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = colors.secondary;
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                          }}
                        >
                          <div
                            style={{
                              width: '14px',
                              height: '14px',
                              borderRadius: '50%',
                              backgroundColor: entry.color,
                              border: `2px solid ${colors.border}`,
                              flexShrink: 0,
                              marginTop: '2px'
                            }}
                          />
                          <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.25rem',
                            flex: 1,
                            minWidth: 0
                          }}>
                            <span style={{
                              color: colors.foreground,
                              fontSize: '13px',
                              fontWeight: '600',
                              lineHeight: '1.4',
                              wordBreak: 'break-word'
                            }}>
                              {entry.name}
                            </span>
                            <span style={{
                              color: colors.mutedForeground,
                              fontSize: '11px',
                              fontWeight: '500',
                              lineHeight: '1.4'
                            }}>
                              {entry.count} cases ({entry.percentage.toFixed(1)}%)
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                );
              })()}
              </div>
            )}
          </div>

          {/* Fraud Trend Over Time - Full Width Below */}
          {csvData.fraudTrendData && csvData.fraudTrendData.length > 0 && (
            <div style={chartBoxStyle}>
              <h3 style={chartTitleStyle}>Fraud Trend Over Time</h3>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={csvData.fraudTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="date" stroke={colors.mutedForeground} />
                  <YAxis yAxisId="left" stroke={colors.mutedForeground} />
                  <YAxis yAxisId="right" orientation="right" stroke={colors.mutedForeground} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.card,
                      border: `1px solid ${colors.border}`,
                      color: colors.foreground
                    }}
                  />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="avgRisk" stroke={primary} strokeWidth={2} name="Avg Risk Score %" />
                  <Line yAxisId="right" type="monotone" dataKey="highRiskCount" stroke="#ef4444" strokeWidth={2} name="High-Risk Count" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BankStatementInsights;

