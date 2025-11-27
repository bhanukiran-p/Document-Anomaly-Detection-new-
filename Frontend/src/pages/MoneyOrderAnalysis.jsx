import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeMoneyOrder } from '../services/api';
import { colors } from '../styles/colors';
import { FaExclamationTriangle, FaMoneyBillWave, FaCog } from 'react-icons/fa';

const buildMoneyOrderSections = (data) => ({
  'Money Order Details': [
    { label: 'Issuer', value: data.issuer || 'N/A' },
    { label: 'Serial Number', value: data.serial_number || data.money_order_number || 'N/A' },
    { label: 'Amount', value: data.amount || 'N/A' },
    { label: 'Amount in Words', value: data.amount_in_words || 'N/A' },
    { label: 'Date', value: data.date || 'N/A' },
  ],
  'Parties & Verification': [
    { label: 'Purchaser', value: data.purchaser || 'N/A' },
    { label: 'Payee', value: data.payee || 'N/A' },
    { label: 'Signature', value: data.signature ? 'Present' : 'Missing' },
    { label: 'Receipt Number', value: data.receipt_number || 'N/A' },
  ],
  Location: [
    { label: 'Location', value: data.location || 'N/A' },
    { label: 'Address', value: data.address || 'N/A' },
    { label: 'City', value: data.city || 'N/A' },
    { label: 'State', value: data.state || 'N/A' },
    { label: 'ZIP Code', value: data.zip_code || 'N/A' },
  ],
});

const normalizeValue = (value) => (typeof value === 'string' ? value.trim() : value);

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

const buildCriticalFactors = (data = {}, anomalies = []) => {
  const factors = [];
  const addFactor = (text) => {
    if (text && !factors.includes(text)) {
      factors.push(text);
    }
  };

  const anomalyText = Array.isArray(anomalies) ? anomalies.join(' | ').toLowerCase() : '';
  const signatureText = normalizeValue(data.signature);

  if (isMissing(signatureText) || anomalyText.includes('missing signature')) {
    addFactor('Signature line is blank — authorization unavailable.');
  }

  if (isMissing(data.serial_number) && isMissing(data.money_order_number)) {
    addFactor('Serial / control number missing — cannot trace the money order.');
  }

  if (isMissing(data.amount_in_words) || anomalyText.includes('amount mismatch')) {
    addFactor('Amount in words missing or conflicts with numeric amount.');
  }

  if (isMissing(data.payee)) {
    addFactor('Payee name missing — funds destination unclear.');
  }

  if (isMissing(data.purchaser)) {
    addFactor('Purchaser/remitter missing — source party not verified.');
  }

  if ((isMissing(data.location) && isMissing(data.address)) || anomalyText.includes('invalid address')) {
    addFactor('Issuing location/address invalid or missing.');
  }

  if (isMissing(data.receipt_number)) {
    addFactor('Receipt reference absent — no purchase proof.');
  }

  if (anomalyText.includes('issuer-specific validation failed')) {
    addFactor('Issuer format validation failed — layout doesn’t match genuine templates.');
  }

  if (anomalyText.includes('missing critical fields')) {
    addFactor('Multiple mandatory sections incomplete per ML rules.');
  }

  return factors;
};

const MoneyOrderAnalysis = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  const toPercent = (value) => {
    if (value === null || value === undefined) return 0;
    const num = Number(value);
    if (!Number.isFinite(num)) return 0;
    const percent = num <= 1 ? num * 100 : num;
    return Math.max(0, Math.min(100, percent));
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
      setError('Please upload a money order image first');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await analyzeMoneyOrder(file);
      console.log('✅ Money order analysis response received:', response);
      console.log('Response success:', response.success);
      console.log('Response has data:', !!response.data);

      if (response.success === false) {
        console.log('❌ Analysis failed - showing error');
        setError(response.error || response.message || 'Failed to analyze money order. Please try again.');
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
      console.error('❌ Money order analysis error caught:', err);
      const errorMessage = err.error || err.message || err.response?.data?.error || err.response?.data?.message || 'Failed to analyze money order. Please try again.';
      setError(errorMessage);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = async () => {
    if (!results || !results.analysis_id) {
      const payload = results
        ? { ...results, extracted_sections: buildMoneyOrderSections(analysisData) }
        : results;
      const dataStr = JSON.stringify(payload, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `money_order_analysis_${new Date().getTime()}.json`;
      link.click();
      return;
    }

    // Download complete JSON from server
    try {
      const response = await fetch(`http://localhost:5001/api/analysis/download/${results.analysis_id}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${results.analysis_id}.json`;
        link.click();
      } else {
        const payload = { ...results, extracted_sections: buildMoneyOrderSections(analysisData) };
        const dataStr = JSON.stringify(payload, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `money_order_analysis_${new Date().getTime()}.json`;
        link.click();
      }
    } catch (err) {
      console.error('Download error:', err);
      const payload = { ...results, extracted_sections: buildMoneyOrderSections(analysisData) };
      const dataStr = JSON.stringify(payload, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `money_order_analysis_${new Date().getTime()}.json`;
      link.click();
    }
  };

  const downloadCSV = () => {
    if (!analysisData) return;

    // CSV Headers
    const headers = [
      'Document Type',
      'Timestamp',
      'Issuer',
      'Serial Number',
      'Amount',
      'Date',
      'Payee',
      'Purchaser',
      'Location',
      'City',
      'State',
      'ZIP Code',
      'Fraud Risk Score (%)',
      'Risk Level',
      'Model Confidence (%)',
      'AI Recommendation',
      'AI Confidence (%)',
      'Signature Status',
      'Anomaly Count',
      'Top Anomalies'
    ];

    // Filter anomalies to exclude AI recommendations and scores
    const filteredAnomalies = (analysisData.anomalies || []).filter(anomaly => {
      const anomalyLower = String(anomaly).toLowerCase();
      return !anomalyLower.includes('ai recommendation') &&
             !anomalyLower.includes('high fraud risk detected') &&
             !anomalyLower.includes('risk score');
    });

    // CSV Row
    const row = [
      'Money Order',
      analysisData.timestamp || new Date().toISOString(),
      analysisData.issuer || 'N/A',
      analysisData.serial_number || analysisData.money_order_number || 'N/A',
      analysisData.amount || 'N/A',
      analysisData.date || 'N/A',
      analysisData.payee || 'N/A',
      analysisData.purchaser || 'N/A',
      analysisData.location || analysisData.address || 'N/A',
      analysisData.city || 'N/A',
      analysisData.state || 'N/A',
      analysisData.zip_code || 'N/A',
      ((analysisData.fraud_risk_score || 0) * 100).toFixed(2),
      analysisData.risk_level || 'UNKNOWN',
      ((analysisData.model_confidence || 0) * 100).toFixed(2),
      analysisData.ai_recommendation || 'UNKNOWN',
      ((analysisData.ai_confidence || 0) * 100).toFixed(2),
      analysisData.signature || 'N/A',
      filteredAnomalies.length,
      filteredAnomalies.slice(0, 3).join(' | ')
    ];

    // Escape CSV values (handle commas and quotes)
    const escapeCsvValue = (value) => {
      const stringValue = String(value);
      if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }
      return stringValue;
    };

    const csvContent = [
      headers.map(escapeCsvValue).join(','),
      row.map(escapeCsvValue).join(',')
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `money_order_analysis_${new Date().getTime()}.csv`;
    link.click();
  };

  // Styles matching landing page design system
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
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
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
    transition: 'all 0.3s',
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
    border: 'none',
  };

  const resultCardStyle = {
    backgroundColor: colors.secondary,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    borderLeft: `4px solid ${primary}`,
    marginBottom: '1rem',
    border: `1px solid ${colors.border}`,
    color: colors.foreground,
  };

  const warningBannerStyle = {
    backgroundColor: `${primary}20`,
    border: `1px solid ${primary}`,
    borderRadius: '0.5rem',
    padding: '1rem',
    marginBottom: '1rem',
  };

  const infoCardStyle = {
    backgroundColor: colors.card,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    marginBottom: '1rem',
    color: colors.foreground,
  };

  // Get the data from response (could be results.data or results directly)
  const analysisData = results?.data || results;
  const mlAnalysis = analysisData?.ml_analysis || analysisData?.ml_fraud_analysis || {};
  const aiAnalysis = analysisData?.ai_analysis || {};
  const criticalFactors = analysisData ? buildCriticalFactors(analysisData, analysisData?.anomalies || []) : [];

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
          Money Order <span style={{ color: primary }}>Analysis</span>
        </h1>
        <p style={{ color: colors.mutedForeground }}>Analyze money orders for fraud and anomaly detection</p>
      </div>

      <div style={gridStyle}>
        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: colors.foreground, marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
            Upload Money Order Image
          </h2>

          <div style={warningBannerStyle}>
            <div style={{ color: primary, fontSize: '0.875rem', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaExclamationTriangle />
              <span>Only upload money order documents (Western Union, MoneyGram, USPS, etc.)</span>
            </div>
          </div>

          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <FaMoneyBillWave style={{ fontSize: '3rem', marginBottom: '1rem', color: colors.foreground }} />
            {isDragActive ? (
              <p style={{ color: primary, fontWeight: '500' }}>
                Drop the money order image here...
              </p>
            ) : (
              <div>
                <p style={{ color: colors.foreground, marginBottom: '0.5rem' }}>
                  Drop your money order image here or click to browse
                </p>
                <p style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
                  Money Orders Only - JPG, JPEG, PNG, PDF
                </p>
              </div>
            )}
          </div>

          {file && (
            <div style={{ marginTop: '1.5rem' }}>
              <div style={{
                backgroundColor: colors.secondary,
                padding: '1rem',
                borderRadius: '0.5rem',
                border: `1px solid ${colors.border}`,
                color: colors.foreground,
              }}>
                <strong>File:</strong> {file.name}<br />
                <strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB<br />
                <strong>Type:</strong> {file.type || 'Unknown'}
              </div>

              {preview && (
                <div style={{ marginTop: '1rem' }}>
                  <img
                    src={preview}
                    alt="Money order preview"
                    style={{
                      width: '100%',
                      borderRadius: '0.5rem',
                      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
                      border: `1px solid ${colors.border}`,
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
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = `0 6px 30px ${primary}60`;
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = `0 0 20px ${primary}40`;
              }
            }}
          >
            {loading ? 'Analyzing...' : 'Analyze Money Order'}
          </button>

          {error && (
            <div style={{
              backgroundColor: `${colors.destructive}20`,
              color: colors.destructive,
              padding: '1rem',
              borderRadius: '0.5rem',
              marginTop: '1rem',
              fontWeight: '500',
              border: `1px solid ${colors.destructive}`,
            }}>
              {error}
            </div>
          )}
        </div>

        {/* Results Section */}
        <div style={cardStyle}>
          <h2 style={{ color: colors.foreground, marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
            Analysis Results
          </h2>

          {!results && !loading && (
            <div style={{
              backgroundColor: colors.secondary,
              padding: '2rem',
              borderRadius: '0.5rem',
              textAlign: 'center',
              color: colors.mutedForeground,
              border: `1px solid ${colors.border}`,
            }}>
              <p>Upload a money order image on the left to begin analysis</p>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <FaCog className="spin" style={{
                fontSize: '3rem',
                color: primary,
              }} />
              <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>
                Analyzing money order...
              </p>
            </div>
          )}

          {/* Display Results */}
          {results && analysisData && (
            <div className="fade-in">
              {(() => {
                const fraudRiskPercent = toPercent(
                  analysisData.fraud_risk_score ?? mlAnalysis?.fraud_risk_score
                );
                const modelConfidencePercent = toPercent(
                  analysisData.model_confidence ?? mlAnalysis?.model_confidence
                );
                const aiConfidencePercent = toPercent(
                  analysisData.ai_confidence ?? aiAnalysis?.confidence
                );
                const aiRecommendation = (analysisData.ai_recommendation ||
                  aiAnalysis.recommendation ||
                  'UNKNOWN').toUpperCase();
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
                      marginBottom: '1.5rem',
                      backgroundColor: `${primary}20`,
                      borderLeft: `4px solid ${primary}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                        Fraud Risk Score
                      </div>
                      <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: primary }}>
                        {fraudRiskPercent.toFixed(1)}%
                      </div>
                      {mlAnalysis?.risk_level && (
                        <div style={{ marginTop: '0.25rem', color: colors.mutedForeground }}>
                          Risk Level: <strong>{mlAnalysis.risk_level}</strong>
                        </div>
                      )}
                    </div>

                    {/* Model Confidence Card */}
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: '1.5rem',
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

              {Array.isArray(analysisData.anomalies) && analysisData.anomalies.length > 0 && (
                <div style={{
                  ...infoCardStyle,
                  marginTop: '1rem',
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
                    {analysisData.anomalies.map((anomaly, idx) => (
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
                  marginTop: '1rem',
                  backgroundColor: `${primary}10`,
                  borderLeft: `4px solid ${primary}`,
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
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="12" y1="8" x2="12" y2="13"/>
                      <line x1="12" y1="16" x2="12.01" y2="16"/>
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

              {/* AI Analysis Details */}
              {(aiAnalysis.summary || aiAnalysis.reasoning || (Array.isArray(aiAnalysis.key_indicators) && aiAnalysis.key_indicators.length) || aiAnalysis.verification_notes) && (
                <div style={{
                  ...infoCardStyle,
                  marginTop: '1rem',
                }}>
                  <h4 style={{ color: colors.foreground, marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/>
                      <path d="M12 6v6l4 2"/>
                    </svg>
                    AI Analysis Details
                  </h4>

                  {aiAnalysis.summary && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Summary:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem' }}>{aiAnalysis.summary}</p>
                    </div>
                  )}
                  {aiAnalysis.reasoning && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Reasoning:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>{aiAnalysis.reasoning}</p>
                    </div>
                  )}
                  {Array.isArray(aiAnalysis.key_indicators) && aiAnalysis.key_indicators.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Key Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {aiAnalysis.key_indicators.map((indicator, idx) => (
                          <li key={idx} style={{ marginBottom: '0.3rem' }}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {aiAnalysis.verification_notes && (
                    <div>
                      <strong>Verification Notes:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
                        {aiAnalysis.verification_notes}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* ML Analysis */}
              {(mlAnalysis.risk_level || (Array.isArray(mlAnalysis.feature_importance) && mlAnalysis.feature_importance.length) || mlAnalysis.model_scores) && (
                <div style={{
                  ...infoCardStyle,
                  marginTop: '1rem',
                }}>
                  <h4 style={{ color: colors.foreground, marginBottom: '1rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 3v18h18"/>
                      <path d="M18 17V9"/>
                      <path d="M13 17V5"/>
                      <path d="M8 17v-3"/>
                    </svg>
                    ML Risk Analysis
                  </h4>

                  {mlAnalysis.risk_level && (
                    <p style={{ marginBottom: '0.75rem' }}>
                      <strong>Risk Level:</strong>{' '}
                      <span style={{
                        color: ['HIGH', 'CRITICAL'].includes(mlAnalysis.risk_level) ? primary : colors.status.success,
                        fontWeight: 'bold',
                      }}>
                        {mlAnalysis.risk_level}
                      </span>
                    </p>
                  )}

                  {Array.isArray(mlAnalysis.feature_importance) && mlAnalysis.feature_importance.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Top Risk Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {mlAnalysis.feature_importance.slice(0, 5).map((item, idx) => {
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

                  {mlAnalysis.model_scores && (
                    <div style={{ fontSize: '0.85rem', color: colors.mutedForeground }}>
                      <strong>Analysis Scores:</strong>
                      {mlAnalysis.model_scores.random_forest !== undefined && (
                        <div>Random Forest: {(mlAnalysis.model_scores.random_forest * 100).toFixed(1)}%</div>
                      )}
                      {mlAnalysis.model_scores.xgboost !== undefined && (
                        <div>XGBoost: {(mlAnalysis.model_scores.xgboost * 100).toFixed(1)}%</div>
                      )}
                      {mlAnalysis.model_scores.ensemble !== undefined && (
                        <div>Ensemble: {(mlAnalysis.model_scores.ensemble * 100).toFixed(1)}%</div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div style={{
                ...infoCardStyle,
                backgroundColor: colors.card,
                border: `1px solid ${colors.border}`
              }}>
                <p style={{ margin: 0 }}>
                  Full money order details (issuer, parties, location, etc.) are included in the downloaded JSON file as tabular sections.
                </p>
              </div>

              {/* Download Buttons */}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  style={{
                    ...buttonStyle,
                    backgroundColor: colors.card,
                    color: colors.foreground,
                    border: `2px solid ${colors.border}`,
                    marginTop: 0,
                    flex: 1,
                  }}
                  onClick={downloadJSON}
                  onMouseEnter={(e) => {
                    e.target.style.borderColor = primary;
                    e.target.style.backgroundColor = colors.muted;
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.borderColor = colors.border;
                    e.target.style.backgroundColor = colors.card;
                  }}
                >
                  Download JSON
                </button>
                <button
                  style={{
                    ...buttonStyle,
                    backgroundColor: primary,
                    color: colors.primaryForeground,
                    border: `2px solid ${primary}`,
                    marginTop: 0,
                    flex: 1,
                  }}
                  onClick={downloadCSV}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = colors.accent.redDark;
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = primary;
                  }}
                >
                  Download CSV (Dashboard)
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MoneyOrderAnalysis;
  const emphasizeAnomaly = (text) => {
    if (!text) return text;
    const lower = text.toLowerCase();
    const highlightKeywords = ['missing', 'invalid', 'mismatch', 'critical'];
    const shouldEmphasize = highlightKeywords.some((keyword) => lower.includes(keyword));
    return shouldEmphasize ? <strong>{text}</strong> : text;
  };
