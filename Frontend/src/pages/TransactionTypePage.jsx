import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { FaChartLine, FaFileUpload } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

const TransactionTypePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuth();

  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  const logoutButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    padding: '0.5rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'transform 0.2s',
  };

  const logoutImageStyle = {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
  };

  const pageStyle = {
    minHeight: '100vh',
    backgroundColor: colors.background,
    display: 'flex',
    flexDirection: 'column',
    color: colors.foreground,
  };
  
  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem 1.5rem 0.75rem 0.5rem',
    backgroundColor: colors.card,
    borderBottom: `1px solid ${colors.border}`,
  };
  
  const logoContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginLeft: '-0.5rem',
  };
  
  const logoImageStyle = {
    height: '75px',
    width: 'auto',
    objectFit: 'contain',
    display: 'block',
  };
  
  const taglineStyle = {
    fontSize: '0.875rem',
    fontWeight: '500',
    color: primary,
    whiteSpace: 'nowrap',
  };
  
  const loginButtonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '0.625rem 1.5rem',
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'all 0.3s',
    boxShadow: `0 0 20px ${primary}40`,
  };
  
  const mainContentStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
    background: colors.gradients.dark,
  };
  
  const dadLogoStyle = {
    height: '150px',
    width: 'auto',
    objectFit: 'contain',
    display: 'block',
    marginBottom: '1.5rem',
  };
  
  const titleStyle = {
    fontSize: '2rem',
    fontWeight: '700',
    color: colors.foreground,
    marginBottom: '0.5rem',
    textAlign: 'center',
  };
  
  const subtitleStyle = {
    fontSize: '1rem',
    color: colors.mutedForeground,
    marginBottom: '2rem',
    textAlign: 'center',
  };
  
  const cardsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '2rem',
    maxWidth: '900px',
    width: '100%',
  };
  
  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem 1.5rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    transition: 'transform 0.3s, box-shadow 0.3s',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    border: `1px solid ${colors.border}`,
    minHeight: '320px',
  };
  
  const iconCircleStyle = {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    backgroundColor: primary,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '1.5rem',
    fontSize: '2rem',
    color: colors.primaryForeground,
  };
  
  const cardTitleStyle = {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: colors.foreground,
    marginBottom: '0.75rem',
  };
  
  const cardDescStyle = {
    fontSize: '0.95rem',
    color: colors.mutedForeground,
    lineHeight: '1.5',
    marginBottom: '2rem',
    flex: 1,
  };
  
  const activeButtonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '0.875rem 2rem',
    borderRadius: '0.5rem',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    width: '100%',
    transition: 'all 0.3s',
    boxShadow: `0 0 20px ${primary}40`,
  };
  
  const disabledButtonStyle = {
    backgroundColor: colors.muted,
    color: colors.mutedForeground,
    padding: '0.875rem 2rem',
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
    cursor: 'not-allowed',
    fontSize: '1rem',
    fontWeight: '600',
    width: '100%',
  };
  
  const footerStyle = {
    backgroundColor: colors.card,
    color: colors.foreground,
    padding: '1.25rem 2rem',
    textAlign: 'center',
    borderTop: `1px solid ${colors.border}`,
  };
  
  const footerTextStyle = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
    fontSize: '0.875rem',
  };
  
  const separatorStyle = {
    color: colors.mutedForeground,
  };
  
  return (
    <div style={pageStyle}>
      {/* Header */}
      <header style={headerStyle}>
        <div 
          style={{ ...logoContainerStyle, cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          <img src="/New_FD.png" alt="XFORIA DAD Logo" style={logoImageStyle} />
          <div style={taglineStyle}>Your Guardian against Fraud</div>
        </div>
        
        {!isAuthenticated ? (
          <button
            style={loginButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.transform = 'scale(1.05)';
              e.target.style.boxShadow = `0 0 30px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'scale(1)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
            onClick={() => navigate('/login')}
          >
            Login →
          </button>
        ) : (
          <button
            style={logoutButtonStyle}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
            onClick={() => {
              logout();
              navigate('/');
            }}
            title="Logout"
          >
            <img
              src="/exit-door.png"
              alt="Logout"
              style={logoutImageStyle}
            />
          </button>
        )}
      </header>
      
      {/* Main Content */}
      <main style={mainContentStyle}>
        <img src="/DAD_red_black.png" alt="DAD Logo" style={dadLogoStyle} />
        <h1 style={titleStyle}>Choose Transaction Type</h1>
        <p style={subtitleStyle}>Select your preferred fraud detection method</p>
        
        <div style={cardsContainerStyle}>
          {/* On Demand Transactions - LEFT SIDE - ACTIVE */}
          <div
            style={cardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-8px)';
              e.currentTarget.style.boxShadow = `0 12px 40px ${primary}30`;
              e.currentTarget.style.borderColor = primary;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
              e.currentTarget.style.borderColor = colors.border;
            }}
          >
            <div style={iconCircleStyle}>
              <FaFileUpload />
            </div>
            <h2 style={cardTitleStyle}>On Demand Transactions</h2>
            <p style={cardDescStyle}>
              Upload and analyze with comprehensive fraud assessment
            </p>
            
            <button
              style={activeButtonStyle}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = `0 6px 30px ${primary}60`;
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = `0 0 20px ${primary}40`;
              }}
              onClick={() => navigate('/finance')}
            >
              On Demand Transactions
            </button>
          </div>
          
          {/* Real Time Transaction - RIGHT SIDE - COMING SOON */}
          <div
            style={{ ...cardStyle, opacity: 0.7 }}
          >
            <div style={iconCircleStyle}>
              <FaChartLine />
            </div>
            <h2 style={cardTitleStyle}>Real Time Transaction</h2>
            <p style={cardDescStyle}>
              Analyze transactions instantly with real-time fraud detection
            </p>
            
            <button style={disabledButtonStyle}>
              COMING SOON
            </button>
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer style={footerStyle}>
        <div style={footerTextStyle}>
          <span>Where Innovation Meets Security</span>
          <span style={separatorStyle}>|</span>
          <span>Zero Tolerance for Fraud</span>
          <span style={separatorStyle}>|</span>
          <span>© Xforia DAD</span>
        </div>
      </footer>
    </div>
  );
};

export default TransactionTypePage;
