import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsHeatmap = ({ data, title, height = 400 }) => {
  const { matrix = [], labels = [] } = data || {};

  // Convert matrix to ECharts format
  const heatmapData = [];
  matrix.forEach((row, i) => {
    row.forEach((value, j) => {
      heatmapData.push([j, i, value || 0]);
    });
  });

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
      position: 'top',
      formatter: (params) => {
        const xLabel = labels[params.value[0]] || params.value[0];
        const yLabel = labels[params.value[1]] || params.value[1];
        const value = params.value[2].toFixed(2);
        return `${xLabel} & ${yLabel}<br/>Correlation: ${value}`;
      },
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    grid: {
      left: '15%',
      right: '10%',
      top: '15%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: labels,
      splitArea: {
        show: true
      },
      axisLabel: {
        rotate: 45,
        color: '#94a3b8',
        fontSize: 10
      }
    },
    yAxis: {
      type: 'category',
      data: labels,
      splitArea: {
        show: true
      },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10
      }
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%',
      inRange: {
        color: ['#3b82f6', '#e2e8f0', '#ef4444']
      },
      textStyle: {
        color: '#94a3b8'
      }
    },
    series: [
      {
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: true,
          formatter: (params) => params.value[2].toFixed(2),
          color: '#1e293b',
          fontSize: 10,
          fontWeight: 600
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
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

export default EChartsHeatmap;
