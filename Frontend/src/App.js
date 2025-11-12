import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import SplashPage from './pages/SplashPage';
import TransactionTypePage from './pages/TransactionTypePage';
import HomePage from './pages/HomePage';
import CheckAnalysis from './pages/CheckAnalysis';
import PaystubAnalysis from './pages/PaystubAnalysis';
import MoneyOrderAnalysis from './pages/MoneyOrderAnalysis';
import './styles/GlobalStyles.css';

function AppContent() {
  const location = useLocation();
  const isCustomLayout = location.pathname === '/' || location.pathname === '/splash' || location.pathname === '/transaction-type';
  
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
          <Route path="/finance" element={<HomePage />} />
          <Route path="/check-analysis" element={<CheckAnalysis />} />
          <Route path="/paystub-analysis" element={<PaystubAnalysis />} />
          <Route path="/money-order-analysis" element={<MoneyOrderAnalysis />} />
        </Routes>
      </main>
      {!isCustomLayout && <Footer />}
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;

