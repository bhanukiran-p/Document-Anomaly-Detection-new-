import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeMoneyOrder } from '../services/api';
import { colors } from '../styles/colors';

const MoneyOrderAnalysis = () => {
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
      setError('Please upload a money order image first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await analyzeMoneyOrder(file);
      setResults(response.data);
    } catch (err) {
      setError(err.error || 'Failed to analyze money order. Please try again.');
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
    link.download = `money_order_analysis_${new Date().getTime()}.json`;
    link.click();
  };

  // Styles
  const containerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
  };

  const headerStyle = {
    background: `linear-gradient(135deg, ${colors.primary.navy} 0%, ${colors.primary.blue} 100%)`,
    padding: '2rem',
    borderRadius: '12px',
    color: colors.neutral.white,
    textAlign: 'center',
    marginBottom: '2rem',
  };

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
    gap: '2rem',
  };

  const cardStyle = {
    backgroundColor: colors.background.card,
    borderRadius: '12px',
    padding: '2rem',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
  };

  const dropzoneStyle = {
    border: `2px dashed ${isDragActive ? colors.primary.blue : colors.neutral.gray300}`,
    borderRadius: '12px',
    padding: '3rem',
    textAlign: 'center',
    backgroundColor: isDragActive ? colors.primary.lightBlue : colors.background.main,
    cursor: 'pointer',
    transition: 'all 0.2s',
  };

  const buttonStyle = {
    backgroundColor: colors.accent.red,
    color: colors.neutral.white,
    padding: '1rem 2rem',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    fontWeight: '600',
    width: '100%',
    marginTop: '1rem',
    cursor: loading ? 'not-allowed' : 'pointer',
    opacity: loading ? 0.6 : 1,
  };

  const resultCardStyle = {
    backgroundColor: colors.background.main,
    padding: '1.5rem',
    borderRadius: '8px',
    borderLeft: `4px solid ${colors.primary.blue}`,
    marginBottom: '1rem',
  };

  const anomalyCardStyle = (severity) => {
    let bgColor = colors.status.infoLight;
    let borderColor = colors.status.info;

    if (severity === 'critical') {
      bgColor = colors.accent.redLight;
      borderColor = colors.accent.red;
    } else if (severity === 'high') {
      bgColor = colors.status.warningLight;
      borderColor = colors.status.warning;
    } else if (severity === 'medium') {
      bgColor = colors.status.infoLight;
      borderColor = colors.status.info;
    }

    return {
      backgroundColor: bgColor,
      padding: '1rem',
      borderRadius: '8px',
      borderLeft: `4px solid ${borderColor}`,
      marginBottom: '0.75rem',
    };
  };

  const confidenceStyle = (confidence) => {
    let bgColor = colors.accent.redLight;
    let textColor = colors.accent.red;

    if (confidence >= 80) {
      bgColor = colors.status.successLight;
      textColor = colors.status.success;
    } else if (confidence >= 60) {
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
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Money Order Analysis</h1>
        <p>Analyze money orders for fraud and anomaly detection</p>
      </div>

      <div style={gridStyle}>
        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: colors.primary.navy, marginBottom: '1.5rem' }}>
            Upload Money Order Image
          </h2>

          <div style={{
            backgroundColor: '#FFF3CD',
            border: '1px solid #FFC107',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1rem',
          }}>
            <p style={{ color: '#856404', fontSize: '0.875rem', margin: 0, fontWeight: '500' }}>
              ⚠️ Only upload money order documents (Western Union, MoneyGram, USPS, etc.)
            </p>
          </div>

          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>💵</div>
            {isDragActive ? (
              <p style={{ color: colors.primary.blue, fontWeight: '500' }}>
                Drop the money order image here...
              </p>
            ) : (
              <div>
                <p style={{ color: colors.neutral.gray700, marginBottom: '0.5rem' }}>
                  Drop your money order image here or click to browse
                </p>
                <p style={{ color: colors.neutral.gray500, fontSize: '0.875rem' }}>
                  Money Orders Only - JPG, JPEG, PNG, PDF
                </p>
              </div>
            )}
          </div>

          {file && (
            <div style={{ marginTop: '1.5rem' }}>
              <div style={{
                backgroundColor: colors.primary.lightBlue,
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
                    alt="Money order preview"
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
            {loading ? 'Analyzing...' : 'Analyze Money Order'}
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
          <h2 style={{ color: colors.primary.navy, marginBottom: '1.5rem' }}>
            Analysis Results
          </h2>

          {!results && !loading && (
            <div style={{
              backgroundColor: colors.primary.lightBlue,
              padding: '2rem',
              borderRadius: '8px',
              textAlign: 'center',
              color: colors.primary.navy,
            }}>
              <p>Upload a money order image on the left to begin analysis</p>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <div className="spin" style={{
                fontSize: '3rem',
                color: colors.primary.blue,
              }}>⚙️</div>
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing money order...
              </p>
            </div>
          )}

          {results && results.status === 'success' && (
            <div className="fade-in">
              <div style={confidenceStyle(results.confidence_score || 0)}>
                [{results.confidence_score >= 80 ? 'HIGH' : results.confidence_score >= 60 ? 'MEDIUM' : 'LOW'}]
                Confidence: {results.confidence_score?.toFixed(1)}%
              </div>

              {/* ML Risk Analysis Section */}
              {results.ml_analysis && (
                <div style={{
                  marginBottom: '2rem',
                  padding: '1.5rem',
                  backgroundColor: results.ml_analysis.risk_level === 'LOW' ? '#e8f5e9' :
                                   results.ml_analysis.risk_level === 'MEDIUM' ? '#fff8e1' :
                                   results.ml_analysis.risk_level === 'HIGH' ? '#ffe0b2' : '#ffebee',
                  border: `2px solid ${results.ml_analysis.risk_level === 'LOW' ? '#4caf50' :
                                        results.ml_analysis.risk_level === 'MEDIUM' ? '#ff9800' :
                                        results.ml_analysis.risk_level === 'HIGH' ? '#ff5722' : '#f44336'}`,
                  borderRadius: '8px'
                }}>
                  <h3 style={{
                    color: results.ml_analysis.risk_level === 'LOW' ? '#2e7d32' :
                           results.ml_analysis.risk_level === 'MEDIUM' ? '#e65100' :
                           results.ml_analysis.risk_level === 'HIGH' ? '#d84315' : '#c62828',
                    marginBottom: '1rem',
                    fontSize: '1.4rem'
                  }}>
                    🤖 ML Fraud Risk Analysis
                  </h3>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', marginBottom: '1rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.9rem', color: colors.neutral.gray600, marginBottom: '0.3rem' }}>
                        Fraud Risk Score
                      </div>
                      <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: colors.primary.navy }}>
                        {(results.ml_analysis.fraud_risk_score * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: '1.1rem', fontWeight: '600', marginTop: '0.3rem' }}>
                        Risk Level: {results.ml_analysis.risk_level}
                      </div>
                    </div>

                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.9rem', color: colors.neutral.gray600, marginBottom: '0.3rem' }}>
                        Model Confidence
                      </div>
                      <div style={{ fontSize: '1.8rem', fontWeight: 'bold', color: colors.status.success }}>
                        {(results.ml_analysis.model_confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Model Scores Breakdown */}
                  {results.ml_analysis.model_scores && (
                    <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: colors.neutral.gray700 }}>
                      <strong>Model Ensemble:</strong>
                      <span style={{ marginLeft: '1rem' }}>
                        Random Forest: {(results.ml_analysis.model_scores.random_forest * 100).toFixed(1)}%
                      </span>
                      <span style={{ marginLeft: '1rem' }}>
                        XGBoost: {(results.ml_analysis.model_scores.xgboost * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* AI Recommendation Section */}
              {results.ai_analysis && (
                <div style={{ marginBottom: '2rem' }}>
                  <div style={{
                    padding: '1.5rem',
                    backgroundColor: results.ai_analysis.recommendation === 'APPROVE' ? '#e8f5e9' :
                                     results.ai_analysis.recommendation === 'REJECT' ? '#ffebee' : '#fff8e1',
                    border: `3px solid ${results.ai_analysis.recommendation === 'APPROVE' ? '#4caf50' :
                                          results.ai_analysis.recommendation === 'REJECT' ? '#f44336' : '#ff9800'}`,
                    borderRadius: '10px',
                    marginBottom: '1rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ fontSize: '0.9rem', color: colors.neutral.gray600, marginBottom: '0.5rem' }}>
                          🧠 AI Recommendation
                        </div>
                        <div style={{
                          fontSize: '2rem',
                          fontWeight: 'bold',
                          color: results.ai_analysis.recommendation === 'APPROVE' ? '#2e7d32' :
                                 results.ai_analysis.recommendation === 'REJECT' ? '#c62828' : '#e65100'
                        }}>
                          {results.ai_analysis.recommendation}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.9rem', color: colors.neutral.gray600 }}>
                          Confidence
                        </div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                          {(results.ai_analysis.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>

                    {/* AI Summary */}
                    {results.ai_analysis.summary && (
                      <div style={{
                        marginTop: '1rem',
                        padding: '1rem',
                        backgroundColor: 'rgba(255,255,255,0.7)',
                        borderRadius: '6px',
                        fontSize: '0.95rem',
                        fontStyle: 'italic'
                      }}>
                        {results.ai_analysis.summary}
                      </div>
                    )}
                  </div>

                  {/* AI Reasoning */}
                  {results.ai_analysis.reasoning && (
                    <div style={{
                      padding: '1.5rem',
                      backgroundColor: colors.neutral.gray100,
                      borderRadius: '8px',
                      marginBottom: '1rem'
                    }}>
                      <h4 style={{ color: colors.primary.navy, marginBottom: '0.8rem' }}>
                        📊 Analysis Reasoning
                      </h4>
                      <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', lineHeight: '1.6' }}>
                        {results.ai_analysis.reasoning}
                      </div>
                    </div>
                  )}

                  {/* Key Indicators */}
                  {results.ai_analysis.key_indicators && results.ai_analysis.key_indicators.length > 0 && (
                    <div style={{
                      padding: '1.5rem',
                      backgroundColor: colors.neutral.gray100,
                      borderRadius: '8px'
                    }}>
                      <h4 style={{ color: colors.primary.navy, marginBottom: '0.8rem' }}>
                        🔍 Key Indicators
                      </h4>
                      <ul style={{ paddingLeft: '1.5rem', margin: 0 }}>
                        {results.ai_analysis.key_indicators.map((indicator, index) => (
                          <li key={index} style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                            {indicator}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Anomalies Section - Show if present */}
              {results.anomalies && results.anomalies.length > 0 && (
                <div style={{ marginBottom: '2rem' }}>
                  <h3 style={{ color: colors.accent.red, marginBottom: '1rem' }}>
                    ⚠️ Detailed Anomalies ({results.anomalies.length})
                  </h3>
                  {results.anomalies.map((anomaly, index) => (
                    <div key={index} style={anomalyCardStyle(anomaly.severity)}>
                      <strong style={{ textTransform: 'uppercase' }}>
                        [{anomaly.severity}] {anomaly.type}:
                      </strong>
                      <br />
                      {anomaly.message}
                    </div>
                  ))}
                </div>
              )}

              <h3 style={{ color: colors.primary.navy, marginBottom: '1rem' }}>
                📄 Issuer Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Issuer:</strong> {results.extracted_data?.issuer || 'N/A'}</p>
                <p><strong>Serial Number:</strong> {results.extracted_data?.serial_number || 'N/A'}</p>
                <p><strong>Receipt Number:</strong> {results.extracted_data?.receipt_number || 'N/A'}</p>
              </div>

              <h3 style={{ color: colors.primary.navy, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Transaction Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Amount (Numeric):</strong>
                  <span style={{ color: colors.status.success, fontSize: '1.2rem', fontWeight: '600', marginLeft: '0.5rem' }}>
                    {results.extracted_data?.amount || 'N/A'}
                  </span>
                </p>
                <p><strong>Amount (Written):</strong> {results.extracted_data?.amount_in_words || 'N/A'}</p>
                <p><strong>Payee:</strong> {results.extracted_data?.payee || 'N/A'}</p>
                <p><strong>Purchaser:</strong> {results.extracted_data?.purchaser || 'N/A'}</p>
                <p><strong>Date:</strong> {results.extracted_data?.date || 'N/A'}</p>
                <p><strong>Location:</strong> {results.extracted_data?.location || 'N/A'}</p>
                <p><strong>Signature:</strong> {results.extracted_data?.signature || 'N/A'}</p>
              </div>

              <button
                style={{
                  ...buttonStyle,
                  backgroundColor: colors.primary.navy,
                  marginTop: '1.5rem',
                }}
                onClick={downloadJSON}
                onMouseEnter={(e) => e.target.style.backgroundColor = colors.primary.blue}
                onMouseLeave={(e) => e.target.style.backgroundColor = colors.primary.navy}
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

export default MoneyOrderAnalysis;
