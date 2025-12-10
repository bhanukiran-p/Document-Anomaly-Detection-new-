import { colors } from '../../styles/colors';

const PaystubMetrics = ({ csvData, primary }) => {
  if (!csvData || !csvData.summary) return null;

  const styles = {
    kpiContainer: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '16px',
      marginBottom: '32px',
    },
    kpiCard: {
      backgroundColor: colors.card,
      padding: '20px',
      borderRadius: '8px',
      border: `1px solid ${colors.border}`,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      textAlign: 'center',
    },
    kpiValue: {
      fontSize: '2rem',
      fontWeight: 'bold',
      color: primary,
      marginBottom: '8px',
    },
    kpiLabel: {
      fontSize: '0.875rem',
      color: colors.mutedForeground,
    }
  };

  return (
    <div data-metrics-section style={styles.kpiContainer}>
      <div style={styles.kpiCard}>
        <div style={styles.kpiValue}>{csvData.summary.totalPaystubs}</div>
        <div style={styles.kpiLabel}>Total Paystubs</div>
      </div>
      <div style={styles.kpiCard}>
        <div style={styles.kpiValue}>{csvData.summary.avgFraudRisk}%</div>
        <div style={styles.kpiLabel}>Avg Fraud Risk</div>
      </div>
      <div style={styles.kpiCard}>
        <div style={styles.kpiValue}>{csvData.summary.avgGrossPay}</div>
        <div style={styles.kpiLabel}>Avg Gross Pay</div>
      </div>
      <div style={styles.kpiCard}>
        <div style={styles.kpiValue}>{csvData.summary.avgNetPay}</div>
        <div style={styles.kpiLabel}>Avg Net Pay</div>
      </div>
      <div style={styles.kpiCard}>
        <div style={styles.kpiValue}>{csvData.summary.uniqueEmployers}</div>
        <div style={styles.kpiLabel}>Unique Employers</div>
      </div>
      <div style={styles.kpiCard}>
        <div style={styles.kpiValue}>{csvData.summary.uniqueEmployees}</div>
        <div style={styles.kpiLabel}>Unique Employees</div>
      </div>
    </div>
  );
};

export default PaystubMetrics;
