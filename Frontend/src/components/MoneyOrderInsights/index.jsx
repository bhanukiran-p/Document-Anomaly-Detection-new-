import { useState } from 'react';
import { colors } from '../../styles/colors';
import { useMoneyOrderData } from './hooks/useMoneyOrderData';
import MoneyOrderFilters from './MoneyOrderFilters';
import MoneyOrderMetrics from './MoneyOrderMetrics';
import MoneyOrderCharts from './MoneyOrderCharts';

const MoneyOrderInsights = () => {
  const [inputMode, setInputMode] = useState('api');
  
  const {
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
    setMoneyOrdersList,
    getRootProps,
    getInputProps,
    isDragActive
  } = useMoneyOrderData(inputMode);

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
          Money Order Insights
        </h2>

        {inputMode === 'api' && (
          <>
            <MoneyOrderFilters
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              handleSearchMoneyOrders={handleSearchMoneyOrders}
              availableIssuers={availableIssuers}
              issuerFilter={issuerFilter}
              setIssuerFilter={setIssuerFilter}
              allMoneyOrdersData={allMoneyOrdersData}
              setMoneyOrdersList={setMoneyOrdersList}
              loadMoneyOrderData={loadMoneyOrderData}
              dateFilter={dateFilter}
              setDateFilter={setDateFilter}
              fetchMoneyOrdersList={fetchMoneyOrdersList}
              totalRecords={totalRecords}
              loadingMoneyOrdersList={loadingMoneyOrdersList}
              showCustomDatePicker={showCustomDatePicker}
              setShowCustomDatePicker={setShowCustomDatePicker}
              customDateRange={customDateRange}
              setCustomDateRange={setCustomDateRange}
              setError={setError}
              moneyOrdersList={moneyOrdersList}
              selectedMoneyOrderId={selectedMoneyOrderId}
              setSelectedMoneyOrderId={setSelectedMoneyOrderId}
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
          <MoneyOrderMetrics csvData={csvData} primary={primary} />
          <MoneyOrderCharts csvData={csvData} issuerFilter={issuerFilter} primary={primary} COLORS={COLORS} />
        </>
      )}
    </div>
  );
};

export default MoneyOrderInsights;
