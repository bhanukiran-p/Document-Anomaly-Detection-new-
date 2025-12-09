import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeMoneyOrder } from '../services/api';
import { colors } from '../styles/colors';
import MoneyOrderInsights from '../components/MoneyOrderInsights.jsx';

const MoneyOrderAnalysis = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('analyze');

  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

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

    try {
      const response = await analyzeMoneyOrder(file);
      setResults(response);
    } catch (err) {
      setError(err.error || 'Failed to analyze money order. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = async () => {
    if (!results || !results.analysis_id) {
      // Fallback: download current results
      const dataStr = JSON.stringify(results, null, 2);
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
        // Fallback to current results
        const dataStr = JSON.stringify(results, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `money_order_analysis_${new Date().getTime()}.json`;
        link.click();
      }
    } catch (err) {
      console.error('Download error:', err);
      // Fallback to current results
      const dataStr = JSON.stringify(results, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `money_order_analysis_${new Date().getTime()}.json`;
      link.click();
    }
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
    borderRadius: '0.5rem',
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

  // Get the data from response (could be results.data or results directly)
  const analysisData = results?.data || results;

  // Check for new nested structure or old flat structure
  const mlAnalysis = analysisData?.ml_analysis || analysisData;
  const aiAnalysis = analysisData?.ai_analysis || analysisData;

  const hasResults = analysisData && (
    (mlAnalysis.fraud_risk_score !== undefined) ||
    (aiAnalysis.recommendation !== undefined || aiAnalysis.ai_recommendation !== undefined)
  );

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
          Money Order <span style={{ color: primary }}>Analysis</span>
        </h1>
        <p style={{ color: colors.mutedForeground }}>Analyze money orders for fraud and anomaly detection</p>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('analyze')}
          style={tabStyle(activeTab === 'analyze')}
          onMouseEnter={(e) => !activeTab && (e.target.style.backgroundColor = colors.muted)}
          onMouseLeave={(e) => !activeTab && (e.target.style.backgroundColor = colors.secondary)}
        >
          Analysis
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          style={tabStyle(activeTab === 'insights')}
          onMouseEnter={(e) => !activeTab && (e.target.style.backgroundColor = colors.muted)}
          onMouseLeave={(e) => !activeTab && (e.target.style.backgroundColor = colors.secondary)}
        >
          Insights
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'analyze' && (
        <div style={gridStyle}>
          {/* Upload Section */}
          <div style={cardStyle}>
            <h2 style={{ color: colors.foreground, marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: 'bold' }}>
              Upload Money Order Image
            </h2>

            <div style={warningBannerStyle}>
              <p style={{ color: primary, fontSize: '0.875rem', margin: 0, fontWeight: '500' }}>
                ⚠️ Only upload money order documents (Western Union, MoneyGram, USPS, etc.)
              </p>
            </div>

            <div {...getRootProps()} style={dropzoneStyle}>
              <input {...getInputProps()} />
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💵</div>
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
                <div className="spin" style={{
                  fontSize: '3rem',
                  color: primary,
                }}>⚙️</div>
                <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>
                  Analyzing money order...
                </p>
              </div>
            )}

            {/* Display Results */}
            {results && results.success && hasResults && (
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
                    {(mlAnalysis.fraud_risk_score * 100).toFixed(1)}%
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
                    {(mlAnalysis.model_confidence * 100).toFixed(1)}%
                  </div>
                </div>

                {/* AI Recommendation Card */}
                <div style={{
                  ...resultCardStyle,
                  marginBottom: '1.5rem',
                  backgroundColor: (aiAnalysis.recommendation || aiAnalysis.ai_recommendation) === 'APPROVE' ? `${colors.status.success}20` :
                    (aiAnalysis.recommendation || aiAnalysis.ai_recommendation) === 'REJECT' ? `${primary}20` :
                      `${colors.status.warning}20`,
                  borderLeft: `4px solid ${(aiAnalysis.recommendation || aiAnalysis.ai_recommendation) === 'APPROVE' ? colors.status.success :
                    (aiAnalysis.recommendation || aiAnalysis.ai_recommendation) === 'REJECT' ? primary :
                      colors.status.warning}`,
                }}>
                  <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                    AI Recommendation
                  </div>
                  <div style={{
                    fontSize: '2rem',
                    fontWeight: 'bold',
                    color: (aiAnalysis.recommendation || aiAnalysis.ai_recommendation) === 'APPROVE' ? colors.status.success :
                      (aiAnalysis.recommendation || aiAnalysis.ai_recommendation) === 'REJECT' ? primary :
                        colors.status.warning,
                  }}>
                    {aiAnalysis.recommendation || aiAnalysis.ai_recommendation || 'UNKNOWN'}
                  </div>
                </div>

                {/* Fraud Type Card - Shows fraud type and explanations for REJECT ONLY */}
                {(() => {
                  // Only show for REJECT (not APPROVE or ESCALATE)
                  const recommendation = aiAnalysis.recommendation || aiAnalysis.ai_recommendation;
                  if (recommendation !== 'REJECT') {
                    return null;
                  }

                  // Get fraud type and explanations from response
                  const fraudType = results.fraud_type || analysisData?.fraud_type;
                  const fraudTypeLabel = results.fraud_type_label || analysisData?.fraud_type_label;
                  const fraudExplanations = results.fraud_explanations || analysisData?.fraud_explanations || [];

                  // Only show if we have fraud type or explanations
                  if (!fraudType && !fraudTypeLabel && fraudExplanations.length === 0) {
                    return null;
                  }

                  // Get display label (prefer fraud_type_label, fallback to formatted fraud_type)
                  const displayLabel = fraudTypeLabel || (fraudType ? fraudType.replace(/_/g, ' ') : 'FRAUD DETECTED');

                  // Collect all reasons from fraud explanations
                  let displayReasons = [];
                  if (fraudExplanations.length > 0) {
                    fraudExplanations.forEach(exp => {
                      if (exp.reasons && exp.reasons.length > 0) {
                        displayReasons.push(...exp.reasons);
                      }
                    });
                  }

                  // Fallback if no reasons
                  if (displayReasons.length === 0) {
                    displayReasons.push('Fraud indicators detected by ML analysis');
                  }

                  return (
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: '1.5rem',
                      backgroundColor: `${primary}15`,
                      borderLeft: `4px solid ${primary}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.75rem' }}>
                        FRAUD TYPE
                      </div>
                      <div style={{
                        fontSize: '1.5rem',
                        fontWeight: 'bold',
                        color: primary,
                        marginBottom: '1rem',
                      }}>
                        {displayLabel}
                      </div>
                      <div style={{ color: colors.foreground }}>
                        <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                          Why this fraud occurred:
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.5rem', color: colors.foreground }}>
                          {displayReasons.slice(0, 3).map((reason, index) => (
                            <li key={index} style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>{reason}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  );
                })()}

                {/* Actionable Recommendations Card */}
                {aiAnalysis.actionable_recommendations && aiAnalysis.actionable_recommendations.length > 0 && (
                  <div style={{
                    ...resultCardStyle,
                    marginBottom: '1.5rem',
                    borderLeft: `4px solid ${colors.status?.info || '#3b82f6'}`,
                  }}>
                    <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '1rem' }}>
                      Actionable Recommendations
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '1.5rem', color: colors.foreground }}>
                      {aiAnalysis.actionable_recommendations.map((rec, index) => (
                        <li key={index} style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Informational Message */}
                <div style={{
                  ...resultCardStyle,
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`
                }}>
                  <p style={{ margin: 0, color: colors.mutedForeground }}>
                    Detailed extracted money order information is available in the downloaded JSON file in a structured table format.
                  </p>
                </div>

                {/* Download Button */}
                <button
                  style={{
                    ...buttonStyle,
                    backgroundColor: colors.card,
                    color: colors.foreground,
                    border: `2px solid ${colors.border}`,
                    marginTop: '1.5rem',
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
                  Download Full Results (JSON)
                </button>
              </div>
            )}

            {/* Legacy format support (if old API response structure) */}
            {results && results.success && !hasResults && results.data && (
              <div className="fade-in">
                <div style={{
                  backgroundColor: colors.secondary,
                  padding: '1.5rem',
                  borderRadius: '0.5rem',
                  border: `1px solid ${colors.border}`,
                  color: colors.foreground,
                }}>
                  <p style={{ color: colors.mutedForeground }}>
                    Analysis completed. Full results available for download.
                  </p>
                </div>

                <button
                  style={{
                    ...buttonStyle,
                    backgroundColor: colors.card,
                    color: colors.foreground,
                    border: `2px solid ${colors.border}`,
                    marginTop: '1.5rem',
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
                  Download Full Results (JSON)
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <MoneyOrderInsights />
      )}
    </div>
  );
};

export default MoneyOrderAnalysis;
