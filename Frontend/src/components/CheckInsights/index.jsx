import { useState } from 'react';
import { colors } from '../../styles/colors';
import { useCheckData } from './hooks/useCheckData';
import CheckFilters from './CheckFilters';
import CheckMetrics from './CheckMetrics';
import CheckCharts from './CheckCharts';

const CheckInsights = () => {
  const [inputMode, setInputMode] = useState('api');
  
  const {
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
    loadCheckData
  } = useCheckData(inputMode);

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const containerStyle = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '1.5rem',
    backgroundColor: colors.background,
  };

  const cardStyle = {
    backgroundColor: colors.card,
    borderRadius: '0.75rem',
    padding: '2rem',
    marginBottom: '2rem',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
    border: `1px solid ${colors.border}`,
  };

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h2 style={{ color: colors.foreground, marginBottom: '1.5rem' }}>
          {inputMode === 'upload' ? 'Check Insights from CSV' : 'Check Insights from Database'}
        </h2>

        {inputMode === 'api' && (
          <>
            <CheckFilters
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              handleSearchChecks={handleSearchChecks}
              dateFilter={dateFilter}
              setDateFilter={setDateFilter}
              fetchChecksList={fetchChecksList}
              bankFilter={bankFilter}
              totalRecords={totalRecords}
              loadingChecksList={loadingChecksList}
              showCustomDatePicker={showCustomDatePicker}
              setShowCustomDatePicker={setShowCustomDatePicker}
              customDateRange={customDateRange}
              setCustomDateRange={setCustomDateRange}
              setError={setError}
              availableBanks={availableBanks}
              setBankFilter={setBankFilter}
              allChecksData={allChecksData}
              setChecksList={setChecksList}
              loadCheckData={loadCheckData}
              checksList={checksList}
              selectedCheckId={selectedCheckId}
              setSelectedCheckId={setSelectedCheckId}
              primary={primary}
            />

            {error && (
              <div style={{
                backgroundColor: colors.accent.redLight,
                color: colors.accent.red,
                padding: '1rem',
                borderRadius: '8px',
                marginTop: '1rem',
                fontWeight: '500',
              }}>
                {error}
              </div>
            )}
          </>
        )}
      </div>

      {csvData && (
        <>
          <CheckMetrics csvData={csvData} primary={primary} />
          <CheckCharts
            csvData={csvData}
            bankFilter={bankFilter}
            primary={primary}
            COLORS={COLORS}
            activePieIndex={activePieIndex}
            setActivePieIndex={setActivePieIndex}
            activeBarIndex={activeBarIndex}
            setActiveBarIndex={setActiveBarIndex}
            activeBankBarIndex={activeBankBarIndex}
            setActiveBankBarIndex={setActiveBankBarIndex}
          />
        </>
      )}
    </div>
  );
};

export default CheckInsights;
