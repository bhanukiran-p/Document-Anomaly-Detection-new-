import { colors } from '../../styles/colors';
import { FaCog } from 'react-icons/fa';

const MoneyOrderFilters = ({
  searchQuery,
  setSearchQuery,
  handleSearchMoneyOrders,
  availableIssuers,
  issuerFilter,
  setIssuerFilter,
  allMoneyOrdersData,
  setMoneyOrdersList,
  loadMoneyOrderData,
  dateFilter,
  setDateFilter,
  fetchMoneyOrdersList,
  totalRecords,
  loadingMoneyOrdersList,
  showCustomDatePicker,
  setShowCustomDatePicker,
  customDateRange,
  setCustomDateRange,
  setError,
  moneyOrdersList,
  selectedMoneyOrderId,
  setSelectedMoneyOrderId,
  primary
}) => {
  return (
    <>
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
          Search by Purchaser Name:
        </label>
        <input
          type="text"
          placeholder="Search money orders by purchaser name..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            handleSearchMoneyOrders(e.target.value);
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

      {/* Issuer Filter Section */}
      {availableIssuers.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '500' }}>
            Filter by Issuer:
          </label>
          <select
            value={issuerFilter || ''}
            onChange={(e) => {
              const selectedIssuer = e.target.value || null;
              setIssuerFilter(selectedIssuer);
              if (selectedIssuer && selectedIssuer !== '' && selectedIssuer !== 'All Issuers') {
                const normalizedSelected = selectedIssuer.trim();
                const filtered = allMoneyOrdersData.filter(mo => {
                  const moIssuer = (mo.money_order_institute || '').trim();
                  return moIssuer === normalizedSelected;
                });
                setMoneyOrdersList(filtered);
                if (filtered.length > 0) {
                  loadMoneyOrderData(filtered, normalizedSelected);
                } else {
                  setError('No money orders found for this issuer');
                }
              } else {
                fetchMoneyOrdersList(dateFilter, null);
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
            <option value="">All Issuers</option>
            {availableIssuers.map((issuer) => (
              <option key={issuer} value={issuer}>
                {issuer}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Date Filter Section */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', color: colors.foreground, marginBottom: '0.75rem', fontWeight: '500' }}>
          Filter by Created Date {totalRecords > 0 && <span style={{ color: colors.mutedForeground, fontWeight: '400', fontSize: '0.9rem' }}>({totalRecords} total records)</span>}
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem' }}>
          <button
            onClick={() => {
              setDateFilter(null);
              fetchMoneyOrdersList(null, issuerFilter);
            }}
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
            onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== null && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== null && (e.target.style.backgroundColor = colors.secondary)}
          >
            All Records
          </button>
          <button
            onClick={() => {
              setDateFilter('last_30');
              fetchMoneyOrdersList('last_30', issuerFilter);
            }}
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
            onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_30' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Last 30
          </button>
          <button
            onClick={() => {
              setDateFilter('last_60');
              fetchMoneyOrdersList('last_60', issuerFilter);
            }}
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
            onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_60' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Last 60
          </button>
          <button
            onClick={() => {
              setDateFilter('last_90');
              fetchMoneyOrdersList('last_90', issuerFilter);
            }}
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
            onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'last_90' && (e.target.style.backgroundColor = colors.secondary)}
          >
            Last 90
          </button>
          <button
            onClick={() => {
              setDateFilter('older');
              fetchMoneyOrdersList('older', issuerFilter);
            }}
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
            onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'older' && (e.target.style.backgroundColor = colors.secondary)}
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
            onMouseEnter={(e) => !loadingMoneyOrdersList && dateFilter !== 'custom' && (e.target.style.backgroundColor = colors.muted)}
            onMouseLeave={(e) => !loadingMoneyOrdersList && dateFilter !== 'custom' && (e.target.style.backgroundColor = colors.secondary)}
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
                    fetchMoneyOrdersList(null, issuerFilter, customDateRange);
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

      {loadingMoneyOrdersList ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <FaCog className="spin" style={{ fontSize: '2rem', color: primary }} />
          <p style={{ marginTop: '1rem', color: colors.mutedForeground }}>Loading money orders...</p>
        </div>
      ) : moneyOrdersList.length > 0 ? (
        <div style={{
          backgroundColor: colors.secondary,
          borderRadius: '0.5rem',
          border: `1px solid ${colors.border}`,
          maxHeight: '400px',
          overflowY: 'auto',
          marginBottom: '1rem',
        }}>
          {moneyOrdersList.map((mo) => (
            <div
              key={mo.money_order_id}
              onClick={() => {
                setSelectedMoneyOrderId(mo.money_order_id);
                loadMoneyOrderData(moneyOrdersList.filter(m => m.money_order_id === mo.money_order_id));
              }}
              style={{
                padding: '1rem',
                borderBottom: `1px solid ${colors.border}`,
                cursor: 'pointer',
                transition: 'background-color 0.3s',
                backgroundColor: selectedMoneyOrderId === mo.money_order_id ? colors.muted : 'transparent',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = colors.muted)}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = selectedMoneyOrderId === mo.money_order_id ? colors.muted : 'transparent')}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ color: colors.foreground, fontWeight: '600', margin: '0 0 0.25rem 0' }}>
                    {mo.purchaser_name || 'Unknown Purchaser'}
                  </p>
                  <p style={{ color: colors.mutedForeground, fontSize: '0.875rem', margin: '0' }}>
                    MO #{mo.money_order_number || 'N/A'} • ${mo.amount || 'N/A'} • {mo.money_order_institute || 'Unknown Issuer'}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    backgroundColor: mo.fraud_risk_score > 0.5 ? `${primary}20` : `${colors.status.success}20`,
                    color: mo.fraud_risk_score > 0.5 ? primary : colors.status.success,
                    padding: '0.25rem 0.75rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.875rem',
                    fontWeight: '600',
                  }}>
                    {((mo.fraud_risk_score || 0) * 100).toFixed(0)}% Risk
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
          <p>No money orders found in database</p>
        </div>
      )}
    </>
  );
};

export default MoneyOrderFilters;
