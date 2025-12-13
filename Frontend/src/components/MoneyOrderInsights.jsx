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

const MoneyOrderInsights = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('api'); // 'upload' or 'api'
  const [moneyOrdersList, setMoneyOrdersList] = useState([]);
  const [loadingMoneyOrdersList, setLoadingMoneyOrdersList] = useState(false);
  const [selectedMoneyOrderId, setSelectedMoneyOrderId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null); // null, 'last_30', 'last_60', 'last_90', 'custom'
  const [totalRecords, setTotalRecords] = useState(0);
  const [issuerFilter, setIssuerFilter] = useState(null);
  const [fraudTypeFilter, setFraudTypeFilter] = useState(null);
  const [availableIssuers, setAvailableIssuers] = useState([]);
  const [availableFraudTypes, setAvailableFraudTypes] = useState([]);
  const [allMoneyOrdersData, setAllMoneyOrdersData] = useState([]);
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

    // 3. Risk by Issuer (Average risk score per issuer)
    const issuerRisks = {};
    rows.forEach(r => {
      const issuer = r['IssuerName'] || r['money_order_institute'] || r['issuer_name'] || 'Unknown';
      if (!issuerRisks[issuer]) {
        issuerRisks[issuer] = { count: 0, totalRisk: 0 };
      }
      issuerRisks[issuer].count++;
      issuerRisks[issuer].totalRisk += parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
    });
    
    // Sort issuers by count (most money orders first), then limit to top 5
    const allIssuers = Object.entries(issuerRisks)
      .map(([name, data]) => ({
        name,
        avgRisk: parseFloat(((data.totalRisk / data.count) * 100).toFixed(1)),
        count: data.count
      }))
      .sort((a, b) => b.count - a.count); // Sort by count first
    
    const TOP_ISSUERS_LIMIT = 5;
    const riskByIssuerData = allIssuers.slice(0, TOP_ISSUERS_LIMIT);

    // 4. Top High-Risk Purchasers
    const purchaserRisks = {};
    rows.forEach(r => {
      const purchaser = (r['PurchaserName'] || r['purchaser_name'] || '').trim();
      if (purchaser && purchaser !== '' && purchaser !== 'Unknown') {
        const purchaserKey = purchaser.toUpperCase();
        if (!purchaserRisks[purchaserKey]) {
          purchaserRisks[purchaserKey] = {
            count: 0,
            totalRisk: 0,
            maxRisk: 0,
            originalName: purchaser
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
        name: data.originalName || key,
        fullName: data.originalName || key,
        avgRisk: (data.totalRisk / data.count).toFixed(1),
        count: data.count,
        maxRisk: data.maxRisk.toFixed(1)
      }))
      .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
      .slice(0, 10); // Always show top 10 purchasers by risk

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

    // 6. Fraud Type Distribution
    const fraudTypeCount = {};
    rows.forEach(r => {
      let fraudType = r['fraud_type'] || r['fraud_types'];
      
      // Handle different data formats: string, array, or null/undefined
      if (Array.isArray(fraudType)) {
        fraudType.forEach(ft => {
          const typeStr = String(ft || '').trim();
          if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
            fraudTypeCount[typeStr] = (fraudTypeCount[typeStr] || 0) + 1;
          }
        });
      } else {
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
      .filter(item => item.name && item.name !== 'Unknown Fraud Type' || item.value > 0)
      .sort((a, b) => b.value - a.value);

    // 7. Weekly Trend Data (High-Risk Activity and Average Risk Score)
    const weeklyData = {};
    
    // Helper function to get week start date (Monday)
    const getWeekStart = (date) => {
      const d = new Date(date);
      const day = d.getDay();
      const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
      return new Date(d.setDate(diff));
    };
    
    // Helper function to format week label
    const formatWeekLabel = (weekStart) => {
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 6);
      const monthStart = weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const monthEnd = weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      return `${monthStart} - ${monthEnd}`;
    };
    
    rows.forEach(r => {
      const dateStr = r['IssueDate'] || r['issue_date'] || r['created_at'] || '';
      if (dateStr) {
        const date = new Date(dateStr.split('T')[0]);
        if (isNaN(date.getTime())) return;
        
        const weekStart = getWeekStart(date);
        const weekKey = weekStart.toISOString().split('T')[0];
        
        if (!weeklyData[weekKey]) {
          weeklyData[weekKey] = {
            weekStart: weekStart,
            count: 0,
            highRiskCount: 0,
            rejectCount: 0,
            totalRisk: 0
          };
        }
        
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
        const recommendation = (r['Decision'] || r['ai_recommendation'] || '').toUpperCase();
        
        weeklyData[weekKey].count++;
        weeklyData[weekKey].totalRisk += risk;
        
        // Count high-risk: REJECT recommendation OR risk >= 75%
        if (recommendation === 'REJECT' || risk >= 75) {
          weeklyData[weekKey].highRiskCount++;
        }
        
        if (recommendation === 'REJECT') {
          weeklyData[weekKey].rejectCount++;
        }
      }
    });
    
    // Process weekly data into arrays for charts
    const weeklyTrendData = Object.entries(weeklyData)
      .map(([weekKey, data]) => ({
        weekKey,
        weekLabel: formatWeekLabel(data.weekStart),
        avgRisk: data.count > 0 ? parseFloat((data.totalRisk / data.count).toFixed(1)) : 0,
        highRiskCount: data.highRiskCount,
        rejectCount: data.rejectCount,
        totalCount: data.count
      }))
      .sort((a, b) => a.weekKey.localeCompare(b.weekKey))
      .slice(-12); // Last 12 weeks

    // 8. High-Risk Count (>75%)
    const highRiskCount = riskScoresPercent.filter(s => s >= 75).length;

    // 9. Summary Metrics
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
      riskByIssuerData,
      topHighRiskPurchasers,
      topFraudIncidentPayees,
      fraudTypeData,
      weeklyTrendData,
      metrics: {
        totalMoneyOrders,
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

  const fetchMoneyOrdersList = async (filter = null, issuer = null, customRange = null) => {
    setLoadingMoneyOrdersList(true);
    setError(null);
    setCsvData(null);
    try {
      let url = '/api/money-orders/list';

      const params = new URLSearchParams();

      if (customRange && (customRange.startDate || customRange.endDate)) {
        if (customRange.startDate) params.append('start_date', customRange.startDate);
        if (customRange.endDate) params.append('end_date', customRange.endDate);
      } else if (filter) {
        params.append('date_filter', filter);
      }

      if (params.toString()) {
        url += '?' + params.toString();
      }

      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        const fetchedData = data.data || [];
        setAllMoneyOrdersData(fetchedData);

        // Extract unique issuers from the data
        const uniqueIssuers = [...new Set(fetchedData.map(mo => mo.money_order_institute).filter(Boolean))].sort();
        setAvailableIssuers(uniqueIssuers);

        // Extract unique fraud types from the data
        const uniqueFraudTypes = [...new Set(
          fetchedData
            .map(mo => mo.fraud_type)
            .filter(Boolean)
            .map(ft => ft.trim())
        )].sort();
        setAvailableFraudTypes(uniqueFraudTypes);

        // Apply issuer filter if specified
        let filteredData = fetchedData;
        if (issuer) {
          filteredData = fetchedData.filter(mo => mo.money_order_institute === issuer);
          setIssuerFilter(issuer);
        } else {
          setIssuerFilter(null);
        }

        setMoneyOrdersList(filteredData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(filter);
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
      const response = await fetch(`/api/money-orders/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setMoneyOrdersList(data.data);
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

  const loadMoneyOrderData = async (moneyOrders) => {
    if (!moneyOrders || moneyOrders.length === 0) {
      setError('No money orders selected');
      return;
    }

    try {
      // Transform database records to format expected by processData
      const rows = moneyOrders.map(mo => ({
        'fraud_risk_score': mo.fraud_risk_score || 0,
        'RiskScore': mo.fraud_risk_score || 0,
        'ai_recommendation': mo.ai_recommendation || 'UNKNOWN',
        'Decision': mo.ai_recommendation || 'UNKNOWN',
        'fraud_type': mo.fraud_type || '',
        'fraud_types': mo.fraud_type || '',
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

      const processed = processData(rows);
      setCsvData(processed);
      setError(null);
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(`Error processing money orders: ${err.message}`);
    }
  };

  // Auto-fetch data when component mounts in 'api' mode
  useEffect(() => {
    if (inputMode === 'api' && allMoneyOrdersData.length === 0 && !loadingMoneyOrdersList) {
      fetchMoneyOrdersList();
    }
  }, []); // Empty dependency array - only run on mount

  // Initial data load - process filtered data when allMoneyOrdersData is first loaded
  useEffect(() => {
    if (inputMode === 'api' && allMoneyOrdersData.length > 0 && !processedData) {
      // This handles the initial load case - processedData will handle subsequent filter changes
      const currentFiltered = getFilteredData();
      if (currentFiltered.length > 0) {
        loadMoneyOrderData(currentFiltered);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allMoneyOrdersData.length]);

  // Filter data based on active filters
  const getFilteredData = () => {
    let filtered = allMoneyOrdersData;

    // Filter by issuer
    if (issuerFilter && issuerFilter !== '' && issuerFilter !== 'All Issuers') {
      filtered = filtered.filter(mo => mo.money_order_institute === issuerFilter);
    }

    // Filter by date range
    if (dateFilter) {
      if (dateFilter === 'custom' && (customDateRange.startDate || customDateRange.endDate)) {
        filtered = filtered.filter(mo => {
          const issueDate = new Date(mo.issue_date || mo.created_at || mo.timestamp);
          const startDate = customDateRange.startDate ? new Date(customDateRange.startDate) : null;
          const endDate = customDateRange.endDate ? new Date(customDateRange.endDate) : null;

          if (startDate && endDate) {
            return issueDate >= startDate && issueDate <= endDate;
          } else if (startDate) {
            return issueDate >= startDate;
          } else if (endDate) {
            return issueDate <= endDate;
          }
          return true;
        });
      } else {
        const now = new Date();
        const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        const sixtyDaysAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000);
        const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);

        filtered = filtered.filter(mo => {
          const issueDate = new Date(mo.issue_date || mo.created_at || mo.timestamp);
          if (dateFilter === 'last_30') return issueDate >= thirtyDaysAgo;
          if (dateFilter === 'last_60') return issueDate >= sixtyDaysAgo;
          if (dateFilter === 'last_90') return issueDate >= ninetyDaysAgo;
          return true;
        });
      }
    }

    // Filter by fraud type
    if (fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types') {
      filtered = filtered.filter(mo => {
        const fraudType = mo.fraud_type;
        if (!fraudType) return false;
        const normalizedFilter = fraudTypeFilter.toLowerCase().trim();
        const typeStr = String(fraudType || '').trim().toLowerCase();
        return typeStr === normalizedFilter;
      });
    }

    return filtered;
  };

  const filteredData = getFilteredData();
  
  // Process filtered data on every render
  const processedData = (() => {
    if (inputMode === 'api' && filteredData.length > 0) {
      const rows = filteredData.map(mo => ({
        'fraud_risk_score': mo.fraud_risk_score || 0,
        'RiskScore': mo.fraud_risk_score || 0,
        'ai_recommendation': mo.ai_recommendation || 'UNKNOWN',
        'Decision': mo.ai_recommendation || 'UNKNOWN',
        'fraud_type': mo.fraud_type || '',
        'fraud_types': mo.fraud_type || '',
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
      return processData(rows);
    }
    return null;
  })();
  
  // Use processedData when available (from filters), fallback to csvData (for CSV upload mode)
  const displayData = processedData || csvData;
  
  // Helper functions to determine chart visibility based on filter rules
  const shouldShowChart = {
    // Risk Level by Issuer: Hide when single issuer filter
    riskByIssuer: () => {
      if (issuerFilter && issuerFilter !== '' && issuerFilter !== 'All Issuers') {
        return false;
      }
      return true;
    },
    
    // Fraud Type Distribution: Hide when filtered to single fraud type
    fraudTypeDistribution: () => {
      if (fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types') {
        return false;
      }
      return true;
    },
    
    // Top High-Risk Purchasers: Show always
    topHighRiskPurchasers: () => true,
    
    // Payees with Highest Fraud Incidents: Show always
    topFraudIncidentPayees: () => true,
    
    // AI Decision Breakdown: Hide when filtered by fraud type
    aiDecisionBreakdown: () => {
      if (fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types') {
        return false;
      }
      return true;
    },
    
    // Risk Score Distribution: Always show
    riskScoreDistribution: () => true,
    
    // Time-based charts: Always show
    weeklyTrends: () => true
  };
  
  // Check if we have a single entity filter
  const hasSingleEntityFilter = () => {
    const hasSingleIssuer = issuerFilter && issuerFilter !== '' && issuerFilter !== 'All Issuers';
    const hasSingleFraudType = fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types';
    return hasSingleIssuer || hasSingleFraudType;
  };
  
  // Initial data load - process and set csvData for CSV upload mode
  useEffect(() => {
    if (inputMode === 'api' && allMoneyOrdersData.length > 0 && !processedData) {
      // Only set initial data if we don't have processedData yet
      // This handles the initial load case
    }
  }, [inputMode, allMoneyOrdersData.length, processedData]);

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

  // Styles matching CheckInsights/PaystubInsights
  const filterStyles = {
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
    }
  };

  const renderActiveShape = (props) => {
    const RADIAN = Math.PI / 180;
    const { cx, cy, midAngle, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;
    const sin = Math.sin(-RADIAN * midAngle);
    const cos = Math.cos(-RADIAN * midAngle);
    const sx = cx + (outerRadius + 10) * cos;
    const sy = cy + (outerRadius + 10) * sin;
    const mx = cx + (outerRadius + 30) * cos;
    const my = cy + (outerRadius + 30) * sin;
    const ex = mx + (cos >= 0 ? 1 : -1) * 22;
    const ey = my;
    const textAnchor = cos >= 0 ? 'start' : 'end';

    return (
      <g>
        <text x={cx} y={cy} dy={8} textAnchor="middle" fill={fill} style={{ fontSize: '18px', fontWeight: 'bold' }}>
          {payload.name}
        </text>
        <Sector
          cx={cx}
          cy={cy}
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          startAngle={startAngle}
          endAngle={endAngle}
          fill={fill}
        />
        <Sector
          cx={cx}
          cy={cy}
          startAngle={startAngle}
          endAngle={endAngle}
          innerRadius={outerRadius + 6}
          outerRadius={outerRadius + 10}
          fill={fill}
        />
        <path d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`} stroke={fill} fill="none" />
        <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
        <text x={ex + (cos >= 0 ? 1 : -1) * 12} y={ey} textAnchor={textAnchor} fill={colors.foreground} style={{ fontSize: '14px' }}>
          {`${value} (${(percent * 100).toFixed(1)}%)`}
        </text>
      </g>
    );
  };

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
          Money Order Insights
        </h2>
      </div>

      {/* Filters Section - Matching CheckInsights Style */}
      {inputMode === 'api' && (
        <div style={filterStyles.filtersSection}>
          {availableIssuers.length > 0 && (
            <select
              value={issuerFilter || ''}
              onChange={(e) => setIssuerFilter(e.target.value || null)}
              style={filterStyles.select}
            >
              <option value="">All Issuers</option>
              {availableIssuers.map(issuer => (
                <option key={issuer} value={issuer}>{issuer}</option>
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
                // Don't call fetchMoneyOrdersList - let useEffect handle filtering locally
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
                      // Don't call fetchMoneyOrdersList - let useEffect handle filtering locally
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

          {totalRecords > 0 && (
            <span style={filterStyles.recordCount}>
              ({totalRecords} records)
            </span>
          )}

          <button
            onClick={() => {
              setSearchQuery('');
              setIssuerFilter(null);
              setDateFilter(null);
              setFraudTypeFilter(null);
              setCustomDateRange({ startDate: '', endDate: '' });
              setShowCustomDatePicker(false);
              fetchMoneyOrdersList();
            }}
            style={{
              padding: '8px 16px',
              borderRadius: '4px',
              border: `1px solid ${colors.border}`,
              backgroundColor: colors.secondary,
              color: colors.foreground,
              cursor: 'pointer',
              fontWeight: '500',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.muted}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = colors.secondary}
          >
            <FaRedo /> Reset
          </button>
        </div>
      )}

      {loadingMoneyOrdersList && inputMode === 'api' && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <FaCog className="spin" style={{ fontSize: '2rem', color: primary }} />
          <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>Loading money orders...</p>
        </div>
      )}

      {error && inputMode === 'api' && (
        <div style={{
          backgroundColor: colors.accent.redLight,
          color: colors.accent.red,
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1rem',
          fontWeight: '500',
        }}>
          {error}
        </div>
      )}

      {displayData && (
        <div data-metrics-section>
          {/* SECTION 1: KPI CARDS */}
          <div style={cardStyle}>
            <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>Summary Metrics</h2>
            <div style={metricsGridStyle}>
              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {displayData.metrics.totalMoneyOrders}
                </div>
                <div style={{ color: colors.mutedForeground }}>Total Money Orders</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {displayData.metrics.avgRiskScore}%
                </div>
                <div style={{ color: colors.mutedForeground }}>Avg Risk</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981', marginBottom: '0.5rem' }}>
                  {displayData.metrics.approveCount}
                </div>
                <div style={{ color: colors.mutedForeground }}>Approve</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ef4444', marginBottom: '0.5rem' }}>
                  {displayData.metrics.rejectCount}
                </div>
                <div style={{ color: colors.mutedForeground }}>Reject</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b', marginBottom: '0.5rem' }}>
                  {displayData.metrics.escalateCount}
                </div>
                <div style={{ color: colors.mutedForeground }}>Escalate</div>
              </div>

              <div style={metricCardStyle}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                  {displayData.metrics.highRiskCount || 0}
                </div>
                <div style={{ color: colors.mutedForeground }}>High-Risk Count</div>
              </div>
            </div>
          </div>

          {/* Charts Section - 2 columns grid */}
          <div style={chartsContainerStyle}>
            {/* Row 1: Risk Score Distribution & AI Decision Breakdown */}
            {shouldShowChart.riskScoreDistribution() && displayData.riskDistribution && displayData.riskDistribution.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Score Distribution (All Money Orders)</h3>
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
            )}

            {shouldShowChart.aiDecisionBreakdown() && displayData.recommendationData && displayData.recommendationData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
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
                          fontSize: '13px',
                          fontWeight: '500'
                        }}>
                          {entry.name}: {entry.value} ({percentage}%)
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Row 2: Risk by Issuer */}
            {shouldShowChart.riskByIssuer() && displayData.riskByIssuerData && displayData.riskByIssuerData.length > 0 && (
              <div style={chartBoxStyle}>
                <h3 style={chartTitleStyle}>Risk Level by Issuer</h3>
                <ResponsiveContainer width="100%" height={480}>
                  <BarChart 
                    data={displayData.riskByIssuerData}
                    margin={{ top: 60, right: 30, left: 20, bottom: 120 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                    <XAxis 
                      dataKey="name" 
                      stroke={colors.border}
                      tick={{ fill: colors.foreground, fontSize: 11 }}
                      angle={-45} 
                      textAnchor="end" 
                      height={80}
                      interval={0}
                      tickMargin={8}
                    />
                    <YAxis 
                      stroke={colors.border}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend 
                      verticalAlign="bottom" 
                      height={36}
                      wrapperStyle={{ paddingTop: '30px' }}
                    />
                    <Bar dataKey="avgRisk" fill={colors.status.warning} name="Avg Risk Score (%)" />
                    <Bar dataKey="count" fill={colors.status.success} name="Money Order Count" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Fraud Type Distribution - Scatter Plot */}
            {shouldShowChart.fraudTypeDistribution() && displayData.fraudTypeData && displayData.fraudTypeData.length > 0 && (
              <div style={{
                ...chartBoxStyle,
                gridColumn: issuerFilter ? '1 / -1' : 'auto'
              }}>
                <h3 style={chartTitleStyle}>Fraud Type Distribution</h3>
                {(() => {
                  const total = displayData.fraudTypeData.reduce((sum, item) => sum + item.value, 0);
                  const maxValue = Math.max(...displayData.fraudTypeData.map(e => e.value));
                  const percentages = displayData.fraudTypeData.map(e => (e.value / total) * 100);
                  const minPercentage = Math.min(...percentages);
                  const maxPercentage = Math.max(...percentages);

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
                                      <span style={{ color: primary, fontWeight: 'bold' }}>Percentage:</span> {data.percentage.toFixed(1)}%
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
                                width: '20px',
                                height: '20px',
                                borderRadius: '50%',
                                backgroundColor: entry.color,
                                border: `2px solid ${colors.border}`,
                                flexShrink: 0,
                                marginTop: '2px'
                              }}
                            />
                            <div style={{ flex: 1 }}>
                              <div style={{ fontWeight: '600', fontSize: '13px', color: colors.foreground, marginBottom: '2px' }}>
                                {entry.name}
                              </div>
                              <div style={{ fontSize: '12px', color: colors.mutedForeground }}>
                                {entry.count} occurrence{entry.count !== 1 ? 's' : ''} ({entry.percentage.toFixed(1)}%)
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  );
                })()}
              </div>
            )}

            {/* Row 3: Top High-Risk Purchasers */}
            {shouldShowChart.topHighRiskPurchasers() && displayData.topHighRiskPurchasers && displayData.topHighRiskPurchasers.length > 0 && (() => {
              const topPurchasersData = displayData.topHighRiskPurchasers.slice(0, 10);
              
              return (
                <div style={chartBoxStyle}>
                  <h3 style={chartTitleStyle}>Top High-Risk Purchasers</h3>
                  <ResponsiveContainer width="100%" height={Math.max(320, topPurchasersData.length * 40)}>
                    <BarChart
                      data={topPurchasersData}
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
                                  <span style={{ fontWeight: '600' }}>Money Orders:</span> {data.count}
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
                        {topPurchasersData.map((entry, index) => {
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
              );
            })()}

            {/* Payees with Highest Fraud Incidents (Bullet Chart) */}
            {shouldShowChart.topFraudIncidentPayees() && displayData.topFraudIncidentPayees && displayData.topFraudIncidentPayees.length > 0 && (() => {
              // Check if both issuer and fraud type filters are active
              const hasIssuerFilter = issuerFilter && issuerFilter !== '' && issuerFilter !== 'All Issuers';
              const hasFraudTypeFilter = fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types';
              const bothFiltersActive = hasIssuerFilter && hasFraudTypeFilter;
              
              return (
              <div style={{
                ...chartBoxStyle,
                gridColumn: bothFiltersActive ? '1 / -1' : 'auto'
              }}>
                <h3 style={chartTitleStyle}>Payees with Highest Fraud Incidents</h3>
                <div style={{ padding: '1rem' }}>
                  {displayData.topFraudIncidentPayees.map((payee, index) => {
                    const maxCount = Math.max(...displayData.topFraudIncidentPayees.map(p => p.fraudCount));
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
              );
            })()}
          </div>

          {/* Weekly Trend Charts - Full Width */}
          {shouldShowChart.weeklyTrends() && displayData.weeklyTrendData && displayData.weeklyTrendData.length > 0 && (
            <>
              {/* 1. High-Risk Activity Over Time - Bar Chart */}
              <div style={cardStyle}>
                <h3 style={chartTitleStyle}>High-Risk Activity Over Time</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={displayData.weeklyTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                    <XAxis 
                      dataKey="weekLabel" 
                      stroke={colors.mutedForeground}
                      tick={{ fill: colors.foreground, fontSize: 11 }}
                      angle={-45}
                      textAnchor="end"
                      height={100}
                      interval={0}
                    />
                    <YAxis 
                      stroke={colors.mutedForeground}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground, fontSize: 12 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: colors.card,
                        border: `1px solid ${colors.border}`,
                        color: colors.foreground,
                        borderRadius: '8px'
                      }}
                      formatter={(value, name) => [value, name]}
                      labelFormatter={(label) => `Week: ${label}`}
                    />
                    <Bar 
                      dataKey="highRiskCount" 
                      fill={primary}
                      name="High-Risk Count (REJECT or HIGH)"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar 
                      dataKey="rejectCount" 
                      fill="#dc2626"
                      name="Reject Count"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* 2. Average Risk Score Trend - Line Chart */}
              <div style={cardStyle}>
                <h3 style={chartTitleStyle}>Average Risk Score Trend</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={displayData.weeklyTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                    <XAxis 
                      dataKey="weekLabel" 
                      stroke={colors.mutedForeground}
                      tick={{ fill: colors.foreground, fontSize: 11 }}
                      angle={-45}
                      textAnchor="end"
                      height={100}
                      interval={0}
                    />
                    <YAxis 
                      stroke={colors.mutedForeground}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      label={{ value: 'Average Risk Score (%)', angle: -90, position: 'insideLeft', fill: colors.foreground, fontSize: 12 }}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: colors.card,
                        border: `1px solid ${colors.border}`,
                        color: colors.foreground,
                        borderRadius: '8px'
                      }}
                      formatter={(value) => [`${value}%`, 'Average Risk Score']}
                      labelFormatter={(label) => `Week: ${label}`}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avgRisk" 
                      stroke={primary} 
                      strokeWidth={3} 
                      name="Average Risk Score"
                      dot={{ fill: primary, r: 5, strokeWidth: 2, stroke: colors.card }}
                      activeDot={{ r: 7, strokeWidth: 2, stroke: primary }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default MoneyOrderInsights;
