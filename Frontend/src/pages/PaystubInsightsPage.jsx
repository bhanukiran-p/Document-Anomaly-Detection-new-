import { useNavigate } from 'react-router-dom';
import PaystubInsights from '../components/PaystubInsights';
import { colors } from '../styles/colors';

const PaystubInsightsPage = () => {
  const navigate = useNavigate();
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  const backButtonStyle = {
    backgroundColor: 'transparent',
    color: colors.foreground,
    border: `2px solid ${colors.border}`,
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: 'pointer',
    marginBottom: '1.5rem',
    transition: 'all 0.3s',
  };

  const containerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '1.5rem',
    backgroundColor: colors.background,
  };

  return (
    <div style={containerStyle}>
      <button
        style={backButtonStyle}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = colors.muted;
          e.target.style.borderColor = primary;
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = 'transparent';
          e.target.style.borderColor = colors.border;
        }}
        onClick={() => navigate('/all-documents-insights')}
      >
        ← Back to Unified Dashboard
      </button>
      <PaystubInsights />
    </div>
  );
};

export default PaystubInsightsPage;
