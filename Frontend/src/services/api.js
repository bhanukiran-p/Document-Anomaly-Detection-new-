import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Check Analysis API
export const analyzeCheck = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post(`${API_BASE_URL}/check/analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to analyze check' };
  }
};

// Paystub Analysis API
export const analyzePaystub = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post(`${API_BASE_URL}/paystub/analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to analyze paystub' };
  }
};

// Money Order Analysis API
export const analyzeMoneyOrder = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post(`${API_BASE_URL}/money-order/analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to analyze money order' };
  }
};

// Bank Statement Analysis API
export const analyzeBankStatement = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post(`${API_BASE_URL}/bank-statement/analyze`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to analyze bank statement' };
  }
};

// Fraud Detection - PDF Validation API
export const validatePDFForFraud = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post(`${API_BASE_URL}/fraud/validate-pdf`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to validate PDF for fraud detection' };
  }
};

// Fraud Detection - Transaction Prediction API
export const predictTransactionFraud = async (transactionData, modelType = 'ensemble') => {
  try {
    const response = await axios.post(`${API_BASE_URL}/fraud/transaction-predict`, {
      transaction_data: transactionData,
      model_type: modelType,
    });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to predict transaction fraud' };
  }
};

// Fraud Detection - Get Models Status
export const getFraudModelsStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/fraud/models-status`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to get fraud models status' };
  }
};

export default api;

