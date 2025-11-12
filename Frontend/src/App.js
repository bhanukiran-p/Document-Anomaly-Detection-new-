import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import CheckAnalysis from './pages/CheckAnalysis';
import PaystubAnalysis from './pages/PaystubAnalysis';
<<<<<<< Updated upstream
=======
import MoneyOrderAnalysis from './pages/MoneyOrderAnalysis';
import StatementAnalysis from './pages/StatementAnalysis';
>>>>>>> Stashed changes
import './styles/GlobalStyles.css';

function App() {
  const appStyle = {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  };
  
  const mainStyle = {
    flex: 1,
    padding: '2rem',
  };
  
  return (
<<<<<<< Updated upstream
=======
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
          <Route path="/statement-analysis" element={<StatementAnalysis />} />
        </Routes>
      </main>
      {!isCustomLayout && <Footer />}
    </div>
  );
}

function App() {
  return (
>>>>>>> Stashed changes
    <Router>
      <div style={appStyle}>
        <Header />
        <main style={mainStyle}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/check-analysis" element={<CheckAnalysis />} />
            <Route path="/paystub-analysis" element={<PaystubAnalysis />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;

