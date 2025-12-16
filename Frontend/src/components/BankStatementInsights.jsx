import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Sector,
  ComposedChart, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { FaUpload, FaCog, FaRedo } from 'react-icons/fa';

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
  const [inputMode, setInputMode] = useState('api'); // 'upload' or 'api'
  const [bankStatementsList, setBankStatementsList] = useState([]);
  const [loadingBankStatementsList, setLoadingBankStatementsList] = useState(false);
  const [selectedBankStatementId, setSelectedBankStatementId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'older', 'custom'
  const [totalRecords, setTotalRecords] = useState(0);
  const [bankFilter, setBankFilter] = useState(null);
  const [fraudTypeFilter, setFraudTypeFilter] = useState(null);
  const [availableBanks, setAvailableBanks] = useState([]);
  const [availableFraudTypes, setAvailableFraudTypes] = useState([]);
  const [allBankStatementsData, setAllBankStatementsData] = useState([]);
  const [activePieIndex, setActivePieIndex] = useState(null);
  const [activeBarIndex, setActiveBarIndex] = useState(null);
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [customDateRange, setCustomDateRange] = useState({ startDate: '', endDate: '' });

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
        avgRisk: parseFloat((data.totalRisk / data.count).toFixed(1)),
        count: data.count
      }))
      .sort((a, b) => b.avgRisk - a.avgRisk)
      .slice(0, 5) // Only take top 5 highest-risk banks
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

    // 6. Top Risk Customers (by account holder)
    const customerRisks = {};
    rows.forEach(r => {
      const accountHolder = (r['Account Holder'] || r['account_holder'] || 'Unknown').trim();
      const risk = parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
      if (accountHolder && accountHolder !== 'Unknown') {
        if (!customerRisks[accountHolder]) {
          customerRisks[accountHolder] = { count: 0, totalRisk: 0, maxRisk: 0 };
        }
        customerRisks[accountHolder].count++;
        customerRisks[accountHolder].totalRisk += risk;
        customerRisks[accountHolder].maxRisk = Math.max(customerRisks[accountHolder].maxRisk, risk);
      }
    });
    const topRiskCustomers = Object.entries(customerRisks)
      .map(([name, data]) => ({
        name: name.length > 20 ? name.substring(0, 20) + '...' : name,
        fullName: name,
        avgRisk: parseFloat((data.totalRisk / data.count).toFixed(1)),
        maxRisk: parseFloat(data.maxRisk.toFixed(1)),
        count: data.count
      }))
      .sort((a, b) => b.avgRisk - a.avgRisk)
      .slice(0, 10);

    // 7. Summary Metrics
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
      topRiskCustomers,
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

  const fetchBankStatementsList = async (filter = null, bank = null, customRange = null) => {
    setLoadingBankStatementsList(true);
    setError(null);
    setCsvData(null);
    try {
      // Use relative URL to leverage proxy in package.json
      let url = '/api/bank-statements/list';

      // Build query parameters
      const params = new URLSearchParams();

      if (customRange && (customRange.startDate || customRange.endDate)) {
        // Custom date range takes priority
        if (customRange.startDate) params.append('start_date', customRange.startDate);
        if (customRange.endDate) params.append('end_date', customRange.endDate);
      } else if (filter) {
        // Predefined filter
        params.append('date_filter', filter);
      }

      if (params.toString()) {
        url += '?' + params.toString();
      }

      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        const fetchedData = data.data || [];
        setAllBankStatementsData(fetchedData);

        // Extract unique banks from the data with normalization
        const normalizeBankName = (bankName) => {
          if (!bankName) return null;
          const normalized = bankName.toUpperCase().trim();

          // Map common variations to standard names
          if (normalized.includes('CHASE')) return 'CHASE BANK';
          if (normalized.includes('BANK OF AMERICA') || normalized.includes('BOFA')) return 'BANK OF AMERICA';
          if (normalized.includes('WELLS FARGO')) return 'WELLS FARGO';
          if (normalized.includes('CITI')) return 'CITIBANK';
          if (normalized.includes('US BANK')) return 'US BANK';
          if (normalized.includes('PNC')) return 'PNC BANK';
          if (normalized.includes('TD BANK')) return 'TD BANK';
          if (normalized.includes('CAPITAL ONE')) return 'CAPITAL ONE';
          if (normalized.includes('ALLY')) return 'ALLY BANK';

          return bankName; // Return original if no match
        };

        const uniqueBanks = [...new Set(
          fetchedData
            .map(bs => normalizeBankName(bs.bank_name))
            .filter(Boolean)
        )].sort();
        setAvailableBanks(uniqueBanks);

        // Extract unique fraud types from the data
        const uniqueFraudTypes = [...new Set(
          fetchedData
            .map(bs => bs.fraud_types || bs.fraud_type)
            .filter(Boolean)
            .map(ft => ft.trim())
        )].sort();
        setAvailableFraudTypes(uniqueFraudTypes);

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
        // Don't call loadBankStatementData here - let the useEffect handle it with current filters
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

  // Normalize bank name helper (same as in fetchBankStatementsList)
  const normalizeBankName = (bankName) => {
    if (!bankName) return null;
    const normalized = bankName.toUpperCase().trim();

    // Map common variations to standard names
    if (normalized.includes('CHASE')) return 'CHASE BANK';
    if (normalized.includes('BANK OF AMERICA') || normalized.includes('BOFA')) return 'BANK OF AMERICA';
    if (normalized.includes('WELLS FARGO')) return 'WELLS FARGO';
    if (normalized.includes('CITI')) return 'CITIBANK';
    if (normalized.includes('US BANK')) return 'US BANK';
    if (normalized.includes('PNC')) return 'PNC BANK';
    if (normalized.includes('TD BANK')) return 'TD BANK';
    if (normalized.includes('CAPITAL ONE')) return 'CAPITAL ONE';
    if (normalized.includes('ALLY')) return 'ALLY BANK';

    return bankName; // Return original if no match
  };

  // Filter data based on active filters (similar to CheckInsights)
  const getFilteredData = () => {
    let filtered = allBankStatementsData;

    // Filter by bank (using normalized names)
    if (bankFilter && bankFilter !== '' && bankFilter !== 'All Banks') {
      filtered = filtered.filter(bs => normalizeBankName(bs.bank_name) === bankFilter);
    }

    // Filter by date range
    if (dateFilter) {
      if (dateFilter === 'custom' && (customDateRange.startDate || customDateRange.endDate)) {
        filtered = filtered.filter(bs => {
          const statementDate = new Date(bs.timestamp || bs.created_at);
          const startDate = customDateRange.startDate ? new Date(customDateRange.startDate) : null;
          const endDate = customDateRange.endDate ? new Date(customDateRange.endDate) : null;

          if (startDate && endDate) {
            return statementDate >= startDate && statementDate <= endDate;
          } else if (startDate) {
            return statementDate >= startDate;
          } else if (endDate) {
            return statementDate <= endDate;
          }
          return true;
        });
      } else {
        const now = new Date();
        const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        const sixtyDaysAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000);
        const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);

        filtered = filtered.filter(bs => {
          const statementDate = new Date(bs.timestamp || bs.created_at);
          if (dateFilter === 'last_30') return statementDate >= thirtyDaysAgo;
          if (dateFilter === 'last_60') return statementDate >= sixtyDaysAgo;
          if (dateFilter === 'last_90') return statementDate >= ninetyDaysAgo;
          return true;
        });
      }
    }

    // Filter by fraud type
    if (fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types') {
      filtered = filtered.filter(bs => {
        const fraudType = bs.fraud_types || bs.fraud_type;
        if (!fraudType) return false;
        const normalizedFilter = fraudTypeFilter.toLowerCase().trim();
        const typeStr = String(fraudType || '').trim().toLowerCase();
        return typeStr === normalizedFilter;
      });
    }

    return filtered;
  };

  const filteredData = getFilteredData();

  // Process filtered data on every render (like CheckInsights) - ensures filters always work
  const processedData = (() => {
    if (inputMode === 'api' && filteredData.length > 0) {
      const rows = filteredData.map(bs => {
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
      return processData(rows);
    }
    return null;
  })();

  // Use processedData when available (from filters), fallback to csvData (for CSV upload mode)
  const displayData = processedData || csvData;

  // Auto-fetch data when component mounts in 'api' mode
  useEffect(() => {
    if (inputMode === 'api' && allBankStatementsData.length === 0 && !loadingBankStatementsList) {
      fetchBankStatementsList();
    }
  }, []); // Empty dependency array - only run on mount

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

  // Styles matching CheckInsights
  const filterStyles = {
    filtersSection: {
      display: 'flex',
      gap: '10px',
      marginBottom: '20px',
      alignItems: 'center',
      flexWrap: 'wrap'
    },
    select: {
      padding: '8px 12px',
      border: `1px solid ${colors.border}`,
      borderRadius: '4px',
      fontSize: '14px',
      backgroundColor: colors.card,
      color: colors.foreground,
      cursor: 'pointer'
    },
    recordCount: {
      fontSize: '12px',
      color: colors.mutedForeground,
      whiteSpace: 'nowrap'
    }
  };

  return (
    <div style={containerStyle}>
      {/* Filters Section - Matching CheckInsights Style */}
      {inputMode === 'api' && displayData && (
        <div style={filterStyles.filtersSection}>
          {availableBanks.length > 0 && (
            <select
              value={bankFilter || ''}
              onChange={(e) => setBankFilter(e.target.value || null)}
              style={filterStyles.select}
            >
              <option value="">All Banks</option>
              {availableBanks.map(bank => (
                <option key={bank} value={bank}>{bank}</option>
              ))}
            </select>
          )}

          <select
            value={dateFilter || ''}
            onChange={(e) => {
              const value = e.target.value || null;
              if (value === 'custom') {
                setShowCustomDatePicker(true);
              } else {
                setShowCustomDatePicker(false);
                setDateFilter(value);
              }
            }}
            style={filterStyles.select}
          >
            <option value="">All Time</option>
            <option value="last_30">Last 30 Days</option>
            <option value="last_60">Last 60 Days</option>
            <option value="last_90">Last 90 Days</option>
            <option value="custom">Custom Range</option>
          </select>

          {/* Custom Date Range Picker */}
          {showCustomDatePicker && (
            <div style={{
              gridColumn: '1 / -1',
              padding: '16px',
              backgroundColor: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{ marginBottom: '12px', fontWeight: '600', color: colors.foreground }}>
                Select Custom Date Range
              </div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                <div style={{ flex: '1', minWidth: '180px' }}>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: colors.mutedForeground }}>
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={customDateRange.startDate}
                    onChange={(e) => setCustomDateRange({ ...customDateRange, startDate: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '4px',
                      border: `1px solid ${colors.border}`,
                      fontSize: '13px',
                      backgroundColor: colors.secondary,
                      color: colors.foreground
                    }}
                  />
                </div>
                <div style={{ flex: '1', minWidth: '180px' }}>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: colors.mutedForeground }}>
                    End Date
                  </label>
                  <input
                    type="date"
                    value={customDateRange.endDate}
                    onChange={(e) => setCustomDateRange({ ...customDateRange, endDate: e.target.value })}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '4px',
                      border: `1px solid ${colors.border}`,
                      fontSize: '13px',
                      backgroundColor: colors.secondary,
                      color: colors.foreground
                    }}
                  />
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => {
                      if (!customDateRange.startDate && !customDateRange.endDate) {
                        setError('Please select at least one date');
                        return;
                      }
                      if (customDateRange.startDate && customDateRange.endDate &&
                        customDateRange.startDate > customDateRange.endDate) {
                        setError('Start date must be before end date');
                        return;
                      }
                      setDateFilter('custom');
                      setShowCustomDatePicker(false);
                    }}
                    style={{
                      padding: '8px 20px',
                      borderRadius: '4px',
                      backgroundColor: primary,
                      color: colors.primaryForeground,
                      border: 'none',
                      cursor: 'pointer',
                      fontWeight: '600',
                      fontSize: '13px',
                      transition: 'all 0.2s',
                    }}
                  >
                    Apply
                  </button>
                  <button
                    onClick={() => {
                      setShowCustomDatePicker(false);
                      setCustomDateRange({ startDate: '', endDate: '' });
                      setDateFilter(null);
                    }}
                    style={{
                      padding: '8px 20px',
                      borderRadius: '4px',
                      backgroundColor: colors.secondary,
                      color: colors.foreground,
                      border: `1px solid ${colors.border}`,
                      cursor: 'pointer',
                      fontWeight: '600',
                      fontSize: '13px',
                      transition: 'all 0.2s',
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {availableFraudTypes.length > 0 && (
            <select
              value={fraudTypeFilter || ''}
              onChange={(e) => setFraudTypeFilter(e.target.value || null)}
              style={filterStyles.select}
            >
              <option value="">All Fraud Types</option>
              {availableFraudTypes.map(fraudType => (
                <option key={fraudType} value={fraudType}>{fraudType}</option>
              ))}
            </select>
          )}

          <button
            onClick={() => {
              setSearchQuery('');
              setBankFilter(null);
              setDateFilter(null);
              setFraudTypeFilter(null);
              setCustomDateRange({ startDate: '', endDate: '' });
              setShowCustomDatePicker(false);
              fetchBankStatementsList();
            }}
            style={{
              padding: '8px 16px',
              borderRadius: '4px',
              border: `1px solid ${colors.border}`,
              backgroundColor: colors.secondary,
              color: colors.foreground,
              cursor: 'pointer',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = colors.muted;
              e.target.style.borderColor = primary;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = colors.secondary;
              e.target.style.borderColor = colors.border;
            }}
          >
            <FaRedo /> Reset Filters
          </button>

          <span style={filterStyles.recordCount}>
            Showing {filteredData.length} of {totalRecords} bank statements
          </span>
        </div>
      )}

      {inputMode === 'api' && error && (
        <div style={{
          backgroundColor: colors.accent.redLight,
          color: colors.accent.red,
          padding: '1rem',
          borderRadius: '8px',
          marginTop: '1rem',
          marginBottom: '1rem',
          fontWeight: '500',
        }}>
          {error}
        </div>
      )}

      {/* Show empty state when filters return no data */}
      {inputMode === 'api' && !displayData && allBankStatementsData.length > 0 && (() => {
        const currentFiltered = getFilteredData();
        const hasActiveFilters =
          (bankFilter && bankFilter !== '' && bankFilter !== 'All Banks') ||
          (dateFilter && dateFilter !== null) ||
          (fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types');

        if (hasActiveFilters && currentFiltered.length === 0) {
          return (
            <div data-metrics-section>
              <div style={cardStyle}>
                <div style={{
                  textAlign: 'center',
                  padding: '3rem',
                  color: colors.mutedForeground
                }}>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>No bank statements found for selected filters</h3>
                  <p>Try adjusting your filters to see data.</p>
                </div>
              </div>
            </div>
          );
        }
        return null;
      })()}

      {displayData && (
        <div>
          {/* Summary Metrics */}
          <div data-metrics-section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Total Statements
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {displayData.metrics.totalStatements}
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Avg Risk Score
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {displayData.metrics.avgRiskScore}%
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Approve
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.success }}>
                {displayData.metrics.approveCount}
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Reject
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {displayData.metrics.rejectCount}
              </div>
            </div>
            <div style={chartBoxStyle}>
              <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Escalate
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.warning }}>
                {displayData.metrics.escalateCount}
              </div>
            </div>
          </div>

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '20px' }}>
            {/* AI Recommendation Breakdown */}
            {displayData.recommendationData && displayData.recommendationData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={displayData.recommendationData}
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
                      {displayData.recommendationData.map((entry, index) => (
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
                          const total = displayData.recommendationData.reduce((sum, item) => sum + item.value, 0);
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
                  {displayData.recommendationData.map((entry, index) => (
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
            {displayData.riskDistribution && displayData.riskDistribution.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Score Distribution by Range</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={displayData.riskDistribution} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
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
                      {displayData.riskDistribution.map((entry, index) => {
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

            {/* Risk Level by Bank (Combined Bar + Line) - Hide when bank filter is active */}
            {!bankFilter && displayData.riskByBankData && displayData.riskByBankData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Level by Bank</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <ComposedChart
                    data={displayData.riskByBankData}
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
                      {displayData.riskByBankData.map((entry, index) => {
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

            {/* Fraud Type Distribution - Scatter Plot (hide when fraud type filter is active) */}
            {!fraudTypeFilter && displayData.fraudTypeData && displayData.fraudTypeData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Fraud Type Distribution</h3>
                {(() => {
                  const total = displayData.fraudTypeData.reduce((sum, item) => sum + item.value, 0);
                  const maxValue = Math.max(...displayData.fraudTypeData.map(e => e.value));

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
                  const scatterData = displayData.fraudTypeData.map((entry, index) => {
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

            {/* Top Risk Customers - Show when fraud type OR bank filter is active */}
            {(fraudTypeFilter || bankFilter) && displayData.topRiskCustomers && displayData.topRiskCustomers.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>
                  Top High-Risk Customers
                  {fraudTypeFilter && ` (${fraudTypeFilter})`}
                  {bankFilter && ` at ${bankFilter}`}
                </h3>
                <div style={{ padding: '20px 0' }}>
                  {displayData.topRiskCustomers.map((customer, index) => (
                    <div key={index} style={{ marginBottom: '16px' }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '6px'
                      }}>
                        <span style={{
                          fontSize: '13px',
                          fontWeight: '500',
                          color: colors.foreground,
                          minWidth: '150px',
                          textAlign: 'right',
                          paddingRight: '12px'
                        }}>
                          {customer.fullName}
                        </span>
                        <div style={{
                          flex: 1,
                          height: '28px',
                          backgroundColor: colors.secondary,
                          borderRadius: '4px',
                          position: 'relative',
                          overflow: 'hidden'
                        }}>
                          <div style={{
                            width: `${customer.avgRisk}%`,
                            height: '100%',
                            backgroundColor: primary,
                            borderRadius: '4px',
                            transition: 'width 0.5s ease',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'flex-end',
                            paddingRight: '8px'
                          }}>
                            <span style={{
                              fontSize: '12px',
                              fontWeight: '600',
                              color: colors.primaryForeground || '#fff'
                            }}>
                              {customer.avgRisk}%
                            </span>
                          </div>
                        </div>
                      </div>
                      {/* Subtle info line */}
                      <div style={{
                        fontSize: '11px',
                        color: colors.mutedForeground,
                        textAlign: 'right',
                        paddingRight: '12px',
                        marginTop: '2px'
                      }}>
                        {customer.count} statement{customer.count > 1 ? 's' : ''} • Max risk: {customer.maxRisk}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Fraud Trend Over Time - Full Width Below */}
          {displayData.fraudTrendData && displayData.fraudTrendData.length > 0 && (
            <div style={chartBoxStyle}>
              <h3 style={chartTitleStyle}>Fraud Trend Over Time</h3>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={displayData.fraudTrendData}>
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

