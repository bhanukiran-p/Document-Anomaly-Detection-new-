import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { FaLink, FaUpload, FaArrowLeft, FaChartBar } from 'react-icons/fa';
import { analyzeRealTimeTransactions } from '../services/api';

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

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

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
    plotImageWrapper: {
      position: 'relative',
      borderRadius: '0.75rem',
      overflow: 'hidden',
    },
    plotImage: {
      width: '100%',
      display: 'block',
    },
    plotHoverOverlay: {
      position: 'absolute',
      inset: 0,
      background: 'linear-gradient(180deg, rgba(15,23,42,0.05) 0%, rgba(15,23,42,0.9) 100%)',
      color: '#f8fafc',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      padding: '1.5rem',
      gap: '0.75rem',
      opacity: 0,
      transition: 'opacity 0.25s ease',
    },
    plotOverlayTitle: {
      fontSize: '0.95rem',
      fontWeight: 600,
      letterSpacing: '0.04em',
      textTransform: 'uppercase',
      color: '#cbd5f5',
    },
    plotDetailItem: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '0.95rem',
      borderBottom: '1px solid rgba(148, 163, 184, 0.25)',
      paddingBottom: '0.35rem',
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
          </div>

          {/* Action Buttons */}
          <div style={styles.buttonGroup}>
            <button
              style={styles.insightsButton}
              onClick={() => setShowInsights(!showInsights)}
            >
              <FaChartBar />
              {showInsights ? 'Hide Insights' : 'Show Insights & Plots'}
            </button>
          </div>

          {/* Top Fraud Cases */}
          {analysisResult.insights?.top_fraud_cases?.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ color: colors.foreground, fontSize: '1.1rem', marginBottom: '1rem' }}>
                Top Fraud Cases
              </h3>
              <div style={styles.transactionList}>
                {analysisResult.insights.top_fraud_cases.map((txn, idx) => (
                  <div key={idx} style={{ ...styles.transactionItem, ...styles.fraudTransaction }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <strong style={{ color: colors.foreground }}>
                        {txn.merchant || 'Unknown Merchant'}
                      </strong>
                      <span style={{ color: '#ef4444', fontWeight: '700' }}>
                        ${txn.amount.toFixed(2)}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: colors.mutedForeground }}>
                      Fraud Probability: {(txn.fraud_probability * 100).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '0.85rem', color: colors.mutedForeground, marginTop: '0.25rem' }}>
                      {txn.reason}
                    </div>
                  </div>
                ))}
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

          {/* Recommendations */}
          {analysisResult.insights.recommendations?.length > 0 && (
            <div style={{ marginBottom: '2rem' }}>
              <h3 style={{ color: colors.foreground, fontSize: '1.1rem', marginBottom: '1rem' }}>
                Recommendations
              </h3>
              <ul style={styles.recommendationsList}>
                {analysisResult.insights.recommendations.map((rec, idx) => (
                  <li key={idx} style={styles.recommendationItem}>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Fraud Patterns */}
          {analysisResult.insights.fraud_patterns?.patterns?.length > 0 && (
            <div style={{ marginBottom: '2rem' }}>
              <h3 style={{ color: colors.foreground, fontSize: '1.1rem', marginBottom: '1rem' }}>
                Fraud Patterns Detected
              </h3>
              {analysisResult.insights.fraud_patterns.patterns.map((pattern, idx) => (
                <div key={idx} style={styles.patternCard}>
                  <div style={{ fontWeight: '600', color: colors.foreground, marginBottom: '0.25rem' }}>
                    {pattern.type.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: colors.mutedForeground }}>
                    {pattern.description}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Plots */}
          {analysisResult.insights.plots?.length > 0 && (
            <div>
              <h3 style={{ color: colors.foreground, fontSize: '1.1rem', marginBottom: '1rem' }}>
                Visual Analytics
              </h3>
              <div style={styles.plotsGrid}>
                {analysisResult.insights.plots.map((plot, idx) => {
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
                      }}
                      onMouseEnter={() => setHoveredPlotIndex(idx)}
                      onMouseLeave={() => setHoveredPlotIndex(null)}
                    >
                      <div style={styles.plotTitle}>{plot.title}</div>
                      <div style={styles.plotImageWrapper}>
                        <img src={plot.image} alt={plot.title} style={styles.plotImage} />
                        {plot.details?.length > 0 && (
                          <div
                            style={{
                              ...styles.plotHoverOverlay,
                              opacity: isHovered ? 1 : 0,
                            }}
                          >
                            <div style={styles.plotOverlayTitle}>Key Highlights</div>
                            {plot.details.map((detail, detailIdx) => (
                              <div key={detailIdx} style={styles.plotDetailItem}>
                                <span style={{ color: 'rgba(226, 232, 240, 0.8)' }}>
                                  {detail.label}
                                </span>
                                <strong>{detail.value}</strong>
                              </div>
                            ))}
                          </div>
                        )}
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
    </div>
  );
};

export default RealTimeAnalysis;
