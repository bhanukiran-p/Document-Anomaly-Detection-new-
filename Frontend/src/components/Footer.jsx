import React from 'react';
import { colors } from '../styles/colors';

const Footer = () => {
  const footerStyle = {
    backgroundColor: colors.primary.navy,
    color: colors.neutral.white,
    padding: '1.5rem 2rem',
    textAlign: 'center',
    marginTop: 'auto',
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
    color: colors.neutral.gray400,
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

