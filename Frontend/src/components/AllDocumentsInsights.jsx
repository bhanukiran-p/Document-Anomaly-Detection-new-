import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { colors } from '../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LabelList
} from 'recharts';
import { FaUpload, FaCog } from 'react-icons/fa';
import CheckInsights from './CheckInsights';
import MoneyOrderInsights from './MoneyOrderInsights';

const AllDocumentsInsights = () => {
  const navigate = useNavigate();
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputMode, setInputMode] = useState('api'); // 'upload' or 'api'
  const [documentsList, setDocumentsList] = useState([]);
  const [allDocumentsData, setAllDocumentsData] = useState([]);
  const [loadingDocumentsList, setLoadingDocumentsList] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null);
  const [documentTypeFilter, setDocumentTypeFilter] = useState(null);
  const [totalRecords, setTotalRecords] = useState(0);
  const [availableDocumentTypes, setAvailableDocumentTypes] = useState([]);

  // Normalize document type filter for comparison
  const normalizedDocumentType = documentTypeFilter 
    ? documentTypeFilter.toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_')
    : null;
  
  // Determine which component to render based on document type filter
  const shouldRenderDedicatedDashboard = normalizedDocumentType && 
    (normalizedDocumentType === 'check' || 
     normalizedDocumentType === 'money_order' || 
     normalizedDocumentType === 'paystub' || 
     normalizedDocumentType === 'bank_statement');

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

  const processData = (rows) => {
    if (!rows.length) return null;

    // 1. Fraud Rate by Document Type
    const fraudRateByType = {};
    const typeCounts = {};
    
    rows.forEach(r => {
      const type = r['document_type'] || r['DocumentType'] || 'Unknown';
      const riskScore = parseFloat_(r['fraud_risk_score'] || r['RiskScore'] || 0);
      const riskScorePercent = riskScore * 100;
      const decision = (r['ai_recommendation'] || r['decision'] || r['status'] || '').toString().toUpperCase();
      
      // Initialize if needed
      if (!fraudRateByType[type]) {
        fraudRateByType[type] = { total: 0, fraud: 0 };
      }
      if (!typeCounts[type]) {
        typeCounts[type] = 0;
      }
      
      typeCounts[type]++;
      fraudRateByType[type].total++;
      
      // Count as fraud if: risk_score >= 70 OR decision = "REJECT"
      if (riskScorePercent >= 70 || decision === 'REJECT') {
        fraudRateByType[type].fraud++;
      }
    });
    
    const fraudRateData = Object.entries(fraudRateByType)
      .map(([name, data]) => ({
        name,
        fraudRate: data.total > 0 ? ((data.fraud / data.total) * 100).toFixed(1) : '0.0',
        fraudCount: data.fraud,
        totalCount: data.total
      }))
      .filter(item => item.totalCount > 0)
      .sort((a, b) => parseFloat(b.fraudRate) - parseFloat(a.fraudRate));
    
    // Document Type Distribution (for pie chart if space allows)
    const documentTypeData = Object.entries(typeCounts)
      .map(([name, value]) => ({ name, value }))
      .filter(item => item.value > 0);

    // 3. Risk Level Distribution (for stacked bar chart)
    // Calculate based on risk_score thresholds: LOW (<50%), MEDIUM (50-75%), HIGH (>=75%)
    const totalRecords = rows.length;
    let lowCount = 0;
    let mediumCount = 0;
    let highCount = 0;
    
    rows.forEach(r => {
      const riskScore = parseFloat_(r['fraud_risk_score'] || r['RiskScore'] || 0);
      const riskScorePercent = riskScore * 100;
      
      if (riskScorePercent >= 75) {
        highCount++;
      } else if (riskScorePercent >= 50) {
        mediumCount++;
      } else {
        lowCount++;
      }
    });
    
    const riskLevelData = {
      lowCount,
      mediumCount,
      highCount,
      totalRecords,
      lowPercent: totalRecords > 0 ? ((lowCount / totalRecords) * 100).toFixed(1) : '0.0',
      mediumPercent: totalRecords > 0 ? ((mediumCount / totalRecords) * 100).toFixed(1) : '0.0',
      highPercent: totalRecords > 0 ? ((highCount / totalRecords) * 100).toFixed(1) : '0.0'
    };


    // 4. Risk Score Trends Over Time
    const dateRisks = {};
    rows.forEach(r => {
      const dateStr = r['upload_date'] || r['UploadDate'] || r['created_at'] || '';
      if (dateStr) {
        const date = dateStr.split('T')[0];
        if (!dateRisks[date]) {
          dateRisks[date] = { count: 0, totalRisk: 0 };
        }
        dateRisks[date].count++;
        dateRisks[date].totalRisk += parseFloat_(r['fraud_risk_score'] || r['RiskScore'] || 0);
      }
    });
    const riskTrends = Object.entries(dateRisks)
      .map(([date, data]) => ({
        date,
        avgRisk: ((data.totalRisk / data.count) * 100).toFixed(1)
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-30); // Last 30 days

    // 6. Fraud Contribution by Document Type (%)
    // Calculate what percentage of total high-risk documents each type contributes
    const highRiskByType = {};
    rows.forEach(r => {
      const type = r['document_type'] || r['DocumentType'] || 'Unknown';
      const riskScore = parseFloat_(r['fraud_risk_score'] || r['RiskScore'] || 0);
      const riskScorePercent = riskScore * 100;
      
      // Count as high-risk if: risk_score >= 75 (HIGH threshold)
      if (riskScorePercent >= 75) {
        if (!highRiskByType[type]) {
          highRiskByType[type] = 0;
        }
        highRiskByType[type]++;
      }
    });
    
    const totalHighRisk = Object.values(highRiskByType).reduce((sum, count) => sum + count, 0);
    const fraudContributionData = Object.entries(highRiskByType)
      .map(([name, count]) => ({
        name,
        value: count,
        percent: totalHighRisk > 0 ? ((count / totalHighRisk) * 100).toFixed(1) : '0.0'
      }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value);

    // 7. Top High-Risk Entities
    // Try to find entity fields: employee_name, employer_name, bank_name, payer, payee, purchaser_name
    const entityData = {};
    rows.forEach(r => {
      const riskScore = parseFloat_(r['fraud_risk_score'] || r['RiskScore'] || 0);
      const riskScorePercent = riskScore * 100;
      
      // Try different entity fields based on document type
      let entityName = null;
      const type = (r['document_type'] || r['DocumentType'] || '').toLowerCase();
      
      if (type.includes('paystub')) {
        entityName = r['employee_name'] || r['EmployeeName'] || r['employer_name'] || r['EmployerName'];
      } else if (type.includes('check')) {
        entityName = r['bank_name'] || r['BankName'] || r['payer'] || r['Payer'] || r['payee'] || r['Payee'];
      } else if (type.includes('money_order')) {
        entityName = r['purchaser_name'] || r['PurchaserName'] || r['issuer'] || r['Issuer'] || r['payee_name'] || r['PayeeName'];
      } else {
        // Fallback: try common fields
        entityName = r['employee_name'] || r['EmployeeName'] || 
                    r['employer_name'] || r['EmployerName'] ||
                    r['bank_name'] || r['BankName'] ||
                    r['payer'] || r['Payer'] ||
                    r['payee'] || r['Payee'] ||
                    r['purchaser_name'] || r['PurchaserName'];
      }
      
      if (entityName && entityName.trim() && entityName !== 'Unknown' && entityName.toLowerCase() !== 'unknown') {
        const entityKey = entityName.trim();
        if (!entityData[entityKey]) {
          entityData[entityKey] = {
            name: entityKey,
            totalRisk: 0,
            count: 0,
            highRiskCount: 0
          };
        }
        entityData[entityKey].count++;
        entityData[entityKey].totalRisk += riskScorePercent;
        if (riskScorePercent >= 75) {
          entityData[entityKey].highRiskCount++;
        }
      }
    });
    
    const topHighRiskEntities = Object.values(entityData)
      .map(entity => ({
        name: entity.name,
        avgRisk: entity.count > 0 ? (entity.totalRisk / entity.count).toFixed(1) : '0.0',
        highRiskCount: entity.highRiskCount,
        totalCount: entity.count
      }))
      .filter(item => item.totalCount > 0)
      .sort((a, b) => {
        // Sort by high-risk count first, then by average risk
        if (b.highRiskCount !== a.highRiskCount) {
          return b.highRiskCount - a.highRiskCount;
        }
        return parseFloat(b.avgRisk) - parseFloat(a.avgRisk);
      })
      .slice(0, 10); // Top 10

    // 8. Summary Metrics
    const totalDocuments = rows.length;
    const riskScores = rows.map(r => parseFloat_(r['fraud_risk_score'] || r['RiskScore'] || 0));
    const avgRiskScore = riskScores.length > 0 
      ? (riskScores.reduce((a, b) => a + b, 0) / riskScores.length * 100).toFixed(1)
      : '0.0';
    const highRiskCount = riskLevelData.highCount;

    return {
      fraudRateData,
      documentTypeData,
      riskLevelData,
      riskTrends,
      fraudContributionData,
      topHighRiskEntities,
      metrics: {
        totalDocuments,
        avgRiskScore,
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

  const fetchDocumentsList = async (dateFilter = null, documentType = null) => {
    setLoadingDocumentsList(true);
    setError(null);
    setCsvData(null);
    try {
      let url = '/api/documents/list';
      const params = [];
      if (dateFilter) params.push(`date_filter=${dateFilter}`);
      if (documentType) params.push(`document_type=${encodeURIComponent(documentType)}`);
      if (params.length > 0) {
        url += '?' + params.join('&');
      }

      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        const fetchedData = data.data || [];
        setAllDocumentsData(fetchedData);

        // Extract unique values for filters
        const uniqueTypes = [...new Set(fetchedData.map(d => d.document_type).filter(Boolean))].sort();

        setAvailableDocumentTypes(uniqueTypes);

        setDocumentsList(fetchedData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(dateFilter);
        setDocumentTypeFilter(documentType);

        if (fetchedData.length > 0) {
          loadDocumentsData(fetchedData);
        } else {
          setError('No documents found for the selected filters');
        }
      } else {
        setError(data.message || 'Failed to fetch documents');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to fetch documents from database');
      console.error('Error fetching documents:', err);
      setCsvData(null);
    } finally {
      setLoadingDocumentsList(false);
    }
  };

  const handleSearchDocuments = async (query) => {
    if (!query) {
      setDocumentTypeFilter(null);
      fetchDocumentsList(dateFilter);
      return;
    }
    setLoadingDocumentsList(true);
    setError(null);
    setCsvData(null);
    try {
      const response = await fetch(`/api/documents/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setDocumentsList(data.data);
        if (data.data && data.data.length > 0) {
          loadDocumentsData(data.data);
        } else {
          setError('No documents found matching your search');
        }
      } else {
        setError(data.message || 'Search failed');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to search documents');
      console.error('Error searching documents:', err);
      setCsvData(null);
    } finally {
      setLoadingDocumentsList(false);
    }
  };

  const loadDocumentsData = async (documents) => {
    if (!documents || documents.length === 0) {
      setError('No documents selected');
      return;
    }

    try {
      const rows = documents.map(doc => {
        const riskScore = parseFloat_(doc.fraud_risk_score || 0);
        let riskLevel = (doc.risk_level || '').trim();
        
        // Normalize risk level - handle "High Risk", "HIGH", "Critical", etc.
        if (riskLevel) {
          const normalized = riskLevel.toUpperCase().replace(/\s+/g, '');
          if (normalized.includes('HIGH') || normalized.includes('CRITICAL')) {
            riskLevel = 'HIGH';
          } else if (normalized.includes('MEDIUM')) {
            riskLevel = 'MEDIUM';
          } else if (normalized.includes('LOW')) {
            riskLevel = 'LOW';
          } else {
            riskLevel = null; // Will calculate from score
          }
        }
        
        // Calculate risk_level from fraud_risk_score if not set or couldn't normalize
        if (!riskLevel || riskLevel === 'UNKNOWN') {
          const riskScorePercent = riskScore * 100;
          if (riskScorePercent >= 70) {
            riskLevel = 'HIGH';
          } else if (riskScorePercent >= 35) {
            riskLevel = 'MEDIUM';
          } else {
            riskLevel = 'LOW';
          }
        }
        
        return {
          'fraud_risk_score': riskScore,
          'document_type': doc.document_type || 'Unknown',
          'risk_level': riskLevel,
          'status': doc.status || 'Unknown',
          'upload_date': doc.upload_date || '',
          'file_name': doc.file_name || '',
          'document_id': doc.document_id || '',
        };
      });

      const processed = processData(rows);
      setCsvData(processed);
      setError(null);
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(`Error processing documents: ${err.message}`);
    }
  };

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];


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

  // Render dedicated dashboard component if a specific document type is selected
  if (shouldRenderDedicatedDashboard) {
    const primary = colors.primaryColor || colors.accent?.red || '#E53935';
    const backButtonStyle = {
      backgroundColor: 'transparent',
      color: colors.foreground,
      border: `2px solid ${colors.border}`,
      padding: '0.75rem 1.5rem',
      borderRadius: '0.5rem',
      fontSize: '0.95rem',
      fontWeight: '600',
      cursor: 'pointer',
      marginBottom: '1.5rem',
      transition: 'all 0.3s',
    };

    if (normalizedDocumentType === 'check') {
      return (
        <div style={containerStyle}>
          <button
            style={backButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = colors.muted;
              e.target.style.borderColor = primary;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.borderColor = colors.border;
            }}
            onClick={() => {
              setDocumentTypeFilter(null);
              setCsvData(null);
              setError(null);
            }}
          >
            ← Back to Unified Dashboard
          </button>
          <CheckInsights />
        </div>
      );
    } else if (normalizedDocumentType === 'money_order') {
      return (
        <div style={containerStyle}>
          <button
            style={backButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = colors.muted;
              e.target.style.borderColor = primary;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.borderColor = colors.border;
            }}
            onClick={() => {
              setDocumentTypeFilter(null);
              setCsvData(null);
              setError(null);
            }}
          >
            ← Back to Unified Dashboard
          </button>
          <MoneyOrderInsights />
        </div>
      );
    } else if (normalizedDocumentType === 'paystub') {
      // Redirect to paystub insights page (similar to how money order and check work)
      navigate('/paystub-insights');
      return null;
    } else if (normalizedDocumentType === 'bank_statement') {
      return (
        <div style={containerStyle}>
          <button
            style={backButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = colors.muted;
              e.target.style.borderColor = primary;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = 'transparent';
              e.target.style.borderColor = colors.border;
            }}
            onClick={() => {
              setDocumentTypeFilter(null);
              setCsvData(null);
              setError(null);
            }}
          >
            ← Back to Unified Dashboard
          </button>
          <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
            Bank Statement Insights
          </h2>
          <div style={{ padding: '2rem', textAlign: 'center', color: colors.mutedForeground }}>
            Bank Statement Insights dashboard coming soon...
          </div>
        </div>
      );
    }
  }

  // Render unified dashboard for all document types or when no filter is selected
  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
          {inputMode === 'upload' ? 'Unified Document Insights Dashboard (CSV)' : 'Unified Document Insights Dashboard (Live Data)'}
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
            Upload CSV
          </button>
          <button
            onClick={() => {
              setInputMode('api');
              setCsvData(null);
              setError(null);
              setDocumentTypeFilter(null);
              setAllDocumentsData([]);
              setDateFilter(null);
              // Don't auto-fetch, let user click date filter or search
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
                    CSV file with document analysis data
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
                <p style={{ marginTop: '0.5rem', color: colors.mutedForeground }}>
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
                Search by File Name or Document ID:
              </label>
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  handleSearchDocuments(e.target.value);
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

            {/* Date Filter Section */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.75rem', fontWeight: '500' }}>
                Filter by Upload Date {totalRecords > 0 && <span style={{ color: colors.mutedForeground, fontWeight: '400', fontSize: '0.9rem' }}>({totalRecords} total records)</span>}
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem' }}>
                <button
                  onClick={() => fetchDocumentsList(null, documentTypeFilter)}
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
                >
                  All Records
                </button>
                <button
                  onClick={() => fetchDocumentsList('last_30', documentTypeFilter)}
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
                  onClick={() => fetchDocumentsList('last_60', documentTypeFilter)}
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
                  onClick={() => fetchDocumentsList('last_90', documentTypeFilter)}
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
                <button
                  onClick={() => fetchDocumentsList('older', documentTypeFilter)}
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
                >
                  Older
                </button>
              </div>
            </div>

            {/* Document Type Filter */}
            {availableDocumentTypes.length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
                  Filter by Document Type:
                </label>
                <select
                  value={documentTypeFilter || ''}
                  onChange={(e) => {
                    const selectedType = e.target.value || null;
                    fetchDocumentsList(dateFilter, selectedType);
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
                  <option value="">All Types</option>
                  {availableDocumentTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>
            )}



            {loadingDocumentsList ? (
              <div style={{ textAlign: 'center', padding: '2rem' }}>
                <FaCog className="spin" style={{ fontSize: '2rem', color: primary }} />
                <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>Loading documents...</p>
              </div>
            ) : documentsList.length > 0 ? (
              <div style={{
                backgroundColor: colors.secondary,
                borderRadius: '0.5rem',
                padding: '1rem',
                maxHeight: '400px',
                overflowY: 'auto',
              }}>
                <p style={{ color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
                  {documentsList.length} document{documentsList.length !== 1 ? 's' : ''} loaded
                </p>
              </div>
            ) : null}

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

      {/* Metrics Section */}
      {csvData && csvData.metrics && (
        <div style={cardStyle} data-metrics-section>
          <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>Summary Metrics</h2>
          <div style={metricsGridStyle}>
            <div style={metricCardStyle}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                {csvData.metrics.totalDocuments}
              </div>
              <div style={{ color: colors.mutedForeground }}>Total Documents</div>
            </div>
            <div style={metricCardStyle}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                {csvData.metrics.avgRiskScore}%
              </div>
              <div style={{ color: colors.mutedForeground }}>Average Risk Score</div>
            </div>
            <div style={metricCardStyle}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
                {csvData.metrics.highRiskCount}
              </div>
              <div style={{ color: colors.mutedForeground }}>High Risk Documents</div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Section */}
      {csvData && (
        <>
          {/* Fraud Rate by Document Type */}
          {csvData.fraudRateData && csvData.fraudRateData.length > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Fraud Rate by Document Type</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={csvData.fraudRateData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="name" stroke={colors.mutedForeground} />
                  <YAxis stroke={colors.mutedForeground} label={{ value: 'Fraud Rate (%)', angle: -90, position: 'insideLeft', style: { fill: colors.foreground } }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.card,
                      border: `1px solid ${colors.border}`,
                      color: colors.foreground
                    }}
                    formatter={(value, name) => {
                      if (name === 'fraudRate') {
                        const item = csvData.fraudRateData.find(d => d.fraudRate === value);
                        return [`${value}%`, `Fraud Rate (${item?.fraudCount || 0} of ${item?.totalCount || 0} documents)`];
                      }
                      return [value, name];
                    }}
                  />
                  <Bar dataKey="fraudRate" fill={primary}>
                    <LabelList 
                      dataKey="fraudRate" 
                      position="top" 
                      formatter={(value) => `${value}%`}
                      fill={colors.foreground}
                      style={{ fontSize: '12px', fontWeight: '600' }}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Risk Level Distribution */}
          {csvData.riskLevelData && csvData.riskLevelData.totalRecords > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Risk Level Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={[{
                    name: 'Risk Distribution',
                    LOW: parseFloat(csvData.riskLevelData.lowPercent),
                    MEDIUM: parseFloat(csvData.riskLevelData.mediumPercent),
                    HIGH: parseFloat(csvData.riskLevelData.highPercent)
                  }]}
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis 
                    type="number" 
                    domain={[0, 100]}
                    stroke={colors.mutedForeground}
                    label={{ value: 'Percentage (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                  />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    stroke={colors.mutedForeground}
                    width={150}
                    tick={{ fill: colors.foreground }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.card,
                      border: `1px solid ${colors.border}`,
                      color: colors.foreground
                    }}
                    formatter={(value, name) => {
                      const label = name === 'LOW' ? 'LOW' : name === 'MEDIUM' ? 'MEDIUM' : 'HIGH';
                      return [`${value.toFixed(1)}%`, label];
                    }}
                  />
                  <Bar dataKey="LOW" stackId="a" fill="#34a853" name={`LOW ${csvData.riskLevelData.lowPercent}%`}>
                    <LabelList 
                      dataKey="LOW" 
                      position="insideLeft" 
                      formatter={(value) => `LOW ${value.toFixed(1)}%`}
                      fill={colors.foreground}
                      style={{ fontSize: '12px', fontWeight: '600' }}
                    />
                  </Bar>
                  <Bar dataKey="MEDIUM" stackId="a" fill="#f4b400" name={`MEDIUM ${csvData.riskLevelData.mediumPercent}%`}>
                    <LabelList 
                      dataKey="MEDIUM" 
                      position="inside" 
                      formatter={(value) => `MEDIUM ${value.toFixed(1)}%`}
                      fill={colors.foreground}
                      style={{ fontSize: '12px', fontWeight: '600' }}
                    />
                  </Bar>
                  <Bar dataKey="HIGH" stackId="a" fill="#e53935" name={`HIGH ${csvData.riskLevelData.highPercent}%`}>
                    <LabelList 
                      dataKey="HIGH" 
                      position="insideRight" 
                      formatter={(value) => `HIGH ${value.toFixed(1)}%`}
                      fill={colors.foreground}
                      style={{ fontSize: '12px', fontWeight: '600' }}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}


          {/* Risk Score Trends */}
          {csvData.riskTrends && csvData.riskTrends.length > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Risk Score Trends Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={csvData.riskTrends}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="date" stroke={colors.mutedForeground} />
                  <YAxis stroke={colors.mutedForeground} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.card,
                      border: `1px solid ${colors.border}`,
                      color: colors.foreground
                    }}
                  />
                  <Area type="monotone" dataKey="avgRisk" stroke={primary} fill={primary} fillOpacity={0.6} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Fraud Contribution by Document Type (%) */}
          {csvData.fraudContributionData && csvData.fraudContributionData.length > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Fraud Contribution by Document Type (%)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={csvData.fraudContributionData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.percent}%`}
                    outerRadius={100}
                    innerRadius={40}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {csvData.fraudContributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.card,
                      border: `1px solid ${colors.border}`,
                      color: colors.foreground
                    }}
                    formatter={(value, name, props) => {
                      const percent = props.payload.percent;
                      return [`${value} high-risk documents (${percent}%)`, props.payload.name];
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top High-Risk Entities */}
          {csvData.topHighRiskEntities && csvData.topHighRiskEntities.length > 0 && (
            <div style={chartContainerStyle}>
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>Top High-Risk Entities</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={csvData.topHighRiskEntities} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
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
                      if (name === 'highRiskCount') {
                        const item = csvData.topHighRiskEntities.find(e => e.highRiskCount === value);
                        return [`${value} high-risk documents`, `Avg Risk: ${item?.avgRisk}% | Total: ${item?.totalCount}`];
                      }
                      return [value, name];
                    }}
                    labelFormatter={(label) => `Entity: ${label}`}
                  />
                  <Bar dataKey="highRiskCount" fill={primary}>
                    <LabelList 
                      dataKey="highRiskCount" 
                      position="right" 
                      formatter={(value) => `${value}`}
                      fill={colors.foreground}
                      style={{ fontSize: '11px', fontWeight: '600' }}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

        </>
      )}
    </div>
  );
};

export default AllDocumentsInsights;

