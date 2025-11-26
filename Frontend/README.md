# XFORIA DAD - Frontend Application

## Overview

The XFORIA Document Analysis & Detection (DAD) Frontend is a modern React-based web application that provides an intuitive interface for fraud detection and document analysis of financial documents. Built with React 18 and featuring a professional dark-themed UI with the XFORIA brand identity.

## Features

### Document Analysis
- **Check Analysis**: Extract and analyze check details with fraud detection
- **Money Order Analysis**: Process money order documents with ML verification
- **Paystub Analysis**: Validate payroll documents with anomaly detection
- **Bank Statement Analysis**: Extract transaction data and detect fraudulent patterns

### Data Export
- **JSON Export**: Complete analysis results with all metadata
- **CSV Export**: Dashboard-ready format for Excel and BI tools
- **Filtered Anomalies**: Clean data exports excluding redundant information

### User Experience
- **Drag & Drop Upload**: Intuitive file upload interface
- **Real-time Analysis**: Live progress indicators and status updates
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark Theme**: Professional XFORIA-branded interface
- **Error Handling**: Comprehensive error messages and recovery options

## Technology Stack

### Core Framework
- **React 18.2**: Modern React with Hooks and Context API
- **React Router DOM 6.x**: Client-side routing and navigation
- **Axios**: HTTP client for API communication

### UI Components
- **React Dropzone**: Drag-and-drop file upload
- **React Icons**: Icon library (Font Awesome)
- **Styled Components (Inline)**: Component-specific styling

### State Management
- **React Context API**: Authentication and global state
- **React Hooks**: useState, useEffect, useCallback for local state

## Project Structure

```
Frontend/
├── public/
│   ├── index.html                # HTML template
│   ├── favicon.ico               # App icon
│   ├── DAD_red_white.png         # Logo assets
│   └── New_FD.png
├── src/
│   ├── components/               # Reusable components
│   │   ├── Header.jsx            # Navigation header
│   │   ├── Footer.jsx            # App footer
│   │   └── ProtectedRoute.jsx    # Auth route wrapper
│   ├── pages/                    # Page components
│   │   ├── LandingPage.jsx       # Public landing page
│   │   ├── SplashPage.jsx        # App intro screen
│   │   ├── LoginPage.jsx         # User login
│   │   ├── RegisterPage.jsx      # User registration
│   │   ├── HomePage.jsx          # Dashboard
│   │   ├── TransactionTypePage.jsx  # Document type selection
│   │   ├── CheckAnalysis.jsx     # Check analysis interface
│   │   ├── MoneyOrderAnalysis.jsx   # Money order analysis
│   │   ├── PaystubAnalysis.jsx   # Paystub analysis
│   │   └── BankStatementAnalysis.jsx  # Bank statement analysis
│   ├── context/                  # React Context providers
│   │   └── AuthContext.js        # Authentication context
│   ├── services/                 # API services
│   │   └── api.js                # Backend API integration
│   ├── styles/                   # Styling and themes
│   │   ├── colors.js             # Color palette
│   │   └── GlobalStyles.css      # Global CSS
│   ├── App.js                    # Main app component
│   ├── index.js                  # App entry point
│   └── App.css                   # App-specific styles
└── package.json                  # Dependencies and scripts
```

## Installation

### Prerequisites

1. Node.js 16.x or higher
2. npm or yarn package manager

### Setup Instructions

1. **Navigate to Frontend directory**
   ```bash
   cd Frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**

   Create a `.env` file in the Frontend directory:
   ```env
   REACT_APP_API_URL=http://localhost:5001/api
   ```

4. **Verify installation**
   ```bash
   npm run build
   ```

## Running the Application

### Development Mode

```bash
npm start
```

The app will open at `http://localhost:3000`

### Production Build

```bash
npm run build
```

The optimized build will be in the `build/` directory.

### Serve Production Build

```bash
npm install -g serve
serve -s build
```

## Color Palette & Branding

### XFORIA DAD Theme

```javascript
// Primary Colors
primaryColor: '#E53935'        // Red (Primary action color)
primaryForeground: '#FFFFFF'   // White text on primary

// Background Colors
background: '#0a0a0a'          // Dark background
foreground: '#f5f5f5'          // Light text
card: '#1a1a1a'                // Card background
secondary: '#2a2a2a'           // Secondary surfaces

// Accent Colors
accent.red: '#E53935'          // Primary red
accent.redLight: '#FFEBEE'     // Light red backgrounds
accent.redDark: '#C62828'      // Dark red hover states

// Status Colors
status.success: '#4CAF50'      // Green for success
status.warning: '#FFC107'      // Yellow for warnings
status.error: '#F44336'        // Red for errors

// Gradients
gradients.navy: 'linear-gradient(135deg, #1a365d 0%, #2d5a8f 100%)'
```

## Page Descriptions

### Public Pages

#### Landing Page (`/`)
- Marketing page with app overview
- Feature highlights
- Call-to-action buttons
- Accessible without login

#### Splash Page (`/splash`)
- App introduction
- Welcome message
- Quick start guide

### Authentication Pages

#### Login Page (`/login`)
- Email/password authentication
- Form validation
- Error handling
- Redirect to dashboard on success

#### Register Page (`/register`)
- New user registration
- Password confirmation
- Email validation
- Auto-login after registration

### Protected Pages (Require Authentication)

#### Home Page (`/home`)
- Dashboard overview
- Quick action buttons
- Recent analysis history
- System health status

#### Transaction Type Page (`/transaction-type`)
- Document type selection
- Icons for each document type
- Navigation to specific analysis pages

#### Analysis Pages

**Check Analysis (`/check-analysis`)**
- Drag-and-drop check upload
- Real-time extraction progress
- Fraud risk scoring
- ML and AI analysis results
- JSON/CSV download options

**Money Order Analysis (`/money-order-analysis`)**
- Money order document processing
- Issuer and payee extraction
- Fraud detection with ensemble models
- Downloadable analysis reports

**Paystub Analysis (`/paystub-analysis`)**
- Payroll document validation
- Earnings and deductions extraction
- Tax withholding verification
- Export to CSV for records

**Bank Statement Analysis (`/bank-statement-analysis`)**
- Transaction history extraction
- Balance reconciliation
- Fraud pattern detection
- Transaction summary export

## API Integration

### API Service (`src/services/api.js`)

The application communicates with the Backend API using Axios:

```javascript
import { analyzeCheck, analyzeMoneyOrder, analyzePaystub, analyzeBankStatement } from './services/api';

// Example usage
const response = await analyzeCheck(fileObject);
if (response.success) {
  console.log(response.data);
}
```

### Available API Functions

- `analyzeCheck(file)`: Analyze check document
- `analyzeMoneyOrder(file)`: Analyze money order
- `analyzePaystub(file)`: Analyze paystub
- `analyzeBankStatement(file)`: Analyze bank statement

### Response Format

```json
{
  "success": true,
  "data": {
    "extracted_data": {...},
    "ml_analysis": {...},
    "ai_analysis": {...},
    "anomalies": [...],
    "confidence_score": 0.85
  }
}
```

## CSV Export Features

All analysis pages include CSV download functionality optimized for dashboards and analytics:

### CSV Structure

```csv
Document Type,Timestamp,Bank Name,Amount,Fraud Risk Score (%),Risk Level,Model Confidence (%),AI Recommendation,Anomaly Count,Top Anomalies
Bank Check,2024-01-15T10:30:00,Chase Bank,$1500.00,23.0,LOW,87.0,APPROVE,0,
```

### CSV Export Features
- **Filtered Anomalies**: Excludes AI recommendations and fraud scores from anomaly column
- **Dashboard Ready**: Optimized for Excel and BI tool imports
- **Proper CSV Escaping**: Handles commas, quotes, and special characters
- **Timestamp Tracking**: ISO format for easy sorting and filtering

## Authentication System

### AuthContext Provider

The app uses React Context for authentication:

```javascript
const { user, login, logout, register } = useAuth();

// Login
await login(email, password);

// Register
await register(email, password);

// Logout
logout();
```

### Protected Routes

Routes are protected using the `ProtectedRoute` component:

```javascript
<Route path="/home" element={
  <ProtectedRoute>
    <HomePage />
  </ProtectedRoute>
} />
```

### Storage

- **Backend**: JSON-based user storage (`Backend/users.json`)
- **Frontend**: Session storage for user data
- **Tokens**: Stored in context (no localStorage for security)

## Development Guidelines

### Component Structure

Components follow a consistent pattern:

```javascript
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { analyzeDocument } from '../services/api';

const DocumentAnalysis = () => {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Component logic...

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
};

export default DocumentAnalysis;
```

### Styling Approach

The app uses inline styles with the color palette from `src/styles/colors.js`:

```javascript
import { colors } from '../styles/colors';

const buttonStyle = {
  backgroundColor: colors.accent.red,
  color: colors.primaryForeground,
  padding: '1rem 2rem',
  borderRadius: '0.5rem',
  // ... more styles
};
```

### Error Handling

All API calls include comprehensive error handling:

```javascript
try {
  const response = await analyzeCheck(file);
  if (response.success) {
    setResults(response.data);
  } else {
    setError(response.error || 'Analysis failed');
  }
} catch (err) {
  setError(err.message || 'Network error');
}
```

## Building for Production

### Optimization Tips

1. **Code Splitting**: React Router automatically code-splits by route
2. **Image Optimization**: Compress images before adding to public folder
3. **Bundle Analysis**: Use `npm run build` and check bundle size
4. **Environment Variables**: Use `.env.production` for production settings

### Production Checklist

- [ ] Update `REACT_APP_API_URL` to production backend URL
- [ ] Run `npm run build` to create optimized build
- [ ] Test build locally with `serve -s build`
- [ ] Configure CORS in backend for production domain
- [ ] Set up HTTPS for secure communication
- [ ] Enable gzip compression on web server
- [ ] Configure caching headers for static assets

## Deployment

### Using Vercel

```bash
npm install -g vercel
vercel --prod
```

### Using Netlify

```bash
npm run build
# Drag and drop 'build' folder to Netlify
```

### Using AWS S3 + CloudFront

```bash
npm run build
aws s3 sync build/ s3://your-bucket-name
# Configure CloudFront distribution
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   ```
   Solution: Verify REACT_APP_API_URL in .env
   Ensure backend is running on the correct port
   ```

2. **CORS Errors**
   ```
   Solution: Check Flask-CORS configuration in backend
   Verify allowed origins include frontend URL
   ```

3. **File Upload Fails**
   ```
   Solution: Check file size (max 16MB)
   Verify file format (JPG, PNG, PDF only)
   ```

4. **Build Errors**
   ```
   Solution: Delete node_modules and package-lock.json
   Run: npm install
   Then: npm run build
   ```

5. **Port 3000 Already in Use**
   ```
   Solution: Kill process or use different port
   Windows: netstat -ano | findstr :3000
   Linux/Mac: lsof -ti:3000 | xargs kill
   ```

## Dependencies

### Production Dependencies

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.22.0",
  "axios": "^1.6.0",
  "react-dropzone": "^14.2.0",
  "react-icons": "^5.0.0"
}
```

### Development Dependencies

```json
{
  "react-scripts": "5.0.1",
  "@testing-library/react": "^13.4.0",
  "@testing-library/jest-dom": "^5.17.0"
}
```

## Testing

### Running Tests

```bash
npm test
```

### Test Coverage

```bash
npm test -- --coverage
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

### Lighthouse Scores (Target)
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+

### Optimization Techniques
- Lazy loading of routes
- Image optimization
- Minified production builds
- Code splitting
- Caching strategies

## Security

### Best Practices Implemented
- No sensitive data in localStorage
- HTTPS in production
- CORS restrictions
- Input validation
- XSS prevention
- CSRF protection (backend)

## License

Copyright © 2024 XFORIA. All rights reserved.

## Support

For technical support or questions:
- Email: support@xforia.com
- Documentation: https://docs.xforia.com

## Version History

### v1.0.0 (Current)
- Initial release
- Four document analysis types (Check, Money Order, Paystub, Bank Statement)
- Authentication system
- CSV and JSON export functionality
- Responsive dark theme UI
- Real-time fraud detection display
