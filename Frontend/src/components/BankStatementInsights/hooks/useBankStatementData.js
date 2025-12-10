import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { parseCSV, processData } from '../BankStatementDataProcessor';

export const useBankStatementData = (inputMode = 'api') => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bankStatementsList, setBankStatementsList] = useState([]);
  const [loadingBankStatementsList, setLoadingBankStatementsList] = useState(false);
  const [selectedBankStatementId, setSelectedBankStatementId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null);
  const [totalRecords, setTotalRecords] = useState(0);
  const [bankFilter, setBankFilter] = useState(null);
  const [availableBanks, setAvailableBanks] = useState([]);
  const [allBankStatementsData, setAllBankStatementsData] = useState([]);
  const [activePieIndex, setActivePieIndex] = useState(null);
  const [activeBarIndex, setActiveBarIndex] = useState(null);
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [customDateRange, setCustomDateRange] = useState({ startDate: '', endDate: '' });

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const rows = parseCSV(text);

        if (rows.length === 0) {
          setError('No valid data found in CSV');
          setLoading(false);
          return;
        }

        const processed = processData(rows);
        setCsvData(processed);
        setError(null);
      } catch (err) {
        setError(`Error parsing CSV: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    reader.onerror = () => {
      setError('Error reading file');
      setLoading(false);
    };

    reader.readAsText(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    multiple: false
  });

  const fetchBankStatementsList = async (filter = null, bank = null, customRange = null) => {
    setLoadingBankStatementsList(true);
    setError(null);
    setCsvData(null);
    try {
      let url = '/api/bank-statements/list';

      const params = new URLSearchParams();

      if (customRange && (customRange.startDate || customRange.endDate)) {
        if (customRange.startDate) params.append('start_date', customRange.startDate);
        if (customRange.endDate) params.append('end_date', customRange.endDate);
      } else if (filter) {
        params.append('date_filter', filter);
      }

      if (params.toString()) {
        url += '?' + params.toString();
      }

      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        const fetchedData = data.data || [];
        setAllBankStatementsData(fetchedData);

        const uniqueBanks = [...new Set(fetchedData.map(bs => bs.bank_name).filter(Boolean))].sort();
        setAvailableBanks(uniqueBanks);

        let filteredData = fetchedData;
        if (bank) {
          filteredData = fetchedData.filter(bs => bs.bank_name === bank);
          setBankFilter(bank);
        } else {
          setBankFilter(null);
        }

        setBankStatementsList(filteredData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(filter);
        if (filteredData.length > 0) {
          loadBankStatementData(filteredData);
        } else {
          setError('No bank statements found for the selected filters');
        }
      } else {
        setError(data.message || 'Failed to fetch bank statements');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to fetch bank statements from database');
      console.error('Error fetching bank statements:', err);
      setCsvData(null);
    } finally {
      setLoadingBankStatementsList(false);
    }
  };

  const handleSearchBankStatements = async (query) => {
    if (!query) {
      setBankFilter(null);
      fetchBankStatementsList(dateFilter);
      return;
    }
    setLoadingBankStatementsList(true);
    setError(null);
    setCsvData(null);
    try {
      const response = await fetch(`/api/bank-statements/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setBankStatementsList(data.data);
        if (data.data && data.data.length > 0) {
          loadBankStatementData(data.data);
        } else {
          setError('No bank statements found matching your search');
        }
      } else {
        setError(data.message || 'Search failed');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to search bank statements');
      console.error('Error searching bank statements:', err);
      setCsvData(null);
    } finally {
      setLoadingBankStatementsList(false);
    }
  };

  const loadBankStatementData = async (bankStatements) => {
    if (!bankStatements || bankStatements.length === 0) {
      setError('No bank statements selected');
      return;
    }

    try {
      const rows = bankStatements.map(bs => {
        let anomalies = '';
        if (bs.top_anomalies) {
          if (typeof bs.top_anomalies === 'string') {
            try {
              const parsed = JSON.parse(bs.top_anomalies);
              anomalies = Array.isArray(parsed) ? parsed.map(a =>
                typeof a === 'string' ? a : (a.message || a.type || JSON.stringify(a))
              ).join(' | ') : bs.top_anomalies;
            } catch {
              anomalies = bs.top_anomalies;
            }
          } else if (Array.isArray(bs.top_anomalies)) {
            anomalies = bs.top_anomalies.map(a =>
              typeof a === 'string' ? a : (a.message || a.type || JSON.stringify(a))
            ).join(' | ');
          } else {
            anomalies = JSON.stringify(bs.top_anomalies);
          }
        }

        return {
          'fraud_risk_score': bs.fraud_risk_score || 0,
          'Fraud Risk Score (%)': (bs.fraud_risk_score || 0) * 100,
          'ai_recommendation': bs.ai_recommendation || 'UNKNOWN',
          'AI Recommendation': bs.ai_recommendation || 'UNKNOWN',
          'bank_name': bs.bank_name || 'Unknown',
          'Bank Name': bs.bank_name || 'Unknown',
          'account_holder': bs.account_holder || '',
          'Account Holder': bs.account_holder || '',
          'account_number': bs.account_number || '',
          'Account Number': bs.account_number || '',
          'statement_period': bs.statement_period || '',
          'Statement Period': bs.statement_period || '',
          'timestamp': bs.timestamp || bs.created_at || '',
          'Timestamp': bs.timestamp || bs.created_at || '',
          'model_confidence': bs.model_confidence || 0,
          'Model Confidence (%)': (bs.model_confidence || 0) * 100,
          'top_anomalies': anomalies,
          'Top Anomalies': anomalies,
          'anomalies': anomalies,
          'Anomalies': anomalies,
          'fraud_types': bs.fraud_types || bs.fraud_type || null,
          'Fraud Types': bs.fraud_types || bs.fraud_type || null,
          'fraud_type': bs.fraud_types || bs.fraud_type || null,
          'Fraud Type': bs.fraud_types || bs.fraud_type || null,
        };
      });

      const processed = processData(rows);
      setCsvData(processed);
      setError(null);
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(`Error processing bank statements: ${err.message}`);
    }
  };

  useEffect(() => {
    if (inputMode === 'api' && allBankStatementsData.length === 0 && !loadingBankStatementsList) {
      fetchBankStatementsList();
    }
  }, []);

  return {
    csvData,
    loading,
    error,
    bankStatementsList,
    allBankStatementsData,
    loadingBankStatementsList,
    selectedBankStatementId,
    searchQuery,
    dateFilter,
    totalRecords,
    bankFilter,
    availableBanks,
    activePieIndex,
    activeBarIndex,
    showCustomDatePicker,
    customDateRange,
    setSearchQuery,
    setDateFilter,
    setBankFilter,
    setSelectedBankStatementId,
    setActivePieIndex,
    setActiveBarIndex,
    setShowCustomDatePicker,
    setCustomDateRange,
    setError,
    setBankStatementsList,
    fetchBankStatementsList,
    handleSearchBankStatements,
    loadBankStatementData,
    getRootProps,
    getInputProps,
    isDragActive
  };
};
