import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { FaChartLine, FaFileUpload } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

const TransactionTypePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuth();

  const logoutButtonStyle = {
    backgroundColor: colors.accent.red,
    color: colors.neutral.white,
    padding: '0.625rem 1.5rem',
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'background-color 0.2s',
  };

  const pageStyle = {
    minHeight: '100vh',
    backgroundColor: colors.neutral.white,
    display: 'flex',
    flexDirection: 'column',
  };
  
  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem 2.5rem',
    backgroundColor: colors.neutral.white,
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
  };
  
  const logoContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  };
  
  const logoImageStyle = {
    height: '50px',
    width: 'auto',
  };
  
  const taglineStyle = {
    fontSize: '1rem',
    fontWeight: '500',
    color: colors.accent.red,
  };
  
  const loginButtonStyle = {
    backgroundColor: colors.primary.blue,
    color: colors.neutral.white,
    padding: '0.625rem 1.5rem',
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'background-color 0.2s',
  };
  
  const mainContentStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
  };
  
  const dadLogoStyle = {
    height: '80px',
    width: 'auto',
    marginBottom: '1.5rem',
  };
  
  const titleStyle = {
    fontSize: '2rem',
    fontWeight: '700',
    color: colors.primary.navy,
    marginBottom: '0.5rem',
    textAlign: 'center',
  };
  
  const subtitleStyle = {
    fontSize: '1rem',
    color: colors.neutral.gray600,
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
    backgroundColor: '#F8F9FA',
    borderRadius: '12px',
    padding: '2rem 1.5rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    transition: 'transform 0.3s, box-shadow 0.3s',
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
    minHeight: '320px',
  };
  
  const iconCircleStyle = {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    backgroundColor: colors.primary.navy,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '1.5rem',
    fontSize: '2rem',
    color: colors.neutral.white,
  };
  
  const cardTitleStyle = {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: colors.primary.navy,
    marginBottom: '0.75rem',
  };
  
  const cardDescStyle = {
    fontSize: '0.95rem',
    color: colors.neutral.gray600,
    lineHeight: '1.5',
    marginBottom: '2rem',
    flex: 1,
  };
  
  const activeButtonStyle = {
    backgroundColor: colors.accent.red,
    color: colors.neutral.white,
    padding: '0.875rem 2rem',
    borderRadius: '0.5rem',
    border: 'none',
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    width: '100%',
    transition: 'background-color 0.2s',
  };
  
  const disabledButtonStyle = {
    backgroundColor: colors.primary.lightBlue,
    color: colors.primary.blue,
    padding: '0.875rem 2rem',
    borderRadius: '0.5rem',
    border: 'none',
    cursor: 'not-allowed',
    fontSize: '1rem',
    fontWeight: '600',
    width: '100%',
  };
  
  const footerStyle = {
    backgroundColor: colors.primary.navy,
    color: colors.neutral.white,
    padding: '1.25rem 2rem',
    textAlign: 'center',
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
    color: colors.neutral.gray400,
  };
  
  return (
    <div style={pageStyle}>
      {/* Header */}
      <header style={headerStyle}>
        <div 
          style={{ ...logoContainerStyle, cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          <img src="/logo.png" alt="XFORIA DAD Logo" style={logoImageStyle} />
          <div style={taglineStyle}>Your Guardian against Fraud</div>
        </div>
        
        {!isAuthenticated ? (
          <button
            style={loginButtonStyle}
            onMouseEnter={(e) => e.target.style.backgroundColor = colors.primary.navy}
            onMouseLeave={(e) => e.target.style.backgroundColor = colors.primary.blue}
            onClick={() => navigate('/login')}
          >
            Login →
          </button>
        ) : (
          <button
            style={logoutButtonStyle}
            onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
            onMouseLeave={(e) => e.target.style.backgroundColor = colors.accent.red}
            onClick={() => {
              logout();
              navigate('/');
            }}
          >
            Logout
          </button>
        )}
      </header>
      
      {/* Main Content */}
      <main style={mainContentStyle}>
        <img src="/dad-logo.png" alt="DAD Logo" style={dadLogoStyle} />
        <h1 style={titleStyle}>Choose Transaction Type</h1>
        <p style={subtitleStyle}>Select your preferred fraud detection method</p>
        
        <div style={cardsContainerStyle}>
          {/* On Demand Transactions - LEFT SIDE - ACTIVE */}
          <div
            style={cardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-8px)';
              e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
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
              onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
              onMouseLeave={(e) => e.target.style.backgroundColor = colors.accent.red}
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

