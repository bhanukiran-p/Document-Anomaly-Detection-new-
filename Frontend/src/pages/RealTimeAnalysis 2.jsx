import { useMemo, useState, useEffect, useRef } from 'react';
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

const PATTERN_VARIATIONS = {
  // Card-not-present variations
  'card-not-present risk': ['card not present', 'cnp', 'cardnotpresent', 'card not present risk', 'card not present fraud'],
  // Velocity abuse variations
  'velocity abuse': ['velocity', 'rapid transactions', 'transaction velocity', 'rapid succession', 'velocity spike'],
  // Transaction burst variations
  'transaction burst': ['burst', 'rapid succession', 'transaction surge', 'multiple transactions', 'transaction burst'],
  // Night-time activity variations
  'night-time activity': ['nighttime', 'night time', 'off hours', 'unusual hours', 'nighttime activity', 'after hours'],
  // Account takeover variations
  'account takeover': ['takeover', 'unauthorized access', 'account compromise', 'credential theft'],
  // Unusual amount variations
  'unusual amount': ['amount anomaly', 'suspicious amount', 'outlier', 'unusual transaction', 'amount spike'],
  // Additional fraud types from backend
  'unusual location': ['location anomaly', 'unusual geo', 'geographic anomaly', 'geo mismatch'],
  'high-risk merchant': ['risky merchant', 'high risk', 'dangerous merchant', 'merchant risk'],
  'money mule pattern': ['money mule', 'mule activity', 'transfer chain', 'mule scheme'],
  'structuring / smurfing': ['structuring', 'smurfing', 'structured transactions', 'structuring smurfing'],
  'round-dollar pattern': ['round dollar', 'round amount', 'even amount', 'whole amount'],
  'cross-border anomaly': ['cross border', 'international anomaly', 'foreign transaction', 'crossborder'],
  'suspicious login': ['suspicious access', 'unusual login', 'login anomaly', 'credential risk'],
  'new payee spike': ['new payee', 'payee spike', 'beneficiary spike', 'new beneficiary'],
  'unusual device': ['new device', 'device anomaly', 'device risk', 'unknown device']
};

const normalizeText = (text = '') =>
  text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const getPatternVariations = (patternName = '') => {
  const lower = patternName.toLowerCase();
  const baseVariations = PATTERN_VARIATIONS[lower] || [];
  const rawValues = [
    lower,
    ...baseVariations
  ].filter(Boolean);

  const normalizedValues = [
    normalizeText(patternName),
    ...rawValues.map((value) => normalizeText(value))
  ].filter(Boolean);

  return {
    raw: Array.from(new Set(rawValues)),
    normalized: Array.from(new Set(normalizedValues))
  };
};

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
    merchant: '',
    transactionCountry: '',
    loginCountry: '',
    cardType: '',
    transactionType: '',
    currency: '',
    dateStart: '',
    dateEnd: '',
    fraudOnly: false,
    legitimateOnly: false,
  });
  const [dateFilter, setDateFilter] = useState(null); // 'last_30', 'last_60', 'last_90', 'custom', or null
  const [showFilters, setShowFilters] = useState(false);
  const [filteredPlots, setFilteredPlots] = useState(null);
  const [regeneratingPlots, setRegeneratingPlots] = useState(false);
  const [hoveredFraudPattern, setHoveredFraudPattern] = useState(null);
  const [enlargedFraudPattern, setEnlargedFraudPattern] = useState(null);
  const [showDataSaved, setShowDataSaved] = useState(false);
  const isInitialMount = useRef(true);

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  // Auto-hide "Data Saved" message after 4 seconds
  useEffect(() => {
    if (analysisResult?.database_status === 'saved') {
      setShowDataSaved(true);
      const timer = setTimeout(() => {
        setShowDataSaved(false);
      }, 4000); // 4 seconds

      return () => clearTimeout(timer);
    }
  }, [analysisResult?.database_status]);

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

  const formatAmountInMillions = (amount) => {
    if (!amount || amount === 0) return '$0M';
    const millions = amount / 1000000;
    return `$${millions.toFixed(2)}M`;
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

  const recommendationPatternMap = useMemo(() => {
    const map = new Map();
    const recommendations = analysisResult?.agent_analysis?.recommendations;
    if (!Array.isArray(recommendations)) {
      return map;
    }

    const candidatePatterns = new Set(STANDARD_FRAUD_REASONS);
    fraudReasonChips.forEach((reason) => candidatePatterns.add(reason));

    recommendations.forEach((rec) => {
      if (!rec || typeof rec === 'string') return;
      const normalizedTitle = normalizeText(rec.title || '');
      const normalizedDesc = normalizeText(rec.description || '');

      let bestPattern = null;
      let bestScore = 0;

      candidatePatterns.forEach((pattern) => {
        const variations = getPatternVariations(pattern);
        let score = 0;

        for (const variation of variations.raw) {
          if (!variation) continue;
          if (
            normalizedTitle.includes(variation) ||
            normalizedDesc.includes(variation)
          ) {
            score = 1;
            break;
          }
        }

        if (score < 1) {
          for (const variation of variations.normalized) {
            if (!variation) continue;
            if (
              normalizedTitle.includes(variation) ||
              normalizedDesc.includes(variation)
            ) {
              score = 1;
              break;
            }
          }
        }

        if (score < 1) {
          const patternWords = variations.normalized[0]?.split(' ').filter((w) => w.length > 2) || [];
          if (patternWords.length > 0) {
            const matchCount = patternWords.filter(
              (word) => normalizedTitle.includes(word) || normalizedDesc.includes(word)
            ).length;
            score = Math.max(score, matchCount / patternWords.length);
          }
        }

        if (score > bestScore && score >= 0.4) {
          bestScore = score;
          bestPattern = pattern;
        }
      });

      if (bestPattern) {
        const key = bestPattern.toLowerCase();
        const existing = map.get(key);
        if (!existing || bestScore > existing.score) {
          map.set(key, { recommendation: rec, score: bestScore });
        }
      }
    });

    return map;
  }, [analysisResult?.agent_analysis?.recommendations, fraudReasonChips]);

  // Debug: Log all fraud types and recommendations on load
  useEffect(() => {
    if (analysisResult?.agent_analysis?.recommendations && console && console.log) {
      console.log('=== FRAUD PATTERN MATCHING DEBUG ===');
      console.log('Frontend Fraud Patterns:', Array.from(fraudReasonChips));
      console.log('AI Recommendation Titles:', analysisResult.agent_analysis.recommendations.map(r => r.title));
      console.log('Fraud Reason Breakdown:', fraudReasonBreakdown.map(f => f.label || f.type));
      console.log('===================================');
    }
  }, [analysisResult, fraudReasonChips, fraudReasonBreakdown]);

  // Helper function to get AI recommendation for a specific fraud pattern
  const getRecommendationForPattern = (patternName) => {
    if (!analysisResult?.agent_analysis?.recommendations) return null;

    const preMatched = recommendationPatternMap.get(patternName.toLowerCase());
    if (preMatched) {
      return preMatched.recommendation;
    }

    const normalizedPattern = normalizeText(patternName);
    const patternVariations = getPatternVariations(patternName);

    const recommendation = analysisResult.agent_analysis.recommendations.find((rec) => {
      if (!rec || typeof rec === 'string') return false;

      const title = (rec.title || '').toLowerCase();
      const description = (rec.description || '').toLowerCase();
      const normalizedTitle = normalizeText(rec.title || '');
      const normalizedDesc = normalizeText(rec.description || '');

      if (console && console.log) {
        console.log(`\nMatching "${patternName}" against "${rec.title}" (fallback search)`);
      }

      for (const variation of patternVariations.raw) {
        if (!variation) continue;
        if (title.includes(variation) || description.includes(variation)) {
          if (console && console.log) {
            console.log(` MATCH (Tier 1 - exact): "${variation}" found in title/description`);
          }
          return true;
        }
      }

      for (const variation of patternVariations.normalized) {
        if (!variation) continue;
        if (normalizedTitle.includes(variation) || normalizedDesc.includes(variation)) {
          if (console && console.log) {
            console.log(` MATCH (Tier 2 - normalized): "${variation}" found`);
          }
          return true;
        }
      }

      const patternWords = normalizedPattern.split(/\s+/).filter((w) => w.length > 2);
      if (patternWords.length > 0) {
        const matchCount = patternWords.filter((word) => {
          const found = normalizedTitle.includes(word) || normalizedDesc.includes(word);
          if (found && console && console.log) {
            console.log(`  - Word "${word}" found in title/description`);
          }
          return found;
        }).length;

        const matchPercentage = matchCount / patternWords.length;
        if (console && console.log) {
          console.log(`  - Match percentage: ${(matchPercentage * 100).toFixed(0)}% (${matchCount}/${patternWords.length} words)`);
        }

        if (matchPercentage >= 0.5) {
          if (console && console.log) {
            console.log(` MATCH (Tier 3 - partial): ${(matchPercentage * 100).toFixed(0)}% words matched`);
          }
          return true;
        }
      }

      const titleWords = normalizedTitle.split(/\s+/).filter((w) => w.length > 2);
      if (titleWords.length > 0) {
        const reverseMatchCount = titleWords.filter((word) => normalizedPattern.includes(word)).length;

        if (reverseMatchCount / titleWords.length >= 0.5) {
          if (console && console.log) {
            console.log(` MATCH (Tier 4 - reverse): ${(reverseMatchCount / titleWords.length * 100).toFixed(0)}% of title words in pattern`);
          }
          return true;
        }
      }

      if (console && console.log) {
        console.log(' NO MATCH');
      }
      return false;
    });

    if (!recommendation && console && console.log) {
      console.log(`\n FINAL: No recommendation found for pattern: "${patternName}" (fallback path)`);
      console.log('Available recommendations:', analysisResult.agent_analysis.recommendations.map((r) => r.title));
    } else if (recommendation && console && console.log) {
      console.log(`\n FINAL: Matched "${patternName}" to "${recommendation.title}"`);
    }

    return recommendation || null;
  };

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

      // Detect year range (ascending order)
      let dateRange = 'N/A';
      const dateColumn = headers.find(h =>
        h.toLowerCase().includes('date') ||
        h.toLowerCase().includes('time')
      );

      if (dateColumn) {
        const dates = rows.map(r => r[dateColumn]).filter(d => d);
        if (dates.length > 0) {
          // Extract years from dates
          const years = dates.map(dateStr => {
            try {
              const date = new Date(dateStr);
              return date.getFullYear();
            } catch {
              return null;
            }
          }).filter(year => year && !isNaN(year));

          if (years.length > 0) {
            const minYear = Math.min(...years);
            const maxYear = Math.max(...years);
            dateRange = minYear === maxYear ? `${minYear}` : `${minYear} - ${maxYear}`;
          }
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
        rows: rows.slice(0, 5), // Limit to first 5 rows for preview
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
      amountMin: '',
      amountMax: '',
      fraudProbabilityMin: '',
      fraudProbabilityMax: '',
      category: '',
      merchant: '',
      transactionCountry: '',
      loginCountry: '',
      cardType: '',
      transactionType: '',
      currency: '',
      dateStart: '',
      dateEnd: '',
      fraudOnly: false,
      legitimateOnly: false,
    });
    setDateFilter(null);
  };

  const handleDateFilterChange = (value) => {
    setDateFilter(value);
    if (value === null || value === '') {
      setFilters(prev => ({ ...prev, dateStart: '', dateEnd: '' }));
    } else if (value === 'custom') {
      // Keep existing date inputs for custom
    } else {
      const endDate = new Date();
      const startDate = new Date();
      if (value === 'last_30') {
        startDate.setDate(startDate.getDate() - 30);
      } else if (value === 'last_60') {
        startDate.setDate(startDate.getDate() - 60);
      } else if (value === 'last_90') {
        startDate.setDate(startDate.getDate() - 90);
      }
      setFilters(prev => ({
        ...prev,
        dateStart: startDate.toISOString().split('T')[0],
        dateEnd: endDate.toISOString().split('T')[0]
      }));
    }
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

    // Merchant filter
    if (filters.merchant !== '') {
      filtered = filtered.filter(t =>
        t.merchant?.toLowerCase().includes(filters.merchant.toLowerCase())
      );
    }

    // Transaction Country filter
    if (filters.transactionCountry !== '') {
      filtered = filtered.filter(t =>
        t.transaction_country === filters.transactionCountry
      );
    }

    // Login Country filter
    if (filters.loginCountry !== '') {
      filtered = filtered.filter(t =>
        t.login_country === filters.loginCountry
      );
    }

    // Card Type filter
    if (filters.cardType !== '') {
      filtered = filtered.filter(t =>
        t.card_type === filters.cardType
      );
    }

    // Transaction Type filter
    if (filters.transactionType !== '') {
      filtered = filtered.filter(t =>
        t.transaction_type === filters.transactionType
      );
    }

    // Currency filter
    if (filters.currency !== '') {
      filtered = filtered.filter(t =>
        t.currency === filters.currency
      );
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

  const getAvailableMerchants = () => {
    if (!analysisResult?.transactions) return [];
    const merchants = new Set(
      analysisResult.transactions
        .map(t => t.merchant)
        .filter(m => m && m !== 'N/A' && m !== 'Unknown')
    );
    return Array.from(merchants).sort();
  };

  const getAvailableTransactionCountries = () => {
    if (!analysisResult?.transactions) return [];
    const countries = new Set(
      analysisResult.transactions
        .map(t => t.transaction_country)
        .filter(c => c && c !== 'N/A' && c !== 'Unknown')
    );
    return Array.from(countries).sort();
  };

  const getAvailableLoginCountries = () => {
    if (!analysisResult?.transactions) return [];
    const countries = new Set(
      analysisResult.transactions
        .map(t => t.login_country)
        .filter(c => c && c !== 'N/A' && c !== 'Unknown')
    );
    return Array.from(countries).sort();
  };

  const getAvailableCardTypes = () => {
    if (!analysisResult?.transactions) return [];
    const cardTypes = new Set(
      analysisResult.transactions
        .map(t => t.card_type)
        .filter(c => c && c !== 'N/A' && c !== 'Unknown')
    );
    return Array.from(cardTypes).sort();
  };

  const getAvailableTransactionTypes = () => {
    if (!analysisResult?.transactions) return [];
    const types = new Set(
      analysisResult.transactions
        .map(t => t.transaction_type)
        .filter(t => t && t !== 'N/A' && t !== 'Unknown')
    );
    return Array.from(types).sort();
  };

  const getAvailableCurrencies = () => {
    if (!analysisResult?.transactions) return [];
    const currencies = new Set(
      analysisResult.transactions
        .map(t => t.currency)
        .filter(c => c && c !== 'N/A' && c !== 'Unknown')
    );
    return Array.from(currencies).sort();
  };

  const getDatasetColumns = () => {
    if (!analysisResult?.csv_info?.columns) return [];
    return analysisResult.csv_info.columns.map(col => col.name);
  };

  const hasColumn = (columnName) => {
    const columns = getDatasetColumns();
    return columns.includes(columnName);
  };

  const activeFilterCount = Object.entries(filters).filter(([key, value]) => {
    if (typeof value === 'boolean') return value;
    return value !== '';
  }).length;

  const handleRegeneratePlots = async () => {
    if (!analysisResult?.transactions) {
      console.log('⚠️ No transactions available for plot regeneration');
      return;
    }

    console.log('🔄 Starting plot regeneration...');
    console.log('Current filters:', filters);

    setRegeneratingPlots(true);
    try {
      // Convert filters to backend format
      const backendFilters = {
        amount_min: filters.amountMin ? parseFloat(filters.amountMin) : null,
        amount_max: filters.amountMax ? parseFloat(filters.amountMax) : null,
        fraud_probability_min: filters.fraudProbabilityMin ? parseFloat(filters.fraudProbabilityMin) : null,
        fraud_probability_max: filters.fraudProbabilityMax ? parseFloat(filters.fraudProbabilityMax) : null,
        category: filters.category || null,
        merchant: filters.merchant || null,
        transaction_country: filters.transactionCountry || null,
        login_country: filters.loginCountry || null,
        card_type: filters.cardType || null,
        transaction_type: filters.transactionType || null,
        currency: filters.currency || null,
        date_start: filters.dateStart || null,
        date_end: filters.dateEnd || null,
        fraud_only: filters.fraudOnly || false,
        legitimate_only: filters.legitimateOnly || false,
      };

      // Remove null values
      Object.keys(backendFilters).forEach(key => {
        if (backendFilters[key] === null || backendFilters[key] === '') {
          delete backendFilters[key];
        }
      });

      // Apply filters on frontend to reduce data size
      const filteredTransactions = getFilteredTransactions();

      console.log('📤 Filtered transactions on frontend:', filteredTransactions.length, '(from', analysisResult.transactions.length, 'total)');
      console.log('📤 Sending to backend for plot regeneration...');

      // Send filtered transactions with empty filters since filtering is already done
      const result = await regeneratePlotsWithFilters(filteredTransactions, {});

      console.log('📥 Received result:', {
        success: result.success,
        plotsCount: result.plots?.length || 0,
        error: result.error
      });
      
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

  // Auto-regenerate plots when filters change (with debouncing)
  useEffect(() => {
    // Only run if we have analysis results
    if (!analysisResult?.transactions || analysisResult.transactions.length === 0) {
      console.log('⚠️ Skipping - no transactions loaded yet');
      return;
    }

    // Skip on initial mount with data
    if (isInitialMount.current) {
      isInitialMount.current = false;
      console.log('⏭️ Skipping initial mount - useEffect initialized with data');
      return;
    }

    console.log('🎯 Filter change detected!', {
      transactionCount: analysisResult.transactions.length,
      filterString: JSON.stringify(filters)
    });

    console.log('⏰ Starting 500ms debounce timer...');

    // Debounce the regeneration to avoid excessive API calls
    const timeoutId = setTimeout(() => {
      console.log('✅ Debounce complete! Calling handleRegeneratePlots NOW');
      handleRegeneratePlots();
    }, 500); // 500ms debounce

    return () => {
      console.log('🧹 Cleanup: Clearing previous debounce timer');
      clearTimeout(timeoutId);
    };
  }, [filters]);

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
      gridTemplateColumns: 'repeat(2, 1fr)',
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
      {/* CSS Animation for Popover */}
      <style>
        {`
          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateX(-50%) translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateX(-50%) translateY(0);
            }
          }

          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }
        `}
      </style>

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
              placeholder="https://payments-api.yourbank.com/transactions"
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
              <div style={styles.previewStatLabel}>Year Range</div>
              <div style={{ ...styles.previewStatValue, fontSize: '0.9rem' }}>{csvPreview.dateRange || 'N/A'}</div>
            </div>
          </div>

          {/* First 5 Rows Preview */}
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
                {formatAmountInMillions(analysisResult.fraud_detection.total_amount || 0)}
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>Fraud Amount</div>
              <div style={{ ...styles.statValue, ...styles.fraudStat, fontSize: '1.5rem' }}>
                {formatAmountInMillions(analysisResult.fraud_detection.total_fraud_amount || 0)}
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
            <div style={styles.reasonLegendTitle}>
              Standard Fraud Patterns
              <span style={{ fontSize: '0.75rem', fontWeight: 400, color: colors.mutedForeground, marginLeft: '0.5rem' }}>
                (Hover to preview, click to enlarge)
              </span>
            </div>
              <div style={styles.reasonLegendGrid}>
                {fraudReasonChips.map((reason) => {
                const count = reasonCountMap[reason] || 0;
                const isActive = count > 0;
                const hasAIRecommendation = isActive && getRecommendationForPattern(reason);

                return (
                  <div
                    key={reason}
                    style={{
                      ...styles.reasonLegendChip,
                      opacity: isActive ? 1 : 0.45,
                      borderColor: isActive ? primary : colors.border,
                      color: colors.foreground,
                      cursor: hasAIRecommendation ? 'pointer' : 'default',
                      position: 'relative',
                      transition: 'all 0.2s ease',
                      transform: hoveredFraudPattern === reason ? 'scale(1.02)' : 'scale(1)',
                      boxShadow: hoveredFraudPattern === reason ? `0 4px 12px rgba(0,0,0,0.15)` : 'none'
                    }}
                    onMouseEnter={() => hasAIRecommendation && setHoveredFraudPattern(reason)}
                    onMouseLeave={() => setHoveredFraudPattern(null)}
                    onClick={() => hasAIRecommendation && getRecommendationForPattern(reason) && setEnlargedFraudPattern(reason)}
                  >
                    <span>{reason}</span>
                    <span style={{ fontWeight: 600 }}>
                      {isActive ? `${count} case${count === 1 ? '' : 's'}` : '—'}
                    </span>

                    {/* Recommendation Popover - positioned relative to this chip */}
                    {hoveredFraudPattern === reason && getRecommendationForPattern(reason) && (
                <div>
                  {(() => {
                    const rec = getRecommendationForPattern(reason);
                    const isCritical = (rec.title || '').includes('CRITICAL');
                    const isHigh = (rec.title || '').includes('HIGH');
                    const isMedium = (rec.title || '').includes('MEDIUM');
                    const isLow = (rec.title || '').includes('LOW');

                    // Define severity colors
                    const severityColor = isCritical ? '#ef4444' : // Red for CRITICAL
                                        isHigh ? '#f97316' : // Orange for HIGH
                                        isMedium ? '#fb923c' : // Light orange for MEDIUM
                                        isLow ? '#60a5fa' : // Blue for LOW
                                        primary; // Default

                    const severityBgColor = isCritical ? 'rgba(239, 68, 68, 0.1)' : // Red bg
                                          isHigh ? 'rgba(249, 115, 22, 0.1)' : // Orange bg
                                          isMedium ? 'rgba(251, 146, 60, 0.1)' : // Light orange bg
                                          isLow ? 'rgba(96, 165, 250, 0.1)' : // Blue bg
                                          'transparent';

                    return (
                      <div 
                        style={{
                          position: 'absolute',
                          bottom: '100%',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          marginBottom: '10px',
                          backgroundColor: colors.card || colors.background,
                          border: `3px solid ${severityColor}`,
                          borderRadius: '8px',
                          padding: '0.75rem 1rem',
                          minWidth: '600px',
                          maxWidth: '700px',
                          boxShadow: `0 10px 40px rgba(0,0,0,0.3), 0 0 0 1px ${severityColor}20`,
                          zIndex: 1000,
                          animation: 'fadeIn 0.2s ease',
                          cursor: 'pointer'
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setEnlargedFraudPattern(reason);
                        }}
                      >
                        {/* Arrow pointing down */}
                        <div style={{
                          position: 'absolute',
                          bottom: '-12px',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: '12px solid transparent',
                          borderRight: '12px solid transparent',
                          borderTop: `12px solid ${severityColor}`
                        }} />

                        {/* Header */}
                        <div style={{
                          fontWeight: '600',
                          color: colors.foreground,
                          marginBottom: '0.5rem',
                          fontSize: '0.95rem',
                          borderBottom: `2px solid ${severityColor}`,
                          paddingBottom: '0.5rem'
                        }}>
                          {rec.title}
                        </div>

                        {/* Description */}
                        <div style={{
                          fontSize: '0.85rem',
                          color: colors.mutedForeground,
                          marginBottom: '0.75rem',
                          lineHeight: '1.4'
                        }}>
                          {rec.description}
                        </div>

                        {/* Stats */}
                        {(rec.fraud_rate || rec.case_count || rec.total_amount) && (
                          <div style={{
                            display: 'flex',
                            gap: '1rem',
                            fontSize: '0.75rem',
                            color: colors.mutedForeground,
                            marginBottom: '0.75rem',
                            padding: '0.5rem',
                            backgroundColor: colors.muted,
                            borderRadius: '4px'
                          }}>
                            {rec.case_count && <span>{rec.case_count}</span>}
                            {rec.fraud_rate && <span>{rec.fraud_rate}</span>}
                            {rec.total_amount && <span>{rec.total_amount}</span>}
                          </div>
                        )}

                        {/* Two Column Layout for Actions and Prevention */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                          {/* Immediate Actions */}
                          {rec.immediate_actions && rec.immediate_actions.length > 0 && (
                            <div>
                              <div style={{
                                fontWeight: '600',
                                fontSize: '0.8rem',
                                marginBottom: '0.4rem',
                                color: colors.foreground
                              }}>
                                Immediate Actions:
                              </div>
                              <ul style={{
                                margin: 0,
                                paddingLeft: '1.25rem',
                                fontSize: '0.75rem',
                                color: colors.foreground,
                                lineHeight: '1.6'
                              }}>
                                {rec.immediate_actions.slice(0, 3).map((action, i) => (
                                  <li key={i}>{action}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Prevention Steps */}
                          {rec.prevention_steps && rec.prevention_steps.length > 0 && (
                            <div>
                              <div style={{
                                fontWeight: '600',
                                fontSize: '0.8rem',
                                marginBottom: '0.4rem',
                                color: colors.foreground
                              }}>
                                Prevention Steps:
                              </div>
                              <ul style={{
                                margin: 0,
                                paddingLeft: '1.25rem',
                                fontSize: '0.75rem',
                                color: colors.foreground,
                                lineHeight: '1.6'
                              }}>
                                {rec.prevention_steps.slice(0, 3).map((step, i) => (
                                  <li key={i}>{step}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

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

          {/* Database Storage Notification - Auto-hides after 7 seconds */}
          {analysisResult?.database_status === 'saved' && showDataSaved && (
            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              backgroundColor: '#d1fae5',
              border: '1px solid #6ee7b7',
              borderRadius: '0.5rem',
              color: '#065f46',
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              animation: 'fadeIn 0.3s ease-in'
            }}>
              <span style={{ fontSize: '1.2rem' }}>✓</span>
              <div>
                <strong>Data Saved</strong>
              </div>
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
                  {(() => {
                    // Deduplicate: keep only 1 transaction per merchant-amount-category combination
                    const seen = new Set();
                    const uniqueTransactions = analysisResult.agent_analysis.top_transactions.transactions.filter(txn => {
                      // Create a key based on merchant, amount, and category to identify truly identical transactions
                      const key = `${txn.merchant || 'unknown'}-${txn.amount || 0}-${txn.category || 'unknown'}`;
                      if (seen.has(key)) {
                        return false; // Skip duplicate
                      }
                      seen.add(key);
                      return true; // Keep first occurrence
                    });
                    return uniqueTransactions.slice(0, 5).map((txn, idx) => (
                      <div key={`${txn.merchant || 'unknown'}-${txn.amount}-${idx}`} style={{
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
                    ));
                  })()}
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

            </div>
          )}

          {/* Filter Bar - Matching CheckInsights Style */}
          <div style={{
            display: 'flex',
            gap: '10px',
            marginBottom: '20px',
            alignItems: 'center',
            flexWrap: 'wrap'
          }}>
            {/* Merchant/Bank Filter */}
            {hasColumn('merchant') && getAvailableMerchants().length > 0 && (
              <select
                value={filters.merchant || ''}
                onChange={(e) => handleFilterChange('merchant', e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Merchants</option>
                {getAvailableMerchants().slice(0, 20).map((merchant) => (
                  <option key={merchant} value={merchant}>
                    {merchant}
                  </option>
                ))}
              </select>
            )}

            {/* Time Filter */}
            {hasColumn('timestamp') && (
              <select
                value={dateFilter || ''}
                onChange={(e) => handleDateFilterChange(e.target.value || null)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Time</option>
                <option value="last_30">Last 30 Days</option>
                <option value="last_60">Last 60 Days</option>
                <option value="last_90">Last 90 Days</option>
                <option value="custom">Custom Range</option>
              </select>
            )}

            {/* Custom Date Range - Show when custom is selected */}
            {dateFilter === 'custom' && hasColumn('timestamp') && (
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="date"
                  value={filters.dateStart}
                  onChange={(e) => handleFilterChange('dateStart', e.target.value)}
                  style={{
                    padding: '8px 12px',
                    border: `1px solid ${colors.border}`,
                    borderRadius: '4px',
                    fontSize: '14px',
                    backgroundColor: colors.card || colors.background,
                    color: colors.foreground
                  }}
                />
                <span style={{ color: colors.mutedForeground }}>to</span>
                <input
                  type="date"
                  value={filters.dateEnd}
                  onChange={(e) => handleFilterChange('dateEnd', e.target.value)}
                  style={{
                    padding: '8px 12px',
                    border: `1px solid ${colors.border}`,
                    borderRadius: '4px',
                    fontSize: '14px',
                    backgroundColor: colors.card || colors.background,
                    color: colors.foreground
                  }}
                />
              </div>
            )}

            {/* Category Filter */}
            {hasColumn('category') && getAvailableCategories().length > 0 && (
              <select
                value={filters.category || ''}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Categories</option>
                {getAvailableCategories().map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            )}

            {/* Transaction Country Filter */}
            {hasColumn('transaction_country') && getAvailableTransactionCountries().length > 0 && (
              <select
                value={filters.transactionCountry || ''}
                onChange={(e) => handleFilterChange('transactionCountry', e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Transaction Countries</option>
                {getAvailableTransactionCountries().slice(0, 20).map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            )}

            {/* Login Country Filter */}
            {hasColumn('login_country') && getAvailableLoginCountries().length > 0 && (
              <select
                value={filters.loginCountry || ''}
                onChange={(e) => handleFilterChange('loginCountry', e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Login Countries</option>
                {getAvailableLoginCountries().slice(0, 20).map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            )}

            {/* Card Type Filter */}
            {hasColumn('card_type') && getAvailableCardTypes().length > 0 && (
              <select
                value={filters.cardType || ''}
                onChange={(e) => handleFilterChange('cardType', e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Card Types</option>
                {getAvailableCardTypes().map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            )}

            {/* Transaction Type Filter */}
            {hasColumn('transaction_type') && getAvailableTransactionTypes().length > 0 && (
              <select
                value={filters.transactionType || ''}
                onChange={(e) => handleFilterChange('transactionType', e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Transaction Types</option>
                {getAvailableTransactionTypes().map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            )}

            {/* Currency Filter */}
            {hasColumn('currency') && getAvailableCurrencies().length > 0 && (
              <select
                value={filters.currency || ''}
                onChange={(e) => handleFilterChange('currency', e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Currencies</option>
                {getAvailableCurrencies().map((curr) => (
                  <option key={curr} value={curr}>
                    {curr}
                  </option>
                ))}
              </select>
            )}

            {/* Fraud Type Filter */}
            {hasColumn('fraud_probability') && (
              <select
                value={filters.fraudOnly ? 'fraud' : filters.legitimateOnly ? 'legitimate' : ''}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === 'fraud') {
                    handleFilterChange('fraudOnly', true);
                    handleFilterChange('legitimateOnly', false);
                  } else if (value === 'legitimate') {
                    handleFilterChange('fraudOnly', false);
                    handleFilterChange('legitimateOnly', true);
                  } else {
                    handleFilterChange('fraudOnly', false);
                    handleFilterChange('legitimateOnly', false);
                  }
                }}
                style={{
                  padding: '8px 12px',
                  border: `1px solid ${colors.border}`,
                  borderRadius: '4px',
                  fontSize: '14px',
                  backgroundColor: colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer'
                }}
              >
                <option value="">All Fraud Types</option>
                <option value="fraud">Fraud Only</option>
                <option value="legitimate">Legitimate Only</option>
              </select>
            )}

            {/* Reset Filters Button */}
              <button
              onClick={() => {
                resetFilters();
                setFilteredPlots(null);
              }}
                style={{
                padding: '8px 16px',
                borderRadius: '4px',
                border: `1px solid ${colors.border}`,
                backgroundColor: colors.secondary || colors.card || colors.background,
                  color: colors.foreground,
                  cursor: 'pointer',
                fontSize: '14px',
                  fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = colors.muted;
                e.target.style.borderColor = primary;
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = colors.secondary || colors.card || colors.background;
                e.target.style.borderColor = colors.border;
              }}
            >
              <FaTimes style={{ fontSize: '0.85rem' }} />
              Reset Filters
            </button>

            {/* Showing count - Always visible */}
            <span style={{
              fontSize: '12px',
              color: colors.mutedForeground,
              whiteSpace: 'nowrap',
              marginLeft: 'auto'
            }}>
              Showing {getFilteredTransactions().length} of {analysisResult?.transactions?.length || 0} transactions
            </span>
          </div>

          {/* Apply Filters Button - REMOVED: Plots now auto-update with filters */}
          {/* Real-time plot updates enabled - filters apply automatically with 500ms debounce */}
            
          {/* Old filter UI - Hidden */}
          {false && (
              <div style={{
                backgroundColor: colors.muted,
                padding: '1.5rem',
                borderRadius: '0.75rem',
                border: `1px solid ${colors.border}`,
                marginBottom: '1rem'
              }}>
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ color: colors.foreground, fontSize: '0.95rem', fontWeight: '600', marginBottom: '0.5rem', marginTop: 0 }}>
                    Filter Plots by Dataset Columns
                  </h4>
                  <p style={{ color: colors.mutedForeground, fontSize: '0.85rem', margin: 0 }}>
                    Available filters are based on your dataset columns: {getDatasetColumns().join(', ')}
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                  {/* Amount Filters - Always available */}
                  {hasColumn('amount') && (
                    <>
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
                    </>
                  )}

                  {/* Fraud Probability Filters */}
                  {hasColumn('fraud_probability') && (
                    <>
                  <div>
                    <label style={styles.label}>Min Fraud Probability</label>
                    <select
                      value={filters.fraudProbabilityMin}
                      onChange={(e) => handleFilterChange('fraudProbabilityMin', e.target.value)}
                      style={styles.input}
                    >
                          <option value="">-- All --</option>
                      <option value="0">0% (All)</option>
                      <option value="0.1">10%</option>
                      <option value="0.2">20%</option>
                      <option value="0.3">30%</option>
                      <option value="0.4">40%</option>
                      <option value="0.5">50%</option>
                      <option value="0.6">60%</option>
                      <option value="0.7">70%</option>
                      <option value="0.8">80%</option>
                      <option value="0.9">90%</option>
                    </select>
                  </div>
                  <div>
                    <label style={styles.label}>Max Fraud Probability</label>
                    <select
                      value={filters.fraudProbabilityMax}
                      onChange={(e) => handleFilterChange('fraudProbabilityMax', e.target.value)}
                      style={styles.input}
                    >
                          <option value="">-- All --</option>
                      <option value="0.1">10%</option>
                      <option value="0.2">20%</option>
                      <option value="0.3">30%</option>
                      <option value="0.4">40%</option>
                      <option value="0.5">50%</option>
                      <option value="0.6">60%</option>
                      <option value="0.7">70%</option>
                      <option value="0.8">80%</option>
                      <option value="0.9">90%</option>
                      <option value="1">100%</option>
                    </select>
                  </div>
                    </>
                  )}

                  {/* Category Filter - Only if category column exists */}
                  {hasColumn('category') && getAvailableCategories().length > 0 && (
                  <div>
                    <label style={styles.label}>Category</label>
                    <select
                      value={filters.category}
                      onChange={(e) => handleFilterChange('category', e.target.value)}
                      style={styles.input}
                    >
                      <option value="">-- All Categories --</option>
                      {getAvailableCategories().map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </select>
                  </div>
                  )}

                  {/* Merchant Filter - Only if merchant column exists */}
                  {hasColumn('merchant') && getAvailableMerchants().length > 0 && (
                    <div>
                      <label style={styles.label}>Merchant</label>
                      <select
                        value={filters.merchant}
                        onChange={(e) => handleFilterChange('merchant', e.target.value)}
                        style={styles.input}
                      >
                        <option value="">-- All Merchants --</option>
                        {getAvailableMerchants().map((merchant) => (
                          <option key={merchant} value={merchant}>
                            {merchant}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Date Filters - Only if timestamp column exists */}
                  {hasColumn('timestamp') && (
                    <>
                  <div>
                    <label style={styles.label}>Start Date</label>
                    <input
                      type="date"
                      value={filters.dateStart}
                      onChange={(e) => handleFilterChange('dateStart', e.target.value)}
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={styles.label}>End Date</label>
                    <input
                      type="date"
                      value={filters.dateEnd}
                      onChange={(e) => handleFilterChange('dateEnd', e.target.value)}
                      style={styles.input}
                    />
                  </div>
                    </>
                  )}
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

          {/* Plots */}
          {(() => {
            const plotsToDisplay = filteredPlots || analysisResult.insights.plots;
            console.log('Plots to display:', plotsToDisplay);
            return plotsToDisplay?.length > 0;
          })() && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ color: colors.foreground, fontSize: '1.1rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  Visual Analytics
                  {regeneratingPlots && (
                    <span style={{
                      fontSize: '0.85rem',
                      color: '#f59e0b',
                      fontWeight: '600',
                      backgroundColor: '#fef3c7',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '0.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}>
                      <span className="spinner" style={{
                        display: 'inline-block',
                        width: '12px',
                        height: '12px',
                        border: '2px solid #f59e0b',
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 0.8s linear infinite'
                      }} />
                      Updating plots...
                    </span>
                  )}
                  {!regeneratingPlots && filteredPlots && (
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
                  {!regeneratingPlots && !filteredPlots && (
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

      {/* Enlarged Fraud Pattern Modal */}
      {enlargedFraudPattern && getRecommendationForPattern(enlargedFraudPattern) && (() => {
        const rec = getRecommendationForPattern(enlargedFraudPattern);
        const isCritical = (rec.title || '').includes('CRITICAL');
        const isHigh = (rec.title || '').includes('HIGH');
        const isMedium = (rec.title || '').includes('MEDIUM');
        const isLow = (rec.title || '').includes('LOW');

        const severityColor = isCritical ? '#ef4444' :
                            isHigh ? '#f97316' :
                            isMedium ? '#fb923c' :
                            isLow ? '#60a5fa' :
                            primary;

        return (
          <div 
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.75)',
              zIndex: 10000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem',
              animation: 'fadeIn 0.2s ease'
            }}
            onClick={() => setEnlargedFraudPattern(null)}
          >
            <div 
              style={{
                backgroundColor: colors.card || colors.background,
                border: `3px solid ${severityColor}`,
                borderRadius: '12px',
                padding: '2rem',
                maxWidth: '900px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto',
                boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px ${severityColor}20`,
                position: 'relative'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close Button */}
              <button
                style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  background: 'transparent',
                  border: 'none',
                  color: colors.foreground,
                  fontSize: '2rem',
                  cursor: 'pointer',
                  width: '2.5rem',
                  height: '2.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '50%',
                  transition: 'background-color 0.2s',
                }}
                onClick={() => setEnlargedFraudPattern(null)}
                onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(148, 163, 184, 0.2)'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
              >
                &times;
              </button>

              {/* Header */}
              <div style={{
                fontWeight: '700',
                color: colors.foreground,
                marginBottom: '1rem',
                fontSize: '1.5rem',
                borderBottom: `3px solid ${severityColor}`,
                paddingBottom: '1rem',
                paddingRight: '3rem'
              }}>
                {rec.title}
              </div>

              {/* Description */}
              <div style={{
                fontSize: '1rem',
                color: colors.mutedForeground,
                marginBottom: '1.5rem',
                lineHeight: '1.6'
              }}>
                {rec.description}
              </div>

              {/* Stats */}
              {(rec.fraud_rate || rec.case_count || rec.total_amount) && (
                <div style={{
                  display: 'flex',
                  gap: '2rem',
                  fontSize: '0.9rem',
                  color: colors.mutedForeground,
                  marginBottom: '1.5rem',
                  padding: '1rem',
                  backgroundColor: colors.muted,
                  borderRadius: '8px'
                }}>
                  {rec.case_count && <span><strong>Cases:</strong> {rec.case_count}</span>}
                  {rec.fraud_rate && <span><strong>Fraud Rate:</strong> {rec.fraud_rate}</span>}
                  {rec.total_amount && <span><strong>Total Amount:</strong> {rec.total_amount}</span>}
                </div>
              )}

              {/* Two Column Layout for Actions and Prevention */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                {/* Immediate Actions */}
                {rec.immediate_actions && rec.immediate_actions.length > 0 && (
                  <div>
                    <div style={{
                      fontWeight: '700',
                      fontSize: '1.1rem',
                      marginBottom: '0.75rem',
                      color: colors.foreground,
                      borderBottom: `2px solid ${severityColor}`,
                      paddingBottom: '0.5rem'
                    }}>
                      Immediate Actions:
                    </div>
                    <ul style={{
                      margin: 0,
                      paddingLeft: '1.5rem',
                      fontSize: '0.95rem',
                      color: colors.foreground,
                      lineHeight: '1.8'
                    }}>
                      {rec.immediate_actions.map((action, i) => (
                        <li key={i} style={{ marginBottom: '0.5rem' }}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Prevention Steps */}
                {rec.prevention_steps && rec.prevention_steps.length > 0 && (
                  <div>
                    <div style={{
                      fontWeight: '700',
                      fontSize: '1.1rem',
                      marginBottom: '0.75rem',
                      color: colors.foreground,
                      borderBottom: `2px solid ${severityColor}`,
                      paddingBottom: '0.5rem'
                    }}>
                      Prevention Steps:
                    </div>
                    <ul style={{
                      margin: 0,
                      paddingLeft: '1.5rem',
                      fontSize: '0.95rem',
                      color: colors.foreground,
                      lineHeight: '1.8'
                    }}>
                      {rec.prevention_steps.map((step, i) => (
                        <li key={i} style={{ marginBottom: '0.5rem' }}>{step}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default RealTimeAnalysis;
