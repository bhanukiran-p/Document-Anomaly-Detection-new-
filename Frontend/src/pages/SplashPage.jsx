import React from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { FaShieldAlt, FaFileAlt, FaBolt, FaSearch, FaDollarSign, FaLock, FaChartLine, FaClock, FaBrain, FaCheckCircle, FaPlug, FaBullseye, FaArrowLeft } from 'react-icons/fa';
import { useAuth } from '../context/AuthContext';

const SplashPage = () => {
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
    backgroundColor: '#F5F5F5',
  };
  
  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem 3rem',
    backgroundColor: '#FAFAFA',
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
  
  const backButtonStyle = {
    backgroundColor: 'transparent',
    color: colors.primary.navy,
    padding: '0.625rem 1rem',
    borderRadius: '0.375rem',
    border: `2px solid ${colors.primary.navy}`,
    cursor: 'pointer',
    fontSize: '1rem',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'all 0.2s',
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
  
  const headerButtonsStyle = {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
  };
  
  const heroSectionStyle = {
    textAlign: 'center',
    padding: '2rem 2rem 1rem 2rem',
    backgroundColor: '#F5F5F5',
  };
  
  const dadLogoStyle = {
    height: '220px',
    width: 'auto',
    marginBottom: '1.5rem',
    padding: '1rem',
    backgroundColor: 'transparent',
    borderRadius: '8px',
  };
  
  const heroTaglineStyle = {
    fontSize: '1.5rem',
    fontWeight: '600',
    color: colors.primary.navy,
    marginBottom: '0',
  };
  
  const mainFeaturesStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '2rem 2rem',
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '2rem',
  };
  
  const featureCardStyle = {
    backgroundColor: colors.neutral.white,
    textAlign: 'center',
    padding: '1.5rem',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    cursor: 'pointer',
  };
  
  const featureIconStyle = {
    fontSize: '3rem',
    color: colors.primary.blue,
    marginBottom: '1rem',
  };
  
  const featureTitleStyle = {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: colors.primary.navy,
    marginBottom: '0.5rem',
  };
  
  const firstLetterStyle = {
    fontSize: '2rem',
    color: colors.accent.red,
    fontWeight: '800',
  };
  
  const featureSubtitleStyle = {
    fontSize: '1rem',
    fontWeight: '600',
    color: colors.accent.red,
    marginBottom: '1rem',
  };
  
  const featureDescStyle = {
    fontSize: '1rem',
    color: colors.neutral.gray600,
    lineHeight: '1.6',
  };
  
  const sectionStyle = {
    backgroundColor: '#F5F5F5',
    padding: '2.5rem 2rem',
  };
  
  const sectionTitleStyle = {
    fontSize: '2.5rem',
    fontWeight: '700',
    color: colors.primary.navy,
    textAlign: 'center',
    marginBottom: '2rem',
  };
  
  const smallFeaturesGridStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1.5rem',
  };
  
  const smallFeatureCardStyle = {
    backgroundColor: colors.neutral.white,
    padding: '1.5rem',
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    cursor: 'pointer',
  };
  
  const smallFeatureIconStyle = {
    fontSize: '2rem',
    color: colors.primary.blue,
    marginBottom: '0.75rem',
  };
  
  const smallFeatureTitleStyle = {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: colors.primary.navy,
    marginBottom: '0.75rem',
  };
  
  const smallFeatureDescStyle = {
    fontSize: '0.95rem',
    color: colors.neutral.gray600,
    lineHeight: '1.5',
  };
  
  const impactsSectionStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '2.5rem 2rem',
  };
  
  const impactCardStyle = {
    display: 'flex',
    gap: '1.5rem',
    padding: '1.25rem',
    backgroundColor: colors.neutral.white,
    borderRadius: '12px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    marginBottom: '1rem',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    cursor: 'pointer',
  };
  
  const impactIconStyle = {
    fontSize: '2.5rem',
    flexShrink: 0,
  };
  
  const redIconStyle = {
    ...impactIconStyle,
    color: colors.accent.red,
  };
  
  const blueIconStyle = {
    ...impactIconStyle,
    color: colors.primary.blue,
  };
  
  const greenIconStyle = {
    ...impactIconStyle,
    color: '#48BB78',
  };
  
  const purpleIconStyle = {
    ...impactIconStyle,
    color: '#9F7AEA',
  };
  
  const impactTitleStyle = {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: colors.primary.navy,
    marginBottom: '0.5rem',
  };
  
  const impactDescStyle = {
    fontSize: '0.95rem',
    color: colors.neutral.gray600,
    lineHeight: '1.5',
  };
  
  const flowImageStyle = {
    width: '100%',
    maxWidth: '600px',
    height: 'auto',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  };
  
  const impactsLayoutStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '3rem',
    alignItems: 'center',
  };
  
  const ctaSectionStyle = {
    textAlign: 'center',
    padding: '2.5rem 2rem',
    backgroundColor: '#F5F5F5',
  };
  
  const launchButtonStyle = {
    backgroundColor: colors.accent.red,
    color: colors.neutral.white,
    padding: '1.25rem 4rem',
    borderRadius: '50px',
    fontSize: '1.5rem',
    fontWeight: '700',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 8px 20px rgba(220, 53, 69, 0.4)',
    transition: 'all 0.3s',
    marginBottom: '1.5rem',
  };
  
  const ctaTaglineStyle = {
    fontSize: '1.125rem',
    color: colors.primary.navy,
    fontStyle: 'italic',
  };
  
  const footerStyle = {
    backgroundColor: colors.primary.navy,
    color: colors.neutral.white,
    padding: '1.5rem 2rem',
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
        
        <div style={headerButtonsStyle}>
          <button 
            style={loginButtonStyle}
            onMouseEnter={(e) => e.target.style.backgroundColor = colors.primary.navy}
            onMouseLeave={(e) => e.target.style.backgroundColor = colors.primary.blue}
            onClick={() => navigate('/login')}
          >
            Login →
          </button>
        </div>
      </header>
      
      {/* Hero Section */}
      <section style={heroSectionStyle}>
        <img src="/DAD_red_black.png" alt="DAD Logo" style={dadLogoStyle} />
        <p style={heroTaglineStyle}>The Intelligence That Safeguards Your Next Move</p>
      </section>
      
      {/* Main Features */}
      <section style={{ padding: '1.5rem 2rem 2rem 2rem', backgroundColor: '#F5F5F5' }}>
        <div style={mainFeaturesStyle}>
          <div 
            style={featureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaFileAlt style={featureIconStyle} />
            <h2 style={featureTitleStyle}>
              <span style={firstLetterStyle}>D</span>OCUMENT
            </h2>
            <h3 style={featureSubtitleStyle}>Trusted document screening</h3>
            <p style={featureDescStyle}>
              Automatically perform KYC checks to screen every document and validate both its format and content to ensure compliance and authenticity.
            </p>
          </div>
          
          <div 
            style={featureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaBolt style={featureIconStyle} />
            <h2 style={featureTitleStyle}>
              <span style={firstLetterStyle}>A</span>NOMALY
            </h2>
            <h3 style={featureSubtitleStyle}>Behavior-aware risk detection</h3>
            <p style={featureDescStyle}>
              The Anomaly Engine detects suspicious patterns and applies behavioral analysis to identify Anti-Money Laundering (AML) risks that humans might miss.
            </p>
          </div>
          
          <div 
            style={featureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaSearch style={featureIconStyle} />
            <h2 style={featureTitleStyle}>
              <span style={firstLetterStyle}>D</span>ETECTION
            </h2>
            <h3 style={featureSubtitleStyle}>Real-time fraud scoring</h3>
            <p style={featureDescStyle}>
              Provides accurate, real-time monitoring with instant scoring so threats are flagged before they cause damage.
            </p>
          </div>
        </div>
      </section>
      
      {/* Features Grid */}
      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>FEATURES</h2>
        <div style={smallFeaturesGridStyle}>
          <div 
            style={smallFeatureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaBrain style={smallFeatureIconStyle} />
            <h3 style={smallFeatureTitleStyle}>Adaptive Risk Models</h3>
            <p style={smallFeatureDescStyle}>
              Adapts quickly to emerging fraud and behavior patterns.
            </p>
          </div>
          
          <div 
            style={smallFeatureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaCheckCircle style={smallFeatureIconStyle} />
            <h3 style={smallFeatureTitleStyle}>Explainable Decisions</h3>
            <p style={smallFeatureDescStyle}>
              Clear, visual reasons for every alert.
            </p>
          </div>
          
          <div 
            style={smallFeatureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaPlug style={smallFeatureIconStyle} />
            <h3 style={smallFeatureTitleStyle}>Seamless Integration</h3>
            <p style={smallFeatureDescStyle}>
              Effortless setup with plug-and-play APIs.
            </p>
          </div>
          
          <div 
            style={smallFeatureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaBullseye style={smallFeatureIconStyle} />
            <h3 style={smallFeatureTitleStyle}>Maximum Impact</h3>
            <p style={smallFeatureDescStyle}>
              Consistently high precision across check and online flows.
            </p>
          </div>
          
          <div 
            style={smallFeatureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaBolt style={smallFeatureIconStyle} />
            <h3 style={smallFeatureTitleStyle}>Real-Time</h3>
            <p style={smallFeatureDescStyle}>
              From raw image to decision in seconds.
            </p>
          </div>
          
          <div 
            style={smallFeatureCardStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-6px)';
              e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}
          >
            <FaLock style={smallFeatureIconStyle} />
            <h3 style={smallFeatureTitleStyle}>Secure Architecture</h3>
            <p style={smallFeatureDescStyle}>
              End-to-end protection with zero data leaks.
            </p>
          </div>
        </div>
      </section>
      
      {/* Business Impacts */}
      <section style={impactsSectionStyle}>
        <h2 style={sectionTitleStyle}>BUSINESS IMPACTS</h2>
        <div style={impactsLayoutStyle}>
          <div>
            <div 
              style={impactCardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateX(8px)';
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.12)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
              }}
            >
              <FaDollarSign style={redIconStyle} />
              <div>
                <h3 style={impactTitleStyle}>Sustain Financial Health</h3>
                <p style={impactDescStyle}>
                  Make smarter decisions faster to protect savings and prevent fraud early.
                </p>
              </div>
            </div>
            
            <div 
              style={impactCardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateX(8px)';
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.12)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
              }}
            >
              <FaShieldAlt style={blueIconStyle} />
              <div>
                <h3 style={impactTitleStyle}>Defend Against Smart Threats</h3>
                <p style={impactDescStyle}>
                  Intercept threats before they impact your bottom line or customer experience.
                </p>
              </div>
            </div>
            
            <div 
              style={impactCardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateX(8px)';
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.12)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
              }}
            >
              <FaChartLine style={greenIconStyle} />
              <div>
                <h3 style={impactTitleStyle}>Accelerate Trusted Approvals</h3>
                <p style={impactDescStyle}>
                  Maintain approvals and cash flow while minimizing false declines.
                </p>
              </div>
            </div>
            
            <div 
              style={impactCardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateX(8px)';
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.12)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
              }}
            >
              <FaClock style={purpleIconStyle} />
              <div>
                <h3 style={impactTitleStyle}>Stay Resilient</h3>
                <p style={impactDescStyle}>
                  Accelerate approvals and keep operations running without disruption.
                </p>
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <img src="/flow.png" alt="Integration Flow Diagram" style={flowImageStyle} />
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section style={ctaSectionStyle}>
        <button
          style={launchButtonStyle}
          onMouseEnter={(e) => {
            e.target.style.transform = 'scale(1.05)';
            e.target.style.boxShadow = '0 12px 28px rgba(220, 53, 69, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = '0 8px 20px rgba(220, 53, 69, 0.4)';
          }}
          onClick={() => navigate('/transaction-type')}
        >
          LAUNCH DAD
        </button>
        <p style={ctaTaglineStyle}>
          "Just like Dad protects the home, Xforia's DAD keeps fraud from going prone"
        </p>
      </section>
      
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

export default SplashPage;

