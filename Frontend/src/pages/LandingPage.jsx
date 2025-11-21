import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { colors } from '../styles/colors';
import { useScrollAnimation } from '../hooks/useScrollAnimation';
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
  FaShieldAlt,
  FaLock,
  FaAward,
  FaNetworkWired,
  FaLayerGroup,
  FaPuzzlePiece,
  FaAlertCircle,
  FaEye,
  FaTrendingUp,
  FaCheck,
} from 'react-icons/fa';

const LandingPage = () => {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);
  
  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

  // Smooth scroll function
  const smoothScrollTo = (elementId) => {
    const element = document.getElementById(elementId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setMobileMenuOpen(false);
    }
  };

  const containerStyle = {
    backgroundColor: colors.background,
    color: colors.foreground,
    minHeight: '100vh',
  };

  // Navigation Styles
  const navStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 50,
    backgroundColor: `${colors.background}95`,
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    borderBottom: `1px solid ${colors.border}`,
    padding: '1rem 1.5rem',
  };

  const navContainerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };
  
  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '1.25rem',
    fontWeight: 'bold',
    color: primary,
    cursor: 'pointer',
  };

  const navLinksStyle = {
    display: 'none',
    gap: '2rem',
    alignItems: 'center',
  };

  const navLinkStyle = {
    fontSize: '0.875rem',
    color: colors.mutedForeground,
    textDecoration: 'none',
    transition: 'color 0.2s',
    cursor: 'pointer',
    position: 'relative',
  };

  const navButtonStyle = {
    backgroundColor: primary,
    color: colors.primaryForeground,
    padding: '0.625rem 1.5rem',
    borderRadius: '0.5rem',
    fontWeight: '600',
    fontSize: '0.875rem',
    cursor: 'pointer',
    transition: 'all 0.3s',
    boxShadow: `0 0 20px ${primary}40`,
    border: 'none',
  };

  // Hero Section
  const heroSectionStyle = {
    position: 'relative',
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    paddingTop: '80px',
    background: `linear-gradient(180deg, ${colors.background} 0%, ${colors.navyDark}20 50%, ${colors.background} 100%)`,
  };

  const heroContentStyle = {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '0 1.5rem',
    textAlign: 'center',
    position: 'relative',
    zIndex: 10,
  };

  const heroTitleStyle = {
    fontSize: '3rem',
    fontWeight: 'bold',
    lineHeight: '1.1',
    marginBottom: '1.5rem',
    background: `linear-gradient(135deg, ${colors.foreground}, ${colors.mutedForeground})`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  };

  const heroGradientTextStyle = {
    background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  };

  const heroSubtitleStyle = {
    fontSize: '1.25rem',
    color: colors.mutedForeground,
    marginBottom: '2rem',
    maxWidth: '800px',
    margin: '0 auto 2rem',
  };

  const heroButtonsStyle = {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
    flexWrap: 'wrap',
    marginBottom: '2rem',
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
    border: 'none',
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
    padding: '6rem 1.5rem',
  };

  const sectionTitleStyle = {
    fontSize: '2.25rem',
    fontWeight: 'bold',
    marginBottom: '1rem',
    textAlign: 'center',
    color: colors.foreground,
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
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
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
    color: colors.foreground,
  };
  
  const cardDescStyle = {
    color: colors.mutedForeground,
    lineHeight: '1.6',
  };

  // Data
  const useCases = [
    {
      icon: <FaBuilding />,
      title: 'Financial Institutions',
      description: 'Stop check fraud, forged signatures, and altered amounts before funds clear. Process thousands of checks daily with consistent, explainable detection.',
    },
    {
      icon: <FaHeartbeat />,
      title: 'Healthcare Providers',
      description: 'Verify insurance documents, prescriptions, and medical records for tampering. Protect patient data and prevent claims fraud with automated screening.',
    },
    {
      icon: <FaGraduationCap />,
      title: 'Government & Education',
      description: 'Authenticate certificates, transcripts, ID documents, and official forms. Scale verification without adding headcount or slowing processing times.',
    },
  ];

  const painPoints = [
    {
      icon: <FaClock />,
      title: "Your Team Can't Keep Up",
      description: "Processing hundreds of documents manually means fraud slips through. Your experts spend hours on routine checks instead of investigating real threats. Backlogs grow, and so does your exposure.",
    },
    {
      icon: <FaFileAlt />,
      title: "Traditional OCR Only Reads—It Doesn't Think",
      description: "Basic text extraction can't spot altered amounts, forged signatures, or manipulated images. By the time you notice patterns, thousands of dollars are already gone.",
    },
    {
      icon: <FaChartLine />,
      title: 'Fraud Evolves Faster Than Your Rules',
      description: "Static rule-based systems fail against sophisticated forgeries. Fraudsters adapt to your defenses while you're stuck waiting on vendor updates or building new rules from scratch.",
    },
  ];

  const advantages = [
    {
      icon: <FaBrain />,
      title: 'Intelligent, Not Just Automated',
      description: "DAD doesn't just scan, it understands context. Our AI combines ensemble machine learning and agentic reasoning to detect anomalies that rule-based systems miss entirely.",
    },
    {
      icon: <FaSearch />,
      title: 'Explainable Results You Can Trust',
      description: 'Every fraud flag comes with clear reasoning. See exactly which elements triggered the alert—altered amounts, signature mismatches, image manipulation—so your team can make confident decisions and document findings for compliance.',
    },
    {
      icon: <FaCubes />,
      title: 'Enterprise-Ready, Modular Architecture',
      description: 'Built on microservices that integrate with your existing systems. Deploy on-premise or cloud. Scale from pilot to production without rebuilding. Add new document types without starting over.',
    },
  ];

  const steps = [
    {
      icon: <FaUpload />,
      title: 'Upload Your Document',
      description: 'Drag and drop PDFs, images, or connect via API. DAD accepts checks, invoices, IDs, certificates, and custom document types.',
      number: '01',
    },
    {
      icon: <FaCog />,
      title: 'AI-Powered Analysis',
      description: 'From clean data to multi-signal analysis, our intelligent workflows pinpoint anomalies with precision and context.',
      number: '02',
    },
    {
      icon: <FaCheckSquare />,
      title: 'Get Actionable Results',
      description: 'Receive clear fraud scores with visual explanations. Flag suspicious documents for review or auto-approve clean ones. Export reports for audit trails and compliance.',
      number: '03',
    },
  ];

  const benefits = [
    {
      icon: <FaNetworkWired />,
      title: 'Context-Aware Detection',
      description: 'Vector embeddings and retrieval systems enable DAD to understand document context, not just isolated data points. Catch sophisticated fraud that looks right on the surface but wrong in context.',
    },
    {
      icon: <FaLayerGroup />,
      title: 'Modular & Scalable Architecture',
      description: 'Start with checks, expand to invoices, then add medical records—all using the same core platform. Dockerized microservices mean you scale processing without infrastructure headaches.',
    },
    {
      icon: <FaFileAlt />,
      title: 'Built for Compliance',
      description: 'Every detection includes full audit trails with explainable reasoning. Meet regulatory requirements for fraud prevention while reducing manual review documentation time.',
    },
    {
      icon: <FaPuzzlePiece />,
      title: 'Integration-Ready',
      description: 'REST APIs connect DAD to your document management systems, payment processors, and case management tools. No rip-and-replace required.',
    },
  ];

  const pricingPlans = [
    {
      name: 'Starter',
      price: '$XX',
      period: '/month',
      description: 'Perfect for teams processing XX-XX documents monthly',
      features: [
        'Up to XX documents/month',
        'Core fraud detection models',
        'Standard API access',
        'Email support',
        '7-day detection history',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Professional',
      price: '$XX',
      period: '/month',
      description: 'For organizations with high-volume processing needs',
      features: [
        'Up to XX documents/month',
        'Advanced ML ensemble models',
        'LangChain agentic detection',
        'Priority API access',
        'Custom document types',
        '90-day detection history',
        'Dedicated support',
        'SLA guarantee',
      ],
      cta: 'Request Demo',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'Complete solution for mission-critical deployments',
      features: [
        'Unlimited documents',
        'On-premise or private cloud',
        'Custom model training',
        'Multi-document correlation',
        'Compliance reporting suite',
        'Unlimited detection history',
        '24/7 premium support',
        'Account manager',
        'Custom integrations',
      ],
      cta: 'Talk to Sales',
      popular: false,
    },
  ];

  const testimonials = [
    {
      quote: "We piloted DAD on XX historical fraud cases. It flagged XX% that our team missed and reduced false positives by XX%. The explainable results meant we could actually use it in production immediately.",
      author: 'Name',
      role: 'Director of Fraud Prevention, Mid-Size Bank',
    },
    {
      quote: 'The modular architecture was key for us. We started with check fraud detection, proved ROI in XX weeks, then expanded to invoice verification. Same platform, different document types—exactly what we needed.',
      author: 'Name',
      role: 'Chief Technology Officer, Payment Processor',
    },
    {
      quote: 'Setup took days, not months. The API documentation was clear, integration was straightforward, and we were processing real documents in our test environment within XX hours.',
      author: 'Name',
      role: 'Senior Engineer, Healthcare System',
    },
  ];

  const faqs = [
    {
      question: 'How accurate is DAD compared to manual review?',
      answer: "DAD's ensemble ML models achieve XX% accuracy on known fraud patterns in testing. Unlike manual review, DAD maintains consistent performance across thousands of documents and doesn't experience fatigue or bias.",
    },
    {
      question: 'What types of documents can DAD analyze?',
      answer: 'Currently optimized for financial checks with expansion to invoices, medical records, ID documents, and certificates. Our modular architecture allows custom document type training for enterprise clients.',
    },
    {
      question: 'How long does implementation take?',
      answer: 'API integration typically takes 1-2 weeks for standard implementations. Enterprise deployments with custom training require XX-XX weeks depending on document types and volume.',
    },
    {
      question: 'Do you support on-premise deployment?',
      answer: 'Yes. Enterprise plans include on-premise deployment options using our Dockerized microservices architecture. You maintain full control over sensitive document data.',
    },
    {
      question: 'How does pricing scale with document volume?',
      answer: 'Plans are tiered by monthly document volume. As you process more documents, per-document costs decrease. Contact sales for custom volume pricing beyond our listed tiers.',
    },
    {
      question: 'What happens to my document data?',
      answer: 'We process documents to generate fraud scores and insights, then delete source files per your retention policy. Enterprise clients can configure zero-data-retention processing where documents never leave your infrastructure.',
    },
    {
      question: 'Can DAD integrate with our existing systems?',
      answer: 'Yes. DAD provides REST APIs that integrate with document management systems, payment processors, case management tools, and workflow automation platforms. Custom integrations available for enterprise clients.',
    },
    {
      question: 'What kind of support do you provide?',
      answer: 'All plans include email support. Professional plans add priority response times. Enterprise clients receive 24/7 support with dedicated account management and technical resources.',
    },
  ];

  // Hero Animation Background
  const HeroBackground = () => {
    const orbStyle = {
      position: 'absolute',
      inset: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      opacity: 0.3,
    };

    const circleContainerStyle = {
      position: 'relative',
      width: '600px',
      height: '600px',
    };

    const circleStyle = (inset) => ({
      position: 'absolute',
      inset: inset,
      borderRadius: '50%',
      border: `1px solid ${primary}${inset === 0 ? '33' : inset === 8 ? '4D' : '66'}`,
    });

    const iconFloatStyle = (position) => ({
      position: 'absolute',
      width: '64px',
      height: '64px',
      backgroundColor: colors.card,
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
      animation: 'float 3s ease-in-out infinite',
      ...position,
    });
  
  return (
      <div style={orbStyle}>
        <div style={circleContainerStyle}>
          <div style={circleStyle(0)} />
          <div style={circleStyle(8)} />
          <div style={circleStyle(16)} />
          <div style={iconFloatStyle({ top: 0, left: '50%', transform: 'translate(-50%, -50%)' })}>
            <FaShieldAlt style={{ fontSize: '2rem', color: primary }} />
        </div>
          <div style={iconFloatStyle({ bottom: 0, left: '50%', transform: 'translate(-50%, 50%)', animationDelay: '1s' })}>
            <FaLock style={{ fontSize: '2rem', color: primary }} />
          </div>
          <div style={iconFloatStyle({ left: 0, top: '50%', transform: 'translate(-50%, -50%)', animationDelay: '0.5s' })}>
            <FaFileAlt style={{ fontSize: '2rem', color: primary }} />
          </div>
          <div style={iconFloatStyle({ right: 0, top: '50%', transform: 'translate(50%, -50%)', animationDelay: '1.5s' })}>
            <FaSearch style={{ fontSize: '2rem', color: primary }} />
          </div>
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <div style={{
              width: '128px',
              height: '128px',
              backgroundColor: `${primary}33`,
              borderRadius: '50%',
              filter: 'blur(48px)',
            }} />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={containerStyle}>
      {/* Navigation */}
      <nav style={navStyle}>
        <div style={navContainerStyle}>
          <div style={logoStyle} onClick={() => navigate('/')}>
            <img src="/dad-logo.png" alt="DAD Logo" style={{ height: '40px' }} />
          </div>
          
          <div style={{ ...navLinksStyle, display: window.innerWidth >= 768 ? 'flex' : 'none' }}>
            <a style={navLinkStyle} onClick={() => smoothScrollTo('solutions')}>Solutions</a>
            <a style={navLinkStyle} onClick={() => smoothScrollTo('benefits')}>Benefits</a>
            <a style={navLinkStyle} onClick={() => smoothScrollTo('how-it-works')}>How It Works</a>
            <a style={navLinkStyle} onClick={() => smoothScrollTo('pricing')}>Pricing</a>
            <a style={navLinkStyle} onClick={() => smoothScrollTo('faq')}>FAQ</a>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              style={{ ...secondaryButtonStyle, display: window.innerWidth >= 640 ? 'block' : 'none', padding: '0.625rem 1rem' }}
              onClick={() => navigate('/register')}
            >
              Talk to Sales
            </button>
            <button
              style={navButtonStyle}
              onClick={() => navigate('/register')}
              onMouseEnter={(e) => {
                e.target.style.transform = 'scale(1.05)';
                e.target.style.boxShadow = `0 0 40px ${primary}60`;
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'scale(1)';
                e.target.style.boxShadow = `0 0 20px ${primary}40`;
              }}
            >
              Get Started
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              style={{ display: window.innerWidth >= 768 ? 'none' : 'block', color: colors.foreground, background: 'none', border: 'none', fontSize: '1.5rem' }}
            >
              {mobileMenuOpen ? '✕' : '☰'}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div style={{ marginTop: '1rem', paddingBottom: '1rem', animation: 'fade-in 0.6s ease-out' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <a style={navLinkStyle} onClick={() => smoothScrollTo('solutions')}>Solutions</a>
              <a style={navLinkStyle} onClick={() => smoothScrollTo('benefits')}>Benefits</a>
              <a style={navLinkStyle} onClick={() => smoothScrollTo('how-it-works')}>How It Works</a>
              <a style={navLinkStyle} onClick={() => smoothScrollTo('pricing')}>Pricing</a>
              <a style={navLinkStyle} onClick={() => smoothScrollTo('faq')}>FAQ</a>
              <button style={{ ...secondaryButtonStyle, width: '100%' }}>Talk to Sales</button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section style={heroSectionStyle}>
        <HeroBackground />
        <div style={heroContentStyle}>
          <h1 style={heroTitleStyle}>
            Stop Document Fraud Before It Costs You{' '}
            <span style={heroGradientTextStyle}>Millions</span>
          </h1>
          <p style={heroSubtitleStyle}>
            AI-powered fraud detection that catches Anomalies in seconds—not weeks.
          </p>
          <div style={heroButtonsStyle}>
            <button
              style={primaryButtonStyle}
              onClick={() => navigate('/register')}
              onMouseEnter={(e) => {
                e.target.style.transform = 'scale(1.05)';
                e.target.style.boxShadow = `0 0 40px ${primary}60`;
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'scale(1)';
                e.target.style.boxShadow = `0 0 30px ${primary}50`;
              }}
            >
              See DAD in Action
            </button>
            <button
              style={secondaryButtonStyle}
              onClick={() => navigate('/register')}
              onMouseEnter={(e) => {
                e.target.style.borderColor = primary;
                e.target.style.color = primary;
              }}
              onMouseLeave={(e) => {
                e.target.style.borderColor = colors.border;
                e.target.style.color = colors.foreground;
              }}
            >
              Talk to Expert
            </button>
          </div>
          <p style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginTop: '1rem' }}>
            Detect fraud with <span style={{ color: primary, fontWeight: '600' }}>XX%</span> accuracy • No AI expertise required
          </p>
        </div>
      </section>

      {/* Social Proof Section */}
      <SocialProofSection colors={colors} primary={primary} cardStyle={cardStyle} />

      {/* Use Cases Section */}
      <UseCasesSection
        id="solutions"
        colors={colors}
        primary={primary}
        useCases={useCases}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardsGridStyle={cardsGridStyle}
        cardStyle={cardStyle}
        cardIconStyle={cardIconStyle}
        cardTitleStyle={cardTitleStyle}
        cardDescStyle={cardDescStyle}
      />

      {/* Pain Points Section */}
      <PainPointsSection
        colors={colors}
        primary={primary}
        painPoints={painPoints}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardsGridStyle={cardsGridStyle}
        cardStyle={cardStyle}
        cardIconStyle={cardIconStyle}
        cardTitleStyle={cardTitleStyle}
        cardDescStyle={cardDescStyle}
      />

      {/* Why Us Section */}
      <WhyUsSection
        colors={colors}
        primary={primary}
        advantages={advantages}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardStyle={cardStyle}
        cardTitleStyle={cardTitleStyle}
        cardDescStyle={cardDescStyle}
      />

      {/* Benefits Section */}
      <BenefitsSection
        id="benefits"
        colors={colors}
        primary={primary}
        benefits={benefits}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardsGridStyle={cardsGridStyle}
        cardStyle={cardStyle}
        cardIconStyle={cardIconStyle}
        cardTitleStyle={cardTitleStyle}
        cardDescStyle={cardDescStyle}
      />

      {/* How It Works Section */}
      <HowItWorksSection
        id="how-it-works"
        colors={colors}
        primary={primary}
        steps={steps}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardsGridStyle={cardsGridStyle}
        cardStyle={cardStyle}
        cardIconStyle={cardIconStyle}
        cardTitleStyle={cardTitleStyle}
        cardDescStyle={cardDescStyle}
      />

      {/* Pricing Section */}
      <PricingSection
        id="pricing"
        colors={colors}
        primary={primary}
        pricingPlans={pricingPlans}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardsGridStyle={cardsGridStyle}
        cardStyle={cardStyle}
        cardTitleStyle={cardTitleStyle}
        primaryButtonStyle={primaryButtonStyle}
        secondaryButtonStyle={secondaryButtonStyle}
        navigate={navigate}
      />

      {/* Testimonials Section */}
      <TestimonialsSection
        colors={colors}
        primary={primary}
        testimonials={testimonials}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardsGridStyle={cardsGridStyle}
        cardStyle={cardStyle}
        cardTitleStyle={cardTitleStyle}
      />

      {/* CTA Section */}
      <CTASection
        colors={colors}
        primary={primary}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        cardStyle={cardStyle}
        primaryButtonStyle={primaryButtonStyle}
        secondaryButtonStyle={secondaryButtonStyle}
        navigate={navigate}
      />

      {/* FAQ Section */}
      <FAQSection
        id="faq"
        colors={colors}
        primary={primary}
        faqs={faqs}
        sectionStyle={sectionStyle}
        sectionTitleStyle={sectionTitleStyle}
        openFaq={openFaq}
        setOpenFaq={setOpenFaq}
      />

      {/* Footer */}
      <FooterSection colors={colors} primary={primary} />
    </div>
  );
};

// Component Sections
const SocialProofSection = ({ colors, primary, cardStyle }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section style={{ padding: '6rem 1.5rem', backgroundColor: `${colors.secondary}80` }} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '3rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <p style={{ fontSize: '0.875rem', color: colors.mutedForeground, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '2rem' }}>
            Trusted by organizations processing high-stakes documents
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '2rem', opacity: 0.6 }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} style={{
                height: '48px',
                width: '128px',
                backgroundColor: `${colors.muted}80`,
                borderRadius: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                color: colors.mutedForeground,
                margin: '0 auto',
              }}>
                Client Logo {i}
              </div>
            ))}
          </div>
        </div>
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out 0.3s',
        }}>
          <div style={{ ...cardStyle, padding: '2rem', textAlign: 'center' }}>
            <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1rem', justifyContent: 'center' }}>
              {[...Array(5)].map((_, i) => (
                <span key={i} style={{ color: primary, fontSize: '1.25rem' }}>★</span>
              ))}
            </div>
            <blockquote style={{ fontSize: '1.125rem', color: colors.foreground, marginBottom: '1.5rem', lineHeight: '1.6' }}>
              "DAD detected <span style={{ color: primary, fontWeight: '600' }}>XX</span> fraudulent checks in our first month that our manual review missed entirely."
            </blockquote>
            <div style={{ fontSize: '0.875rem', color: colors.mutedForeground }}>
              <p style={{ fontWeight: '600' }}>Name</p>
              <p>VP of Risk Management, Financial Institution</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

const UseCasesSection = ({ id, colors, primary, useCases, sectionStyle, sectionTitleStyle, cardsGridStyle, cardStyle, cardIconStyle, cardTitleStyle, cardDescStyle }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section id={id} style={sectionStyle} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            Built for Organizations Where Document Integrity is{' '}
            <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Non-Negotiable
            </span>
          </h2>
        </div>
        <div style={cardsGridStyle}>
          {useCases.map((useCase, index) => (
            <div
              key={index}
              style={{
                ...cardStyle,
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                transition: `all 0.5s ease-out ${index * 0.15}s`,
              }}
              onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = `${primary}80`;
                e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
                e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
              }}
            >
              <div style={cardIconStyle}>{useCase.icon}</div>
              <h3 style={cardTitleStyle}>{useCase.title}</h3>
              <p style={cardDescStyle}>{useCase.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const PainPointsSection = ({ colors, primary, painPoints, sectionStyle, sectionTitleStyle, cardsGridStyle, cardStyle, cardIconStyle, cardTitleStyle, cardDescStyle }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section style={{ ...sectionStyle, backgroundColor: `${colors.secondary}50` }} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            The Hidden Cost of{' '}
            <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Manual Document Review
            </span>
          </h2>
        </div>
        <div style={cardsGridStyle}>
          {painPoints.map((point, index) => (
            <div
              key={index}
              style={{
                ...cardStyle,
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                transition: `all 0.5s ease-out ${index * 0.15}s`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = `${colors.destructive}4D`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
              }}
            >
              <div style={{ ...cardIconStyle, color: colors.destructive }}>{point.icon}</div>
              <h3 style={cardTitleStyle}>{point.title}</h3>
              <p style={cardDescStyle}>{point.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const WhyUsSection = ({ colors, primary, advantages, sectionStyle, sectionTitleStyle, cardStyle, cardTitleStyle, cardDescStyle }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section style={sectionStyle} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            Why DAD Outperforms{' '}
            <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Traditional Fraud Detection
            </span>
          </h2>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
          {advantages.map((advantage, index) => (
            <div
              key={index}
              style={{
                ...cardStyle,
                display: 'flex',
                flexDirection: window.innerWidth >= 768 ? 'row' : 'column',
                gap: '1.5rem',
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                transition: `all 0.5s ease-out ${index * 0.15}s`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = `${primary}80`;
                e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
                e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
              }}
            >
              <div style={{ flexShrink: 0 }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  backgroundColor: `${primary}1A`,
                  borderRadius: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <div style={{ fontSize: '2rem', color: primary }}>{advantage.icon}</div>
                </div>
              </div>
              <div>
                <h3 style={{ ...cardTitleStyle, marginBottom: '0.75rem' }}>{advantage.title}</h3>
                <p style={{ ...cardDescStyle, fontSize: '1.125rem' }}>{advantage.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const BenefitsSection = ({ id, colors, primary, benefits, sectionStyle, sectionTitleStyle, cardsGridStyle, cardStyle, cardIconStyle, cardTitleStyle, cardDescStyle }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section id={id} style={sectionStyle} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            What Makes DAD <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Different</span>
          </h2>
        </div>
        <div style={{ ...cardsGridStyle, gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))' }}>
          {benefits.map((benefit, index) => (
            <div
              key={index}
              style={{
                ...cardStyle,
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                transition: `all 0.5s ease-out ${index * 0.15}s`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = `${primary}80`;
                e.currentTarget.style.boxShadow = `0 10px 40px ${primary}30`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
                e.currentTarget.style.boxShadow = '0 10px 40px rgba(0, 0, 0, 0.5)';
              }}
            >
              <div style={cardIconStyle}>{benefit.icon}</div>
              <h3 style={cardTitleStyle}>{benefit.title}</h3>
              <p style={cardDescStyle}>{benefit.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const HowItWorksSection = ({ id, colors, primary, steps, sectionStyle, sectionTitleStyle, cardsGridStyle, cardStyle, cardIconStyle, cardTitleStyle, cardDescStyle }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section id={id} style={{ ...sectionStyle, backgroundColor: `${colors.secondary}50` }} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            From Upload to Insight in{' '}
            <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Three Simple Steps
            </span>
          </h2>
        </div>
        <div style={cardsGridStyle}>
          {steps.map((step, index) => (
            <div
              key={index}
              style={{
                ...cardStyle,
                position: 'relative',
                overflow: 'hidden',
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                transition: `all 0.5s ease-out ${index * 0.15}s`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = `${primary}80`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = colors.border;
              }}
            >
              <div style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                fontSize: '4rem',
                fontWeight: 'bold',
                color: `${primary}1A`,
              }}>
                {step.number}
              </div>
              <div style={{ position: 'relative', zIndex: 10 }}>
                <div style={cardIconStyle}>{step.icon}</div>
                <h3 style={cardTitleStyle}>{step.title}</h3>
                <p style={cardDescStyle}>{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const PricingSection = ({ id, colors, primary, pricingPlans, sectionStyle, sectionTitleStyle, cardsGridStyle, cardStyle, cardTitleStyle, primaryButtonStyle, secondaryButtonStyle, navigate }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section id={id} style={{ ...sectionStyle, backgroundColor: `${colors.secondary}50` }} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            Transparent Pricing That{' '}
            <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Scales With You
            </span>
          </h2>
        </div>
        <div style={cardsGridStyle}>
          {pricingPlans.map((plan, index) => (
            <div
              key={index}
              style={{
                ...cardStyle,
                position: 'relative',
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                transition: `all 0.5s ease-out ${index * 0.15}s`,
                border: plan.popular ? `2px solid ${primary}` : `1px solid ${colors.border}`,
                boxShadow: plan.popular ? `0 10px 40px ${primary}33` : '0 10px 40px rgba(0, 0, 0, 0.5)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.borderColor = `${primary}80`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = plan.popular ? primary : colors.border;
              }}
            >
              {plan.popular && (
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                }}>
                  <span style={{
                    backgroundColor: primary,
                    color: colors.primaryForeground,
                    padding: '0.25rem 1rem',
                    borderRadius: '1rem',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                  }}>
                    Most Popular
                  </span>
                </div>
              )}
              <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={cardTitleStyle}>{plan.name}</h3>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '2.5rem', fontWeight: 'bold', color: colors.foreground }}>{plan.price}</span>
                  {plan.price !== 'Custom' && <span style={{ color: colors.mutedForeground }}>{plan.period}</span>}
                </div>
                <p style={{ fontSize: '0.875rem', color: colors.mutedForeground }}>{plan.description}</p>
              </div>
              <ul style={{ listStyle: 'none', marginBottom: '2rem', padding: 0 }}>
                {plan.features.map((feature, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'start', gap: '0.75rem', marginBottom: '0.75rem' }}>
                    <FaCheck style={{ color: primary, flexShrink: 0, marginTop: '0.25rem' }} />
                    <span style={{ fontSize: '0.875rem', color: colors.foreground }}>{feature}</span>
                  </li>
                ))}
              </ul>
              <button
                style={plan.popular ? primaryButtonStyle : secondaryButtonStyle}
                onClick={() => navigate('/register')}
                onMouseEnter={(e) => {
                  if (plan.popular) {
                    e.target.style.transform = 'scale(1.05)';
                    e.target.style.boxShadow = `0 0 40px ${primary}60`;
                  } else {
                    e.target.style.transform = 'scale(1.05)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'scale(1)';
                  if (plan.popular) {
                    e.target.style.boxShadow = `0 0 30px ${primary}50`;
                  }
                }}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const TestimonialsSection = ({ colors, primary, testimonials, sectionStyle, sectionTitleStyle, cardsGridStyle, cardStyle, cardTitleStyle }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section style={sectionStyle} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            Real Results from Organizations{' '}
            <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Like Yours
            </span>
          </h2>
        </div>
        <div style={cardsGridStyle}>
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              style={{
                ...cardStyle,
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                transition: `all 0.5s ease-out ${index * 0.15}s`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ display: 'flex', gap: '0.25rem', marginBottom: '1rem' }}>
                {[...Array(5)].map((_, i) => (
                  <span key={i} style={{ color: primary }}>★</span>
                ))}
              </div>
              <blockquote style={{ color: colors.foreground, marginBottom: '1.5rem', lineHeight: '1.6', fontStyle: 'italic' }}>
                "{testimonial.quote}"
              </blockquote>
              <div style={{ fontSize: '0.875rem' }}>
                <p style={{ fontWeight: '600', color: colors.foreground }}>{testimonial.author}</p>
                <p style={{ color: colors.mutedForeground }}>{testimonial.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const CTASection = ({ colors, primary, sectionStyle, sectionTitleStyle, cardStyle, primaryButtonStyle, secondaryButtonStyle, navigate }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section style={{ ...sectionStyle, backgroundColor: `${colors.secondary}50` }} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <div style={{
            ...cardStyle,
            padding: '3rem',
            textAlign: 'center',
            background: `linear-gradient(135deg, ${colors.card}, ${colors.card}80)`,
            borderColor: `${primary}4D`,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-8px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
          }}
          >
            <h2 style={{ ...sectionTitleStyle, marginBottom: '1rem', fontSize: '2rem' }}>
              See DAD Detect Fraud in Real-Time
            </h2>
            <p style={{ fontSize: '1.25rem', color: colors.mutedForeground, marginBottom: '2rem' }}>
              Upload your own anonymized documents and watch DAD work. No credit card required.
            </p>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
                <button
                style={primaryButtonStyle}
                onClick={() => navigate('/register')}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'scale(1.05)';
                  e.target.style.boxShadow = `0 0 40px ${primary}60`;
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'scale(1)';
                  e.target.style.boxShadow = `0 0 30px ${primary}50`;
                }}
              >
                Try DAD Free for 14 Days
                </button>
              <button
                style={secondaryButtonStyle}
                onClick={() => navigate('/register')}
                onMouseEnter={(e) => {
                  e.target.style.borderColor = primary;
                  e.target.style.transform = 'scale(1.05)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.borderColor = colors.border;
                  e.target.style.transform = 'scale(1)';
                }}
              >
                Book Your Demo
                </button>
            </div>
            <p style={{ fontSize: '0.875rem', color: colors.mutedForeground }}>
              Schedule a personalized demo with our fraud detection experts
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

const FAQSection = ({ id, colors, primary, faqs, sectionStyle, sectionTitleStyle, openFaq, setOpenFaq }) => {
  const { ref, isVisible } = useScrollAnimation();
  
  return (
    <section id={id} style={sectionStyle} ref={ref}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '4rem',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out',
        }}>
          <h2 style={sectionTitleStyle}>
            Common Questions About <span style={{ background: `linear-gradient(135deg, ${primary}, ${colors.redGlow})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>DAD</span>
          </h2>
        </div>
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          opacity: isVisible ? 1 : 0,
          transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.7s ease-out 0.2s',
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {faqs.map((faq, index) => (
              <div
                key={index}
                style={{
                  backgroundColor: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '0.75rem',
                  padding: '1.5rem',
                  transition: 'all 0.3s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = `${primary}80`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = colors.border;
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                >
                  <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: colors.foreground }}>
                    {faq.question}
                  </h3>
                  {openFaq === index ? (
                    <FaChevronUp style={{ color: primary, flexShrink: 0 }} />
                  ) : (
                    <FaChevronDown style={{ color: colors.mutedForeground, flexShrink: 0 }} />
                  )}
                </div>
                {openFaq === index && (
                  <div style={{
                    marginTop: '1rem',
                    paddingTop: '1rem',
                    borderTop: `1px solid ${colors.border}`,
                    color: colors.mutedForeground,
                    lineHeight: '1.6',
                    animation: 'fade-in 0.3s ease-out',
                  }}>
                    {faq.answer}
                  </div>
              )}
            </div>
          ))}
        </div>
    </div>
      </div>
    </section>
  );
};

const FooterSection = ({ colors, primary }) => {
  return (
    <footer style={{
      backgroundColor: `${colors.secondary}80`,
      borderTop: `1px solid ${colors.border}`,
      paddingTop: '4rem',
      paddingBottom: '2rem',
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '3rem', marginBottom: '3rem' }}>
          <div>
            <img src="/dad-logo.png" alt="DAD Logo" style={{ height: '40px', marginBottom: '1rem' }} />
            <p style={{ fontSize: '0.875rem', color: colors.mutedForeground, marginBottom: '1rem' }}>
              Enterprise AI for Document Fraud Detection
            </p>
          </div>
          <div>
            <h4 style={{ fontWeight: '600', marginBottom: '1rem', color: colors.foreground }}>Product</h4>
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {['Solutions', 'How It Works', 'Integrations', 'API Documentation', 'Security & Compliance'].map((item, i) => (
                <li key={i}>
                  <a href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} style={{ fontSize: '0.875rem', color: colors.mutedForeground, textDecoration: 'none' }}>
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 style={{ fontWeight: '600', marginBottom: '1rem', color: colors.foreground }}>Company</h4>
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {['About Us', 'Contact', 'Careers', 'Press Kit'].map((item, i) => (
                <li key={i}>
                  <a href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} style={{ fontSize: '0.875rem', color: colors.mutedForeground, textDecoration: 'none' }}>
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 style={{ fontWeight: '600', marginBottom: '1rem', color: colors.foreground }}>Resources</h4>
            <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {['Documentation', 'Blog', 'Case Studies', 'Support Center'].map((item, i) => (
                <li key={i}>
                  <a href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} style={{ fontSize: '0.875rem', color: colors.mutedForeground, textDecoration: 'none' }}>
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div style={{ borderTop: `1px solid ${colors.border}`, paddingTop: '2rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: '2rem', fontSize: '0.875rem', color: colors.mutedForeground }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaShieldAlt style={{ color: primary }} />
              <span>SOC 2 Type II</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaLock style={{ color: primary }} />
              <span>GDPR Compliant</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaFileAlt style={{ color: primary }} />
              <span>HIPAA Ready</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FaAward style={{ color: primary }} />
              <span>256-bit Encryption</span>
            </div>
          </div>
        </div>
        <div style={{ textAlign: 'center', fontSize: '0.875rem', color: colors.mutedForeground }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: '1.5rem', marginBottom: '1rem' }}>
            <a href="#terms" style={{ color: colors.mutedForeground, textDecoration: 'none' }}>Terms of Service</a>
            <a href="#privacy" style={{ color: colors.mutedForeground, textDecoration: 'none' }}>Privacy Policy</a>
            <a href="#security" style={{ color: colors.mutedForeground, textDecoration: 'none' }}>Security</a>
          </div>
          <p>© 2025 DAD by Xforia. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default LandingPage;
