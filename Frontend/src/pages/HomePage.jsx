import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';

const HomePage = () => {
  const navigate = useNavigate();
  
  const containerStyle = {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '2rem',
  };
  
  const headerStyle = {
    background: `linear-gradient(135deg, ${colors.primary.navy} 0%, ${colors.primary.blue} 100%)`,
    padding: '3rem',
    borderRadius: '12px',
    color: colors.neutral.white,
    textAlign: 'center',
    marginBottom: '3rem',
  };
  
  const titleStyle = {
    fontSize: '2.5rem',
    fontWeight: '700',
    marginBottom: '1rem',
  };
  
  const subtitleStyle = {
    fontSize: '1.25rem',
    opacity: 0.9,
  };
  
  const cardsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '2rem',
    marginBottom: '3rem',
  };
  
  const cardStyle = {
    backgroundColor: colors.background.card,
    borderRadius: '12px',
    padding: '2rem',
    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    borderLeft: `5px solid ${colors.primary.navy}`,
    transition: 'transform 0.2s, box-shadow 0.2s',
    cursor: 'pointer',
  };
  
  const cardTitleStyle = {
    fontSize: '1.5rem',
    fontWeight: '600',
    color: colors.primary.navy,
    marginBottom: '1rem',
  };
  
  const cardDescStyle = {
    color: colors.neutral.gray600,
    lineHeight: '1.6',
    marginBottom: '1.5rem',
  };
  
  const buttonStyle = {
    backgroundColor: colors.accent.red,
    color: colors.neutral.white,
    padding: '0.75rem 2rem',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    fontWeight: '600',
    border: 'none',
    cursor: 'pointer',
    width: '100%',
    transition: 'background-color 0.2s',
  };
  
  const featureListStyle = {
    listStyle: 'none',
    padding: 0,
    margin: '1.5rem 0',
  };
  
  const featureItemStyle = {
    padding: '0.5rem 0',
    color: colors.neutral.gray700,
  };
  
  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h1 style={titleStyle}>Document Extraction System</h1>
        <p style={subtitleStyle}>Powered by Google Cloud Vision API</p>
        <p style={{ opacity: 0.8, marginTop: '0.5rem' }}>
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
          <h2 style={cardTitleStyle}>Check Extraction</h2>
          <p style={cardDescStyle}>
            Extract detailed information from bank checks with AI-powered OCR
          </p>
          
          <ul style={featureListStyle}>
            <li style={featureItemStyle}>• Payee Name & Amount Detection</li>
            <li style={featureItemStyle}>• Date & Check Number Extraction</li>
            <li style={featureItemStyle}>• Bank Information Identification</li>
            <li style={featureItemStyle}>• Account & Routing Numbers</li>
            <li style={featureItemStyle}>• MICR/IFSC Code Extraction</li>
            <li style={featureItemStyle}>• Signature Detection</li>
          </ul>
          
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
          <h2 style={cardTitleStyle}>Paystub Extraction</h2>
          <p style={cardDescStyle}>
            Extract comprehensive payroll information from paystubs and payslips
          </p>
          
          <ul style={featureListStyle}>
            <li style={featureItemStyle}>• Employee Information Extraction</li>
            <li style={featureItemStyle}>• Gross & Net Pay Calculation</li>
            <li style={featureItemStyle}>• Pay Period & Date Detection</li>
            <li style={featureItemStyle}>• Tax Withholding Details</li>
            <li style={featureItemStyle}>• Earnings & Deductions Breakdown</li>
            <li style={featureItemStyle}>• YTD Totals Tracking</li>
          </ul>
          
          <button 
            style={buttonStyle}
            onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
            onMouseLeave={(e) => e.target.style.backgroundColor = colors.accent.red}
            onClick={() => navigate('/paystub-analysis')}
          >
            Analyze Paystubs
          </button>
        </div>
      </div>
      
      <div style={{
        backgroundColor: colors.primary.lightBlue,
        padding: '2rem',
        borderRadius: '12px',
        marginBottom: '2rem',
      }}>
        <h3 style={{ color: colors.primary.navy, marginBottom: '1rem' }}>About XFORIA DAD</h3>
        <div style={{ color: colors.neutral.gray700, lineHeight: '1.6' }}>
          <p><strong>Supported Document Types:</strong></p>
          <ul style={{ marginLeft: '2rem', marginTop: '0.5rem' }}>
            <li>Checks: Axis Bank, Bank of America, ICICI, HDFC, Chase, Wells Fargo</li>
            <li>Paystubs: US and International formats</li>
          </ul>
          
          <p style={{ marginTop: '1rem' }}><strong>Features:</strong></p>
          <ul style={{ marginLeft: '2rem', marginTop: '0.5rem' }}>
            <li>Real-time OCR with Google Vision API</li>
            <li>AI-powered data extraction</li>
            <li>High accuracy confidence scoring</li>
            <li>Export results as JSON</li>
            <li>PDF and Image file support</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

