import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { parseCSV, processData } from '../CheckDataProcessor';

export const useCheckData = (inputMode = 'api') => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [checksList, setChecksList] = useState([]);
  const [loadingChecksList, setLoadingChecksList] = useState(false);
  const [selectedCheckId, setSelectedCheckId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null);
  const [totalRecords, setTotalRecords] = useState(0);
  const [bankFilter, setBankFilter] = useState(null);
  const [availableBanks, setAvailableBanks] = useState([]);
  const [allChecksData, setAllChecksData] = useState([]);
  const [activePieIndex, setActivePieIndex] = useState(null);
  const [activeBarIndex, setActiveBarIndex] = useState(null);
  const [activeBankBarIndex, setActiveBankBarIndex] = useState({ bankIndex: null, series: null });
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

  const fetchChecksList = async (filter = null, bank = null, customRange = null) => {
    setLoadingChecksList(true);
    setError(null);
    setCsvData(null);
    try {
      let url = '/api/checks/list';

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
        setAllChecksData(fetchedData);

        const uniqueBanks = [...new Set(fetchedData.map(check => check.bank_name).filter(Boolean))].sort();
        setAvailableBanks(uniqueBanks);

        let filteredData = fetchedData;
        if (bank) {
          filteredData = fetchedData.filter(check => check.bank_name === bank);
          setBankFilter(bank);
        } else {
          setBankFilter(null);
        }

        setChecksList(filteredData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(filter);
        if (filteredData.length > 0) {
          loadCheckData(filteredData);
        } else {
          setError('No checks found for the selected filters');
        }
      } else {
        setError(data.message || 'Failed to fetch checks');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to fetch checks from database');
      console.error('Error fetching checks:', err);
      setCsvData(null);
    } finally {
      setLoadingChecksList(false);
    }
  };

  const handleSearchChecks = async (query) => {
    if (!query) {
      setBankFilter(null);
      fetchChecksList(dateFilter);
      return;
    }
    setLoadingChecksList(true);
    setError(null);
    setCsvData(null);
    try {
      const response = await fetch(`/api/checks/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setChecksList(data.data);
        if (data.data && data.data.length > 0) {
          loadCheckData(data.data);
        } else {
          setError('No checks found matching your search');
        }
      } else {
        setError(data.message || 'Search failed');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to search checks');
      console.error('Error searching checks:', err);
      setCsvData(null);
    } finally {
      setLoadingChecksList(false);
    }
  };

  const loadCheckData = async (checks) => {
    if (!checks || checks.length === 0) {
      setError('No checks selected');
      return;
    }

    try {
      const rows = checks.map(check => ({
        'fraud_risk_score': check.fraud_risk_score || 0,
        'RiskScore': check.fraud_risk_score || 0,
        'ai_recommendation': check.ai_recommendation || 'UNKNOWN',
        'Decision': check.ai_recommendation || 'UNKNOWN',
        'bank_name': check.bank_name || 'Unknown',
        'BankName': check.bank_name || 'Unknown',
        'check_number': check.check_number || 'N/A',
        'CheckNumber': check.check_number || 'N/A',
        'amount': check.amount || 0,
        'Amount': check.amount || 0,
        'payer_name': check.payer_name || '',
        'PayerName': check.payer_name || '',
        'payee_name': check.payee_name || '',
        'PayeeName': check.payee_name || '',
        'check_date': check.check_date || '',
        'CheckDate': check.check_date || '',
        'created_at': check.created_at || check.timestamp || '',
        'model_confidence': check.model_confidence || 0,
        'Confidence': check.model_confidence || 0,
        'confidence': check.model_confidence || 0,
      }));

      const processed = processData(rows);
      setCsvData(processed);
      setError(null);
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(`Error processing checks: ${err.message}`);
    }
  };

  useEffect(() => {
    if (inputMode === 'api' && allChecksData.length === 0 && !loadingChecksList) {
      fetchChecksList();
    }
  }, []);

  return {
    csvData,
    loading,
    error,
    checksList,
    allChecksData,
    loadingChecksList,
    selectedCheckId,
    searchQuery,
    dateFilter,
    totalRecords,
    bankFilter,
    availableBanks,
    activePieIndex,
    activeBarIndex,
    activeBankBarIndex,
    showCustomDatePicker,
    customDateRange,
    setSearchQuery,
    setDateFilter,
    setBankFilter,
    setSelectedCheckId,
    setActivePieIndex,
    setActiveBarIndex,
    setActiveBankBarIndex,
    setShowCustomDatePicker,
    setCustomDateRange,
    setError,
    setChecksList,
    fetchChecksList,
    handleSearchChecks,
    loadCheckData,
    getRootProps,
    getInputProps,
    isDragActive
  };
};
