import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeBankStatement } from '../services/api';
import { colors } from '../styles/colors';
import { FaExclamationTriangle, FaUniversity, FaCog } from 'react-icons/fa';
import * as pdfjsLib from 'pdfjs-dist';
import BankStatementInsights from '../components/BankStatementInsights.jsx';

const buildBankStatementSections = (data) => ({
  'Account Information': [
    { label: 'Bank Name', value: data.bank_name || 'N/A' },
    { label: 'Account Holder', value: data.account_holder || 'N/A' },
    { label: 'Account Number', value: data.account_number || 'N/A' },
    { label: 'Statement Period', value: data.statement_period || 'N/A' },
  ],
  'Balance Summary': [
    { label: 'Opening Balance', value: data.balances?.opening_balance || 'N/A' },
    { label: 'Ending Balance', value: data.balances?.ending_balance || 'N/A' },
    { label: 'Available Balance', value: data.balances?.available_balance || 'N/A' },
    { label: 'Current Balance', value: data.balances?.current_balance || 'N/A' },
  ],
  'Transaction Summary': [
    { label: 'Total Transactions', value: data.summary?.transaction_count ?? 'N/A' },
    { label: 'Total Credits', value: data.summary?.total_credits ?? 'N/A' },
    { label: 'Total Debits', value: data.summary?.total_debits ?? 'N/A' },
    { label: 'Net Activity', value: data.summary?.net_activity ?? 'N/A' },
  ],
  'Transactions (sample)': (data.transactions || []).slice(0, 10).map((txn) => ({
    label: txn.date || 'Date',
    value: `${txn.description || 'Transaction'} | Amount: ${txn.amount || 'N/A'} | Balance: ${txn.balance || 'N/A'}`,
  })),
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

const buildBankCriticalFactors = (data = {}, anomalies = []) => {
  const factors = [];
  const addFactor = (text) => {
    if (text && !factors.includes(text)) {
      factors.push(text);
    }
  };

  const anomalyText = Array.isArray(anomalies) ? anomalies.join(' | ').toLowerCase() : '';
  const balances = data.balances || {};
  const summary = data.summary || {};
  const transactionCount = Array.isArray(data.transactions) ? data.transactions.length : summary.transaction_count;

  if (isMissing(data.bank_name)) {
    addFactor('Bank name missing — issuing institution cannot be confirmed.');
  }

  if (isMissing(data.account_holder)) {
    addFactor('Account holder absent — ownership cannot be proven.');
  }

  if (isMissing(data.account_number)) {
    addFactor('Account number unavailable — no way to reference the account.');
  }

  if (isMissing(data.statement_period)) {
    addFactor('Statement period missing — coverage window unclear.');
  }

  if (isMissing(balances.opening_balance) || isMissing(balances.ending_balance)) {
    addFactor('Opening/ending balances not captured — balance movement cannot be reconciled.');
  }

  if (!transactionCount || transactionCount < 3) {
    addFactor('Too few transactions detected — insufficient activity for validation.');
  }

  if (anomalyText.includes('balances inconsistent') || anomalyText.includes('amount mismatch')) {
    addFactor('Balance math inconsistent with net activity per ML review.');
  }

  if (anomalyText.includes('invalid date')) {
    addFactor('Statement or transaction dates flagged as invalid.');
  }

  if (anomalyText.includes('missing critical fields')) {
    addFactor('Multiple mandatory sections left blank according to ML model.');
  }

  return factors;
};

const BankStatementAnalysis = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('analyze');

  useEffect(() => {
    pdfjsLib.GlobalWorkerOptions.workerSrc = `${process.env.PUBLIC_URL}/pdf.worker.min.js`;
  }, []);

  const renderPdfPreview = async (fileObject) => {
    try {
      const fileReader = new FileReader();
      fileReader.onload = async (e) => {
        const typedArray = new Uint8Array(e.target.result);
        const pdf = await pdfjsLib.getDocument(typedArray).promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 2 });
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        await page.render({ canvasContext: context, viewport }).promise;
        setPreview(canvas.toDataURL('image/png'));
      };
      fileReader.readAsArrayBuffer(fileObject);
    } catch (err) {
      console.error('Error rendering PDF preview:', err);
      setPreview(null);
    }
  };

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
      } else if (selectedFile.type === 'application/pdf') {
        // Render PDF preview
        renderPdfPreview(selectedFile);
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
    setResults(null);

    try {
      const response = await analyzeBankStatement(file);
      console.log('✅ Bank statement analysis response received:', response);
      console.log('Response success:', response.success);
      console.log('Response has data:', !!response.data);

      if (response.success === false) {
        console.log('❌ Analysis failed - showing error');
        setError(response.error || response.message || 'Failed to analyze bank statement. Please try again.');
        setResults(null);
      } else if (response.success === true && response.data) {
        console.log('✅ Analysis successful - displaying results');
        // Process results to ensure ml_analysis and ai_analysis are properly extracted
        const processedResults = {
          ...response.data,
          // Extract ML analysis fields
          fraud_risk_score: response.data.ml_analysis?.fraud_risk_score || response.data.fraud_risk_score || 0,
          risk_level: response.data.ml_analysis?.risk_level || response.data.risk_level || 'UNKNOWN',
          model_confidence: response.data.ml_analysis?.model_confidence || response.data.model_confidence || 0,
          // Extract AI analysis fields with proper naming
          ai_recommendation: response.data.ai_analysis?.recommendation || response.data.ai_recommendation || 'UNKNOWN',
          ai_confidence: response.data.ai_analysis?.confidence_score || response.data.ai_confidence || 0,
          // Ensure ml_analysis and ai_analysis objects exist
          ml_analysis: response.data.ml_analysis || {},
          ai_analysis: response.data.ai_analysis || {},
        };
        setResults(processedResults);
        setError(null);
      } else {
        console.log('⚠️ Unexpected response format:', response);
        setError('Received unexpected response format from server');
        setResults(null);
      }
    } catch (err) {
      console.error('❌ Bank statement analysis error caught:', err);
      const errorMessage = err.error || err.message || err.response?.data?.error || err.response?.data?.message || 'Failed to analyze bank statement. Please try again.';
      setError(errorMessage);
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const downloadJSON = () => {
    const payload = results
      ? { ...results, extracted_sections: buildBankStatementSections(results) }
      : results;
    const dataStr = JSON.stringify(payload, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `bank_statement_analysis_${new Date().getTime()}.json`;
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
      'Bank Name',
      'Account Holder',
      'Account Number',
      'Statement Period',
      'Opening Balance',
      'Ending Balance',
      'Available Balance',
      'Total Transactions',
      'Total Credits',
      'Total Debits',
      'Net Activity',
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
      'Bank Statement',
      results.timestamp || new Date().toISOString(),
      results.bank_name || 'N/A',
      results.account_holder || 'N/A',
      results.account_number || 'N/A',
      results.statement_period || 'N/A',
      results.balances?.opening_balance || 'N/A',
      results.balances?.ending_balance || 'N/A',
      results.balances?.available_balance || 'N/A',
      results.summary?.transaction_count ?? 'N/A',
      results.summary?.total_credits ?? 'N/A',
      results.summary?.total_debits ?? 'N/A',
      results.summary?.net_activity ?? 'N/A',
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
    link.download = `bank_statement_analysis_${new Date().getTime()}.csv`;
    link.click();
  };

  const emphasizeAnomaly = (text) => {
    if (!text) return text;
    const lower = text.toLowerCase();
    const highlightKeywords = ['missing', 'invalid', 'mismatch', 'critical'];
    const shouldEmphasize = highlightKeywords.some((keyword) => lower.includes(keyword));
    return shouldEmphasize ? <strong>{text}</strong> : text;
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

  const infoCardStyle = {
    backgroundColor: colors.card,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    marginBottom: '1rem',
    color: colors.foreground,
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

  const analysisData = results;
  const mlAnalysis = analysisData?.ml_analysis || {};
  const aiAnalysis = analysisData?.ai_analysis || {};
  const anomalies = analysisData?.anomalies || [];
  const criticalFactors = analysisData ? buildBankCriticalFactors(analysisData, anomalies) : [];

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
          Bank Statement <span style={{ color: primary }}>Analysis</span>
        </h1>
        <p>Extract and analyze bank statement details with transaction history</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', marginBottom: '0', borderBottom: `1px solid ${colors.border}` }}>
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
            Upload Bank Statement
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
              <span>Only upload bank statement documents (checking/savings account statements)</span>
            </div>
          </div>

          <div {...getRootProps()} style={dropzoneStyle}>
            <input {...getInputProps()} />
            <FaUniversity style={{ fontSize: '3rem', marginBottom: '1rem', color: colors.foreground }} />
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
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      border: `1px solid ${colors.border}`
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
              <FaCog className="spin" style={{
                fontSize: '3rem',
                color: primary,
              }} />
              <p style={{ marginTop: '1rem', color: colors.neutral.gray600 }}>
                Analyzing bank statement...
              </p>
            </div>
          )}

          {analysisData && (
            <div className="fade-in">
              {/* Risk Cards */}
              {(() => {
                const fraudRiskPercent = toPercent(analysisData.fraud_risk_score ?? mlAnalysis.fraud_risk_score);
                const modelConfidencePercent = toPercent(analysisData.model_confidence ?? mlAnalysis.model_confidence);
                const aiConfidencePercent = toPercent(analysisData.ai_confidence ?? aiAnalysis.confidence);
                const riskLevel = mlAnalysis.risk_level || analysisData.risk_level || 'UNKNOWN';
                const aiRecommendation = (analysisData.ai_recommendation || aiAnalysis.recommendation || 'UNKNOWN').toUpperCase();
                const aiColor = aiRecommendation === 'APPROVE'
                  ? colors.status.success
                  : aiRecommendation === 'REJECT'
                    ? primary
                    : colors.status.warning;

                return (
                  <>
                    <div style={{
                      ...resultCardStyle,
                      backgroundColor: `${primary}20`,
                      borderLeft: `4px solid ${primary}`
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

                    <div style={{
                      ...resultCardStyle,
                      backgroundColor: `${colors.status.success}20`,
                      borderLeft: `4px solid ${colors.status.success}`
                    }}>
                      <div style={{ fontSize: '0.9rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
                        Model Confidence
                      </div>
                      <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: colors.status.success }}>
                        {modelConfidencePercent.toFixed(1)}%
                      </div>
                    </div>

                    <div style={{
                      ...resultCardStyle,
                      backgroundColor: `${aiColor}20`,
                      borderLeft: `4px solid ${aiColor}`
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

              {/* Fraud Type Card - Primary Fraud Type with Customer History as Reasons */}
              {(() => {
                // Hide if recommendation is APPROVE
                const aiRecommendation = (analysisData.ai_recommendation || aiAnalysis.recommendation || 'UNKNOWN').toUpperCase();
                if (aiRecommendation === 'APPROVE') {
                  return false;
                }
                
                // Check if we have fraud types or customer info to display
                // Check multiple locations for fraud_types (backend returns at top level and in nested data)
                const fraudTypes = analysisData.fraud_types || 
                                  analysisData.data?.fraud_types || 
                                  mlAnalysis.fraud_types ||
                                  analysisData.data?.ml_analysis?.fraud_types || 
                                  (analysisData.fraud_type ? [analysisData.fraud_type] : []) || // Also check singular fraud_type
                                  [];
                const customerInfo = analysisData.customer_info || analysisData.data?.customer_info || {};
                const escalateCount = customerInfo.escalate_count || 0;
                const fraudCount = customerInfo.fraud_count || 0;
                const isNewCustomer = !customerInfo.customer_id;
                const customerStatus = isNewCustomer ? 'New Customer' : 'Repeat Customer';
                
                // CRITICAL: Hide fraud type card for new customers (matches paystub behavior)
                // EXCEPTION: If recommendation is REJECT, it means this is a repeat customer (new customers always get ESCALATE)
                // So show fraud types for REJECT even if customer_id is missing
                if (isNewCustomer && aiRecommendation !== 'REJECT') {
                  return false;
                }
                
                // CRITICAL: Only show card if LLM provided fraud_types (NO FALLBACKS)
                // Must have actual fraud_types from LLM (ai_analysis.fraud_types)
                const hasLLMFraudTypes = (aiAnalysis.fraud_types && aiAnalysis.fraud_types.length > 0) ||
                                        (analysisData.fraud_types && analysisData.fraud_types.length > 0) ||
                                        (analysisData.fraud_type && analysisData.fraud_type !== null) ||
                                        (analysisData.fraud_type_label && analysisData.fraud_type_label !== null);
                
                // Only show if LLM provided fraud types - no fallbacks based on customer history or recommendation
                return hasLLMFraudTypes;
              })() ? (
                (() => {
                  // Check multiple locations for fraud_types (backend returns at top level and in nested data)
                  const fraudTypes = analysisData.fraud_types || 
                                    analysisData.data?.fraud_types || 
                                    mlAnalysis.fraud_types ||
                                    analysisData.data?.ml_analysis?.fraud_types || 
                                    (analysisData.fraud_type ? [analysisData.fraud_type] : []) || // Also check singular fraud_type
                                    [];
                  const customerInfo = analysisData.customer_info || analysisData.data?.customer_info || {};
                  const escalateCount = customerInfo.escalate_count || 0;
                  const fraudCount = customerInfo.fraud_count || 0;
                  const isNewCustomer = !customerInfo.customer_id;
                  const customerStatus = isNewCustomer ? 'New Customer' : 'Repeat Customer';
                  
                  // Get fraud explanations from multiple possible locations
                  const fraudExplanations = analysisData.fraud_explanations ||
                                            analysisData.data?.fraud_explanations ||
                                            aiAnalysis.fraud_explanations ||
                                            analysisData.data?.ai_analysis?.fraud_explanations || [];
                  
                  // Get primary fraud type - ONLY from LLM (NO FALLBACKS)
                  // Must come from ai_analysis.fraud_types or fraud_type_label
                  let primaryFraudType = null;
                  if (analysisData.fraud_type_label) {
                    // Use human-readable label from backend (comes from LLM)
                    primaryFraudType = analysisData.fraud_type_label;
                  } else if (aiAnalysis.fraud_types && aiAnalysis.fraud_types.length > 0) {
                    // Use fraud_types from LLM (ai_analysis)
                    primaryFraudType = aiAnalysis.fraud_types[0].replace(/_/g, ' ');
                  } else if (analysisData.fraud_types && analysisData.fraud_types.length > 0) {
                    // Use fraud_types from top level (comes from LLM)
                    primaryFraudType = analysisData.fraud_types[0].replace(/_/g, ' ');
                  } else if (analysisData.fraud_type) {
                    // Use singular fraud_type (comes from LLM)
                    primaryFraudType = analysisData.fraud_type.replace(/_/g, ' ');
                  } else if (fraudExplanations.length > 0 && fraudExplanations[0].type) {
                    // Use fraud explanation type (comes from LLM)
                    primaryFraudType = fraudExplanations[0].type.replace(/_/g, ' ');
                  }
                  // NO FALLBACKS - if LLM didn't provide fraud type, primaryFraudType remains null
                  
                  // ONLY use fraud explanations from LLM (NO FALLBACKS)
                  // Must come from ai_analysis.fraud_explanations
                  let displayReasons = [];
                  
                  // Get fraud explanations ONLY from LLM (ai_analysis.fraud_explanations)
                  const llmFraudExplanations = aiAnalysis.fraud_explanations || 
                                               analysisData.fraud_explanations || 
                                               analysisData.data?.fraud_explanations || 
                                               analysisData.data?.ai_analysis?.fraud_explanations || [];
                  
                  if (llmFraudExplanations && llmFraudExplanations.length > 0) {
                    // Find explanations matching the primary fraud type
                    if (primaryFraudType) {
                      const primaryFraudTypeNormalized = primaryFraudType.replace(/\s+/g, '_').toUpperCase();
                      const matchingExplanations = llmFraudExplanations.filter(exp => {
                        const expTypeNormalized = exp.type?.replace(/\s+/g, '_').toUpperCase();
                        return expTypeNormalized === primaryFraudTypeNormalized;
                      });
                      
                      // Use matching explanations if found
                      if (matchingExplanations.length > 0) {
                        matchingExplanations.forEach(exp => {
                          if (exp.reasons && Array.isArray(exp.reasons) && exp.reasons.length > 0) {
                            displayReasons.push(...exp.reasons);
                          }
                        });
                      } else {
                        // If no matching explanations, use first explanation's reasons
                        llmFraudExplanations.forEach(exp => {
                          if (exp.reasons && Array.isArray(exp.reasons) && exp.reasons.length > 0) {
                            displayReasons.push(...exp.reasons);
                          }
                        });
                      }
                    } else {
                      // No primary fraud type, use all explanations
                      llmFraudExplanations.forEach(exp => {
                        if (exp.reasons && Array.isArray(exp.reasons) && exp.reasons.length > 0) {
                          displayReasons.push(...exp.reasons);
                        }
                      });
                    }
                  }
                  
                  // NO FALLBACKS - if LLM didn't provide explanations, displayReasons remains empty
                  // If empty, we'll still show the fraud type but no explanations
                  
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
                      {primaryFraudType ? (
                        <div style={{
                          fontSize: '1.5rem',
                          fontWeight: 'bold',
                          color: primary,
                          marginBottom: '1rem',
                        }}>
                          {primaryFraudType}
                        </div>
                      ) : null}
                      {displayReasons.length > 0 ? (
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
                      ) : null}
                    </div>
                  );
                })()
              ) : null}

              {/* Actionable Recommendations Card */}
              {(() => {
                const aiRecommendation = (analysisData.ai_recommendation || aiAnalysis.recommendation || 'UNKNOWN').toUpperCase();
                const customerInfo = analysisData.customer_info || analysisData.data?.customer_info || {};
                const isNewCustomer = !customerInfo.customer_id;
                
                // CRITICAL: Hide actionable recommendations for new customers (matches paystub behavior)
                // EXCEPTION: If recommendation is REJECT, it means this is a repeat customer (new customers always get ESCALATE)
                // So show recommendations for REJECT even if customer_id is missing
                if (isNewCustomer && aiRecommendation !== 'REJECT') {
                  return false;
                }
                
                return aiRecommendation !== 'APPROVE' && aiAnalysis.actionable_recommendations && aiAnalysis.actionable_recommendations.length > 0;
              })() && (
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

              <div style={{
                ...infoCardStyle,
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
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <BankStatementInsights />
      )}
    </div>
  );
};

export default BankStatementAnalysis;
