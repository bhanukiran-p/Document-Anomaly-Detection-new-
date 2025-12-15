import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsDonut = ({ data, title, height = 220 }) => {
  const safeData = Array.isArray(data)
    ? data
        .map((item) => {
          if (!item) return null;
          const value = Number(item.value);
          const label = item.label || item.name;
          if (!label || Number.isNaN(value)) return null;
          return { label, value };
        })
        .filter(Boolean)
    : [];

  if (safeData.length === 0) {
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
        No distribution data available
      </div>
    );
  }

  const option = {
    tooltip: {
      trigger: 'item',
      confine: true,
      formatter: (params) => {
        try {
          if (!params || typeof params !== 'object') {
            return '';
          }
          // Safely access data
          const data = params.data;
          if (!data) {
            return '';
          }
          const name = params.name || data.name || '';
          const value = params.value !== undefined ? params.value : (data.value !== undefined ? data.value : 0);
          const percent = params.percent !== undefined ? params.percent : 0;
          return `${name}: ${value} (${percent.toFixed(1)}%)`;
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
    legend: {
      bottom: 10,
      left: 'center',
      textStyle: {
        color: '#94a3b8'
      },
      itemGap: 20
    },
    series: [
      {
        name: 'Transactions',
        type: 'pie',
        radius: ['45%', '70%'], // Donut shape
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#0f172a',
          borderWidth: 2
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{d}%',
          color: '#e2e8f0',
          fontSize: 12,
          fontWeight: 600
        },
        labelLine: {
          show: true,
          lineStyle: {
            color: '#475569'
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 20,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          },
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: safeData.map((item) => ({
          value: item.value,
          name: item.label,
          itemStyle: {
            color: item.label === 'Fraud' ? '#ef4444' : '#10b981'
          }
        }))
      }
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut'
  };

  // Create a key based on data to force remount on data change
  const dataKey = React.useMemo(() => {
    return safeData.map(d => `${d.label}-${d.value}`).join('|');
  }, [safeData]);

  return (
    <ReactECharts
      key={dataKey}
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
      opts={{ renderer: 'canvas' }}
      notMerge={true}
      lazyUpdate={false}
      onEvents={{
        mouseover: (params) => {
          // Prevent errors by checking params validity
          if (!params || !params.data) {
            return;
          }
        },
        mouseout: (params) => {
          // Prevent errors by checking params validity
          if (!params || !params.data) {
            return;
          }
        }
      }}
    />
  );
};

export default EChartsDonut;
