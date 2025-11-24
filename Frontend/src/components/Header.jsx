import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { colors } from '../styles/colors';
import { FaBars, FaTimes, FaSignOutAlt } from 'react-icons/fa';

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  // eslint-disable-next-line no-unused-vars
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setIsMenuOpen(false);
    navigate('/');
  };
  
  const headerStyle = {
    backgroundColor: colors.card,
    borderBottom: `1px solid ${colors.border}`,
    padding: '0.75rem 1.5rem 0.75rem 0.5rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    backdropFilter: 'blur(10px)',
  };
  
  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    textDecoration: 'none',
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
    color: colors.primaryColor || colors.accent?.red || '#E53935',
    whiteSpace: 'nowrap',
  };
  
  const hamburgerButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    fontSize: '1.5rem',
    color: colors.foreground,
    cursor: 'pointer',
    padding: '0.5rem',
    display: 'flex',
    alignItems: 'center',
    transition: 'color 0.2s',
  };
  
  const navOverlayStyle = {
    position: 'fixed',
    top: 0,
    right: isMenuOpen ? 0 : '-100%',
    width: '300px',
    height: '100vh',
    backgroundColor: colors.card,
    boxShadow: `-4px 0 8px ${colors.background}80`,
    transition: 'right 0.3s ease',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    padding: '2rem',
    borderLeft: `1px solid ${colors.border}`,
  };
  
  const navBackdropStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    backgroundColor: 'rgba(3, 5, 7, 0.8)',
    zIndex: 999,
    display: isMenuOpen ? 'block' : 'none',
  };
  
  const closeButtonStyle = {
    alignSelf: 'flex-end',
    backgroundColor: 'transparent',
    border: 'none',
    fontSize: '1.5rem',
    color: colors.foreground,
    cursor: 'pointer',
    marginBottom: '2rem',
    transition: 'color 0.2s',
  };
  
  const navStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  };
  
  const linkStyle = (isActive) => ({
    padding: '0.75rem 1rem',
    borderRadius: '0.5rem',
    fontWeight: '500',
    backgroundColor: isActive ? colors.muted : 'transparent',
    color: isActive ? (colors.primaryColor || colors.accent?.red || '#E53935') : colors.foreground,
    transition: 'all 0.2s',
    textDecoration: 'none',
    display: 'block',
  });

  // eslint-disable-next-line no-unused-vars
  const logoutButtonStyle = {
    width: '50px',
    height: '50px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primaryColor || colors.accent?.red || '#E53935',
    color: colors.primaryForeground,
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.2s',
    marginTop: '2rem',
    borderTop: `1px solid ${colors.border}`,
    paddingTop: '2rem',
    alignSelf: 'center',
    fontSize: '1.25rem',
  };
  
  return (
    <>
      <header style={headerStyle}>
        <Link 
          to="/" 
          style={logoStyle}
          onMouseEnter={(e) => {
            const img = e.currentTarget.querySelector('img');
            if (img) {
              img.style.filter = 'drop-shadow(0 0 12px rgba(255, 255, 255, 0.5)) drop-shadow(0 0 20px rgba(229, 57, 53, 0.6))';
              img.style.transform = 'scale(1.05)';
            }
          }}
          onMouseLeave={(e) => {
            const img = e.currentTarget.querySelector('img');
            if (img) {
              img.style.filter = 'drop-shadow(0 0 8px rgba(255, 255, 255, 0.3)) drop-shadow(0 0 15px rgba(229, 57, 53, 0.4))';
              img.style.transform = 'scale(1)';
            }
          }}
        >
          <img src="/New_FD.png" alt="XFORIA DAD Logo" style={logoImageStyle} />
          <div style={taglineStyle}>
            Your Guardian against Fraud
          </div>
        </Link>
        
        <button 
          style={hamburgerButtonStyle}
          onClick={() => setIsMenuOpen(true)}
            onMouseEnter={(e) => e.target.style.color = colors.primaryColor || colors.accent?.red || '#E53935'}
          onMouseLeave={(e) => e.target.style.color = colors.foreground}
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
            onMouseEnter={(e) => e.target.style.color = colors.primaryColor || colors.accent?.red || '#E53935'}
          onMouseLeave={(e) => e.target.style.color = colors.foreground}
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

        <button
          style={logoutButtonStyle}
          onClick={handleLogout}
          onMouseEnter={(e) => {
            e.target.style.transform = 'scale(1.1)';
            e.target.style.boxShadow = `0 0 20px ${colors.primaryColor || colors.accent?.red || '#E53935'}60`;
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = 'none';
          }}
          title="Logout"
        >
          <FaSignOutAlt />
        </button>
      </div>
    </>
  );
};

export default Header;
