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

  // Use primaryColor for new design system red
  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

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
      backgroundColor: colors.background,
      padding: '20px',
      background: colors.gradients.dark,
    },
    card: {
      width: '100%',
      maxWidth: '450px',
      backgroundColor: colors.card,
      borderRadius: '0.75rem',
      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
      padding: '40px',
      border: `1px solid ${colors.border}`,
    },
    logoSection: {
      textAlign: 'center',
      marginBottom: '32px',
    },
    logoContainer: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '0.75rem',
      marginBottom: '24px',
    },
    logoImage: {
      height: '100px',
      width: 'auto',
      objectFit: 'contain',
      display: 'block',
    },
    logoText: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      color: primary,
    },
    title: {
      fontSize: '28px',
      fontWeight: '700',
      color: colors.foreground,
      margin: '0 0 8px 0',
    },
    subtitle: {
      fontSize: '14px',
      color: colors.mutedForeground,
      margin: 0,
    },
    form: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
    },
    formGroup: {
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
    },
    label: {
      fontSize: '14px',
      fontWeight: '500',
      color: colors.foreground,
    },
    input: {
      padding: '12px 16px',
      fontSize: '14px',
      border: `2px solid ${colors.border}`,
      borderRadius: '0.5rem',
      fontFamily: 'inherit',
      transition: 'all 0.3s ease',
      boxSizing: 'border-box',
      backgroundColor: colors.muted,
      color: colors.foreground,
    },
    inputFocus: {
      borderColor: primary,
      boxShadow: `0 0 0 3px ${primary}20`,
    },
    inputPlaceholder: {
      color: colors.mutedForeground,
    },
    errorMessage: {
      backgroundColor: `${colors.destructive}20`,
      border: `1px solid ${colors.destructive}`,
      color: colors.destructive,
      padding: '12px 16px',
      borderRadius: '0.5rem',
      fontSize: '14px',
    },
    button: {
      padding: '12px 16px',
      fontSize: '16px',
      fontWeight: '600',
      border: 'none',
      borderRadius: '0.5rem',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      backgroundColor: primary,
      color: colors.primaryForeground,
      boxShadow: `0 0 20px ${primary}40`,
    },
    buttonHover: {
      transform: 'translateY(-2px)',
      boxShadow: `0 6px 30px ${primary}60`,
    },
    buttonDisabled: {
      backgroundColor: colors.muted,
      cursor: 'not-allowed',
      transform: 'none',
      boxShadow: 'none',
      opacity: 0.6,
    },
    linkSection: {
      textAlign: 'center',
      marginTop: '20px',
    },
    linkText: {
      fontSize: '14px',
      color: colors.mutedForeground,
      margin: 0,
    },
    link: {
      color: primary,
      textDecoration: 'none',
      fontWeight: '600',
      transition: 'color 0.3s ease',
    },
  };

  const [focusedField, setFocusedField] = useState(null);
  const [buttonHovered, setButtonHovered] = useState(false);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* Logo Section */}
        <div style={styles.logoSection}>
          <div style={styles.logoContainer}>
            <img src="/DAD_red_black.png" alt="DAD Logo" style={styles.logoImage} />
          </div>
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
                ...(focusedField === 'email' ? styles.inputFocus : {}),
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
                ...(focusedField === 'password' ? styles.inputFocus : {}),
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
                ...(focusedField === 'confirmPassword' ? styles.inputFocus : {}),
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
              ...(buttonHovered && !loading ? styles.buttonHover : {}),
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
              onMouseEnter={(e) => (e.target.style.opacity = '0.8')}
              onMouseLeave={(e) => (e.target.style.opacity = '1')}
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
