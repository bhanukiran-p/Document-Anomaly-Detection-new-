import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzePaystub } from '../services/api';
import { colors } from '../styles/colors';
import { FaExclamationTriangle, FaMoneyCheckAlt, FaCog } from 'react-icons/fa';

const buildPaystubSections = (data) => ({
  'Company & Employee Information': [
    { label: 'Company', value: data.company_name || 'N/A' },
    { label: 'Employee', value: data.employee_name || 'N/A' },
    { label: 'Employee ID', value: data.employee_id || 'N/A' },
  ],
  'Pay Period Information': [
    { label: 'Pay Period Start', value: data.pay_period_start || 'N/A' },
    { label: 'Pay Period End', value: data.pay_period_end || 'N/A' },
    { label: 'Pay Date', value: data.pay_date || 'N/A' },
  ],
  Earnings: [
    { label: 'Gross Pay', value: data.gross_pay || 'N/A' },
    { label: 'Net Pay', value: data.net_pay || 'N/A' },
    { label: 'YTD Gross', value: data.ytd_gross || 'N/A' },
    { label: 'YTD Net', value: data.ytd_net || 'N/A' },
  ],
  'Tax Withholdings': [
    { label: 'Federal Tax', value: data.federal_tax || 'N/A' },
    { label: 'State Tax', value: data.state_tax || 'N/A' },
    { label: 'Social Security', value: data.social_security || 'N/A' },
    { label: 'Medicare', value: data.medicare || 'N/A' },
  ],
});

const isMissing = (value) => {
  if (value === undefined || value === null) return true;
  if (typeof value === 'number') return false;
  const normalized = String(value).trim().toLowerCase();
  return (
    !normalized ||
    normalized === 'n/a' ||
    normalized === 'na' ||
    normalized === 'none' ||
    normalized === 'unknown' ||
    normalized === 'missing'
  );
};

const buildPaystubCriticalFactors = (data = {}, anomalies = []) => {
  const factors = [];
  const addFactor = (text) => {
    if (text && !factors.includes(text)) {
      factors.push(text);
    }
  };

  const anomalyText = Array.isArray(anomalies) ? anomalies.join(' | ').toLowerCase() : '';

  if (isMissing(data.company_name)) {
    addFactor('Employer name missing — payroll origin cannot be verified.');
  }

  if (isMissing(data.employee_name)) {
    addFactor('Employee name missing — payee identity unclear.');
  }

  if (isMissing(data.pay_period_start) || isMissing(data.pay_period_end)) {
    addFactor('Pay period range incomplete — earnings window cannot be confirmed.');
  }

  if (isMissing(data.pay_date)) {
    addFactor('Pay date absent — deposit timing unknown.');
  }

  if (isMissing(data.gross_pay) || isMissing(data.net_pay)) {
    addFactor('Gross or net pay missing — total compensation unverifiable.');
  }

  if (isMissing(data.ytd_gross) || isMissing(data.ytd_net)) {
    addFactor('Year-to-date totals missing — cumulative payroll history unavailable.');
  }

  if (
    isMissing(data.federal_tax) &&
    isMissing(data.state_tax) &&
    isMissing(data.social_security) &&
    isMissing(data.medicare)
  ) {
    addFactor('Withholding section empty — taxes and deductions not documented.');
  }

  if (anomalyText.includes('invalid date')) {
    addFactor('Date formatting invalid — pay period timeline flagged.');
  }

  if (anomalyText.includes('amount mismatch')) {
    addFactor('Earnings totals do not reconcile with deductions per ML review.');
  }

  if (anomalyText.includes('missing critical fields')) {
    addFactor('ML model flagged multiple mandatory paystub sections as missing.');
  }

  return factors;
};

const PaystubAnalysis = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const toPercent = (value) => {
    if (value === null || value === undefined) return 0;
    const num = Number(value);
    if (!Number.isFinite(num)) return 0;
    const percent = num <= 1 ? num * 100 : num;
    return Math.max(0, Math.min(100, percent));
  };

  const emphasizeAnomaly = (text) => {
    if (!text) return text;
    const lower = text.toLowerCase();
    const highlightKeywords = ['missing', 'invalid', 'mismatch', 'critical'];
    const shouldEmphasize = highlightKeywords.some((keyword) => lower.includes(keyword));
    return shouldEmphasize ? <strong>{text}</strong> : text;
  };
  
  const onDrop = useCallback((acceptedFiles) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResults(null);
      
      // Create preview for images
      if (selectedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = () => setPreview(reader.result);
        reader.readAsDataURL(selectedFile);
      } else {
        setPreview(null);
      }
    }
  }, []);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  });
  
  const handleAnalyze = async () => {
    if (!file) {
      setError('Please upload a paystub first');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await analyzePaystub(file);
      console.log('✅ Paystub analysis response received:', response);
      console.log('Response success:', response.success);
      console.log('Response has data:', !!response.data);

      if (response.success === false) {
        console.log('❌ Analysis failed - showing error');
        setError(response.error || response.message || 'Failed to analyze paystub. Please try again.');
        setResults(null);
      } else if (response.success === true && response.data) {
        console.log('✅ Analysis successful - displaying results');
        setResults(response.data);
        setError(null);
      } else {
        console.log('⚠️ Unexpected response format:', response);
        setError('Received unexpected response format from server');
        setResults(null);
      }
    } catch (err) {
      console.error('❌ Paystub analysis error caught:', err);
      const errorMessage = err.error || err.message || err.response?.data?.error || err.response?.data?.message || 'Failed to analyze paystub. Please try again.';
      setError(errorMessage);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };
  
  const downloadJSON = () => {
    const payload = results
      ? { ...results, extracted_sections: buildPaystubSections(results) }
      : results;
    const dataStr = JSON.stringify(payload, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `paystub_analysis_${new Date().getTime()}.json`;
    link.click();
  };

  const downloadCSV = () => {
    if (!results) return;

    // Filter anomalies to exclude AI recommendations and risk scores
    const filteredAnomalies = (results.anomalies || []).filter(anomaly => {
      const anomalyLower = String(anomaly).toLowerCase();
      return !anomalyLower.includes('ai recommendation') &&
             !anomalyLower.includes('high fraud risk detected') &&
             !anomalyLower.includes('risk score');
    });

    const fraudRiskPercent = toPercent(results.fraud_risk_score ?? results.ml_analysis?.fraud_risk_score);
    const modelConfidencePercent = toPercent(results.model_confidence ?? results.ml_analysis?.model_confidence);
    const aiConfidencePercent = toPercent(results.ai_confidence ?? results.ai_analysis?.confidence);
    const riskLevel = (results.risk_level || results.ml_analysis?.risk_level || 'UNKNOWN').toString().toUpperCase();
    const aiRecommendation = (results.ai_recommendation || results.ai_analysis?.recommendation || 'UNKNOWN').toString().toUpperCase();

    // Helper to escape CSV values
    const escapeCSV = (value) => {
      if (value === null || value === undefined) return '';
      const str = String(value);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };

    // CSV Headers
    const headers = [
      'Document Type',
      'Timestamp',
      'Company Name',
      'Employee Name',
      'Employee ID',
      'Pay Period Start',
      'Pay Period End',
      'Pay Date',
      'Gross Pay',
      'Net Pay',
      'YTD Gross',
      'YTD Net',
      'Federal Tax',
      'State Tax',
      'Social Security',
      'Medicare',
      'Fraud Risk Score (%)',
      'Risk Level',
      'Model Confidence (%)',
      'AI Recommendation',
      'AI Confidence (%)',
      'Anomaly Count',
      'Top Anomalies'
    ];

    // CSV Data
    const row = [
      'Paystub',
      results.timestamp || new Date().toISOString(),
      results.company_name || 'N/A',
      results.employee_name || 'N/A',
      results.employee_id || 'N/A',
      results.pay_period_start || 'N/A',
      results.pay_period_end || 'N/A',
      results.pay_date || 'N/A',
      results.gross_pay || 'N/A',
      results.net_pay || 'N/A',
      results.ytd_gross || 'N/A',
      results.ytd_net || 'N/A',
      results.federal_tax || 'N/A',
      results.state_tax || 'N/A',
      results.social_security || 'N/A',
      results.medicare || 'N/A',
      fraudRiskPercent.toFixed(1),
      riskLevel,
      modelConfidencePercent.toFixed(1),
      aiRecommendation,
      aiConfidencePercent.toFixed(1),
      filteredAnomalies.length,
      filteredAnomalies.slice(0, 3).join(' | ')
    ];

    const csvContent = [
      headers.map(escapeCSV).join(','),
      row.map(escapeCSV).join(',')
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `paystub_analysis_${new Date().getTime()}.csv`;
    link.click();
  };
  
  // Styles
  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  
  const containerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    backgroundColor: colors.background,
    minHeight: '100vh',
    color: colors.foreground,
    padding: '1.5rem',
  };
  
  const headerStyle = {
    background: 'linear-gradient(135deg, #0f1820 0%, #1a2332 100%)',
    padding: '2rem',
    borderRadius: '0.75rem',
    color: colors.foreground,
    textAlign: 'center',
    marginBottom: '2rem',
    border: `1px solid ${colors.border}`,
  };
  
  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
    gap: '2rem',
  };
  
  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem',
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
  
  const buttonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '1rem 2rem',
    borderRadius: '50px',
    fontSize: '1rem',
    fontWeight: '600',
    width: '100%',
    marginTop: '1rem',
    cursor: loading ? 'not-allowed' : 'pointer',
    opacity: loading ? 0.6 : 1,
    boxShadow: `0 0 20px ${primary}40`,
    transition: 'all 0.3s',
  };
  
  const resultCardStyle = {
    backgroundColor: colors.secondary,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    borderLeft: `4px solid ${primary}`,
    marginBottom: '1rem',
    border: `1px solid ${colors.border}`,
  };
  
  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginTop: '1rem',
  };
  
  const metricStyle = {
    backgroundColor: colors.secondary,
    padding: '1rem',
    borderRadius: '0.5rem',
    textAlign: 'center',
    border: `1px solid ${colors.border}`,
  };
  
  const confidenceStyle = (confidence) => {
    let bgColor = colors.accent.redLight;
    let textColor = colors.accent.red;
    
    if (confidence >= 70) {
      bgColor = colors.status.successLight;
      textColor = colors.status.success;
    } else if (confidence >= 50) {
      bgColor = colors.status.warningLight;
      textColor = colors.status.warning;
    }
    
    return {
      backgroundColor: bgColor,
      color: textColor,
      padding: '0.75rem 1.5rem',
      borderRadius: '0.5rem',
      fontWeight: '600',
      fontSize: '1.1rem',
      marginBottom: '1.5rem',
      textAlign: 'center',
    };
  };
  
  const infoCardStyle = {
    backgroundColor: colors.card,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    marginBottom: '1rem',
    color: colors.foreground,
  };

  const criticalFactors = results ? buildPaystubCriticalFactors(results, results?.anomalies || []) : [];

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
          Paystub <span style={{ color: primary }}>Analysis</span>
        </h1>
        <p>Analyze paystubs for payroll verification</p>
      </div>
      
      <div style={gridStyle}>
        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
            Upload Paystub Document
          </h2>
          
          <div style={{
            backgroundColor: '#FFF3CD',
            border: '1px solid #FFC107',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1rem',
          }}>
            <div style={{ color: '#856404', fontSize: '0.875rem', margin: 0, fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaExclamationTriangle />
              <span>Only upload paystub documents (payslips or salary statements)</span>
            </div>
          </div>
          
          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <FaMoneyCheckAlt style={{ fontSize: '3rem', marginBottom: '1rem', color: colors.foreground }} />
            {isDragActive ? (
              <p style={{ color: primary, fontWeight: '500' }}>
                Drop the paystub here...
              </p>
            ) : (
              <div>
                <p style={{ color: colors.foreground, marginBottom: '0.5rem' }}>
                  Drop your paystub here or click to browse
                </p>
                <p style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
                  Paystubs Only - JPG, JPEG, PNG, PDF
                </p>
              </div>
            )}
          </div>
          
          {file && (
            <div style={{ marginTop: '1.5rem' }}>
              <div style={{
                backgroundColor: colors.muted,
                padding: '1rem',
                borderRadius: '8px',
              }}>
                <strong>File:</strong> {file.name}<br />
                <strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB<br />
                <strong>Type:</strong> {file.type || 'Unknown'}
              </div>
              
              {preview && (
                <div style={{ marginTop: '1rem' }}>
                  <img 
                    src={preview} 
                    alt="Paystub preview" 
                    style={{ 
                      width: '100%', 
                      borderRadius: '8px',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                    }} 
                  />
                </div>
              )}
            </div>
          )}
          
          <button 
            style={buttonStyle}
            onClick={handleAnalyze}
            disabled={loading || !file}
            onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = colors.accent.redDark)}
            onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = colors.accent.red)}
          >
            {loading ? 'Analyzing...' : 'Analyze Paystub'}
          </button>
          
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
        </div>
        
        {/* Results Section */}
        <div style={cardStyle}>
          <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
            Analysis Results
          </h2>
          
          {!results && !loading && (
            <div style={{
              backgroundColor: colors.muted,
              padding: '2rem',
              borderRadius: '8px',
              textAlign: 'center',
              color: colors.foreground,
            }}>
              <p>Upload a paystub on the left to begin analysis</p>
            </div>
          )}
          
          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <FaCog className="spin" style={{ fontSize: '3rem', color: primary }} />
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing paystub...
              </p>
            </div>
          )}
          
          {results && (
            <div className="fade-in">
              {(() => {
                const confidencePercent = toPercent(results.confidence_score);
                const fraudRiskPercent = toPercent(results.fraud_risk_score ?? results.ml_analysis?.fraud_risk_score);
                const modelConfidencePercent = toPercent(results.model_confidence ?? results.ml_analysis?.model_confidence);
                const aiConfidencePercent = toPercent(results.ai_confidence ?? results.ai_analysis?.confidence);
                const riskLevel = (results.risk_level || results.ml_analysis?.risk_level || 'UNKNOWN').toString().toUpperCase();
                const aiRecommendation = (results.ai_recommendation || results.ai_analysis?.recommendation || 'UNKNOWN').toString().toUpperCase();
                const aiColor = aiRecommendation === 'APPROVE'
                  ? colors.status.success
                  : aiRecommendation === 'REJECT'
                    ? primary
                    : colors.status.warning;

                return (
                  <>
                    {/* Fraud Risk Score Card */}
                    <div style={{
                      ...resultCardStyle,
                      marginTop: '1.25rem',
                      marginBottom: '1rem',
                      backgroundColor: `${primary}20`,
                      borderLeft: `4px solid ${primary}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                        Fraud Risk Score
                      </div>
                      <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: primary }}>
                        {fraudRiskPercent.toFixed(1)}%
                      </div>
                      <div style={{ marginTop: '0.25rem', color: colors.mutedForeground }}>
                        Risk Level: <strong>{riskLevel}</strong>
                      </div>
                    </div>

                    {/* Model Confidence Card */}
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: '1rem',
                      backgroundColor: `${colors.status.success}20`,
                      borderLeft: `4px solid ${colors.status.success}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                        Model Confidence
                      </div>
                      <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: colors.status.success }}>
                        {modelConfidencePercent.toFixed(1)}%
                      </div>
                    </div>

                    {/* AI Recommendation Card */}
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: '1.5rem',
                      backgroundColor: `${aiColor}20`,
                      borderLeft: `4px solid ${aiColor}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                        AI Recommendation
                      </div>
                      <div style={{ fontSize: '2rem', fontWeight: 'bold', color: aiColor }}>
                        {aiRecommendation}
                      </div>
                    </div>
                  </>
                );
              })()}

              {results.anomalies && results.anomalies.length > 0 && (
                <div style={{
                  ...resultCardStyle,
                  marginBottom: '1.5rem',
                  backgroundColor: `${colors.status.warning}10`,
                  borderLeft: `4px solid ${colors.status.warning}`,
                }}>
                  <h4 style={{ color: colors.foreground, marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                      <line x1="12" y1="9" x2="12" y2="13"/>
                      <line x1="12" y1="17" x2="12.01" y2="17"/>
                    </svg>
                    Detected Anomalies
                  </h4>
                  <ul style={{ color: colors.mutedForeground, paddingLeft: '1.5rem' }}>
                    {results.anomalies.map((anomaly, idx) => (
                      <li key={idx} style={{ marginBottom: '0.4rem' }}>
                        {emphasizeAnomaly(anomaly)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {criticalFactors.length > 0 && (
                <div style={{
                  ...infoCardStyle,
                  backgroundColor: `${primary}10`,
                  borderLeft: `4px solid ${primary}`,
                  marginTop: '-0.5rem',
                }}>
                  <h4 style={{
                    color: colors.foreground,
                    marginBottom: '0.75rem',
                    fontSize: '1.05rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="8" x2="12" y2="13" />
                      <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                    Key Missing / Risk Factors
                  </h4>
                  <ul style={{ color: colors.foreground, paddingLeft: '1.5rem', marginBottom: 0 }}>
                    {criticalFactors.map((factor, idx) => (
                      <li key={idx} style={{ marginBottom: '0.35rem' }}>
                        <strong>{factor}</strong>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {results.ai_analysis && (
                <div style={{
                  ...resultCardStyle,
                  marginBottom: '1.5rem',
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`,
                }}>
                  <h4 style={{ color: colors.foreground, marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/>
                      <path d="M12 6v6l4 2"/>
                    </svg>
                    Analysis Details
                  </h4>
                  {results.ai_analysis.summary && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Summary:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem' }}>
                        {results.ai_analysis.summary}
                      </p>
                    </div>
                  )}
                  {results.ai_analysis.reasoning && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Reasoning:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
                        {results.ai_analysis.reasoning}
                      </p>
                    </div>
                  )}
                  {Array.isArray(results.ai_analysis.key_indicators) && results.ai_analysis.key_indicators.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Key Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {results.ai_analysis.key_indicators.map((item, idx) => (
                          <li key={idx} style={{ marginBottom: '0.3rem' }}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {results.ai_analysis.verification_notes && (
                    <div>
                      <strong>Verification Notes:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
                        {results.ai_analysis.verification_notes}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {results.ml_analysis && (
                <div style={{
                  ...resultCardStyle,
                  marginBottom: '1.5rem',
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`,
                }}>
                  <h4 style={{ color: colors.foreground, marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 3v18h18"/>
                      <path d="M18 17V9"/>
                      <path d="M13 17V5"/>
                      <path d="M8 17v-3"/>
                    </svg>
                    Risk Analysis
                  </h4>
                  {results.ml_analysis.risk_level && (
                    <p style={{ marginBottom: '0.5rem' }}>
                      <strong>Risk Level:</strong>{' '}
                      <span style={{
                        color: ['HIGH', 'CRITICAL'].includes(results.ml_analysis.risk_level) ? primary : colors.status.success,
                        fontWeight: 'bold',
                      }}>
                        {results.ml_analysis.risk_level}
                      </span>
                    </p>
                  )}
                  {Array.isArray(results.ml_analysis.feature_importance) && results.ml_analysis.feature_importance.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Top Risk Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {results.ml_analysis.feature_importance.slice(0, 5).map((item, idx) => {
                          if (typeof item === 'string') {
                            return <li key={idx} style={{ marginBottom: '0.3rem' }}>{item}</li>;
                          }
                          if (item?.feature && item?.importance !== undefined) {
                            return (
                              <li key={idx} style={{ marginBottom: '0.3rem' }}>
                                {item.feature}: {(item.importance * 100).toFixed(1)}%
                              </li>
                            );
                          }
                          return null;
                        })}
                      </ul>
                    </div>
                  )}

                  {results.ml_analysis.model_scores && (
                    <div style={{ fontSize: '0.85rem', color: colors.mutedForeground }}>
                      <strong>Analysis Scores:</strong>
                      {results.ml_analysis.model_scores.random_forest !== undefined && (
                        <div>Primary Analysis: {(results.ml_analysis.model_scores.random_forest * 100).toFixed(1)}%</div>
                      )}
                      {results.ml_analysis.model_scores.xgboost !== undefined && (
                        <div>Secondary Analysis: {(results.ml_analysis.model_scores.xgboost * 100).toFixed(1)}%</div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div style={{
                ...resultCardStyle,
                backgroundColor: colors.card,
                border: `1px solid ${colors.border}`
              }}>
                <p style={{ margin: 0 }}>
                  Download results in JSON format for complete details or CSV format for dashboard/analytics integration.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  style={{
                    ...buttonStyle,
                    backgroundColor: primary,
                    marginTop: 0,
                  }}
                  onClick={downloadJSON}
                  onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
                  onMouseLeave={(e) => e.target.style.backgroundColor = primary}
                >
                  Download JSON
                </button>

                <button
                  style={{
                    ...buttonStyle,
                    backgroundColor: colors.status.success,
                    marginTop: 0,
                  }}
                  onClick={downloadCSV}
                  onMouseEnter={(e) => e.target.style.backgroundColor = colors.status.successDark || '#1b5e20'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = colors.status.success}
                >
                  Download CSV
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaystubAnalysis;
