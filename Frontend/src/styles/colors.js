// DAD Design System Color Palette
export const colors = {
  // Primary Colors (New Design System)
  background: '#030507',           // hsl(210, 40%, 2%) - Very dark blue-black
  foreground: '#FAFAFA',            // hsl(0, 0%, 98%) - Off-white text
  primaryColor: '#E53935',          // hsl(0, 72%, 55%) - Red (main brand color) - Use colors.primaryColor
  primaryForeground: '#FFFFFF',     // hsl(0, 0%, 100%) - White

  // Navy Shades
  navy: '#224460',                  // hsl(210, 47%, 25%)
  navyDark: '#132538',              // hsl(210, 50%, 15%)

  // Red Variations
  redAccent: '#E53935',             // hsl(0, 72%, 55%) - Primary red
  redGlow: '#F05653',               // hsl(0, 72%, 65%) - Lighter red for glows

  // UI Element Colors
  card: '#0E1419',                  // hsl(210, 30%, 8%) - Dark navy cards
  secondary: '#15191F',             // hsl(210, 30%, 12%) - Slightly lighter sections
  muted: '#1C2229',                 // hsl(210, 30%, 15%) - Subtle backgrounds
  border: '#1C2229',                // hsl(210, 30%, 15%) - Border color
  input: '#1C2229',                 // hsl(210, 30%, 15%) - Input border

  // Text Colors
  mutedForeground: '#94979C',       // hsl(210, 10%, 60%) - Secondary text
  destructive: '#F44336',           // hsl(0, 84.2%, 60.2%) - Error states

  // Gradients (as CSS strings for direct use)
  gradients: {
    dark: 'linear-gradient(135deg, hsl(210, 50%, 8%), hsl(210, 50%, 4%))',
    navy: 'linear-gradient(135deg, hsl(210, 47%, 25%), hsl(210, 50%, 15%))',
    red: 'linear-gradient(135deg, hsl(0, 72%, 55%), hsl(0, 72%, 65%))',
  },

  // Legacy support (for backward compatibility with existing pages)
  // Note: New design system uses 'primary' as string (#E53935)
  // Legacy pages use primary.navy, primary.blue, etc.
  primary: {
    // New design system primary (red) is available as colors.primary (string above)
    // Legacy structure maintained for existing pages:
    navy: '#224460',
    blue: '#2c5282',
    lightBlue: '#e6f2ff',
  },
  accent: {
    red: '#E53935',
    redDark: '#b91c1c',
    redLight: '#fee2e2',
  },
  neutral: {
    white: '#FAFAFA',
    gray50: '#f9fafb',
    gray100: '#f3f4f6',
    gray200: '#e5e7eb',
    gray300: '#d1d5db',
    gray400: '#9ca3af',
    gray500: '#6b7280',
    gray600: '#4b5563',
    gray700: '#374151',
    gray800: '#1f2937',
    gray900: '#111827',
  },
  status: {
    success: '#10b981',
    successLight: '#d1fae5',
    warning: '#f59e0b',
    warningLight: '#fef3c7',
    info: '#3b82f6',
    infoLight: '#dbeafe',
  },
};
