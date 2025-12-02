import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import EChartsDonut from '../components/EChartsDonut';
import EChartsLine from '../components/EChartsLine';
import EChartsBar from '../components/EChartsBar';
import EChartsSankey from '../components/EChartsSankey';
import EChartsGeo from '../components/EChartsGeo';
import EChartsHeatmap from '../components/EChartsHeatmap';
import {
  FaLink,
  FaUpload,
  FaArrowLeft,
  FaChartBar,
  FaRobot,
  FaFilter,
  FaTimes
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
import { analyzeRealTimeTransactions, regeneratePlotsWithFilters } from '../services/api';

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
    amountMin: '',
    amountMax: '',
    fraudProbabilityMin: '',
    fraudProbabilityMax: '',
    category: '',
    hourOfDayStart: '',
    hourOfDayEnd: '',
    fraudOnly: false,
    legitimateOnly: false,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [filteredPlots, setFilteredPlots] = useState(null);
  const [regeneratingPlots, setRegeneratingPlots] = useState(false);

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

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
      const key = pattern.label || pattern.type;
      if (!key) return;
      map[key] = pattern.count;
    });
    return map;
  }, [fraudReasonBreakdown]);

  const renderPlotVisualization = (plot, options = {}) => {
    const height = options.height || 220;

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
        const data = plot.data || [];
        // Use ECharts for better visuals and performance
        return <EChartsDonut data={data} title={plot.title} height={height} />;
      }
      case 'line_trend': {
        const data = plot.data || [];
        return <EChartsLine data={data} title={plot.title} height={height} />;
      }
      case 'heatmap': {
        const xLabels = plot.xLabels || [];
        const yLabels = plot.yLabels || [];
        const dataPoints = plot.data || [];

        // Convert to matrix format for ECharts
        const matrix = yLabels.map(yLabel =>
          xLabels.map(xLabel => {
            const cell = dataPoints.find(item => item.x === xLabel && item.y === yLabel);
            return cell ? cell.value : 0;
          })
        );

        return <EChartsHeatmap data={{ matrix, labels: xLabels }} title={plot.title} height={height} />;
      }
      case 'geo_scatter': {
        const data = plot.data || [];
        return <EChartsGeo data={data} title={plot.title} height={height} />;
      }
      case 'bar_reasons': {
        const data = plot.data || [];
        return <EChartsBar data={data} title={plot.title} height={height} />;
      }
      case 'sankey': {
        return <EChartsSankey data={plot.data} title={plot.title} height={height} />;
      }
      default:
        return (
          <div style={styles.missingPlot}>
            No visualization available for plot type: {plot.type || 'unknown'}
            {plot.image && <div style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: colors.mutedForeground }}>
              (Legacy static plot detected but not supported in this view)
            </div>}
          </div>
        );
    }
  };

  const handleDownloadCSV = () => {
    if (!analysisResult?.transactions?.length) return;

    const rows = analysisResult.transactions;
    const headers = Object.keys(rows[0] || {});

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
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `real_time_transactions_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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
    
    // Validate hour fields (must be between 0 and 23)
    if (filterName === 'hourOfDayStart' || filterName === 'hourOfDayEnd') {
      const numValue = parseInt(value);
      if (!isNaN(numValue)) {
        // Clamp between 0 and 23
        processedValue = Math.max(0, Math.min(23, numValue)).toString();
      } else if (value === '') {
        processedValue = value; // Allow empty
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
      amountMin: '',
      amountMax: '',
      fraudProbabilityMin: '',
      fraudProbabilityMax: '',
      category: '',
      hourOfDayStart: '',
      hourOfDayEnd: '',
      fraudOnly: false,
      legitimateOnly: false,
    });
  };

  const getFilteredTransactions = () => {
    if (!analysisResult?.transactions) return [];

    let filtered = [...analysisResult.transactions];

    // Amount filters
    if (filters.amountMin !== '') {
      filtered = filtered.filter(t => t.amount >= parseFloat(filters.amountMin));
    }
    if (filters.amountMax !== '') {
      filtered = filtered.filter(t => t.amount <= parseFloat(filters.amountMax));
    }

    // Fraud probability filters
    if (filters.fraudProbabilityMin !== '') {
      filtered = filtered.filter(t => t.fraud_probability >= parseFloat(filters.fraudProbabilityMin));
    }
    if (filters.fraudProbabilityMax !== '') {
      filtered = filtered.filter(t => t.fraud_probability <= parseFloat(filters.fraudProbabilityMax));
    }

    // Category filter
    if (filters.category !== '') {
      filtered = filtered.filter(t =>
        t.category?.toLowerCase().includes(filters.category.toLowerCase())
      );
    }

    // Hour of day filter
    if (filters.hourOfDayStart !== '' || filters.hourOfDayEnd !== '') {
      filtered = filtered.filter(t => {
        if (!t.timestamp) return true;
        const date = new Date(t.timestamp);
        const hour = date.getHours();
        const start = filters.hourOfDayStart !== '' ? parseInt(filters.hourOfDayStart) : 0;
        const end = filters.hourOfDayEnd !== '' ? parseInt(filters.hourOfDayEnd) : 23;
        return hour >= start && hour <= end;
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
        amount_min: filters.amountMin ? parseFloat(filters.amountMin) : null,
        amount_max: filters.amountMax ? parseFloat(filters.amountMax) : null,
        fraud_probability_min: filters.fraudProbabilityMin ? parseFloat(filters.fraudProbabilityMin) : null,
        fraud_probability_max: filters.fraudProbabilityMax ? parseFloat(filters.fraudProbabilityMax) : null,
        category: filters.category || null,
        hour_of_day_start: filters.hourOfDayStart ? parseInt(filters.hourOfDayStart) : null,
        hour_of_day_end: filters.hourOfDayEnd ? parseInt(filters.hourOfDayEnd) : null,
        fraud_only: filters.fraudOnly || false,
        legitimate_only: filters.legitimateOnly || false,
      };
      
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
      gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
      gap: '2rem',
      marginTop: '2rem',
    },
    plotCard: {
      backgroundColor: colors.muted,
      padding: '1.5rem',
      borderRadius: '1rem',
      border: `1px solid ${colors.border}`,
      position: 'relative',
      overflow: 'hidden',
      boxShadow: '0 18px 35px rgba(5, 7, 15, 0.45)',
      transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    },
    plotTitle: {
      fontSize: '1.1rem',
      fontWeight: '600',
      color: colors.foreground,
      marginBottom: '1rem',
    },
    plotDescription: {
      fontSize: '0.9rem',
      color: colors.mutedForeground,
      marginTop: '0.75rem',
    },
    plotCanvas: {
      width: '100%',
      height: '230px',
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
              <div style={styles.previewStatValue}>{csvPreview.totalRows.toLocaleString()}</div>
            </div>
            <div style={styles.previewStatCard}>
              <div style={styles.previewStatLabel}>Total Columns</div>
              <div style={styles.previewStatValue}>{csvPreview.totalColumns}</div>
            </div>
            <div style={styles.previewStatCard}>
              <div style={styles.previewStatLabel}>Fraud Transactions</div>
              <div style={{ ...styles.previewStatValue, color: '#ef4444' }}>{csvPreview.fraudCount.toLocaleString()}</div>
            </div>
            <div style={styles.previewStatCard}>
              <div style={styles.previewStatLabel}>Date Range</div>
              <div style={{ ...styles.previewStatValue, fontSize: '0.9rem' }}>{csvPreview.dateRange}</div>
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
              <div style={styles.statValue}>
                ${analysisResult.fraud_detection.total_amount.toLocaleString()}
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Fraud Amount</div>
              <div style={{ ...styles.statValue, ...styles.fraudStat, fontSize: '1.5rem' }}>
                ${analysisResult.fraud_detection.total_fraud_amount.toLocaleString()}
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Model Type</div>
              <div style={{ ...styles.statValue, fontSize: '1.2rem' }}>
                {analysisResult.fraud_detection.model_type}
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
              {STANDARD_FRAUD_REASONS.map((reason) => {
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
                  {insightPoints.length > 0 ? (
                    <ul style={{
                      backgroundColor: colors.muted,
                      padding: '1rem 1.25rem',
                      borderRadius: '0.5rem',
                      border: `1px solid ${colors.border}`,
                      fontSize: '0.9rem',
                      color: colors.foreground,
                      lineHeight: '1.6',
                      maxHeight: '220px',
                      overflowY: 'auto',
                      margin: 0,
                      listStyle: 'disc',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem'
                    }}>
                      {insightPoints.map((point, idx) => (
                        <li key={idx} style={{ marginLeft: '1rem' }}>
                          {point}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div style={{
                      backgroundColor: colors.muted,
                      padding: '1rem',
                      borderRadius: '0.5rem',
                      border: `1px solid ${colors.border}`,
                      fontSize: '0.9rem',
                      color: colors.foreground,
                      lineHeight: '1.6',
                      maxHeight: '200px',
                      overflowY: 'auto',
                      whiteSpace: 'pre-line'
                    }}>
                      {agentInsights}
                    </div>
                  )}
                </div>
              )}

              {/* Recommendations - Condensed */}
              {analysisResult.agent_analysis.recommendations?.length > 0 && (
                <div>
                  <h4 style={{ color: colors.foreground, fontSize: '0.95rem', marginBottom: '0.75rem', fontWeight: '600' }}>
                    Recommendations
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {analysisResult.agent_analysis.recommendations.slice(0, 5).map((rec, idx) => (
                      <div key={idx} style={{
                        backgroundColor: colors.muted,
                        padding: '0.75rem',
                        borderRadius: '0.5rem',
                        border: `1px solid ${colors.border}`,
                        borderLeft: `3px solid ${primary}`,
                        fontSize: '0.85rem',
                        color: colors.foreground
                      }}>
                        {rec}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Filter Panel */}
          <div style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ color: colors.foreground, fontSize: '1.1rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FaFilter style={{ color: primary }} />
                Plot Filters
                {activeFilterCount > 0 && (
                  <span style={{
                    backgroundColor: primary,
                    color: 'white',
                    borderRadius: '9999px',
                    padding: '0.25rem 0.75rem',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    marginLeft: '0.5rem'
                  }}>
                    {activeFilterCount} active
                  </span>
                )}
              </h3>
              <button
                onClick={() => setShowFilters(!showFilters)}
                style={{
                  backgroundColor: 'transparent',
                  color: colors.foreground,
                  border: `2px solid ${colors.border}`,
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {showFilters ? <FaTimes /> : <FaFilter />}
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </button>
            </div>
            
            {showFilters && (
              <div style={{
                backgroundColor: colors.muted,
                padding: '1.5rem',
                borderRadius: '0.75rem',
                border: `1px solid ${colors.border}`,
                marginBottom: '1rem'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                  <div>
                    <label style={styles.label}>Min Amount ($)</label>
                    <input
                      type="number"
                      value={filters.amountMin}
                      onChange={(e) => handleFilterChange('amountMin', e.target.value)}
                      placeholder="0"
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>Max Amount ($)</label>
                    <input
                      type="number"
                      value={filters.amountMax}
                      onChange={(e) => handleFilterChange('amountMax', e.target.value)}
                      placeholder="∞"
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>
                      Min Fraud Probability
                      <span style={{ fontSize: '0.75rem', color: colors.mutedForeground, marginLeft: '0.5rem' }}>
                        (0.00 = 0%, 1.00 = 100%)
                      </span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={filters.fraudProbabilityMin}
                      onChange={(e) => handleFilterChange('fraudProbabilityMin', e.target.value)}
                      onBlur={(e) => {
                        const val = parseFloat(e.target.value);
                        if (!isNaN(val)) {
                          const clamped = Math.max(0, Math.min(1, val));
                          if (clamped !== val) {
                            handleFilterChange('fraudProbabilityMin', clamped.toString());
                          }
                        }
                      }}
                      placeholder="0.00"
                      style={{
                        ...styles.input,
                        borderColor: filters.fraudProbabilityMin && (parseFloat(filters.fraudProbabilityMin) < 0 || parseFloat(filters.fraudProbabilityMin) > 1) 
                          ? '#ef4444' 
                          : styles.input.borderColor
                      }}
                    />
                    {filters.fraudProbabilityMin && (parseFloat(filters.fraudProbabilityMin) < 0 || parseFloat(filters.fraudProbabilityMin) > 1) && (
                      <div style={{ fontSize: '0.75rem', color: '#ef4444', marginTop: '0.25rem' }}>
                        Must be between 0.00 and 1.00
                      </div>
                    )}
                  </div>
                  <div>
                    <label style={styles.label}>
                      Max Fraud Probability
                      <span style={{ fontSize: '0.75rem', color: colors.mutedForeground, marginLeft: '0.5rem' }}>
                        (0.00 = 0%, 1.00 = 100%)
                      </span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={filters.fraudProbabilityMax}
                      onChange={(e) => handleFilterChange('fraudProbabilityMax', e.target.value)}
                      onBlur={(e) => {
                        const val = parseFloat(e.target.value);
                        if (!isNaN(val)) {
                          const clamped = Math.max(0, Math.min(1, val));
                          if (clamped !== val) {
                            handleFilterChange('fraudProbabilityMax', clamped.toString());
                          }
                        }
                      }}
                      placeholder="1.00"
                      style={{
                        ...styles.input,
                        borderColor: filters.fraudProbabilityMax && (parseFloat(filters.fraudProbabilityMax) < 0 || parseFloat(filters.fraudProbabilityMax) > 1) 
                          ? '#ef4444' 
                          : styles.input.borderColor
                      }}
                    />
                    {filters.fraudProbabilityMax && (parseFloat(filters.fraudProbabilityMax) < 0 || parseFloat(filters.fraudProbabilityMax) > 1) && (
                      <div style={{ fontSize: '0.75rem', color: '#ef4444', marginTop: '0.25rem' }}>
                        Must be between 0.00 and 1.00
                      </div>
                    )}
                  </div>
                  <div>
                    <label style={styles.label}>Category</label>
                    <input
                      type="text"
                      value={filters.category}
                      onChange={(e) => handleFilterChange('category', e.target.value)}
                      placeholder="Filter by category"
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>
                      Start Hour (0-23)
                      <span style={{ fontSize: '0.75rem', color: colors.mutedForeground, marginLeft: '0.5rem' }}>
                        (supports midnight wrap, e.g., 22 to 06)
                      </span>
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="23"
                      value={filters.hourOfDayStart}
                      onChange={(e) => handleFilterChange('hourOfDayStart', e.target.value)}
                      placeholder="0"
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>
                      End Hour (0-23)
                      <span style={{ fontSize: '0.75rem', color: colors.mutedForeground, marginLeft: '0.5rem' }}>
                        (supports midnight wrap, e.g., 22 to 06)
                      </span>
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="23"
                      value={filters.hourOfDayEnd}
                      onChange={(e) => handleFilterChange('hourOfDayEnd', e.target.value)}
                      placeholder="23"
                      style={styles.input}
                    />
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: colors.foreground, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={filters.fraudOnly}
                      onChange={(e) => {
                        handleFilterChange('fraudOnly', e.target.checked);
                        if (e.target.checked) handleFilterChange('legitimateOnly', false);
                      }}
                      style={{ cursor: 'pointer' }}
                    />
                    Fraud Only
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: colors.foreground, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={filters.legitimateOnly}
                      onChange={(e) => {
                        handleFilterChange('legitimateOnly', e.target.checked);
                        if (e.target.checked) handleFilterChange('fraudOnly', false);
                      }}
                      style={{ cursor: 'pointer' }}
                    />
                    Legitimate Only
                  </label>
                </div>
                
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <button
                    onClick={handleRegeneratePlots}
                    disabled={regeneratingPlots}
                    style={{
                      backgroundColor: primary,
                      color: 'white',
                      padding: '0.75rem 2rem',
                      borderRadius: '0.5rem',
                      border: 'none',
                      cursor: regeneratingPlots ? 'not-allowed' : 'pointer',
                      fontSize: '0.95rem',
                      fontWeight: '600',
                      opacity: regeneratingPlots ? 0.6 : 1
                    }}
                  >
                    {regeneratingPlots ? '⏳ Regenerating...' : '🔄 Apply Filters to Plots'}
                  </button>
                  <button
                    onClick={() => {
                      resetFilters();
                      setFilteredPlots(null);
                    }}
                    style={{
                      backgroundColor: 'transparent',
                      color: colors.foreground,
                      border: `2px solid ${colors.border}`,
                      padding: '0.75rem 2rem',
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      fontSize: '0.95rem',
                      fontWeight: '600',
                      transition: 'all 0.3s'
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
                    Reset Filters
                  </button>
                </div>
              </div>
            )}
          </div>

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
            <div style={styles.plotCanvas}>
              {renderPlotVisualization(zoomedPlot, { height: 320 })}
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
