import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { parseCSV, processData } from '../PaystubDataProcessor';

export const usePaystubData = (inputMode = 'api') => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [paystubsList, setPaystubsList] = useState([]);
  const [allPaystubsData, setAllPaystubsData] = useState([]);
  const [loadingPaystubsList, setLoadingPaystubsList] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState(null);
  const [employerFilter, setEmployerFilter] = useState(null);
  const [fraudTypeFilter, setFraudTypeFilter] = useState(null);
  const [availableEmployers, setAvailableEmployers] = useState([]);
  const [availableFraudTypes, setAvailableFraudTypes] = useState([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [showCustomDatePicker, setShowCustomDatePicker] = useState(false);
  const [customDateRange, setCustomDateRange] = useState({ startDate: '', endDate: '' });

  const onDrop = useCallback(acceptedFiles => {
    setLoading(true);
    setError(null);

    const file = acceptedFiles[0];
    if (!file) {
      setLoading(false);
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const rows = parseCSV(text);

        if (rows.length === 0) {
          setError('No valid data in CSV file');
          setLoading(false);
          return;
        }

        setAllPaystubsData(rows);
        setTotalRecords(rows.length);

        const employers = [...new Set(rows.map(r => r['employer_name'] || 'Unknown'))]
          .filter(emp => emp && emp !== 'Unknown' && emp.toLowerCase() !== 'unknown');
        setAvailableEmployers(employers.sort());

        const fraudTypes = new Set();
        rows.forEach(r => {
          const fraudType = r['fraud_types'];
          if (fraudType) {
            if (Array.isArray(fraudType)) {
              fraudType.forEach(ft => {
                const typeStr = String(ft || '').trim();
                if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
                  fraudTypes.add(typeStr.replace(/_/g, ' '));
                }
              });
            } else {
              const typeStr = String(fraudType || '').trim();
              if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
                fraudTypes.add(typeStr.replace(/_/g, ' '));
              }
            }
          }
        });
        setAvailableFraudTypes(Array.from(fraudTypes).sort());

        const processed = processData(rows, null, null, rows);
        setCsvData(processed);
        setPaystubsList(rows);
        setLoading(false);
      } catch (err) {
        setError(`Error parsing CSV: ${err.message}`);
        setLoading(false);
      }
    };
    reader.readAsText(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] }
  });

  const fetchPaystubsFromAPI = async () => {
    setLoadingPaystubsList(true);
    setError(null);
    try {
      const response = await fetch('/api/paystubs/insights');
      if (!response.ok) throw new Error('Failed to fetch paystubs');

      const data = await response.json();
      const rows = data.data || [];

      setAllPaystubsData(rows);
      setTotalRecords(rows.length);

      const employers = [...new Set(rows.map(r => r.employer_name || 'Unknown'))]
        .filter(emp => emp && emp !== 'Unknown' && emp.toLowerCase() !== 'unknown');
      setAvailableEmployers(employers.sort());

      const fraudTypes = new Set();
      rows.forEach(r => {
        const fraudType = r.fraud_types;
        if (fraudType) {
          if (Array.isArray(fraudType)) {
            fraudType.forEach(ft => {
              const typeStr = String(ft || '').trim();
              if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
                fraudTypes.add(typeStr.replace(/_/g, ' '));
              }
            });
          } else {
            const typeStr = String(fraudType || '').trim();
            if (typeStr && typeStr !== 'No Flag' && typeStr !== 'null' && typeStr !== 'undefined') {
              fraudTypes.add(typeStr.replace(/_/g, ' '));
            }
          }
        }
      });
      setAvailableFraudTypes(Array.from(fraudTypes).sort());

      const processed = processData(rows, null, null, rows);
      setCsvData(processed);
      setPaystubsList(rows);
    } catch (err) {
      setError(`Error fetching paystubs: ${err.message}`);
    }
    setLoadingPaystubsList(false);
  };

  useEffect(() => {
    if (inputMode === 'api' && allPaystubsData.length === 0 && !loadingPaystubsList) {
      fetchPaystubsFromAPI();
    }
  }, []);

  const getFilteredData = () => {
    let filtered = allPaystubsData;

    if (employerFilter && employerFilter !== '' && employerFilter !== 'All Employers') {
      filtered = filtered.filter(p => p.employer_name === employerFilter);
    }

    if (searchQuery.trim()) {
      filtered = filtered.filter(p =>
        (p.employee_name || '').toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (dateFilter) {
      if (dateFilter === 'custom' && (customDateRange.startDate || customDateRange.endDate)) {
        filtered = filtered.filter(p => {
          const createdAt = new Date(p.created_at);
          const startDate = customDateRange.startDate ? new Date(customDateRange.startDate) : null;
          const endDate = customDateRange.endDate ? new Date(customDateRange.endDate) : null;

          if (startDate && endDate) {
            return createdAt >= startDate && createdAt <= endDate;
          } else if (startDate) {
            return createdAt >= startDate;
          } else if (endDate) {
            return createdAt <= endDate;
          }
          return true;
        });
      } else {
        const now = new Date();
        const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        const sixtyDaysAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000);
        const ninetyDaysAgo = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);

        filtered = filtered.filter(p => {
          const createdAt = new Date(p.created_at);
          if (dateFilter === 'last_30') return createdAt >= thirtyDaysAgo;
          if (dateFilter === 'last_60') return createdAt >= sixtyDaysAgo && createdAt < thirtyDaysAgo;
          if (dateFilter === 'last_90') return createdAt >= ninetyDaysAgo && createdAt < sixtyDaysAgo;
          if (dateFilter === 'older') return createdAt < ninetyDaysAgo;
          return true;
        });
      }
    }

    if (fraudTypeFilter && fraudTypeFilter !== '' && fraudTypeFilter !== 'All Fraud Types') {
      filtered = filtered.filter(p => {
        const fraudType = p.fraud_types;
        if (!fraudType) return false;

        const normalizedFilter = fraudTypeFilter.toLowerCase().trim();

        if (Array.isArray(fraudType)) {
          return fraudType.some(ft => {
            const typeStr = String(ft || '').trim();
            const normalizedType = typeStr.replace(/_/g, ' ').toLowerCase();
            return normalizedType === normalizedFilter || typeStr.toLowerCase() === normalizedFilter;
          });
        } else {
          const typeStr = String(fraudType || '').trim();
          const normalizedType = typeStr.replace(/_/g, ' ').toLowerCase();
          return normalizedType === normalizedFilter || typeStr.toLowerCase() === normalizedFilter;
        }
      });
    }

    return filtered;
  };

  useEffect(() => {
    if (allPaystubsData.length > 0) {
      const filtered = getFilteredData();
      setPaystubsList(filtered);
      const processed = processData(filtered, employerFilter, fraudTypeFilter, allPaystubsData);
      setCsvData(processed);
      setTimeout(() => {
        document.querySelector('[data-metrics-section]')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [employerFilter, fraudTypeFilter, searchQuery, dateFilter, customDateRange, allPaystubsData]);

  const filteredData = getFilteredData();

  return {
    csvData,
    loading,
    error,
    paystubsList,
    allPaystubsData,
    loadingPaystubsList,
    searchQuery,
    dateFilter,
    employerFilter,
    fraudTypeFilter,
    availableEmployers,
    availableFraudTypes,
    totalRecords,
    showCustomDatePicker,
    customDateRange,
    filteredDataLength: filteredData.length,
    setSearchQuery,
    setDateFilter,
    setEmployerFilter,
    setFraudTypeFilter,
    setShowCustomDatePicker,
    setCustomDateRange,
    setError,
    fetchPaystubsFromAPI,
    getRootProps,
    getInputProps,
    isDragActive
  };
};
