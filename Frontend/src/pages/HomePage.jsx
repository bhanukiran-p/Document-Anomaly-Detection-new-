import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { useScrollAnimation } from '../hooks/useScrollAnimation';

const HomePage = () => {
  const navigate = useNavigate();
  
  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  
  const containerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '1.5rem',
    backgroundColor: colors.background,
    minHeight: '100vh',
    color: colors.foreground,
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
  
  const cardsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '2rem',
    marginBottom: '2rem',
    maxWidth: '1200px',
    margin: '0 auto 2rem auto',
  };
  
  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    border: `1px solid ${colors.border}`,
    transition: 'all 0.3s',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    minHeight: '280px',
    justifyContent: 'space-between',
  };
  
  const cardTitleStyle = {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: colors.foreground,
    marginBottom: '1rem',
  };
  
  const cardDescStyle = {
    color: colors.mutedForeground,
    lineHeight: '1.6',
    marginBottom: 'auto',
    fontSize: '1rem',
    flex: 1,
    paddingBottom: '1.5rem',
  };
  
  const buttonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '1rem 2rem',
    borderRadius: '999px',
    fontSize: '1rem',
    fontWeight: '600',
    border: 'none',
    cursor: 'pointer',
    width: '100%',
    transition: 'all 0.3s',
    marginTop: 'auto',
    boxShadow: `0 0 20px ${primary}40`,
  };
  
  const backButtonStyle = {
    backgroundColor: 'transparent',
    color: colors.foreground,
    border: `2px solid ${colors.border}`,
    padding: '0.75rem 1.5rem',
    borderRadius: '9999px', // Pill shape
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: 'pointer',
    marginBottom: '1.5rem',
    transition: 'all 0.3s',
  };

  const insightsSection = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    border: `1px solid ${colors.border}`,
    marginTop: '2rem',
    maxWidth: '1200px',
    margin: '2rem auto 0',
  };

  const insightsTitleStyle = {
    fontSize: '1.75rem',
    fontWeight: 'bold',
    color: colors.foreground,
    marginBottom: '1.5rem',
    textAlign: 'center',
  };

  const tabsContainerStyle = {
    display: 'flex',
    gap: '1rem',
    marginBottom: '2rem',
    justifyContent: 'center',
  };

  const tabButtonStyle = (isActive) => ({
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    fontWeight: '600',
    border: `2px solid ${isActive ? primary : colors.border}`,
    backgroundColor: isActive ? `${primary}20` : 'transparent',
    color: isActive ? primary : colors.mutedForeground,
    cursor: 'pointer',
    transition: 'all 0.3s',
  });

  const { ref, isVisible } = useScrollAnimation();
  
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
        onClick={() => navigate('/transaction-type')}
      >
        ← Back to Transaction Types
      </button>
      
      <div style={headerStyle}>
        <h1 style={titleStyle}>
          Document <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Analysis</span>
        </h1>
        <p style={subtitleStyle}>
          Where Innovation Meets Security
        </p>
      </div>
      
      <div style={cardsContainerStyle} ref={ref}>
        <div 
          style={{
            ...cardStyle,
            opacity: isVisible ? 1 : 0,
            transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
            transition: 'all 0.5s ease-out 0s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-8px)';
            e.currentTarget.style.borderColor = `${primary}80`;
            e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = isVisible ? 'translateY(0)' : 'translateY(20px)';
            e.currentTarget.style.borderColor = colors.border;
            e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
          }}
        >
          <div>
            <h2 style={cardTitleStyle}>Check Analysis</h2>
            <p style={cardDescStyle}>
              Extract payee, amount, bank details, routing numbers, and signatures from checks with AI-powered OCR
            </p>
          </div>
          
          <button 
            style={buttonStyle}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = `0 6px 30px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
            onClick={() => navigate('/check-analysis')}
          >
            Analyze Checks
          </button>
        </div>
        
        <div 
          style={{
            ...cardStyle,
            opacity: isVisible ? 1 : 0,
            transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
            transition: 'all 0.5s ease-out 0.15s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-8px)';
            e.currentTarget.style.borderColor = `${primary}80`;
            e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = isVisible ? 'translateY(0)' : 'translateY(20px)';
            e.currentTarget.style.borderColor = colors.border;
            e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
          }}
        >
          <div>
            <h2 style={cardTitleStyle}>Paystub Analysis</h2>
            <p style={cardDescStyle}>
              Extract employee information, gross & net pay, tax details, and YTD totals from paystubs
            </p>
          </div>
          
          <button
            style={buttonStyle}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = `0 6px 30px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
            onClick={() => navigate('/paystub-analysis')}
          >
            Analyze Paystubs
          </button>
        </div>

        <div
          style={{
            ...cardStyle,
            opacity: isVisible ? 1 : 0,
            transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
            transition: 'all 0.5s ease-out 0.3s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-8px)';
            e.currentTarget.style.borderColor = `${primary}80`;
            e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = isVisible ? 'translateY(0)' : 'translateY(20px)';
            e.currentTarget.style.borderColor = colors.border;
            e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
          }}
        >
          <div>
            <h2 style={cardTitleStyle}>Money Order Analysis</h2>
            <p style={cardDescStyle}>
              Identify issuers, extract serial numbers, amounts, and detect fraud with high amount alerts
            </p>
          </div>

          <button
            style={buttonStyle}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = `0 6px 30px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
            onClick={() => navigate('/money-order-analysis')}
          >
            Analyze Money Orders
          </button>
        </div>

        <div
          style={{
            ...cardStyle,
            opacity: isVisible ? 1 : 0,
            transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
            transition: 'all 0.5s ease-out 0.45s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-8px)';
            e.currentTarget.style.borderColor = `${primary}80`;
            e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = isVisible ? 'translateY(0)' : 'translateY(20px)';
            e.currentTarget.style.borderColor = colors.border;
            e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
          }}
        >
          <div>
            <h2 style={cardTitleStyle}>Bank Statement Analysis</h2>
            <p style={cardDescStyle}>
              Extract account details, balances, transaction history, and financial summaries from bank statements
            </p>
          </div>

          <button
            style={buttonStyle}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = `0 6px 30px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
            onClick={() => navigate('/bank-statement-analysis')}
          >
            Analyze Bank Statements
          </button>
        </div>
      </div>

      <div style={insightsSection}>
        <h2 style={insightsTitleStyle}>Financial Insights</h2>
        <p style={{ color: colors.mutedForeground, textAlign: 'center', marginBottom: '2rem' }}>
          View comprehensive insights across all document types
        </p>

        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            style={{
              ...buttonStyle,
              maxWidth: '400px',
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = `0 6px 30px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
            onClick={() => navigate('/all-documents-insights')}
          >
            Unified Document Insights Dashboard
          </button>
        </div>
      </div>

    </div>
  );
};

export default HomePage;
