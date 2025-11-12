import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeStatement } from '../services/api';
import { colors } from '../styles/colors';

const StatementAnalysis = () => {
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
      setError('Please upload a bank statement first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await analyzeStatement(file);
      setResults(response.data);
    } catch (err) {
      setError(err.error || 'Failed to analyze bank statement. Please try again.');
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
    link.download = `statement_analysis_${new Date().getTime()}.json`;
    link.click();
  };

  const downloadCSV = () => {
    if (!results || !results.transactions || results.transactions.length === 0) {
      return;
    }

    const transactions = results.transactions;
    const headers = ['Date', 'Description', 'Amount', 'Balance'];
    const rows = transactions.map(t => [
      t.date || '',
      `"${(t.description || '').replace(/"/g, '""')}"`,
      t.amount || '',
      t.balance || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `statement_transactions_${new Date().getTime()}.csv`;
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
    border: 'none',
  };

  const resultCardStyle = {
    backgroundColor: colors.background.main,
    padding: '1.5rem',
    borderRadius: '8px',
    borderLeft: `4px solid ${colors.primary.blue}`,
    marginBottom: '1rem',
  };

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    marginTop: '1rem',
    fontSize: '0.9rem',
  };

  const thStyle = {
    backgroundColor: colors.primary.navy,
    color: colors.neutral.white,
    padding: '0.75rem',
    textAlign: 'left',
    fontWeight: '600',
  };

  const tdStyle = {
    padding: '0.75rem',
    borderBottom: `1px solid ${colors.neutral.gray200}`,
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
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Bank Statement Analysis</h1>
      </div>

      <div style={gridStyle}>
        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: colors.primary.navy, marginBottom: '1.5rem' }}>
            Upload Bank Statement
          </h2>

          <div style={{
            backgroundColor: '#FFF3CD',
            border: '1px solid #FFC107',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1rem',
          }}>
            <p style={{ color: '#856404', fontSize: '0.875rem', margin: 0, fontWeight: '500' }}>
              ⚠️ Upload bank statements (checking, savings, credit card statements)
            </p>
          </div>

          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
            {isDragActive ? (
              <p style={{ color: colors.primary.blue, fontWeight: '500' }}>
                Drop the statement here...
              </p>
            ) : (
              <div>
                <p style={{ color: colors.neutral.gray700, marginBottom: '0.5rem' }}>
                  Drop your bank statement here or click to browse
                </p>
                <p style={{ color: colors.neutral.gray500, fontSize: '0.875rem' }}>
                  Supports JPG, JPEG, PNG, PDF
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
                    alt="Statement preview"
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
            {loading ? 'Analyzing...' : 'Analyze Statement'}
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
              <p>Upload a bank statement to begin analysis</p>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <div className="spin" style={{
                fontSize: '3rem',
                color: colors.primary.blue,
              }}>⚙️</div>
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing statement...
              </p>
            </div>
          )}

          {results && (
            <div className="fade-in" style={{ maxHeight: '800px', overflowY: 'auto' }}>
              {results.summary && (
                <div style={confidenceStyle(results.summary.confidence || 0)}>
                  Confidence: {results.summary.confidence?.toFixed(1)}%
                </div>
              )}

              {/* Summary Metrics */}
              {results.summary && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                  <div style={resultCardStyle}>
                    <p style={{ fontSize: '0.875rem', color: colors.neutral.gray600, marginBottom: '0.25rem' }}>
                      Total Transactions
                    </p>
                    <p style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.primary.navy, margin: 0 }}>
                      {results.summary.transaction_count || 0}
                    </p>
                  </div>
                  <div style={resultCardStyle}>
                    <p style={{ fontSize: '0.875rem', color: colors.neutral.gray600, marginBottom: '0.25rem' }}>
                      Net Activity
                    </p>
                    <p style={{ fontSize: '1.5rem', fontWeight: '600', color: colors.status.success, margin: 0 }}>
                      ${results.summary.net_activity?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                </div>
              )}

              <h3 style={{ color: colors.primary.navy, marginBottom: '1rem' }}>
                Statement Overview
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Bank Name:</strong> {results.bank_name || 'N/A'}</p>
                <p><strong>Account Holder:</strong> {results.account_holder || 'N/A'}</p>
                <p><strong>Account Number:</strong> {results.account_number || 'N/A'}</p>
                <p><strong>Statement Period:</strong> {results.statement_period || 'N/A'}</p>
              </div>

              <h3 style={{ color: colors.primary.navy, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Balance Summary
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Opening Balance:</strong> {results.balances?.opening_balance || 'N/A'}</p>
                <p><strong>Ending Balance:</strong> {results.balances?.ending_balance || 'N/A'}</p>
                {results.balances?.available_balance && (
                  <p><strong>Available Balance:</strong> {results.balances.available_balance}</p>
                )}
                {results.balances?.current_balance && (
                  <p><strong>Current Balance:</strong> {results.balances.current_balance}</p>
                )}
              </div>

              {results.transactions && results.transactions.length > 0 && (
                <>
                  <h3 style={{ color: colors.primary.navy, marginBottom: '1rem', marginTop: '1.5rem' }}>
                    Transactions ({results.transactions.length})
                  </h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Date</th>
                          <th style={thStyle}>Description</th>
                          <th style={thStyle}>Amount</th>
                          <th style={thStyle}>Balance</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.transactions.slice(0, 20).map((transaction, index) => (
                          <tr key={index}>
                            <td style={tdStyle}>{transaction.date || 'N/A'}</td>
                            <td style={tdStyle}>{transaction.description || 'N/A'}</td>
                            <td style={{
                              ...tdStyle,
                              color: transaction.amount_value < 0 ? colors.accent.red : colors.status.success,
                              fontWeight: '500'
                            }}>
                              {transaction.amount || 'N/A'}
                            </td>
                            <td style={tdStyle}>{transaction.balance || 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {results.transactions.length > 20 && (
                      <p style={{ textAlign: 'center', marginTop: '1rem', color: colors.neutral.gray600, fontSize: '0.875rem' }}>
                        Showing first 20 of {results.transactions.length} transactions. Download CSV for complete data.
                      </p>
                    )}
                  </div>

                  <button
                    style={{
                      ...buttonStyle,
                      backgroundColor: colors.status.success,
                      marginTop: '1rem',
                    }}
                    onClick={downloadCSV}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#1e7e34'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = colors.status.success}
                  >
                    📥 Download Transactions CSV
                  </button>
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
                📥 Download Full Results (JSON)
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatementAnalysis;
