import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';

const HomePage = () => {
  const navigate = useNavigate();
  
  const containerStyle = {
    maxWidth: '1300px',
    margin: '0 auto',
    padding: '1.5rem',
  };
  
  const headerStyle = {
    background: `linear-gradient(135deg, ${colors.primary.navy} 0%, ${colors.primary.blue} 100%)`,
    padding: '2rem',
    borderRadius: '12px',
    color: colors.neutral.white,
    textAlign: 'center',
    marginBottom: '1.5rem',
  };
  
  const titleStyle = {
    fontSize: '2rem',
    fontWeight: '700',
    marginBottom: '0.5rem',
  };
  
  const subtitleStyle = {
    fontSize: '1.125rem',
    opacity: 0.9,
  };
  
  const cardsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1.5rem',
    marginBottom: '2rem',
  };
  
  const cardStyle = {
    backgroundColor: colors.background.card,
    borderRadius: '12px',
    padding: '1.5rem',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    borderTop: `4px solid ${colors.primary.navy}`,
    transition: 'transform 0.2s, box-shadow 0.2s',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    minHeight: '220px',
    justifyContent: 'space-between',
  };
  
  const cardTitleStyle = {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: colors.primary.navy,
    marginBottom: '0.75rem',
  };
  
  const cardDescStyle = {
    color: colors.neutral.gray600,
    lineHeight: '1.5',
    marginBottom: 'auto',
    fontSize: '0.9rem',
    flex: 1,
    paddingBottom: '1.5rem',
  };
  
  const buttonStyle = {
    backgroundColor: colors.accent.red,
    color: colors.neutral.white,
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
    fontWeight: '600',
    border: 'none',
    cursor: 'pointer',
    width: '100%',
    transition: 'background-color 0.2s',
    marginTop: 'auto',
  };
  
  const backButtonStyle = {
    backgroundColor: 'transparent',
    color: colors.primary.navy,
    border: `2px solid ${colors.primary.navy}`,
    padding: '0.625rem 1.5rem',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: 'pointer',
    marginBottom: '1.5rem',
    transition: 'all 0.2s',
  };
  
  return (
    <div style={containerStyle}>
      <button 
        style={backButtonStyle}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = colors.primary.navy;
          e.target.style.color = colors.neutral.white;
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = 'transparent';
          e.target.style.color = colors.primary.navy;
        }}
        onClick={() => navigate('/transaction-type')}
      >
        ← Back to Transaction Types
      </button>
      
      <div style={headerStyle}>
        <h1 style={titleStyle}>Document Analysis</h1>
        <p style={subtitleStyle}>
          Where Innovation Meets Security
        </p>
      </div>
      
      <div style={cardsContainerStyle}>
        <div 
          style={cardStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 8px 12px rgba(0,0,0,0.15)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
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
            onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
            onMouseLeave={(e) => e.target.style.backgroundColor = colors.accent.red}
            onClick={() => navigate('/check-analysis')}
          >
            Analyze Checks
          </button>
        </div>
        
        <div 
          style={cardStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 8px 12px rgba(0,0,0,0.15)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
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
            onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
            onMouseLeave={(e) => e.target.style.backgroundColor = colors.accent.red}
            onClick={() => navigate('/paystub-analysis')}
          >
            Analyze Paystubs
          </button>
        </div>

        <div
          style={cardStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 8px 12px rgba(0,0,0,0.15)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
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
            onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
            onMouseLeave={(e) => e.target.style.backgroundColor = colors.accent.red}
            onClick={() => navigate('/money-order-analysis')}
          >
            Analyze Money Orders
          </button>
        </div>
      </div>
      
      <div style={{
        backgroundColor: colors.primary.lightBlue,
        padding: '1.5rem',
        borderRadius: '12px',
        marginBottom: '1rem',
      }}>
        <h3 style={{ color: colors.primary.navy, marginBottom: '0.75rem', fontSize: '1.125rem' }}>About XFORIA DAD</h3>
        <div style={{ color: colors.neutral.gray700, lineHeight: '1.5', fontSize: '0.9rem' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong>Supported:</strong> Checks (Axis, BOA, ICICI, HDFC, Chase, Wells Fargo) • Paystubs (US & International) • Money Orders (Western Union, MoneyGram, USPS)
          </p>
          <p>
            <strong>Features:</strong> Real-time OCR • AI-powered extraction • High accuracy scoring • JSON export • PDF & Image support
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

