import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { colors } from '../styles/colors';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate form
    if (!email || !password || !confirmPassword) {
      setError('All fields are required');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      await register(email, password);
      navigate('/transaction-type');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const styles = {
    container: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.background.main,
      padding: '20px'
    },
    card: {
      width: '100%',
      maxWidth: '450px',
      backgroundColor: colors.background.card,
      borderRadius: '12px',
      boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
      padding: '40px'
    },
    logoSection: {
      textAlign: 'center',
      marginBottom: '32px'
    },
    logo: {
      width: '120px',
      height: '80px',
      marginBottom: '16px',
      margin: '0 auto 16px auto',
      objectFit: 'contain'
    },
    title: {
      fontSize: '28px',
      fontWeight: '700',
      color: colors.primary.navy,
      margin: '0 0 8px 0'
    },
    subtitle: {
      fontSize: '14px',
      color: colors.neutral.gray600,
      margin: 0
    },
    form: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    },
    formGroup: {
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    },
    label: {
      fontSize: '14px',
      fontWeight: '500',
      color: colors.primary.navy
    },
    input: {
      padding: '12px 16px',
      fontSize: '14px',
      border: `2px solid ${colors.neutral.gray200}`,
      borderRadius: '8px',
      fontFamily: 'inherit',
      transition: 'border-color 0.3s ease',
      boxSizing: 'border-box'
    },
    inputFocus: {
      borderColor: colors.primary.blue
    },
    errorMessage: {
      backgroundColor: colors.status.error + '10',
      border: `1px solid ${colors.status.error}`,
      color: colors.status.error,
      padding: '12px 16px',
      borderRadius: '8px',
      fontSize: '14px'
    },
    button: {
      padding: '0.5rem 1.25rem',
      fontSize: '16px',
      fontWeight: '600',
      border: 'none',
      borderRadius: '9999px', // Pill shape
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      backgroundColor: colors.accent.red,
      color: colors.neutral.white
    },
    buttonHover: {
      backgroundColor: colors.accent.redDark,
      transform: 'translateY(-2px)',
      boxShadow: '0 6px 20px rgba(220, 38, 38, 0.3)'
    },
    buttonDisabled: {
      backgroundColor: colors.neutral.gray400,
      cursor: 'not-allowed',
      transform: 'none'
    },
    divider: {
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      margin: '24px 0'
    },
    dividerLine: {
      flex: 1,
      height: '1px',
      backgroundColor: colors.neutral.gray200
    },
    dividerText: {
      color: colors.neutral.gray500,
      fontSize: '12px',
      fontWeight: '500'
    },
    linkSection: {
      textAlign: 'center',
      marginTop: '20px'
    },
    linkText: {
      fontSize: '14px',
      color: colors.neutral.gray600,
      margin: 0
    },
    link: {
      color: colors.accent.red,
      textDecoration: 'none',
      fontWeight: '600',
      transition: 'color 0.3s ease'
    },
    linkHover: {
      color: colors.accent.redDark
    }
  };

  const [focusedField, setFocusedField] = useState(null);
  const [buttonHovered, setButtonHovered] = useState(false);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* Logo Section */}
        <div style={styles.logoSection}>
          <img
            src="/dad-logo.png"
            alt="DAD Logo"
            style={styles.logo}
          />
          <h1 style={styles.title}>Create Account</h1>
          <p style={styles.subtitle}>Join XFORIA to get started</p>
        </div>

        {/* Form */}
        <form style={styles.form} onSubmit={handleSubmit}>
          {/* Error Message */}
          {error && (
            <div style={styles.errorMessage}>
              ⚠️ {error}
            </div>
          )}

          {/* Email Field */}
          <div style={styles.formGroup}>
            <label style={styles.label}>Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              style={{
                ...styles.input,
                ...(focusedField === 'email' ? styles.inputFocus : {})
              }}
              onFocus={() => setFocusedField('email')}
              onBlur={() => setFocusedField(null)}
              disabled={loading}
            />
          </div>

          {/* Password Field */}
          <div style={styles.formGroup}>
            <label style={styles.label}>Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              style={{
                ...styles.input,
                ...(focusedField === 'password' ? styles.inputFocus : {})
              }}
              onFocus={() => setFocusedField('password')}
              onBlur={() => setFocusedField(null)}
              disabled={loading}
            />
          </div>

          {/* Confirm Password Field */}
          <div style={styles.formGroup}>
            <label style={styles.label}>Confirm Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
              style={{
                ...styles.input,
                ...(focusedField === 'confirmPassword' ? styles.inputFocus : {})
              }}
              onFocus={() => setFocusedField('confirmPassword')}
              onBlur={() => setFocusedField(null)}
              disabled={loading}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              ...styles.button,
              ...(loading ? styles.buttonDisabled : {}),
              ...(buttonHovered && !loading ? styles.buttonHover : {})
            }}
            onMouseEnter={() => setButtonHovered(true)}
            onMouseLeave={() => setButtonHovered(false)}
          >
            {loading ? '⏳ Creating account...' : 'Create Account'}
          </button>
        </form>

        {/* Login Link */}
        <div style={styles.linkSection}>
          <p style={styles.linkText}>
            Already have an account?{' '}
            <Link
              to="/login"
              style={styles.link}
              onMouseEnter={(e) => (e.target.style.color = colors.accent.redDark)}
              onMouseLeave={(e) => (e.target.style.color = colors.accent.red)}
            >
              Login here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
