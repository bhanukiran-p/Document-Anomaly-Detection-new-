import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsDonut = ({ data, title, height = 220 }) => {
  const option = {
    title: {
      text: title,
      left: 'center',
      top: 10,
      textStyle: {
        color: '#e2e8f0',
        fontSize: 14,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
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
        data: data.map((item) => ({
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

export default EChartsDonut;
