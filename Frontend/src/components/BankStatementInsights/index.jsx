import { useState } from 'react';
import { colors } from '../../styles/colors';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useBankStatementData } from './hooks/useBankStatementData';
import BankStatementFilters from './BankStatementFilters';
import BankStatementMetrics from './BankStatementMetrics';
import BankStatementCharts from './BankStatementCharts';

const BankStatementInsights = () => {
  const [inputMode, setInputMode] = useState('api');
  
  const {
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
    loadBankStatementData
  } = useBankStatementData(inputMode);

  const primary = colors.primaryColor || colors.accent?.red || '#E53935';

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
          Bank Statement Insights
        </h2>

        {inputMode === 'api' && (
          <>
            <BankStatementFilters
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              handleSearchBankStatements={handleSearchBankStatements}
              fetchBankStatementsList={fetchBankStatementsList}
              dateFilter={dateFilter}
              setDateFilter={setDateFilter}
              bankFilter={bankFilter}
              setBankFilter={setBankFilter}
              availableBanks={availableBanks}
              totalRecords={totalRecords}
              loadingBankStatementsList={loadingBankStatementsList}
              showCustomDatePicker={showCustomDatePicker}
              setShowCustomDatePicker={setShowCustomDatePicker}
              customDateRange={customDateRange}
              setCustomDateRange={setCustomDateRange}
              setError={setError}
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
          <BankStatementMetrics csvData={csvData} primary={primary} />
          <BankStatementCharts
            csvData={csvData}
            bankFilter={bankFilter}
            primary={primary}
            activePieIndex={activePieIndex}
            setActivePieIndex={setActivePieIndex}
            activeBarIndex={activeBarIndex}
            setActiveBarIndex={setActiveBarIndex}
          />
          {csvData.fraudTrendData && csvData.fraudTrendData.length > 0 && (
            <div style={{
              backgroundColor: colors.card,
              padding: '24px',
              borderRadius: '12px',
              border: `1px solid ${colors.border}`,
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              marginTop: '2rem'
            }}>
              <h3 style={{
                fontSize: '18px',
                fontWeight: '600',
                color: colors.foreground,
                marginBottom: '20px',
                paddingBottom: '12px',
                borderBottom: `2px solid ${colors.border}`,
              }}>Fraud Trend Over Time</h3>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={csvData.fraudTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="date" stroke={colors.mutedForeground} />
                  <YAxis yAxisId="left" stroke={colors.mutedForeground} />
                  <YAxis yAxisId="right" orientation="right" stroke={colors.mutedForeground} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.card,
                      border: `1px solid ${colors.border}`,
                      color: colors.foreground
                    }}
                  />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="avgRisk" stroke={primary} strokeWidth={2} name="Avg Risk Score %" />
                  <Line yAxisId="right" type="monotone" dataKey="highRiskCount" stroke="#ef4444" strokeWidth={2} name="High-Risk Count" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BankStatementInsights;
