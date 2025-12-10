import { colors } from '../../styles/colors';

const CheckMetrics = ({ csvData, primary }) => {
  if (!csvData || !csvData.metrics) return null;

  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem',
    marginBottom: '2rem',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    border: `1px solid ${colors.border}`,
  };

  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  };

  const metricCardStyle = {
    backgroundColor: colors.secondary,
    padding: '1.5rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    textAlign: 'center',
  };

  return (
    <div data-metrics-section>
      <div style={cardStyle}>
        <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>Summary Metrics</h2>
        <div style={metricsGridStyle}>
          <div style={metricCardStyle}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
              {csvData.metrics.totalChecks}
            </div>
            <div style={{ color: colors.mutedForeground }}>Total Checks</div>
          </div>

          <div style={metricCardStyle}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
              {csvData.metrics.avgRiskScore}%
            </div>
            <div style={{ color: colors.mutedForeground }}>Avg Risk Score</div>
          </div>

          <div style={metricCardStyle}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981', marginBottom: '0.5rem' }}>
              {csvData.metrics.approveCount}
            </div>
            <div style={{ color: colors.mutedForeground }}>Approve</div>
          </div>

          <div style={metricCardStyle}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#ef4444', marginBottom: '0.5rem' }}>
              {csvData.metrics.rejectCount}
            </div>
            <div style={{ color: colors.mutedForeground }}>Reject</div>
          </div>

          <div style={metricCardStyle}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b', marginBottom: '0.5rem' }}>
              {csvData.metrics.escalateCount}
            </div>
            <div style={{ color: colors.mutedForeground }}>Escalate</div>
          </div>

          <div style={metricCardStyle}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
              {csvData.metrics.highRiskCount || 0}
            </div>
            <div style={{ color: colors.mutedForeground }}>High-Risk Count (&gt;75%)</div>
          </div>

          <div style={metricCardStyle}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: primary, marginBottom: '0.5rem' }}>
              {csvData.metrics.repeatOffenders || 0}
            </div>
            <div style={{ color: colors.mutedForeground }}>Repeat Offenders</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckMetrics;
