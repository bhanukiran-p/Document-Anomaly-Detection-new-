import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { colors } from '../styles/colors';

const Header = () => {
  const location = useLocation();
  
  const headerStyle = {
    backgroundColor: colors.neutral.white,
    borderBottom: `2px solid ${colors.primary.navy}`,
    padding: '1rem 2rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  };
  
  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  };
  
  const logoTextStyle = {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: colors.primary.navy,
    textDecoration: 'none',
  };
  
  const taglineStyle = {
    fontSize: '0.875rem',
    color: colors.neutral.gray600,
  };
  
  const navStyle = {
    display: 'flex',
    gap: '1.5rem',
    alignItems: 'center',
  };
  
  const linkStyle = (isActive) => ({
    padding: '0.5rem 1rem',
    borderRadius: '0.375rem',
    fontWeight: '500',
    backgroundColor: isActive ? colors.primary.lightBlue : 'transparent',
    color: isActive ? colors.primary.navy : colors.neutral.gray700,
    transition: 'all 0.2s',
    textDecoration: 'none',
  });
  
  return (
    <header style={headerStyle}>
      <Link to="/" style={logoStyle}>
        <div style={logoTextStyle}>
          XFORIA DAD
        </div>
        <div style={taglineStyle}>
          Your Guardian against Fraud
        </div>
      </Link>
      
      <nav style={navStyle}>
        <Link
          to="/"
          style={linkStyle(location.pathname === '/')}
        >
          Home
        </Link>
        <Link
          to="/check-analysis"
          style={linkStyle(location.pathname === '/check-analysis')}
        >
          Check Analysis
        </Link>
        <Link
          to="/paystub-analysis"
          style={linkStyle(location.pathname === '/paystub-analysis')}
        >
          Paystub Analysis
        </Link>
        <Link
          to="/money-order-analysis"
          style={linkStyle(location.pathname === '/money-order-analysis')}
        >
          Money Order Analysis
        </Link>
      </nav>
    </header>
  );
};

export default Header;

