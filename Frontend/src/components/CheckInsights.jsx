import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Sector,
  ComposedChart
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

const CheckInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('api'); // 'upload' or 'api'
  const [checksList, setChecksList] = useState([]);
  const [loadingChecksList, setLoadingChecksList] = useState(false);
  const [selectedCheckId, setSelectedCheckId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'older', 'custom'
  const [totalRecords, setTotalRecords] = useState(0);
  const [bankFilter, setBankFilter] = useState(null);
  const [availableBanks, setAvailableBanks] = useState([]);
  const [allChecksData, setAllChecksData] = useState([]);
  const [activePieIndex, setActivePieIndex] = useState(null);
  const [activeBarIndex, setActiveBarIndex] = useState(null);
  const [activeBankBarIndex, setActiveBankBarIndex] = useState({ bankIndex: null, series: null });
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
        avgRisk: parseFloat(((data.totalRisk / data.count) * 100).toFixed(1)), // Convert to number for line chart
        count: data.count
      }))
      .sort((a, b) => b.avgRisk - a.avgRisk); // Sort by risk, but show all banks

    // 4. Top High-Risk Payers
    const payerRisks = {};
    rows.forEach(r => {
      const payer = r['PayerName'] || r['payer_name'] || 'Unknown';
      if (payer && payer !== 'Unknown') {
        if (!payerRisks[payer]) {
          payerRisks[payer] = { count: 0, totalRisk: 0, maxRisk: 0 };
        }
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
        payerRisks[payer].count++;
        payerRisks[payer].totalRisk += risk;
        payerRisks[payer].maxRisk = Math.max(payerRisks[payer].maxRisk, risk);
      }
    });
    const topHighRiskPayers = Object.entries(payerRisks)
      .map(([name, data]) => ({
        name: name, // Keep full name, let chart handle display
        fullName: name,
        avgRisk: (data.totalRisk / data.count).toFixed(1),
        count: data.count,
        maxRisk: data.maxRisk.toFixed(1)
      }))
      .filter(item => parseFloat(item.avgRisk) >= 50)
      .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
      .slice(0, 10);

    // 5. Payees with Highest Fraud Incidents (Count of REJECT/ESCALATE or high risk >= 75%)
    const payeeFraudIncidents = {};
    rows.forEach(r => {
      const payee = r['PayeeName'] || r['payee_name'] || 'Unknown';
      if (payee && payee !== 'Unknown') {
        const decision = (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase();
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
        const isFraudulent = decision === 'REJECT' || decision === 'ESCALATE' || risk >= 75;

        if (isFraudulent) {
          if (!payeeFraudIncidents[payee]) {
            payeeFraudIncidents[payee] = 0;
          }
          payeeFraudIncidents[payee]++;
        }
      }
    });
    const topFraudIncidentPayees = Object.entries(payeeFraudIncidents)
      .map(([name, fraudCount]) => ({
        name: name,
        fraudCount: fraudCount
      }))
      .filter(item => item.fraudCount > 0)
      .sort((a, b) => b.fraudCount - a.fraudCount)
      .slice(0, 10);

    // 6. Fraud Over Time (High-Risk Count and Avg Risk)
    const fraudOverTime = {};
    rows.forEach(r => {
      const dateStr = r['CheckDate'] || r['check_date'] || r['created_at'] || '';
      if (dateStr) {
        const date = dateStr.split('T')[0];
        if (!fraudOverTime[date]) {
          fraudOverTime[date] = { count: 0, highRiskCount: 0, totalRisk: 0 };
        }
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
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



    // 9. Repeat Offenders (Payers with multiple high-risk checks)
    const repeatOffenders = Object.entries(payerRisks)
      .filter(([name, data]) => data.count > 1 && parseFloat((data.totalRisk / data.count).toFixed(1)) >= 50)
      .length;


    // 11. High-Risk Count (>75%)
    const highRiskCount = riskScoresPercent.filter(s => s >= 75).length;

    // 12. Summary Metrics
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
      topHighRiskPayers,
      topFraudIncidentPayees, // Payees with highest fraud incidents
      fraudTrendData,
      metrics: {
        totalChecks,
        avgRiskScore,
        approveCount,
        rejectCount,
        escalateCount,
        highRiskCount,
        repeatOffenders
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

  const fetchChecksList = async (filter = null, bank = null, customRange = null) => {
    setLoadingChecksList(true);
    setError(null);
    setCsvData(null);
    try {
      // Use relative URL to leverage proxy in package.json
      let url = '/api/checks/list';

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
        // Store all fetched data
        setAllChecksData(fetchedData);

        // Extract unique banks from the data
        const uniqueBanks = [...new Set(fetchedData.map(check => check.bank_name).filter(Boolean))].sort();
        setAvailableBanks(uniqueBanks);

        // Apply bank filter if specified
        let filteredData = fetchedData;
        if (bank) {
          filteredData = fetchedData.filter(check => check.bank_name === bank);
          setBankFilter(bank);
        } else {
          setBankFilter(null);
        }

        setChecksList(filteredData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(filter);
        // Auto-load all checks as insights if data exists
        if (filteredData.length > 0) {
          loadCheckData(filteredData);
        } else {
          setError('No checks found for the selected filters');
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

  const handleSearchChecks = async (query) => {
    if (!query) {
      setBankFilter(null);
      fetchChecksList(dateFilter);
      return;
    }
    setLoadingChecksList(true);
    setError(null);
    setCsvData(null);
    try {
      // Use relative URL to leverage proxy in package.json
      const response = await fetch(`/api/checks/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setChecksList(data.data);
        // Auto-load search results as insights if data exists
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

  const loadCheckData = async (checks) => {
    if (!checks || checks.length === 0) {
      setError('No checks selected');
      return;
    }

    try {
      // Transform database records to format expected by processData
      const rows = checks.map(check => ({
        'fraud_risk_score': check.fraud_risk_score || 0,
        'RiskScore': check.fraud_risk_score || 0,
        'ai_recommendation': check.ai_recommendation || 'UNKNOWN',
        'Decision': check.ai_recommendation || 'UNKNOWN',
        'bank_name': check.bank_name || 'Unknown',
        'BankName': check.bank_name || 'Unknown',
        'check_number': check.check_number || 'N/A',
        'CheckNumber': check.check_number || 'N/A',
        'amount': check.amount || 0,
        'Amount': check.amount || 0,
        'payer_name': check.payer_name || '',
        'PayerName': check.payer_name || '',
        'payee_name': check.payee_name || '',
        'PayeeName': check.payee_name || '',
        'check_date': check.check_date || '',
        'CheckDate': check.check_date || '',
        'created_at': check.created_at || check.timestamp || '',
        'model_confidence': check.model_confidence || 0,
        'Confidence': check.model_confidence || 0,
        'confidence': check.model_confidence || 0,
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

  // Auto-fetch data when component mounts in 'api' mode
  useEffect(() => {
    if (inputMode === 'api' && allChecksData.length === 0 && !loadingChecksList) {
      fetchChecksList();
    }
  }, []); // Empty dependency array - only run on mount

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

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

  const chartContainerStyle = {
    marginBottom: '2rem',
    padding: '1.5rem',
    backgroundColor: colors.secondary,
    borderRadius: '0.75rem',
    border: `1px solid ${colors.border}`,
  };

  const chartsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '20px',
    marginTop: '2rem'
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

  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  };

  const metricCardStyle = {
    backgroundColor: colors.secondary,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    textAlign: 'center',
  };

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
          {inputMode === 'upload' ? 'Check Insights from CSV' : 'Check Insights from Database'}
        </h2>



        {inputMode === 'api' && (
          <>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
                Search by Payer Name:
              </label>
              <input
                type="text"
                placeholder="Search checks by payer name..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  handleSearchChecks(e.target.value);
                }}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  backgroundColor: colors.secondary,
                  color: colors.foreground,
                  border: `1px solid ${colors.border}`,
                  fontSize: '1rem',
                }}
              />
            </div>

            {/* Date Filter Section */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.75rem', fontWeight: '500' }}>
                Filter by Created Date {totalRecords > 0 && <span style={{ color: colors.mutedForeground, fontWeight: '400', fontSize: '0.9rem' }}>({totalRecords} total records)</span>}
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem' }}>
                <button
                  onClick={() => fetchChecksList(null, bankFilter)}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    backgroundColor: dateFilter === null ? primary : colors.secondary,
                    color: dateFilter === null ? colors.primaryForeground : colors.foreground,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer',
                    fontWeight: dateFilter === null ? '600' : '500',
                    transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => !loadingChecksList && dateFilter !== null && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingChecksList && dateFilter !== null && (e.target.style.backgroundColor = colors.secondary)}
                >
                  All Records
                </button>
                <button
                  onClick={() => fetchChecksList('last_30', bankFilter)}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    backgroundColor: dateFilter === 'last_30' ? primary : colors.secondary,
                    color: dateFilter === 'last_30' ? colors.primaryForeground : colors.foreground,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer',
                    fontWeight: dateFilter === 'last_30' ? '600' : '500',
                    transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Last 30
                </button>
                <button
                  onClick={() => fetchChecksList('last_60', bankFilter)}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    backgroundColor: dateFilter === 'last_60' ? primary : colors.secondary,
                    color: dateFilter === 'last_60' ? colors.primaryForeground : colors.foreground,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer',
                    fontWeight: dateFilter === 'last_60' ? '600' : '500',
                    transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Last 60
                </button>
                <button
                  onClick={() => fetchChecksList('last_90', bankFilter)}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    backgroundColor: dateFilter === 'last_90' ? primary : colors.secondary,
                    color: dateFilter === 'last_90' ? colors.primaryForeground : colors.foreground,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer',
                    fontWeight: dateFilter === 'last_90' ? '600' : '500',
                    transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Last 90
                </button>
                <button
                  onClick={() => fetchChecksList('older', bankFilter)}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    backgroundColor: dateFilter === 'older' ? primary : colors.secondary,
                    color: dateFilter === 'older' ? colors.primaryForeground : colors.foreground,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer',
                    fontWeight: dateFilter === 'older' ? '600' : '500',
                    transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Older
                </button>
                <button
                  onClick={() => setShowCustomDatePicker(!showCustomDatePicker)}
                  style={{
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    backgroundColor: dateFilter === 'custom' ? primary : colors.secondary,
                    color: dateFilter === 'custom' ? colors.primaryForeground : colors.foreground,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer',
                    fontWeight: dateFilter === 'custom' ? '600' : '500',
                    transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'custom' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'custom' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Custom Range
                </button>
              </div>

              {/* Custom Date Range Picker */}
              {showCustomDatePicker && (
                <div style={{
                  marginTop: '1rem',
                  padding: '1.5rem',
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '0.5rem',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
                }}>
                  <div style={{ marginBottom: '1rem', fontWeight: '600', color: colors.foreground }}>
                    Select Custom Date Range
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                    <div style={{ flex: '1', minWidth: '200px' }}>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '14px', color: colors.mutedForeground }}>
                        Start Date
                      </label>
                      <input
                        type="date"
                        value={customDateRange.startDate}
                        onChange={(e) => setCustomDateRange({ ...customDateRange, startDate: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          borderRadius: '0.5rem',
                          border: `1px solid ${colors.border}`,
                          fontSize: '14px',
                          backgroundColor: colors.secondary,
                          color: colors.foreground
                        }}
                      />
                    </div>
                    <div style={{ flex: '1', minWidth: '200px' }}>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '14px', color: colors.mutedForeground }}>
                        End Date
                      </label>
                      <input
                        type="date"
                        value={customDateRange.endDate}
                        onChange={(e) => setCustomDateRange({ ...customDateRange, endDate: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          borderRadius: '0.5rem',
                          border: `1px solid ${colors.border}`,
                          fontSize: '14px',
                          backgroundColor: colors.secondary,
                          color: colors.foreground
                        }}
                      />
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
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
                          fetchChecksList(null, bankFilter, customDateRange);
                        }}
                        style={{
                          padding: '0.75rem 1.5rem',
                          borderRadius: '0.5rem',
                          backgroundColor: primary,
                          color: colors.primaryForeground,
                          border: 'none',
                          cursor: 'pointer',
                          fontWeight: '600',
                          transition: 'all 0.3s',
                        }}
                      >
                        Apply
                      </button>
                      <button
                        onClick={() => {
                          setShowCustomDatePicker(false);
                          setCustomDateRange({ startDate: '', endDate: '' });
                        }}
                        style={{
                          padding: '0.75rem 1.5rem',
                          borderRadius: '0.5rem',
                          backgroundColor: colors.secondary,
                          color: colors.foreground,
                          border: `1px solid ${colors.border}`,
                          cursor: 'pointer',
                          fontWeight: '600',
                          transition: 'all 0.3s',
                        }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Bank Filter Section */}
            {availableBanks.length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
                  Filter by Bank:
                </label>
                <select
                  value={bankFilter || ''}
                  onChange={(e) => {
                    const selectedBank = e.target.value || null;
                    setBankFilter(selectedBank);
                    // Filter from full dataset by bank
                    if (selectedBank) {
                      const filtered = allChecksData.filter(check => check.bank_name === selectedBank);
                      setChecksList(filtered);
                      if (filtered.length > 0) {
                        loadCheckData(filtered);
                      } else {
                        setError('No checks found for this bank');
                      }
                    } else {
                      // Show all data from current fetch
                      setChecksList(allChecksData);
                      if (allChecksData.length > 0) {
                        loadCheckData(allChecksData);
                      } else {
                        fetchChecksList(dateFilter);
                      }
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    borderRadius: '0.5rem',
                    backgroundColor: colors.secondary,
                    color: colors.foreground,
                    border: `1px solid ${colors.border}`,
                    fontSize: '1rem',
                    cursor: 'pointer',
                    appearance: 'none',
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='${encodeURIComponent(colors.foreground)}' d='M6 9L1 4h10z'/%3E%3C/svg%3E")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 0.75rem center',
                    paddingRight: '2.5rem',
                  }}
                >
                  <option value="">All Banks</option>
                  {availableBanks.map((bank) => (
                    <option key={bank} value={bank}>
                      {bank}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {loadingChecksList ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <FaCog className="spin" style={{ fontSize: '2rem', color: primary }} />
                <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>Loading checks...</p>
              </div>
            ) : checksList.length > 0 ? (
              <div style={{
                backgroundColor: colors.secondary,
                borderRadius: '0.5rem',
                border: `1px solid ${colors.border}`,
                maxHeight: '400px',
                overflowY: 'auto',
                marginBottom: '1rem',
              }}>
                {checksList.map((check) => (
                  <div
                    key={check.check_id}
                    onClick={() => {
                      setSelectedCheckId(check.check_id);
                      loadCheckData(checksList.filter(c => c.check_id === check.check_id));
                    }}
                    style={{
                      padding: '1rem',
                      borderBottom: `1px solid ${colors.border}`,
                      cursor: 'pointer',
                      transition: 'background-color 0.3s',
                      backgroundColor: selectedCheckId === check.check_id ? colors.muted : 'transparent',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = colors.muted)}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = selectedCheckId === check.check_id ? colors.muted : 'transparent')}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <p style={{ color: colors.foreground, fontWeight: '600', margin: '0 0 0.25rem 0' }}>
                          {check.payer_name || 'Unknown Payer'}
                        </p>
                        <p style={{ color: colors.mutedForeground, fontSize: '0.875rem', margin: '0' }}>
                          Check #{check.check_number || 'N/A'} • ${check.amount || 'N/A'}
                        </p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{
                          backgroundColor: check.fraud_risk_score > 0.5 ? `${primary}20` : `${colors.status.success}20`,
                          color: check.fraud_risk_score > 0.5 ? primary : colors.status.success,
                          padding: '0.25rem 0.75rem',
                          borderRadius: '0.25rem',
                          fontSize: '0.875rem',
                          fontWeight: '600',
                        }}>
                          {((check.fraud_risk_score || 0) * 100).toFixed(0)}% Risk
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                backgroundColor: colors.muted,
                padding: '2rem',
                borderRadius: '0.5rem',
                textAlign: 'center',
                color: colors.mutedForeground,
                marginBottom: '1rem',
              }}>
                <p>No checks found in database</p>
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
      </div>

      {csvData && (
        <div data-metrics-section>
          {/* Summary Metrics */}
          <div style={cardStyle}>
            <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>Summary Metrics</h2>
            <div style={metricsGridStyle}>
              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {csvData.metrics.totalChecks}
                </div>
                <div style={{ color: colors.mutedForeground }}>Total Checks</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {csvData.metrics.avgRiskScore}%
                </div>
                <div style={{ color: colors.mutedForeground }}>Avg Risk Score</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981', marginBottom: '0.5rem' }}>
                  {csvData.metrics.approveCount}
                </div>
                <div style={{ color: colors.mutedForeground }}>Approve</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ef4444', marginBottom: '0.5rem' }}>
                  {csvData.metrics.rejectCount}
                </div>
                <div style={{ color: colors.mutedForeground }}>Reject</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b', marginBottom: '0.5rem' }}>
                  {csvData.metrics.escalateCount}
                </div>
                <div style={{ color: colors.mutedForeground }}>Escalate</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {csvData.metrics.highRiskCount || 0}
                </div>
                <div style={{ color: colors.mutedForeground }}>High-Risk Count (&gt;75%)</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {csvData.metrics.repeatOffenders || 0}
                </div>
                <div style={{ color: colors.mutedForeground }}>Repeat Offenders</div>
              </div>
            </div>
          </div>

          {/* Charts Section - 3 rows x 2 columns grid */}
          <div style={chartsContainerStyle}>
            {/* Row 1: Risk Score Distribution & AI Recommendation Breakdown */}
            <div style={chartBoxStyle}>
              <h3 style={chartTitleStyle}>Risk Score Distribution by Range</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart
                  data={csvData.riskDistribution}
                  margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
                  onMouseLeave={() => setActiveBarIndex(null)}
                >
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
                        const data = payload[0];
                        return (
                          <div style={{
                            backgroundColor: colors.card,
                            border: `1px solid ${colors.border}`,
                            borderRadius: '8px',
                            padding: '12px',
                            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                          }}>
                            <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                              {data.payload.range}
                            </p>
                            <p style={{ margin: '4px 0', color: primary }}>
                              <span style={{ fontWeight: '600' }}>Count:</span> {data.value}
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                    cursor={{ fill: 'transparent' }}
                  />
                  <Bar
                    dataKey="count"
                    fill="url(#riskGradient)"
                    radius={[8, 8, 0, 0]}
                  >
                    {csvData.riskDistribution.map((entry, index) => {
                      const isActive = activeBarIndex === index;
                      return (
                        <Cell
                          key={`cell-${index}`}
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

            <div style={chartBoxStyle}>
              <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
              {/* Centered Donut Chart */}
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '320px' }}>
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart
                    onMouseLeave={() => setActivePieIndex(null)}
                  >
                    <Pie
                      data={csvData.recommendationData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={false}
                      outerRadius={120}
                      innerRadius={60}
                      fill="#8884d8"
                      dataKey="value"
                      stroke={colors.card}
                      strokeWidth={3}
                      startAngle={90}
                      endAngle={-270}
                      activeIndex={activePieIndex}
                      activeShape={(props) => {
                        const {
                          cx, cy, innerRadius, outerRadius, startAngle, endAngle,
                          fill
                        } = props;
                        return (
                          <g>
                            <Sector
                              cx={cx}
                              cy={cy}
                              innerRadius={innerRadius - 5}
                              outerRadius={outerRadius + 20}
                              startAngle={startAngle}
                              endAngle={endAngle}
                              fill={fill}
                              stroke={colors.card}
                              strokeWidth={3}
                            />
                          </g>
                        );
                      }}
                      onMouseEnter={(_, index) => setActivePieIndex(index)}
                      onMouseLeave={() => setActivePieIndex(null)}
                    >
                      {csvData.recommendationData.map((entry, index) => {
                        const colorMap = {
                          'APPROVE': colors.status.success || '#4CAF50',
                          'REJECT': primary,
                          'ESCALATE': colors.status.warning || '#FFA726'
                        };
                        const baseColor = colorMap[entry.name] || COLORS[index % COLORS.length];
                        const isActive = activePieIndex === index;

                        return (
                          <Cell
                            key={`cell-${index}`}
                            fill={baseColor}
                            style={{
                              filter: isActive ? 'brightness(1.2)' : 'brightness(1)',
                              transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                              cursor: 'pointer'
                            }}
                          />
                        );
                      })}
                    </Pie>
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0];
                          const total = csvData.recommendationData.reduce((sum, item) => sum + item.value, 0);
                          const percentage = total > 0 ? ((data.payload.value / total) * 100).toFixed(2) : 0;
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
                                <span style={{ fontWeight: '600' }}>Count:</span> {data.payload.value}
                              </p>
                              <p style={{ margin: '4px 0', color: data.color }}>
                                <span style={{ fontWeight: '600' }}>Percentage:</span> {percentage}%
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Legend below the chart */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '2rem',
                marginTop: '1.5rem',
                padding: '1rem',
                flexWrap: 'wrap'
              }}>
                {csvData.recommendationData.map((entry, index) => {
                  const colorMap = {
                    'APPROVE': colors.status.success || '#4CAF50',
                    'REJECT': primary,
                    'ESCALATE': colors.status.warning || '#FFA726'
                  };
                  const total = csvData.recommendationData.reduce((sum, item) => sum + item.value, 0);
                  const percentage = total > 0 ? ((entry.value / total) * 100).toFixed(2) : 0;

                  return (
                    <div
                      key={`legend-${index}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem'
                      }}
                    >
                      <div
                        style={{
                          width: '16px',
                          height: '16px',
                          borderRadius: '50%',
                          backgroundColor: colorMap[entry.name] || primary,
                          flexShrink: 0,
                          border: `2px solid ${colors.card}`
                        }}
                      />
                      <span style={{
                        color: colors.foreground,
                        fontSize: '14px',
                        fontWeight: '500'
                      }}>
                        {entry.name}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Row 2: Risk by Bank (Combined Bar + Line) & Top High-Risk Payers */}
            {!bankFilter && csvData.riskByBankData && csvData.riskByBankData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Level by Bank</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <ComposedChart
                    data={csvData.riskByBankData.map(bank => ({
                      ...bank,
                      displayName: (() => {
                        const name = bank.name.toUpperCase();
                        if (name.includes('BANK OF AMERICA') || name.includes('BOFA')) return 'BOFA';
                        if (name.includes('CHASE') || name.includes('JPM')) return 'JPMC';
                        if (name.includes('WELLS FARGO') || name.includes('WELLS')) return 'WF';
                        if (name.includes('CITIBANK') || name.includes('CITI')) return 'CITI';
                        if (name.includes('US BANK')) return 'USB';
                        if (name.includes('ALLY')) return 'ALLY';
                        // Return shortened version if name is too long
                        return bank.name.length > 10 ? bank.name.substring(0, 10) + '...' : bank.name;
                      })()
                    }))}
                    margin={{ top: 10, right: 30, left: 10, bottom: 60 }}
                    onMouseLeave={() => setActiveBankBarIndex({ bankIndex: null, series: null })}
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
                      label={{ value: 'Check Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
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
                      name="Check Count"
                    >
                      {csvData.riskByBankData.map((entry, index) => {
                        const isActive = activeBankBarIndex.bankIndex === index && activeBankBarIndex.series === 'count';
                        return (
                          <Cell
                            key={`count-cell-${index}`}
                            fill={isActive ? "url(#countGradientHover)" : "url(#countGradient)"}
                            onMouseEnter={() => setActiveBankBarIndex({ bankIndex: index, series: 'count' })}
                            onMouseLeave={() => setActiveBankBarIndex({ bankIndex: null, series: null })}
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

            {csvData.topHighRiskPayers && csvData.topHighRiskPayers.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Top High-Risk Payers</h3>
                <ResponsiveContainer width="100%" height={Math.max(320, csvData.topHighRiskPayers.length * 40)}>
                  <BarChart
                    data={csvData.topHighRiskPayers}
                    layout="vertical"
                    margin={{ left: 120, right: 60, top: 10, bottom: 10 }}
                  >
                    <defs>
                      <linearGradient id="heatGradientHigh" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#ef4444" stopOpacity={1} />
                        <stop offset="100%" stopColor="#ef4444" stopOpacity={0.8} />
                      </linearGradient>
                      <linearGradient id="heatGradientMedium" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity={1} />
                        <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.8} />
                      </linearGradient>
                      <linearGradient id="heatGradientLow" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#eab308" stopOpacity={1} />
                        <stop offset="100%" stopColor="#eab308" stopOpacity={0.8} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} horizontal={false} />
                    <XAxis
                      type="number"
                      domain={[0, 100]}
                      tick={{ fill: colors.foreground, fontSize: 11 }}
                      stroke={colors.border}
                      label={{ value: 'Risk Score (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                    />
                    <YAxis
                      dataKey="name"
                      type="category"
                      stroke={colors.border}
                      width={110}
                      tick={{ fill: colors.foreground, fontSize: 11 }}
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
                              <p style={{ margin: '4px 0', color: primary }}>
                                <span style={{ fontWeight: '600' }}>Avg Risk:</span> {data.avgRisk}%
                              </p>
                              <p style={{ margin: '4px 0', color: colors.mutedForeground }}>
                                <span style={{ fontWeight: '600' }}>Checks:</span> {data.count}
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                      cursor={{ fill: 'transparent' }}
                    />
                    <Bar
                      dataKey="avgRisk"
                      barSize={12}
                      radius={[0, 4, 4, 0]}
                      label={({ value, x, y, width }) => {
                        return (
                          <text
                            x={x + width + 5}
                            y={y + 6}
                            fill={colors.foreground}
                            fontSize={12}
                            fontWeight="600"
                            textAnchor="start"
                          >
                            {parseFloat(value).toFixed(0)}%
                          </text>
                        );
                      }}
                    >
                      {csvData.topHighRiskPayers.map((entry, index) => {
                        const risk = parseFloat(entry.avgRisk);
                        let gradientId = 'heatGradientLow';
                        if (risk >= 75) gradientId = 'heatGradientHigh';
                        else if (risk >= 50) gradientId = 'heatGradientMedium';

                        return (
                          <Cell
                            key={`heat-cell-${index}`}
                            fill={`url(#${gradientId})`}
                          />
                        );
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Row 3: Payees with Highest Fraud Incidents (Bullet Chart) & Fraud Trend Over Time */}
            {csvData.topFraudIncidentPayees && csvData.topFraudIncidentPayees.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Payees with Highest Fraud Incidents</h3>
                <div style={{ padding: '1rem' }}>
                  {csvData.topFraudIncidentPayees.map((payee, index) => {
                    const maxCount = Math.max(...csvData.topFraudIncidentPayees.map(p => p.fraudCount));
                    const barWidth = (payee.fraudCount / maxCount) * 100;
                    let barColor = '#FFB59E'; // Low Fraud Level - Pastel Faded Peach (<=20)
                    if (payee.fraudCount >= 60) barColor = '#FF6B5A'; // High Fraud Level - Soft Coral-Red (>=60)
                    else if (payee.fraudCount > 20) barColor = '#FF8A75'; // Medium Fraud Level - Faded Coral (>20 and <60)

                    return (
                      <div
                        key={`payee-bullet-${index}`}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          marginBottom: '1rem',
                          gap: '1rem'
                        }}
                      >
                        <div style={{
                          minWidth: '180px',
                          fontSize: '13px',
                          fontWeight: '500',
                          color: colors.foreground,
                          textAlign: 'right'
                        }}>
                          {payee.name.length > 20 ? payee.name.substring(0, 20) + '...' : payee.name}
                        </div>
                        <div style={{
                          flex: 1,
                          position: 'relative',
                          height: '24px',
                          backgroundColor: colors.secondary,
                          borderRadius: '4px',
                          overflow: 'hidden',
                          border: `1px solid ${colors.border}`
                        }}>
                          <div style={{
                            width: `${barWidth}%`,
                            height: '100%',
                            backgroundColor: barColor,
                            borderRadius: '4px',
                            transition: 'width 0.3s ease'
                          }} />
                        </div>
                        <div style={{
                          minWidth: '40px',
                          fontSize: '14px',
                          fontWeight: '600',
                          color: colors.foreground,
                          textAlign: 'left'
                        }}>
                          {payee.fraudCount}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

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

        </div>
      )}
    </div>
  );
};

export default CheckInsights;
