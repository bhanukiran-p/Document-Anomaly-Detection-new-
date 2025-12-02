import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzePaystub } from '../services/api';
import { colors } from '../styles/colors';

const PaystubAnalysis = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

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

    try {
      const response = await analyzePaystub(file);
      setResults(response.data);
    } catch (err) {
      setError(err.error || 'Failed to analyze paystub. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `paystub_analysis_${new Date().getTime()}.json`;
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
    background: colors.gradients.navy,
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

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Paystub Analysis</h1>
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
            <p style={{ color: '#856404', fontSize: '0.875rem', margin: 0, fontWeight: '500' }}>
              ⚠️ Only upload paystub documents (payslips or salary statements)
            </p>
          </div>

          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💰</div>
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
              <div className="spin" style={{ fontSize: '3rem', color: primary }}>⚙️</div>
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing paystub...
              </p>
            </div>
          )}

          {results && (
            <div className="fade-in">
              {/* AI Analysis Section */}
              {results.fraud_risk_score !== undefined && (
                <div style={{ marginBottom: '2rem' }}>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
                    Fraud Analysis
                  </h3>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
                    {/* Fraud Risk Score Card */}
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: 0,
                      backgroundColor: `${primary}20`,
                      borderLeft: `4px solid ${primary}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                        Fraud Risk Score
                      </div>
                      <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: primary }}>
                        {(results.fraud_risk_score * 100).toFixed(1)}%
                      </div>
                    </div>

                    {/* Model Confidence Card */}
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: 0,
                      backgroundColor: `${colors.status.success}20`,
                      borderLeft: `4px solid ${colors.status.success}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                        Model Confidence
                      </div>
                      <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: colors.status.success }}>
                        {(results.model_confidence * 100).toFixed(1)}%
                      </div>
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

                  {/* Actionable Recommendations Card */}
                  {results.ai_analysis && results.ai_analysis.actionable_recommendations && results.ai_analysis.actionable_recommendations.length > 0 && (
                    <div style={{
                      ...resultCardStyle,
                      marginBottom: '1.5rem',
                      borderLeft: `4px solid ${colors.status?.info || '#3b82f6'}`,
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '1rem' }}>
                        Actionable Recommendations
                      </div>
                      <ul style={{ margin: 0, paddingLeft: '1.5rem', color: colors.foreground }}>
                        {results.ai_analysis.actionable_recommendations.map((rec, index) => (
                          <li key={index} style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Analysis Details Section - Similar to Money Order */}
              {results && (results.ai_analysis || results.ml_analysis) && (
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

                  {results.ai_analysis && results.ai_analysis.summary ? (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Summary:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem' }}>
                        {results.ai_analysis.summary}
                      </p>
                    </div>
                  ) : results.ml_analysis ? (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Summary:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem' }}>
                        {results.ml_analysis.risk_level === 'HIGH' || results.ml_analysis.risk_level === 'CRITICAL' 
                          ? 'High fraud risk - requires immediate review'
                          : results.ml_analysis.risk_level === 'MEDIUM'
                          ? 'Moderate fraud risk - requires human review'
                          : 'Low fraud risk - proceed with caution'}
                      </p>
                    </div>
                  ) : null}

                  {results.ai_analysis && results.ai_analysis.reasoning ? (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Reasoning:</strong>
                      <div style={{ color: colors.mutedForeground, marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
                        {Array.isArray(results.ai_analysis.reasoning) 
                          ? results.ai_analysis.reasoning.map((reason, idx) => (
                              <div key={idx} style={{ marginBottom: '0.5rem' }}>
                                • {reason}
                              </div>
                            ))
                          : typeof results.ai_analysis.reasoning === 'string'
                          ? results.ai_analysis.reasoning.split('\n').map((line, idx) => (
                              <div key={idx} style={{ marginBottom: '0.3rem' }}>{line}</div>
                            ))
                          : String(results.ai_analysis.reasoning)}
                      </div>
                      {results.ml_analysis && (
                        <div style={{ color: colors.mutedForeground, marginTop: '0.5rem', padding: '0.75rem', backgroundColor: colors.secondary, borderRadius: '0.5rem' }}>
                          <strong>ML Model Results:</strong> Random Forest {((results.ml_analysis.fraud_risk_score || 0) * 100).toFixed(1)}%, 
                          combined fraud risk {((results.ml_analysis.fraud_risk_score || 0) * 100).toFixed(1)}% 
                          with {((results.ml_analysis.model_confidence || 0) * 100).toFixed(1)}% model confidence
                          {((results.ml_analysis.fraud_risk_score || 0) * 100) < 30 
                            ? ' - indicates no algorithmic red flags'
                            : ' - indicates potential fraud risk'}
                        </div>
                      )}
                    </div>
                  ) : results.ml_analysis ? (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Reasoning:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem' }}>
                        AI analysis unavailable - using ML-based fallback decision<br/>
                        ML fraud score: {((results.ml_analysis.fraud_risk_score || 0) * 100).toFixed(2)}%<br/>
                        Risk level: {results.ml_analysis.risk_level || 'UNKNOWN'}
                      </p>
                    </div>
                  ) : null}

                  {results.ai_analysis && results.ai_analysis.key_indicators && results.ai_analysis.key_indicators.length > 0 ? (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Key Fraud Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {results.ai_analysis.key_indicators.map((indicator, idx) => (
                          <li key={idx} style={{ marginBottom: '0.3rem' }}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  ) : results.ml_analysis && results.ml_analysis.anomalies && results.ml_analysis.anomalies.length > 0 ? (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Key Fraud Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {results.ml_analysis.anomalies.map((indicator, idx) => (
                          <li key={idx} style={{ marginBottom: '0.3rem' }}>{indicator}</li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Key Fraud Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        <li>None identified by ML or manual review</li>
                      </ul>
                    </div>
                  )}

                  {results.ai_analysis && results.ai_analysis.verification_notes && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Verification Notes:</strong>
                      <p style={{ color: colors.mutedForeground, marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
                        {results.ai_analysis.verification_notes}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Risk Analysis Details - Feature Importance */}
              {results && results.ml_analysis && (
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
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Risk Level:</strong>
                      <span style={{
                        marginLeft: '0.5rem',
                        color: results.ml_analysis.risk_level === 'HIGH' || results.ml_analysis.risk_level === 'CRITICAL' ? primary : 
                               results.ml_analysis.risk_level === 'MEDIUM' ? colors.status.warning : colors.status.success,
                        fontWeight: 'bold'
                      }}>
                        {results.ml_analysis.risk_level}
                      </span>
                    </div>
                  )}

                  {results.ml_analysis.model_scores && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Model Scores:</strong>
                      <div style={{ color: colors.mutedForeground, marginTop: '0.5rem' }}>
                        {results.ml_analysis.model_scores.random_forest !== undefined && (
                          <div>Primary Analysis: {((results.ml_analysis.model_scores.random_forest || 0) * 100).toFixed(1)}%</div>
                        )}
                        {results.ml_analysis.model_scores.xgboost !== undefined && (
                          <div>Secondary Analysis: {((results.ml_analysis.model_scores.xgboost || 0) * 100).toFixed(1)}%</div>
                        )}
                        {results.ml_analysis.model_scores.ensemble !== undefined && (
                          <div>Ensemble Score: {((results.ml_analysis.model_scores.ensemble || 0) * 100).toFixed(1)}%</div>
                        )}
                        {results.ml_analysis.model_scores.heuristic !== undefined && (
                          <div>Heuristic Score: {((results.ml_analysis.model_scores.heuristic || 0) * 100).toFixed(1)}%</div>
                        )}
                      </div>
                    </div>
                  )}

                  {results.ml_analysis && Array.isArray(results.ml_analysis.feature_importance) && results.ml_analysis.feature_importance.length > 0 ? (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Top Risk Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        {results.ml_analysis.feature_importance.slice(0, 5).map((item, idx) => {
                          if (typeof item === 'string') {
                            return <li key={idx} style={{ marginBottom: '0.3rem' }}>{item}</li>;
                          } else if (item.feature && item.importance) {
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
                  ) : (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong style={{ color: colors.foreground }}>Top Risk Indicators:</strong>
                      <ul style={{ color: colors.mutedForeground, marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                        <li>No significant risk factors identified</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Detailed sections removed as per user request to show only top 4 metrics */}
              {/*
              <div style={confidenceStyle(results.confidence_score || 0)}>
                [{results.confidence_score >= 70 ? 'HIGH' : results.confidence_score >= 50 ? 'MEDIUM' : 'LOW'}]
                Extraction Confidence: {results.confidence_score?.toFixed(1)}%
              </div>

              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
                Company & Employee Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Company:</strong> {results.company_name || 'N/A'}</p>
                <p><strong>Employee:</strong> {results.employee_name || 'N/A'}</p>
                <p><strong>Employee ID:</strong> {results.employee_id || 'N/A'}</p>
              </div>

              <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Pay Period Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Pay Period:</strong> {results.pay_period_start || 'N/A'} to {results.pay_period_end || 'N/A'}</p>
                <p><strong>Pay Date:</strong> {results.pay_date || 'N/A'}</p>
              </div>

              <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Earnings
              </h3>
              <div style={metricsGridStyle}>
                <div style={metricStyle}>
                  <div style={{ color: colors.neutral.gray600, fontSize: '0.875rem' }}>Gross Pay</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.status.success }}>
                    ${results.gross_pay || 'N/A'}
                  </div>
                </div>
                <div style={metricStyle}>
                  <div style={{ color: colors.neutral.gray600, fontSize: '0.875rem' }}>Net Pay</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.status.success }}>
                    ${results.net_pay || 'N/A'}
                  </div>
                </div>
                <div style={metricStyle}>
                  <div style={{ color: colors.neutral.gray600, fontSize: '0.875rem' }}>YTD Gross</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.foreground }}>
                    ${results.ytd_gross || 'N/A'}
                  </div>
                </div>
                <div style={metricStyle}>
                  <div style={{ color: colors.neutral.gray600, fontSize: '0.875rem' }}>YTD Net</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.foreground }}>
                    ${results.ytd_net || 'N/A'}
                  </div>
                </div>
              </div>

              {/* 
              {results.federal_tax && (
                <>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                    Tax Withholdings
                  </h3>
                  <div style={resultCardStyle}>
                    {results.federal_tax && <p><strong>Federal Tax:</strong> ${results.federal_tax}</p>}
                    {results.state_tax && <p><strong>State Tax:</strong> ${results.state_tax}</p>}
                    {results.social_security && <p><strong>Social Security:</strong> ${results.social_security}</p>}
                    {results.medicare && <p><strong>Medicare:</strong> ${results.medicare}</p>}
                  </div>
                </>
              )}
              */}

              <button
                style={{
                  ...buttonStyle,
                  backgroundColor: primary,
                  marginTop: '1.5rem',
                }}
                onClick={downloadJSON}
                onMouseEnter={(e) => e.target.style.backgroundColor = primary}
                onMouseLeave={(e) => e.target.style.backgroundColor = primary}
              >
                Download Full Results (JSON)
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaystubAnalysis;

