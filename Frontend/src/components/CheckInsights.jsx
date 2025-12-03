import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { FaUpload, FaCog } from 'react-icons/fa';

const CheckInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('upload'); // 'upload' or 'api'
  const [checksList, setChecksList] = useState([]);
  const [loadingChecksList, setLoadingChecksList] = useState(false);
  const [selectedCheckId, setSelectedCheckId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'older'
  const [totalRecords, setTotalRecords] = useState(0);
  const [bankFilter, setBankFilter] = useState(null);
  const [availableBanks, setAvailableBanks] = useState([]);
  const [allChecksData, setAllChecksData] = useState([]);

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
        avgRisk: ((data.totalRisk / data.count) * 100).toFixed(1),
        count: data.count
      }))
      .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
      .slice(0, 10); // Top 10 banks

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

    // 5. Top High-Risk Payees
    const payeeRisks = {};
    rows.forEach(r => {
      const payee = r['PayeeName'] || r['payee_name'] || 'Unknown';
      if (payee && payee !== 'Unknown') {
        if (!payeeRisks[payee]) {
          payeeRisks[payee] = { count: 0, totalRisk: 0 };
        }
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
        payeeRisks[payee].count++;
        payeeRisks[payee].totalRisk += risk;
      }
    });
    const topHighRiskPayees = Object.entries(payeeRisks)
      .map(([name, data]) => ({
        name: name, // Keep full name, let chart handle display
        fullName: name,
        avgRisk: (data.totalRisk / data.count).toFixed(1),
        count: data.count
      }))
      .filter(item => parseFloat(item.avgRisk) >= 50)
      .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
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
      topHighRiskPayees,
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

  const fetchChecksList = async (filter = null, bank = null) => {
    setLoadingChecksList(true);
    setError(null);
    setCsvData(null);
    try {
      // Use relative URL to leverage proxy in package.json
      const url = filter
        ? `/api/checks/list?date_filter=${filter}`
        : `/api/checks/list`;
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

        {/* Input Mode Toggle */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <button
            onClick={() => {
              setInputMode('upload');
              setCsvData(null);
              setError(null);
            }}
            style={{
              flex: 1,
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: inputMode === 'upload' ? primary : colors.secondary,
              color: inputMode === 'upload' ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: inputMode === 'upload' ? '600' : '500',
              transition: 'all 0.3s',
            }}
          >
            Upload CSV
          </button>
          <button
            onClick={() => {
              setInputMode('api');
              setCsvData(null);
              setError(null);
              setBankFilter(null);
              setAllChecksData([]);
              fetchChecksList();
            }}
            style={{
              flex: 1,
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: inputMode === 'api' ? primary : colors.secondary,
              color: inputMode === 'api' ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: inputMode === 'api' ? '600' : '500',
              transition: 'all 0.3s',
            }}
          >
            Live Data
          </button>
        </div>

        {inputMode === 'upload' && (
          <>
            <div {...getRootProps()} style={dropzoneStyle}>
              <input {...getInputProps()} />
              <FaUpload style={{ fontSize: '2rem', marginBottom: '1rem', color: colors.foreground }} />
              {isDragActive ? (
                <p style={{ color: primary, fontWeight: '500' }}>
                  Drop the CSV file here...
                </p>
              ) : (
                <div>
                  <p style={{ color: colors.foreground, marginBottom: '0.5rem' }}>
                    Drag and drop your CSV file here, or click to browse
                  </p>
                  <p style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
                    CSV file with check analysis data
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
              </div>
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
            </div>

            <div style={chartBoxStyle}>
              <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={csvData.recommendationData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={100}
                    innerRadius={40}
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
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Row 2: Risk by Bank & Top High-Risk Payers */}
            {!bankFilter && csvData.riskByBankData && csvData.riskByBankData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Level by Bank</h3>
                <ResponsiveContainer width="100%" height={320}>
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
              </div>
            )}

            {csvData.topHighRiskPayers && csvData.topHighRiskPayers.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Top High-Risk Payers</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={csvData.topHighRiskPayers} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                    <XAxis 
                      type="number" 
                      stroke={colors.mutedForeground}
                      label={{ value: 'Average Risk Score (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                    />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      stroke={colors.mutedForeground} 
                      width={180}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: colors.card,
                        border: `1px solid ${colors.border}`,
                        color: colors.foreground
                      }}
                      formatter={(value, name) => {
                        if (name === 'avgRisk') return [`${value}%`, 'Avg Risk'];
                        if (name === 'count') return [value, 'Checks'];
                        return [value, name];
                      }}
                      labelFormatter={(label) => `Payer: ${label}`}
                    />
                    <Bar dataKey="avgRisk" fill={primary} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Row 3: Top High-Risk Payees & Fraud Trend Over Time */}
            {csvData.topHighRiskPayees && csvData.topHighRiskPayees.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Top High-Risk Payees</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={csvData.topHighRiskPayees} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                    <XAxis 
                      type="number" 
                      stroke={colors.mutedForeground}
                      label={{ value: 'Average Risk Score (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                    />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      stroke={colors.mutedForeground} 
                      width={180}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: colors.card,
                        border: `1px solid ${colors.border}`,
                        color: colors.foreground
                      }}
                      formatter={(value, name) => {
                        if (name === 'avgRisk') return [`${value}%`, 'Avg Risk'];
                        if (name === 'count') return [value, 'Checks'];
                        return [value, name];
                      }}
                      labelFormatter={(label) => `Payee: ${label}`}
                    />
                    <Bar dataKey="avgRisk" fill={primary} />
                  </BarChart>
                </ResponsiveContainer>
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
