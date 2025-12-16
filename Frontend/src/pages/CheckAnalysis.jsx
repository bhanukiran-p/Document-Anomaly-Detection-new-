import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeCheck } from '../services/api';
import { colors } from '../styles/colors';
import { FaExclamationTriangle, FaLandmark, FaCog } from 'react-icons/fa';
import CheckInsights from '../components/CheckInsights.jsx';

const buildCheckSections = (data) => ({
  'Bank Information': [
    { label: 'Bank Name', value: data.bank_name || 'N/A' },
    { label: 'Bank Type', value: data.bank_type || 'N/A' },
    { label: 'Country', value: data.country || 'N/A' },
  ],
  'Payment Information': [
    { label: 'Payee Name', value: data.payee_name || 'N/A' },
    { label: 'Amount', value: data.amount || 'N/A' },
    { label: 'Amount in Words', value: data.amount_words || 'N/A' },
    { label: 'Date', value: data.date || 'N/A' },
    { label: 'Memo', value: data.memo || 'N/A' },
  ],
  'Account & Check Details': [
    { label: 'Check Number', value: data.check_number || 'N/A' },
    { label: 'Account Number', value: data.account_number || 'N/A' },
    { label: 'Routing Number', value: data.routing_number || 'N/A' },
  ],
  'Verification': [
    { label: 'Signature Detected', value: data.signature_detected ? 'Yes' : 'No' },
    { label: 'Analysis Time', value: data.timestamp || 'N/A' },
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

const buildCheckCriticalFactors = (data = {}, anomalies = []) => {
  const factors = [];
  const addFactor = (text) => {
    if (text && !factors.includes(text)) {
      factors.push(text);
    }
  };

  const anomalyText = Array.isArray(anomalies) ? anomalies.join(' | ').toLowerCase() : '';

  if (!data.signature_detected || anomalyText.includes('missing signature')) {
    addFactor('Signature panel is blank or unreadable — cannot validate authorization.');
  }

  if (isMissing(data.amount_words) || anomalyText.includes('amount mismatch')) {
    addFactor('Written amount missing or mismatched with numeric figures.');
  }

  if (isMissing(data.payee_name)) {
    addFactor('Payee field is empty — destination of funds unclear.');
  }

  if (isMissing(data.date)) {
    addFactor('Issue date missing or invalid — stale‑date checks cannot be cleared.');
  }

  if (isMissing(data.routing_number)) {
    addFactor('Routing number unreadable — bank cannot locate issuing institution.');
  }

  if (isMissing(data.account_number)) {
    addFactor('Account number missing — cannot debit the originating account.');
  }

  if (isMissing(data.check_number)) {
    addFactor('Check number absent — sequence tracking failed.');
  }

  if (anomalyText.includes('missing critical fields')) {
    addFactor('Multiple required sections flagged by ML as incomplete.');
  }

  return factors;
};

const CheckAnalysis = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('analyze');
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
      setError('Please upload a check image first');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await analyzeCheck(file);
      console.log('✅ Check analysis response received:', response);
      console.log('Response success:', response.success);
      console.log('Response has data:', !!response.data);

      if (response.success === false) {
        console.log('❌ Analysis failed - showing error');
        setError(response.error || response.message || 'Failed to analyze check. Please try again.');
        setResults(null);
      } else if (response.success === true && response.data) {
        console.log('✅ Analysis successful - displaying results');
        // Process results with proper nested data access
        const processedResults = {
          ...response.data,
          // Extract ML analysis fields
          fraud_risk_score: response.data.ml_analysis?.fraud_risk_score || 0,
          risk_level: response.data.ml_analysis?.risk_level || 'UNKNOWN',
          model_confidence: response.data.ml_analysis?.model_confidence || 0,
          // Extract AI analysis fields with proper naming
          ai_recommendation: response.data.ai_analysis?.recommendation || 'UNKNOWN',
          ai_confidence: response.data.ai_analysis?.confidence_score || 0,
        };
        setResults(processedResults);
        setError(null);
      } else {
        console.log('⚠️ Unexpected response format:', response);
        setError('Received unexpected response format from server');
        setResults(null);
      }
    } catch (err) {
      console.error('❌ Check analysis error caught:', err);
      const errorMessage = err.error || err.message || err.response?.data?.error || err.response?.data?.message || 'Failed to analyze check. Please try again.';
      setError(errorMessage);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = () => {
    const payload = results
      ? { ...results, extracted_sections: buildCheckSections(results) }
      : results;
    const dataStr = JSON.stringify(payload, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `check_analysis_${new Date().getTime()}.json`;
    link.click();
  };

  const downloadCSV = () => {
    if (!results) return;

    // CSV Headers
    const headers = [
      'Document Type',
      'Timestamp',
      'Bank Name',
      'Check Number',
      'Amount',
      'Date',
      'Payee Name',
      'Payer Name',
      'Account Number',
      'Routing Number',
      'Fraud Risk Score (%)',
      'Risk Level',
      'Model Confidence (%)',
      'AI Recommendation',
      'AI Confidence (%)',
      'Signature Detected',
      'Anomaly Count',
      'Top Anomalies'
    ];

    // Filter anomalies to exclude AI recommendations and scores
    const filteredAnomalies = (results.anomalies || []).filter(anomaly => {
      const anomalyLower = String(anomaly).toLowerCase();
      return !anomalyLower.includes('ai recommendation') &&
        !anomalyLower.includes('high fraud risk detected') &&
        !anomalyLower.includes('risk score');
    });

    // CSV Row
    const row = [
      'Bank Check',
      results.timestamp || new Date().toISOString(),
      results.bank_name || 'N/A',
      results.check_number || 'N/A',
      results.amount || 'N/A',
      results.date || 'N/A',
      results.payee_name || 'N/A',
      results.payer_name || 'N/A',
      results.account_number || 'N/A',
      results.routing_number || 'N/A',
      ((results.fraud_risk_score || 0) * 100).toFixed(2),
      results.risk_level || 'UNKNOWN',
      ((results.model_confidence || 0) * 100).toFixed(2),
      results.ai_recommendation || 'UNKNOWN',
      ((results.ai_confidence || 0) * 100).toFixed(2),
      results.signature_detected ? 'Yes' : 'No',
      filteredAnomalies.length,
      filteredAnomalies.slice(0, 3).join(' | ')
    ];

    // Escape CSV values
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
    link.download = `check_analysis_${new Date().getTime()}.csv`;
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
    borderRadius: '0.5rem',
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

  const infoCardStyle = {
    backgroundColor: colors.card,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    marginBottom: '1rem',
    color: colors.foreground,
  };

  const criticalFactors = results ? buildCheckCriticalFactors(results, results?.anomalies || []) : [];

  const tabStyle = (isActive) => ({
    padding: '1rem 2rem',
    borderRadius: '0.75rem 0.75rem 0 0',
    backgroundColor: isActive ? primary : colors.secondary,
    color: isActive ? colors.primaryForeground : colors.foreground,
    border: `1px solid ${colors.border}`,
    borderBottom: isActive ? 'none' : `1px solid ${colors.border}`,
    cursor: 'pointer',
    fontWeight: isActive ? '600' : '500',
    transition: 'all 0.3s',
  });

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
          Check <span style={{ color: primary }}>Analysis</span>
        </h1>
        <p>Analyze bank checks for fraud detection</p>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('analyze')}
          style={tabStyle(activeTab === 'analyze')}
          onMouseEnter={(e) => activeTab === 'analyze' || (e.target.style.backgroundColor = colors.muted)}
          onMouseLeave={(e) => activeTab === 'analyze' || (e.target.style.backgroundColor = colors.secondary)}
        >
          Analysis
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          style={tabStyle(activeTab === 'insights')}
          onMouseEnter={(e) => activeTab === 'insights' || (e.target.style.backgroundColor = colors.muted)}
          onMouseLeave={(e) => activeTab === 'insights' || (e.target.style.backgroundColor = colors.secondary)}
        >
          Insights
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'analyze' && (
        <div style={gridStyle}>
          {/* Upload Section */}
          <div style={cardStyle}>
            <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
              Upload Check Image
            </h2>

            <div style={{
              backgroundColor: '#FFF3CD',
              border: '1px solid #FFC107',
              borderRadius: '8px',
              padding: '1rem',
              marginBottom: '1rem',
            }}>
              <div style={{ color: '#856404', fontSize: '0.875rem', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FaExclamationTriangle />
                <span>Only upload bank check images (personal or business checks)</span>
              </div>
            </div>

            <div {...getRootProps()} style={dropzoneStyle}>
              <input {...getInputProps()} />
              <FaLandmark style={{ fontSize: '3rem', marginBottom: '1rem', color: colors.foreground }} />
              {isDragActive ? (
                <p style={{ color: primary, fontWeight: '500' }}>
                  Drop the check image here...
                </p>
              ) : (
                <div>
                  <p style={{ color: colors.foreground, marginBottom: '0.5rem' }}>
                    Drop your check image here or click to browse
                  </p>
                  <p style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
                    Bank Checks Only - JPG, JPEG, PNG, PDF
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
                      alt="Check preview"
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
              {loading ? 'Analyzing...' : 'Analyze Check'}
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
                <p>Upload a check image on the left to begin analysis</p>
              </div>
            )}

            {loading && (
              <div style={{ textAlign: 'center', padding: '3rem' }}>
                <FaCog className="spin" style={{
                  fontSize: '3rem',
                  color: primary,
                }} />
                <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                  Analyzing check...
                </p>
              </div>
            )}

            {results && (
              <div className="fade-in">
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
                    {((results.fraud_risk_score || 0) * 100).toFixed(1)}%
                  </div>
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
                    {((results.model_confidence || 0) * 100).toFixed(1)}%
                  </div>
                </div>

                {/* AI Recommendation Card */}
                <div style={{
                  ...resultCardStyle,
                  marginBottom: '1.5rem',
                  backgroundColor: results.ai_recommendation === 'APPROVE' ? `${colors.status.success}20` :
                    results.ai_recommendation === 'REJECT' ? `${primary}20` :
                      `${colors.status.warning}20`,
                  borderLeft: `4px solid ${results.ai_recommendation === 'APPROVE' ? colors.status.success :
                    results.ai_recommendation === 'REJECT' ? primary :
                      colors.status.warning}`,
                }}>
                  <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                    AI Recommendation
                  </div>
                  <div style={{
                    fontSize: '2rem',
                    fontWeight: 'bold',
                    color: results.ai_recommendation === 'APPROVE' ? colors.status.success :
                      results.ai_recommendation === 'REJECT' ? primary :
                        colors.status.warning,
                  }}>
                    {results.ai_recommendation || 'UNKNOWN'}
                  </div>
                </div>

                {/* Fraud Type Card - Shows fraud type and explanations for REJECT ONLY */}
                {(() => {
                  // Get AI recommendation
                  const aiRecommendation = results.ai_recommendation;

                  // Only show for REJECT (not APPROVE or ESCALATE)
                  if (aiRecommendation !== 'REJECT') {
                    return null;
                  }

                  // Get fraud types and explanations from AI analysis
                  const aiAnalysis = results.ai_analysis || {};
                  const fraudTypes = aiAnalysis.fraud_types || [];
                  const fraudExplanations = aiAnalysis.fraud_explanations || [];

                  // Only show if we have fraud types or explanations
                  if (fraudTypes.length === 0 && fraudExplanations.length === 0) {
                    return null;
                  }

                  // Get primary fraud type (first in list)
                  const primaryFraudType = fraudTypes[0];
                  const displayLabel = primaryFraudType ? primaryFraudType.replace(/_/g, ' ') : 'FRAUD DETECTED';

                  // Collect all explanations
                  let displayExplanations = [];
                  if (fraudExplanations.length > 0) {
                    fraudExplanations.forEach(exp => {
                      if (exp.explanation) {
                        displayExplanations.push(exp.explanation);
                      }
                    });
                  }

                  // Fallback if no explanations
                  if (displayExplanations.length === 0 && primaryFraudType) {
                    displayExplanations.push(`${displayLabel} detected by fraud analysis`);
                  }

                  // Determine color based on fraud type
                  const fraudTypeColor = primaryFraudType === 'SIGNATURE_FORGERY' ? primary :
                    primaryFraudType === 'AMOUNT_ALTERATION' ? primary :
                      primaryFraudType === 'COUNTERFEIT_CHECK' ? primary :
                        primaryFraudType === 'REPEAT_OFFENDER' ? colors.status.warning :
                          primaryFraudType === 'STALE_CHECK' ? colors.status.warning :
                            primary;

                  return (
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: '1.5rem',
                      backgroundColor: `${fraudTypeColor}15`,
                      borderLeft: `4px solid ${fraudTypeColor}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.75rem' }}>
                        FRAUD TYPE
                      </div>
                      <div style={{
                        fontSize: '1.5rem',
                        fontWeight: 'bold',
                        color: fraudTypeColor,
                        marginBottom: '1rem',
                      }}>
                        {displayLabel}
                      </div>
                    </div>
                  );
                })()}

                {/* Actionable Recommendations Card */}
                {(() => {
                  const aiAnalysis = results.ai_analysis || {};
                  const actionableRecommendations = aiAnalysis.actionable_recommendations || [];

                  if (actionableRecommendations.length === 0) {
                    return null;
                  }

                  return (
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: '1.5rem',
                      borderLeft: `4px solid ${colors.status?.info || '#3b82f6'}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '1rem' }}>
                        Actionable Recommendations
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '1.5rem', color: colors.foreground }}>
                        {actionableRecommendations.map((rec, index) => (
                          <li key={index} style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  );
                })()}

                {/* Key Missing / Risk Factors section - HIDDEN */}


                {/* Removed Analysis Details and Risk Analysis sections */}


                <div style={{
                  ...resultCardStyle,
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`
                }}>
                  <p style={{ margin: 0 }}>
                    Detailed extracted check information is available in the downloaded JSON file in a structured table format.
                  </p>
                </div>

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
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <CheckInsights />
      )}
    </div>
  );
};

export default CheckAnalysis;
