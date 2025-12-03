import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
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

const PaystubInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('upload'); // 'upload' or 'api'
  const [paystubsList, setPaystubsList] = useState([]);
  const [allPaystubsData, setAllPaystubsData] = useState([]);
  const [loadingPaystubsList, setLoadingPaystubsList] = useState(false);
  const [selectedPaystubId, setSelectedPaystubId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'older'
  const [employerFilter, setEmployerFilter] = useState(null);
  const [availableEmployers, setAvailableEmployers] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);

  const parseCSV = (text) => {
    const lines = text.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim());
    const rows = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

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

  const processData = (rows, selectedEmployer = null) => {
    if (!rows.length) return null;

    // Check if we're in single employer view
    const isSingleEmployerView = selectedEmployer && selectedEmployer !== '' && selectedEmployer !== 'All Employers';

    // 1. Fraud Risk Distribution (0-25%, 25-50%, 50-75%, 75-100%)
    const riskScores = rows.map(r => parseFloat_(r['fraud_risk_score'] || 0));
    const riskScoresPercent = riskScores.map(s => s * 100);
    const riskDistribution = [
      { range: '0-25%', count: riskScoresPercent.filter(s => s < 25).length },
      { range: '25-50%', count: riskScoresPercent.filter(s => s >= 25 && s < 50).length },
      { range: '50-75%', count: riskScoresPercent.filter(s => s >= 50 && s < 75).length },
      { range: '75-100%', count: riskScoresPercent.filter(s => s >= 75).length },
    ];

    // 2. AI Recommendation Distribution
    const recommendations = rows.map(r => (r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
    const recommendationData = [
      { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
      { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
      { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
    ].filter(item => item.value > 0);

    // 3. Risk Level Category Distribution
    const riskLevelCounts = {
      'HIGH': 0,
      'MEDIUM': 0,
      'LOW': 0
    };

    riskScoresPercent.forEach(score => {
      if (score >= 70) {
        riskLevelCounts['HIGH']++;
      } else if (score >= 35) {
        riskLevelCounts['MEDIUM']++;
      } else {
        riskLevelCounts['LOW']++;
      }
    });

    const riskLevelData = [
      { name: 'HIGH (70%+)', value: riskLevelCounts['HIGH'], color: colors.accent.red },
      { name: 'MEDIUM (35-70%)', value: riskLevelCounts['MEDIUM'], color: colors.status.warning },
      { name: 'LOW (<35%)', value: riskLevelCounts['LOW'], color: colors.status.success }
    ].filter(item => item.value > 0);

    // 4. Risk by Employer
    const employerRisks = {};
    rows.forEach(r => {
      const employer = r['employer_name'] || 'Unknown';
      if (!employerRisks[employer]) {
        employerRisks[employer] = { count: 0, totalRisk: 0 };
      }
      employerRisks[employer].count++;
      employerRisks[employer].totalRisk += parseFloat_(r['fraud_risk_score'] || 0);
    });

    const riskByEmployerData = Object.entries(employerRisks)
      .map(([name, data]) => ({
        name,
        avgRisk: ((data.totalRisk / data.count) * 100).toFixed(1),
        count: data.count
      }))
      .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
      .slice(0, 10); // Top 10 employers

    // 5. Top High-Risk Employees
    const employeeRisks = {};
    rows.forEach(r => {
      const employee = r['employee_name'] || 'Unknown';
      if (employee && employee !== 'Unknown') {
        if (!employeeRisks[employee]) {
          employeeRisks[employee] = { count: 0, totalRisk: 0, maxRisk: 0 };
        }
        const risk = parseFloat_(r['fraud_risk_score'] || 0) * 100;
        employeeRisks[employee].count++;
        employeeRisks[employee].totalRisk += risk;
        employeeRisks[employee].maxRisk = Math.max(employeeRisks[employee].maxRisk, risk);
      }
    });

    const topHighRiskEmployees = Object.entries(employeeRisks)
      .map(([name, data]) => {
        const avgRisk = parseFloat((data.totalRisk / data.count).toFixed(1));
        return {
          name,
          fullName: name,
          avgRisk: avgRisk, // Store as number for chart
          avgRiskDisplay: avgRisk.toFixed(1), // For display purposes
          count: data.count,
          maxRisk: parseFloat(data.maxRisk.toFixed(1))
        };
      })
      .filter(item => item.avgRisk >= 50)
      .sort((a, b) => b.avgRisk - a.avgRisk)
      .slice(0, 10);

    // 6. Fraud Type Distribution
    const fraudTypeCount = {};
    rows.forEach(r => {
      let fraudType = r['fraud_types'];
      
      // Handle different data formats: string, array, or null/undefined
      if (Array.isArray(fraudType)) {
        // If it's an array, process each element
        fraudType.forEach(ft => {
          const typeStr = String(ft || '').trim();
          if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
            fraudTypeCount[typeStr] = (fraudTypeCount[typeStr] || 0) + 1;
          }
        });
      } else {
        // If it's a string or other type
        const typeStr = String(fraudType || 'No Flag').trim();
        if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined' && typeStr.length > 0) {
          fraudTypeCount[typeStr] = (fraudTypeCount[typeStr] || 0) + 1;
        }
      }
    });

    const fraudTypeData = Object.entries(fraudTypeCount)
      .map(([name, count]) => ({
        name: name.replace(/_/g, ' ').trim() || 'Unknown Fraud Type',
        value: count
      }))
      .filter(item => item.name && item.name !== 'Unknown Fraud Type' || item.value > 0) // Filter out empty names
      .sort((a, b) => b.value - a.value);

    // 7. Income Distribution Stats
    const grossPayValues = rows.map(r => parseFloat_(r['gross_pay'] || 0));
    const netPayValues = rows.map(r => parseFloat_(r['net_pay'] || 0));

    const avgGrossPay = (grossPayValues.reduce((a, b) => a + b, 0) / grossPayValues.length).toFixed(2);
    const avgNetPay = (netPayValues.reduce((a, b) => a + b, 0) / netPayValues.length).toFixed(2);
    const maxGrossPay = Math.max(...grossPayValues).toFixed(2);
    const minGrossPay = Math.min(...grossPayValues).toFixed(2);

    // 8. Summary metrics
    const totalPaystubs = rows.length;
    const avgFraudRisk = ((riskScores.reduce((a, b) => a + b, 0) / riskScores.length) * 100).toFixed(1);
    const highRiskCount = riskScoresPercent.filter(s => s >= 75).length;
    const uniqueEmployers = Object.keys(employerRisks).length;
    const uniqueEmployees = Object.keys(employeeRisks).length;

    return {
      riskDistribution,
      recommendationData,
      riskLevelData,
      riskByEmployerData,
      topHighRiskEmployees,
      fraudTypeData,
      summary: {
        totalPaystubs,
        avgFraudRisk,
        highRiskCount,
        avgGrossPay,
        avgNetPay,
        maxGrossPay,
        minGrossPay,
        uniqueEmployers,
        uniqueEmployees
      }
    };
  };

  const onDrop = useCallback(acceptedFiles => {
    setLoading(true);
    setError(null);

    const file = acceptedFiles[0];
    if (!file) {
      setLoading(false);
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const rows = parseCSV(text);

        if (rows.length === 0) {
          setError('No valid data in CSV file');
          setLoading(false);
          return;
        }

        setAllPaystubsData(rows);
        setTotalRecords(rows.length);

        const employers = [...new Set(rows.map(r => r['employer_name'] || 'Unknown'))];
        setAvailableEmployers(employers.sort());

        const processed = processData(rows);
        setCsvData(processed);
        setPaystubsList(rows);
        setLoading(false);
      } catch (err) {
        setError(`Error parsing CSV: ${err.message}`);
        setLoading(false);
      }
    };
    reader.readAsText(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] }
  });

  const fetchPaystubsFromAPI = async () => {
    setLoadingPaystubsList(true);
    setError(null);
    try {
      const response = await fetch('/api/paystubs/insights');
      if (!response.ok) throw new Error('Failed to fetch paystubs');

      const data = await response.json();
      const rows = data.data || [];

      setAllPaystubsData(rows);
      setTotalRecords(rows.length);

      const employers = [...new Set(rows.map(r => r.employer_name || 'Unknown'))];
      setAvailableEmployers(employers.sort());

      const processed = processData(rows);
      setCsvData(processed);
      setPaystubsList(rows);
    } catch (err) {
      setError(`Error fetching paystubs: ${err.message}`);
    }
    setLoadingPaystubsList(false);
  };

  const getFilteredData = () => {
    let filtered = allPaystubsData;

    // Filter by employer
    if (employerFilter && employerFilter !== '' && employerFilter !== 'All Employers') {
      filtered = filtered.filter(p => p.employer_name === employerFilter);
    }

    // Filter by search query (employee name)
    if (searchQuery.trim()) {
      filtered = filtered.filter(p =>
        (p.employee_name || '').toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by date range
    if (dateFilter) {
      const now = new Date();
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      const sixtyDaysAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000);
      const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);

      filtered = filtered.filter(p => {
        const createdAt = new Date(p.created_at);
        if (dateFilter === 'last_30') return createdAt >= thirtyDaysAgo;
        if (dateFilter === 'last_60') return createdAt >= sixtyDaysAgo && createdAt < thirtyDaysAgo;
        if (dateFilter === 'last_90') return createdAt >= ninetyDaysAgo && createdAt < sixtyDaysAgo;
        if (dateFilter === 'older') return createdAt < ninetyDaysAgo;
        return true;
      });
    }

    return filtered;
  };

  const filteredData = getFilteredData();
  const processedData = filteredData.length > 0 ? processData(filteredData, employerFilter) : null;

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  const COLORS = [
    primary,
    colors.status.warning || '#FFA726',
    colors.accent.redDark || '#C62828',
    '#FF6B6B',
    colors.status.success || '#4CAF50',
    '#9C27B0',
    '#2196F3',
    '#FF9800'
  ];

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Paystub Insights Dashboard</h1>

      {/* Input Mode Selector */}
      <div style={styles.modeSelector}>
        <button
          style={{...styles.modeButton, ...(inputMode === 'upload' ? styles.modeButtonActive : {})}}
          onClick={() => setInputMode('upload')}
        >
          <FaUpload /> CSV Upload
        </button>
        <button
          style={{...styles.modeButton, ...(inputMode === 'api' ? styles.modeButtonActive : {})}}
          onClick={() => {
            setInputMode('api');
            fetchPaystubsFromAPI();
          }}
        >
          <FaCog /> Database
        </button>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {/* CSV Upload Mode */}
      {inputMode === 'upload' && (
        <div
          {...getRootProps()}
          style={{...styles.dropzone, ...(isDragActive ? styles.dropzoneActive : {})}}
        >
          <input {...getInputProps()} />
          <FaUpload size={32} style={{marginBottom: '10px'}} />
          {isDragActive ? (
            <p>Drop CSV file here...</p>
          ) : (
            <>
              <p>Drag and drop CSV file here, or click to select</p>
              <small>Expected columns: paystub_id, employee_name, employer_name, gross_pay, net_pay, fraud_risk_score, ai_recommendation, fraud_types, created_at</small>
            </>
          )}
        </div>
      )}

      {/* Filters Section */}
      {(csvData || processedData) && (
        <div style={styles.filtersSection}>
          <input
            type="text"
            placeholder="Search by employee name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={styles.searchInput}
          />

          <select
            value={employerFilter || ''}
            onChange={(e) => setEmployerFilter(e.target.value || null)}
            style={styles.select}
          >
            <option value="">All Employers</option>
            {availableEmployers.map(emp => (
              <option key={emp} value={emp}>{emp}</option>
            ))}
          </select>

          <select
            value={dateFilter || ''}
            onChange={(e) => setDateFilter(e.target.value || null)}
            style={styles.select}
          >
            <option value="">All Time</option>
            <option value="last_30">Last 30 Days</option>
            <option value="last_60">Last 60 Days</option>
            <option value="last_90">Last 90 Days</option>
            <option value="older">Older</option>
          </select>

          <span style={styles.recordCount}>
            Showing {filteredData.length} of {totalRecords} paystubs
          </span>
        </div>
      )}

      {loading && <div style={styles.loading}>Loading...</div>}
      {loadingPaystubsList && <div style={styles.loading}>Fetching paystubs from database...</div>}

      {/* Summary KPI Cards */}
      {(csvData || processedData) && (
        <div style={styles.kpiContainer}>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{(csvData || processedData).summary.totalPaystubs}</div>
            <div style={styles.kpiLabel}>Total Paystubs</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{(csvData || processedData).summary.avgFraudRisk}%</div>
            <div style={styles.kpiLabel}>Avg Fraud Risk</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>${(csvData || processedData).summary.avgGrossPay}</div>
            <div style={styles.kpiLabel}>Avg Gross Pay</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>${(csvData || processedData).summary.avgNetPay}</div>
            <div style={styles.kpiLabel}>Avg Net Pay</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{(csvData || processedData).summary.uniqueEmployers}</div>
            <div style={styles.kpiLabel}>Unique Employers</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{(csvData || processedData).summary.uniqueEmployees}</div>
            <div style={styles.kpiLabel}>Unique Employees</div>
          </div>
        </div>
      )}

      {/* Charts Section */}
      {(csvData || processedData) && (
        <div style={styles.chartsContainer}>
          {/* Risk Distribution */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Fraud Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={(csvData || processedData).riskDistribution} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                <defs>
                  <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={primary} stopOpacity={1} />
                    <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
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
                <Tooltip content={<CustomTooltip />} />
                <Bar 
                  dataKey="count" 
                  fill="url(#riskGradient)"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* AI Recommendation Distribution */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>AI Recommendation Breakdown</h3>
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={(csvData || processedData).recommendationData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  innerRadius={40}
                  fill="#8884d8"
                  dataKey="value"
                  stroke={colors.card}
                  strokeWidth={2}
                >
                  {(csvData || processedData).recommendationData.map((entry, index) => {
                    const colorMap = {
                      'APPROVE': colors.status.success || '#4CAF50',
                      'REJECT': primary,
                      'ESCALATE': colors.status.warning || '#FFA726'
                    };
                    return (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={colorMap[entry.name] || COLORS[index % COLORS.length]}
                      />
                    );
                  })}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ color: colors.foreground }}
                  iconType="circle"
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Risk Level Distribution */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Risk Level Distribution</h3>
            <ResponsiveContainer width="100%" height={320}>
              <PieChart>
                <Pie
                  data={(csvData || processedData).riskLevelData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  innerRadius={40}
                  fill="#8884d8"
                  dataKey="value"
                  stroke={colors.card}
                  strokeWidth={2}
                >
                  {(csvData || processedData).riskLevelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ color: colors.foreground }}
                  iconType="circle"
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Risk by Employer */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Risk by Employer (Top 10)</h3>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                data={(csvData || processedData).riskByEmployerData}
                margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
              >
                <defs>
                  <linearGradient id="employerGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={primary} stopOpacity={1} />
                    <stop offset="100%" stopColor={primary} stopOpacity={0.6} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                  tick={{ fill: colors.foreground, fontSize: 11 }}
                  stroke={colors.border}
                />
                <YAxis 
                  tick={{ fill: colors.foreground, fontSize: 12 }}
                  stroke={colors.border}
                  label={{ value: 'Risk %', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ color: colors.foreground }}
                  iconType="square"
                />
                <Bar 
                  dataKey="avgRisk" 
                  fill="url(#employerGradient)" 
                  name="Avg Risk %"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top High-Risk Employees */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Top High-Risk Employees (≥50%)</h3>
            {(csvData || processedData).topHighRiskEmployees && (csvData || processedData).topHighRiskEmployees.length > 0 ? (
              <ResponsiveContainer width="100%" height={350}>
                <BarChart
                  data={(csvData || processedData).topHighRiskEmployees}
                  margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                >
                <defs>
                  <linearGradient id="employeeGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FF6B6B" stopOpacity={1} />
                    <stop offset="100%" stopColor="#FF6B6B" stopOpacity={0.6} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  interval={0}
                  tick={{ fill: colors.foreground, fontSize: 11 }}
                  stroke={colors.border}
                />
                <YAxis 
                  tick={{ fill: colors.foreground, fontSize: 12 }}
                  stroke={colors.border}
                  label={{ value: 'Risk %', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ color: colors.foreground }}
                  iconType="square"
                />
                <Bar 
                  dataKey="avgRisk" 
                  fill="url(#employeeGradient)" 
                  name="Avg Risk %"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
            ) : (
              <div style={{
                padding: '3rem',
                textAlign: 'center',
                color: colors.mutedForeground,
                backgroundColor: colors.secondary,
                borderRadius: '8px',
                border: `1px solid ${colors.border}`
              }}>
                <p>No employees found with risk score ≥ 50%</p>
                <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                  Try adjusting filters or upload data with higher risk scores
                </p>
              </div>
            )}
          </div>

          {/* Fraud Type Distribution */}
          {(csvData || processedData).fraudTypeData.length > 0 && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Fraud Type Distribution</h3>
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={(csvData || processedData).fraudTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => percent > 0.05 ? `${name}: ${(percent * 100).toFixed(0)}%` : ''}
                    outerRadius={100}
                    innerRadius={40}
                    fill="#8884d8"
                    dataKey="value"
                    stroke={colors.card}
                    strokeWidth={2}
                  >
                    {(csvData || processedData).fraudTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend 
                    wrapperStyle={{ color: colors.foreground }}
                    iconType="circle"
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: '0',
    maxWidth: '100%',
    margin: '0',
    backgroundColor: 'transparent',
    borderRadius: '0'
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
    marginBottom: '20px',
    color: colors.foreground,
    display: 'none'
  },
  modeSelector: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px'
  },
  modeButton: {
    padding: '10px 20px',
    border: `1px solid ${colors.border}`,
    backgroundColor: colors.card,
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.3s'
  },
  modeButtonActive: {
    backgroundColor: colors.accent.red,
    color: 'white',
    borderColor: colors.accent.red
  },
  dropzone: {
    border: `2px dashed ${colors.border}`,
    borderRadius: '8px',
    padding: '40px',
    textAlign: 'center',
    cursor: 'pointer',
    backgroundColor: colors.card,
    marginBottom: '20px',
    transition: 'all 0.3s'
  },
  dropzoneActive: {
    backgroundColor: colors.secondary,
    borderColor: colors.accent.red
  },
  filtersSection: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    alignItems: 'center',
    flexWrap: 'wrap'
  },
  searchInput: {
    padding: '8px 12px',
    border: `1px solid ${colors.border}`,
    borderRadius: '4px',
    fontSize: '14px',
    flex: 1,
    minWidth: '200px',
    backgroundColor: colors.card,
    color: colors.foreground
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
  },
  loading: {
    textAlign: 'center',
    padding: '20px',
    color: colors.mutedForeground
  },
  error: {
    backgroundColor: colors.accent.red,
    color: 'white',
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '20px'
  },
  kpiContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '15px',
    marginBottom: '30px'
  },
  kpiCard: {
    backgroundColor: colors.card,
    padding: '20px',
    borderRadius: '8px',
    border: `1px solid ${colors.border}`,
    textAlign: 'center'
  },
  kpiValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: colors.accent.red,
    marginBottom: '8px'
  },
  kpiLabel: {
    fontSize: '12px',
    color: colors.mutedForeground,
    textTransform: 'uppercase'
  },
  chartsContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
    gap: '20px'
  },
  chartBox: {
    backgroundColor: colors.card,
    padding: '24px',
    borderRadius: '12px',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    transition: 'all 0.3s ease',
  },
  chartTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: colors.foreground,
    marginBottom: '20px',
    paddingBottom: '12px',
    borderBottom: `2px solid ${colors.border}`,
  }
};

export default PaystubInsights;
