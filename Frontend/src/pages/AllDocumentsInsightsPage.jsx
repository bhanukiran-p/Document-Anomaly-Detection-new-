import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import AllDocumentsInsights from '../components/AllDocumentsInsights';

const AllDocumentsInsightsPage = () => {
  const navigate = useNavigate();
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  const backButtonStyle = {
    backgroundColor: 'transparent',
    color: colors.foreground,
    border: `2px solid ${colors.border}`,
    padding: '0.75rem 1.5rem',
    borderRadius: '9999px',
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: 'pointer',
    marginBottom: '1.5rem',
    transition: 'all 0.3s',
  };

  const headerStyle = {
    background: colors.gradients.dark,
    padding: '2rem',
    borderRadius: '0.75rem',
    color: colors.foreground,
    textAlign: 'center',
    marginBottom: '2rem',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
  };

  const titleStyle = {
    fontSize: '2.25rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
    color: colors.foreground,
  };

  const subtitleStyle = {
    fontSize: '1.125rem',
    color: colors.mutedForeground,
  };

  const containerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '1.5rem',
    backgroundColor: colors.background,
    minHeight: '100vh',
    color: colors.foreground,
  };

  return (
    <div style={containerStyle}>
      <button 
        style={backButtonStyle}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = colors.muted;
          e.target.style.borderColor = primary;
          e.target.style.transform = 'translateY(-2px)';
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = 'transparent';
          e.target.style.borderColor = colors.border;
          e.target.style.transform = 'translateY(0)';
        }}
        onClick={() => navigate('/finance')}
      >
        ← Back to Document Analysis
      </button>

      <div style={headerStyle}>
        <h1 style={titleStyle}>
          Unified Document <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Insights Dashboard</span>
        </h1>
        <p style={subtitleStyle}>
          Comprehensive analysis across all document types
        </p>
      </div>

      <AllDocumentsInsights />
    </div>
  );
};

export default AllDocumentsInsightsPage;

