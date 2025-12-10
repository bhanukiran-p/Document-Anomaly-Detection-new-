/**
 * Bank Statement Data Processor
 * Handles CSV parsing and data processing for bank statement insights
 * Includes fraud type classification logic
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
  const riskScores = rows.map(r => parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0));
  const riskDistribution = [
    { range: '0-25%', count: riskScores.filter(s => s < 25).length },
    { range: '25-50%', count: riskScores.filter(s => s >= 25 && s < 50).length },
    { range: '50-75%', count: riskScores.filter(s => s >= 50 && s < 75).length },
    { range: '75-100%', count: riskScores.filter(s => s >= 75).length },
  ];

  // 2. AI Recommendation Distribution (APPROVE/REJECT/ESCALATE)
  const recommendations = rows.map(r => (r['AI Recommendation'] || r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
  const recommendationData = [
    { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
    { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
    { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
  ].filter(item => item.value > 0);

  // 3. Risk by Bank (Average risk score per bank)
  const bankRisks = {};
  rows.forEach(r => {
    const bank = r['Bank Name'] || r['bank_name'] || 'Unknown';
    if (!bankRisks[bank]) {
      bankRisks[bank] = { count: 0, totalRisk: 0 };
    }
    bankRisks[bank].count++;
    bankRisks[bank].totalRisk += parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
  });
  const riskByBankData = Object.entries(bankRisks)
    .map(([name, data]) => ({
      name,
      avgRisk: parseFloat(((data.totalRisk / data.count) * 100).toFixed(1)),
      count: data.count
    }))
    .sort((a, b) => b.avgRisk - a.avgRisk)
    .map(bank => ({
      ...bank,
      displayName: (() => {
        const name = bank.name.toUpperCase();
        if (name.includes('BANK OF AMERICA') || name.includes('BOFA')) return 'BOFA';
        if (name.includes('CHASE') || name.includes('JPM')) return 'JPMC';
        if (name.includes('WELLS FARGO') || name.includes('WELLS')) return 'WF';
        if (name.includes('CITIBANK') || name.includes('CITI')) return 'CITI';
        if (name.includes('US BANK')) return 'USB';
        if (name.includes('ALLY')) return 'ALLY';
        return bank.name.length > 10 ? bank.name.substring(0, 10) + '...' : bank.name;
      })()
    }));

  // 4. Fraud Type Distribution (classify by actual fraud types)
  const fraudTypeCount = {};

  // Track account holders for repeat offender detection
  const accountHolderRiskCount = {};

  // Helper function to normalize fraud type name from database
  const normalizeFraudType = (fraudType) => {
    if (fraudType === null || fraudType === undefined || fraudType === '') {
      return null;
    }
    const normalized = fraudType.toString().trim();
    if (!normalized) return null;

    const typeMap = {
      'fabricated document': 'Fabricated Document',
      'altered legitimate document': 'Altered Legitimate Document',
      'suspicious transaction patterns': 'Suspicious Transaction Patterns',
      'balance consistency violation': 'Balance Consistency Violation',
      'unrealistic financial proportion': 'Unrealistic Financial Proportion',
      'repeat offender': 'Repeat Offender'
    };
    return typeMap[normalized.toLowerCase()] || normalized;
  };

  // Helper function to classify fraud type based on anomalies and data
  const classifyFraudType = (row) => {
    const anomalies = row['Top Anomalies'] || row['top_anomalies'] || row['Anomalies'] || row['anomalies'] || '';
    const anomaliesStr = typeof anomalies === 'string' ? anomalies.toLowerCase() :
      (Array.isArray(anomalies) ? anomalies.join(' ').toLowerCase() :
        (typeof anomalies === 'object' ? JSON.stringify(anomalies).toLowerCase() : ''));

    const risk = parseFloat_(row['Fraud Risk Score (%)'] || row['fraud_risk_score'] || 0);
    const confidence = parseFloat_(row['Model Confidence (%)'] || row['model_confidence'] || 0);
    const accountHolder = (row['Account Holder'] || row['account_holder'] || '').toLowerCase().trim();

    // 1. Fabricated Document
    if (confidence < 50 ||
      anomaliesStr.includes('missing critical fields') ||
      anomaliesStr.includes('document structure') ||
      anomaliesStr.includes('invalid format') ||
      anomaliesStr.includes('poor ocr') ||
      (!row['Bank Name'] && !row['bank_name']) ||
      (!row['Account Number'] && !row['account_number'])) {
      return 'Fabricated Document';
    }

    // 2. Altered Legitimate Document
    if (anomaliesStr.includes('altered') ||
      anomaliesStr.includes('tampered') ||
      anomaliesStr.includes('modified') ||
      anomaliesStr.includes('inconsistent formatting') ||
      anomaliesStr.includes('font mismatch') ||
      anomaliesStr.includes('date mismatch') ||
      anomaliesStr.includes('signature mismatch')) {
      return 'Altered Legitimate Document';
    }

    // 3. Suspicious Transaction Patterns
    if (anomaliesStr.includes('suspicious transaction') ||
      anomaliesStr.includes('unusual pattern') ||
      anomaliesStr.includes('rapid transactions') ||
      anomaliesStr.includes('round number') ||
      anomaliesStr.includes('odd hours') ||
      anomaliesStr.includes('transaction frequency') ||
      anomaliesStr.includes('unusual amount')) {
      return 'Suspicious Transaction Patterns';
    }

    // 4. Balance Consistency Violation
    if (anomaliesStr.includes('balance inconsistent') ||
      anomaliesStr.includes('balance mismatch') ||
      anomaliesStr.includes('amount mismatch') ||
      anomaliesStr.includes('math inconsistent') ||
      anomaliesStr.includes('reconciliation') ||
      anomaliesStr.includes('balance calculation')) {
      return 'Balance Consistency Violation';
    }

    // 5. Unrealistic Financial Proportion
    if (anomaliesStr.includes('unrealistic') ||
      anomaliesStr.includes('proportion') ||
      anomaliesStr.includes('unusual amount') ||
      anomaliesStr.includes('excessive') ||
      anomaliesStr.includes('improbable') ||
      risk > 70 && confidence > 70) {
      return 'Unrealistic Financial Proportion';
    }

    if (risk >= 75) {
      return 'Suspicious Transaction Patterns';
    }

    return 'Unrealistic Financial Proportion';
  };

  // First pass: track account holders for repeat offender detection
  rows.forEach(r => {
    const accountHolder = (r['Account Holder'] || r['account_holder'] || '').toLowerCase().trim();
    const risk = parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
    if (accountHolder) {
      if (!accountHolderRiskCount[accountHolder]) {
        accountHolderRiskCount[accountHolder] = { count: 0, highRiskCount: 0 };
      }
      accountHolderRiskCount[accountHolder].count++;
      if (risk >= 50) {
        accountHolderRiskCount[accountHolder].highRiskCount++;
      }
    }
  });

  // Second pass: classify all statements
  const repeatOffenderThreshold = 2;
  const genericFallbackTypes = ['Suspicious Transaction Patterns', 'Unrealistic Financial Proportion'];

  rows.forEach(r => {
    const accountHolder = (r['Account Holder'] || r['account_holder'] || '').toLowerCase().trim();
    const risk = parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);

    const dbFraudType = r['fraud_types'] !== undefined ? r['fraud_types'] :
      (r['Fraud Types'] !== undefined ? r['Fraud Types'] :
        (r['fraud_type'] !== undefined ? r['fraud_type'] :
          (r['Fraud Type'] !== undefined ? r['Fraud Type'] : null)));

    if (dbFraudType === null ||
      dbFraudType === undefined ||
      dbFraudType === '' ||
      (typeof dbFraudType === 'string' && dbFraudType.toLowerCase() === 'null')) {
      return;
    }

    let fraudType = normalizeFraudType(dbFraudType);

    if (!fraudType) {
      fraudType = classifyFraudType(r);

      const anomalies = r['Top Anomalies'] || r['top_anomalies'] || r['Anomalies'] || r['anomalies'] || '';
      const anomaliesStr = typeof anomalies === 'string' ? anomalies.toLowerCase() :
        (Array.isArray(anomalies) ? anomalies.join(' ').toLowerCase() :
          (typeof anomalies === 'object' ? JSON.stringify(anomalies).toLowerCase() : ''));

      const hasSpecificIndicators = anomaliesStr.length > 0 && (
        anomaliesStr.includes('missing') ||
        anomaliesStr.includes('altered') ||
        anomaliesStr.includes('tampered') ||
        anomaliesStr.includes('suspicious transaction') ||
        anomaliesStr.includes('balance inconsistent') ||
        anomaliesStr.includes('balance mismatch') ||
        anomaliesStr.includes('amount mismatch') ||
        anomaliesStr.includes('math inconsistent') ||
        anomaliesStr.includes('unrealistic') ||
        anomaliesStr.includes('proportion') ||
        anomaliesStr.includes('document structure') ||
        anomaliesStr.includes('invalid format') ||
        anomaliesStr.includes('poor ocr') ||
        anomaliesStr.includes('inconsistent formatting') ||
        anomaliesStr.includes('font mismatch') ||
        anomaliesStr.includes('date mismatch') ||
        anomaliesStr.includes('signature mismatch')
      );

      if (accountHolder && accountHolderRiskCount[accountHolder]) {
        const holderData = accountHolderRiskCount[accountHolder];
        const isRepeatOffender = holderData.highRiskCount >= repeatOffenderThreshold && holderData.count >= repeatOffenderThreshold;
        const isCurrentHighRisk = risk >= 50;

        if (isRepeatOffender && isCurrentHighRisk && (!hasSpecificIndicators || genericFallbackTypes.includes(fraudType))) {
          fraudType = 'Repeat Offender';
        }
      }
    }

    if (fraudType) {
      if (!fraudTypeCount[fraudType]) {
        fraudTypeCount[fraudType] = 0;
      }
      fraudTypeCount[fraudType]++;
    }
  });

  const fraudTypeData = Object.entries(fraudTypeCount)
    .map(([name, count]) => ({
      name: name.replace(/_/g, ' ').trim(),
      value: count
    }))
    .filter(item => item.value > 0)
    .sort((a, b) => b.value - a.value);

  // 5. Fraud Trend Over Time
  const fraudOverTime = {};
  rows.forEach(r => {
    const dateStr = r['Timestamp'] || r['timestamp'] || r['Statement Period'] || '';
    if (dateStr) {
      const date = dateStr.split('T')[0].split(' ')[0];
      if (!fraudOverTime[date]) {
        fraudOverTime[date] = { count: 0, highRiskCount: 0, totalRisk: 0 };
      }
      const risk = parseFloat_(r['Fraud Risk Score (%)'] || r['fraud_risk_score'] || 0);
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

  // 6. Summary Metrics
  const totalStatements = rows.length;
  const avgRiskScore = riskScores.length > 0 ? (riskScores.reduce((a, b) => a + b, 0) / riskScores.length).toFixed(1) : '0.0';
  const approveCount = recommendations.filter(d => d === 'APPROVE').length;
  const rejectCount = recommendations.filter(d => d === 'REJECT').length;
  const escalateCount = recommendations.filter(d => d === 'ESCALATE').length;
  const highRiskCount = riskScores.filter(s => s >= 75).length;

  return {
    riskDistribution,
    recommendationData: recommendationData.length > 0 ? recommendationData : [
      { name: 'No Data', value: rows.length }
    ],
    riskByBankData,
    fraudTypeData,
    fraudTrendData,
    metrics: {
      totalStatements,
      avgRiskScore,
      approveCount,
      rejectCount,
      escalateCount,
      highRiskCount
    }
  };
};
