import React from 'react';
import { colors } from '../styles/colors';

const Footer = () => {
  const footerStyle = {
    backgroundColor: colors.card,
    color: colors.foreground,
    padding: '1.5rem 2rem',
    textAlign: 'center',
    marginTop: 'auto',
    borderTop: `1px solid ${colors.border}`,
  };
  
  const textStyle = {
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
    <footer style={footerStyle}>
      <div style={textStyle}>
        <span>Where Innovation Meets Security</span>
        <span style={separatorStyle}>|</span>
        <span>Zero Tolerance for Fraud</span>
        <span style={separatorStyle}>|</span>
        <span>© 2025 Xforia DAD</span>
      </div>
    </footer>
  );
};

export default Footer;
