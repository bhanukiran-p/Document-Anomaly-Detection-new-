/**
 * Check Data Processor
 * Handles CSV parsing and data processing for check insights
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

export const processData = (rows) => {
  if (!rows.length) return null;

  // 1. Fraud Risk Distribution (0-25%, 25-50%, 50-75%, 75-100%)
  const riskScores = rows.map(r => parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0));
  const riskScoresPercent = riskScores.map(s => s * 100);
  const riskDistribution = [
    { range: '0-25%', count: riskScoresPercent.filter(s => s < 25).length },
    { range: '25-50%', count: riskScoresPercent.filter(s => s >= 25 && s < 50).length },
    { range: '50-75%', count: riskScoresPercent.filter(s => s >= 50 && s < 75).length },
    { range: '75-100%', count: riskScoresPercent.filter(s => s >= 75).length },
  ];

  // 2. AI Recommendation Distribution (APPROVE/REJECT/ESCALATE)
  const recommendations = rows.map(r => (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
  const recommendationData = [
    { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
    { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
    { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
  ].filter(item => item.value > 0);

  // 3. Risk by Bank (Average risk score per bank)
  const bankRisks = {};
  rows.forEach(r => {
    const bank = r['BankName'] || r['bank_name'] || 'Unknown';
    if (!bankRisks[bank]) {
      bankRisks[bank] = { count: 0, totalRisk: 0 };
    }
    bankRisks[bank].count++;
    bankRisks[bank].totalRisk += parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0);
  });
  const riskByBankData = Object.entries(bankRisks)
    .map(([name, data]) => ({
      name,
      avgRisk: parseFloat(((data.totalRisk / data.count) * 100).toFixed(1)),
      count: data.count
    }))
    .sort((a, b) => b.avgRisk - a.avgRisk);

  // 4. Top High-Risk Payers
  const payerRisks = {};
  rows.forEach(r => {
    const payer = r['PayerName'] || r['payer_name'] || 'Unknown';
    if (payer && payer !== 'Unknown') {
      if (!payerRisks[payer]) {
        payerRisks[payer] = { count: 0, totalRisk: 0, maxRisk: 0 };
      }
      const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
      payerRisks[payer].count++;
      payerRisks[payer].totalRisk += risk;
      payerRisks[payer].maxRisk = Math.max(payerRisks[payer].maxRisk, risk);
    }
  });
  const topHighRiskPayers = Object.entries(payerRisks)
    .map(([name, data]) => ({
      name: name,
      fullName: name,
      avgRisk: (data.totalRisk / data.count).toFixed(1),
      count: data.count,
      maxRisk: data.maxRisk.toFixed(1)
    }))
    .filter(item => parseFloat(item.avgRisk) >= 50)
    .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
    .slice(0, 10);

  // 5. Payees with Highest Fraud Incidents (Count of REJECT/ESCALATE or high risk >= 75%)
  const payeeFraudIncidents = {};
  rows.forEach(r => {
    const payee = r['PayeeName'] || r['payee_name'] || 'Unknown';
    if (payee && payee !== 'Unknown') {
      const decision = (r['Decision'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase();
      const risk = parseFloat_(r['RiskScore'] || r['fraud_risk_score'] || 0) * 100;
      const isFraudulent = decision === 'REJECT' || decision === 'ESCALATE' || risk >= 75;

      if (isFraudulent) {
        if (!payeeFraudIncidents[payee]) {
          payeeFraudIncidents[payee] = 0;
        }
        payeeFraudIncidents[payee]++;
      }
    }
  });
  const topFraudIncidentPayees = Object.entries(payeeFraudIncidents)
    .map(([name, fraudCount]) => ({
      name: name,
      fraudCount: fraudCount
    }))
    .filter(item => item.fraudCount > 0)
    .sort((a, b) => b.fraudCount - a.fraudCount)
    .slice(0, 10);

  // 6. Fraud Over Time (High-Risk Count and Avg Risk)
  const fraudOverTime = {};
  rows.forEach(r => {
    const dateStr = r['CheckDate'] || r['check_date'] || r['created_at'] || '';
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

  // 9. Repeat Offenders (Payers with multiple high-risk checks)
  const repeatOffenders = Object.entries(payerRisks)
    .filter(([name, data]) => data.count > 1 && parseFloat((data.totalRisk / data.count).toFixed(1)) >= 50)
    .length;

  // 11. High-Risk Count (>75%)
  const highRiskCount = riskScoresPercent.filter(s => s >= 75).length;

  // 12. Summary Metrics
  const totalChecks = rows.length;
  const avgRiskScore = (riskScores.reduce((a, b) => a + b, 0) / riskScores.length * 100).toFixed(1);
  const approveCount = recommendations.filter(d => d === 'APPROVE').length;
  const rejectCount = recommendations.filter(d => d === 'REJECT').length;
  const escalateCount = recommendations.filter(d => d === 'ESCALATE').length;

  return {
    riskDistribution,
    recommendationData: recommendationData.length > 0 ? recommendationData : [
      { name: 'No Data', value: rows.length }
    ],
    riskByBankData,
    topHighRiskPayers,
    topFraudIncidentPayees,
    fraudTrendData,
    metrics: {
      totalChecks,
      avgRiskScore,
      approveCount,
      rejectCount,
      escalateCount,
      highRiskCount,
      repeatOffenders
    }
  };
};
