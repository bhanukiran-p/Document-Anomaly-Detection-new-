import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { 
  FaBuilding, 
  FaHeartbeat, 
  FaGraduationCap, 
  FaClock, 
  FaFileAlt, 
  FaChartLine,
  FaBrain,
  FaSearch,
  FaCubes,
  FaUpload,
  FaCog,
  FaCheckSquare,
  FaChevronDown,
  FaChevronUp,
  FaLinkedin,
  FaTwitter,
  FaStar
} from 'react-icons/fa';

const LandingPage = () => {
  const navigate = useNavigate();
  const [openFaq, setOpenFaq] = useState(null);
  const sectionRefs = useRef([]);
  
  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  useEffect(() => {
    // Scroll-triggered animations
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    sectionRefs.current.forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, []);

  const addToRefs = (el) => {
    if (el && !sectionRefs.current.includes(el)) {
      sectionRefs.current.push(el);
    }
  };

  const containerStyle = {
    backgroundColor: colors.background,
    color: colors.foreground,
    minHeight: '100vh',
  };

  // Header Styles
  const headerStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem 3rem',
    backgroundColor: 'transparent',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    backdropFilter: 'blur(10px)',
    borderBottom: `1px solid ${colors.border}`,
  };

  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    fontSize: '1.25rem',
    fontWeight: 'bold',
    color: primary,
  };

  const navStyle = {
    display: 'flex',
    gap: '2rem',
    alignItems: 'center',
  };

  const navLinkStyle = {
    color: colors.foreground,
    fontSize: '0.9375rem',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'color 0.2s',
  };

  const getStartedButtonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '0.625rem 1.5rem',
    borderRadius: '0.5rem',
    fontWeight: '600',
    fontSize: '0.9375rem',
    cursor: 'pointer',
    transition: 'all 0.3s',
    boxShadow: `0 0 20px ${primary}40`,
  };

  // Hero Section
  const heroStyle = {
    padding: '6rem 3rem',
    textAlign: 'center',
    background: colors.gradients.dark,
  };

  const heroTitleStyle = {
    fontSize: '3rem',
    fontWeight: 'bold',
    marginBottom: '1.5rem',
    lineHeight: '1.1',
    background: `linear-gradient(135deg, ${colors.foreground}, ${colors.mutedForeground})`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  };

  const heroSubtitleStyle = {
    fontSize: '1.25rem',
    color: colors.mutedForeground,
    marginBottom: '2.5rem',
    maxWidth: '800px',
    margin: '0 auto 2.5rem',
  };

  const heroButtonsStyle = {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
    flexWrap: 'wrap',
  };

  const primaryButtonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '1rem 2rem',
    borderRadius: '0.75rem',
    fontWeight: '600',
    fontSize: '1rem',
    cursor: 'pointer',
    transition: 'all 0.3s',
    boxShadow: `0 0 30px ${primary}50`,
  };

  const secondaryButtonStyle = {
    backgroundColor: 'transparent',
    color: colors.foreground,
    padding: '1rem 2rem',
    borderRadius: '0.75rem',
    fontWeight: '600',
    fontSize: '1rem',
    cursor: 'pointer',
    border: `2px solid ${colors.border}`,
    transition: 'all 0.3s',
  };

  // Section Styles
  const sectionStyle = {
    padding: '5rem 3rem',
  };

  const sectionTitleStyle = {
    fontSize: '2.25rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
    textAlign: 'center',
  };

  const sectionSubtitleStyle = {
    fontSize: '1.125rem',
    color: colors.mutedForeground,
    textAlign: 'center',
    marginBottom: '3rem',
    maxWidth: '700px',
    margin: '0 auto 3rem',
  };

  // Card Styles
  const cardsGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '2rem',
    maxWidth: '1200px',
    margin: '0 auto',
  };

  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem',
    border: `1px solid ${colors.border}`,
    transition: 'all 0.3s',
    cursor: 'pointer',
  };

  const cardIconStyle = {
    fontSize: '2.5rem',
    color: primary,
    marginBottom: '1.5rem',
  };

  const cardTitleStyle = {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
  };

  const cardDescStyle = {
    color: colors.mutedForeground,
    lineHeight: '1.6',
  };

  // Pricing Card Styles
  const pricingCardStyle = {
    ...cardStyle,
    position: 'relative',
  };

  const popularBadgeStyle = {
    position: 'absolute',
    top: '-12px',
    left: '50%',
    transform: 'translateX(-50%)',
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '0.25rem 1rem',
    borderRadius: '1rem',
    fontSize: '0.75rem',
    fontWeight: '600',
  };

  const priceStyle = {
    fontSize: '2.5rem',
    fontWeight: 'bold',
    margin: '1rem 0',
  };

  const featureListStyle = {
    listStyle: 'none',
    margin: '1.5rem 0',
  };

  const featureItemStyle = {
    padding: '0.75rem 0',
    borderBottom: `1px solid ${colors.border}`,
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  };

  // FAQ Styles
  const faqItemStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    marginBottom: '1rem',
    border: `1px solid ${colors.border}`,
    overflow: 'hidden',
  };

  const faqQuestionStyle = {
    padding: '1.5rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    cursor: 'pointer',
    fontWeight: '600',
  };

  const faqAnswerStyle = {
    padding: '0 1.5rem 1.5rem',
    color: colors.mutedForeground,
    lineHeight: '1.6',
  };

  // Footer Styles
  const footerStyle = {
    backgroundColor: colors.card,
    padding: '3rem',
    borderTop: `1px solid ${colors.border}`,
  };

  const footerGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '2rem',
    maxWidth: '1200px',
    margin: '0 auto',
  };

  const footerColumnStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  };

  const footerTitleStyle = {
    fontWeight: 'bold',
    marginBottom: '0.5rem',
  };

  const footerLinkStyle = {
    color: colors.mutedForeground,
    fontSize: '0.875rem',
    cursor: 'pointer',
  };

  const footerBottomStyle = {
    marginTop: '3rem',
    paddingTop: '2rem',
    borderTop: `1px solid ${colors.border}`,
    textAlign: 'center',
    color: colors.mutedForeground,
    fontSize: '0.875rem',
  };

  const industries = [
    {
      icon: <FaBuilding />,
      title: 'Financial Institutions',
      description: 'Protect against fraud in loans, mortgages, and financial transactions with real-time anomaly detection.',
    },
    {
      icon: <FaHeartbeat />,
      title: 'Healthcare Providers',
      description: 'Secure patient data and prevent insurance fraud with advanced document verification.',
    },
    {
      icon: <FaGraduationCap />,
      title: 'Government & Education',
      description: 'Safeguard public funds and ensure document authenticity in government and educational institutions.',
    },
  ];

  const challenges = [
    {
      icon: <FaClock />,
      title: 'Your Team Can\'t Keep Up',
      description: 'The overwhelming volume of documents makes manual review time-consuming and error-prone.',
    },
    {
      icon: <FaFileAlt />,
      title: 'Traditional OCR Only Reads—It Doesn\'t Think',
      description: 'OCR limitations prevent detection of sophisticated fraud patterns and anomalies.',
    },
    {
      icon: <FaChartLine />,
      title: 'Fraud Evolves Faster Than Your Rules',
      description: 'Rule-based systems struggle to keep up with evolving fraud tactics and patterns.',
    },
  ];

  const advantages = [
    {
      icon: <FaBrain />,
      title: 'Intelligent, Not Just Automated',
      description: 'DAD\'s AI understands context and reasons through complex document patterns.',
    },
    {
      icon: <FaSearch />,
      title: 'Explainable Results You Can Trust',
      description: 'Clear reasoning for fraud flags and comprehensive audit trails for compliance.',
    },
    {
      icon: <FaCubes />,
      title: 'Enterprise-Ready, Modular Architecture',
      description: 'Flexible deployment options (on-premise, cloud) with unlimited scalability.',
    },
  ];

  const steps = [
    {
      icon: <FaUpload />,
      title: 'Upload Your Document',
      description: 'Upload various document types including PDFs, images, and scanned documents.',
      number: '1',
    },
    {
      icon: <FaCog />,
      title: 'AI-Powered Analysis',
      description: 'DAD\'s AI processes and analyzes your document in real-time for anomalies.',
      number: '2',
    },
    {
      icon: <FaCheckSquare />,
      title: 'Get Actionable Results',
      description: 'Receive fraud scores, detailed explanations, and actionable insights instantly.',
      number: '3',
    },
  ];

  const pricingPlans = [
    {
      name: 'Starter',
      price: '$XX',
      period: '/month',
      badge: null,
      features: [
        'Up to XX documents/month',
        'Core fraud detection',
        'Storage for XX days',
        'Email support',
        'XX-day data retention',
      ],
      buttonText: 'Start Free Trial',
      buttonStyle: secondaryButtonStyle,
    },
    {
      name: 'Professional',
      price: '$XX',
      period: '/month',
      badge: 'Most Popular',
      features: [
        'Up to XX documents/month',
        'Advanced AI models',
        'Custom fraud rules',
        'Dedicated account manager',
        'API access',
        'XX-day data retention',
        'Priority support',
      ],
      buttonText: 'Get Started',
      buttonStyle: primaryButtonStyle,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      badge: null,
      features: [
        'Unlimited documents',
        'Custom model training',
        'Multi-document processing',
        'On-premise deployment',
        'Dedicated account manager',
        'XX-day data retention',
        'Custom integrations',
      ],
      buttonText: 'Talk to Sales',
      buttonStyle: secondaryButtonStyle,
    },
  ];

  const testimonials = [
    {
      name: 'Rahul',
      role: 'Director of Fraud Prevention',
      company: 'Mid-Size Bank',
      text: 'DAD detected XX financial fraud events and improved our efficiency by XX%.',
      rating: 5,
    },
    {
      name: 'Sarah',
      role: 'Chief Risk Officer',
      company: 'Fintech Startup',
      text: 'DAD\'s seamless integration and real-time fraud detection transformed our operations.',
      rating: 5,
    },
    {
      name: 'Maria',
      role: 'Senior Compliance',
      company: 'Healthcare System',
      text: 'DAD processed XX documents in XX hours, saving us countless hours of manual review.',
      rating: 5,
    },
  ];

  const faqs = [
    {
      question: 'How accurate is DAD compared to manual review?',
      answer: 'DAD achieves XX% accuracy in fraud detection, significantly outperforming manual review processes while processing documents in seconds instead of hours.',
    },
    {
      question: 'What types of documents can DAD analyze?',
      answer: 'DAD can analyze checks, paystubs, money orders, bank statements, invoices, contracts, and many other document types across various industries.',
    },
    {
      question: 'How long does implementation take?',
      answer: 'DAD can be integrated in as little as XX days, with full deployment and training completed within XX weeks.',
    },
    {
      question: 'Do you support on-premise deployment?',
      answer: 'Yes, DAD offers flexible deployment options including on-premise, cloud, and hybrid solutions to meet your security requirements.',
    },
    {
      question: 'How does pricing scale with document volume?',
      answer: 'Our pricing is designed to scale with your needs. Contact us for custom pricing based on your document volume and requirements.',
    },
    {
      question: 'What happens to my document data?',
      answer: 'DAD follows strict data privacy and security protocols. Your documents are processed securely and can be retained according to your plan settings.',
    },
    {
      question: 'Can DAD integrate with our existing systems?',
      answer: 'Yes, DAD offers comprehensive API access and integrations with popular document management systems, CRMs, and workflow tools.',
    },
    {
      question: 'What kind of support do you provide?',
      answer: 'We offer email support for Starter plans, priority support for Professional plans, and dedicated account managers for Enterprise customers.',
    },
  ];

  return (
    <div style={containerStyle}>
      {/* Header */}
      <header style={headerStyle}>
        <div style={logoStyle}>
          <span style={{ color: colors.primary }}>DAD</span>
        </div>
        <nav style={navStyle}>
          <span style={navLinkStyle}>Product</span>
          <span style={navLinkStyle}>Solutions</span>
          <span style={navLinkStyle}>Pricing</span>
          <span style={navLinkStyle}>Resources</span>
          <button
            style={getStartedButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.transform = 'scale(1.05)';
              e.target.style.boxShadow = `0 0 40px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'scale(1)';
              e.target.style.boxShadow = `0 0 20px ${colors.primary}40`;
            }}
            onClick={() => navigate('/register')}
          >
            Get Started
          </button>
        </nav>
      </header>

      {/* Hero Section */}
      <section style={heroStyle} ref={addToRefs} className="scroll-reveal">
        <h1 style={heroTitleStyle}>
          Stop Document Fraud Before It Costs You Millions
        </h1>
        <p style={heroSubtitleStyle}>
          AI-powered fraud detection that catches anomalies in seconds—not weeks.
        </p>
        <div style={heroButtonsStyle}>
          <button
            style={primaryButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.transform = 'scale(1.05)';
              e.target.style.boxShadow = `0 0 40px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'scale(1)';
              e.target.style.boxShadow = `0 0 30px ${colors.primary}50`;
            }}
            onClick={() => navigate('/register')}
          >
            See DAD in Action
          </button>
          <button
            style={secondaryButtonStyle}
            onMouseEnter={(e) => {
              e.target.style.borderColor = primary;
              e.target.style.color = colors.primary;
            }}
            onMouseLeave={(e) => {
              e.target.style.borderColor = colors.border;
              e.target.style.color = colors.foreground;
            }}
            onClick={() => navigate('/register')}
          >
            Talk to Expert
          </button>
        </div>
        <p style={{ marginTop: '2rem', color: colors.mutedForeground, fontSize: '0.875rem' }}>
          Trusted by organizations processing XX million documents
        </p>
      </section>

      {/* Built for Organizations */}
      <section style={sectionStyle} ref={addToRefs} className="scroll-reveal">
        <h2 style={sectionTitleStyle}>
          Built for Organizations Where Document Integrity is Non-Negotiable
        </h2>
        <div style={cardsGridStyle}>
          {industries.map((industry, idx) => (
            <div
              key={idx}
              style={cardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = primary;
                e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={cardIconStyle}>{industry.icon}</div>
              <h3 style={cardTitleStyle}>{industry.title}</h3>
              <p style={cardDescStyle}>{industry.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Hidden Cost Section */}
      <section style={{ ...sectionStyle, backgroundColor: colors.secondary }} ref={addToRefs} className="scroll-reveal">
        <h2 style={sectionTitleStyle}>The Hidden Cost of Manual Document Review</h2>
        <div style={cardsGridStyle}>
          {challenges.map((challenge, idx) => (
            <div
              key={idx}
              style={cardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
              }}
            >
              <div style={cardIconStyle}>{challenge.icon}</div>
              <h3 style={cardTitleStyle}>{challenge.title}</h3>
              <p style={cardDescStyle}>{challenge.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Why DAD Outperforms */}
      <section style={sectionStyle} ref={addToRefs} className="scroll-reveal">
        <h2 style={sectionTitleStyle}>Why DAD Outperforms Traditional Fraud Detection</h2>
        <div style={cardsGridStyle}>
          {advantages.map((advantage, idx) => (
            <div
              key={idx}
              style={cardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = primary;
                e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={cardIconStyle}>{advantage.icon}</div>
              <h3 style={cardTitleStyle}>{advantage.title}</h3>
              <p style={cardDescStyle}>{advantage.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Three Steps */}
      <section style={{ ...sectionStyle, backgroundColor: colors.secondary }} ref={addToRefs} className="scroll-reveal">
        <h2 style={sectionTitleStyle}>From Upload to Insight in Three Simple Steps</h2>
        <div style={cardsGridStyle}>
          {steps.map((step, idx) => (
            <div
              key={idx}
              style={{
                ...cardStyle,
                position: 'relative',
                textAlign: 'center',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
              }}
            >
              <div style={{
                position: 'absolute',
                top: '-20px',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: primary,
                color: colors.primaryForeground,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: '1.25rem',
              }}>
                {step.number}
              </div>
              <div style={{ ...cardIconStyle, marginTop: '1rem' }}>{step.icon}</div>
              <h3 style={cardTitleStyle}>{step.title}</h3>
              <p style={cardDescStyle}>{step.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section style={sectionStyle} ref={addToRefs} className="scroll-reveal">
        <h2 style={sectionTitleStyle}>Transparent Pricing That Scales With You</h2>
        <div style={cardsGridStyle}>
          {pricingPlans.map((plan, idx) => (
            <div
              key={idx}
              style={pricingCardStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = primary;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
              }}
            >
              {plan.badge && <div style={popularBadgeStyle}>{plan.badge}</div>}
              <h3 style={cardTitleStyle}>{plan.name}</h3>
              <div style={priceStyle}>
                {plan.price}
                <span style={{ fontSize: '1rem', color: colors.mutedForeground }}>
                  {plan.period}
                </span>
              </div>
              <ul style={featureListStyle}>
                {plan.features.map((feature, fIdx) => (
                  <li key={fIdx} style={featureItemStyle}>
                    <FaCheckSquare style={{ color: primary, flexShrink: 0 }} />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <button
                style={{
                  ...plan.buttonStyle,
                  width: '100%',
                  marginTop: '1.5rem',
                }}
                onClick={() => navigate('/register')}
              >
                {plan.buttonText}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section style={{ ...sectionStyle, backgroundColor: colors.secondary }} ref={addToRefs} className="scroll-reveal">
        <h2 style={sectionTitleStyle}>Real Results from Organizations Like Yours</h2>
        <div style={cardsGridStyle}>
          {testimonials.map((testimonial, idx) => (
            <div key={idx} style={cardStyle}>
              <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1rem' }}>
                {[...Array(testimonial.rating)].map((_, i) => (
                  <FaStar key={i} style={{ color: primary }} />
                ))}
              </div>
              <p style={{ ...cardDescStyle, marginBottom: '1.5rem', fontStyle: 'italic' }}>
                "{testimonial.text}"
              </p>
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                  {testimonial.name}
                </div>
                <div style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
                  {testimonial.role}, {testimonial.company}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Demo Section */}
      <section style={sectionStyle} ref={addToRefs} className="scroll-reveal">
        <div style={{
          ...cardStyle,
          textAlign: 'center',
          maxWidth: '800px',
          margin: '0 auto',
          padding: '3rem',
        }}>
          <h2 style={{ ...sectionTitleStyle, marginBottom: '1.5rem' }}>
            See DAD Detect Fraud in Real-Time
          </h2>
          <p style={{ ...cardDescStyle, marginBottom: '2rem', fontSize: '1.125rem' }}>
            Upload your own anonymized documents and watch DAD work. No credit card required.
          </p>
          <button
            style={{
              ...primaryButtonStyle,
              marginBottom: '1rem',
            }}
            onClick={() => navigate('/register')}
          >
            Book Your Demo
          </button>
          <p style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
            Or try DAD free for 14 Days
          </p>
        </div>
      </section>

      {/* FAQ */}
      <section style={{ ...sectionStyle, backgroundColor: colors.secondary }} ref={addToRefs} className="scroll-reveal">
        <h2 style={sectionTitleStyle}>Common Questions About DAD</h2>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          {faqs.map((faq, idx) => (
            <div key={idx} style={faqItemStyle}>
              <div
                style={faqQuestionStyle}
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
              >
                <span>{faq.question}</span>
                {openFaq === idx ? (
                  <FaChevronUp style={{ color: primary }} />
                ) : (
                  <FaChevronDown style={{ color: colors.mutedForeground }} />
                )}
              </div>
              {openFaq === idx && (
                <div style={faqAnswerStyle}>{faq.answer}</div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={footerStyle}>
        <div style={footerGridStyle}>
          <div style={footerColumnStyle}>
            <div style={footerTitleStyle}>© 2025 DAD. All rights reserved.</div>
            <div style={{ color: colors.mutedForeground, fontSize: '0.875rem' }}>
              Customer-Centric Document Fraud Detection
            </div>
          </div>
          <div style={footerColumnStyle}>
            <div style={footerTitleStyle}>Product</div>
            <span style={footerLinkStyle}>Solutions</span>
            <span style={footerLinkStyle}>How it works</span>
            <span style={footerLinkStyle}>Integrations</span>
            <span style={footerLinkStyle}>API Documentation</span>
            <span style={footerLinkStyle}>Security & Compliance</span>
          </div>
          <div style={footerColumnStyle}>
            <div style={footerTitleStyle}>Company</div>
            <span style={footerLinkStyle}>About Us</span>
            <span style={footerLinkStyle}>Contact</span>
            <span style={footerLinkStyle}>Careers</span>
            <span style={footerLinkStyle}>Press Kit</span>
          </div>
          <div style={footerColumnStyle}>
            <div style={footerTitleStyle}>Resources</div>
            <span style={footerLinkStyle}>Blog</span>
            <span style={footerLinkStyle}>Case Studies</span>
            <span style={footerLinkStyle}>Whitepapers</span>
            <span style={footerLinkStyle}>Support Center</span>
          </div>
        </div>
        <div style={footerBottomStyle}>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
            <FaLinkedin style={{ cursor: 'pointer', fontSize: '1.25rem' }} />
            <FaTwitter style={{ cursor: 'pointer', fontSize: '1.25rem' }} />
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
