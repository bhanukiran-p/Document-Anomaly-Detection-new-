import { colors } from '../../styles/colors';
import { FaRedo } from 'react-icons/fa';

const PaystubFilters = ({
  searchQuery,
  setSearchQuery,
  employerFilter,
  setEmployerFilter,
  availableEmployers,
  dateFilter,
  setDateFilter,
  showCustomDatePicker,
  setShowCustomDatePicker,
  customDateRange,
  setCustomDateRange,
  setError,
  fraudTypeFilter,
  setFraudTypeFilter,
  availableFraudTypes,
  filteredDataLength,
  totalRecords,
  primary
}) => {
  const styles = {
    filtersSection: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '12px',
      marginBottom: '24px',
      padding: '16px',
      backgroundColor: colors.card,
      borderRadius: '8px',
      border: `1px solid ${colors.border}`,
    },
    searchInput: {
      padding: '8px 12px',
      borderRadius: '4px',
      border: `1px solid ${colors.border}`,
      fontSize: '14px',
      backgroundColor: colors.secondary,
      color: colors.foreground,
      width: '100%',
    },
    select: {
      padding: '8px 12px',
      borderRadius: '4px',
      border: `1px solid ${colors.border}`,
      fontSize: '14px',
      backgroundColor: colors.secondary,
      color: colors.foreground,
      cursor: 'pointer',
      width: '100%',
    },
    recordCount: {
      fontSize: '13px',
      color: colors.mutedForeground,
      alignSelf: 'center',
      whiteSpace: 'nowrap',
    }
  };

  return (
    <div style={styles.filtersSection}>
      <input
        type="text"
        placeholder="Search by employee name..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        style={styles.searchInput}
      />

      <select
        value={employerFilter || ''}
        onChange={(e) => setEmployerFilter(e.target.value || null)}
        style={styles.select}
      >
        <option value="">All Employers</option>
        {availableEmployers.map(emp => (
          <option key={emp} value={emp}>{emp}</option>
        ))}
      </select>

      <select
        value={dateFilter || ''}
        onChange={(e) => {
          const value = e.target.value || null;
          if (value === 'custom') {
            setShowCustomDatePicker(true);
          } else {
            setShowCustomDatePicker(false);
            setDateFilter(value);
          }
        }}
        style={styles.select}
      >
        <option value="">All Time</option>
        <option value="last_30">Last 30 Days</option>
        <option value="last_60">Last 60 Days</option>
        <option value="last_90">Last 90 Days</option>
        <option value="older">Older</option>
        <option value="custom">Custom Range</option>
      </select>

      {/* Custom Date Range Picker */}
      {showCustomDatePicker && (
        <div style={{
          gridColumn: '1 / -1',
          padding: '16px',
          backgroundColor: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ marginBottom: '12px', fontWeight: '600', color: colors.foreground }}>
            Select Custom Date Range
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div style={{ flex: '1', minWidth: '180px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: colors.mutedForeground }}>
                Start Date
              </label>
              <input
                type="date"
                value={customDateRange.startDate}
                onChange={(e) => setCustomDateRange({ ...customDateRange, startDate: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: `1px solid ${colors.border}`,
                  fontSize: '13px',
                  backgroundColor: colors.secondary,
                  color: colors.foreground
                }}
              />
            </div>
            <div style={{ flex: '1', minWidth: '180px' }}>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: colors.mutedForeground }}>
                End Date
              </label>
              <input
                type="date"
                value={customDateRange.endDate}
                onChange={(e) => setCustomDateRange({ ...customDateRange, endDate: e.target.value })}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: `1px solid ${colors.border}`,
                  fontSize: '13px',
                  backgroundColor: colors.secondary,
                  color: colors.foreground
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
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
                }}
                style={{
                  padding: '8px 20px',
                  borderRadius: '4px',
                  backgroundColor: primary,
                  color: colors.primaryForeground,
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '13px',
                  transition: 'all 0.2s',
                }}
              >
                Apply
              </button>
              <button
                onClick={() => {
                  setShowCustomDatePicker(false);
                  setCustomDateRange({ startDate: '', endDate: '' });
                  setDateFilter(null);
                }}
                style={{
                  padding: '8px 20px',
                  borderRadius: '4px',
                  backgroundColor: colors.secondary,
                  color: colors.foreground,
                  border: `1px solid ${colors.border}`,
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '13px',
                  transition: 'all 0.2s',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {availableFraudTypes.length > 0 && (
        <select
          value={fraudTypeFilter || ''}
          onChange={(e) => setFraudTypeFilter(e.target.value || null)}
          style={styles.select}
        >
          <option value="">All Fraud Types</option>
          {availableFraudTypes.map(fraudType => (
            <option key={fraudType} value={fraudType}>{fraudType}</option>
          ))}
        </select>
      )}

      <button
        onClick={() => {
          setSearchQuery('');
          setEmployerFilter(null);
          setDateFilter(null);
          setFraudTypeFilter(null);
          setCustomDateRange({ startDate: '', endDate: '' });
          setShowCustomDatePicker(false);
        }}
        style={{
          padding: '8px 16px',
          borderRadius: '4px',
          border: `1px solid ${colors.border}`,
          backgroundColor: colors.secondary,
          color: colors.foreground,
          cursor: 'pointer',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.target.style.backgroundColor = colors.muted;
          e.target.style.borderColor = primary;
        }}
        onMouseLeave={(e) => {
          e.target.style.backgroundColor = colors.secondary;
          e.target.style.borderColor = colors.border;
        }}
      >
        <FaRedo /> Reset Filters
      </button>

      <span style={styles.recordCount}>
        Showing {filteredDataLength} of {totalRecords} paystubs
      </span>
    </div>
  );
};

export default PaystubFilters;
