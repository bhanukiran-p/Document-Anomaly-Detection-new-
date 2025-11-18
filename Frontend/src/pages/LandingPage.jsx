import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { FaBook, FaBriefcase, FaHeartbeat, FaLock } from 'react-icons/fa';

const LandingPage = () => {
  const navigate = useNavigate();
  
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
    padding: '1.5rem 3rem',
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
  
  const mainContentStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '3rem 3rem',
  };
  
  const mainLogoStyle = {
    height: '120px',
    width: 'auto',
    marginBottom: '2rem',
  };
  
  const titleStyle = {
    fontSize: '2.5rem',
    fontWeight: '700',
    color: colors.primary.navy,
    marginBottom: '0.75rem',
    textAlign: 'center',
  };
  
  const subtitleStyle = {
    fontSize: '1.125rem',
    color: colors.neutral.gray600,
    marginBottom: '2.5rem',
    textAlign: 'center',
  };
  
  const cardsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '2rem',
    maxWidth: '1400px',
    width: '100%',
  };
  
  const cardStyle = {
    backgroundColor: '#F8F9FA',
    borderRadius: '12px',
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    transition: 'transform 0.2s, box-shadow 0.2s',
  };
  
  const iconCircleStyle = {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    backgroundColor: colors.primary.blue,
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
    color: '#000',
    marginBottom: '1rem',
  };
  
  const cardDescStyle = {
    fontSize: '0.9375rem',
    color: colors.neutral.gray600,
    lineHeight: '1.6',
    marginBottom: '2rem',
    flex: 1,
  };
  
  const activeButtonStyle = {
    backgroundColor: colors.accent.red,
    color: colors.neutral.white,
    padding: '0.5rem 1.25rem',
    borderRadius: '9999px', // Pill shape
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
  
  const solutions = [
    {
      id: 'education',
      title: 'Education',
      icon: <FaBook />,
      description: 'Ensure academic integrity and verify educational documents and assessments',
      active: false,
    },
    {
      id: 'finance',
      title: 'Finance',
      icon: <FaBriefcase />,
      description: 'Detect fraud in financial documents, checks, and transactions with real-time analysis',
      active: true,
    },
    {
      id: 'healthcare',
      title: 'Healthcare',
      icon: <FaHeartbeat />,
      description: 'Verify medical records and ensure compliance with healthcare regulations',
      active: false,
    },
    {
      id: 'federal',
      title: 'Federal Services',
      icon: <FaLock />,
      description: 'Secure government document verification and identity authentication for federal agencies',
      active: false,
    },
  ];
  
  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <div style={logoContainerStyle}>
          <img src="/logo.png" alt="XFORIA DAD Logo" style={logoImageStyle} />
          <div style={taglineStyle}>Your Guardian against Fraud</div>
        </div>
      </header>
      
      <main style={mainContentStyle}>
        <img src="/logo.png" alt="XFORIA DAD" style={mainLogoStyle} />
        <h1 style={titleStyle}>Choose Your DAD Solution</h1>
        <p style={subtitleStyle}>Powered by Advanced AI Detection Technology</p>
        
        <div style={cardsContainerStyle}>
          {solutions.map((solution) => (
            <div
              key={solution.id}
              style={cardStyle}
              onMouseEnter={(e) => {
                if (solution.active) {
                  e.currentTarget.style.transform = 'translateY(-8px)';
                  e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.15)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={iconCircleStyle}>
                {solution.icon}
              </div>
              <h2 style={cardTitleStyle}>{solution.title}</h2>
              <p style={cardDescStyle}>{solution.description}</p>
              
              {solution.active ? (
                <button
                  style={activeButtonStyle}
                  onMouseEnter={(e) => e.target.style.backgroundColor = colors.accent.redDark}
                  onMouseLeave={(e) => e.target.style.backgroundColor = colors.accent.red}
                  onClick={() => navigate('/splash')}
                >
                  ENTER FINANCE
                </button>
              ) : (
                <button style={disabledButtonStyle}>
                  COMING SOON
                </button>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default LandingPage;

