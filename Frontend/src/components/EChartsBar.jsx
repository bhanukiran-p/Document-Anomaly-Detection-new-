import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsBar = ({ data, title, height = 400 }) => {
  // Calculate dynamic height based on number of bars
  const calculatedHeight = Math.max(400, data.length * 50);

  // Reverse data so highest values appear at the top (descending order)
  const reversedData = [...data].reverse();

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
      axisPointer: {
        type: 'shadow'
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
      top: '15%',
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
        data: reversedData.map(item => ({
          value: item.value,
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
        })),
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
      option={option}
      style={{ height: `${calculatedHeight}px`, width: '100%' }}
      opts={{ renderer: 'canvas' }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
};

export default EChartsBar;
