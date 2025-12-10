import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area,
  ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
  ScatterChart, Scatter, ZAxis, Sector
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

const PaystubInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('api'); // 'upload' or 'api'
  const [paystubsList, setPaystubsList] = useState([]);
  const [allPaystubsData, setAllPaystubsData] = useState([]);
  const [loadingPaystubsList, setLoadingPaystubsList] = useState(false);
  const [selectedPaystubId, setSelectedPaystubId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'older', 'custom'
  const [employerFilter, setEmployerFilter] = useState(null);
  const [fraudTypeFilter, setFraudTypeFilter] = useState(null);
  const [availableEmployers, setAvailableEmployers] = useState([]);
  const [availableFraudTypes, setAvailableFraudTypes] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [activePieIndex, setActivePieIndex] = useState(null);
  const [activeBarIndex, setActiveBarIndex] = useState(null);
  const [activeScatterIndex, setActiveScatterIndex] = useState(null);
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

  const processData = (rows, selectedEmployer = null, selectedFraudType = null, allRowsForComparison = null) => {
    if (!rows.length) return null;

    // Check if we're in single employer view
    const isSingleEmployerView = selectedEmployer && selectedEmployer !== '' && selectedEmployer !== 'All Employers';

    // Check if we're filtering by a specific fraud type
    const isFraudTypeFiltered = selectedFraudType && selectedFraudType !== '' && selectedFraudType !== 'All Fraud Types';

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
      // Skip Unknown employers
      if (!employer || employer === 'Unknown' || employer.toLowerCase() === 'unknown') {
        return;
      }
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

    // Format currency values with K notation (e.g., $4.8K instead of $4765.67)
    const formatCurrencyK = (value) => {
      if (value >= 1000) {
        return `$${(value / 1000).toFixed(1)}K`;
      }
      return `$${value.toFixed(0)}`;
    };

    const avgGrossPayRaw = grossPayValues.reduce((a, b) => a + b, 0) / grossPayValues.length;
    const avgNetPayRaw = netPayValues.reduce((a, b) => a + b, 0) / netPayValues.length;

    const avgGrossPay = formatCurrencyK(avgGrossPayRaw);
    const avgNetPay = formatCurrencyK(avgNetPayRaw);
    const maxGrossPay = Math.max(...grossPayValues).toFixed(2);
    const minGrossPay = Math.min(...grossPayValues).toFixed(2);

    // 8. Fraud-Type-Specific Metrics (only when filtering by fraud type)
    let fraudTypeSpecificData = null;
    if (isFraudTypeFiltered) {
      // (A) Avg Risk Comparison
      const filteredAvgRisk = riskScores.length > 0
        ? ((riskScores.reduce((a, b) => a + b, 0) / riskScores.length) * 100).toFixed(1)
        : '0.0';

      // Calculate average risk for all paystubs (for comparison)
      let allAvgRisk = '0.0';
      if (allRowsForComparison && allRowsForComparison.length > 0) {
        const allRiskScores = allRowsForComparison.map(r => parseFloat_(r['fraud_risk_score'] || 0));
        if (allRiskScores.length > 0) {
          allAvgRisk = ((allRiskScores.reduce((a, b) => a + b, 0) / allRiskScores.length) * 100).toFixed(1);
        }
      }

      // (B) Severity Breakdown for This Fraud Type (LOW: <50%, MEDIUM: 50-70%, HIGH: >70%)
      const severityCounts = {
        'LOW': 0,
        'MEDIUM': 0,
        'HIGH': 0
      };
      riskScoresPercent.forEach(score => {
        if (score < 50) {
          severityCounts['LOW']++;
        } else if (score >= 50 && score <= 70) {
          severityCounts['MEDIUM']++;
        } else {
          severityCounts['HIGH']++;
        }
      });
      const severityBreakdown = [
        { name: 'LOW (<50%)', value: severityCounts['LOW'], color: colors.status.success || '#4CAF50' },
        { name: 'MEDIUM (50-70%)', value: severityCounts['MEDIUM'], color: colors.status.warning || '#FFA726' },
        { name: 'HIGH (>70%)', value: severityCounts['HIGH'], color: colors.accent.red }
      ].filter(item => item.value > 0);

      // (C) Monthly Fraud Trend for This Fraud Type
      const monthlyTrend = {};
      rows.forEach(r => {
        const dateStr = r['created_at'] || r['pay_date'] || r['timestamp'] || '';
        if (dateStr) {
          const date = new Date(dateStr);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          if (!monthlyTrend[monthKey]) {
            monthlyTrend[monthKey] = 0;
          }
          monthlyTrend[monthKey]++;
        }
      });
      const monthlyTrendData = Object.entries(monthlyTrend)
        .map(([month, count]) => ({
          month,
          count
        }))
        .sort((a, b) => a.month.localeCompare(b.month));

      // (D) Top Employers for This Fraud Type
      const employerCounts = {};
      rows.forEach(r => {
        const employer = r['employer_name'] || 'Unknown';
        // Skip Unknown employers
        if (!employer || employer === 'Unknown' || employer.toLowerCase() === 'unknown') {
          return;
        }
        employerCounts[employer] = (employerCounts[employer] || 0) + 1;
      });
      const topEmployersForFraudType = Object.entries(employerCounts)
        .map(([name, count]) => ({
          name,
          count
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);

      // (E) Employee Risk Distribution (when single employer + fraud type selected)
      const employeeRiskDistribution = {};
      rows.forEach(r => {
        const employeeName = r['employee_name'] || 'Unknown';
        const riskScore = parseFloat_(r['fraud_risk_score'] || 0) * 100;
        if (!employeeRiskDistribution[employeeName]) {
          employeeRiskDistribution[employeeName] = {
            name: employeeName,
            avgRisk: 0,
            count: 0,
            totalRisk: 0
          };
        }
        employeeRiskDistribution[employeeName].count++;
        employeeRiskDistribution[employeeName].totalRisk += riskScore;
      });
      const employeeRiskData = Object.values(employeeRiskDistribution)
        .map(emp => ({
          ...emp,
          avgRisk: emp.totalRisk / emp.count
        }))
        .sort((a, b) => b.avgRisk - a.avgRisk)
        .slice(0, 10);

      // (F) Risk Score Distribution (for when severity breakdown is not meaningful)
      const riskScoreRanges = {
        '0-25%': 0,
        '25-50%': 0,
        '50-75%': 0,
        '75-100%': 0
      };
      riskScoresPercent.forEach(score => {
        if (score < 25) {
          riskScoreRanges['0-25%']++;
        } else if (score < 50) {
          riskScoreRanges['25-50%']++;
        } else if (score < 75) {
          riskScoreRanges['50-75%']++;
        } else {
          riskScoreRanges['75-100%']++;
        }
      });
      const riskScoreDistribution = Object.entries(riskScoreRanges)
        .map(([range, count]) => ({
          range,
          count
        }))
        .filter(item => item.count > 0);

      // (F-alt) Risk Score Timeline (for when both employer and fraud type selected)
      const riskScoreTimeline = rows
        .map(r => {
          const dateStr = r['created_at'] || r['pay_date'] || r['timestamp'] || '';
          const date = dateStr ? new Date(dateStr) : new Date();
          const riskScore = parseFloat_(r['fraud_risk_score'] || 0) * 100;
          const employeeName = r['employee_name'] || 'Unknown';
          return {
            date: date.toISOString().split('T')[0],
            riskScore: parseFloat(riskScore.toFixed(1)),
            employeeName: employeeName,
            timestamp: date.getTime()
          };
        })
        .sort((a, b) => a.timestamp - b.timestamp)
        .slice(0, 50); // Limit to 50 most recent

      // (G) Additional KPIs for Fraud Type
      // 1. Medium-Risk Cases Count
      // Number of paystubs with fraud risk score between 50-75% (moderate cases)
      const mediumRiskCasesCount = riskScoresPercent.filter(score => score >= 50 && score < 75).length;

      // 2. High-Risk Cases Count
      // Number of paystubs with fraud risk score >= 75% (severe cases)
      const highRiskCasesCount = riskScoresPercent.filter(score => score >= 75).length;

      fraudTypeSpecificData = {
        avgRiskComparison: {
          selectedFraudType: filteredAvgRisk,
          allPaystubs: allAvgRisk,
          fraudTypeName: selectedFraudType
        },
        severityBreakdown,
        monthlyTrend: monthlyTrendData,
        topEmployersForFraudType,
        employeeRiskDistribution: employeeRiskData,
        riskScoreDistribution,
        riskScoreTimeline,
        kpis: {
          mediumRiskCasesCount: mediumRiskCasesCount,
          highRiskCasesCount: highRiskCasesCount
        }
      };
    }

    // 9. Summary metrics
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
      fraudTypeSpecificData,
      isFraudTypeFiltered,
      isSingleEmployerView,
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

        const employers = [...new Set(rows.map(r => r['employer_name'] || 'Unknown'))]
          .filter(emp => emp && emp !== 'Unknown' && emp.toLowerCase() !== 'unknown');
        setAvailableEmployers(employers.sort());

        // Extract available fraud types
        const fraudTypes = new Set();
        rows.forEach(r => {
          const fraudType = r['fraud_types'];
          if (fraudType) {
            if (Array.isArray(fraudType)) {
              fraudType.forEach(ft => {
                const typeStr = String(ft || '').trim();
                if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
                  fraudTypes.add(typeStr.replace(/_/g, ' '));
                }
              });
            } else {
              const typeStr = String(fraudType || '').trim();
              if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
                fraudTypes.add(typeStr.replace(/_/g, ' '));
              }
            }
          }
        });
        setAvailableFraudTypes(Array.from(fraudTypes).sort());

        const processed = processData(rows, null, null, rows);
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

      const employers = [...new Set(rows.map(r => r.employer_name || 'Unknown'))]
        .filter(emp => emp && emp !== 'Unknown' && emp.toLowerCase() !== 'unknown');
      setAvailableEmployers(employers.sort());

      // Extract available fraud types
      const fraudTypes = new Set();
      rows.forEach(r => {
        const fraudType = r.fraud_types;
        if (fraudType) {
          if (Array.isArray(fraudType)) {
            fraudType.forEach(ft => {
              const typeStr = String(ft || '').trim();
              if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
                fraudTypes.add(typeStr.replace(/_/g, ' '));
              }
            });
          } else {
            const typeStr = String(fraudType || '').trim();
            if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
              fraudTypes.add(typeStr.replace(/_/g, ' '));
            }
          }
        }
      });
      setAvailableFraudTypes(Array.from(fraudTypes).sort());

      const processed = processData(rows, null, null, rows);
      setCsvData(processed);
      setPaystubsList(rows);
    } catch (err) {
      setError(`Error fetching paystubs: ${err.message}`);
    }
    setLoadingPaystubsList(false);
  };

  // Auto-fetch data when component mounts in 'api' mode
  useEffect(() => {
    if (inputMode === 'api' && allPaystubsData.length === 0 && !loadingPaystubsList) {
      fetchPaystubsFromAPI();
    }
  }, []); // Empty dependency array - only run on mount

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
      if (dateFilter === 'custom' && (customDateRange.startDate || customDateRange.endDate)) {
        // Custom date range filtering
        filtered = filtered.filter(p => {
          const createdAt = new Date(p.created_at);
          const startDate = customDateRange.startDate ? new Date(customDateRange.startDate) : null;
          const endDate = customDateRange.endDate ? new Date(customDateRange.endDate) : null;

          if (startDate && endDate) {
            return createdAt >= startDate && createdAt <= endDate;
          } else if (startDate) {
            return createdAt >= startDate;
          } else if (endDate) {
            return createdAt <= endDate;
          }
          return true;
        });
      } else {
        // Predefined date filters
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
    }

    // Filter by fraud type
    if (fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types') {
      filtered = filtered.filter(p => {
        const fraudType = p.fraud_types;
        if (!fraudType) return false;

        // Normalize the filter value for comparison (handle both formats)
        const normalizedFilter = fraudTypeFilter.toLowerCase().trim();

        // Handle different formats: string, array, or null
        if (Array.isArray(fraudType)) {
          return fraudType.some(ft => {
            const typeStr = String(ft || '').trim();
            const normalizedType = typeStr.replace(/_/g, ' ').toLowerCase();
            return normalizedType === normalizedFilter || typeStr.toLowerCase() === normalizedFilter;
          });
        } else {
          const typeStr = String(fraudType || '').trim();
          const normalizedType = typeStr.replace(/_/g, ' ').toLowerCase();
          return normalizedType === normalizedFilter || typeStr.toLowerCase() === normalizedFilter;
        }
      });
    }

    return filtered;
  };

  const filteredData = getFilteredData();
  // Always process filtered data - if no filters, filteredData === allPaystubsData
  // Pass allPaystubsData for comparison when fraud type filter is active
  const processedData = filteredData.length > 0
    ? processData(filteredData, employerFilter, fraudTypeFilter, allPaystubsData)
    : null;
  // Use processedData when available (from filters or initial load), fallback to csvData
  const displayData = processedData || csvData;

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


      {/* Filters Section */}
      {displayData && (
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
            onChange={(e) => {
              const value = e.target.value || null;
              if (value === 'custom') {
                setShowCustomDatePicker(true);
              } else {
                setShowCustomDatePicker(false);
                setDateFilter(value);
              }
            }}
            style={styles.select}
          >
            <option value="">All Time</option>
            <option value="last_30">Last 30 Days</option>
            <option value="last_60">Last 60 Days</option>
            <option value="last_90">Last 90 Days</option>
            <option value="older">Older</option>
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
              style={styles.select}
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
              setEmployerFilter(null);
              setDateFilter(null);
              setFraudTypeFilter(null);
              setCustomDateRange({ startDate: '', endDate: '' });
              setShowCustomDatePicker(false);
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

          <span style={styles.recordCount}>
            Showing {filteredData.length} of {totalRecords} paystubs
          </span>
        </div>
      )}

      {loading && <div style={styles.loading}>Loading...</div>}
      {loadingPaystubsList && <div style={styles.loading}>Fetching paystubs from database...</div>}

      {/* Summary KPI Cards */}
      {displayData && (
        <div style={styles.kpiContainer}>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{displayData.summary.totalPaystubs}</div>
            <div style={styles.kpiLabel}>Total Paystubs</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{displayData.summary.avgFraudRisk}%</div>
            <div style={styles.kpiLabel}>Avg Fraud Risk</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{displayData.summary.avgGrossPay}</div>
            <div style={styles.kpiLabel}>Avg Gross Pay</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{displayData.summary.avgNetPay}</div>
            <div style={styles.kpiLabel}>Avg Net Pay</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{displayData.summary.uniqueEmployers}</div>
            <div style={styles.kpiLabel}>Unique Employers</div>
          </div>
          <div style={styles.kpiCard}>
            <div style={styles.kpiValue}>{displayData.summary.uniqueEmployees}</div>
            <div style={styles.kpiLabel}>Unique Employees</div>
          </div>
        </div>
      )}

      {/* Charts Section */}
      {displayData && (
        <div style={styles.chartsContainer}>
          {/* Show standard charts only when NO fraud type filter is active */}
          {!displayData.isFraudTypeFiltered && (
            <>
              {/* Risk Distribution */}
              <div style={styles.chartBox}>
                <h3 style={styles.chartTitle}>Fraud Risk Distribution</h3>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart
                    data={displayData.riskDistribution}
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
                      {displayData.riskDistribution.map((entry, index) => {
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

              {/* AI Recommendation Distribution */}
              <div style={styles.chartBox}>
                <h3 style={styles.chartTitle}>AI Recommendation Breakdown</h3>
                {/* Centered Donut Chart */}
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '320px' }}>
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart
                      onMouseLeave={() => setActivePieIndex(null)}
                    >
                      <Pie
                        data={displayData.recommendationData}
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
                        {displayData.recommendationData.map((entry, index) => {
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
                            const total = displayData.recommendationData.reduce((sum, item) => sum + item.value, 0);
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
                  {displayData.recommendationData.map((entry, index) => {
                    const colorMap = {
                      'APPROVE': colors.status.success || '#4CAF50',
                      'REJECT': primary,
                      'ESCALATE': colors.status.warning || '#FFA726'
                    };
                    const total = displayData.recommendationData.reduce((sum, item) => sum + item.value, 0);
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

              {/* Risk by Employer - Converted to Area Chart with Data Points */}
              {/* Hide this chart when filtering by a single employer - it becomes useless */}
              {!displayData.isSingleEmployerView && (
                <div style={styles.chartBox}>
                  <h3 style={styles.chartTitle}>Risk by Employer (Top 10)</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <AreaChart
                      data={displayData.riskByEmployerData}
                      margin={{ top: 20, right: 30, left: 30, bottom: 80 }}
                    >
                      <defs>
                        <linearGradient id="employerAreaGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={primary} stopOpacity={0.8} />
                          <stop offset="100%" stopColor={primary} stopOpacity={0.1} />
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
                        dx={-5}
                        dy={5}
                      />
                      <YAxis
                        tick={{ fill: colors.foreground, fontSize: 12 }}
                        stroke={colors.border}
                        label={{ value: 'Risk %', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Area
                        type="monotone"
                        dataKey="avgRisk"
                        stroke={primary}
                        strokeWidth={3}
                        fill="url(#employerAreaGradient)"
                        name="Avg Risk %"
                      />
                      <Line
                        type="monotone"
                        dataKey="avgRisk"
                        stroke={primary}
                        strokeWidth={3}
                        dot={{ fill: primary, r: 6, strokeWidth: 2, stroke: colors.card }}
                        activeDot={{ r: 8, strokeWidth: 2, stroke: colors.card }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Risk Level Distribution - Converted to Heatmap */}
              <div style={styles.chartBox}>
                <h3 style={styles.chartTitle}>Risk Level Distribution</h3>
                <div style={{ padding: '1rem', minHeight: '280px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: displayData.riskLevelData.length === 3 ? 'repeat(3, 1fr)' : `repeat(${displayData.riskLevelData.length}, 1fr)`,
                    gap: '1rem',
                    flex: 1,
                    alignItems: 'stretch'
                  }}>
                    {displayData.riskLevelData.map((entry, index) => {
                      const total = displayData.riskLevelData.reduce((sum, item) => sum + item.value, 0);
                      const percentage = total > 0 ? ((entry.value / total) * 100).toFixed(1) : 0;

                      // Use brighter opacity for all cards (0.9 for vibrant, bright appearance)
                      // MEDIUM already uses colors.status.warning (#f59e0b - yellow)
                      const cardColor = entry.color;

                      return (
                        <div
                          key={`heatmap-cell-${index}`}
                          style={{
                            backgroundColor: cardColor,
                            opacity: 0.9,
                            padding: '1.25rem',
                            borderRadius: '8px',
                            border: `2px solid ${cardColor}`,
                            textAlign: 'center',
                            transition: 'transform 0.2s',
                            cursor: 'pointer',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            minHeight: '180px'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'scale(1.02)';
                            e.currentTarget.style.opacity = '1';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'scale(1)';
                            e.currentTarget.style.opacity = '0.9';
                          }}
                        >
                          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.foreground, marginBottom: '0.75rem' }}>
                            {entry.value}
                          </div>
                          <div style={{ fontSize: '0.85rem', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '600', whiteSpace: 'nowrap' }}>
                            {entry.name}
                          </div>
                          <div style={{ fontSize: '1rem', color: colors.foreground, fontWeight: '600' }}>
                            {percentage}%
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  {displayData.riskLevelData.length > 0 && (
                    <div style={{
                      marginTop: '1rem',
                      padding: '0.75rem 1rem',
                      backgroundColor: colors.secondary,
                      borderRadius: '8px',
                      border: `1px solid ${colors.border}`
                    }}>
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '0.9rem',
                        color: colors.foreground
                      }}>
                        <span>Total Paystubs:</span>
                        <span style={{ fontWeight: 'bold', color: primary }}>
                          {displayData.riskLevelData.reduce((sum, item) => sum + item.value, 0)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Top High-Risk Employees - Bullet Chart + Horizontal Ranking */}
              <div style={styles.chartBox}>
                <h3 style={styles.chartTitle}>Top High-Risk Employees (≥50%)</h3>
                {displayData.topHighRiskEmployees && displayData.topHighRiskEmployees.length > 0 ? (
                  <ResponsiveContainer width="100%" height={Math.max(550, displayData.topHighRiskEmployees.length * 45)}>
                    <ComposedChart
                      data={displayData.topHighRiskEmployees.map(emp => ({
                        ...emp,
                        lowZone: 50,      // 0-50% zone
                        mediumZone: 25,   // 50-75% zone (25% width)
                        highZone: 25      // 75-100% zone (25% width)
                      }))}
                      layout="vertical"
                      margin={{ top: 20, right: 20, left: 40, bottom: 20 }}
                    >
                      <defs>
                        <linearGradient id="bulletGradient" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor={primary} stopOpacity={0.9} />
                          <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.2} horizontal={false} />
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                        tick={{ fill: colors.foreground, fontSize: 11 }}
                        stroke={colors.border}
                        label={{ value: 'Risk %', position: 'insideBottom', offset: -5, fill: colors.foreground }}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={50}
                        tick={{ fill: colors.foreground, fontSize: 11 }}
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
                                  {data.name}
                                </p>
                                <p style={{ margin: '4px 0', color: primary }}>
                                  <span style={{ fontWeight: '600' }}>Risk:</span> {data.avgRisk.toFixed(1)}%
                                </p>
                                <p style={{ margin: '4px 0', color: colors.mutedForeground, fontSize: '0.85rem' }}>
                                  {data.avgRisk >= 75 ? '🔴 High Risk' : data.avgRisk >= 50 ? '🟡 Medium Risk' : '🟢 Low Risk'}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      {/* Background zones for bullet chart effect */}
                      <Bar
                        dataKey="lowZone"
                        stackId="zones"
                        fill={colors.status.success || '#4CAF50'}
                        fillOpacity={0.15}
                        name="Low Risk Zone (0-50%)"
                        isAnimationActive={false}
                      />
                      <Bar
                        dataKey="mediumZone"
                        stackId="zones"
                        fill={colors.status.warning || '#FFA726'}
                        fillOpacity={0.2}
                        name="Medium Risk Zone (50-75%)"
                        isAnimationActive={false}
                      />
                      <Bar
                        dataKey="highZone"
                        stackId="zones"
                        fill={primary}
                        fillOpacity={0.15}
                        name="High Risk Zone (75-100%)"
                        isAnimationActive={false}
                      />
                      {/* Primary bar showing actual risk */}
                      <Bar
                        dataKey="avgRisk"
                        fill="url(#bulletGradient)"
                        name="Risk %"
                        radius={[0, 4, 4, 0]}
                        stroke={primary}
                        strokeWidth={2}
                      />
                      {/* Threshold reference lines */}
                      <ReferenceLine
                        x={50}
                        stroke={colors.status.warning || '#FFA726'}
                        strokeWidth={1.5}
                        strokeDasharray="4 4"
                        label={{ value: "50%", position: "top", fill: colors.status.warning || '#FFA726', fontSize: 10 }}
                      />
                      <ReferenceLine
                        x={75}
                        stroke={primary}
                        strokeWidth={1.5}
                        strokeDasharray="4 4"
                        label={{ value: "75%", position: "top", fill: primary, fontSize: 10 }}
                      />
                    </ComposedChart>
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

              {/* Fraud Type Distribution - Scatter Plot */}
              {displayData.fraudTypeData && displayData.fraudTypeData.length > 0 && (
                <div style={styles.chartBox}>
                  <h3 style={styles.chartTitle}>Fraud Type Distribution</h3>
                  {(() => {
                    const total = displayData.fraudTypeData.reduce((sum, item) => sum + item.value, 0);
                    const maxValue = Math.max(...displayData.fraudTypeData.map(e => e.value));
                    const percentages = displayData.fraudTypeData.map(e => (e.value / total) * 100);
                    const minPercentage = Math.min(...percentages);
                    const maxPercentage = Math.max(...percentages);

                    // Colors that complement DAD color scheme (red/navy theme)
                    // Using complementary colors: teal, coral, amber, purple, cyan
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

                    // Prepare scatter plot data with complementary colors and jitter to prevent overlapping
                    const scatterData = displayData.fraudTypeData.map((entry, index) => {
                      const percentage = total > 0 ? ((entry.value / total) * 100) : 0;
                      return {
                        name: entry.name,
                        count: entry.value,
                        percentage: parseFloat(percentage.toFixed(1)),
                        size: entry.value, // For Z-axis (bubble size)
                        color: COMPLEMENTARY_COLORS[index % COMPLEMENTARY_COLORS.length],
                        index: index
                      };
                    });

                    // Add jitter to prevent overlapping points
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

                      // Add small offset to prevent overlap (spread in a circle pattern)
                      const jitterRadius = 0.8; // percentage points
                      const angle = (duplicateIndex * (2 * Math.PI)) / (duplicates.length + 1);
                      const jitterX = duplicateIndex > 0 ? Math.cos(angle) * jitterRadius : 0;
                      const jitterY = duplicateIndex > 0 ? Math.sin(angle) * (jitterRadius * 2) : 0;

                      return {
                        ...entry,
                        percentage: entry.percentage + jitterX,
                        count: entry.count + jitterY
                      };
                    });

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
                              domain={[minPercentage - 2, maxPercentage + 2]}
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
                                        <span style={{ color: primary, fontWeight: 'bold' }}>Percentage:</span> {data.percentage}%
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
                                  {entry.count} cases ({entry.percentage}%)
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
            </>
          )}

          {/* Show fraud-type-specific charts when fraud type filter is active */}
          {displayData.isFraudTypeFiltered && displayData.fraudTypeSpecificData && (
            <>
              {/* 2x2 Matrix: Average Risk Comparison + KPIs */}
              <div style={styles.chartBox}>
                <h3 style={styles.chartTitle}>Average Risk Comparison</h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gridTemplateRows: 'repeat(2, 1fr)',
                  gap: '1.5rem',
                  marginTop: '1rem'
                }}>
                  {/* Top Left: Selected Fraud Type Average Risk */}
                  <div style={{
                    backgroundColor: colors.secondary,
                    padding: '1.5rem',
                    borderRadius: '0.75rem',
                    border: `1px solid ${colors.border}`,
                    textAlign: 'center'
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      color: colors.mutedForeground,
                      marginBottom: '0.5rem'
                    }}>
                      {displayData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}
                    </div>
                    <div style={{
                      fontSize: '2rem',
                      fontWeight: 'bold',
                      color: primary,
                      marginBottom: '0.25rem'
                    }}>
                      {displayData.fraudTypeSpecificData.avgRiskComparison.selectedFraudType}%
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: colors.mutedForeground
                    }}>
                      Average Risk
                    </div>
                  </div>

                  {/* Top Right: All Paystubs Average Risk */}
                  <div style={{
                    backgroundColor: colors.secondary,
                    padding: '1.5rem',
                    borderRadius: '0.75rem',
                    border: `1px solid ${colors.border}`,
                    textAlign: 'center'
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      color: colors.mutedForeground,
                      marginBottom: '0.5rem'
                    }}>
                      All Paystubs
                    </div>
                    <div style={{
                      fontSize: '2rem',
                      fontWeight: 'bold',
                      color: colors.foreground,
                      marginBottom: '0.25rem'
                    }}>
                      {displayData.fraudTypeSpecificData.avgRiskComparison.allPaystubs}%
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: colors.mutedForeground
                    }}>
                      Average Risk
                    </div>
                  </div>

                  {/* Bottom Left: Medium-Risk Cases */}
                  {displayData.fraudTypeSpecificData.kpis && (
                    <div style={{
                      backgroundColor: colors.secondary,
                      padding: '1.5rem',
                      borderRadius: '0.75rem',
                      border: `1px solid ${colors.border}`,
                      textAlign: 'center'
                    }}>
                      <div style={{
                        fontSize: '0.875rem',
                        color: colors.mutedForeground,
                        marginBottom: '0.5rem'
                      }}>
                        Medium-Risk Cases
                      </div>
                      <div style={{
                        fontSize: '2rem',
                        fontWeight: 'bold',
                        color: colors.status.warning || '#FFA726',
                        marginBottom: '0.25rem'
                      }}>
                        {displayData.fraudTypeSpecificData.kpis.mediumRiskCasesCount || 0}
                      </div>
                      <div style={{
                        fontSize: '0.75rem',
                        color: colors.mutedForeground
                      }}>
                        Risk 50-75%
                      </div>
                    </div>
                  )}

                  {/* Bottom Right: High-Risk Cases */}
                  {displayData.fraudTypeSpecificData.kpis && (
                    <div style={{
                      backgroundColor: colors.secondary,
                      padding: '1.5rem',
                      borderRadius: '0.75rem',
                      border: `1px solid ${colors.border}`,
                      textAlign: 'center'
                    }}>
                      <div style={{
                        fontSize: '0.875rem',
                        color: colors.mutedForeground,
                        marginBottom: '0.5rem'
                      }}>
                        High-Risk Cases
                      </div>
                      <div style={{
                        fontSize: '2rem',
                        fontWeight: 'bold',
                        color: primary,
                        marginBottom: '0.25rem'
                      }}>
                        {displayData.fraudTypeSpecificData.kpis.highRiskCasesCount || 0}
                      </div>
                      <div style={{
                        fontSize: '0.75rem',
                        color: colors.mutedForeground
                      }}>
                        Risk ≥ 75%
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* (B) Severity Breakdown for This Fraud Type - Only show when meaningful (more than one category) */}
              {displayData.fraudTypeSpecificData.severityBreakdown && displayData.fraudTypeSpecificData.severityBreakdown.length > 1 && (
                <div style={styles.chartBox}>
                  <h3 style={styles.chartTitle}>Severity Breakdown for {displayData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart>
                      <Pie
                        data={displayData.fraudTypeSpecificData.severityBreakdown}
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
                        {displayData.fraudTypeSpecificData.severityBreakdown.map((entry, index) => (
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
              )}

              {/* (B-alt) Risk Score Distribution - Show when severity breakdown is not meaningful (single category) */}
              {displayData.fraudTypeSpecificData.severityBreakdown && displayData.fraudTypeSpecificData.severityBreakdown.length === 1 && displayData.fraudTypeSpecificData.riskScoreDistribution && displayData.fraudTypeSpecificData.riskScoreDistribution.length > 0 && (
                <div style={styles.chartBox}>
                  <h3 style={styles.chartTitle}>Risk Score Distribution for {displayData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={displayData.fraudTypeSpecificData.riskScoreDistribution} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                      <defs>
                        <linearGradient id="riskDistGradient" x1="0" y1="0" x2="0" y2="1">
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
                        label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar
                        dataKey="count"
                        fill="url(#riskDistGradient)"
                        radius={[8, 8, 0, 0]}
                        name="Paystub Count"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* (C) Monthly Fraud Trend for This Fraud Type */}
              {displayData.fraudTypeSpecificData.monthlyTrend && displayData.fraudTypeSpecificData.monthlyTrend.length > 0 && (
                <div style={styles.chartBox}>
                  <h3 style={styles.chartTitle}>Monthly Trend: {displayData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={displayData.fraudTypeSpecificData.monthlyTrend}>
                      <defs>
                        <linearGradient id="trendLineGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={primary} stopOpacity={0.8} />
                          <stop offset="100%" stopColor={primary} stopOpacity={0.1} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                      <XAxis
                        dataKey="month"
                        tick={{ fill: colors.foreground, fontSize: 11 }}
                        stroke={colors.border}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis
                        tick={{ fill: colors.foreground, fontSize: 12 }}
                        stroke={colors.border}
                        label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Line
                        type="monotone"
                        dataKey="count"
                        stroke={primary}
                        strokeWidth={3}
                        dot={{ fill: primary, r: 5 }}
                        name="Paystub Count"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* (D) Top Employers for This Fraud Type - Only show when NOT filtering by single employer */}
              {!displayData.isSingleEmployerView && displayData.fraudTypeSpecificData.topEmployersForFraudType && displayData.fraudTypeSpecificData.topEmployersForFraudType.length > 0 && (
                <div style={styles.chartBox}>
                  <h3 style={styles.chartTitle}>Top Employers for {displayData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart
                      data={displayData.fraudTypeSpecificData.topEmployersForFraudType}
                      margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                    >
                      <defs>
                        <linearGradient id="employerFraudTypeGradient" x1="0" y1="0" x2="0" y2="1">
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
                        label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar
                        dataKey="count"
                        fill="url(#employerFraudTypeGradient)"
                        name="Paystub Count"
                        radius={[8, 8, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* (D-alt) Employee Risk Distribution - Show when single employer + fraud type selected */}
              {displayData.isSingleEmployerView && displayData.fraudTypeSpecificData.employeeRiskDistribution && displayData.fraudTypeSpecificData.employeeRiskDistribution.length > 0 && (
                <div style={styles.chartBox}>
                  <h3 style={styles.chartTitle}>Employee Risk Distribution for {displayData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart
                      data={displayData.fraudTypeSpecificData.employeeRiskDistribution}
                      layout="vertical"
                      margin={{ top: 20, right: 30, left: 120, bottom: 20 }}
                    >
                      <defs>
                        <linearGradient id="employeeRiskGradient" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor={primary} stopOpacity={0.9} />
                          <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} horizontal={false} />
                      <XAxis
                        type="number"
                        domain={[0, 100]}
                        tick={{ fill: colors.foreground, fontSize: 11 }}
                        stroke={colors.border}
                        label={{ value: 'Risk %', position: 'insideBottom', offset: -5, fill: colors.foreground }}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={110}
                        tick={{ fill: colors.foreground, fontSize: 11 }}
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
                                  {data.name}
                                </p>
                                <p style={{ margin: '4px 0', color: primary }}>
                                  <span style={{ fontWeight: '600' }}>Avg Risk:</span> {data.avgRisk.toFixed(1)}%
                                </p>
                                <p style={{ margin: '4px 0', color: colors.mutedForeground }}>
                                  <span style={{ fontWeight: '600' }}>Cases:</span> {data.count}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar
                        dataKey="avgRisk"
                        fill="url(#employeeRiskGradient)"
                        name="Risk %"
                        radius={[0, 4, 4, 0]}
                      />
                      <ReferenceLine
                        x={50}
                        stroke={colors.status.warning || '#FFA726'}
                        strokeDasharray="5 5"
                        label={{ value: '50%', position: 'top', fill: colors.status.warning }}
                      />
                      <ReferenceLine
                        x={75}
                        stroke={primary}
                        strokeDasharray="5 5"
                        label={{ value: '75%', position: 'top', fill: primary }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
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
    gap: '0.5rem',
    marginBottom: '1.5rem'
  },
  modeButton: {
    flex: 1,
    padding: '0.75rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    cursor: 'pointer',
    transition: 'all 0.3s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontSize: '14px'
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
