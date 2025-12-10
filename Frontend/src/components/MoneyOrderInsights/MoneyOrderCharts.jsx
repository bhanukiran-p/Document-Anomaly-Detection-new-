import { colors } from '../../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const MoneyOrderCharts = ({ csvData, issuerFilter, primary, COLORS }) => {
  if (!csvData) return null;

  const chartsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '20px',
    marginTop: '2rem'
  };

  const chartBoxStyle = {
    backgroundColor: colors.card,
    padding: '24px',
    borderRadius: '12px',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    transition: 'all 0.3s ease',
  };

  const chartTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: colors.foreground,
    marginBottom: '20px',
    paddingBottom: '12px',
    borderBottom: `2px solid ${colors.border}`,
  };

  return (
    <>
      {/* Charts Section - 3 rows x 2 columns grid */}
      <div style={chartsContainerStyle}>
        {/* Row 1: Fraud Severity Breakdown & AI Recommendation Breakdown */}
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Fraud Severity Breakdown</h3>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={csvData.fraudSeverityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                innerRadius={40}
                fill="#8884d8"
                dataKey="value"
              >
                {csvData.fraudSeverityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`,
                  color: colors.foreground
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={csvData.recommendationData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={100}
                innerRadius={40}
                fill="#8884d8"
                dataKey="value"
              >
                {csvData.recommendationData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`,
                  color: colors.foreground
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Row 2: Risk by Issuer / Top Risky Purchasers */}
        {(!issuerFilter || issuerFilter === '' || issuerFilter === 'All Issuers') && csvData.riskByIssuerData && csvData.riskByIssuerData.length > 0 && (
          <div style={chartBoxStyle}>
            <h3 style={chartTitleStyle}>Risk Level by Issuer</h3>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={csvData.riskByIssuerData}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis dataKey="name" stroke={colors.mutedForeground} />
                <YAxis stroke={colors.mutedForeground} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: colors.card,
                    border: `1px solid ${colors.border}`,
                    color: colors.foreground
                  }}
                />
                <Legend />
                <Bar dataKey="avgRisk" fill={colors.status.warning} name="Avg Risk Score (%)" />
                <Bar dataKey="count" fill={colors.status.success} name="Money Order Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {csvData.isSingleIssuerView && csvData.topRiskyPurchasersForIssuer && csvData.topRiskyPurchasersForIssuer.length > 0 && (
          <div style={chartBoxStyle}>
            <h3 style={chartTitleStyle}>Top Risky Purchasers ({csvData.selectedIssuerName})</h3>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={csvData.topRiskyPurchasersForIssuer} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis
                  type="number"
                  stroke={colors.mutedForeground}
                  label={{ value: 'High-Risk Money Orders', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke={colors.mutedForeground}
                  width={180}
                  tick={{ fill: colors.foreground, fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: colors.card,
                    border: `1px solid ${colors.border}`,
                    color: colors.foreground
                  }}
                  formatter={(value, name) => {
                    if (name === 'highRiskCount') return [`${value} high-risk MOs`, 'High-Risk Count'];
                    if (name === 'totalCount') return [value, 'Total MOs'];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Purchaser: ${label}`}
                />
                <Bar dataKey="highRiskCount" fill={primary} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Row 3: Top Fraudulent Issuers / Top High-Risk Purchasers & Top High-Risk Payees */}
        {(!issuerFilter || issuerFilter === '' || issuerFilter === 'All Issuers') && csvData.topFraudulentIssuers && csvData.topFraudulentIssuers.length > 0 && (
          <div style={chartBoxStyle}>
            <h3 style={chartTitleStyle}>Top Fraudulent Issuers (% High-Risk MOs &gt;75%)</h3>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={csvData.topFraudulentIssuers} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis
                  type="number"
                  stroke={colors.mutedForeground}
                  label={{ value: 'High-Risk Percentage (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke={colors.mutedForeground}
                  width={180}
                  tick={{ fill: colors.foreground, fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: colors.card,
                    border: `1px solid ${colors.border}`,
                    color: colors.foreground
                  }}
                  formatter={(value, name) => {
                    if (name === 'highRiskPercent') return [`${value}%`, 'High-Risk %'];
                    if (name === 'highRiskCount') return [value, 'High-Risk Count'];
                    if (name === 'totalCount') return [value, 'Total MOs'];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Issuer: ${label}`}
                />
                <Bar dataKey="highRiskPercent" fill={primary} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {!csvData.isSingleIssuerView && csvData.topHighRiskPurchasers && csvData.topHighRiskPurchasers.length > 0 && (
          <div style={chartBoxStyle}>
            <h3 style={chartTitleStyle}>Top High-Risk Purchasers</h3>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={csvData.topHighRiskPurchasers} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis
                  type="number"
                  stroke={colors.mutedForeground}
                  label={{ value: 'Average Risk Score (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke={colors.mutedForeground}
                  width={180}
                  tick={{ fill: colors.foreground, fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: colors.card,
                    border: `1px solid ${colors.border}`,
                    color: colors.foreground
                  }}
                  formatter={(value, name) => {
                    if (name === 'avgRisk') return [`${value}%`, 'Avg Risk'];
                    if (name === 'count') return [value, 'Money Orders'];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Purchaser: ${label}`}
                />
                <Bar dataKey="avgRisk" fill={primary} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Row 3: Top High-Risk Payees */}
        {csvData.topHighRiskPayees && csvData.topHighRiskPayees.length > 0 && (
          <div style={chartBoxStyle}>
            <h3 style={chartTitleStyle}>Top High-Risk Payees</h3>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={csvData.topHighRiskPayees} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis
                  type="number"
                  stroke={colors.mutedForeground}
                  label={{ value: 'High-Risk Count', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke={colors.mutedForeground}
                  width={180}
                  tick={{ fill: colors.foreground, fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: colors.card,
                    border: `1px solid ${colors.border}`,
                    color: colors.foreground
                  }}
                  formatter={(value, name) => {
                    if (name === 'highRiskCount') return [value, 'High-Risk Count'];
                    if (name === 'count') return [value, 'Total MOs'];
                    if (name === 'avgRisk') return [`${value}%`, 'Avg Risk'];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Payee: ${label}`}
                />
                <Bar dataKey="highRiskCount" fill={primary} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* High-Risk Money Orders Over Time - Full Width */}
      {csvData.fraudTrendData && csvData.fraudTrendData.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>
            High-Risk Money Orders Over Time{csvData.isSingleIssuerView && csvData.selectedIssuerName ? ` (${csvData.selectedIssuerName})` : ''}
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={csvData.fraudTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
              <XAxis dataKey="date" stroke={colors.mutedForeground} />
              <YAxis
                yAxisId="left"
                stroke={colors.mutedForeground}
                label={{ value: 'Avg Risk Score (%)', angle: -90, position: 'insideLeft', style: { fill: colors.foreground } }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke={colors.mutedForeground}
                label={{ value: 'High-Risk Count', angle: 90, position: 'insideRight', style: { fill: colors.foreground } }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`,
                  color: colors.foreground
                }}
              />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="avgRisk" stroke={primary} strokeWidth={2} name="Avg Risk Score %" />
              <Line yAxisId="right" type="monotone" dataKey="highRiskCount" stroke="#ef4444" strokeWidth={2} name="High-Risk Count" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </>
  );
};

export default MoneyOrderCharts;
