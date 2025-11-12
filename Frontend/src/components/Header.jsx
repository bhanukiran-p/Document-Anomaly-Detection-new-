import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { colors } from '../styles/colors';
import { FaBars, FaTimes } from 'react-icons/fa';

const Header = () => {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  
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
    textDecoration: 'none',
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
  
  const hamburgerButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    fontSize: '1.5rem',
    color: colors.primary.navy,
    cursor: 'pointer',
    padding: '0.5rem',
    display: 'flex',
    alignItems: 'center',
  };
  
  const navOverlayStyle = {
    position: 'fixed',
    top: 0,
    right: isMenuOpen ? 0 : '-100%',
    width: '300px',
    height: '100vh',
    backgroundColor: colors.neutral.white,
    boxShadow: '-4px 0 8px rgba(0,0,0,0.1)',
    transition: 'right 0.3s ease',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    padding: '2rem',
  };
  
  const navBackdropStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    backgroundColor: 'rgba(0,0,0,0.5)',
    zIndex: 999,
    display: isMenuOpen ? 'block' : 'none',
  };
  
  const closeButtonStyle = {
    alignSelf: 'flex-end',
    backgroundColor: 'transparent',
    border: 'none',
    fontSize: '1.5rem',
    color: colors.primary.navy,
    cursor: 'pointer',
    marginBottom: '2rem',
  };
  
  const navStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  };
  
  const linkStyle = (isActive) => ({
    padding: '0.75rem 1rem',
    borderRadius: '0.375rem',
    fontWeight: '500',
    backgroundColor: isActive ? colors.primary.lightBlue : 'transparent',
    color: isActive ? colors.primary.navy : colors.neutral.gray700,
    transition: 'all 0.2s',
    textDecoration: 'none',
    display: 'block',
  });
  
  return (
    <>
      <header style={headerStyle}>
        <Link to="/" style={logoStyle}>
          <img src="/logo.png" alt="XFORIA DAD Logo" style={logoImageStyle} />
          <div style={taglineStyle}>
            Your Guardian against Fraud
          </div>
        </Link>
        
        <button 
          style={hamburgerButtonStyle}
          onClick={() => setIsMenuOpen(true)}
        >
          <FaBars />
        </button>
      </header>
      
      {/* Backdrop */}
      <div 
        style={navBackdropStyle}
        onClick={() => setIsMenuOpen(false)}
      />
      
      {/* Sidebar Menu */}
      <div style={navOverlayStyle}>
        <button 
          style={closeButtonStyle}
          onClick={() => setIsMenuOpen(false)}
        >
          <FaTimes />
        </button>
        
        <nav style={navStyle}>
          <Link
            to="/"
            style={linkStyle(location.pathname === '/')}
            onClick={() => setIsMenuOpen(false)}
          >
            Home
          </Link>
          <Link
            to="/splash"
            style={linkStyle(location.pathname === '/splash')}
            onClick={() => setIsMenuOpen(false)}
          >
            About DAD
          </Link>
          <Link
            to="/transaction-type"
            style={linkStyle(location.pathname === '/transaction-type')}
            onClick={() => setIsMenuOpen(false)}
          >
            Transaction Types
          </Link>
          <Link
            to="/finance"
            style={linkStyle(location.pathname === '/finance')}
            onClick={() => setIsMenuOpen(false)}
          >
            Finance Detection
          </Link>
          <Link
            to="/check-analysis"
            style={linkStyle(location.pathname === '/check-analysis')}
            onClick={() => setIsMenuOpen(false)}
          >
            Check Analysis
          </Link>
          <Link
            to="/paystub-analysis"
            style={linkStyle(location.pathname === '/paystub-analysis')}
            onClick={() => setIsMenuOpen(false)}
          >
            Paystub Analysis
          </Link>
          <Link
            to="/money-order-analysis"
            style={linkStyle(location.pathname === '/money-order-analysis')}
            onClick={() => setIsMenuOpen(false)}
          >
            Money Order Analysis
          </Link>
        </nav>
      </div>
    </>
  );
};

export default Header;

