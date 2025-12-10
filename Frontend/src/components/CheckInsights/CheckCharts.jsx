import { colors } from '../../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Sector,
  ComposedChart
} from 'recharts';

const CheckCharts = ({ csvData, bankFilter, primary, COLORS, activePieIndex, setActivePieIndex, activeBarIndex, setActiveBarIndex, activeBankBarIndex, setActiveBankBarIndex }) => {
  if (!csvData) return null;

  const chartsContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '20px',
    marginTop: '2rem'
  };

  const chartBoxStyle = {
    backgroundColor: colors.card,
    padding: '24px',
    borderRadius: '12px',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    transition: 'all 0.3s ease',
  };

  const chartTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: colors.foreground,
    marginBottom: '20px',
    paddingBottom: '12px',
    borderBottom: `2px solid ${colors.border}`,
  };

  return (
    <div style={chartsContainerStyle}>
      {/* Row 1: Risk Score Distribution & AI Recommendation Breakdown */}
      <div style={chartBoxStyle}>
        <h3 style={chartTitleStyle}>Risk Score Distribution by Range</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={csvData.riskDistribution}
            margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
            onMouseLeave={() => setActiveBarIndex(null)}
          >
            <defs>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={primary} stopOpacity={1} />
                <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
              </linearGradient>
              <linearGradient id="riskGradientHover" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={primary} stopOpacity={1} />
                <stop offset="100%" stopColor={primary} stopOpacity={0.9} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
            <XAxis
              dataKey="range"
              tick={{ fill: colors.foreground, fontSize: 12 }}
              stroke={colors.border}
            />
            <YAxis
              tick={{ fill: colors.foreground, fontSize: 12 }}
              stroke={colors.border}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0];
                  return (
                    <div style={{
                      backgroundColor: colors.card,
                      border: `1px solid ${colors.border}`,
                      borderRadius: '8px',
                      padding: '12px',
                      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                    }}>
                      <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                        {data.payload.range}
                      </p>
                      <p style={{ margin: '4px 0', color: primary }}>
                        <span style={{ fontWeight: '600' }}>Count:</span> {data.value}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
              cursor={{ fill: 'transparent' }}
            />
            <Bar
              dataKey="count"
              fill="url(#riskGradient)"
              radius={[8, 8, 0, 0]}
            >
              {csvData.riskDistribution.map((entry, index) => {
                const isActive = activeBarIndex === index;
                return (
                  <Cell
                    key={`cell-${index}`}
                    fill={isActive ? "url(#riskGradientHover)" : "url(#riskGradient)"}
                    onMouseEnter={() => setActiveBarIndex(index)}
                    onMouseLeave={() => setActiveBarIndex(null)}
                    style={{
                      cursor: 'pointer',
                      transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                      filter: isActive ? 'brightness(1.1)' : 'brightness(1)'
                    }}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={chartBoxStyle}>
        <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '320px' }}>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart
              onMouseLeave={() => setActivePieIndex(null)}
            >
              <Pie
                data={csvData.recommendationData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={false}
                outerRadius={120}
                innerRadius={60}
                fill="#8884d8"
                dataKey="value"
                stroke={colors.card}
                strokeWidth={3}
                startAngle={90}
                endAngle={-270}
                activeIndex={activePieIndex}
                activeShape={(props) => {
                  const {
                    cx, cy, innerRadius, outerRadius, startAngle, endAngle,
                    fill
                  } = props;
                  return (
                    <g>
                      <Sector
                        cx={cx}
                        cy={cy}
                        innerRadius={innerRadius - 5}
                        outerRadius={outerRadius + 20}
                        startAngle={startAngle}
                        endAngle={endAngle}
                        fill={fill}
                        stroke={colors.card}
                        strokeWidth={3}
                      />
                    </g>
                  );
                }}
                onMouseEnter={(_, index) => setActivePieIndex(index)}
                onMouseLeave={() => setActivePieIndex(null)}
              >
                {csvData.recommendationData.map((entry, index) => {
                  const colorMap = {
                    'APPROVE': colors.status.success || '#4CAF50',
                    'REJECT': primary,
                    'ESCALATE': colors.status.warning || '#FFA726'
                  };
                  const baseColor = colorMap[entry.name] || COLORS[index % COLORS.length];
                  const isActive = activePieIndex === index;

                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={baseColor}
                      style={{
                        filter: isActive ? 'brightness(1.2)' : 'brightness(1)',
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        cursor: 'pointer'
                      }}
                    />
                  );
                })}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0];
                    const total = csvData.recommendationData.reduce((sum, item) => sum + item.value, 0);
                    const percentage = total > 0 ? ((data.payload.value / total) * 100).toFixed(2) : 0;
                    return (
                      <div style={{
                        backgroundColor: colors.card,
                        border: `1px solid ${colors.border}`,
                        borderRadius: '8px',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                      }}>
                        <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                          {data.name}
                        </p>
                        <p style={{ margin: '4px 0', color: data.color }}>
                          <span style={{ fontWeight: '600' }}>Count:</span> {data.payload.value}
                        </p>
                        <p style={{ margin: '4px 0', color: data.color }}>
                          <span style={{ fontWeight: '600' }}>Percentage:</span> {percentage}%
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend below the chart */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '2rem',
          marginTop: '1.5rem',
          padding: '1rem',
          flexWrap: 'wrap'
        }}>
          {csvData.recommendationData.map((entry, index) => {
            const colorMap = {
              'APPROVE': colors.status.success || '#4CAF50',
              'REJECT': primary,
              'ESCALATE': colors.status.warning || '#FFA726'
            };
            const total = csvData.recommendationData.reduce((sum, item) => sum + item.value, 0);
            const percentage = total > 0 ? ((entry.value / total) * 100).toFixed(2) : 0;

            return (
              <div
                key={`legend-${index}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem'
                }}
              >
                <div
                  style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    backgroundColor: colorMap[entry.name] || primary,
                    flexShrink: 0,
                    border: `2px solid ${colors.card}`
                  }}
                />
                <span style={{
                  color: colors.foreground,
                  fontSize: '14px',
                  fontWeight: '500'
                }}>
                  {entry.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Row 2: Risk by Bank (Combined Bar + Line) & Top High-Risk Payers */}
      {!bankFilter && csvData.riskByBankData && csvData.riskByBankData.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Risk Level by Bank</h3>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart
              data={csvData.riskByBankData.map(bank => ({
                ...bank,
                displayName: (() => {
                  const name = bank.name.toUpperCase();
                  if (name.includes('BANK OF AMERICA') || name.includes('BOFA')) return 'BOFA';
                  if (name.includes('CHASE') || name.includes('JPM')) return 'JPMC';
                  if (name.includes('WELLS FARGO') || name.includes('WELLS')) return 'WF';
                  if (name.includes('CITIBANK') || name.includes('CITI')) return 'CITI';
                  if (name.includes('US BANK')) return 'USB';
                  if (name.includes('ALLY')) return 'ALLY';
                  return bank.name.length > 10 ? bank.name.substring(0, 10) + '...' : bank.name;
                })()
              }))}
              margin={{ top: 10, right: 30, left: 10, bottom: 60 }}
              onMouseLeave={() => setActiveBankBarIndex({ bankIndex: null, series: null })}
            >
              <defs>
                <linearGradient id="countGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colors.status.success || '#10b981'} stopOpacity={1} />
                  <stop offset="100%" stopColor={colors.status.success || '#10b981'} stopOpacity={0.7} />
                </linearGradient>
                <linearGradient id="countGradientHover" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colors.status.success || '#10b981'} stopOpacity={1} />
                  <stop offset="100%" stopColor={colors.status.success || '#10b981'} stopOpacity={0.9} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
              <XAxis
                dataKey="displayName"
                tick={{ fill: colors.foreground, fontSize: 11 }}
                stroke={colors.border}
                angle={-45}
                textAnchor="end"
                height={80}
                interval={0}
              />
              <YAxis
                yAxisId="left"
                tick={{ fill: colors.foreground, fontSize: 12 }}
                stroke={colors.border}
                label={{ value: 'Check Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                domain={[0, 100]}
                tick={{ fill: colors.foreground, fontSize: 12 }}
                stroke={colors.border}
                label={{ value: 'Avg Risk Score (%)', angle: 90, position: 'insideRight', fill: colors.foreground }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div style={{
                        backgroundColor: colors.card,
                        border: `1px solid ${colors.border}`,
                        borderRadius: '8px',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                      }}>
                        <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                          {data.name}
                        </p>
                        {payload.map((entry, index) => (
                          <p key={index} style={{ margin: '4px 0', color: entry.color }}>
                            <span style={{ fontWeight: '600' }}>{entry.name}:</span> {entry.name === 'Avg Risk Score (%)' ? `${entry.value}%` : entry.value}
                          </p>
                        ))}
                      </div>
                    );
                  }
                  return null;
                }}
                cursor={{ fill: 'transparent' }}
              />
              <Legend />
              <Bar
                yAxisId="left"
                dataKey="count"
                fill="url(#countGradient)"
                name="Check Count"
              >
                {csvData.riskByBankData.map((entry, index) => {
                  const isActive = activeBankBarIndex.bankIndex === index && activeBankBarIndex.series === 'count';
                  return (
                    <Cell
                      key={`count-cell-${index}`}
                      fill={isActive ? "url(#countGradientHover)" : "url(#countGradient)"}
                      onMouseEnter={() => setActiveBankBarIndex({ bankIndex: index, series: 'count' })}
                      onMouseLeave={() => setActiveBankBarIndex({ bankIndex: null, series: null })}
                      style={{
                        cursor: 'pointer',
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        filter: isActive ? 'brightness(1.1)' : 'brightness(1)'
                      }}
                    />
                  );
                })}
              </Bar>
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avgRisk"
                stroke={primary}
                strokeWidth={3}
                dot={{ fill: primary, r: 5 }}
                activeDot={{ r: 7 }}
                name="Avg Risk Score (%)"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {csvData.topHighRiskPayers && csvData.topHighRiskPayers.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Top High-Risk Payers</h3>
          <ResponsiveContainer width="100%" height={Math.max(320, csvData.topHighRiskPayers.length * 40)}>
            <BarChart
              data={csvData.topHighRiskPayers}
              layout="vertical"
              margin={{ left: 120, right: 60, top: 10, bottom: 10 }}
            >
              <defs>
                <linearGradient id="heatGradientHigh" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={1} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0.8} />
                </linearGradient>
                <linearGradient id="heatGradientMedium" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#f59e0b" stopOpacity={1} />
                  <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.8} />
                </linearGradient>
                <linearGradient id="heatGradientLow" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#eab308" stopOpacity={1} />
                  <stop offset="100%" stopColor="#eab308" stopOpacity={0.8} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} horizontal={false} />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fill: colors.foreground, fontSize: 11 }}
                stroke={colors.border}
                label={{ value: 'Risk Score (%)', position: 'insideBottom', offset: -5, style: { textAnchor: 'middle', fill: colors.foreground } }}
              />
              <YAxis
                dataKey="name"
                type="category"
                stroke={colors.border}
                width={110}
                tick={{ fill: colors.foreground, fontSize: 11 }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div style={{
                        backgroundColor: colors.card,
                        border: `1px solid ${colors.border}`,
                        borderRadius: '8px',
                        padding: '12px',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                      }}>
                        <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
                          {data.name}
                        </p>
                        <p style={{ margin: '4px 0', color: primary }}>
                          <span style={{ fontWeight: '600' }}>Avg Risk:</span> {data.avgRisk}%
                        </p>
                        <p style={{ margin: '4px 0', color: colors.mutedForeground }}>
                          <span style={{ fontWeight: '600' }}>Checks:</span> {data.count}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
                cursor={{ fill: 'transparent' }}
              />
              <Bar
                dataKey="avgRisk"
                barSize={12}
                radius={[0, 4, 4, 0]}
                label={({ value, x, y, width }) => {
                  return (
                    <text
                      x={x + width + 5}
                      y={y + 6}
                      fill={colors.foreground}
                      fontSize={12}
                      fontWeight="600"
                      textAnchor="start"
                    >
                      {parseFloat(value).toFixed(0)}%
                    </text>
                  );
                }}
              >
                {csvData.topHighRiskPayers.map((entry, index) => {
                  const risk = parseFloat(entry.avgRisk);
                  let gradientId = 'heatGradientLow';
                  if (risk >= 75) gradientId = 'heatGradientHigh';
                  else if (risk >= 50) gradientId = 'heatGradientMedium';

                  return (
                    <Cell
                      key={`heat-cell-${index}`}
                      fill={`url(#${gradientId})`}
                    />
                  );
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Row 3: Payees with Highest Fraud Incidents (Bullet Chart) & Fraud Trend Over Time */}
      {csvData.topFraudIncidentPayees && csvData.topFraudIncidentPayees.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Payees with Highest Fraud Incidents</h3>
          <div style={{ padding: '1rem' }}>
            {csvData.topFraudIncidentPayees.map((payee, index) => {
              const maxCount = Math.max(...csvData.topFraudIncidentPayees.map(p => p.fraudCount));
              const barWidth = (payee.fraudCount / maxCount) * 100;
              let barColor = '#FFB59E';
              if (payee.fraudCount >= 60) barColor = '#FF6B5A';
              else if (payee.fraudCount > 20) barColor = '#FF8A75';

              return (
                <div
                  key={`payee-bullet-${index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '1rem',
                    gap: '1rem'
                  }}
                >
                  <div style={{
                    minWidth: '180px',
                    fontSize: '13px',
                    fontWeight: '500',
                    color: colors.foreground,
                    textAlign: 'right'
                  }}>
                    {payee.name.length > 20 ? payee.name.substring(0, 20) + '...' : payee.name}
                  </div>
                  <div style={{
                    flex: 1,
                    position: 'relative',
                    height: '24px',
                    backgroundColor: colors.secondary,
                    borderRadius: '4px',
                    overflow: 'hidden',
                    border: `1px solid ${colors.border}`
                  }}>
                    <div style={{
                      width: `${barWidth}%`,
                      height: '100%',
                      backgroundColor: barColor,
                      borderRadius: '4px',
                      transition: 'width 0.3s ease'
                    }} />
                  </div>
                  <div style={{
                    minWidth: '40px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: colors.foreground,
                    textAlign: 'left'
                  }}>
                    {payee.fraudCount}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {csvData.fraudTrendData && csvData.fraudTrendData.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Fraud Trend Over Time</h3>
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
    </div>
  );
};

export default CheckCharts;
