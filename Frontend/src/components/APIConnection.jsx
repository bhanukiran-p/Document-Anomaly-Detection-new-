import React, { useState } from 'react';
import axios from 'axios';
import { colors } from '../styles/colors';

const APIConnection = () => {
  const [apiConfig, setApiConfig] = useState({
    url: '',
    method: 'GET',
    headers: '',
    params: '',
  });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const primary = colors.primaryColor || '#E53935';

  const formGroupStyle = {
    marginBottom: '1.5rem',
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '0.5rem',
    fontSize: '0.95rem',
    fontWeight: '600',
    color: colors.foreground,
  };

  const inputStyle = {
    width: '100%',
    padding: '0.75rem',
    backgroundColor: colors.background,
    border: `1px solid ${colors.border}`,
    borderRadius: '0.5rem',
    color: colors.foreground,
    fontSize: '0.95rem',
    boxSizing: 'border-box',
    transition: 'border-color 0.3s',
  };

  const selectStyle = {
    ...inputStyle,
    cursor: 'pointer',
  };

  const textareaStyle = {
    ...inputStyle,
    minHeight: '80px',
    fontFamily: 'monospace',
    resize: 'vertical',
  };

  const buttonStyle = {
    backgroundColor: primary,
    color: '#fff',
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    fontWeight: '600',
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.3s',
    boxShadow: `0 0 20px ${primary}40`,
    width: '100%',
  };

  const messageStyle = (type) => ({
    borderRadius: '0.5rem',
    padding: '1rem',
    marginTop: '1rem',
    fontSize: '0.95rem',
    backgroundColor: type === 'error' ? 'rgba(244, 67, 54, 0.1)' : 'rgba(16, 185, 129, 0.1)',
    border: `1px solid ${type === 'error' ? '#F44336' : '#10b981'}`,
    color: type === 'error' ? '#FF6B6B' : '#10b981',
  });

  const parseJSON = (str) => {
    if (!str.trim()) return {};
    try {
      return JSON.parse(str);
    } catch {
      return {};
    }
  };

  const handleConnect = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      if (!apiConfig.url) {
        throw new Error('API URL is required');
      }

      const config = {
        method: apiConfig.method.toLowerCase(),
        url: apiConfig.url,
        headers: {
          'Content-Type': 'application/json',
          ...parseJSON(apiConfig.headers),
        },
      };

      if (apiConfig.method === 'GET' && apiConfig.params) {
        config.params = parseJSON(apiConfig.params);
      } else if (apiConfig.method === 'POST' && apiConfig.params) {
        config.data = parseJSON(apiConfig.params);
      }

      const response = await axios(config);
      setSuccess(`Successfully connected! Received ${JSON.stringify(response.data).length} bytes of data.`);
    } catch (err) {
      setError(
        err.response?.data?.message ||
        err.message ||
        'Failed to connect to API'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleConnect}>
      <div style={formGroupStyle}>
        <label style={labelStyle}>API URL *</label>
        <input
          type="text"
          style={inputStyle}
          placeholder="https://api.example.com/financial-data"
          value={apiConfig.url}
          onChange={(e) =>
            setApiConfig({ ...apiConfig, url: e.target.value })
          }
          onFocus={(e) => (e.target.style.borderColor = primary)}
          onBlur={(e) => (e.target.style.borderColor = colors.border)}
        />
      </div>

      <div style={formGroupStyle}>
        <label style={labelStyle}>Method</label>
        <select
          style={selectStyle}
          value={apiConfig.method}
          onChange={(e) =>
            setApiConfig({ ...apiConfig, method: e.target.value })
          }
          onFocus={(e) => (e.target.style.borderColor = primary)}
          onBlur={(e) => (e.target.style.borderColor = colors.border)}
        >
          <option>GET</option>
          <option>POST</option>
        </select>
      </div>

      <div style={formGroupStyle}>
        <label style={labelStyle}>Headers (JSON)</label>
        <textarea
          style={textareaStyle}
          placeholder={'{\n  "Authorization": "Bearer YOUR_TOKEN"\n}'}
          value={apiConfig.headers}
          onChange={(e) =>
            setApiConfig({ ...apiConfig, headers: e.target.value })
          }
          onFocus={(e) => (e.target.style.borderColor = primary)}
          onBlur={(e) => (e.target.style.borderColor = colors.border)}
        />
      </div>

      <div style={formGroupStyle}>
        <label style={labelStyle}>
          {apiConfig.method === 'GET' ? 'Query Parameters' : 'Request Body'} (JSON)
        </label>
        <textarea
          style={textareaStyle}
          placeholder={
            apiConfig.method === 'GET'
              ? '{\n  "account_id": "12345",\n  "date_range": "30d"\n}'
              : '{\n  "transactions": []\n}'
          }
          value={apiConfig.params}
          onChange={(e) =>
            setApiConfig({ ...apiConfig, params: e.target.value })
          }
          onFocus={(e) => (e.target.style.borderColor = primary)}
          onBlur={(e) => (e.target.style.borderColor = colors.border)}
        />
      </div>

      <button
        type="submit"
        style={buttonStyle}
        onMouseEnter={(e) => {
          e.target.style.transform = 'translateY(-2px)';
          e.target.style.boxShadow = `0 6px 30px ${primary}60`;
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = `0 0 20px ${primary}40`;
        }}
        disabled={isLoading}
      >
        {isLoading ? 'Connecting...' : 'Connect to API'}
      </button>

      {error && <div style={messageStyle('error')}>{error}</div>}
      {success && <div style={messageStyle('success')}>{success}</div>}
    </form>
  );
};

export default APIConnection;
