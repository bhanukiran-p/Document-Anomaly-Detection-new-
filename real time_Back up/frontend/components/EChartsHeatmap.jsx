import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsHeatmap = ({ data, title, height = 400 }) => {
  const matrix = Array.isArray(data?.matrix) ? data.matrix : [];
  const labels = Array.isArray(data?.labels) ? data.labels : [];

  if (
    !matrix.length ||
    !labels.length ||
    !Array.isArray(matrix[0]) ||
    matrix[0].length === 0
  ) {
    return (
      <div
        style={{
          height,
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#94a3b8',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '0.75rem',
          border: '1px solid rgba(148, 163, 184, 0.3)',
          fontSize: '0.9rem'
        }}
      >
        No correlation data available
      </div>
    );
  }

  const size = Math.min(matrix.length, labels.length);

  const normalizedLabels = labels.slice(0, size);

  const normalizedMatrix = matrix.slice(0, size).map((row, i) => {
    if (!Array.isArray(row)) {
      return new Array(size).fill(0);
    }
    return row.slice(0, size).map((val, j) => {
      const num = Number(val);
      if (Number.isNaN(num)) return 0;
      if (num > 1) return 1;
      if (num < -1) return -1;
      return num;
    });
  });

  const heatmapData = [];
  normalizedMatrix.forEach((row, i) => {
    row.forEach((value, j) => {
      heatmapData.push([j, i, value]);
    });
  });

  const option = {
    title: {
      text: title || 'Correlation Heatmap',
      left: 'center',
      textStyle: {
        color: '#e5e7eb',
        fontSize: 14,
        fontWeight: 500
      }
    },
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(15,23,42,0.95)',
      borderColor: 'rgba(148,163,184,0.4)',
      borderWidth: 1,
      textStyle: {
        color: '#e5e7eb',
        fontSize: 12
      },
      formatter: (params) => {
        try {
          const [xIndex, yIndex, value] = Array.isArray(params.value)
            ? params.value
            : [params.data?.[0], params.data?.[1], params.data?.[2]];

          const xLabel =
            typeof xIndex === 'number' && normalizedLabels[xIndex] != null
              ? normalizedLabels[xIndex]
              : '';
          const yLabel =
            typeof yIndex === 'number' && normalizedLabels[yIndex] != null
              ? normalizedLabels[yIndex]
              : '';

          const v =
            typeof value === 'number' && !Number.isNaN(value)
              ? value.toFixed(2)
              : '0.00';

          return `${yLabel} vs ${xLabel}<br/>Correlation: ${v}`;
        } catch (e) {
          return '';
        }
      }
    },
    grid: {
      left: '15%',
      right: '10%',
      top: '10%',
      bottom: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: normalizedLabels,
      splitArea: { show: true },
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        rotate: 45,
        color: '#94a3b8',
        fontSize: 10,
        interval: 0
      },
      boundaryGap: true
    },
    yAxis: {
      type: 'category',
      data: normalizedLabels,
      splitArea: { show: true },
      axisLine: {
        lineStyle: {
          color: '#475569'
        }
      },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10
      },
      boundaryGap: true
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
          formatter: (params) => {
            try {
              if (!params || !params.value || !Array.isArray(params.value)) {
                return '';
              }
              const value = params.value[2];
              if (typeof value !== 'number' || Number.isNaN(value)) {
                return '';
              }
              return value.toFixed(2);
            } catch (e) {
              return '';
            }
          },
          // Use white text for visibility on colored backgrounds
          color: '#ffffff',
          fontSize: 11,
          fontWeight: 700,
          textBorderColor: 'rgba(0, 0, 0, 0.8)',
          textBorderWidth: 2
        },
        itemStyle: {
          borderColor: 'rgba(0, 0, 0, 0.2)',
          borderWidth: 1
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.4)'
          }
        }
      }
    ]
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
