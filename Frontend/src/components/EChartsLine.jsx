import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsLine = ({ data, title, height = 220 }) => {
  // Validate and log data
  console.log('EChartsLine received data:', data);

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

  // Extract fraud and legitimate counts, calculate fraud rate
  // Ensure all values are defined and valid
  const validData = data.filter(item => item && item.month);

  const months = validData.map(item => item.month || 'Unknown');
  const fraudCounts = validData.map(item => {
    const value = item.fraud ?? item.fraud_count ?? 0;
    return typeof value === 'number' && !isNaN(value) ? value : 0;
  });
  const legitimateCounts = validData.map(item => {
    const value = item.legitimate ?? item.legitimate_count ?? 0;
    return typeof value === 'number' && !isNaN(value) ? value : 0;
  });

  // Calculate fraud rate as percentage
  const fraudRates = validData.map(item => {
    const fraud = item.fraud ?? item.fraud_count ?? 0;
    const legitimate = item.legitimate ?? item.legitimate_count ?? 0;
    const total = fraud + legitimate;
    const rate = total > 0 ? ((fraud / total) * 100) : 0;
    return typeof rate === 'number' && !isNaN(rate) ? parseFloat(rate.toFixed(2)) : 0;
  });

  console.log('EChartsLine processed:', { months, fraudCounts, legitimateCounts, fraudRates });

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      },
      formatter: (params) => {
        if (!params || !Array.isArray(params) || params.length === 0) {
          return '';
        }
        let result = `<strong>${params[0]?.axisValue || 'Unknown'}</strong><br/>`;
        params.forEach(param => {
          if (param && param.seriesName && param.value !== undefined && param.value !== null) {
            result += `${param.marker} ${param.seriesName}: ${param.value}${param.seriesName.includes('Rate') ? '%' : ''}<br/>`;
          }
        });
        return result;
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
    yAxis: {
      type: 'value',
      name: 'Transaction Count',
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        color: '#94a3b8'
      },
      splitLine: {
        lineStyle: {
          color: '#334155',
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: 'Fraud',
        type: 'line',
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
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'canvas' }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
};

export default EChartsLine;
