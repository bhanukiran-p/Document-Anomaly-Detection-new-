import { colors } from '../../styles/colors';
import { FaCog } from 'react-icons/fa';

const BankStatementFilters = ({
  searchQuery,
  setSearchQuery,
  handleSearchBankStatements,
  fetchBankStatementsList,
  dateFilter,
  setDateFilter,
  bankFilter,
  setBankFilter,
  availableBanks,
  totalRecords,
  loadingBankStatementsList,
  showCustomDatePicker,
  setShowCustomDatePicker,
  customDateRange,
  setCustomDateRange,
  setError,
  primary
}) => {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Search bank statements..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            if (e.target.value) {
              handleSearchBankStatements(e.target.value);
            } else {
              fetchBankStatementsList(dateFilter);
            }
          }}
          style={{
            padding: '0.75rem',
            borderRadius: '0.5rem',
            border: `1px solid ${colors.border}`,
            fontSize: '14px',
            flex: 1,
            minWidth: '200px',
            backgroundColor: colors.card,
            color: colors.foreground
          }}
        />
        {availableBanks.length > 0 && (
          <select
            value={bankFilter || ''}
            onChange={(e) => {
              const bank = e.target.value || null;
              setBankFilter(bank);
              fetchBankStatementsList(dateFilter, bank);
            }}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              border: `1px solid ${colors.border}`,
              fontSize: '14px',
              backgroundColor: colors.card,
              color: colors.foreground,
              cursor: 'pointer'
            }}
          >
            <option value="">All Banks</option>
            {availableBanks.map(bank => (
              <option key={bank} value={bank}>{bank}</option>
            ))}
          </select>
        )}
        <div style={{ fontSize: '12px', color: colors.mutedForeground, whiteSpace: 'nowrap' }}>
          {totalRecords} records
        </div>
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <button
          onClick={() => fetchBankStatementsList(null, bankFilter)}
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            backgroundColor: !dateFilter ? primary : colors.secondary,
            color: !dateFilter ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: !dateFilter ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          All Time
        </button>
        <button
          onClick={() => fetchBankStatementsList('last_30', bankFilter)}
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            backgroundColor: dateFilter === 'last_30' ? primary : colors.secondary,
            color: dateFilter === 'last_30' ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: dateFilter === 'last_30' ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          Last 30
        </button>
        <button
          onClick={() => fetchBankStatementsList('last_60', bankFilter)}
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            backgroundColor: dateFilter === 'last_60' ? primary : colors.secondary,
            color: dateFilter === 'last_60' ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: dateFilter === 'last_60' ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          Last 60
        </button>
        <button
          onClick={() => fetchBankStatementsList('last_90', bankFilter)}
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            backgroundColor: dateFilter === 'last_90' ? primary : colors.secondary,
            color: dateFilter === 'last_90' ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: dateFilter === 'last_90' ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          Last 90
        </button>
        <button
          onClick={() => fetchBankStatementsList('older', bankFilter)}
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            backgroundColor: dateFilter === 'older' ? primary : colors.secondary,
            color: dateFilter === 'older' ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: dateFilter === 'older' ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          Older
        </button>
        <button
          onClick={() => setShowCustomDatePicker(!showCustomDatePicker)}
          style={{
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            backgroundColor: dateFilter === 'custom' ? primary : colors.secondary,
            color: dateFilter === 'custom' ? colors.primaryForeground : colors.foreground,
            border: `1px solid ${colors.border}`,
            cursor: 'pointer',
            fontWeight: dateFilter === 'custom' ? '600' : '500',
            transition: 'all 0.3s',
          }}
        >
          Custom Range
        </button>
        {(dateFilter || bankFilter) && (
          <button
            onClick={() => {
              setDateFilter(null);
              setBankFilter(null);
              setSearchQuery('');
              setCustomDateRange({ startDate: '', endDate: '' });
              setShowCustomDatePicker(false);
              fetchBankStatementsList(null, null);
            }}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '0.5rem',
              backgroundColor: colors.accent.redLight || '#fee2e2',
              color: colors.accent.red || primary,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: '600',
              transition: 'all 0.3s',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span>Reset Filters</span>
          </button>
        )}
      </div>

      {/* Custom Date Range Picker */}
      {showCustomDatePicker && (
        <div style={{
          marginTop: '1rem',
          padding: '1.5rem',
          backgroundColor: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: '0.5rem',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ marginBottom: '1rem', fontWeight: '600', color: colors.foreground }}>
            Select Custom Date Range
          </div>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: '1', minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '14px', color: colors.mutedForeground }}>
                Start Date
              </label>
              <input
                type="date"
                value={customDateRange.startDate}
                onChange={(e) => setCustomDateRange({ ...customDateRange, startDate: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  border: `1px solid ${colors.border}`,
                  fontSize: '14px',
                  backgroundColor: colors.secondary,
                  color: colors.foreground
                }}
              />
            </div>
            <div style={{ flex: '1', minWidth: '200px' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '14px', color: colors.mutedForeground }}>
                End Date
              </label>
              <input
                type="date"
                value={customDateRange.endDate}
                onChange={(e) => setCustomDateRange({ ...customDateRange, endDate: e.target.value })}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  border: `1px solid ${colors.border}`,
                  fontSize: '14px',
                  backgroundColor: colors.secondary,
                  color: colors.foreground
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => {
                  if (!customDateRange.startDate && !customDateRange.endDate) {
                    setError('Please select at least one date');
                    return;
                  }
                  if (customDateRange.startDate && customDateRange.endDate &&
                    customDateRange.startDate > customDateRange.endDate) {
                    setError('Start date must be before end date');
                    return;
                  }
                  setDateFilter('custom');
                  setShowCustomDatePicker(false);
                  fetchBankStatementsList(null, bankFilter, customDateRange);
                }}
                style={{
                  padding: '0.75rem 1.5rem',
                  borderRadius: '0.5rem',
                  backgroundColor: primary,
                  color: colors.primaryForeground,
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'all 0.3s',
                }}
              >
                Apply
              </button>
              <button
                onClick={() => {
                  setShowCustomDatePicker(false);
                  setCustomDateRange({ startDate: '', endDate: '' });
                }}
                style={{
                  padding: '0.75rem 1.5rem',
                  borderRadius: '0.5rem',
                  backgroundColor: colors.secondary,
                  color: colors.foreground,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                  fontWeight: '500',
                  transition: 'all 0.3s',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {loadingBankStatementsList && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <FaCog className="spin" style={{
            fontSize: '2rem',
            color: primary,
          }} />
          <p style={{ marginTop: '0.5rem', color: colors.mutedForeground }}>
            Loading bank statements...
          </p>
        </div>
      )}
    </div>
  );
};

export default BankStatementFilters;
