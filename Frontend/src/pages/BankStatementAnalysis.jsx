import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeBankStatement } from '../services/api';
import { colors } from '../styles/colors';

const BankStatementAnalysis = () => {
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
      setError('Please upload a bank statement image first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await analyzeBankStatement(file);
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
    link.download = `bank_statement_analysis_${new Date().getTime()}.json`;
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

  const transactionRowStyle = (isDebit) => ({
    display: 'grid',
    gridTemplateColumns: '80px 1fr 120px 120px',
    gap: '1rem',
    padding: '0.75rem',
    backgroundColor: colors.background.card,
    borderRadius: '6px',
    marginBottom: '0.5rem',
    fontSize: '0.9rem',
    borderLeft: `3px solid ${isDebit ? colors.accent.red : colors.status.success}`,
  });

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Bank Statement Analysis</h1>
        <p>Extract and analyze bank statement details with transaction history</p>
      </div>

      <div style={gridStyle}>
        {/* Upload Section */}
        <div style={cardStyle}>
          <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
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
              ⚠️ Only upload bank statement documents (checking/savings account statements)
            </p>
          </div>

          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏦</div>
            {isDragActive ? (
              <p style={{ color: primary, fontWeight: '500' }}>
                Drop the bank statement here...
              </p>
            ) : (
              <div>
                <p style={{ color: colors.foreground, marginBottom: '0.5rem' }}>
                  Drop your bank statement here or click to browse
                </p>
                <p style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
                  Bank Statements Only - JPG, JPEG, PNG, PDF
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
                    alt="Bank statement preview"
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
            {loading ? 'Analyzing...' : 'Analyze Bank Statement'}
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
              <p>Upload a bank statement on the left to begin analysis</p>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '3rem' }}>
              <div className="spin" style={{
                fontSize: '3rem',
                color: primary,
              }}>⚙️</div>
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing bank statement...
              </p>
            </div>
          )}

          {results && (
            <div className="fade-in">
              {results.summary?.confidence && (
                <div style={confidenceStyle(results.summary.confidence)}>
                  [{results.summary.confidence >= 80 ? 'HIGH' : results.summary.confidence >= 60 ? 'MEDIUM' : 'LOW'}]
                  Confidence: {results.summary.confidence?.toFixed(1)}%
                </div>
              )}

              <h3 style={{ color: colors.foreground, marginBottom: '1rem' }}>
                Account Information
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Bank Name:</strong> {results.bank_name || 'N/A'}</p>
                <p><strong>Account Holder:</strong> {results.account_holder || 'N/A'}</p>
                <p><strong>Account Number:</strong> {results.account_number ? `****${results.account_number}` : 'N/A'}</p>
                <p><strong>Statement Period:</strong> {results.statement_period || 'N/A'}</p>
              </div>

              <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                Balance Summary
              </h3>
              <div style={resultCardStyle}>
                <p><strong>Opening Balance:</strong>
                  <span style={{ color: colors.foreground, fontSize: '1.1rem', fontWeight: '600', marginLeft: '0.5rem' }}>
                    {results.balances?.opening_balance || 'N/A'}
                  </span>
                </p>
                <p><strong>Ending Balance:</strong>
                  <span style={{ color: colors.status.success, fontSize: '1.1rem', fontWeight: '600', marginLeft: '0.5rem' }}>
                    {results.balances?.ending_balance || 'N/A'}
                  </span>
                </p>
                {results.balances?.available_balance && (
                  <p><strong>Available Balance:</strong> {results.balances.available_balance}</p>
                )}
                {results.balances?.current_balance && (
                  <p><strong>Current Balance:</strong> {results.balances.current_balance}</p>
                )}
              </div>

              {results.summary && (
                <>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                    Transaction Summary
                  </h3>
                  <div style={resultCardStyle}>
                    <p><strong>Total Transactions:</strong> {results.summary.transaction_count || 0}</p>
                    <p><strong>Total Credits:</strong>
                      <span style={{ color: colors.status.success, fontWeight: '600', marginLeft: '0.5rem' }}>
                        {results.summary.total_credits !== null && results.summary.total_credits !== undefined
                          ? `$${results.summary.total_credits.toFixed(2)}`
                          : 'N/A'}
                      </span>
                    </p>
                    <p><strong>Total Debits:</strong>
                      <span style={{ color: colors.accent.red, fontWeight: '600', marginLeft: '0.5rem' }}>
                        {results.summary.total_debits !== null && results.summary.total_debits !== undefined
                          ? `$${Math.abs(results.summary.total_debits).toFixed(2)}`
                          : 'N/A'}
                      </span>
                    </p>
                    <p><strong>Net Activity:</strong>
                      <span style={{
                        color: results.summary.net_activity >= 0 ? colors.status.success : colors.accent.red,
                        fontWeight: '600',
                        marginLeft: '0.5rem'
                      }}>
                        {results.summary.net_activity !== null && results.summary.net_activity !== undefined
                          ? `$${results.summary.net_activity.toFixed(2)}`
                          : 'N/A'}
                      </span>
                    </p>
                  </div>
                </>
              )}

              {results.transactions && results.transactions.length > 0 && (
                <>
                  <h3 style={{ color: colors.foreground, marginBottom: '1rem', marginTop: '1.5rem' }}>
                    Recent Transactions ({Math.min(results.transactions.length, 10)} shown)
                  </h3>
                  <div style={{
                    backgroundColor: colors.background.main,
                    padding: '1rem',
                    borderRadius: '8px',
                    maxHeight: '400px',
                    overflowY: 'auto'
                  }}>
                    {/* Header */}
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '80px 1fr 120px 120px',
                      gap: '1rem',
                      padding: '0.75rem',
                      fontWeight: '600',
                      color: colors.foreground,
                      borderBottom: `2px solid ${colors.neutral.gray300}`,
                      marginBottom: '0.5rem',
                      fontSize: '0.9rem',
                    }}>
                      <div>Date</div>
                      <div>Description</div>
                      <div>Amount</div>
                      <div>Balance</div>
                    </div>

                    {/* Transaction rows */}
                    {results.transactions.slice(0, 10).map((txn, index) => (
                      <div key={index} style={transactionRowStyle(txn.amount_value < 0)}>
                        <div style={{ fontWeight: '500' }}>{txn.date || 'N/A'}</div>
                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {txn.description || 'No description'}
                        </div>
                        <div style={{
                          fontWeight: '600',
                          color: txn.amount_value < 0 ? colors.accent.red : colors.status.success
                        }}>
                          {txn.amount || 'N/A'}
                        </div>
                        <div style={{ fontWeight: '500' }}>{txn.balance || 'N/A'}</div>
                      </div>
                    ))}
                  </div>

                  {results.transactions.length > 10 && (
                    <p style={{
                      color: colors.neutral.gray600,
                      fontSize: '0.875rem',
                      marginTop: '0.5rem',
                      fontStyle: 'italic'
                    }}>
                      + {results.transactions.length - 10} more transactions (download JSON for full list)
                    </p>
                  )}
                </>
              )}

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

export default BankStatementAnalysis;
