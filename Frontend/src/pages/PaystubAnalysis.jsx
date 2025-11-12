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
  
  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginTop: '1rem',
  };
  
  const metricStyle = {
    backgroundColor: colors.background.main,
    padding: '1rem',
    borderRadius: '8px',
    textAlign: 'center',
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
          <h2 style={{ color: colors.primary.navy, marginBottom: '1.5rem' }}>
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
              <p style={{ color: colors.primary.blue, fontWeight: '500' }}>
                Drop the paystub here...
              </p>
            ) : (
              <div>
                <p style={{ color: colors.neutral.gray700, marginBottom: '0.5rem' }}>
                  Drop your paystub here or click to browse
                </p>
                <p style={{ color: colors.neutral.gray500, fontSize: '0.875rem' }}>
                  Paystubs Only - JPG, JPEG, PNG, PDF
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
              <p>Upload a paystub on the left to begin analysis</p>
            </div>
          )}
          
          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <div className="spin" style={{ fontSize: '3rem', color: colors.primary.blue }}>⚙️</div>
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing paystub...
              </p>
            </div>
          )}
          
          {results && (
            <div className="fade-in">
              <div style={confidenceStyle(results.confidence_score || 0)}>
                [{results.confidence_score >= 70 ? 'HIGH' : results.confidence_score >= 50 ? 'MEDIUM' : 'LOW'}] 
                Confidence: {results.confidence_score?.toFixed(1)}%
              </div>
              
              <h3 style={{ color: colors.primary.navy, marginBottom: '1rem' }}>
                Company & Employee Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Company:</strong> {results.company_name || 'N/A'}</p>
                <p><strong>Employee:</strong> {results.employee_name || 'N/A'}</p>
                <p><strong>Employee ID:</strong> {results.employee_id || 'N/A'}</p>
              </div>
              
              <h3 style={{ color: colors.primary.navy, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Pay Period Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Pay Period:</strong> {results.pay_period_start || 'N/A'} to {results.pay_period_end || 'N/A'}</p>
                <p><strong>Pay Date:</strong> {results.pay_date || 'N/A'}</p>
              </div>
              
              <h3 style={{ color: colors.primary.navy, marginBottom: '1rem', marginTop: '1.5rem' }}>
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
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.primary.navy }}>
                    ${results.ytd_gross || 'N/A'}
                  </div>
                </div>
                <div style={metricStyle}>
                  <div style={{ color: colors.neutral.gray600, fontSize: '0.875rem' }}>YTD Net</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.primary.navy }}>
                    ${results.ytd_net || 'N/A'}
                  </div>
                </div>
              </div>
              
              {results.federal_tax && (
                <>
                  <h3 style={{ color: colors.primary.navy, marginBottom: '1rem', marginTop: '1.5rem' }}>
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

export default PaystubAnalysis;

