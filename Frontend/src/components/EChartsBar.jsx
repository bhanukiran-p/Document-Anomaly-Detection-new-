import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsBar = ({ data, title, height = 400 }) => {

  const normalizedData = React.useMemo(() => {
    return Array.isArray(data)
      ? data
          .map((item) => {
            if (!item) return null;
            const label = item.label || item.name;
            const value = Number(item.value);
            if (!label || Number.isNaN(value)) return null;
            return { label, value };
          })
          .filter(Boolean)
      : [];
  }, [data]);

  // Calculate dynamic height based on number of bars
  const calculatedHeight = Math.max(400, normalizedData.length * 50);

  // Reverse data so highest values appear at the top (descending order)
  const reversedData = React.useMemo(() => {
    return [...normalizedData].reverse();
  }, [normalizedData]);

  // Create a key based on data to force remount on data change
  const dataKey = React.useMemo(() => {
    return reversedData.map(d => `${d.label}-${d.value}`).join('|');
  }, [reversedData]);

  if (normalizedData.length === 0) {
    return (
      <div
        style={{
          height: `${height}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#94a3b8',
          fontSize: '0.9rem'
        }}
      >
        No breakdown data available
      </div>
    );
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        try {
          if (!params || !Array.isArray(params) || params.length === 0) {
            return '';
          }
          const param = params[0];
          if (!param || param.value === undefined || param.value === null) {
            return '';
          }
          return `<strong>${param.axisValueLabel || param.name || ''}</strong><br/>${param.marker || ''} ${param.value}`;
        } catch (error) {
          console.error('Tooltip formatter error:', error);
          return '';
        }
      },
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    grid: {
      left: '20%',
      right: '10%',
      top: '5%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
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
    yAxis: {
      type: 'category',
      data: reversedData.map(item => item.label),
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        color: '#e2e8f0',
        fontSize: 12,
        fontWeight: 500
      },
      axisTick: {
        show: false
      }
    },
    series: [
      {
        type: 'bar',
        name: 'Count',
        data: reversedData.map(item => {
          const value = typeof item.value === 'number' ? item.value : 0;
          return {
            value: value,
            itemStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 1,
                y2: 0,
                colorStops: [
                  { offset: 0, color: '#f59e0b' },
                  { offset: 1, color: '#f97316' }
                ]
              },
              borderRadius: [0, 8, 8, 0]
            }
          };
        }),
        barWidth: '60%',
        label: {
          show: true,
          position: 'right',
          color: '#e2e8f0',
          fontSize: 12,
          fontWeight: 600
        },
        emphasis: {
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 1,
              y2: 0,
              colorStops: [
                { offset: 0, color: '#fb923c' },
                { offset: 1, color: '#fb923c' }
              ]
            }
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
      style={{ height: `${calculatedHeight}px`, width: '100%' }}
      opts={{ renderer: 'canvas' }}
      notMerge={true}
      lazyUpdate={false}
    />
  );
};

export default EChartsBar;
