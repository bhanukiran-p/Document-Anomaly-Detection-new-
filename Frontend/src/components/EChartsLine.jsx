import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsLine = ({ data, title, height = 220 }) => {
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
      trigger: 'axis',
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    legend: {
      data: ['Fraud Count', 'Fraud Rate'],
      bottom: 10,
      textStyle: {
        color: '#94a3b8'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.month),
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        color: '#94a3b8'
      }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Count',
        position: 'left',
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
      {
        type: 'value',
        name: 'Rate (%)',
        position: 'right',
        axisLine: {
          lineStyle: {
            color: '#475569'
          }
        },
        axisLabel: {
          color: '#94a3b8',
          formatter: '{value}%'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: 'Fraud Count',
        type: 'line',
        data: data.map(item => item.fraud_count),
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
        name: 'Fraud Rate',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(item => item.fraud_rate),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 3,
          color: '#3b82f6'
        },
        itemStyle: {
          color: '#3b82f6',
          borderWidth: 2,
          borderColor: '#fff'
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
