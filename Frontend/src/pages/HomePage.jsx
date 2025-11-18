import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';

const HomePage = () => {
  const navigate = useNavigate();
  
  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  
  const containerStyle = {
    maxWidth: '1300px',
    margin: '0 auto',
    padding: '1.5rem',
    backgroundColor: colors.background,
    minHeight: '100vh',
    color: colors.foreground,
  };
  
  const headerStyle = {
    background: colors.gradients.navy,
    padding: '2rem',
    borderRadius: '0.75rem',
    color: colors.foreground,
    textAlign: 'center',
    marginBottom: '1.5rem',
    border: `1px solid ${colors.border}`,
  };
  
  const titleStyle = {
    fontSize: '2rem',
    fontWeight: '700',
    marginBottom: '0.5rem',
    color: colors.foreground,
  };
  
  const subtitleStyle = {
    fontSize: '1.125rem',
    color: colors.mutedForeground,
  };
  
  const cardsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '1.5rem',
    marginBottom: '2rem',
    maxWidth: '900px',
    margin: '0 auto 2rem auto',
  };
  
  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '1.5rem',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    border: `1px solid ${colors.border}`,
    borderTop: `4px solid ${primary}`,
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
    color: colors.foreground,
    marginBottom: '0.75rem',
  };
  
  const cardDescStyle = {
    color: colors.mutedForeground,
    lineHeight: '1.5',
    marginBottom: 'auto',
    fontSize: '0.9rem',
    flex: 1,
    paddingBottom: '1.5rem',
  };
  
  const buttonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
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
          e.target.style.backgroundColor = colors.muted;
          e.target.style.borderColor = primary;
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = 'transparent';
          e.target.style.borderColor = colors.border;
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
      
      <div style={{
        backgroundColor: colors.card,
        padding: '1.5rem',
        borderRadius: '0.75rem',
        marginBottom: '1rem',
        border: `1px solid ${colors.border}`,
      }}>
        <h3 style={{ color: colors.foreground, marginBottom: '0.75rem', fontSize: '1.125rem' }}>About XFORIA DAD</h3>
        <div style={{ color: colors.mutedForeground, lineHeight: '1.5', fontSize: '0.9rem' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong>Supported:</strong> Checks (Axis, BOA, ICICI, HDFC, Chase, Wells Fargo) • Paystubs (US & International) • Money Orders (Western Union, MoneyGram, USPS) • Bank Statements (All major banks)
          </p>
          <p>
            <strong>Features:</strong> Real-time OCR • AI-powered extraction • Transaction history parsing • High accuracy scoring • JSON export • PDF & Image support
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

