import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import CheckAnalysis from './pages/CheckAnalysis';
import PaystubAnalysis from './pages/PaystubAnalysis';
import MoneyOrderAnalysis from './pages/MoneyOrderAnalysis';
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
    <Router>
      <div style={appStyle}>
        <Header />
        <main style={mainStyle}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/check-analysis" element={<CheckAnalysis />} />
            <Route path="/paystub-analysis" element={<PaystubAnalysis />} />
            <Route path="/money-order-analysis" element={<MoneyOrderAnalysis />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;

