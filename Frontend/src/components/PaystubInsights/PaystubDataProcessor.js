/**
 * Paystub Data Processor
 * Handles CSV parsing and data processing for paystub insights
 * Includes complex fraud type filtering logic
 */

import { colors } from '../../styles/colors';

export const parseCSV = (text) => {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];

  const headers = lines[0].split(',').map(h => h.trim());
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

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

export const processData = (rows, selectedEmployer = null, selectedFraudType = null, allRowsForComparison = null) => {
  if (!rows.length) return null;

  const isSingleEmployerView = selectedEmployer && selectedEmployer !== '' && selectedEmployer !== 'All Employers';
  const isFraudTypeFiltered = selectedFraudType && selectedFraudType !== '' && selectedFraudType !== 'All Fraud Types';

  // 1. Fraud Risk Distribution
  const riskScores = rows.map(r => parseFloat_(r['fraud_risk_score'] || 0));
  const riskScoresPercent = riskScores.map(s => s * 100);
  const riskDistribution = [
    { range: '0-25%', count: riskScoresPercent.filter(s => s < 25).length },
    { range: '25-50%', count: riskScoresPercent.filter(s => s >= 25 && s < 50).length },
    { range: '50-75%', count: riskScoresPercent.filter(s => s >= 50 && s < 75).length },
    { range: '75-100%', count: riskScoresPercent.filter(s => s >= 75).length },
  ];

  // 2. AI Recommendation Distribution
  const recommendations = rows.map(r => (r['ai_recommendation'] || 'UNKNOWN').toUpperCase());
  const recommendationData = [
    { name: 'APPROVE', value: recommendations.filter(d => d === 'APPROVE').length },
    { name: 'REJECT', value: recommendations.filter(d => d === 'REJECT').length },
    { name: 'ESCALATE', value: recommendations.filter(d => d === 'ESCALATE').length },
  ].filter(item => item.value > 0);

  // 3. Risk Level Category Distribution
  const riskLevelCounts = { 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0 };
  riskScoresPercent.forEach(score => {
    if (score >= 70) {
      riskLevelCounts['HIGH']++;
    } else if (score >= 35) {
      riskLevelCounts['MEDIUM']++;
    } else {
      riskLevelCounts['LOW']++;
    }
  });
  const riskLevelData = [
    { name: 'HIGH (70%+)', value: riskLevelCounts['HIGH'], color: colors.accent.red },
    { name: 'MEDIUM (35-70%)', value: riskLevelCounts['MEDIUM'], color: colors.status.warning },
    { name: 'LOW (<35%)', value: riskLevelCounts['LOW'], color: colors.status.success }
  ].filter(item => item.value > 0);

  // 4. Risk by Employer
  const employerRisks = {};
  rows.forEach(r => {
    const employer = r['employer_name'] || 'Unknown';
    if (!employer || employer === 'Unknown' || employer.toLowerCase() === 'unknown') {
      return;
    }
    if (!employerRisks[employer]) {
      employerRisks[employer] = { count: 0, totalRisk: 0 };
    }
    employerRisks[employer].count++;
    employerRisks[employer].totalRisk += parseFloat_(r['fraud_risk_score'] || 0);
  });
  const riskByEmployerData = Object.entries(employerRisks)
    .map(([name, data]) => ({
      name,
      avgRisk: ((data.totalRisk / data.count) * 100).toFixed(1),
      count: data.count
    }))
    .sort((a, b) => parseFloat(b.avgRisk) - parseFloat(a.avgRisk))
    .slice(0, 10);

  // 5. Top High-Risk Employees
  const employeeRisks = {};
  rows.forEach(r => {
    const employee = r['employee_name'] || 'Unknown';
    if (employee && employee !== 'Unknown') {
      if (!employeeRisks[employee]) {
        employeeRisks[employee] = { count: 0, totalRisk: 0, maxRisk: 0 };
      }
      const risk = parseFloat_(r['fraud_risk_score'] || 0) * 100;
      employeeRisks[employee].count++;
      employeeRisks[employee].totalRisk += risk;
      employeeRisks[employee].maxRisk = Math.max(employeeRisks[employee].maxRisk, risk);
    }
  });
  const topHighRiskEmployees = Object.entries(employeeRisks)
    .map(([name, data]) => {
      const avgRisk = parseFloat((data.totalRisk / data.count).toFixed(1));
      return {
        name,
        fullName: name,
        avgRisk,
        avgRiskDisplay: avgRisk.toFixed(1),
        count: data.count,
        maxRisk: parseFloat(data.maxRisk.toFixed(1))
      };
    })
    .filter(item => item.avgRisk >= 50)
    .sort((a, b) => b.avgRisk - a.avgRisk)
    .slice(0, 10);

  // 6. Fraud Type Distribution
  const fraudTypeCount = {};
  rows.forEach(r => {
    let fraudType = r['fraud_types'];
    if (Array.isArray(fraudType)) {
      fraudType.forEach(ft => {
        const typeStr = String(ft || '').trim();
        if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
          fraudTypeCount[typeStr] = (fraudTypeCount[typeStr] || 0) + 1;
        }
      });
    } else {
      const typeStr = String(fraudType || 'No Flag').trim();
      if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined' && typeStr.length > 0) {
        fraudTypeCount[typeStr] = (fraudTypeCount[typeStr] || 0) + 1;
      }
    }
  });
  const fraudTypeData = Object.entries(fraudTypeCount)
    .map(([name, count]) => ({
      name: name.replace(/_/g, ' ').trim() || 'Unknown Fraud Type',
      value: count
    }))
    .filter(item => item.name && item.name !== 'Unknown Fraud Type' || item.value > 0)
    .sort((a, b) => b.value - a.value);

  // 7. Income Distribution Stats
  const grossPayValues = rows.map(r => parseFloat_(r['gross_pay'] || 0));
  const netPayValues = rows.map(r => parseFloat_(r['net_pay'] || 0));
  const formatCurrencyK = (value) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toFixed(0)}`;
  };
  const avgGrossPayRaw = grossPayValues.reduce((a, b) => a + b, 0) / grossPayValues.length;
  const avgNetPayRaw = netPayValues.reduce((a, b) => a + b, 0) / netPayValues.length;
  const avgGrossPay = formatCurrencyK(avgGrossPayRaw);
  const avgNetPay = formatCurrencyK(avgNetPayRaw);
  const maxGrossPay = Math.max(...grossPayValues).toFixed(2);
  const minGrossPay = Math.min(...grossPayValues).toFixed(2);

  // 8. Fraud-Type-Specific Metrics
  let fraudTypeSpecificData = null;
  if (isFraudTypeFiltered) {
    const filteredAvgRisk = riskScores.length > 0
      ? ((riskScores.reduce((a, b) => a + b, 0) / riskScores.length) * 100).toFixed(1)
      : '0.0';
    let allAvgRisk = '0.0';
    if (allRowsForComparison && allRowsForComparison.length > 0) {
      const allRiskScores = allRowsForComparison.map(r => parseFloat_(r['fraud_risk_score'] || 0));
      if (allRiskScores.length > 0) {
        allAvgRisk = ((allRiskScores.reduce((a, b) => a + b, 0) / allRiskScores.length) * 100).toFixed(1);
      }
    }
    const severityCounts = { 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0 };
    riskScoresPercent.forEach(score => {
      if (score < 50) {
        severityCounts['LOW']++;
      } else if (score >= 50 && score <= 70) {
        severityCounts['MEDIUM']++;
      } else {
        severityCounts['HIGH']++;
      }
    });
    const severityBreakdown = [
      { name: 'LOW (<50%)', value: severityCounts['LOW'], color: colors.status.success || '#4CAF50' },
      { name: 'MEDIUM (50-70%)', value: severityCounts['MEDIUM'], color: colors.status.warning || '#FFA726' },
      { name: 'HIGH (>70%)', value: severityCounts['HIGH'], color: colors.accent.red }
    ].filter(item => item.value > 0);
    const monthlyTrend = {};
    rows.forEach(r => {
      const dateStr = r['created_at'] || r['pay_date'] || r['timestamp'] || '';
      if (dateStr) {
        const date = new Date(dateStr);
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        if (!monthlyTrend[monthKey]) {
          monthlyTrend[monthKey] = 0;
        }
        monthlyTrend[monthKey]++;
      }
    });
    const monthlyTrendData = Object.entries(monthlyTrend)
      .map(([month, count]) => ({ month, count }))
      .sort((a, b) => a.month.localeCompare(b.month));
    const employerCounts = {};
    rows.forEach(r => {
      const employer = r['employer_name'] || 'Unknown';
      if (!employer || employer === 'Unknown' || employer.toLowerCase() === 'unknown') {
        return;
      }
      employerCounts[employer] = (employerCounts[employer] || 0) + 1;
    });
    const topEmployersForFraudType = Object.entries(employerCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
    const employeeRiskDistribution = {};
    rows.forEach(r => {
      const employeeName = r['employee_name'] || 'Unknown';
      const riskScore = parseFloat_(r['fraud_risk_score'] || 0) * 100;
      if (!employeeRiskDistribution[employeeName]) {
        employeeRiskDistribution[employeeName] = {
          name: employeeName,
          avgRisk: 0,
          count: 0,
          totalRisk: 0
        };
      }
      employeeRiskDistribution[employeeName].count++;
      employeeRiskDistribution[employeeName].totalRisk += riskScore;
    });
    const employeeRiskData = Object.values(employeeRiskDistribution)
      .map(emp => ({
        ...emp,
        avgRisk: emp.totalRisk / emp.count
      }))
      .sort((a, b) => b.avgRisk - a.avgRisk)
      .slice(0, 10);
    const riskScoreRanges = { '0-25%': 0, '25-50%': 0, '50-75%': 0, '75-100%': 0 };
    riskScoresPercent.forEach(score => {
      if (score < 25) {
        riskScoreRanges['0-25%']++;
      } else if (score < 50) {
        riskScoreRanges['25-50%']++;
      } else if (score < 75) {
        riskScoreRanges['50-75%']++;
      } else {
        riskScoreRanges['75-100%']++;
      }
    });
    const riskScoreDistribution = Object.entries(riskScoreRanges)
      .map(([range, count]) => ({ range, count }))
      .filter(item => item.count > 0);
    const riskScoreTimeline = rows
      .map(r => {
        const dateStr = r['created_at'] || r['pay_date'] || r['timestamp'] || '';
        const date = dateStr ? new Date(dateStr) : new Date();
        const riskScore = parseFloat_(r['fraud_risk_score'] || 0) * 100;
        const employeeName = r['employee_name'] || 'Unknown';
        return {
          date: date.toISOString().split('T')[0],
          riskScore: parseFloat(riskScore.toFixed(1)),
          employeeName: employeeName,
          timestamp: date.getTime()
        };
      })
      .sort((a, b) => a.timestamp - b.timestamp)
      .slice(0, 50);
    const mediumRiskCasesCount = riskScoresPercent.filter(score => score >= 50 && score < 75).length;
    const highRiskCasesCount = riskScoresPercent.filter(score => score >= 75).length;
    fraudTypeSpecificData = {
      avgRiskComparison: {
        selectedFraudType: filteredAvgRisk,
        allPaystubs: allAvgRisk,
        fraudTypeName: selectedFraudType
      },
      severityBreakdown,
      monthlyTrend: monthlyTrendData,
      topEmployersForFraudType,
      employeeRiskDistribution: employeeRiskData,
      riskScoreDistribution,
      riskScoreTimeline,
      kpis: {
        mediumRiskCasesCount,
        highRiskCasesCount
      }
    };
  }

  // 9. Summary metrics
  const totalPaystubs = rows.length;
  const avgFraudRisk = ((riskScores.reduce((a, b) => a + b, 0) / riskScores.length) * 100).toFixed(1);
  const highRiskCount = riskScoresPercent.filter(s => s >= 75).length;
  const uniqueEmployers = Object.keys(employerRisks).length;
  const uniqueEmployees = Object.keys(employeeRisks).length;

  return {
    riskDistribution,
    recommendationData,
    riskLevelData,
    riskByEmployerData,
    topHighRiskEmployees,
    fraudTypeData,
    fraudTypeSpecificData,
    isFraudTypeFiltered,
    isSingleEmployerView,
    summary: {
      totalPaystubs,
      avgFraudRisk,
      highRiskCount,
      avgGrossPay,
      avgNetPay,
      maxGrossPay,
      minGrossPay,
      uniqueEmployers,
      uniqueEmployees
    }
  };
};
