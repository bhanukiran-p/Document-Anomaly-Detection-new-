import { colors } from '../../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Sector,
  ComposedChart, ScatterChart, Scatter, ZAxis
} from 'recharts';

const BankStatementCharts = ({ csvData, bankFilter, primary, activePieIndex, setActivePieIndex, activeBarIndex, setActiveBarIndex }) => {
  if (!csvData) return null;

  const chartBoxStyle = {
    backgroundColor: colors.card,
    padding: '24px',
    borderRadius: '12px',
    border: `1px solid ${colors.border}`,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
  };

  const chartTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: colors.foreground,
    marginBottom: '20px',
    paddingBottom: '12px',
    borderBottom: `2px solid ${colors.border}`,
  };

  const colorMap = {
    'APPROVE': colors.status.success || '#4CAF50',
    'REJECT': primary,
    'ESCALATE': colors.status.warning || '#FFA726'
  };

  const COMPLEMENTARY_COLORS = [
    '#E53935', '#14B8A6', '#F97316', '#8B5CF6',
    '#06B6D4', '#F59E0B', '#EC4899', '#10B981'
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '20px' }}>
      {/* AI Recommendation Breakdown */}
      {csvData.recommendationData && csvData.recommendationData.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>AI Decision Breakdown</h3>
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={csvData.recommendationData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                label={false}
                dataKey="value"
                stroke={colors.card}
                strokeWidth={3}
                startAngle={90}
                endAngle={-270}
                activeIndex={activePieIndex}
                activeShape={(props) => {
                  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props;
                  return (
                    <Sector
                      cx={cx}
                      cy={cy}
                      innerRadius={innerRadius}
                      outerRadius={outerRadius + 5}
                      startAngle={startAngle}
                      endAngle={endAngle}
                      fill={fill}
                      opacity={0.9}
                    />
                  );
                }}
              >
                {csvData.recommendationData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={colorMap[entry.name] || primary}
                    onMouseEnter={() => setActivePieIndex(index)}
                    onMouseLeave={() => setActivePieIndex(null)}
                  />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0];
                    const total = csvData.recommendationData.reduce((sum, item) => sum + item.value, 0);
                    const percentage = total > 0 ? ((data.value / total) * 100).toFixed(1) : 0;
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
                          <span style={{ fontWeight: '600' }}>Count:</span> {data.value}
                        </p>
                        <p style={{ margin: '4px 0', color: data.color }}>
                          <span style={{ fontWeight: '600' }}>Percentage:</span> {percentage}%
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
                cursor={{ fill: 'transparent' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
            {csvData.recommendationData.map((entry, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: colorMap[entry.name] || primary
                }} />
                <span style={{ fontSize: '0.875rem', color: colors.foreground }}>
                  {entry.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Score Distribution by Range */}
      {csvData.riskDistribution && csvData.riskDistribution.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Risk Score Distribution by Range</h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={csvData.riskDistribution} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
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
                          {data.range}
                        </p>
                        <p style={{ margin: '4px 0', color: primary }}>
                          <span style={{ fontWeight: '600' }}>Count:</span> {data.count}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
                cursor={{ fill: 'transparent' }}
              />
              <Bar dataKey="count" fill="url(#riskGradient)" radius={[8, 8, 0, 0]} name="Bank Statement Count">
                {csvData.riskDistribution.map((entry, index) => {
                  const isActive = activeBarIndex === index;
                  return (
                    <Cell
                      key={`risk-cell-${index}`}
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
      )}

      {/* Risk Level by Bank (Combined Bar + Line) */}
      {!bankFilter && csvData.riskByBankData && csvData.riskByBankData.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Risk Level by Bank</h3>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart
              data={csvData.riskByBankData}
              margin={{ top: 10, right: 30, left: 10, bottom: 60 }}
              onMouseLeave={() => setActiveBarIndex(null)}
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
                label={{ value: 'Statement Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
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
                name="Statement Count"
              >
                {csvData.riskByBankData.map((entry, index) => {
                  const isActive = activeBarIndex === index;
                  return (
                    <Cell
                      key={`count-cell-${index}`}
                      fill={isActive ? "url(#countGradientHover)" : "url(#countGradient)"}
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

      {/* Fraud Type Distribution - Scatter Plot */}
      {csvData.fraudTypeData && csvData.fraudTypeData.length > 0 && (
        <div style={chartBoxStyle}>
          <h3 style={chartTitleStyle}>Fraud Type Distribution</h3>
          {(() => {
            const total = csvData.fraudTypeData.reduce((sum, item) => sum + item.value, 0);
            const scatterData = csvData.fraudTypeData.map((entry, index) => {
              const percentage = total > 0 ? ((entry.value / total) * 100) : 0;
              return {
                name: entry.name,
                count: entry.value,
                percentage: parseFloat(percentage.toFixed(1)),
                originalPercentage: parseFloat(percentage.toFixed(1)),
                size: entry.value,
                color: COMPLEMENTARY_COLORS[index % COMPLEMENTARY_COLORS.length],
                index: index
              };
            });

            const processedData = scatterData.map((entry, index) => {
              const duplicates = scatterData.filter((e, i) =>
                i !== index &&
                e.count === entry.count &&
                Math.abs(e.percentage - entry.percentage) < 0.1
              );
              const duplicateIndex = scatterData.slice(0, index).filter((e) =>
                e.count === entry.count &&
                Math.abs(e.percentage - entry.percentage) < 0.1
              ).length;
              const jitterRadius = 2;
              const angle = (duplicateIndex * (2 * Math.PI)) / (duplicates.length + 1);
              const jitterY = duplicateIndex > 0 ? Math.sin(angle) * jitterRadius : 0;

              return {
                ...entry,
                percentage: entry.originalPercentage,
                count: entry.count + jitterY
              };
            });

            const originalPercentages = scatterData.map(e => e.originalPercentage);
            const minPercentage = Math.min(...originalPercentages);
            const maxPercentage = Math.max(...originalPercentages);

            return (
              <>
                <ResponsiveContainer width="100%" height={400}>
                  <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                    <XAxis
                      type="number"
                      dataKey="percentage"
                      name="Percentage"
                      domain={[Math.max(0, minPercentage - 2), maxPercentage + 2]}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      tickFormatter={(value) => `${value.toFixed(1)}%`}
                      tickCount={8}
                      allowDecimals={true}
                      stroke={colors.border}
                      label={{ value: 'Percentage (%)', position: 'insideBottom', offset: -5, fill: colors.foreground, fontSize: 12 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="count"
                      name="Count"
                      domain={[0, 'dataMax + 5']}
                      tick={{ fill: colors.foreground, fontSize: 12 }}
                      stroke={colors.border}
                      label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground, fontSize: 12 }}
                    />
                    <ZAxis
                      type="number"
                      dataKey="size"
                      range={[50, 300]}
                      name="Size"
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div style={{
                              backgroundColor: colors.card,
                              border: `2px solid ${primary}`,
                              borderRadius: '8px',
                              padding: '12px',
                              boxShadow: `0 4px 20px rgba(0, 0, 0, 0.8)`,
                              color: colors.foreground
                            }}>
                              <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '8px', borderBottom: `1px solid ${colors.border}`, paddingBottom: '4px' }}>
                                {data.name}
                              </div>
                              <div style={{ fontSize: '13px', marginTop: '4px' }}>
                                <span style={{ color: primary, fontWeight: 'bold' }}>Count:</span> {data.count}
                              </div>
                              <div style={{ fontSize: '13px', marginTop: '4px' }}>
                                <span style={{ color: primary, fontWeight: 'bold' }}>Percentage:</span> {data.originalPercentage.toFixed(1)}%
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter name="Fraud Types" data={processedData} fill={primary}>
                      {processedData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '1rem',
                  marginTop: '1rem',
                  padding: '1rem',
                  backgroundColor: colors.card,
                  borderRadius: '8px',
                  border: `1px solid ${colors.border}`
                }}>
                  {scatterData.map((entry, index) => (
                    <div
                      key={`legend-${index}`}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.75rem',
                        padding: '0.5rem',
                        borderRadius: '6px',
                        transition: 'all 0.2s ease',
                        cursor: 'pointer'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = colors.secondary;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <div
                        style={{
                          width: '14px',
                          height: '14px',
                          borderRadius: '50%',
                          backgroundColor: entry.color,
                          border: `2px solid ${colors.border}`,
                          flexShrink: 0,
                          marginTop: '2px'
                        }}
                      />
                      <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.25rem',
                        flex: 1,
                        minWidth: 0
                      }}>
                        <span style={{
                          color: colors.foreground,
                          fontSize: '13px',
                          fontWeight: '600',
                          lineHeight: '1.4',
                          wordBreak: 'break-word'
                        }}>
                          {entry.name}
                        </span>
                        <span style={{
                          color: colors.mutedForeground,
                          fontSize: '11px',
                          fontWeight: '500',
                          lineHeight: '1.4'
                        }}>
                          {entry.count} cases ({entry.percentage.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default BankStatementCharts;
