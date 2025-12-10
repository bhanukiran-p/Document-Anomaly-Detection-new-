/**
 * Money Order Data Processor
 * Handles CSV parsing and data processing for money order insights
 */

export const parseCSV = (text) => {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map(h => h.trim());
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // Handle quoted CSV values
    const values = [];
    let current = '';
    let inQuotes = false;

    for (let j = 0; j < line.length; j++) {
      const char = line[j];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());

    const row = {};
    headers.forEach((header, idx) => {
      row[header] = values[idx] || '';
    });
    rows.push(row);
  }

  return rows;
};

export const parseFloat_ = (val) => {
  const num = parseFloat(val);
  return isNaN(num) ? 0 : num;
};

export const processData = (rows, selectedIssuer = null) => {
  if (!rows.length) return null;

  // Check if we're in single issuer view
  const isSingleIssuerView = selectedIssuer && selectedIssuer !== '' && selectedIssuer !== 'All Issuers';

  // 1. Fraud Severity Breakdown (High >=75%, Medium 50-75%, Low <50%)
  const riskScores = rows.map(r => parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0));
  const riskScoresPercent = riskScores.map(s => s * 100);
  const severityCounts = {
    'HIGH': riskScoresPercent.filter(s => s >= 75).length,
    'MEDIUM': riskScoresPercent.filter(s => s >= 50 && s < 75).length,
    'LOW': riskScoresPercent.filter(s => s < 50).length
  };
  const fraudSeverityData = [
    { name: 'HIGH (>=75%)', value: severityCounts['HIGH'], color: '#e53935' },
    { name: 'MEDIUM (50-75%)', value: severityCounts['MEDIUM'], color: '#f4b400' },
    { name: 'LOW (<50%)', value: severityCounts['LOW'], color: '#34a853' }
  ].filter(item => item.value > 0);

  // 2. AI Recommendation Distribution (APPROVE/REJECT/ESCALATE)
  const recommendations = rows.map(r => (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
  const recommendationData = [
    { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
    { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
    { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
  ].filter(item => item.value > 0);


  // 4. Risk by Issuer (Average risk score per issuer)
  const issuerRisks = {};
  rows.forEach(r => {
    const issuer = r['IssuerName'] || r['money_order_institute'] || r['issuer_name'] || 'Unknown';
    if (!issuerRisks[issuer]) {
      issuerRisks[issuer] = { count: 0, totalRisk: 0 };
    }
    issuerRisks[issuer].count++;
    issuerRisks[issuer].totalRisk += parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
  });
  const riskByIssuerData = Object.entries(issuerRisks)
    .map(([name, data]) => ({
      name,
      avgRisk: ((data.totalRisk / data.count) * 100).toFixed(1),
      count: data.count
    }))
    .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
    .slice(0, 10); // Top 10 issuers

  // 5. Top Fraudulent Issuers (% High-Risk MOs >75%)
  const issuerHighRisk = {};
  rows.forEach(r => {
    const issuer = r['IssuerName'] || r['money_order_institute'] || r['issuer_name'] || 'Unknown';
    const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
    if (!issuerHighRisk[issuer]) {
      issuerHighRisk[issuer] = { total: 0, highRisk: 0 };
    }
    issuerHighRisk[issuer].total++;
    if (risk > 75) {
      issuerHighRisk[issuer].highRisk++;
    }
  });
  const topFraudulentIssuers = Object.entries(issuerHighRisk)
    .map(([name, data]) => ({
      name,
      highRiskPercent: data.total > 0 ? ((data.highRisk / data.total) * 100).toFixed(1) : '0.0',
      highRiskCount: data.highRisk,
      totalCount: data.total
    }))
    .filter(item => item.totalCount > 0)
    .sort((a, b) => parseFloat(b.highRiskPercent) - parseFloat(a.highRiskPercent))
    .slice(0, 10);

  // 6. Top High-Risk Purchasers
  const purchaserRisks = {};
  rows.forEach(r => {
    // Normalize purchaser name - handle multiple field names and trim whitespace
    const purchaser = (r['PurchaserName'] || r['purchaser_name'] || '').trim();
    if (purchaser && purchaser !== '' && purchaser !== 'Unknown' && purchaser.toLowerCase() !== 'unknown') {
      // Use uppercase for consistent grouping (case-insensitive)
      const purchaserKey = purchaser.toUpperCase();
      if (!purchaserRisks[purchaserKey]) {
        purchaserRisks[purchaserKey] = {
          count: 0,
          totalRisk: 0,
          maxRisk: 0,
          originalName: purchaser // Keep original for display
        };
      }
      const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
      purchaserRisks[purchaserKey].count++;
      purchaserRisks[purchaserKey].totalRisk += risk;
      purchaserRisks[purchaserKey].maxRisk = Math.max(purchaserRisks[purchaserKey].maxRisk, risk);
    }
  });
  const topHighRiskPurchasers = Object.entries(purchaserRisks)
    .map(([key, data]) => ({
      name: data.originalName || key, // Use original name for display
      fullName: data.originalName || key,
      avgRisk: (data.totalRisk / data.count).toFixed(1),
      count: data.count,
      maxRisk: data.maxRisk.toFixed(1)
    }))
    .filter(item => parseFloat(item.avgRisk) >= 50)
    .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
    .slice(0, 10);

  // 7. Top High-Risk Payees
  const payeeRisks = {};
  rows.forEach(r => {
    const payee = r['PayeeName'] || r['payee_name'] || 'Unknown';
    if (payee && payee !== 'Unknown') {
      if (!payeeRisks[payee]) {
        payeeRisks[payee] = { count: 0, totalRisk: 0, highRiskCount: 0 };
      }
      const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
      payeeRisks[payee].count++;
      payeeRisks[payee].totalRisk += risk;
      if (risk > 75) {
        payeeRisks[payee].highRiskCount++;
      }
    }
  });
  const topHighRiskPayees = Object.entries(payeeRisks)
    .map(([name, data]) => ({
      name,
      fullName: name,
      avgRisk: (data.totalRisk / data.count).toFixed(1),
      count: data.count,
      highRiskCount: data.highRiskCount
    }))
    .filter(item => parseFloat(item.avgRisk) >= 50)
    .sort((a, b) => b.highRiskCount - a.highRiskCount)
    .slice(0, 10);

  // 8. Fraud Trend Over Time (High-Risk Count)
  const fraudOverTime = {};
  rows.forEach(r => {
    const dateStr = r['IssueDate'] || r['issue_date'] || r['created_at'] || '';
    if (dateStr) {
      const date = dateStr.split('T')[0];
      if (!fraudOverTime[date]) {
        fraudOverTime[date] = { count: 0, highRiskCount: 0, totalRisk: 0 };
      }
      const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
      fraudOverTime[date].count++;
      fraudOverTime[date].totalRisk += risk;
      if (risk >= 75) {
        fraudOverTime[date].highRiskCount++;
      }
    }
  });
  const fraudTrendData = Object.entries(fraudOverTime)
    .map(([date, data]) => ({
      date,
      avgRisk: (data.totalRisk / data.count).toFixed(1),
      highRiskCount: data.highRiskCount,
      totalCount: data.count
    }))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-30);

  // 9. Issuer-Specific Charts (only when single issuer is selected)
  let topRiskyPurchasersForIssuer = [];
  let riskScoreTrendForIssuer = [];

  if (isSingleIssuerView) {
    // Chart A: Top Risky Purchasers (Selected Issuer)
    const purchaserHighRisk = {};
    rows.forEach(r => {
      const purchaser = (r['PurchaserName'] || r['purchaser_name'] || '').trim();
      if (purchaser && purchaser !== '' && purchaser !== 'Unknown') {
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
        const recommendation = (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase();
        const isHighRisk = risk >= 0.75 || recommendation !== 'APPROVE';

        const purchaserKey = purchaser.toUpperCase();
        if (!purchaserHighRisk[purchaserKey]) {
          purchaserHighRisk[purchaserKey] = {
            originalName: purchaser,
            highRiskCount: 0,
            totalCount: 0
          };
        }
        purchaserHighRisk[purchaserKey].totalCount++;
        if (isHighRisk) {
          purchaserHighRisk[purchaserKey].highRiskCount++;
        }
      }
    });

    topRiskyPurchasersForIssuer = Object.entries(purchaserHighRisk)
      .map(([key, data]) => ({
        name: data.originalName || key,
        highRiskCount: data.highRiskCount,
        totalCount: data.totalCount
      }))
      .sort((a, b) => b.highRiskCount - a.highRiskCount)
      .slice(0, 10);

    // Chart B: Risk Score Trend (Selected Issuer)
    const issuerTrendByDay = {};
    rows.forEach(r => {
      const dateStr = r['IssueDate'] || r['issue_date'] || r['created_at'] || '';
      if (dateStr) {
        const date = dateStr.split('T')[0];
        if (!issuerTrendByDay[date]) {
          issuerTrendByDay[date] = { count: 0, totalRisk: 0, highRiskCount: 0 };
        }
        const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
        const recommendation = (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase();
        const isHighRisk = risk >= 0.75 || recommendation !== 'APPROVE';

        issuerTrendByDay[date].count++;
        issuerTrendByDay[date].totalRisk += risk;
        if (isHighRisk) {
          issuerTrendByDay[date].highRiskCount++;
        }
      }
    });

    riskScoreTrendForIssuer = Object.entries(issuerTrendByDay)
      .map(([date, data]) => ({
        date,
        avgRisk: (data.totalRisk / data.count * 100).toFixed(1),
        highRiskRate: data.count > 0 ? ((data.highRiskCount / data.count) * 100).toFixed(1) : '0.0',
        highRiskCount: data.highRiskCount,
        totalCount: data.count
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-30);
  }

  // 12. High-Risk Count (>75%)
  const highRiskCount = riskScoresPercent.filter(s => s >= 75).length;


  // 14. Summary Metrics
  const totalMoneyOrders = rows.length;
  const avgRiskScore = (riskScores.reduce((a, b) => a + b, 0) / riskScores.length * 100).toFixed(1);
  const approveCount = recommendations.filter(d => d === 'APPROVE').length;
  const rejectCount = recommendations.filter(d => d === 'REJECT').length;
  const escalateCount = recommendations.filter(d => d === 'ESCALATE').length;

  return {
    fraudSeverityData,
    recommendationData: recommendationData.length > 0 ? recommendationData : [
      { name: 'No Data', value: rows.length }
    ],
    riskByIssuerData,
    topFraudulentIssuers,
    topHighRiskPurchasers,
    topHighRiskPayees,
    fraudTrendData,
    topRiskyPurchasersForIssuer,
    riskScoreTrendForIssuer,
    isSingleIssuerView,
    selectedIssuerName: isSingleIssuerView ? selectedIssuer : null,
    metrics: {
      totalMoneyOrders,
      avgRiskScore,
      approveCount,
      rejectCount,
      escalateCount,
      highRiskCount,
    }
  };
};
