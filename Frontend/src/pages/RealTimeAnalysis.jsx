import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import EChartsDonut from '../components/EChartsDonut';
import EChartsLine from '../components/EChartsLine';
import EChartsBar from '../components/EChartsBar';
import EChartsSankey from '../components/EChartsSankey';
import EChartsHeatmap from '../components/EChartsHeatmap';
import EChartsGeo from '../components/EChartsGeo';
import {
  FaLink,
  FaUpload,
  FaArrowLeft,
  FaChartBar,
  FaRobot,
  FaFilter,
  FaTimes,
  FaShieldAlt,
  FaExclamationTriangle,
  FaCheckCircle,
  FaChartLine,
  FaLock,
  FaBan,
  FaGlobeAmericas,
  FaMobileAlt,
  FaBolt,
  FaFire,
  FaStore,
  FaDollarSign,
  FaUserPlus,
  FaPlane,
  FaCreditCard,
  FaExchangeAlt,
  FaLayerGroup,
  FaCalculator,
  FaMoon,
  FaClock
} from 'react-icons/fa';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
  Sankey
} from 'recharts';
import { analyzeRealTimeTransactions, regeneratePlotsWithFilters, getFilterOptions } from '../services/api';

const STANDARD_FRAUD_REASONS = [
  'Suspicious login',
  'Account takeover',
  'Unusual location',
  'Unusual device',
  'Velocity abuse',
  'Transaction burst',
  'High-risk merchant',
  'Unusual amount',
  'New payee spike',
  'Cross-border anomaly',
  'Card-not-present risk',
  'Money mule pattern',
  'Structuring / smurfing',
  'Round-dollar pattern',
  'Night-time activity'
];

const plotColorPalette = ['#10b981', '#ef4444', '#60a5fa', '#f97316', '#a78bfa', '#fbbf24'];

const renderHeatmapCellColor = (value) => {
  if (value === null || value === undefined) return 'rgba(148, 163, 184, 0.2)';
  const normalized = Math.max(-1, Math.min(1, value));
  const hue = normalized > 0 ? 10 : 220;
  const intensity = Math.round(Math.abs(normalized) * 70) + 30;
  return `hsl(${hue}, 70%, ${100 - intensity}%)`;
};

const getInsightPoints = (insightsText) => {
  if (!insightsText) return [];

  const points = [];
  const numberedMatches = [...insightsText.matchAll(/\*\*(\d+)\.\s*(.+?)(?=(\*\*\d+\.)|$)/gs)];

  if (numberedMatches.length > 0) {
    numberedMatches.forEach((match) => {
      const number = match[1];
      const content = match[2] || '';

      const cleaned = content
        .replace(/\*\*/g, '')
        .replace(/–/g, '-')
        .replace(/\s+/g, ' ')
        .trim();

      const subSegments = cleaned.split(/\s+-\s+/).map((segment) => segment.trim()).filter(Boolean);

      subSegments.forEach((segment, idx) => {
        if (idx === 0) {
          points.push(`${number}. ${segment}`);
        } else {
          points.push(`- ${segment}`);
        }
      });
    });
    return points;
  }

  let normalized = insightsText
    .replace(/\*\*/g, '')
    .replace(/•/g, '-')
    .replace(/–/g, '-')
    .trim();

  normalized = normalized
    .replace(/(?=\d+\.)/g, '\n')
    .replace(/\s+-\s+/g, '\n- ')
    .replace(/ - /g, '\n- ')
    .replace(/\. -/g, '.\n-')
    .replace(/;\s*/g, ';\n');

  return normalized
    .split(/\n+/)
    .map((segment) => segment.trim())
    .filter(Boolean);
};

const RealTimeAnalysis = () => {
  const navigate = useNavigate();
  const [bankingUrl, setBankingUrl] = useState('');
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [showInsights, setShowInsights] = useState(false);
  const [csvPreview, setCsvPreview] = useState(null);
  const [hoveredPlotIndex, setHoveredPlotIndex] = useState(null);
  const [zoomedPlot, setZoomedPlot] = useState(null);
  const [filters, setFilters] = useState({
    amountRange: '',
    fraudProbabilityRange: '',
    category: '',
    merchant: '',
    city: '',
    country: '',
    fraudReason: '',
    dateStart: '',
    dateEnd: '',
    fraudOnly: false,
    legitimateOnly: false,
  });
  const [filterOptions, setFilterOptions] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Map fraud pattern types to Font Awesome icons
  const getFraudPatternIcon = (patternType) => {
    const iconMap = {
      'Suspicious login': FaLock,
      'Account takeover': FaBan,
      'Unusual location': FaGlobeAmericas,
      'Unusual device': FaMobileAlt,
      'Velocity abuse': FaBolt,
      'Transaction burst': FaFire,
      'High-risk merchant': FaStore,
      'Unusual amount': FaDollarSign,
      'New payee spike': FaUserPlus,
      'Cross-border anomaly': FaPlane,
      'Card-not-present risk': FaCreditCard,
      'Money mule pattern': FaExchangeAlt,
      'Structuring / smurfing': FaLayerGroup,
      'Round-dollar pattern': FaCalculator,
      'Night-time activity': FaMoon,
      'High Night-Time Fraud Activity': FaMoon,
      'Elevated Weekend Fraud Activity': FaClock,
      'High-Value Fraud Detected': FaDollarSign,
      'CRITICAL: Extremely High Fraud Rate Detected': FaExclamationTriangle,
      'HIGH RISK: Elevated Fraud Activity': FaExclamationTriangle,
      'MODERATE RISK: Above-Normal Fraud Levels': FaExclamationTriangle,
      'LOW RISK: Normal Fraud Levels': FaCheckCircle
    };
    return iconMap[patternType] || FaShieldAlt;
  };
  const [filteredPlots, setFilteredPlots] = useState(null);
  const [regeneratingPlots, setRegeneratingPlots] = useState(false);

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  const renderMarkdownText = (text) => {
    if (!text) return null;

    // Split by lines but preserve structure
    const lines = text.split('\n');

    return lines.map((line, idx) => {
      // Remove markdown bold syntax
      const cleanLine = line.replace(/\*\*/g, '');

      // Check if it's a bullet point
      if (cleanLine.trim().startsWith('-') || cleanLine.trim().startsWith('•')) {
        const content = cleanLine.replace(/^[-•]\s*/, '').trim();
        if (content) {
          return (
            <div key={idx} style={{
              marginLeft: '1rem',
              marginBottom: '0.5rem',
              display: 'flex',
              gap: '0.5rem'
            }}>
              <span style={{ color: colors.mutedForeground }}>•</span>
              <span>{content}</span>
            </div>
          );
        }
      }

      // Check if it's a numbered item
      const numberedMatch = cleanLine.match(/^(\d+)\.\s*(.+)/);
      if (numberedMatch) {
        return (
          <div key={idx} style={{
            marginBottom: '0.75rem',
            fontWeight: '600'
          }}>
            <span style={{ color: primary }}>{numberedMatch[1]}. </span>
            <span>{numberedMatch[2]}</span>
          </div>
        );
      }

      // Regular line
      if (cleanLine.trim()) {
        return (
          <div key={idx} style={{ marginBottom: '0.5rem' }}>
            {cleanLine}
          </div>
        );
      }

      return null;
    }).filter(Boolean);
  };

  const formatFraudReason = (fraudType) => {
    if (!fraudType) return 'N/A';
    if (fraudType === 'legitimate') return 'Legitimate';
    if (fraudType.includes(' ')) return fraudType;
    return fraudType
      .split('_')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  };

  const topFraudCases = analysisResult?.transactions
    ? [...analysisResult.transactions]
        .filter((t) => t.is_fraud === 1)
        .sort((a, b) => (b.fraud_probability || 0) - (a.fraud_probability || 0))
        .slice(0, 4)
    : [];

  const fraudReasonBreakdown =
    analysisResult?.fraud_detection?.fraud_reason_breakdown ||
    analysisResult?.fraud_detection?.fraud_type_breakdown ||
    [];
  const agentInsights = analysisResult?.agent_analysis?.detailed_insights || '';
  const insightPoints = getInsightPoints(agentInsights);
  const reasonCountMap = useMemo(() => {
    const map = {};
    fraudReasonBreakdown.forEach((pattern) => {
      const rawKey = pattern.label || pattern.type;
      if (!rawKey) return;
      const formattedKey = formatFraudReason(rawKey);
      map[formattedKey] = (map[formattedKey] || 0) + (pattern.count || 0);
    });
    return map;
  }, [fraudReasonBreakdown]);

  const fraudReasonChips = useMemo(() => {
    const unique = new Set(STANDARD_FRAUD_REASONS);
    Object.keys(reasonCountMap).forEach((reason) => unique.add(reason));
    return Array.from(unique);
  }, [reasonCountMap]);

  const renderPlotVisualization = (plot, options = {}) => {
    const height = options.height || 450;
    const renderFallback = (message) => (
      <div style={styles.missingPlot}>
        {message || 'No visualization data available'}
      </div>
    );

    // Debug: Log plot structure
    console.log('Rendering plot:', {
      title: plot.title,
      type: plot.type,
      hasData: !!plot.data,
      dataLength: Array.isArray(plot.data) ? plot.data.length : 'not array'
    });

    if (!plot.type) {
      console.error('Plot missing type property:', plot);
    }

    switch (plot.type) {
      case 'donut': {
        const data = Array.isArray(plot.data) ? plot.data.filter(Boolean) : [];
        if (data.length === 0) {
          return renderFallback('No distribution data available');
        }
        console.log('🔥 DONUT DATA:', data);
        return <EChartsDonut data={data} title={plot.title} height={height} />;
      }
      case 'line_trend': {
        const data = Array.isArray(plot.data) ? plot.data.filter(Boolean) : [];
        if (data.length === 0) {
          return renderFallback('No trend data available');
        }
        console.log('🔥 LINE DATA:', data);
        return <EChartsLine data={data} title={plot.title} height={height} />;
      }
      case 'heatmap': {
        const xLabels = Array.isArray(plot.xLabels) ? plot.xLabels : [];
        const yLabels = Array.isArray(plot.yLabels) ? plot.yLabels : [];
        const dataPoints = Array.isArray(plot.data) ? plot.data : [];

        if (
          xLabels.length === 0 ||
          yLabels.length === 0 ||
          dataPoints.length === 0
        ) {
          return renderFallback('No correlation data available');
        }

        const matrix = yLabels.map((yLabel) =>
          xLabels.map((xLabel) => {
            const cell = dataPoints.find(
              (item) => item.x === xLabel && item.y === yLabel
            );
            return cell ? cell.value : 0;
          })
        );

        console.log('🔥 HEATMAP DATA:', { xLabels, yLabels, matrix });

        return <EChartsHeatmap data={{ matrix, labels: xLabels }} title={plot.title} height={height} />;
      }
      case 'geo_scatter': {
        const data = Array.isArray(plot.data) ? plot.data.filter(Boolean) : [];
        if (data.length === 0) {
          return renderFallback('No location data available');
        }
        console.log('🔥 GEO DATA:', data);
        return <EChartsGeo data={data} title={plot.title} height={height} />;
      }
      case 'bar_reasons': {
        const data = Array.isArray(plot.data) ? plot.data.filter(Boolean) : [];
        if (data.length === 0) {
          return renderFallback('No breakdown data available');
        }
        console.log('🔥 BAR DATA:', data);
        return <EChartsBar data={data} title={plot.title} height={height} />;
      }
      case 'sankey': {
        if (
          !plot.data ||
          !Array.isArray(plot.data.nodes) ||
          !Array.isArray(plot.data.links) ||
          plot.data.nodes.length === 0 ||
          plot.data.links.length === 0
        ) {
          return renderFallback('No flow data available');
        }
        console.log('🔥 SANKEY DATA:', plot.data);
        return <EChartsSankey data={plot.data} title={plot.title} height={height} />;
      }
      default:
        return renderFallback(`No visualization available for plot type: ${plot.type || 'unknown'}`);
    }
  };

  const handleDownloadCSV = () => {
    console.log('Download CSV clicked');
    console.log('Analysis result:', analysisResult);
    console.log('Transactions:', analysisResult?.transactions);
    console.log('Transactions length:', analysisResult?.transactions?.length);

    if (!analysisResult?.transactions?.length) {
      console.error('No transactions available for download');
      setError('No transactions available for download');
      return;
    }

    try {
      const rows = analysisResult.transactions;
      const headers = Object.keys(rows[0] || {});

      console.log('Headers:', headers);
      console.log('Total rows:', rows.length);

      const escapeValue = (value) => {
        if (value === null || value === undefined) return '';
        if (typeof value === 'object') {
          try {
            return JSON.stringify(value);
          } catch {
            return String(value);
          }
        }
        return String(value);
      };

      const headerRow = headers.join(',');
      const dataRows = rows.map((row) =>
        headers
          .map((key) => {
            const rawValue = escapeValue(row[key]);
            const safeValue = rawValue.replace(/"/g, '""');
            return `"${safeValue}"`;
          })
          .join(',')
      );

      const csvContent = [headerRow, ...dataRows].join('\n');
      console.log('CSV content length:', csvContent.length);

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `real_time_transactions_${Date.now()}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      console.log('CSV download initiated successfully');
    } catch (err) {
      console.error('Error generating CSV:', err);
      setError(`Failed to download CSV: ${err.message}`);
    }
  };

  

  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    // TODO: Implement URL connection logic
    console.log('Connecting to:', bankingUrl);
    setLoading(false);
  };

  const parseCSVPreview = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n').filter(line => line.trim());

      if (lines.length === 0) {
        setError('CSV file is empty');
        return;
      }

      // Parse header
      const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));

      // Parse rows (limit to first 10 for preview)
      const rows = lines.slice(1, 11).map(line => {
        const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
        const row = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        return row;
      });

      // Calculate statistics
      const totalRows = lines.length - 1; // excluding header
      const totalColumns = headers.length;

      // Count fraud transactions (if applicable)
      let fraudCount = 0;
      rows.forEach(row => {
        // Check for high-risk indicators
        const amount = parseFloat(row.amount || row.Amount || 0);
        const category = (row.category || row.Category || '').toLowerCase();
        const merchant = (row.merchant || row.Merchant || '').toLowerCase();

        if (amount > 5000 ||
            category.includes('gambling') ||
            category.includes('cryptocurrency') ||
            merchant.includes('unknown')) {
          fraudCount++;
        }
      });

      // Detect date range
      let dateRange = 'N/A';
      const dateColumn = headers.find(h =>
        h.toLowerCase().includes('date') ||
        h.toLowerCase().includes('time')
      );

      if (dateColumn) {
        const dates = rows.map(r => r[dateColumn]).filter(d => d);
        if (dates.length > 0) {
          dateRange = `${dates[0]} to ${dates[dates.length - 1]}`;
        }
      }

      // Count non-null values per column
      const columnInfo = headers.map(header => {
        const nonNullCount = rows.filter(row => row[header] && row[header] !== '').length;
        const nullCount = rows.length - nonNullCount;

        // Determine data type
        let dataType = 'object';
        const firstValue = rows.find(row => row[header])?.[header];
        if (firstValue) {
          if (!isNaN(firstValue) && !isNaN(parseFloat(firstValue))) {
            dataType = 'float64';
          } else if (firstValue.match(/^\d{4}-\d{2}-\d{2}/)) {
            dataType = 'datetime64[ns]';
          }
        }

        return {
          name: header,
          dataType,
          nonNullCount: totalRows, // Use total rows, not preview
          nullCount: 0
        };
      });

      setCsvPreview({
        headers,
        rows,
        totalRows,
        totalColumns,
        fraudCount,
        dateRange,
        columnInfo
      });
    };

    reader.readAsText(file);
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setAnalysisResult(null);
      setShowInsights(false);
      parseCSVPreview(selectedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile);
      setError(null);
      setAnalysisResult(null);
      setShowInsights(false);
      parseCSVPreview(droppedFile);
    } else {
      setError('Please upload a CSV file');
    }
  };

  const handleUploadDifferentFile = () => {
    setFile(null);
    setCsvPreview(null);
    setAnalysisResult(null);
    setShowInsights(false);
    setError(null);
  };

  const handleFilterChange = (filterName, value) => {
    let processedValue = value;
    
    // Validate fraud probability fields (must be between 0 and 1)
    if (filterName === 'fraudProbabilityMin' || filterName === 'fraudProbabilityMax') {
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        // Clamp between 0 and 1
        processedValue = Math.max(0, Math.min(1, numValue)).toString();
      } else if (value === '' || value === '.') {
        processedValue = value; // Allow empty or partial input
      } else {
        return; // Invalid input, don't update
      }
    }
    
    setFilters(prev => ({
      ...prev,
      [filterName]: processedValue
    }));
  };

  const resetFilters = () => {
    setFilters({
      amountRange: '',
      fraudProbabilityRange: '',
      category: '',
      merchant: '',
      city: '',
      country: '',
      fraudReason: '',
      dateStart: '',
      dateEnd: '',
      fraudOnly: false,
      legitimateOnly: false,
    });
  };

  const getFilteredTransactions = () => {
    if (!analysisResult?.transactions) return [];

    let filtered = [...analysisResult.transactions];

    // Amount range filter
    if (filters.amountRange !== '') {
      const range = JSON.parse(filters.amountRange);
      filtered = filtered.filter(t => t.amount >= range.min && t.amount <= range.max);
    }

    // Fraud probability range filter
    if (filters.fraudProbabilityRange !== '') {
      const range = JSON.parse(filters.fraudProbabilityRange);
      filtered = filtered.filter(t => t.fraud_probability >= range.min && t.fraud_probability <= range.max);
    }

    // Category filter
    if (filters.category !== '') {
      filtered = filtered.filter(t => t.category === filters.category);
    }

    // Merchant filter
    if (filters.merchant !== '') {
      filtered = filtered.filter(t => t.merchant === filters.merchant);
    }

    // City filter
    if (filters.city !== '') {
      const cityField = t => t.transaction_city || t.transaction_location_city || t.transactionlocationcity;
      filtered = filtered.filter(t => cityField(t) === filters.city);
    }

    // Country filter
    if (filters.country !== '') {
      const countryField = t => t.transaction_country || t.transaction_location_country || t.transactionlocationcountry;
      filtered = filtered.filter(t => countryField(t) === filters.country);
    }

    // Fraud reason filter
    if (filters.fraudReason !== '') {
      filtered = filtered.filter(t => t.fraud_reason === filters.fraudReason);
    }

    // Date filter
    if (filters.dateStart !== '' || filters.dateEnd !== '') {
      filtered = filtered.filter(t => {
        if (!t.timestamp) return true;
        const txnDate = new Date(t.timestamp);
        if (isNaN(txnDate.getTime())) return true;
        
        let isWithinRange = true;
        if (filters.dateStart !== '') {
          const startDate = new Date(`${filters.dateStart}T00:00:00`);
          if (!isNaN(startDate.getTime())) {
            isWithinRange = isWithinRange && txnDate >= startDate;
          }
        }
        if (filters.dateEnd !== '' && isWithinRange) {
          const endDate = new Date(`${filters.dateEnd}T23:59:59.999`);
          if (!isNaN(endDate.getTime())) {
            isWithinRange = isWithinRange && txnDate <= endDate;
          }
        }
        return isWithinRange;
      });
    }

    // Fraud/Legitimate only filters
    if (filters.fraudOnly) {
      filtered = filtered.filter(t => t.is_fraud === 1);
    }
    if (filters.legitimateOnly) {
      filtered = filtered.filter(t => t.is_fraud === 0);
    }

    return filtered;
  };

  const getFilteredStatistics = () => {
    const filtered = getFilteredTransactions();
    const fraudTransactions = filtered.filter(t => t.is_fraud === 1);
    const legitTransactions = filtered.filter(t => t.is_fraud === 0);

    const totalAmount = filtered.reduce((sum, t) => sum + t.amount, 0);
    const fraudAmount = fraudTransactions.reduce((sum, t) => sum + t.amount, 0);
    const legitAmount = legitTransactions.reduce((sum, t) => sum + t.amount, 0);

    return {
      total_count: filtered.length,
      fraud_count: fraudTransactions.length,
      legitimate_count: legitTransactions.length,
      fraud_percentage: filtered.length > 0 ? (fraudTransactions.length / filtered.length * 100).toFixed(2) : 0,
      legitimate_percentage: filtered.length > 0 ? (legitTransactions.length / filtered.length * 100).toFixed(2) : 0,
      total_amount: totalAmount,
      total_fraud_amount: fraudAmount,
      total_legitimate_amount: legitAmount,
    };
  };

  const getAvailableCategories = () => {
    if (!analysisResult?.transactions) return [];
    const categories = new Set(
      analysisResult.transactions
        .map(t => t.category)
        .filter(c => c && c !== 'N/A')
    );
    return Array.from(categories).sort();
  };

  const activeFilterCount = Object.entries(filters).filter(([key, value]) => {
    if (typeof value === 'boolean') return value;
    return value !== '';
  }).length;

  const handleRegeneratePlots = async () => {
    if (!analysisResult?.transactions) return;

    setRegeneratingPlots(true);
    try {
      // Convert filters to backend format
      const backendFilters = {
        category: filters.category || null,
        merchant: filters.merchant || null,
        city: filters.city || null,
        country: filters.country || null,
        fraud_reason: filters.fraudReason || null,
        date_start: filters.dateStart || null,
        date_end: filters.dateEnd || null,
        fraud_only: filters.fraudOnly || false,
        legitimate_only: filters.legitimateOnly || false,
      };

      // Handle amount range
      if (filters.amountRange) {
        const range = JSON.parse(filters.amountRange);
        backendFilters.amount_min = range.min;
        backendFilters.amount_max = range.max;
      }

      // Handle fraud probability range
      if (filters.fraudProbabilityRange) {
        const range = JSON.parse(filters.fraudProbabilityRange);
        backendFilters.fraud_probability_min = range.min;
        backendFilters.fraud_probability_max = range.max;
      }

      // Remove null values
      Object.keys(backendFilters).forEach(key => {
        if (backendFilters[key] === null || backendFilters[key] === '') {
          delete backendFilters[key];
        }
      });

      console.log('Regenerating plots with filters:', backendFilters);
      console.log('Sending transactions:', analysisResult.transactions.length);

      const result = await regeneratePlotsWithFilters(analysisResult.transactions, backendFilters);
      
      if (result.success) {
        console.log('Received filtered plots:', result.plots?.length || 0);
        if (result.plots && result.plots.length > 0) {
          setFilteredPlots(result.plots);
          setError(null); // Clear any previous errors
        } else {
          setFilteredPlots([]);
          setError('No plots generated. The filters may have excluded all transactions. Try adjusting your filter criteria.');
        }
      } else {
        console.error('Failed to regenerate plots:', result.error);
        setError(result.error || 'Failed to regenerate plots');
        setFilteredPlots(null);
      }
    } catch (err) {
      console.error('Error regenerating plots:', err);
      setError(err.error || err.message || 'Failed to regenerate plots');
    } finally {
      setRegeneratingPlots(false);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await analyzeRealTimeTransactions(file);

      if (result.success) {
        console.log('Analysis result received:', {
          hasInsights: !!result.insights,
          plotsCount: result.insights?.plots?.length || 0,
          firstPlot: result.insights?.plots?.[0]
        });
        setAnalysisResult(result);
        setShowInsights(false);

        // Fetch filter options from the transactions
        try {
          const filterOptionsResult = await getFilterOptions(result.transactions);
          if (filterOptionsResult.success) {
            setFilterOptions(filterOptionsResult.filter_options);
            console.log('Filter options loaded:', filterOptionsResult.filter_options);
          }
        } catch (filterErr) {
          console.warn('Failed to load filter options:', filterErr);
          // Don't fail the whole analysis if filter options fail
        }
      } else {
        setError(result.error || 'Analysis failed');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      let errorMessage = 'Failed to analyze transactions';

      if (err.message && err.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please make sure the backend API server is running on http://localhost:5001';
      } else if (err.error) {
        errorMessage = err.error;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const styles = {
    container: {
      minHeight: '100vh',
      backgroundColor: colors.background,
      background: colors.gradients.dark,
      padding: '2rem',
    },
    backButton: {
      backgroundColor: 'transparent',
      color: colors.foreground,
      border: `2px solid ${colors.border}`,
      padding: '0.75rem 1.5rem',
      borderRadius: '9999px',
      fontSize: '0.95rem',
      fontWeight: '600',
      cursor: 'pointer',
      marginBottom: '2rem',
      transition: 'all 0.3s',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.5rem',
    },
    header: {
      marginBottom: '2rem',
    },
    title: {
      fontSize: '2rem',
      fontWeight: '700',
      color: colors.foreground,
      marginBottom: '0.5rem',
    },
    section: {
      backgroundColor: colors.card,
      borderRadius: '1rem',
      padding: '2.5rem',
      marginBottom: '1.5rem',
      border: `1px solid ${colors.border}`,
    },
    sectionHeader: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      marginBottom: '1rem',
      paddingBottom: '1rem',
      borderBottom: `2px solid ${colors.border}`,
    },
    sectionIcon: {
      fontSize: '1.5rem',
      color: primary,
    },
    sectionTitle: {
      fontSize: '1.25rem',
      fontWeight: '600',
      color: colors.foreground,
      margin: 0,
    },
    sectionSubtitle: {
      fontSize: '0.9rem',
      color: colors.mutedForeground,
      margin: '0.5rem 0 1.5rem 0',
    },
    formGroup: {
      marginBottom: '1rem',
    },
    label: {
      display: 'block',
      fontSize: '0.9rem',
      fontWeight: '500',
      color: colors.foreground,
      marginBottom: '0.5rem',
    },
    input: {
      width: '100%',
      padding: '0.875rem 1rem',
      fontSize: '1rem',
      border: `2px solid ${colors.border}`,
      borderRadius: '0.5rem',
      backgroundColor: colors.muted,
      color: colors.foreground,
      transition: 'all 0.3s',
      boxSizing: 'border-box',
    },
    submitButton: {
      backgroundColor: primary,
      color: colors.primaryForeground,
      padding: '0.875rem 2rem',
      borderRadius: '9999px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '1rem',
      fontWeight: '600',
      width: '100%',
      transition: 'all 0.3s',
      boxShadow: `0 0 20px ${primary}40`,
      marginTop: '1rem',
    },
    orDivider: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      margin: '2rem 0',
      position: 'relative',
    },
    orText: {
      backgroundColor: colors.background,
      padding: '0.5rem 1.5rem',
      borderRadius: '9999px',
      fontSize: '0.9rem',
      fontWeight: '600',
      color: colors.mutedForeground,
      border: `2px solid ${colors.border}`,
    },
    uploadArea: {
      border: `2px dashed ${isDragging ? primary : colors.border}`,
      borderRadius: '1rem',
      padding: '3rem 2rem',
      textAlign: 'center',
      cursor: 'pointer',
      transition: 'all 0.3s',
      backgroundColor: isDragging ? `${primary}10` : colors.muted,
    },
    uploadIcon: {
      fontSize: '3rem',
      color: colors.mutedForeground,
      marginBottom: '1rem',
    },
    uploadText: {
      fontSize: '1rem',
      fontWeight: '600',
      color: colors.foreground,
      marginBottom: '0.5rem',
    },
    uploadSubtext: {
      fontSize: '0.85rem',
      color: colors.mutedForeground,
      marginBottom: '1.5rem',
    },
    browseButton: {
      backgroundColor: 'transparent',
      color: primary,
      border: `2px solid ${primary}`,
      padding: '0.75rem 2rem',
      borderRadius: '9999px',
      fontSize: '0.95rem',
      fontWeight: '600',
      cursor: 'pointer',
      transition: 'all 0.3s',
    },
    fileName: {
      marginTop: '1rem',
      padding: '1rem',
      backgroundColor: colors.background,
      borderRadius: '0.5rem',
      fontSize: '0.9rem',
      color: colors.foreground,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    analyzeButton: {
      backgroundColor: primary,
      color: colors.primaryForeground,
      padding: '0.75rem 2rem',
      borderRadius: '9999px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '0.95rem',
      fontWeight: '600',
      transition: 'all 0.3s',
      boxShadow: `0 0 20px ${primary}40`,
    },
    errorBox: {
      backgroundColor: '#fee',
      color: '#c00',
      padding: '1rem',
      borderRadius: '0.5rem',
      marginTop: '1rem',
      border: '1px solid #fcc',
    },
    resultSummary: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1rem',
      marginBottom: '2rem',
    },
    statCard: {
      backgroundColor: colors.muted,
      padding: '1.5rem',
      borderRadius: '0.75rem',
      border: `1px solid ${colors.border}`,
    },
    statLabel: {
      fontSize: '0.85rem',
      color: colors.mutedForeground,
      marginBottom: '0.5rem',
    },
    statValue: {
      fontSize: '1.75rem',
      fontWeight: '700',
      color: colors.foreground,
    },
    fraudStat: {
      color: '#ef4444',
    },
    legitimateStat: {
      color: '#10b981',
    },
    buttonGroup: {
      display: 'flex',
      gap: '1rem',
      marginTop: '1.5rem',
    },
    insightsButton: {
      backgroundColor: '#3b82f6',
      color: 'white',
      padding: '0.875rem 2rem',
      borderRadius: '9999px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '1rem',
      fontWeight: '600',
      transition: 'all 0.3s',
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.5rem',
    },
    downloadButton: {
      backgroundColor: '#22c55e',
      color: '#052e16',
      padding: '0.875rem 2rem',
      borderRadius: '9999px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '1rem',
      fontWeight: '600',
      transition: 'all 0.3s',
      boxShadow: '0 0 20px rgba(34, 197, 94, 0.4)',
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.5rem',
    },
    transactionList: {
      maxHeight: '400px',
      overflowY: 'auto',
      marginTop: '1rem',
    },
    transactionItem: {
      backgroundColor: colors.muted,
      padding: '1rem',
      borderRadius: '0.5rem',
      marginBottom: '0.75rem',
      border: `1px solid ${colors.border}`,
    },
    fraudTypeSection: {
      marginTop: '1.5rem',
    },
    fraudTypeTitle: {
      color: colors.foreground,
      fontSize: '1rem',
      fontWeight: '600',
      marginBottom: '0.75rem',
    },
    fraudTypeGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
      gap: '0.75rem',
    },
    fraudTypeCard: {
      backgroundColor: colors.muted,
      borderRadius: '0.75rem',
      padding: '1rem',
      border: `1px solid ${colors.border}`,
    },
    fraudTypeLabel: {
      fontSize: '0.85rem',
      color: colors.mutedForeground,
      marginBottom: '0.35rem',
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
    },
    fraudTypeCount: {
      fontSize: '1.4rem',
      fontWeight: '700',
      color: colors.foreground,
    },
    fraudTypeMeta: {
      fontSize: '0.8rem',
      color: colors.mutedForeground,
      marginTop: '0.35rem',
    },
    reasonLegend: {
      marginTop: '1.25rem',
      padding: '1rem',
      borderRadius: '0.75rem',
      border: `1px dashed ${colors.border}`,
      backgroundColor: colors.muted
    },
    reasonLegendTitle: {
      fontSize: '0.9rem',
      fontWeight: '600',
      color: colors.mutedForeground,
      marginBottom: '0.5rem',
      textTransform: 'uppercase',
      letterSpacing: '0.05em'
    },
    reasonLegendGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '0.5rem'
    },
    reasonLegendChip: {
      borderRadius: '0.65rem',
      border: `1px solid ${colors.border}`,
      padding: '0.6rem 0.75rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      fontSize: '0.85rem',
      backgroundColor: colors.background,
      transition: 'all 0.2s ease'
    },
    topFraudList: {
      marginTop: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem',
    },
    topFraudItem: {
      backgroundColor: colors.muted,
      borderRadius: '0.75rem',
      padding: '0.9rem 1.1rem',
      border: `1px solid ${colors.border}`,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: '1rem',
    },
    topFraudLabel: {
      fontWeight: '600',
      color: colors.foreground,
      fontSize: '0.95rem',
    },
    topFraudMeta: {
      fontSize: '0.8rem',
      color: colors.mutedForeground,
      marginTop: '0.15rem',
    },
    topFraudAmount: {
      fontWeight: '700',
      color: '#ef4444',
      fontSize: '1rem',
    },
    fraudTransaction: {
      borderLeft: `4px solid #ef4444`,
    },
    legitimateTransaction: {
      borderLeft: `4px solid #10b981`,
    },
    plotsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
      gap: '2rem',
      marginTop: '2rem',
    },
    plotCard: {
      backgroundColor: colors.muted,
      padding: '2rem',
      borderRadius: '1rem',
      border: `1px solid ${colors.border}`,
      position: 'relative',
      overflow: 'hidden',
      boxShadow: '0 18px 35px rgba(5, 7, 15, 0.45)',
      transition: 'transform 0.3s ease, box-shadow 0.3s ease',
      width: '100%',
    },
    plotTitle: {
      fontSize: '1.3rem',
      fontWeight: '600',
      color: colors.foreground,
      marginBottom: '1.5rem',
    },
    plotDescription: {
      fontSize: '0.95rem',
      color: colors.mutedForeground,
      marginTop: '1rem',
    },
    plotCanvas: {
      width: '100%',
      height: '450px',
    },
    plotDetailsRow: {
      marginTop: '1rem',
      display: 'flex',
      flexWrap: 'wrap',
      gap: '0.5rem',
    },
    plotDetailChip: {
      background: 'rgba(15, 23, 42, 0.6)',
      color: '#e2e8f0',
      borderRadius: '9999px',
      padding: '0.35rem 0.85rem',
      fontSize: '0.8rem',
      display: 'inline-flex',
      flexDirection: 'column',
      lineHeight: 1.2,
      border: '1px solid rgba(148, 163, 184, 0.3)',
    },
    heatmapWrapper: {
      width: '100%',
      overflowX: 'auto',
      paddingBottom: '0.5rem'
    },
    heatmapHeaderRow: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(70px, 1fr))',
      gap: '4px',
      fontSize: '0.75rem',
      color: colors.mutedForeground,
      marginBottom: '0.25rem'
    },
    heatmapCorner: {
      width: '70px'
    },
    heatmapHeaderCell: {
      textAlign: 'center',
      fontSize: '0.75rem',
      fontWeight: 600
    },
    heatmapRow: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(70px, 1fr))',
      gap: '4px',
      alignItems: 'center'
    },
    heatmapCell: {
      borderRadius: '6px',
      padding: '0.35rem 0.25rem',
      fontSize: '0.75rem',
      textAlign: 'center'
    },
    geoMap: {
      position: 'relative',
      width: '100%',
      borderRadius: '0.75rem',
      background: `
        radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 80% 50%, rgba(16, 185, 129, 0.1) 0%, transparent 50%),
        linear-gradient(135deg, #1e293b 0%, #0f172a 100%)
      `,
      border: `1px solid ${colors.border}`,
      overflow: 'hidden',
      backgroundImage: `
        linear-gradient(rgba(148, 163, 184, 0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148, 163, 184, 0.1) 1px, transparent 1px)
      `,
      backgroundSize: '50px 50px',
      backgroundPosition: 'center center'
    },
    geoDot: {
      position: 'absolute',
      borderRadius: '50%',
      backgroundColor: '#ef4444',
      border: '2px solid #fca5a5',
      transform: 'translate(-50%, -50%)',
      boxShadow: '0 0 20px rgba(239, 68, 68, 0.9), 0 0 40px rgba(239, 68, 68, 0.5)',
      cursor: 'pointer',
      transition: 'all 0.2s ease'
    },
    missingPlot: {
      width: '100%',
      height: '220px',
      borderRadius: '0.75rem',
      border: `1px dashed ${colors.border}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: colors.mutedForeground,
      fontSize: '0.9rem'
    },
    zoomModalOverlay: {
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(6, 11, 23, 0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 999,
      padding: '2rem',
      backdropFilter: 'blur(6px)',
    },
    zoomModalContent: {
      backgroundColor: '#0f172a',
      borderRadius: '1.5rem',
      padding: '2rem',
      maxWidth: '90vw',
      maxHeight: '90vh',
      overflow: 'auto',
      border: `1px solid ${colors.border}`,
      boxShadow: '0 35px 60px rgba(0,0,0,0.65)',
      width: 'min(1000px, 90vw)',
    },
    zoomModalHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '1.5rem',
      color: '#f8fafc',
    },
    zoomModalImg: {
      width: '100%',
      borderRadius: '1rem',
      display: 'block',
    },
    zoomModalClose: {
      border: 'none',
      background: 'transparent',
      color: '#cbd5f5',
      fontSize: '1.25rem',
      cursor: 'pointer',
    },
    recommendationsList: {
      listStyle: 'none',
      padding: 0,
      margin: '1rem 0',
    },
    recommendationItem: {
      backgroundColor: colors.muted,
      padding: '1rem',
      borderRadius: '0.5rem',
      marginBottom: '0.75rem',
      fontSize: '0.95rem',
      color: colors.foreground,
      borderLeft: `4px solid ${primary}`,
    },
    patternCard: {
      backgroundColor: colors.muted,
      padding: '1rem',
      borderRadius: '0.5rem',
      marginBottom: '0.75rem',
      borderLeft: `4px solid #f59e0b`,
    },
    previewContainer: {
      backgroundColor: colors.card,
      borderRadius: '1rem',
      padding: '2rem',
      marginBottom: '1.5rem',
      border: `1px solid ${colors.border}`,
    },
    statsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
      gap: '1rem',
      marginBottom: '2rem',
    },
    previewStatCard: {
      backgroundColor: colors.background,
      padding: '1rem',
      borderRadius: '0.5rem',
      border: `1px solid ${colors.border}`,
    },
    previewStatLabel: {
      fontSize: '0.75rem',
      color: colors.mutedForeground,
      marginBottom: '0.25rem',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
    },
    previewStatValue: {
      fontSize: '1.5rem',
      fontWeight: '700',
      color: colors.foreground,
    },
    columnInfoSection: {
      marginBottom: '2rem',
    },
    columnInfoTitle: {
      fontSize: '0.9rem',
      fontWeight: '600',
      color: colors.foreground,
      marginBottom: '1rem',
    },
    columnInfoTable: {
      width: '100%',
      backgroundColor: colors.background,
      borderRadius: '0.5rem',
      overflow: 'hidden',
      border: `1px solid ${colors.border}`,
    },
    tableHeader: {
      backgroundColor: colors.muted,
      padding: '0.75rem 1rem',
      fontSize: '0.85rem',
      fontWeight: '600',
      color: colors.mutedForeground,
      borderBottom: `1px solid ${colors.border}`,
      textAlign: 'left',
    },
    tableCell: {
      padding: '0.75rem 1rem',
      fontSize: '0.85rem',
      color: colors.foreground,
      borderBottom: `1px solid ${colors.border}`,
    },
    previewTableSection: {
      marginBottom: '2rem',
    },
    previewTableTitle: {
      fontSize: '0.9rem',
      fontWeight: '600',
      color: colors.foreground,
      marginBottom: '1rem',
    },
    previewTable: {
      width: '100%',
      backgroundColor: colors.background,
      borderRadius: '0.5rem',
      overflow: 'auto',
      maxHeight: '400px',
      border: `1px solid ${colors.border}`,
    },
    tableRow: {
      borderBottom: `1px solid ${colors.border}`,
    },
    actionButtons: {
      display: 'flex',
      gap: '1rem',
      justifyContent: 'flex-start',
    },
    proceedButton: {
      backgroundColor: primary,
      color: colors.primaryForeground,
      padding: '0.875rem 3rem',
      borderRadius: '9999px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '1rem',
      fontWeight: '600',
      transition: 'all 0.3s',
      boxShadow: `0 0 20px ${primary}40`,
    },
    uploadDifferentButton: {
      backgroundColor: 'transparent',
      color: colors.foreground,
      border: `2px solid ${colors.border}`,
      padding: '0.875rem 3rem',
      borderRadius: '9999px',
      cursor: 'pointer',
      fontSize: '1rem',
      fontWeight: '600',
      transition: 'all 0.3s',
    },
  };

  return (
    <div style={styles.container}>
      {/* Back Button */}
      <button
        style={styles.backButton}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = colors.muted;
          e.target.style.borderColor = primary;
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = 'transparent';
          e.target.style.borderColor = colors.border;
        }}
        onClick={() => navigate('/transaction-type')}
      >
        <FaArrowLeft /> Back to Transaction Types
      </button>

      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Real-time Transaction Analysis</h1>
      </div>

      {/* Connect to Banking System Section */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <FaLink style={styles.sectionIcon} />
          <h2 style={styles.sectionTitle}>Connect to your Banking Systems</h2>
        </div>
        <p style={styles.sectionSubtitle}>
          Enter your Banking System URL to fetch transaction data
        </p>

        <form onSubmit={handleUrlSubmit}>
          <div style={styles.formGroup}>
            <label style={styles.label}>Banking System URL</label>
            <input
              type="url"
              value={bankingUrl}
              onChange={(e) => setBankingUrl(e.target.value)}
              placeholder="https://api.example.com/transactions"
              style={styles.input}
              onFocus={(e) => {
                e.target.style.borderColor = primary;
                e.target.style.boxShadow = `0 0 0 3px ${primary}20`;
              }}
              onBlur={(e) => {
                e.target.style.borderColor = colors.border;
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <button
            type="submit"
            style={styles.submitButton}
            disabled={loading || !bankingUrl}
            onMouseEnter={(e) => {
              if (!loading && bankingUrl) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = `0 6px 30px ${primary}60`;
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
          >
            {loading ? '⏳ Connecting...' : 'Connect to Banking System'}
          </button>
        </form>
      </div>

      {/* OR Divider */}
      <div style={styles.orDivider}>
        <span style={styles.orText}>OR</span>
      </div>

      {/* Upload Data File Section */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <FaUpload style={styles.sectionIcon} />
          <h2 style={styles.sectionTitle}>Upload Your Data File</h2>
        </div>
        <p style={styles.sectionSubtitle}>
          Upload a CSV file containing your transaction data
        </p>

        <div
          style={styles.uploadArea}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => document.getElementById('fileInput').click()}
        >
          <div style={styles.uploadIcon}>☁️</div>
          <div style={styles.uploadText}>Drag and drop CSV file here</div>
          <div style={styles.uploadSubtext}>
            Limit 200MB per file • CSV format only
          </div>
          <button
            type="button"
            style={styles.browseButton}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = `${primary}10`;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
            }}
          >
            Browse files
          </button>
          <input
            id="fileInput"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </div>

        {file && (
          <div style={styles.fileName}>
            <span>📄 Selected file: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
            <button
              style={styles.analyzeButton}
              onClick={handleAnalyze}
              disabled={loading}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.target.style.transform = 'scale(1.05)';
                }
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'scale(1)';
              }}
            >
              {loading ? '⏳ Analyzing...' : 'Analyze Transactions'}
            </button>
          </div>
        )}

        {error && <div style={styles.errorBox}>❌ {error}</div>}
      </div>

      {/* CSV Preview Section */}
      {csvPreview && !analysisResult && (
        <div style={styles.previewContainer}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: '700', color: colors.foreground, marginBottom: '1.5rem' }}>
            Data Preview
          </h2>

          {/* Statistics Cards */}
          <div style={styles.statsGrid}>
            <div style={styles.previewStatCard}>
              <div style={styles.previewStatLabel}>Total Rows</div>
              <div style={styles.previewStatValue}>{(csvPreview.totalRows || 0).toLocaleString()}</div>
            </div>
            <div style={styles.previewStatCard}>
              <div style={styles.previewStatLabel}>Total Columns</div>
              <div style={styles.previewStatValue}>{csvPreview.totalColumns || 0}</div>
            </div>
            <div style={styles.previewStatCard}>
              <div style={styles.previewStatLabel}>Fraud Transactions</div>
              <div style={{ ...styles.previewStatValue, color: '#ef4444' }}>{(csvPreview.fraudCount || 0).toLocaleString()}</div>
            </div>
            <div style={styles.previewStatCard}>
              <div style={styles.previewStatLabel}>Date Range</div>
              <div style={{ ...styles.previewStatValue, fontSize: '0.9rem' }}>{csvPreview.dateRange || 'N/A'}</div>
            </div>
          </div>

          {/* Column Information */}
          <div style={styles.columnInfoSection}>
            <div style={styles.columnInfoTitle}>Column Information:</div>
            <div style={{ overflowX: 'auto' }}>
              <table style={styles.columnInfoTable}>
                <thead>
                  <tr>
                    <th style={styles.tableHeader}></th>
                    <th style={styles.tableHeader}>Column Name</th>
                    <th style={styles.tableHeader}>Data Type</th>
                    <th style={styles.tableHeader}>Non-Null Count</th>
                    <th style={styles.tableHeader}>Null Count</th>
                  </tr>
                </thead>
                <tbody>
                  {csvPreview.columnInfo.map((col, idx) => (
                    <tr key={idx} style={styles.tableRow}>
                      <td style={styles.tableCell}>{idx}</td>
                      <td style={styles.tableCell}>{col.name}</td>
                      <td style={styles.tableCell}>{col.dataType}</td>
                      <td style={styles.tableCell}>{col.nonNullCount}</td>
                      <td style={styles.tableCell}>{col.nullCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* First 10 Rows Preview */}
          <div style={styles.previewTableSection}>
            <div style={styles.previewTableTitle}>First {csvPreview.rows.length} Rows:</div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', backgroundColor: colors.background, borderRadius: '0.5rem', border: `1px solid ${colors.border}` }}>
                <thead>
                  <tr style={{ backgroundColor: colors.muted }}>
                    <th style={{ ...styles.tableHeader, position: 'sticky', top: 0, zIndex: 1 }}></th>
                    {csvPreview.headers.map((header, idx) => (
                      <th key={idx} style={{ ...styles.tableHeader, position: 'sticky', top: 0, zIndex: 1, whiteSpace: 'nowrap' }}>
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {csvPreview.rows.map((row, rowIdx) => (
                    <tr key={rowIdx} style={styles.tableRow}>
                      <td style={styles.tableCell}>{rowIdx}</td>
                      {csvPreview.headers.map((header, colIdx) => (
                        <td key={colIdx} style={{ ...styles.tableCell, whiteSpace: 'nowrap' }}>
                          {row[header] || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={styles.actionButtons}>
            <button
              style={styles.proceedButton}
              onClick={handleAnalyze}
              disabled={loading}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = `0 6px 30px ${primary}60`;
                }
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = `0 0 20px ${primary}40`;
              }}
            >
              {loading ? '⏳ Analyzing...' : '▶ Proceed to Insights'}
            </button>
            <button
              style={styles.uploadDifferentButton}
              onClick={handleUploadDifferentFile}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = colors.muted;
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'transparent';
              }}
            >
              ⬆ Upload Different File
            </button>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <FaChartBar style={styles.sectionIcon} />
            <h2 style={styles.sectionTitle}>Analysis Results</h2>
          </div>

          {/* Summary Statistics */}
          <div style={styles.resultSummary}>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Total Transactions</div>
              <div style={styles.statValue}>
                {analysisResult.csv_info.total_count}
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Fraudulent</div>
              <div style={{ ...styles.statValue, ...styles.fraudStat }}>
                {analysisResult.fraud_detection.fraud_count}
              </div>
              <div style={{ fontSize: '0.8rem', color: colors.mutedForeground, marginTop: '0.25rem' }}>
                {analysisResult.fraud_detection.fraud_percentage}%
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Legitimate</div>
              <div style={{ ...styles.statValue, ...styles.legitimateStat }}>
                {analysisResult.fraud_detection.legitimate_count}
              </div>
              <div style={{ fontSize: '0.8rem', color: colors.mutedForeground, marginTop: '0.25rem' }}>
                {analysisResult.fraud_detection.legitimate_percentage}%
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Total Amount</div>
              <div style={{ ...styles.statValue, fontSize: '1.5rem' }}>
                ${(analysisResult.fraud_detection.total_amount || 0).toLocaleString()}
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Fraud Amount</div>
              <div style={{ ...styles.statValue, ...styles.fraudStat, fontSize: '1.5rem' }}>
                ${(analysisResult.fraud_detection.total_fraud_amount || 0).toLocaleString()}
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Top Fraud Pattern</div>
              <div style={{ ...styles.statValue, fontSize: '1.1rem' }}>
                {analysisResult.fraud_detection.dominant_fraud_reason
                  ? formatFraudReason(analysisResult.fraud_detection.dominant_fraud_reason)
                  : analysisResult.fraud_detection.dominant_fraud_type
                  ? formatFraudReason(analysisResult.fraud_detection.dominant_fraud_type)
                  : 'N/A'}
              </div>
            </div>
          </div>

          {fraudReasonBreakdown.length > 0 && (
            <div style={styles.fraudTypeSection}>
              <h3 style={styles.fraudTypeTitle}>Fraud Reason Breakdown</h3>
              <div style={styles.fraudTypeGrid}>
                {fraudReasonBreakdown.slice(0, 4).map((pattern, idx) => (
                  <div key={`${pattern.type || pattern.label}-${idx}`} style={styles.fraudTypeCard}>
                    <div style={styles.fraudTypeLabel}>
                      {formatFraudReason(pattern.label || pattern.type)}
                    </div>
                    <div style={styles.fraudTypeCount}>{pattern.count} cases</div>
                    <div style={styles.fraudTypeMeta}>
                      {pattern.percentage}% of fraud • $
                      {(pattern.total_amount || 0).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={styles.reasonLegend}>
            <div style={styles.reasonLegendTitle}>Standard Fraud Patterns</div>
              <div style={styles.reasonLegendGrid}>
                {fraudReasonChips.map((reason) => {
                const count = reasonCountMap[reason] || 0;
                const isActive = count > 0;
                return (
                  <div
                    key={reason}
                    style={{
                      ...styles.reasonLegendChip,
                      opacity: isActive ? 1 : 0.45,
                      borderColor: isActive ? primary : colors.border,
                      color: colors.foreground
                    }}
                  >
                    <span>{reason}</span>
                    <span style={{ fontWeight: 600 }}>
                      {isActive ? `${count} case${count === 1 ? '' : 's'}` : '—'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {topFraudCases.length > 0 && (
            <div style={styles.topFraudList}>
              <h3 style={styles.fraudTypeTitle}>Top ML-Flagged Transactions</h3>
              {topFraudCases.map((txn, idx) => {
                const txnAmount = typeof txn.amount === 'number' ? txn.amount : parseFloat(txn.amount || 0);
                return (
                  <div key={txn.transaction_id || `${txn.merchant}-${idx}`} style={styles.topFraudItem}>
                    <div>
                      <div style={styles.topFraudLabel}>{txn.merchant || txn.category || 'Unknown Merchant'}</div>
                      <div style={styles.topFraudMeta}>
                        {formatFraudReason(txn.fraud_reason)} • {((txn.fraud_probability || 0) * 100).toFixed(0)}% risk
                      </div>
                      {txn.fraud_reason_detail && (
                        <div style={{ fontSize: '0.75rem', color: colors.mutedForeground, marginTop: '0.25rem' }}>
                          {txn.fraud_reason_detail}
                        </div>
                      )}
                    </div>
                    <div style={styles.topFraudAmount}>
                      ${txnAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Action Buttons */}
          <div style={styles.buttonGroup}>
            <button
              style={{
                ...styles.downloadButton,
                opacity: analysisResult?.transactions?.length ? 1 : 0.5,
                cursor: analysisResult?.transactions?.length ? 'pointer' : 'not-allowed',
              }}
              onClick={handleDownloadCSV}
              disabled={!analysisResult?.transactions?.length}
            >
              Download CSV
            </button>
            <button
              style={styles.insightsButton}
              onClick={() => setShowInsights(!showInsights)}
            >
              <FaChartBar />
              {showInsights ? 'Hide Insights' : 'Show Insights & Plots'}
            </button>
          </div>

          {/* Database Storage Notification */}
          {analysisResult?.database_status === 'saved' && (
            <div style={{
              marginTop: '1rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#d1fae5',
              border: '1px solid #6ee7b7',
              borderRadius: '50px',
              color: '#065f46',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}>
              <span style={{ fontSize: '1rem' }}>✓</span>
              <span>Saved to analyzed_real_time_trn</span>
            </div>
          )}

        </div>
      )}

      {/* Insights Section */}
      {showInsights && analysisResult?.insights && (
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <FaChartBar style={styles.sectionIcon} />
            <h2 style={styles.sectionTitle}>Detailed Insights</h2>
          </div>

          {/* AI Analysis - Minimal Version */}
          {analysisResult.agent_analysis && (
            <div style={{ marginBottom: '2rem' }}>
              <h3 style={{ color: colors.foreground, fontSize: '1.2rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FaRobot style={{ color: primary }} />
                AI Analysis
              </h3>

              {/* Top Suspicious Transactions - Condensed */}
              {analysisResult.agent_analysis.top_transactions?.transactions?.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: colors.foreground, fontSize: '0.95rem', marginBottom: '0.75rem', fontWeight: '600' }}>
                    Top Suspicious Transactions
                  </h4>
                  {analysisResult.agent_analysis.top_transactions.transactions.slice(0, 3).map((txn, idx) => (
                    <div key={idx} style={{
                      backgroundColor: colors.muted,
                      padding: '0.75rem',
                      borderRadius: '0.5rem',
                      border: `1px solid ${colors.border}`,
                      borderLeft: `3px solid #ef4444`,
                      marginBottom: '0.5rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: '600', color: colors.foreground, fontSize: '0.9rem' }}>
                          {txn.merchant || 'Unknown'}
                        </span>
                        <span style={{ fontWeight: '700', color: '#ef4444', fontSize: '0.95rem' }}>
                          ${txn.amount.toFixed(2)}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: colors.mutedForeground, marginTop: '0.25rem' }}>
                        {txn.category || 'N/A'} • {(txn.fraud_probability * 100).toFixed(0)}% probability
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Key Insights - Condensed */}
              {agentInsights && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: colors.foreground, fontSize: '0.95rem', marginBottom: '0.75rem', fontWeight: '600' }}>
                    Key Insights
                  </h4>
                  <div style={{
                    backgroundColor: colors.muted,
                    padding: '1rem',
                    borderRadius: '0.5rem',
                    border: `1px solid ${colors.border}`,
                    fontSize: '0.9rem',
                    color: colors.foreground,
                    lineHeight: '1.6',
                    maxHeight: '400px',
                    overflowY: 'auto'
                  }}>
                    {renderMarkdownText(agentInsights)}
                  </div>
                </div>
              )}

              {/* Fraud-Specific Prevention Recommendations */}
              {analysisResult.agent_analysis.pattern_recommendations?.length > 0 && (
                <div>
                  <h4 style={{ color: colors.foreground, fontSize: '1rem', marginBottom: '1rem', fontWeight: '600' }}>
                    Fraud Prevention Recommendations
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {analysisResult.agent_analysis.pattern_recommendations.slice(0, 3).map((rec, idx) => {
                      const severityColors = {
                        'CRITICAL': { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', text: '#fee2e2' },
                        'HIGH': { bg: 'rgba(251, 146, 60, 0.15)', border: '#fb923c', text: '#fed7aa' },
                        'MEDIUM': { bg: 'rgba(234, 179, 8, 0.15)', border: '#eab308', text: '#fef08a' },
                        'LOW': { bg: 'rgba(34, 197, 94, 0.15)', border: '#22c55e', text: '#dcfce7' },
                        'INFO': { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6', text: '#dbeafe' }
                      };
                      const severity = rec.severity || 'MEDIUM';
                      const color = severityColors[severity] || severityColors['MEDIUM'];

                      return (
                        <div key={idx} style={{
                          backgroundColor: color.bg,
                          padding: '1.25rem',
                          borderRadius: '0.75rem',
                          border: `2px solid ${color.border}`,
                          boxShadow: `0 2px 8px ${color.border}30`
                        }}>
                          {/* Header */}
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                            <div>
                              <div style={{
                                fontSize: '1.05rem',
                                fontWeight: '700',
                                color: colors.foreground,
                                marginBottom: '0.25rem'
                              }}>
                                {rec.title || rec.pattern_type}
                              </div>
                              <div style={{ fontSize: '0.85rem', color: colors.mutedForeground }}>
                                {rec.description}
                              </div>
                            </div>
                            <div style={{
                              backgroundColor: color.border,
                              color: '#0f172a',
                              padding: '0.375rem 0.75rem',
                              borderRadius: '0.5rem',
                              fontSize: '0.75rem',
                              fontWeight: '700',
                              whiteSpace: 'nowrap'
                            }}>
                              {severity}
                            </div>
                          </div>

                          {/* Stats (if available) */}
                          {(rec.count || rec.fraud_count || rec.fraud_percentage) && (
                            <div style={{
                              display: 'flex',
                              gap: '1rem',
                              marginBottom: '1rem',
                              paddingBottom: '0.75rem',
                              borderBottom: `1px solid ${color.border}40`
                            }}>
                              {rec.count && (
                                <div style={{ fontSize: '0.8rem', color: colors.foreground }}>
                                  <span style={{ fontWeight: '600' }}>{rec.count}</span> cases
                                </div>
                              )}
                              {rec.percentage && (
                                <div style={{ fontSize: '0.8rem', color: colors.foreground }}>
                                  <span style={{ fontWeight: '600' }}>{rec.percentage.toFixed(1)}%</span> of fraud
                                </div>
                              )}
                              {rec.total_amount && (
                                <div style={{ fontSize: '0.8rem', color: colors.foreground }}>
                                  <span style={{ fontWeight: '600' }}>${rec.total_amount.toLocaleString()}</span> total
                                </div>
                              )}
                            </div>
                          )}

                          {/* Immediate Actions */}
                          {rec.immediate_actions?.length > 0 && (
                            <div style={{ marginBottom: '1rem' }}>
                              <div style={{
                                fontSize: '0.85rem',
                                fontWeight: '600',
                                color: colors.foreground,
                                marginBottom: '0.5rem'
                              }}>
                                Immediate Actions
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                {rec.immediate_actions.slice(0, 4).map((action, aIdx) => (
                                  <div key={aIdx} style={{
                                    fontSize: '0.8rem',
                                    color: colors.foreground,
                                    paddingLeft: '1rem',
                                    position: 'relative',
                                    lineHeight: '1.4'
                                  }}>
                                    <span style={{ position: 'absolute', left: 0 }}>•</span>
                                    {action}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Prevention Steps */}
                          {rec.prevention_steps?.length > 0 && (
                            <div style={{ marginBottom: '0.75rem' }}>
                              <div style={{
                                fontSize: '0.85rem',
                                fontWeight: '600',
                                color: colors.foreground,
                                marginBottom: '0.5rem'
                              }}>
                                Prevention Steps
                              </div>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                {rec.prevention_steps.slice(0, 5).map((step, sIdx) => (
                                  <div key={sIdx} style={{
                                    fontSize: '0.8rem',
                                    color: colors.foreground,
                                    paddingLeft: '1rem',
                                    position: 'relative',
                                    lineHeight: '1.4'
                                  }}>
                                    <span style={{ position: 'absolute', left: 0 }}>•</span>
                                    {step}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Monitoring */}
                          {rec.monitoring && (
                            <div style={{
                              marginTop: '0.75rem',
                              paddingTop: '0.75rem',
                              borderTop: `1px solid ${color.border}40`
                            }}>
                              <div style={{
                                fontSize: '0.85rem',
                                fontWeight: '600',
                                color: colors.foreground,
                                marginBottom: '0.25rem'
                              }}>
                                Monitor
                              </div>
                              <div style={{ fontSize: '0.8rem', color: colors.mutedForeground, lineHeight: '1.4' }}>
                                {rec.monitoring}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Plots */}
          {(() => {
            const plotsToDisplay = filteredPlots || analysisResult.insights.plots;
            console.log('Plots to display:', plotsToDisplay);
            return plotsToDisplay?.length > 0;
          })() && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ color: colors.foreground, fontSize: '1.1rem', margin: 0 }}>
                  Visual Analytics
                  {filteredPlots && (
                    <span style={{ 
                      fontSize: '0.85rem', 
                      color: primary,
                      marginLeft: '0.5rem',
                      fontWeight: '600',
                      backgroundColor: `${primary}20`,
                      padding: '0.25rem 0.75rem',
                      borderRadius: '0.5rem'
                    }}>
                      🔍 Filtered ({filteredPlots.length} plots)
                    </span>
                  )}
                  {!filteredPlots && (
                    <span style={{ fontSize: '0.85rem', color: colors.mutedForeground, marginLeft: '0.5rem' }}>
                      (All Data)
                    </span>
                  )}
                </h3>
                {filteredPlots && (
                  <button
                    onClick={() => setFilteredPlots(null)}
                    style={{
                      backgroundColor: 'transparent',
                      color: colors.foreground,
                      border: `1px solid ${colors.border}`,
                      padding: '0.5rem 1rem',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      fontWeight: '600'
                    }}
                  >
                    Show All Plots
                  </button>
                )}
              </div>
              
              {/* Filter Panel - Styled like Insights Page */}
              {analysisResult && (
                <div style={{
                  display: 'flex',
                  gap: '10px',
                  marginBottom: '20px',
                  alignItems: 'center',
                  flexWrap: 'wrap'
                }}>
                  <select
                    value={filters.amountRange}
                    onChange={(e) => handleFilterChange('amountRange', e.target.value)}
                    disabled={!filterOptions}
                    style={{
                      padding: '8px 12px',
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: colors.card,
                      color: colors.foreground,
                      cursor: filterOptions ? 'pointer' : 'not-allowed',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">All Amounts</option>
                    {filterOptions?.amount_ranges?.map((range, idx) => (
                      <option key={idx} value={JSON.stringify({min: range.min, max: range.max})}>
                        {range.label}
                      </option>
                    ))}
                  </select>

                  <select
                    value={filters.fraudProbabilityRange}
                    onChange={(e) => handleFilterChange('fraudProbabilityRange', e.target.value)}
                    disabled={!filterOptions}
                    style={{
                      padding: '8px 12px',
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: colors.card,
                      color: colors.foreground,
                      cursor: filterOptions ? 'pointer' : 'not-allowed',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">All Probabilities</option>
                    {filterOptions?.fraud_probability_ranges?.map((range, idx) => (
                      <option key={idx} value={JSON.stringify({min: range.min, max: range.max})}>
                        {range.label}
                      </option>
                    ))}
                  </select>

                  <select
                    value={filters.category}
                    onChange={(e) => handleFilterChange('category', e.target.value)}
                    disabled={!filterOptions}
                    style={{
                      padding: '8px 12px',
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: colors.card,
                      color: colors.foreground,
                      cursor: filterOptions ? 'pointer' : 'not-allowed',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">All Categories</option>
                    {filterOptions?.categories?.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>

                  <select
                    value={filters.merchant}
                    onChange={(e) => handleFilterChange('merchant', e.target.value)}
                    disabled={!filterOptions}
                    style={{
                      padding: '8px 12px',
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: colors.card,
                      color: colors.foreground,
                      cursor: filterOptions ? 'pointer' : 'not-allowed',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">All Merchants</option>
                    {filterOptions?.merchants?.map((merchant) => (
                      <option key={merchant} value={merchant}>
                        {merchant}
                      </option>
                    ))}
                  </select>

                  <select
                    value={filters.city}
                    onChange={(e) => handleFilterChange('city', e.target.value)}
                    disabled={!filterOptions}
                    style={{
                      padding: '8px 12px',
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: colors.card,
                      color: colors.foreground,
                      cursor: filterOptions ? 'pointer' : 'not-allowed',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">All Cities</option>
                    {filterOptions?.cities?.map((city) => (
                      <option key={city} value={city}>
                        {city}
                      </option>
                    ))}
                  </select>

                  <select
                    value={filters.country}
                    onChange={(e) => handleFilterChange('country', e.target.value)}
                    disabled={!filterOptions}
                    style={{
                      padding: '8px 12px',
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: colors.card,
                      color: colors.foreground,
                      cursor: filterOptions ? 'pointer' : 'not-allowed',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">All Countries</option>
                    {filterOptions?.countries?.map((country) => (
                      <option key={country} value={country}>
                        {country}
                      </option>
                    ))}
                  </select>

                  <select
                    value={filters.fraudReason}
                    onChange={(e) => handleFilterChange('fraudReason', e.target.value)}
                    disabled={!filterOptions}
                    style={{
                      padding: '8px 12px',
                      border: `1px solid ${colors.border}`,
                      borderRadius: '4px',
                      fontSize: '14px',
                      backgroundColor: colors.card,
                      color: colors.foreground,
                      cursor: filterOptions ? 'pointer' : 'not-allowed',
                      minWidth: '150px'
                    }}
                  >
                    <option value="">All Fraud Reasons</option>
                    {filterOptions?.fraud_reasons?.map((reason) => (
                      <option key={reason} value={reason}>
                        {reason}
                      </option>
                    ))}
                  </select>

                  <button
                    onClick={handleRegeneratePlots}
                    disabled={regeneratingPlots || !filterOptions}
                    style={{
                      backgroundColor: primary,
                      color: 'white',
                      padding: '8px 16px',
                      borderRadius: '4px',
                      border: 'none',
                      cursor: regeneratingPlots || !filterOptions ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: '600',
                      opacity: regeneratingPlots || !filterOptions ? 0.6 : 1,
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {regeneratingPlots ? '⏳ Regenerating...' : '🔄 Apply Filters'}
                  </button>

                  {activeFilterCount > 0 && (
                    <button
                      onClick={() => {
                        resetFilters();
                        setFilteredPlots(null);
                      }}
                      style={{
                        backgroundColor: 'transparent',
                        color: colors.foreground,
                        border: `1px solid ${colors.border}`,
                        padding: '8px 16px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '600',
                        whiteSpace: 'nowrap'
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.backgroundColor = colors.muted;
                        e.target.style.borderColor = primary;
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.backgroundColor = 'transparent';
                        e.target.style.borderColor = colors.border;
                      }}
                    >
                      Reset ({activeFilterCount})
                    </button>
                  )}
                </div>
              )}
              
              <div style={styles.plotsGrid}>
                {(filteredPlots || analysisResult.insights.plots).map((plot, idx) => {
                  const isHovered = hoveredPlotIndex === idx;
                  return (
                    <div
                      key={idx}
                      style={{
                        ...styles.plotCard,
                        transform: isHovered ? 'translateY(-8px)' : 'translateY(0)',
                        boxShadow: isHovered
                          ? '0 30px 55px rgba(5, 7, 15, 0.6)'
                          : styles.plotCard.boxShadow,
                        cursor: 'zoom-in',
                      }}
                      onMouseEnter={() => setHoveredPlotIndex(idx)}
                      onMouseLeave={() => setHoveredPlotIndex(null)}
                      onClick={() => setZoomedPlot(plot)}
                    >
                      <div style={styles.plotTitle}>{plot.title}</div>
                      <div style={styles.plotCanvas}>
                        {renderPlotVisualization(plot)}
                      </div>
                      {plot.description && (
                        <div style={styles.plotDescription}>{plot.description}</div>
                      )}
                      {plot.details?.length > 0 && (
                        <div style={styles.plotDetailsRow}>
                          {plot.details.slice(0, 3).map((detail, detailIdx) => (
                            <div key={detailIdx} style={styles.plotDetailChip}>
                              <span style={{ opacity: 0.65 }}>{detail.label}</span>
                              <span style={{ fontWeight: 600 }}>{detail.value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {zoomedPlot && (
        <div style={styles.zoomModalOverlay} onClick={() => setZoomedPlot(null)}>
          <div style={styles.zoomModalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.zoomModalHeader}>
              <h3 style={{ margin: 0 }}>{zoomedPlot.title}</h3>
              <button style={styles.zoomModalClose} onClick={() => setZoomedPlot(null)}>
                &times;
              </button>
            </div>
            <div style={{ width: '100%', height: '600px' }}>
              {renderPlotVisualization(zoomedPlot, { height: 600 })}
            </div>
            {zoomedPlot.description && (
              <p style={{ color: '#cbd5f5', marginTop: '1rem' }}>{zoomedPlot.description}</p>
            )}
            {zoomedPlot.details?.length > 0 && (
              <div style={{ marginTop: '1.25rem', display: 'grid', gap: '0.75rem' }}>
                {zoomedPlot.details.map((detail, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '0.75rem 1rem',
                      backgroundColor: 'rgba(15, 23, 42, 0.85)',
                      borderRadius: '0.75rem',
                      border: '1px solid rgba(148, 163, 184, 0.25)',
                      color: '#e2e8f0',
                    }}
                  >
                    <span style={{ opacity: 0.75 }}>{detail.label}</span>
                    <strong>{detail.value}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeAnalysis;