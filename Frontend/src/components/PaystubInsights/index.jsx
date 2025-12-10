import { useState } from 'react';
import { colors } from '../../styles/colors';
import { usePaystubData } from './hooks/usePaystubData';
import PaystubFilters from './PaystubFilters';
import PaystubMetrics from './PaystubMetrics';
import PaystubCharts from './PaystubCharts';

const PaystubInsights = () => {
  const [inputMode, setInputMode] = useState('api');
  const [activePieIndex, setActivePieIndex] = useState(null);
  const [activeBarIndex, setActiveBarIndex] = useState(null);
  
  const {
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
    filteredDataLength,
    setSearchQuery,
    setDateFilter,
    setEmployerFilter,
    setFraudTypeFilter,
    setShowCustomDatePicker,
    setCustomDateRange,
    setError
  } = usePaystubData(inputMode);

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  const COLORS = [
    primary,
    colors.status.warning || '#FFA726',
    colors.accent.redDark || '#C62828',
    '#FF6B6B',
    colors.status.success || '#4CAF50',
    '#9C27B0',
    '#2196F3',
    '#FF9800'
  ];

  const styles = {
    container: {
      padding: '0',
      maxWidth: '100%',
      margin: '0',
      backgroundColor: 'transparent',
      borderRadius: '0'
    },
    loading: {
      textAlign: 'center',
      padding: '20px',
      color: colors.mutedForeground
    },
    error: {
      backgroundColor: colors.accent.red,
      color: 'white',
      padding: '12px',
      borderRadius: '4px',
      marginBottom: '20px'
    }
  };

  return (
    <div style={styles.container}>
      {loading && <div style={styles.loading}>Loading...</div>}
      {loadingPaystubsList && <div style={styles.loading}>Fetching paystubs from database...</div>}
      {error && <div style={styles.error}>{error}</div>}

      {/* Filters Section */}
      {csvData && (
        <PaystubFilters
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          employerFilter={employerFilter}
          setEmployerFilter={setEmployerFilter}
          availableEmployers={availableEmployers}
          dateFilter={dateFilter}
          setDateFilter={setDateFilter}
          showCustomDatePicker={showCustomDatePicker}
          setShowCustomDatePicker={setShowCustomDatePicker}
          customDateRange={customDateRange}
          setCustomDateRange={setCustomDateRange}
          setError={setError}
          fraudTypeFilter={fraudTypeFilter}
          setFraudTypeFilter={setFraudTypeFilter}
          availableFraudTypes={availableFraudTypes}
          filteredDataLength={filteredDataLength}
          totalRecords={totalRecords}
          primary={primary}
        />
      )}

      {/* Summary KPI Cards */}
      {csvData && (
        <PaystubMetrics csvData={csvData} primary={primary} />
      )}

      {/* Charts Section */}
      {csvData && (
        <PaystubCharts
          csvData={csvData}
          primary={primary}
          COLORS={COLORS}
          activePieIndex={activePieIndex}
          setActivePieIndex={setActivePieIndex}
          activeBarIndex={activeBarIndex}
          setActiveBarIndex={setActiveBarIndex}
        />
      )}
    </div>
  );
};

export default PaystubInsights;
