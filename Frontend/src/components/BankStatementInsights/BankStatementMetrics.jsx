import { colors } from '../../styles/colors';

const BankStatementMetrics = ({ csvData, primary }) => {
  if (!csvData || !csvData.metrics) return null;

  const chartBoxStyle = {
    backgroundColor: colors.card,
    padding: '24px',
    borderRadius: '12px',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
  };

  return (
    <div data-metrics-section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
      <div style={chartBoxStyle}>
        <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
          Total Statements
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
          {csvData.metrics.totalStatements}
        </div>
      </div>
      <div style={chartBoxStyle}>
        <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
          Avg Risk Score
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
          {csvData.metrics.avgRiskScore}%
        </div>
      </div>
      <div style={chartBoxStyle}>
        <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
          Approve
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.success }}>
          {csvData.metrics.approveCount}
        </div>
      </div>
      <div style={chartBoxStyle}>
        <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
          Reject
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary }}>
          {csvData.metrics.rejectCount}
        </div>
      </div>
      <div style={chartBoxStyle}>
        <div style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '0.5rem' }}>
          Escalate
        </div>
        <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.status.warning }}>
          {csvData.metrics.escalateCount}
        </div>
      </div>
    </div>
  );
};

export default BankStatementMetrics;
