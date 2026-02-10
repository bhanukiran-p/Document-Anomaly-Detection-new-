import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsLine = ({ data, title, height = 220 }) => {
  // Validate and log data
  console.log('EChartsLine received data:', data);

  // Extract fraud and legitimate counts, calculate fraud rate
  // Ensure all values are defined and valid
  const validData = React.useMemo(() => {
    return data?.filter(item => item && item.month) || [];
  }, [data]);

  const months = React.useMemo(() => {
    return validData.map(item => item.month || 'Unknown');
  }, [validData]);

  const fraudCounts = React.useMemo(() => {
    return validData.map(item => {
      const value = item.fraud ?? item.fraud_count ?? 0;
      return typeof value === 'number' && !isNaN(value) ? value : 0;
    });
  }, [validData]);

  const legitimateCounts = React.useMemo(() => {
    return validData.map(item => {
      const value = item.legitimate ?? item.legitimate_count ?? 0;
      return typeof value === 'number' && !isNaN(value) ? value : 0;
    });
  }, [validData]);

  // Calculate fraud rate as percentage
  const fraudRates = React.useMemo(() => {
    return validData.map(item => {
      const fraud = item.fraud ?? item.fraud_count ?? 0;
      const legitimate = item.legitimate ?? item.legitimate_count ?? 0;
      const total = fraud + legitimate;
      const rate = total > 0 ? ((fraud / total) * 100) : 0;
      return typeof rate === 'number' && !isNaN(rate) ? parseFloat(rate.toFixed(2)) : 0;
    });
  }, [validData]);

  // Create a key based on data to force remount on data change
  const dataKey = React.useMemo(() => {
    return months.join('|') + fraudCounts.join('|') + legitimateCounts.join('|');
  }, [months, fraudCounts, legitimateCounts]);

  console.log('EChartsLine processed:', { months, fraudCounts, legitimateCounts, fraudRates });

  if (!data || data.length === 0) {
    return (
      <div style={{
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#94a3b8',
        fontSize: '0.9rem'
      }}>
        No trend data available
      </div>
    );
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      },
      formatter: (params) => {
        try {
          if (!params || !Array.isArray(params) || params.length === 0) {
            return '';
          }
          const firstParam = params[0];
          if (!firstParam) {
            return '';
          }
          let result = `<strong>${firstParam.axisValue || firstParam.name || 'Unknown'}</strong><br/>`;
          params.forEach(param => {
            if (param && param.seriesName && param.value !== undefined && param.value !== null) {
              result += `${param.marker || ''} ${param.seriesName}: ${param.value}${param.seriesName.includes('Rate') ? '%' : ''}<br/>`;
            }
          });
          return result;
        } catch (error) {
          console.error('Tooltip formatter error:', error);
          return '';
        }
      }
    },
    legend: {
      data: ['Fraud', 'Legitimate'],
      bottom: 10,
      textStyle: {
        color: '#94a3b8'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        color: '#94a3b8',
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Fraud Count',
        position: 'left',
        min: function(value) {
          // Calculate min with padding
          const minValue = value.min;
          const maxValue = value.max;
          const range = maxValue - minValue;
          // Add 20% padding below
          return Math.max(0, Math.floor(minValue - range * 0.2));
        },
        max: function(value) {
          // Calculate max with padding
          const minValue = value.min;
          const maxValue = value.max;
          const range = maxValue - minValue;
          // Add 20% padding above
          return Math.ceil(maxValue + range * 0.2);
        },
        interval: 50,
        axisLine: {
          lineStyle: {
            color: '#ef4444'
          }
        },
        axisLabel: {
          color: '#ef4444',
          formatter: '{value}'
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#334155',
            type: 'dashed',
            opacity: 0.3
          }
        }
      },
      {
        type: 'value',
        name: 'Legitimate Count',
        position: 'right',
        axisLine: {
          lineStyle: {
            color: '#10b981'
          }
        },
        axisLabel: {
          color: '#10b981',
          formatter: '{value}'
        },
        splitLine: {
          lineStyle: {
            color: '#334155',
            type: 'dashed'
          }
        }
      }
    ],
    series: [
      {
        name: 'Fraud',
        type: 'line',
        yAxisIndex: 0,
        data: fraudCounts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 3,
          color: '#ef4444'
        },
        itemStyle: {
          color: '#ef4444',
          borderWidth: 2,
          borderColor: '#fff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
              { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
            ]
          }
        }
      },
      {
        name: 'Legitimate',
        type: 'line',
        yAxisIndex: 1,
        data: legitimateCounts,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 3,
          color: '#10b981'
        },
        itemStyle: {
          color: '#10b981',
          borderWidth: 2,
          borderColor: '#fff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
            ]
          }
        }
      }
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut'
  };

  return (
    <ReactECharts
      key={dataKey}
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'canvas' }}
      notMerge={true}
      lazyUpdate={false}
    />
  );
};

export default EChartsLine;
