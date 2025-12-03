import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is already logged in on mount
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const storedUser = localStorage.getItem('user');

    if (token && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        // Set default Authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (parseError) {
        console.warn('Invalid user data in storage, clearing session.', parseError);
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);


  const register = async (email, password) => {
    try {
      setError(null);

      const response = await axios.post(`${API_BASE_URL}/auth/register`, {
        email,
        password
      });

      const { token, user: userData } = response.data;

      localStorage.setItem('authToken', token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

      setUser(userData);
      return response.data;
    } catch (err) {
      console.error('Register error:', err);
      const errorMessage = err.response?.data?.error || err.message || 'Registration failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);

      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        email,
        password
      });

      const { token, user: userData } = response.data;

      localStorage.setItem('authToken', token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

      setUser(userData);
      return response.data;
    } catch (err) {
      console.error('Login error:', err);
      const errorMessage = err.response?.data?.error || err.message || 'Login failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setError(null);
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
