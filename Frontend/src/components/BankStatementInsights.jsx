import { useState, useCallback } from 'react';
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

    // 4. Fraud Trend Over Time
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

    // 5. Summary Metrics
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
      const rows = bankStatements.map(bs => ({
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
      }));

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
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => fetchBankStatementsList('last_30', bankFilter)}
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
              >
                Last 30
              </button>
              <button
                onClick={() => fetchBankStatementsList('last_60', bankFilter)}
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
              >
                Last 60
              </button>
              <button
                onClick={() => fetchBankStatementsList('last_90', bankFilter)}
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
              >
                Last 90
              </button>
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
                High Risk Count
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {csvData.metrics.highRiskCount}
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
                <ResponsiveContainer width="100%" height={320}>
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

            {/* Fraud Trend Over Time */}
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

export default BankStatementInsights;

