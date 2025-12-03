import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { FaUpload, FaCog } from 'react-icons/fa';

const MoneyOrderInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('upload'); // 'upload' or 'api'
  const [moneyOrdersList, setMoneyOrdersList] = useState([]);
  const [allMoneyOrdersData, setAllMoneyOrdersData] = useState([]); // Store full dataset for filtering
  const [loadingMoneyOrdersList, setLoadingMoneyOrdersList] = useState(false);
  const [selectedMoneyOrderId, setSelectedMoneyOrderId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'older'
  const [issuerFilter, setIssuerFilter] = useState(null); // null or issuer name
  const [availableIssuers, setAvailableIssuers] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);

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

  const processData = (rows, selectedIssuer = null) => {
    if (!rows.length) return null;

    // Check if we're in single issuer view
    const isSingleIssuerView = selectedIssuer && selectedIssuer !== '' && selectedIssuer !== 'All Issuers';

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

    // 4. Risk by Issuer (Average risk score per issuer)
    const issuerRisks = {};
    rows.forEach(r => {
      const issuer = r['IssuerName'] || r['money_order_institute'] || r['issuer_name'] || 'Unknown';
      if (!issuerRisks[issuer]) {
        issuerRisks[issuer] = { count: 0, totalRisk: 0 };
      }
      issuerRisks[issuer].count++;
      issuerRisks[issuer].totalRisk += parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
    });
    const riskByIssuerData = Object.entries(issuerRisks)
      .map(([name, data]) => ({
        name,
        avgRisk: ((data.totalRisk / data.count) * 100).toFixed(1),
        count: data.count
      }))
      .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
      .slice(0, 10); // Top 10 issuers

    // 5. Top Fraudulent Issuers (% High-Risk MOs >75%)
    const issuerHighRisk = {};
    rows.forEach(r => {
      const issuer = r['IssuerName'] || r['money_order_institute'] || r['issuer_name'] || 'Unknown';
      const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
      if (!issuerHighRisk[issuer]) {
        issuerHighRisk[issuer] = { total: 0, highRisk: 0 };
      }
      issuerHighRisk[issuer].total++;
      if (risk > 75) {
        issuerHighRisk[issuer].highRisk++;
      }
    });
    const topFraudulentIssuers = Object.entries(issuerHighRisk)
      .map(([name, data]) => ({
        name,
        highRiskPercent: data.total > 0 ? ((data.highRisk / data.total) * 100).toFixed(1) : '0.0',
        highRiskCount: data.highRisk,
        totalCount: data.total
      }))
      .filter(item => item.totalCount > 0)
      .sort((a, b) => parseFloat(b.highRiskPercent) - parseFloat(a.highRiskPercent))
      .slice(0, 10);

    // 6. Top High-Risk Purchasers
    const purchaserRisks = {};
    rows.forEach(r => {
      // Normalize purchaser name - handle multiple field names and trim whitespace
      const purchaser = (r['PurchaserName'] || r['purchaser_name'] || '').trim();
      if (purchaser && purchaser !== '' && purchaser !== 'Unknown' && purchaser.toLowerCase() !== 'unknown') {
        // Use uppercase for consistent grouping (case-insensitive)
        const purchaserKey = purchaser.toUpperCase();
        if (!purchaserRisks[purchaserKey]) {
          purchaserRisks[purchaserKey] = { 
            count: 0, 
            totalRisk: 0, 
            maxRisk: 0,
            originalName: purchaser // Keep original for display
          };
        }
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
        purchaserRisks[purchaserKey].count++;
        purchaserRisks[purchaserKey].totalRisk += risk;
        purchaserRisks[purchaserKey].maxRisk = Math.max(purchaserRisks[purchaserKey].maxRisk, risk);
      }
    });
    const topHighRiskPurchasers = Object.entries(purchaserRisks)
      .map(([key, data]) => ({
        name: data.originalName || key, // Use original name for display
        fullName: data.originalName || key,
        avgRisk: (data.totalRisk / data.count).toFixed(1),
        count: data.count,
        maxRisk: data.maxRisk.toFixed(1)
      }))
      .filter(item => parseFloat(item.avgRisk) >= 50)
      .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
      .slice(0, 10);

    // 7. Top High-Risk Payees
    const payeeRisks = {};
    rows.forEach(r => {
      const payee = r['PayeeName'] || r['payee_name'] || 'Unknown';
      if (payee && payee !== 'Unknown') {
        if (!payeeRisks[payee]) {
          payeeRisks[payee] = { count: 0, totalRisk: 0, highRiskCount: 0 };
        }
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
        payeeRisks[payee].count++;
        payeeRisks[payee].totalRisk += risk;
        if (risk > 75) {
          payeeRisks[payee].highRiskCount++;
        }
      }
    });
    const topHighRiskPayees = Object.entries(payeeRisks)
      .map(([name, data]) => ({
        name,
        fullName: name,
        avgRisk: (data.totalRisk / data.count).toFixed(1),
        count: data.count,
        highRiskCount: data.highRiskCount
      }))
      .filter(item => parseFloat(item.avgRisk) >= 50)
      .sort((a, b) => b.highRiskCount - a.highRiskCount)
      .slice(0, 10);

    // 8. Fraud Trend Over Time (High-Risk Count)
    const fraudOverTime = {};
    rows.forEach(r => {
      const dateStr = r['IssueDate'] || r['issue_date'] || r['created_at'] || '';
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

    // 9. Issuer-Specific Charts (only when single issuer is selected)
    let topRiskyPurchasersForIssuer = [];
    let riskScoreTrendForIssuer = [];

    if (isSingleIssuerView) {
      // Chart A: Top Risky Purchasers (Selected Issuer)
      const purchaserHighRisk = {};
      rows.forEach(r => {
        const purchaser = (r['PurchaserName'] || r['purchaser_name'] || '').trim();
        if (purchaser && purchaser !== '' && purchaser !== 'Unknown') {
          const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
          const recommendation = (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase();
          const isHighRisk = risk >= 0.75 || recommendation !== 'APPROVE';
          
          const purchaserKey = purchaser.toUpperCase();
          if (!purchaserHighRisk[purchaserKey]) {
            purchaserHighRisk[purchaserKey] = {
              originalName: purchaser,
              highRiskCount: 0,
              totalCount: 0
            };
          }
          purchaserHighRisk[purchaserKey].totalCount++;
          if (isHighRisk) {
            purchaserHighRisk[purchaserKey].highRiskCount++;
          }
        }
      });
      
      topRiskyPurchasersForIssuer = Object.entries(purchaserHighRisk)
        .map(([key, data]) => ({
          name: data.originalName || key,
          highRiskCount: data.highRiskCount,
          totalCount: data.totalCount
        }))
        .sort((a, b) => b.highRiskCount - a.highRiskCount)
        .slice(0, 10);

      // Chart B: Risk Score Trend (Selected Issuer)
      const issuerTrendByDay = {};
      rows.forEach(r => {
        const dateStr = r['IssueDate'] || r['issue_date'] || r['created_at'] || '';
        if (dateStr) {
          const date = dateStr.split('T')[0];
          if (!issuerTrendByDay[date]) {
            issuerTrendByDay[date] = { count: 0, totalRisk: 0, highRiskCount: 0 };
          }
          const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
          const recommendation = (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase();
          const isHighRisk = risk >= 0.75 || recommendation !== 'APPROVE';
          
          issuerTrendByDay[date].count++;
          issuerTrendByDay[date].totalRisk += risk;
          if (isHighRisk) {
            issuerTrendByDay[date].highRiskCount++;
          }
        }
      });
      
      riskScoreTrendForIssuer = Object.entries(issuerTrendByDay)
        .map(([date, data]) => ({
          date,
          avgRisk: (data.totalRisk / data.count * 100).toFixed(1),
          highRiskRate: data.count > 0 ? ((data.highRiskCount / data.count) * 100).toFixed(1) : '0.0',
          highRiskCount: data.highRiskCount,
          totalCount: data.count
        }))
        .sort((a, b) => a.date.localeCompare(b.date))
        .slice(-30);
    }

    // 12. High-Risk Count (>75%)
    const highRiskCount = riskScoresPercent.filter(s => s >= 75).length;


    // 14. Summary Metrics
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
      riskByIssuerData,
      topFraudulentIssuers,
      topHighRiskPurchasers,
      topHighRiskPayees,
      fraudTrendData,
      topRiskyPurchasersForIssuer,
      riskScoreTrendForIssuer,
      isSingleIssuerView,
      selectedIssuerName: isSingleIssuerView ? selectedIssuer : null,
      metrics: {
        totalMoneyOrders,
        avgRiskScore,
        approveCount,
        rejectCount,
        escalateCount,
        highRiskCount,
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

        const processed = processData(rows, issuerFilter);
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

  const fetchMoneyOrdersList = async (filter = null, issuer = null) => {
    setLoadingMoneyOrdersList(true);
    setError(null);
    setCsvData(null);
    try {
      // Use relative URL to leverage proxy in package.json
      const url = filter
        ? `/api/money-orders/list?date_filter=${filter}`
        : `/api/money-orders/list`;
      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        // Extract unique issuers from the data
        const issuers = [...new Set(data.data.map(mo => mo.money_order_institute).filter(Boolean))].sort();
        setAvailableIssuers(issuers);
        
        // Store full dataset
        setAllMoneyOrdersData(data.data);
        
        // Apply issuer filter if selected
        let filteredData = data.data;
        const activeIssuerFilter = issuer !== null ? issuer : issuerFilter;
        if (activeIssuerFilter && activeIssuerFilter !== '' && activeIssuerFilter !== 'All Issuers') {
          // Normalize issuer names for comparison
          const normalizedIssuer = activeIssuerFilter.trim();
          filteredData = data.data.filter(mo => {
            const moIssuer = (mo.money_order_institute || '').trim();
            return moIssuer === normalizedIssuer;
          });
        }
        
        setMoneyOrdersList(filteredData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(filter);
        // Auto-load all money orders as insights if data exists
        if (filteredData && filteredData.length > 0) {
          // Pass the active issuer filter to ensure correct chart data
          const issuerToPass = (activeIssuerFilter && activeIssuerFilter !== '' && activeIssuerFilter !== 'All Issuers') 
            ? activeIssuerFilter.trim() 
            : null;
          loadMoneyOrderData(filteredData, issuerToPass);
        } else {
          setError('No money orders found for the selected filters');
        }
      } else {
        setError(data.message || 'Failed to fetch money orders');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to fetch money orders from database');
      console.error('Error fetching money orders:', err);
      setCsvData(null);
    } finally {
      setLoadingMoneyOrdersList(false);
    }
  };

  const handleSearchMoneyOrders = async (query) => {
    if (!query) {
      setIssuerFilter(null);
      fetchMoneyOrdersList(dateFilter);
      return;
    }
    setLoadingMoneyOrdersList(true);
    setError(null);
    setCsvData(null);
    try {
      // Use relative URL to leverage proxy in package.json
      const response = await fetch(`/api/money-orders/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setMoneyOrdersList(data.data);
        // Auto-load search results as insights if data exists
        if (data.data && data.data.length > 0) {
          loadMoneyOrderData(data.data);
        } else {
          setError('No money orders found matching your search');
        }
      } else {
        setError(data.message || 'Search failed');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to search money orders');
      console.error('Error searching money orders:', err);
      setCsvData(null);
    } finally {
      setLoadingMoneyOrdersList(false);
    }
  };

  const loadMoneyOrderData = async (moneyOrders, explicitIssuer = null) => {
    if (!moneyOrders || moneyOrders.length === 0) {
      setError('No money orders selected');
      return;
    }

    try {
      // Use explicit issuer if provided, otherwise use issuerFilter state
      const issuerToUse = explicitIssuer !== null ? explicitIssuer : issuerFilter;
      
      // Transform database records to format expected by processData
      const rows = moneyOrders.map(mo => ({
        'fraud_risk_score': mo.fraud_risk_score || 0,
        'RiskScore': mo.fraud_risk_score || 0,
        'ai_recommendation': mo.ai_recommendation || 'UNKNOWN',
        'Decision': mo.ai_recommendation || 'UNKNOWN',
        'money_order_institute': mo.money_order_institute || 'Unknown',
        'IssuerName': mo.money_order_institute || 'Unknown',
        'issuer_name': mo.money_order_institute || 'Unknown',
        'money_order_number': mo.money_order_number || 'N/A',
        'MoneyOrderNumber': mo.money_order_number || 'N/A',
        'amount': mo.amount || 0,
        'Amount': mo.amount || 0,
        'purchaser_name': mo.purchaser_name || '',
        'PurchaserName': mo.purchaser_name || '',
        'payee_name': mo.payee_name || '',
        'PayeeName': mo.payee_name || '',
        'issue_date': mo.issue_date || '',
        'IssueDate': mo.issue_date || '',
        'created_at': mo.created_at || mo.timestamp || '',
      }));

      // Verify all rows belong to the selected issuer (if filtering by issuer)
      if (issuerToUse && issuerToUse !== '' && issuerToUse !== 'All Issuers') {
        const normalizedIssuer = issuerToUse.trim();
        // Double-check: filter rows to ensure they match the selected issuer
        const filteredRows = rows.filter(r => {
          const rowIssuer = (r['IssuerName'] || r['money_order_institute'] || r['issuer_name'] || '').trim();
          return rowIssuer === normalizedIssuer;
        });
        
        // Debug logging
        console.log('Issuer Filter Debug:', {
          selectedIssuer: normalizedIssuer,
          totalRows: rows.length,
          filteredRows: filteredRows.length,
          sampleIssuers: [...new Set(rows.map(r => r['IssuerName'] || r['money_order_institute'] || 'Unknown'))].slice(0, 5)
        });
        
        if (filteredRows.length === 0) {
          setError(`No money orders found for issuer: ${issuerToUse}. Found issuers: ${[...new Set(rows.map(r => r['IssuerName'] || r['money_order_institute'] || 'Unknown'))].join(', ')}`);
          return;
        }
        
        const processed = processData(filteredRows, normalizedIssuer);
        setCsvData(processed);
      } else {
        const processed = processData(rows, null);
        setCsvData(processed);
      }
      setError(null);
      // Auto-scroll to metrics section
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(`Error processing money orders: ${err.message}`);
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
          {inputMode === 'upload' ? 'Money Order Insights' : 'Money Order Insights'}
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
            Insights
          </button>
          <button
            onClick={() => {
              setInputMode('api');
              setCsvData(null);
              setError(null);
              setIssuerFilter(null);
              setAllMoneyOrdersData([]);
              fetchMoneyOrdersList();
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
                    CSV file with money order analysis data
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
                Search by Purchaser Name:
              </label>
              <input
                type="text"
                placeholder="Search money orders by purchaser name..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  handleSearchMoneyOrders(e.target.value);
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

            {/* Issuer Filter Section */}
            {availableIssuers.length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
                  Filter by Issuer:
                </label>
                <select
                  value={issuerFilter || ''}
                  onChange={(e) => {
                    const selectedIssuer = e.target.value || null;
                    setIssuerFilter(selectedIssuer);
                    // Filter from full dataset by issuer
                    if (selectedIssuer && selectedIssuer !== '' && selectedIssuer !== 'All Issuers') {
                      // Normalize issuer names for comparison (case-insensitive, trim whitespace)
                      const normalizedSelected = selectedIssuer.trim();
                      const filtered = allMoneyOrdersData.filter(mo => {
                        const moIssuer = (mo.money_order_institute || '').trim();
                        return moIssuer === normalizedSelected;
                      });
                      setMoneyOrdersList(filtered);
                      if (filtered.length > 0) {
                        // Pass the selected issuer to ensure correct chart data
                        loadMoneyOrderData(filtered, normalizedSelected);
                      } else {
                        setError('No money orders found for this issuer');
                      }
                    } else {
                      // Show all data - reload from API to ensure fresh data
                      // This ensures we get the full unfiltered dataset
                      fetchMoneyOrdersList(dateFilter, null);
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
                  <option value="">All Issuers</option>
                  {availableIssuers.map((issuer) => (
                    <option key={issuer} value={issuer}>
                      {issuer}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Date Filter Section */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.75rem', fontWeight: '500' }}>
                Filter by Created Date {totalRecords > 0 && <span style={{ color: colors.mutedForeground, fontWeight: '400', fontSize: '0.9rem' }}>({totalRecords} total records)</span>}
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem' }}>
                <button
                  onClick={() => {
                    setDateFilter(null);
                    fetchMoneyOrdersList(null, issuerFilter);
                  }}
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
                  onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== null && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== null && (e.target.style.backgroundColor = colors.secondary)}
                >
                  All Records
                </button>
                <button
                  onClick={() => {
                    setDateFilter('last_30');
                    fetchMoneyOrdersList('last_30', issuerFilter);
                  }}
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
                  onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Last 30
                </button>
                <button
                  onClick={() => {
                    setDateFilter('last_60');
                    fetchMoneyOrdersList('last_60', issuerFilter);
                  }}
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
                  onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Last 60
                </button>
                <button
                  onClick={() => {
                    setDateFilter('last_90');
                    fetchMoneyOrdersList('last_90', issuerFilter);
                  }}
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
                  onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Last 90
                </button>
                <button
                  onClick={() => {
                    setDateFilter('older');
                    fetchMoneyOrdersList('older', issuerFilter);
                  }}
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
                  onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.muted)}
                  onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.secondary)}
                >
                  Older
                </button>
              </div>
            </div>

            {loadingMoneyOrdersList ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <FaCog className="spin" style={{ fontSize: '2rem', color: primary }} />
                <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>Loading money orders...</p>
              </div>
            ) : moneyOrdersList.length > 0 ? (
              <div style={{
                backgroundColor: colors.secondary,
                borderRadius: '0.5rem',
                border: `1px solid ${colors.border}`,
                maxHeight: '400px',
                overflowY: 'auto',
                marginBottom: '1rem',
              }}>
                {moneyOrdersList.map((mo) => (
                  <div
                    key={mo.money_order_id}
                    onClick={() => {
                      setSelectedMoneyOrderId(mo.money_order_id);
                      loadMoneyOrderData(moneyOrdersList.filter(m => m.money_order_id === mo.money_order_id));
                    }}
                    style={{
                      padding: '1rem',
                      borderBottom: `1px solid ${colors.border}`,
                      cursor: 'pointer',
                      transition: 'background-color 0.3s',
                      backgroundColor: selectedMoneyOrderId === mo.money_order_id ? colors.muted : 'transparent',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = colors.muted)}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = selectedMoneyOrderId === mo.money_order_id ? colors.muted : 'transparent')}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <p style={{ color: colors.foreground, fontWeight: '600', margin: '0 0 0.25rem 0' }}>
                          {mo.purchaser_name || 'Unknown Purchaser'}
                        </p>
                        <p style={{ color: colors.mutedForeground, fontSize: '0.875rem', margin: '0' }}>
                          MO #{mo.money_order_number || 'N/A'} • ${mo.amount || 'N/A'} • {mo.money_order_institute || 'Unknown Issuer'}
                        </p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{
                          backgroundColor: mo.fraud_risk_score > 0.5 ? `${primary}20` : `${colors.status.success}20`,
                          color: mo.fraud_risk_score > 0.5 ? primary : colors.status.success,
                          padding: '0.25rem 0.75rem',
                          borderRadius: '0.25rem',
                          fontSize: '0.875rem',
                          fontWeight: '600',
                        }}>
                          {((mo.fraud_risk_score || 0) * 100).toFixed(0)}% Risk
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
                <p>No money orders found in database</p>
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
          {/* SECTION 1: KPI CARDS */}
          <div style={cardStyle}>
            <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>Summary Metrics</h2>
            <div style={metricsGridStyle}>
              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {csvData.metrics.totalMoneyOrders}
                </div>
                <div style={{ color: colors.mutedForeground }}>Total Money Orders</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {csvData.metrics.avgRiskScore}%
                </div>
                <div style={{ color: colors.mutedForeground }}>Avg Risk</div>
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
                <div style={{ color: colors.mutedForeground }}>High-Risk Count</div>
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

          {/* SECTION 3: Issuer Insights */}
          {/* Show issuer comparison charts only when NO specific issuer is selected (All Issuers) */}
          {/* Hide these charts when a single issuer is selected */}
          {(!issuerFilter || issuerFilter === '' || issuerFilter === 'All Issuers') && (
            <>
              {/* Risk by Issuer */}
              {csvData.riskByIssuerData && csvData.riskByIssuerData.length > 0 && (
                <div style={chartContainerStyle}>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
                    Risk Level by Issuer
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={csvData.riskByIssuerData}>
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
                      <Bar dataKey="count" fill={colors.status.success} name="Money Order Count" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Top Fraudulent Issuers (% High-Risk MOs >75%) */}
              {csvData.topFraudulentIssuers && csvData.topFraudulentIssuers.length > 0 && (
                <div style={chartContainerStyle}>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Top Fraudulent Issuers (% High-Risk MOs &gt;75%)</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={csvData.topFraudulentIssuers} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                      <XAxis 
                        type="number" 
                        stroke={colors.mutedForeground}
                        label={{ value: 'High-Risk Percentage (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
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
                          if (name === 'highRiskPercent') return [`${value}%`, 'High-Risk %'];
                          if (name === 'highRiskCount') return [value, 'High-Risk Count'];
                          if (name === 'totalCount') return [value, 'Total MOs'];
                          return [value, name];
                        }}
                        labelFormatter={(label) => `Issuer: ${label}`}
                      />
                      <Bar dataKey="highRiskPercent" fill={primary} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}

          {/* Show issuer-specific charts when a single issuer is selected */}
          {csvData.isSingleIssuerView && (
            <>
              {/* Chart A: Top Risky Purchasers (Selected Issuer) */}
              {csvData.topRiskyPurchasersForIssuer && csvData.topRiskyPurchasersForIssuer.length > 0 && (
                <div style={chartContainerStyle}>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
                    Top Risky Purchasers ({csvData.selectedIssuerName})
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={csvData.topRiskyPurchasersForIssuer} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                      <XAxis 
                        type="number" 
                        stroke={colors.mutedForeground}
                        label={{ value: 'High-Risk Money Orders', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
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
                          if (name === 'highRiskCount') return [`${value} high-risk MOs`, 'High-Risk Count'];
                          if (name === 'totalCount') return [value, 'Total MOs'];
                          return [value, name];
                        }}
                        labelFormatter={(label) => `Purchaser: ${label}`}
                      />
                      <Bar dataKey="highRiskCount" fill={primary} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

            </>
          )}

          {/* SECTION 4: Behavior Insights */}
          {/* Top High-Risk Purchasers - Hide when single issuer is selected (duplicate of issuer-specific chart) */}
          {!csvData.isSingleIssuerView && csvData.topHighRiskPurchasers && csvData.topHighRiskPurchasers.length > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Top High-Risk Purchasers</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={csvData.topHighRiskPurchasers} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
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
                      if (name === 'count') return [value, 'Money Orders'];
                      return [value, name];
                    }}
                    labelFormatter={(label) => `Purchaser: ${label}`}
                  />
                  <Bar dataKey="avgRisk" fill={primary} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top High-Risk Payees */}
          {csvData.topHighRiskPayees && csvData.topHighRiskPayees.length > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Top High-Risk Payees</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={csvData.topHighRiskPayees} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis 
                    type="number" 
                    stroke={colors.mutedForeground}
                    label={{ value: 'High-Risk Count', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
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
                      if (name === 'highRiskCount') return [value, 'High-Risk Count'];
                      if (name === 'count') return [value, 'Total MOs'];
                      if (name === 'avgRisk') return [`${value}%`, 'Avg Risk'];
                      return [value, name];
                    }}
                    labelFormatter={(label) => `Payee: ${label}`}
                  />
                  <Bar dataKey="highRiskCount" fill={primary} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* SECTION 5: Trend Insights */}
          {/* Fraud Trend Over Time - Shows all issuers when no filter, or specific issuer when filtered */}
          {csvData.fraudTrendData && csvData.fraudTrendData.length > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
                High-Risk Money Orders Over Time{csvData.isSingleIssuerView && csvData.selectedIssuerName ? ` (${csvData.selectedIssuerName})` : ''}
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={csvData.fraudTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="date" stroke={colors.mutedForeground} />
                  <YAxis
                    yAxisId="left"
                    stroke={colors.mutedForeground}
                    label={{ value: 'Avg Risk Score (%)', angle: -90, position: 'insideLeft', style: { fill: colors.foreground } }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    stroke={colors.mutedForeground}
                    label={{ value: 'High-Risk Count', angle: 90, position: 'insideRight', style: { fill: colors.foreground } }}
                  />
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

export default MoneyOrderInsights;
