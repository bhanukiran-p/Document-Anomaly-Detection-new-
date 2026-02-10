// Use jsPDF from CDN (loaded in index.html)
// The CDN exposes jsPDF as window.jspdf.jsPDF
const getJsPDF = () => {
  if (typeof window !== 'undefined' && window.jspdf && window.jspdf.jsPDF) {
    return window.jspdf.jsPDF;
  }
  throw new Error('jsPDF not loaded. Please ensure the CDN script is included in index.html');
};

// Helper function to format percentage
const formatPercent = (value) => {
  if (value === null || value === undefined) return 'N/A';
  const num = Number(value);
  if (!Number.isFinite(num)) return 'N/A';
  const percent = num <= 1 ? num * 100 : num;
  return `${Math.max(0, Math.min(100, percent)).toFixed(1)}%`;
};

// Helper function to format date
const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleString();
  } catch {
    return dateStr;
  }
};

// Helper function to get risk color
const getRiskColor = (riskLevel) => {
  const level = String(riskLevel || '').toUpperCase();
  if (level.includes('HIGH') || level.includes('CRITICAL')) return [231, 76, 60]; // Red
  if (level.includes('MEDIUM') || level.includes('MODERATE')) return [241, 196, 15]; // Yellow
  return [46, 204, 113]; // Green
};

// Helper function to add header
const addHeader = (doc, title, timestamp) => {
  doc.setFillColor(15, 24, 32);
  doc.rect(0, 0, 210, 40, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(20);
  doc.setFont('helvetica', 'bold');
  doc.text(title, 15, 20);
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(`Analysis Report | Generated: ${formatDate(timestamp)}`, 15, 32);
  doc.setTextColor(0, 0, 0);
  return 45; // Return Y position after header
};

// Helper function to add section header
const addSectionHeader = (doc, y, text) => {
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(15, 24, 32);
  doc.text(text, 15, y);
  doc.setDrawColor(200, 200, 200);
  doc.line(15, y + 2, 195, y + 2);
  return y + 8;
};

// Helper function to add key-value pair
const addKeyValue = (doc, y, key, value, maxWidth = 180) => {
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text(key + ':', 15, y);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);
  const lines = doc.splitTextToSize(String(value || 'N/A'), maxWidth);
  doc.text(lines, 80, y);
  return y + (lines.length * 5) + 3;
};

// Helper function to add table
const addTable = (doc, y, headers, rows, colWidths) => {
  const startY = y;
  const rowHeight = 8;
  const headerHeight = 10;
  
  // Header
  doc.setFillColor(240, 240, 240);
  doc.rect(15, startY, 180, headerHeight, 'F');
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0, 0, 0);
  
  let xPos = 15;
  headers.forEach((header, i) => {
    doc.text(header, xPos + 2, startY + 7);
    xPos += colWidths[i];
  });
  
  // Rows
  doc.setFont('helvetica', 'normal');
  let currentY = startY + headerHeight;
  
  rows.forEach((row, rowIdx) => {
    if (currentY + rowHeight > 280) {
      doc.addPage();
      currentY = 20;
    }
    
    xPos = 15;
    row.forEach((cell, colIdx) => {
      const cellText = doc.splitTextToSize(String(cell || ''), colWidths[colIdx] - 4);
      doc.text(cellText, xPos + 2, currentY + 5);
      xPos += colWidths[colIdx];
    });
    
    doc.setDrawColor(220, 220, 220);
    doc.line(15, currentY + rowHeight, 195, currentY + rowHeight);
    currentY += rowHeight;
  });
  
  return currentY + 5;
};

// Helper function to add summary box
const addSummaryBox = (doc, y, riskScore, riskLevel, recommendation, confidence) => {
  const boxHeight = 40;
  const riskColor = getRiskColor(riskLevel);
  
  // Background box
  doc.setFillColor(riskColor[0], riskColor[1], riskColor[2]);
  doc.setGlobalAlpha(0.1);
  doc.rect(15, y, 180, boxHeight, 'F');
  doc.setGlobalAlpha(1.0);
  
  // Border
  doc.setDrawColor(riskColor[0], riskColor[1], riskColor[2]);
  doc.setLineWidth(2);
  doc.rect(15, y, 180, boxHeight);
  doc.setLineWidth(0.5);
  
  // Content
  doc.setFontSize(12);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(riskColor[0], riskColor[1], riskColor[2]);
  doc.text('Executive Summary', 20, y + 8);
  
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);
  
  let currentY = y + 18;
  currentY = addKeyValue(doc, currentY, 'Fraud Risk Score', formatPercent(riskScore), 100);
  currentY = addKeyValue(doc, currentY, 'Risk Level', String(riskLevel || 'UNKNOWN').toUpperCase(), 100);
  currentY = addKeyValue(doc, currentY, 'AI Recommendation', String(recommendation || 'UNKNOWN').toUpperCase(), 100);
  addKeyValue(doc, currentY, 'Confidence', formatPercent(confidence), 100);
  
  return y + boxHeight + 10;
};

// Generate Bank Statement PDF
export const generateBankStatementPDF = (results) => {
  const jsPDF = getJsPDF();
  const doc = new jsPDF();
  let y = addHeader(doc, 'Bank Statement Analysis Report', results.timestamp || new Date().toISOString());
  
  const mlAnalysis = results.ml_analysis || {};
  const aiAnalysis = results.ai_analysis || {};
  const fraudRiskScore = results.fraud_risk_score ?? mlAnalysis.fraud_risk_score;
  const riskLevel = results.risk_level || mlAnalysis.risk_level || 'UNKNOWN';
  const recommendation = results.ai_recommendation || aiAnalysis.recommendation || 'UNKNOWN';
  const confidence = results.ai_confidence ?? aiAnalysis.confidence_score ?? aiAnalysis.confidence;
  
  // Executive Summary
  y = addSummaryBox(doc, y, fraudRiskScore, riskLevel, recommendation, confidence);
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Account Information
  y = addSectionHeader(doc, y, 'Account Information');
  y = addKeyValue(doc, y, 'Bank Name', results.bank_name);
  y = addKeyValue(doc, y, 'Account Holder', results.account_holder || results.account_holder_name);
  y = addKeyValue(doc, y, 'Account Number', results.account_number);
  y = addKeyValue(doc, y, 'Statement Period', results.statement_period || results.statement_period_start_date);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Balance Summary
  y = addSectionHeader(doc, y, 'Balance Summary');
  const balances = results.balances || {};
  y = addKeyValue(doc, y, 'Opening Balance', balances.opening_balance);
  y = addKeyValue(doc, y, 'Ending Balance', balances.ending_balance);
  y = addKeyValue(doc, y, 'Available Balance', balances.available_balance);
  y = addKeyValue(doc, y, 'Current Balance', balances.current_balance);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Transaction Summary
  y = addSectionHeader(doc, y, 'Transaction Summary');
  const summary = results.summary || {};
  y = addKeyValue(doc, y, 'Total Transactions', summary.transaction_count);
  y = addKeyValue(doc, y, 'Total Credits', summary.total_credits);
  y = addKeyValue(doc, y, 'Total Debits', summary.total_debits);
  y = addKeyValue(doc, y, 'Net Activity', summary.net_activity);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // ML Analysis Details
  y = addSectionHeader(doc, y, 'ML Analysis Details');
  y = addKeyValue(doc, y, 'Random Forest Score', formatPercent(mlAnalysis.rf_score));
  y = addKeyValue(doc, y, 'XGBoost Score', formatPercent(mlAnalysis.xgb_score));
  y = addKeyValue(doc, y, 'Model Confidence', formatPercent(results.model_confidence ?? mlAnalysis.model_confidence));
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // AI Analysis
  if (aiAnalysis.reasoning || aiAnalysis.summary) {
    y = addSectionHeader(doc, y, 'AI Analysis');
    if (aiAnalysis.summary) {
      const summaryLines = doc.splitTextToSize(aiAnalysis.summary, 180);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(summaryLines, 15, y);
      y += summaryLines.length * 5 + 5;
    }
    if (aiAnalysis.reasoning && Array.isArray(aiAnalysis.reasoning)) {
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.text('Reasoning:', 15, y);
      y += 5;
      doc.setFont('helvetica', 'normal');
      aiAnalysis.reasoning.forEach((reason) => {
        const reasonLines = doc.splitTextToSize(`• ${reason}`, 180);
        doc.text(reasonLines, 15, y);
        y += reasonLines.length * 5;
      });
    }
    y += 5;
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Fraud Types & Explanations
  if (results.fraud_types && results.fraud_types.length > 0) {
    y = addSectionHeader(doc, y, 'Fraud Types Detected');
    results.fraud_types.forEach((fraudType) => {
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(231, 76, 60);
      doc.text(`• ${fraudType}`, 15, y);
      y += 6;
      
      if (results.fraud_explanations && Array.isArray(results.fraud_explanations)) {
        const explanation = results.fraud_explanations.find(exp => exp.type === fraudType);
        if (explanation && explanation.reasons) {
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(0, 0, 0);
          doc.setFontSize(9);
          explanation.reasons.forEach((reason) => {
            const reasonLines = doc.splitTextToSize(`  - ${reason}`, 175);
            doc.text(reasonLines, 20, y);
            y += reasonLines.length * 4;
          });
        }
      }
      y += 2;
    });
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Anomalies
  if (results.anomalies && results.anomalies.length > 0) {
    y = addSectionHeader(doc, y, 'Detected Anomalies & Issues');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    results.anomalies.forEach((anomaly) => {
      const anomalyLines = doc.splitTextToSize(`• ${anomaly}`, 180);
      doc.text(anomalyLines, 15, y);
      y += anomalyLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Actionable Recommendations
  if (aiAnalysis.actionable_recommendations && aiAnalysis.actionable_recommendations.length > 0) {
    if (y > 250) {
      doc.addPage();
      y = 20;
    }
    y = addSectionHeader(doc, y, 'Actionable Recommendations');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    aiAnalysis.actionable_recommendations.forEach((rec) => {
      const recLines = doc.splitTextToSize(`• ${rec}`, 180);
      doc.text(recLines, 15, y);
      y += recLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Footer
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(128, 128, 128);
    doc.text(`Page ${i} of ${pageCount}`, 195, 290, { align: 'right' });
    doc.text('Document Anomaly Detection System', 15, 290);
  }
  
  return doc;
};

// Generate Check PDF
export const generateCheckPDF = (results) => {
  const jsPDF = getJsPDF();
  const doc = new jsPDF();
  let y = addHeader(doc, 'Check Analysis Report', results.timestamp || new Date().toISOString());
  
  const mlAnalysis = results.ml_analysis || {};
  const aiAnalysis = results.ai_analysis || {};
  const fraudRiskScore = results.fraud_risk_score ?? mlAnalysis.fraud_risk_score;
  const riskLevel = results.risk_level || mlAnalysis.risk_level || 'UNKNOWN';
  const recommendation = results.ai_recommendation || aiAnalysis.recommendation || 'UNKNOWN';
  const confidence = results.ai_confidence ?? aiAnalysis.confidence_score ?? aiAnalysis.confidence;
  
  // Executive Summary
  y = addSummaryBox(doc, y, fraudRiskScore, riskLevel, recommendation, confidence);
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Bank Information
  y = addSectionHeader(doc, y, 'Bank Information');
  y = addKeyValue(doc, y, 'Bank Name', results.bank_name);
  y = addKeyValue(doc, y, 'Bank Type', results.bank_type);
  y = addKeyValue(doc, y, 'Country', results.country);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Payment Information
  y = addSectionHeader(doc, y, 'Payment Information');
  y = addKeyValue(doc, y, 'Payee Name', results.payee_name);
  y = addKeyValue(doc, y, 'Payer Name', results.payer_name);
  y = addKeyValue(doc, y, 'Amount', results.amount);
  y = addKeyValue(doc, y, 'Amount in Words', results.amount_words || results.amount_in_words);
  y = addKeyValue(doc, y, 'Date', results.date);
  y = addKeyValue(doc, y, 'Memo', results.memo);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Account & Check Details
  y = addSectionHeader(doc, y, 'Account & Check Details');
  y = addKeyValue(doc, y, 'Check Number', results.check_number);
  y = addKeyValue(doc, y, 'Account Number', results.account_number);
  y = addKeyValue(doc, y, 'Routing Number', results.routing_number);
  y = addKeyValue(doc, y, 'Signature Detected', results.signature_detected ? 'Yes' : 'No');
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // ML Analysis Details
  y = addSectionHeader(doc, y, 'ML Analysis Details');
  y = addKeyValue(doc, y, 'Random Forest Score', formatPercent(mlAnalysis.rf_score));
  y = addKeyValue(doc, y, 'XGBoost Score', formatPercent(mlAnalysis.xgb_score));
  y = addKeyValue(doc, y, 'Model Confidence', formatPercent(results.model_confidence ?? mlAnalysis.model_confidence));
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // AI Analysis
  if (aiAnalysis.reasoning || aiAnalysis.summary) {
    y = addSectionHeader(doc, y, 'AI Analysis');
    if (aiAnalysis.summary) {
      const summaryLines = doc.splitTextToSize(aiAnalysis.summary, 180);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(summaryLines, 15, y);
      y += summaryLines.length * 5 + 5;
    }
    if (aiAnalysis.reasoning && Array.isArray(aiAnalysis.reasoning)) {
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.text('Reasoning:', 15, y);
      y += 5;
      doc.setFont('helvetica', 'normal');
      aiAnalysis.reasoning.forEach((reason) => {
        const reasonLines = doc.splitTextToSize(`• ${reason}`, 180);
        doc.text(reasonLines, 15, y);
        y += reasonLines.length * 5;
      });
    }
    y += 5;
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Fraud Types & Explanations
  if (results.fraud_types && results.fraud_types.length > 0) {
    y = addSectionHeader(doc, y, 'Fraud Types Detected');
    results.fraud_types.forEach((fraudType) => {
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(231, 76, 60);
      doc.text(`• ${fraudType}`, 15, y);
      y += 6;
      
      if (results.fraud_explanations && Array.isArray(results.fraud_explanations)) {
        const explanation = results.fraud_explanations.find(exp => exp.type === fraudType);
        if (explanation && explanation.reasons) {
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(0, 0, 0);
          doc.setFontSize(9);
          explanation.reasons.forEach((reason) => {
            const reasonLines = doc.splitTextToSize(`  - ${reason}`, 175);
            doc.text(reasonLines, 20, y);
            y += reasonLines.length * 4;
          });
        }
      }
      y += 2;
    });
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Anomalies
  if (results.anomalies && results.anomalies.length > 0) {
    y = addSectionHeader(doc, y, 'Detected Anomalies & Issues');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    results.anomalies.forEach((anomaly) => {
      const anomalyLines = doc.splitTextToSize(`• ${anomaly}`, 180);
      doc.text(anomalyLines, 15, y);
      y += anomalyLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Actionable Recommendations
  if (aiAnalysis.actionable_recommendations && aiAnalysis.actionable_recommendations.length > 0) {
    if (y > 250) {
      doc.addPage();
      y = 20;
    }
    y = addSectionHeader(doc, y, 'Actionable Recommendations');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    aiAnalysis.actionable_recommendations.forEach((rec) => {
      const recLines = doc.splitTextToSize(`• ${rec}`, 180);
      doc.text(recLines, 15, y);
      y += recLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Footer
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(128, 128, 128);
    doc.text(`Page ${i} of ${pageCount}`, 195, 290, { align: 'right' });
    doc.text('Document Anomaly Detection System', 15, 290);
  }
  
  return doc;
};

// Generate Money Order PDF
export const generateMoneyOrderPDF = (results) => {
  const jsPDF = getJsPDF();
  const doc = new jsPDF();
  let y = addHeader(doc, 'Money Order Analysis Report', results.timestamp || new Date().toISOString());
  
  const mlAnalysis = results.ml_analysis || {};
  const aiAnalysis = results.ai_analysis || {};
  const fraudRiskScore = results.fraud_risk_score ?? mlAnalysis.fraud_risk_score;
  const riskLevel = results.risk_level || mlAnalysis.risk_level || 'UNKNOWN';
  const recommendation = results.ai_recommendation || aiAnalysis.recommendation || 'UNKNOWN';
  const confidence = results.ai_confidence ?? aiAnalysis.confidence_score ?? aiAnalysis.confidence;
  
  // Executive Summary
  y = addSummaryBox(doc, y, fraudRiskScore, riskLevel, recommendation, confidence);
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Money Order Information
  y = addSectionHeader(doc, y, 'Money Order Information');
  y = addKeyValue(doc, y, 'Issuer', results.issuer);
  y = addKeyValue(doc, y, 'Serial Number', results.serial_number);
  y = addKeyValue(doc, y, 'Amount (Numeric)', results.amount);
  y = addKeyValue(doc, y, 'Amount (Written)', results.amount_in_words || results.amount_words);
  y = addKeyValue(doc, y, 'Payee', results.payee || results.payee_name);
  y = addKeyValue(doc, y, 'Purchaser', results.purchaser || results.purchaser_name);
  y = addKeyValue(doc, y, 'Date', results.date);
  y = addKeyValue(doc, y, 'Location', results.location);
  y = addKeyValue(doc, y, 'Signature Present', results.signature_present ? 'Yes' : 'No');
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // ML Analysis Details
  y = addSectionHeader(doc, y, 'ML Analysis Details');
  y = addKeyValue(doc, y, 'Random Forest Score', formatPercent(mlAnalysis.rf_score));
  y = addKeyValue(doc, y, 'XGBoost Score', formatPercent(mlAnalysis.xgb_score));
  y = addKeyValue(doc, y, 'Model Confidence', formatPercent(results.model_confidence ?? mlAnalysis.model_confidence));
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // AI Analysis
  if (aiAnalysis.reasoning || aiAnalysis.summary) {
    y = addSectionHeader(doc, y, 'AI Analysis');
    if (aiAnalysis.summary) {
      const summaryLines = doc.splitTextToSize(aiAnalysis.summary, 180);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(summaryLines, 15, y);
      y += summaryLines.length * 5 + 5;
    }
    if (aiAnalysis.reasoning && Array.isArray(aiAnalysis.reasoning)) {
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.text('Reasoning:', 15, y);
      y += 5;
      doc.setFont('helvetica', 'normal');
      aiAnalysis.reasoning.forEach((reason) => {
        const reasonLines = doc.splitTextToSize(`• ${reason}`, 180);
        doc.text(reasonLines, 15, y);
        y += reasonLines.length * 5;
      });
    }
    y += 5;
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Fraud Types & Explanations
  if (results.fraud_types && results.fraud_types.length > 0) {
    y = addSectionHeader(doc, y, 'Fraud Types Detected');
    results.fraud_types.forEach((fraudType) => {
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(231, 76, 60);
      doc.text(`• ${fraudType}`, 15, y);
      y += 6;
      
      if (results.fraud_explanations && Array.isArray(results.fraud_explanations)) {
        const explanation = results.fraud_explanations.find(exp => exp.type === fraudType);
        if (explanation && explanation.reasons) {
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(0, 0, 0);
          doc.setFontSize(9);
          explanation.reasons.forEach((reason) => {
            const reasonLines = doc.splitTextToSize(`  - ${reason}`, 175);
            doc.text(reasonLines, 20, y);
            y += reasonLines.length * 4;
          });
        }
      }
      y += 2;
    });
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Anomalies
  if (results.anomalies && results.anomalies.length > 0) {
    y = addSectionHeader(doc, y, 'Detected Anomalies & Issues');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    results.anomalies.forEach((anomaly) => {
      const anomalyLines = doc.splitTextToSize(`• ${anomaly}`, 180);
      doc.text(anomalyLines, 15, y);
      y += anomalyLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Actionable Recommendations
  if (aiAnalysis.actionable_recommendations && aiAnalysis.actionable_recommendations.length > 0) {
    if (y > 250) {
      doc.addPage();
      y = 20;
    }
    y = addSectionHeader(doc, y, 'Actionable Recommendations');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    aiAnalysis.actionable_recommendations.forEach((rec) => {
      const recLines = doc.splitTextToSize(`• ${rec}`, 180);
      doc.text(recLines, 15, y);
      y += recLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Footer
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(128, 128, 128);
    doc.text(`Page ${i} of ${pageCount}`, 195, 290, { align: 'right' });
    doc.text('Document Anomaly Detection System', 15, 290);
  }
  
  return doc;
};

// Generate Paystub PDF
export const generatePaystubPDF = (results) => {
  const jsPDF = getJsPDF();
  const doc = new jsPDF();
  let y = addHeader(doc, 'Paystub Analysis Report', results.timestamp || new Date().toISOString());
  
  const mlAnalysis = results.ml_analysis || {};
  const aiAnalysis = results.ai_analysis || {};
  const fraudRiskScore = results.fraud_risk_score ?? mlAnalysis.fraud_risk_score;
  const riskLevel = results.risk_level || mlAnalysis.risk_level || 'UNKNOWN';
  const recommendation = results.ai_recommendation || aiAnalysis.recommendation || 'UNKNOWN';
  const confidence = results.ai_confidence ?? aiAnalysis.confidence_score ?? aiAnalysis.confidence;
  
  // Executive Summary
  y = addSummaryBox(doc, y, fraudRiskScore, riskLevel, recommendation, confidence);
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Employee Information
  y = addSectionHeader(doc, y, 'Employee Information');
  y = addKeyValue(doc, y, 'Employee Name', results.employee_name);
  y = addKeyValue(doc, y, 'Employee ID', results.employee_id);
  y = addKeyValue(doc, y, 'SSN', results.ssn || results.social_security_number);
  y = addKeyValue(doc, y, 'Address', results.address);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Employer Information
  y = addSectionHeader(doc, y, 'Employer Information');
  y = addKeyValue(doc, y, 'Employer Name', results.employer_name);
  y = addKeyValue(doc, y, 'Employer Address', results.employer_address);
  y = addKeyValue(doc, y, 'Pay Period', results.pay_period);
  y = addKeyValue(doc, y, 'Pay Date', results.pay_date);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Earnings
  y = addSectionHeader(doc, y, 'Earnings');
  const earnings = results.earnings || {};
  y = addKeyValue(doc, y, 'Gross Pay', earnings.gross_pay || earnings.gross);
  y = addKeyValue(doc, y, 'Regular Hours', earnings.regular_hours);
  y = addKeyValue(doc, y, 'Regular Rate', earnings.regular_rate);
  y = addKeyValue(doc, y, 'Overtime Hours', earnings.overtime_hours);
  y = addKeyValue(doc, y, 'Overtime Rate', earnings.overtime_rate);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Deductions
  y = addSectionHeader(doc, y, 'Deductions');
  const deductions = results.deductions || {};
  y = addKeyValue(doc, y, 'Federal Tax', deductions.federal_tax);
  y = addKeyValue(doc, y, 'State Tax', deductions.state_tax);
  y = addKeyValue(doc, y, 'Social Security', deductions.social_security);
  y = addKeyValue(doc, y, 'Medicare', deductions.medicare);
  y = addKeyValue(doc, y, 'Other Deductions', deductions.other);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Net Pay
  y = addSectionHeader(doc, y, 'Net Pay');
  y = addKeyValue(doc, y, 'Total Deductions', results.total_deductions);
  y = addKeyValue(doc, y, 'Net Pay', results.net_pay);
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // ML Analysis Details
  y = addSectionHeader(doc, y, 'ML Analysis Details');
  y = addKeyValue(doc, y, 'Random Forest Score', formatPercent(mlAnalysis.rf_score));
  y = addKeyValue(doc, y, 'XGBoost Score', formatPercent(mlAnalysis.xgb_score));
  y = addKeyValue(doc, y, 'Model Confidence', formatPercent(results.model_confidence ?? mlAnalysis.model_confidence));
  y += 5;
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // AI Analysis
  if (aiAnalysis.reasoning || aiAnalysis.summary) {
    y = addSectionHeader(doc, y, 'AI Analysis');
    if (aiAnalysis.summary) {
      const summaryLines = doc.splitTextToSize(aiAnalysis.summary, 180);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(summaryLines, 15, y);
      y += summaryLines.length * 5 + 5;
    }
    if (aiAnalysis.reasoning && Array.isArray(aiAnalysis.reasoning)) {
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.text('Reasoning:', 15, y);
      y += 5;
      doc.setFont('helvetica', 'normal');
      aiAnalysis.reasoning.forEach((reason) => {
        const reasonLines = doc.splitTextToSize(`• ${reason}`, 180);
        doc.text(reasonLines, 15, y);
        y += reasonLines.length * 5;
      });
    }
    y += 5;
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Fraud Types & Explanations
  if (results.fraud_types && results.fraud_types.length > 0) {
    y = addSectionHeader(doc, y, 'Fraud Types Detected');
    results.fraud_types.forEach((fraudType) => {
      doc.setFontSize(10);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(231, 76, 60);
      doc.text(`• ${fraudType}`, 15, y);
      y += 6;
      
      if (results.fraud_explanations && Array.isArray(results.fraud_explanations)) {
        const explanation = results.fraud_explanations.find(exp => exp.type === fraudType);
        if (explanation && explanation.reasons) {
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(0, 0, 0);
          doc.setFontSize(9);
          explanation.reasons.forEach((reason) => {
            const reasonLines = doc.splitTextToSize(`  - ${reason}`, 175);
            doc.text(reasonLines, 20, y);
            y += reasonLines.length * 4;
          });
        }
      }
      y += 2;
    });
  }
  
  if (y > 250) {
    doc.addPage();
    y = 20;
  }
  
  // Anomalies
  if (results.anomalies && results.anomalies.length > 0) {
    y = addSectionHeader(doc, y, 'Detected Anomalies & Issues');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    results.anomalies.forEach((anomaly) => {
      const anomalyLines = doc.splitTextToSize(`• ${anomaly}`, 180);
      doc.text(anomalyLines, 15, y);
      y += anomalyLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Actionable Recommendations
  if (aiAnalysis.actionable_recommendations && aiAnalysis.actionable_recommendations.length > 0) {
    if (y > 250) {
      doc.addPage();
      y = 20;
    }
    y = addSectionHeader(doc, y, 'Actionable Recommendations');
    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    aiAnalysis.actionable_recommendations.forEach((rec) => {
      const recLines = doc.splitTextToSize(`• ${rec}`, 180);
      doc.text(recLines, 15, y);
      y += recLines.length * 4 + 2;
      if (y > 270) {
        doc.addPage();
        y = 20;
      }
    });
  }
  
  // Footer
  const pageCount = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(128, 128, 128);
    doc.text(`Page ${i} of ${pageCount}`, 195, 290, { align: 'right' });
    doc.text('Document Anomaly Detection System', 15, 290);
  }
  
  return doc;
};

