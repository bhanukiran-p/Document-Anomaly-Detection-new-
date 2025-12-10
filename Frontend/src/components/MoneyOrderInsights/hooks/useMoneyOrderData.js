import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { parseCSV, processData } from '../MoneyOrderDataProcessor';

export const useMoneyOrderData = (inputMode = 'api') => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [moneyOrdersList, setMoneyOrdersList] = useState([]);
  const [allMoneyOrdersData, setAllMoneyOrdersData] = useState([]);
  const [loadingMoneyOrdersList, setLoadingMoneyOrdersList] = useState(false);
  const [selectedMoneyOrderId, setSelectedMoneyOrderId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null);
  const [issuerFilter, setIssuerFilter] = useState(null);
  const [availableIssuers, setAvailableIssuers] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
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

        const processed = processData(rows, issuerFilter);
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
  }, [issuerFilter]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    multiple: false
  });

  const fetchMoneyOrdersList = async (filter = null, issuer = null, customRange = null) => {
    setLoadingMoneyOrdersList(true);
    setError(null);
    setCsvData(null);
    try {
      let url = '/api/money-orders/list';

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
        const issuers = [...new Set(data.data.map(mo => mo.money_order_institute).filter(Boolean))].sort();
        setAvailableIssuers(issuers);

        setAllMoneyOrdersData(data.data);

        let filteredData = data.data;
        const activeIssuerFilter = issuer !== null ? issuer : issuerFilter;
        if (activeIssuerFilter && activeIssuerFilter !== '' && activeIssuerFilter !== 'All Issuers') {
          const normalizedIssuer = activeIssuerFilter.trim();
          filteredData = data.data.filter(mo => {
            const moIssuer = (mo.money_order_institute || '').trim();
            return moIssuer === normalizedIssuer;
          });
        }

        setMoneyOrdersList(filteredData);
        setTotalRecords(data.total_records || data.count);
        setDateFilter(filter);
        if (filteredData && filteredData.length > 0) {
          const issuerToPass = (activeIssuerFilter && activeIssuerFilter !== '' && activeIssuerFilter !== 'All Issuers')
            ? activeIssuerFilter.trim()
            : null;
          loadMoneyOrderData(filteredData, issuerToPass);
        } else {
          setError('No money orders found for the selected filters');
        }
      } else {
        setError(data.message || 'Failed to fetch money orders');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to fetch money orders from database');
      console.error('Error fetching money orders:', err);
      setCsvData(null);
    } finally {
      setLoadingMoneyOrdersList(false);
    }
  };

  const handleSearchMoneyOrders = async (query) => {
    if (!query) {
      setIssuerFilter(null);
      fetchMoneyOrdersList(dateFilter);
      return;
    }
    setLoadingMoneyOrdersList(true);
    setError(null);
    setCsvData(null);
    try {
      const response = await fetch(`/api/money-orders/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await response.json();
      if (data.success) {
        setMoneyOrdersList(data.data);
        if (data.data && data.data.length > 0) {
          loadMoneyOrderData(data.data);
        } else {
          setError('No money orders found matching your search');
        }
      } else {
        setError(data.message || 'Search failed');
        setCsvData(null);
      }
    } catch (err) {
      setError('Failed to search money orders');
      console.error('Error searching money orders:', err);
      setCsvData(null);
    } finally {
      setLoadingMoneyOrdersList(false);
    }
  };

  const loadMoneyOrderData = async (moneyOrders, explicitIssuer = null) => {
    if (!moneyOrders || moneyOrders.length === 0) {
      setError('No money orders selected');
      return;
    }

    try {
      const issuerToUse = explicitIssuer !== null ? explicitIssuer : issuerFilter;

      const rows = moneyOrders.map(mo => ({
        'fraud_risk_score': mo.fraud_risk_score || 0,
        'RiskScore': mo.fraud_risk_score || 0,
        'ai_recommendation': mo.ai_recommendation || 'UNKNOWN',
        'Decision': mo.ai_recommendation || 'UNKNOWN',
        'money_order_institute': mo.money_order_institute || 'Unknown',
        'IssuerName': mo.money_order_institute || 'Unknown',
        'issuer_name': mo.money_order_institute || 'Unknown',
        'money_order_number': mo.money_order_number || 'N/A',
        'MoneyOrderNumber': mo.money_order_number || 'N/A',
        'amount': mo.amount || 0,
        'Amount': mo.amount || 0,
        'purchaser_name': mo.purchaser_name || '',
        'PurchaserName': mo.purchaser_name || '',
        'payee_name': mo.payee_name || '',
        'PayeeName': mo.payee_name || '',
        'issue_date': mo.issue_date || '',
        'IssueDate': mo.issue_date || '',
        'created_at': mo.created_at || mo.timestamp || '',
      }));

      if (issuerToUse && issuerToUse !== '' && issuerToUse !== 'All Issuers') {
        const normalizedIssuer = issuerToUse.trim();
        const filteredRows = rows.filter(r => {
          const rowIssuer = (r['IssuerName'] || r['money_order_institute'] || r['issuer_name'] || '').trim();
          return rowIssuer === normalizedIssuer;
        });

        console.log('Issuer Filter Debug:', {
          selectedIssuer: normalizedIssuer,
          totalRows: rows.length,
          filteredRows: filteredRows.length,
          sampleIssuers: [...new Set(rows.map(r => r['IssuerName'] || r['money_order_institute'] || 'Unknown'))].slice(0, 5)
        });

        if (filteredRows.length === 0) {
          setError(`No money orders found for issuer: ${issuerToUse}. Found issuers: ${[...new Set(rows.map(r => r['IssuerName'] || r['money_order_institute'] || 'Unknown'))].join(', ')}`);
          return;
        }

        const processed = processData(filteredRows, normalizedIssuer);
        setCsvData(processed);
      } else {
        const processed = processData(rows, null);
        setCsvData(processed);
      }
      setError(null);
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err) {
      setError(`Error processing money orders: ${err.message}`);
    }
  };

  useEffect(() => {
    if (inputMode === 'api' && allMoneyOrdersData.length === 0 && !loadingMoneyOrdersList) {
      fetchMoneyOrdersList();
    }
  }, []);

  return {
    csvData,
    loading,
    error,
    moneyOrdersList,
    allMoneyOrdersData,
    loadingMoneyOrdersList,
    selectedMoneyOrderId,
    searchQuery,
    dateFilter,
    issuerFilter,
    availableIssuers,
    totalRecords,
    showCustomDatePicker,
    customDateRange,
    setSearchQuery,
    setDateFilter,
    setIssuerFilter,
    setSelectedMoneyOrderId,
    setShowCustomDatePicker,
    setCustomDateRange,
    setError,
    fetchMoneyOrdersList,
    handleSearchMoneyOrders,
    loadMoneyOrderData,
    getRootProps,
    getInputProps,
    isDragActive
  };
};
