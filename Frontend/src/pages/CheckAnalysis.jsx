import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeCheck } from '../services/api';
import { colors } from '../styles/colors';

const CheckAnalysis = () => {
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
      setError('Please upload a check image first');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await analyzeCheck(file);
      setResults(response.data);
    } catch (err) {
      setError(err.error || 'Failed to analyze check. Please try again.');
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
    link.download = `check_analysis_${new Date().getTime()}.json`;
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
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Check Analysis</h1>
        <p>Analyze bank checks for fraud detection</p>
      </div>
      
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
            <p style={{ color: '#856404', fontSize: '0.875rem', margin: 0, fontWeight: '500' }}>
              ⚠️ Only upload bank check images (personal or business checks)
            </p>
          </div>
          
          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏦</div>
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
              <div className="spin" style={{ 
                fontSize: '3rem',
                color: primary,
              }}>⚙️</div>
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing check...
              </p>
            </div>
          )}
          
          {results && (
            <div className="fade-in">
              <div style={confidenceStyle(results.confidence_score || 0)}>
                [{results.confidence_score >= 80 ? 'HIGH' : results.confidence_score >= 60 ? 'MEDIUM' : 'LOW'}] 
                Confidence: {results.confidence_score?.toFixed(1)}%
              </div>
              
              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
                Bank Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Bank Name:</strong> {results.bank_name || 'N/A'}</p>
                <p><strong>Bank Type:</strong> {results.bank_type || 'N/A'}</p>
                {results.country && <p><strong>Country:</strong> {results.country}</p>}
                {results.check_type && <p><strong>Check Type:</strong> {results.check_type}</p>}
              </div>
              
              <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Payment Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Payee Name:</strong> {results.payee_name || 'N/A'}</p>
                <p><strong>Amount:</strong> 
                  <span style={{ color: colors.status.success, fontSize: '1.2rem', fontWeight: '600', marginLeft: '0.5rem' }}>
                    {results.currency} {results.amount_numeric || 'N/A'}
                  </span>
                </p>
                <p><strong>Amount in Words:</strong> {results.amount_words || 'N/A'}</p>
                <p><strong>Date:</strong> {results.date || 'N/A'}</p>
              </div>
              
              <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Account & Check Details
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Check Number:</strong> {results.check_number || 'N/A'}</p>
                <p><strong>Account Number:</strong> {results.account_number || 'N/A'}</p>
                {results.routing_number && <p><strong>Routing Number:</strong> {results.routing_number}</p>}
                {results.micr_code && <p><strong>MICR Code:</strong> {results.micr_code}</p>}
                {results.ifsc_code && <p><strong>IFSC Code:</strong> {results.ifsc_code}</p>}
              </div>
              
              <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Verification
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Signature Detected:</strong> {results.signature_detected ? 'Yes' : 'No'}</p>
                <p><strong>Extraction Time:</strong> {results.extraction_timestamp}</p>
              </div>
              
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

export default CheckAnalysis;

