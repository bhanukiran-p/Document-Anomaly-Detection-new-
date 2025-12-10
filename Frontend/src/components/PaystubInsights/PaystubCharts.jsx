import { colors } from '../../styles/colors';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area,
  ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
  ScatterChart, Scatter, ZAxis, Sector
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: '8px',
        padding: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
      }}>
        <p style={{ margin: '0 0 8px 0', fontWeight: '600', color: colors.foreground }}>
          {label}
        </p>
        {payload.map((entry, index) => (
          <p key={index} style={{ margin: '4px 0', color: entry.color }}>
            <span style={{ fontWeight: '600' }}>{entry.name || entry.dataKey}:</span> {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const PaystubCharts = ({ csvData, primary, COLORS, activePieIndex, setActivePieIndex, activeBarIndex, setActiveBarIndex }) => {
  if (!csvData) return null;

  const styles = {
    chartsContainer: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
      gap: '20px'
    },
    chartBox: {
      backgroundColor: colors.card,
      padding: '24px',
      borderRadius: '12px',
      border: `1px solid ${colors.border}`,
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
      transition: 'all 0.3s ease',
    },
    chartTitle: {
      fontSize: '18px',
      fontWeight: '600',
      color: colors.foreground,
      marginBottom: '20px',
      paddingBottom: '12px',
      borderBottom: `2px solid ${colors.border}`,
    }
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
    <div style={styles.chartsContainer}>
      {/* Show standard charts only when NO fraud type filter is active */}
      {!csvData.isFraudTypeFiltered && (
        <>
          {/* Risk Distribution */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Fraud Risk Distribution</h3>
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

          {/* AI Recommendation Distribution */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>AI Recommendation Breakdown</h3>
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
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '2rem',
              marginTop: '1.5rem',
              padding: '1rem',
              flexWrap: 'wrap'
            }}>
              {csvData.recommendationData.map((entry, index) => {
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

          {/* Risk by Employer */}
          {!csvData.isSingleEmployerView && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Risk by Employer (Top 10)</h3>
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart
                  data={csvData.riskByEmployerData}
                  margin={{ top: 20, right: 30, left: 30, bottom: 80 }}
                >
                  <defs>
                    <linearGradient id="employerAreaGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={primary} stopOpacity={0.8} />
                      <stop offset="100%" stopColor={primary} stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                    tick={{ fill: colors.foreground, fontSize: 11 }}
                    stroke={colors.border}
                    dx={-5}
                    dy={5}
                  />
                  <YAxis
                    tick={{ fill: colors.foreground, fontSize: 12 }}
                    stroke={colors.border}
                    label={{ value: 'Risk %', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="avgRisk"
                    stroke={primary}
                    strokeWidth={3}
                    fill="url(#employerAreaGradient)"
                    name="Avg Risk %"
                  />
                  <Line
                    type="monotone"
                    dataKey="avgRisk"
                    stroke={primary}
                    strokeWidth={3}
                    dot={{ fill: primary, r: 6, strokeWidth: 2, stroke: colors.card }}
                    activeDot={{ r: 8, strokeWidth: 2, stroke: colors.card }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Risk Level Distribution */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Risk Level Distribution</h3>
            <div style={{ padding: '1rem', minHeight: '280px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: csvData.riskLevelData.length === 3 ? 'repeat(3, 1fr)' : `repeat(${csvData.riskLevelData.length}, 1fr)`,
                gap: '1rem',
                flex: 1,
                alignItems: 'stretch'
              }}>
                {csvData.riskLevelData.map((entry, index) => {
                  const total = csvData.riskLevelData.reduce((sum, item) => sum + item.value, 0);
                  const percentage = total > 0 ? ((entry.value / total) * 100).toFixed(1) : 0;
                  const cardColor = entry.color;

                  return (
                    <div
                      key={`heatmap-cell-${index}`}
                      style={{
                        backgroundColor: cardColor,
                        opacity: 0.9,
                        padding: '1.25rem',
                        borderRadius: '8px',
                        border: `2px solid ${cardColor}`,
                        textAlign: 'center',
                        transition: 'transform 0.2s',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        minHeight: '180px'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.02)';
                        e.currentTarget.style.opacity = '1';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.opacity = '0.9';
                      }}
                    >
                      <div style={{ fontSize: '2rem', fontWeight: 'bold', color: colors.foreground, marginBottom: '0.75rem' }}>
                        {entry.value}
                      </div>
                      <div style={{ fontSize: '0.85rem', color: colors.foreground, marginBottom: '0.5rem', fontWeight: '600', whiteSpace: 'nowrap' }}>
                        {entry.name}
                      </div>
                      <div style={{ fontSize: '1rem', color: colors.foreground, fontWeight: '600' }}>
                        {percentage}%
                      </div>
                    </div>
                  );
                })}
              </div>
              {csvData.riskLevelData.length > 0 && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem 1rem',
                  backgroundColor: colors.secondary,
                  borderRadius: '8px',
                  border: `1px solid ${colors.border}`
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.9rem',
                    color: colors.foreground
                  }}>
                    <span>Total Paystubs:</span>
                    <span style={{ fontWeight: 'bold', color: primary }}>
                      {csvData.riskLevelData.reduce((sum, item) => sum + item.value, 0)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Top High-Risk Employees */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Top High-Risk Employees (≥50%)</h3>
            {csvData.topHighRiskEmployees && csvData.topHighRiskEmployees.length > 0 ? (
              <ResponsiveContainer width="100%" height={Math.max(550, csvData.topHighRiskEmployees.length * 45)}>
                <ComposedChart
                  data={csvData.topHighRiskEmployees.map(emp => ({
                    ...emp,
                    lowZone: 50,
                    mediumZone: 25,
                    highZone: 25
                  }))}
                  layout="vertical"
                  margin={{ top: 20, right: 20, left: 40, bottom: 20 }}
                >
                  <defs>
                    <linearGradient id="bulletGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor={primary} stopOpacity={0.9} />
                      <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.2} horizontal={false} />
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    tick={{ fill: colors.foreground, fontSize: 11 }}
                    stroke={colors.border}
                    label={{ value: 'Risk %', position: 'insideBottom', offset: -5, fill: colors.foreground }}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={50}
                    tick={{ fill: colors.foreground, fontSize: 11 }}
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
                              {data.name}
                            </p>
                            <p style={{ margin: '4px 0', color: primary }}>
                              <span style={{ fontWeight: '600' }}>Risk:</span> {data.avgRisk.toFixed(1)}%
                            </p>
                            <p style={{ margin: '4px 0', color: colors.mutedForeground, fontSize: '0.85rem' }}>
                              {data.avgRisk >= 75 ? '🔴 High Risk' : data.avgRisk >= 50 ? '🟡 Medium Risk' : '🟢 Low Risk'}
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar
                    dataKey="lowZone"
                    stackId="zones"
                    fill={colors.status.success || '#4CAF50'}
                    fillOpacity={0.15}
                    name="Low Risk Zone (0-50%)"
                    isAnimationActive={false}
                  />
                  <Bar
                    dataKey="mediumZone"
                    stackId="zones"
                    fill={colors.status.warning || '#FFA726'}
                    fillOpacity={0.2}
                    name="Medium Risk Zone (50-75%)"
                    isAnimationActive={false}
                  />
                  <Bar
                    dataKey="highZone"
                    stackId="zones"
                    fill={primary}
                    fillOpacity={0.15}
                    name="High Risk Zone (75-100%)"
                    isAnimationActive={false}
                  />
                  <Bar
                    dataKey="avgRisk"
                    fill="url(#bulletGradient)"
                    name="Risk %"
                    radius={[0, 4, 4, 0]}
                    stroke={primary}
                    strokeWidth={2}
                  />
                  <ReferenceLine
                    x={50}
                    stroke={colors.status.warning || '#FFA726'}
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    label={{ value: "50%", position: "top", fill: colors.status.warning || '#FFA726', fontSize: 10 }}
                  />
                  <ReferenceLine
                    x={75}
                    stroke={primary}
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    label={{ value: "75%", position: "top", fill: primary, fontSize: 10 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <div style={{
                padding: '3rem',
                textAlign: 'center',
                color: colors.mutedForeground,
                backgroundColor: colors.secondary,
                borderRadius: '8px',
                border: `1px solid ${colors.border}`
              }}>
                <p>No employees found with risk score ≥ 50%</p>
                <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                  Try adjusting filters or upload data with higher risk scores
                </p>
              </div>
            )}
          </div>

          {/* Fraud Type Distribution - Scatter Plot */}
          {csvData.fraudTypeData && csvData.fraudTypeData.length > 0 && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Fraud Type Distribution</h3>
              {(() => {
                const total = csvData.fraudTypeData.reduce((sum, item) => sum + item.value, 0);
                const percentages = csvData.fraudTypeData.map(e => (e.value / total) * 100);
                const minPercentage = Math.min(...percentages);
                const maxPercentage = Math.max(...percentages);

                const scatterData = csvData.fraudTypeData.map((entry, index) => {
                  const percentage = total > 0 ? ((entry.value / total) * 100) : 0;
                  return {
                    name: entry.name,
                    count: entry.value,
                    percentage: parseFloat(percentage.toFixed(1)),
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
                  const jitterRadius = 0.8;
                  const angle = (duplicateIndex * (2 * Math.PI)) / (duplicates.length + 1);
                  const jitterX = duplicateIndex > 0 ? Math.cos(angle) * jitterRadius : 0;
                  const jitterY = duplicateIndex > 0 ? Math.sin(angle) * (jitterRadius * 2) : 0;

                  return {
                    ...entry,
                    percentage: entry.percentage + jitterX,
                    count: entry.count + jitterY
                  };
                });

                return (
                  <>
                    <ResponsiveContainer width="100%" height={400}>
                      <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                        <XAxis
                          type="number"
                          dataKey="percentage"
                          name="Percentage"
                          domain={[minPercentage - 2, maxPercentage + 2]}
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
                                    <span style={{ color: primary, fontWeight: 'bold' }}>Percentage:</span> {data.percentage.toFixed(1)}%
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
        </>
      )}

      {/* Show fraud-type-specific charts when fraud type filter is active */}
      {csvData.isFraudTypeFiltered && csvData.fraudTypeSpecificData && (
        <>
          {/* Average Risk Comparison */}
          <div style={styles.chartBox}>
            <h3 style={styles.chartTitle}>Average Risk Comparison</h3>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gridTemplateRows: 'repeat(2, 1fr)',
              gap: '1.5rem',
              marginTop: '1rem'
            }}>
              <div style={{
                backgroundColor: colors.secondary,
                padding: '1.5rem',
                borderRadius: '0.75rem',
                border: `1px solid ${colors.border}`,
                textAlign: 'center'
              }}>
                <div style={{
                  fontSize: '0.875rem',
                  color: colors.mutedForeground,
                  marginBottom: '0.5rem'
                }}>
                  {csvData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}
                </div>
                <div style={{
                  fontSize: '2rem',
                  fontWeight: 'bold',
                  color: primary,
                  marginBottom: '0.25rem'
                }}>
                  {csvData.fraudTypeSpecificData.avgRiskComparison.selectedFraudType}%
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: colors.mutedForeground
                }}>
                  Average Risk
                </div>
              </div>
              <div style={{
                backgroundColor: colors.secondary,
                padding: '1.5rem',
                borderRadius: '0.75rem',
                border: `1px solid ${colors.border}`,
                textAlign: 'center'
              }}>
                <div style={{
                  fontSize: '0.875rem',
                  color: colors.mutedForeground,
                  marginBottom: '0.5rem'
                }}>
                  All Paystubs
                </div>
                <div style={{
                  fontSize: '2rem',
                  fontWeight: 'bold',
                  color: colors.foreground,
                  marginBottom: '0.25rem'
                }}>
                  {csvData.fraudTypeSpecificData.avgRiskComparison.allPaystubs}%
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: colors.mutedForeground
                }}>
                  Average Risk
                </div>
              </div>
              {csvData.fraudTypeSpecificData.kpis && (
                <>
                  <div style={{
                    backgroundColor: colors.secondary,
                    padding: '1.5rem',
                    borderRadius: '0.75rem',
                    border: `1px solid ${colors.border}`,
                    textAlign: 'center'
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      color: colors.mutedForeground,
                      marginBottom: '0.5rem'
                    }}>
                      Medium-Risk Cases
                    </div>
                    <div style={{
                      fontSize: '2rem',
                      fontWeight: 'bold',
                      color: colors.status.warning || '#FFA726',
                      marginBottom: '0.25rem'
                    }}>
                      {csvData.fraudTypeSpecificData.kpis.mediumRiskCasesCount || 0}
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: colors.mutedForeground
                    }}>
                      Risk 50-75%
                    </div>
                  </div>
                  <div style={{
                    backgroundColor: colors.secondary,
                    padding: '1.5rem',
                    borderRadius: '0.75rem',
                    border: `1px solid ${colors.border}`,
                    textAlign: 'center'
                  }}>
                    <div style={{
                      fontSize: '0.875rem',
                      color: colors.mutedForeground,
                      marginBottom: '0.5rem'
                    }}>
                      High-Risk Cases
                    </div>
                    <div style={{
                      fontSize: '2rem',
                      fontWeight: 'bold',
                      color: primary,
                      marginBottom: '0.25rem'
                    }}>
                      {csvData.fraudTypeSpecificData.kpis.highRiskCasesCount || 0}
                    </div>
                    <div style={{
                      fontSize: '0.75rem',
                      color: colors.mutedForeground
                    }}>
                      Risk ≥ 75%
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Severity Breakdown */}
          {csvData.fraudTypeSpecificData.severityBreakdown && csvData.fraudTypeSpecificData.severityBreakdown.length > 1 && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Severity Breakdown for {csvData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={csvData.fraudTypeSpecificData.severityBreakdown}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    innerRadius={40}
                    fill="#8884d8"
                    dataKey="value"
                    stroke={colors.card}
                    strokeWidth={2}
                  >
                    {csvData.fraudTypeSpecificData.severityBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{ color: colors.foreground }}
                    iconType="circle"
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Risk Score Distribution */}
          {csvData.fraudTypeSpecificData.severityBreakdown && csvData.fraudTypeSpecificData.severityBreakdown.length === 1 && csvData.fraudTypeSpecificData.riskScoreDistribution && csvData.fraudTypeSpecificData.riskScoreDistribution.length > 0 && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Risk Score Distribution for {csvData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={csvData.fraudTypeSpecificData.riskScoreDistribution} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <defs>
                    <linearGradient id="riskDistGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={primary} stopOpacity={1} />
                      <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
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
                    label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey="count"
                    fill="url(#riskDistGradient)"
                    radius={[8, 8, 0, 0]}
                    name="Paystub Count"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Monthly Trend */}
          {csvData.fraudTypeSpecificData.monthlyTrend && csvData.fraudTypeSpecificData.monthlyTrend.length > 0 && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Monthly Trend: {csvData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={csvData.fraudTypeSpecificData.monthlyTrend}>
                  <defs>
                    <linearGradient id="trendLineGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={primary} stopOpacity={0.8} />
                      <stop offset="100%" stopColor={primary} stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                  <XAxis
                    dataKey="month"
                    tick={{ fill: colors.foreground, fontSize: 11 }}
                    stroke={colors.border}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis
                    tick={{ fill: colors.foreground, fontSize: 12 }}
                    stroke={colors.border}
                    label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke={primary}
                    strokeWidth={3}
                    dot={{ fill: primary, r: 5 }}
                    name="Paystub Count"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top Employers for This Fraud Type */}
          {!csvData.isSingleEmployerView && csvData.fraudTypeSpecificData.topEmployersForFraudType && csvData.fraudTypeSpecificData.topEmployersForFraudType.length > 0 && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Top Employers for {csvData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart
                  data={csvData.fraudTypeSpecificData.topEmployersForFraudType}
                  margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
                >
                  <defs>
                    <linearGradient id="employerFraudTypeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={primary} stopOpacity={1} />
                      <stop offset="100%" stopColor={primary} stopOpacity={0.6} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                    tick={{ fill: colors.foreground, fontSize: 11 }}
                    stroke={colors.border}
                  />
                  <YAxis
                    tick={{ fill: colors.foreground, fontSize: 12 }}
                    stroke={colors.border}
                    label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: colors.foreground }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey="count"
                    fill="url(#employerFraudTypeGradient)"
                    name="Paystub Count"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Employee Risk Distribution */}
          {csvData.isSingleEmployerView && csvData.fraudTypeSpecificData.employeeRiskDistribution && csvData.fraudTypeSpecificData.employeeRiskDistribution.length > 0 && (
            <div style={styles.chartBox}>
              <h3 style={styles.chartTitle}>Employee Risk Distribution for {csvData.fraudTypeSpecificData.avgRiskComparison.fraudTypeName}</h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart
                  data={csvData.fraudTypeSpecificData.employeeRiskDistribution}
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 120, bottom: 20 }}
                >
                  <defs>
                    <linearGradient id="employeeRiskGradient" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor={primary} stopOpacity={0.9} />
                      <stop offset="100%" stopColor={primary} stopOpacity={0.7} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} opacity={0.3} horizontal={false} />
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    tick={{ fill: colors.foreground, fontSize: 11 }}
                    stroke={colors.border}
                    label={{ value: 'Risk %', position: 'insideBottom', offset: -5, fill: colors.foreground }}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={110}
                    tick={{ fill: colors.foreground, fontSize: 11 }}
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
                              {data.name}
                            </p>
                            <p style={{ margin: '4px 0', color: primary }}>
                              <span style={{ fontWeight: '600' }}>Avg Risk:</span> {data.avgRisk.toFixed(1)}%
                            </p>
                            <p style={{ margin: '4px 0', color: colors.mutedForeground }}>
                              <span style={{ fontWeight: '600' }}>Cases:</span> {data.count}
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar
                    dataKey="avgRisk"
                    fill="url(#employeeRiskGradient)"
                    name="Risk %"
                    radius={[0, 4, 4, 0]}
                  />
                  <ReferenceLine
                    x={50}
                    stroke={colors.status.warning || '#FFA726'}
                    strokeDasharray="5 5"
                    label={{ value: '50%', position: 'top', fill: colors.status.warning }}
                  />
                  <ReferenceLine
                    x={75}
                    stroke={primary}
                    strokeDasharray="5 5"
                    label={{ value: '75%', position: 'top', fill: primary }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PaystubCharts;
