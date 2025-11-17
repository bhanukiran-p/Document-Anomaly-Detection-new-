import React from 'react'; // eslint-disable-line no-unused-vars
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext'; // eslint-disable-line no-unused-vars
import Header from './components/Header';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute'; // eslint-disable-line no-unused-vars
import LandingPage from './pages/LandingPage';
import SplashPage from './pages/SplashPage';
import TransactionTypePage from './pages/TransactionTypePage';
import LoginPage from './pages/LoginPage'; // eslint-disable-line no-unused-vars
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import CheckAnalysis from './pages/CheckAnalysis';
import PaystubAnalysis from './pages/PaystubAnalysis';
import MoneyOrderAnalysis from './pages/MoneyOrderAnalysis';
import BankStatementAnalysis from './pages/BankStatementAnalysis';
import './styles/GlobalStyles.css';

function AppContent() {
  const location = useLocation();
  const isCustomLayout = location.pathname === '/' || location.pathname === '/splash' || location.pathname === '/transaction-type' || location.pathname === '/login' || location.pathname === '/register';

  const appStyle = {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  };

  const mainStyle = {
    flex: 1,
    padding: isCustomLayout ? '0' : '2rem',
  };

  return (
    <div style={appStyle}>
      {!isCustomLayout && <Header />}
      <main style={mainStyle}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/splash" element={<SplashPage />} />
          <Route path="/transaction-type" element={<TransactionTypePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/finance" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
          <Route path="/check-analysis" element={<CheckAnalysis />} />
          <Route path="/paystub-analysis" element={<PaystubAnalysis />} />
          <Route path="/money-order-analysis" element={<MoneyOrderAnalysis />} />
          <Route path="/bank-statement-analysis" element={<BankStatementAnalysis />} />
        </Routes>
      </main>
      {!isCustomLayout && <Footer />}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

export default App;

