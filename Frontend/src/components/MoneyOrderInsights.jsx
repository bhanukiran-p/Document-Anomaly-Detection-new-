import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { FaUpload, FaCog } from 'react-icons/fa';

const MoneyOrderInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const parseCSV = (text) => {
    const lines = text.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim());
    const rows = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // Simple CSV parsing (handles basic cases)
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

    // Fraud Risk Distribution
    const riskScores = rows.map(r => parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0));
    const riskScoresPercent = riskScores.map(s => s * 100);
    const riskDistribution = [
      { range: '0-25%', count: riskScoresPercent.filter(s => s < 25).length },
      { range: '25-50%', count: riskScoresPercent.filter(s => s >= 25 && s < 50).length },
      { range: '50-75%', count: riskScoresPercent.filter(s => s >= 50 && s < 75).length },
      { range: '75-100%', count: riskScoresPercent.filter(s => s >= 75).length },
    ];

    // AI Recommendation Distribution
    const recommendations = rows.map(r => (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
    const recommendationData = [
      { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
      { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
      { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
    ].filter(item => item.value > 0);

    // Risk Level Category Distribution
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

    // Summary metrics
    const totalMoneyOrders = rows.length;
    const avgRiskScore = (riskScores.reduce((a, b) => a + b, 0) / riskScores.length * 100).toFixed(1);
    const approveCount = recommendations.filter(d => d === 'APPROVE').length;
    const rejectCount = recommendations.filter(d => d === 'REJECT').length;
    const escalateCount = recommendations.filter(d => d === 'ESCALATE').length;

    return {
      riskDistribution,
      recommendationData: recommendationData.length > 0 ? recommendationData : [
        { name: 'No Data', value: rows.length }
      ],
      riskLevelData,
      metrics: {
        totalMoneyOrders,
        avgRiskScore,
        approveCount,
        rejectCount,
        escalateCount
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
          Money Order Insights from CSV
        </h2>

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
                CSV file with money order analysis data
              </p>
            </div>
          )}
        </div>

        {error && (
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

        {loading && (
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
      </div>

      {csvData && (
        <div>
          {/* Summary Metrics */}
          <div style={metricsGridStyle}>
            <div style={metricCardStyle}>
              <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Total Money Orders
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
                {csvData.metrics.totalMoneyOrders}
              </div>
            </div>

            <div style={metricCardStyle}>
              <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                Avg Risk Score
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.warning }}>
                {csvData.metrics.avgRiskScore}%
              </div>
            </div>

            <div style={metricCardStyle}>
              <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                APPROVE
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.success }}>
                {csvData.metrics.approveCount}
              </div>
            </div>

            <div style={metricCardStyle}>
              <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                REJECT
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.accent.red }}>
                {csvData.metrics.rejectCount}
              </div>
            </div>

            <div style={metricCardStyle}>
              <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                ESCALATE
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.warning }}>
                {csvData.metrics.escalateCount}
              </div>
            </div>
          </div>

          {/* Risk Score Distribution */}
          <div style={chartContainerStyle}>
            <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
              Risk Score Distribution by Range
            </h3>
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
          </div>

          {/* AI Recommendation Breakdown */}
          <div style={chartContainerStyle}>
            <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
              AI Decision Breakdown (APPROVE/REJECT/ESCALATE)
            </h3>
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
          </div>

          {/* Risk Level Category Distribution */}
          <div style={chartContainerStyle}>
            <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
              Transaction Distribution by Risk Level
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={csvData.riskLevelData}>
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
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={colors.accent.red}
                  fill={colors.accent.red}
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default MoneyOrderInsights;
