import { colors } from '../../styles/colors';
import { FaCog } from 'react-icons/fa';

const CheckFilters = ({
  searchQuery,
  setSearchQuery,
  handleSearchChecks,
  dateFilter,
  setDateFilter,
  fetchChecksList,
  bankFilter,
  totalRecords,
  loadingChecksList,
  showCustomDatePicker,
  setShowCustomDatePicker,
  customDateRange,
  setCustomDateRange,
  setError,
  availableBanks,
  bankFilter: bankFilterProp,
  setBankFilter,
  allChecksData,
  setChecksList,
  loadCheckData,
  checksList,
  selectedCheckId,
  setSelectedCheckId,
  primary
}) => {
  return (
    <>
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
          Search by Payer Name:
        </label>
        <input
          type="text"
          placeholder="Search checks by payer name..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            handleSearchChecks(e.target.value);
          }}
          style={{
            width: '100%',
            padding: '0.75rem',
            borderRadius: '0.5rem',
            backgroundColor: colors.secondary,
            color: colors.foreground,
            border: `1px solid ${colors.border}`,
            fontSize: '1rem',
          }}
        />
      </div>

      {/* Date Filter Section */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.75rem', fontWeight: '500' }}>
          Filter by Created Date {totalRecords > 0 && <span style={{ color: colors.mutedForeground, fontWeight: '400', fontSize: '0.9rem' }}>({totalRecords} total records)</span>}
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem' }}>
          <button
            onClick={() => fetchChecksList(null, bankFilterProp)}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: dateFilter === null ? primary : colors.secondary,
              color: dateFilter === null ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: dateFilter === null ? '600' : '500',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => !loadingChecksList && dateFilter !== null && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingChecksList && dateFilter !== null && (e.target.style.backgroundColor = colors.secondary)}
          >
            All Records
          </button>
          <button
            onClick={() => fetchChecksList('last_30', bankFilterProp)}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: dateFilter === 'last_30' ? primary : colors.secondary,
              color: dateFilter === 'last_30' ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: dateFilter === 'last_30' ? '600' : '500',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Last 30
          </button>
          <button
            onClick={() => fetchChecksList('last_60', bankFilterProp)}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: dateFilter === 'last_60' ? primary : colors.secondary,
              color: dateFilter === 'last_60' ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: dateFilter === 'last_60' ? '600' : '500',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Last 60
          </button>
          <button
            onClick={() => fetchChecksList('last_90', bankFilterProp)}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: dateFilter === 'last_90' ? primary : colors.secondary,
              color: dateFilter === 'last_90' ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: dateFilter === 'last_90' ? '600' : '500',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Last 90
          </button>
          <button
            onClick={() => fetchChecksList('older', bankFilterProp)}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: dateFilter === 'older' ? primary : colors.secondary,
              color: dateFilter === 'older' ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: dateFilter === 'older' ? '600' : '500',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Older
          </button>
          <button
            onClick={() => setShowCustomDatePicker(!showCustomDatePicker)}
            style={{
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: dateFilter === 'custom' ? primary : colors.secondary,
              color: dateFilter === 'custom' ? colors.primaryForeground : colors.foreground,
              border: `1px solid ${colors.border}`,
              cursor: 'pointer',
              fontWeight: dateFilter === 'custom' ? '600' : '500',
              transition: 'all 0.3s',
            }}
            onMouseEnter={(e) => !loadingChecksList && dateFilter !== 'custom' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingChecksList && dateFilter !== 'custom' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Custom Range
          </button>
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
                    fetchChecksList(null, bankFilterProp, customDateRange);
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
                    fontWeight: '600',
                    transition: 'all 0.3s',
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bank Filter Section */}
      {availableBanks.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
            Filter by Bank:
          </label>
          <select
            value={bankFilterProp || ''}
            onChange={(e) => {
              const selectedBank = e.target.value || null;
              setBankFilter(selectedBank);
              if (selectedBank) {
                const filtered = allChecksData.filter(check => check.bank_name === selectedBank);
                setChecksList(filtered);
                if (filtered.length > 0) {
                  loadCheckData(filtered);
                } else {
                  setError('No checks found for this bank');
                }
              } else {
                setChecksList(allChecksData);
                if (allChecksData.length > 0) {
                  loadCheckData(allChecksData);
                } else {
                  fetchChecksList(dateFilter);
                }
              }
            }}
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '0.5rem',
              backgroundColor: colors.secondary,
              color: colors.foreground,
              border: `1px solid ${colors.border}`,
              fontSize: '1rem',
              cursor: 'pointer',
              appearance: 'none',
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='${encodeURIComponent(colors.foreground)}' d='M6 9L1 4h10z'/%3E%3C/svg%3E")`,
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'right 0.75rem center',
              paddingRight: '2.5rem',
            }}
          >
            <option value="">All Banks</option>
            {availableBanks.map((bank) => (
              <option key={bank} value={bank}>
                {bank}
              </option>
            ))}
          </select>
        </div>
      )}

      {loadingChecksList ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <FaCog className="spin" style={{ fontSize: '2rem', color: primary }} />
          <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>Loading checks...</p>
        </div>
      ) : checksList.length > 0 ? (
        <div style={{
          backgroundColor: colors.secondary,
          borderRadius: '0.5rem',
          border: `1px solid ${colors.border}`,
          maxHeight: '400px',
          overflowY: 'auto',
          marginBottom: '1rem',
        }}>
          {checksList.map((check) => (
            <div
              key={check.check_id}
              onClick={() => {
                setSelectedCheckId(check.check_id);
                loadCheckData(checksList.filter(c => c.check_id === check.check_id));
              }}
              style={{
                padding: '1rem',
                borderBottom: `1px solid ${colors.border}`,
                cursor: 'pointer',
                transition: 'background-color 0.3s',
                backgroundColor: selectedCheckId === check.check_id ? colors.muted : 'transparent',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = colors.muted)}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = selectedCheckId === check.check_id ? colors.muted : 'transparent')}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ color: colors.foreground, fontWeight: '600', margin: '0 0 0.25rem 0' }}>
                    {check.payer_name || 'Unknown Payer'}
                  </p>
                  <p style={{ color: colors.mutedForeground, fontSize: '0.875rem', margin: '0' }}>
                    Check #{check.check_number || 'N/A'} • ${check.amount || 'N/A'}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    backgroundColor: check.fraud_risk_score > 0.5 ? `${primary}20` : `${colors.status.success}20`,
                    color: check.fraud_risk_score > 0.5 ? primary : colors.status.success,
                    padding: '0.25rem 0.75rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                  }}>
                    {((check.fraud_risk_score || 0) * 100).toFixed(0)}% Risk
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{
          backgroundColor: colors.muted,
          padding: '2rem',
          borderRadius: '0.5rem',
          textAlign: 'center',
          color: colors.mutedForeground,
          marginBottom: '1rem',
        }}>
          <p>No checks found in database</p>
        </div>
      )}
    </>
  );
};

export default CheckFilters;
