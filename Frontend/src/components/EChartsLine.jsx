// import React from 'react';
// import ReactECharts from 'echarts-for-react';

// const EChartsLine = ({ data, title, height = 220 }) => {
//   // Validate and log data
//   console.log('EChartsLine received data:', data);

//   if (!data || data.length === 0) {
//     return (
//       <div style={{
//         height: `${height}px`,
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         color: '#94a3b8',
//         fontSize: '0.9rem'
//       }}>
//         No trend data available
//       </div>
//     );
//   }

//   // Extract fraud and legitimate counts, calculate fraud rate
//   const months = data.map(item => item.month);
//   const fraudCounts = data.map(item => item.fraud || item.fraud_count || 0);
//   const legitimateCounts = data.map(item => item.legitimate || item.legitimate_count || 0);

//   // Calculate fraud rate as percentage
//   const fraudRates = data.map(item => {
//     const fraud = item.fraud || item.fraud_count || 0;
//     const legitimate = item.legitimate || item.legitimate_count || 0;
//     const total = fraud + legitimate;
//     return total > 0 ? ((fraud / total) * 100).toFixed(2) : 0;
//   });

//   console.log('EChartsLine processed:', { months, fraudCounts, legitimateCounts, fraudRates });

//   const option = {
//     tooltip: {
//       trigger: 'axis',
//       backgroundColor: 'rgba(30, 41, 59, 0.95)',
//       borderColor: '#334155',
//       textStyle: {
//         color: '#e2e8f0'
//       },
//       formatter: (params) => {
//         let result = `<strong>${params[0].axisValue}</strong><br/>`;
//         params.forEach(param => {
//           result += `${param.marker} ${param.seriesName}: ${param.value}${param.seriesName.includes('Rate') ? '%' : ''}<br/>`;
//         });
//         return result;
//       }
//     },
//     legend: {
//       data: ['Fraud', 'Legitimate'],
//       bottom: 10,
//       textStyle: {
//         color: '#94a3b8'
//       }
//     },
//     grid: {
//       left: '3%',
//       right: '4%',
//       bottom: '15%',
//       top: '10%',
//       containLabel: true
//     },
//     xAxis: {
//       type: 'category',
//       data: months,
//       axisLine: {
//         lineStyle: {
//           color: '#475569'
//         }
//       },
//       axisLabel: {
//         color: '#94a3b8',
//         rotate: 45
//       }
//     },
//     yAxis: {
//       type: 'value',
//       name: 'Transaction Count',
//       axisLine: {
//         lineStyle: {
//           color: '#475569'
//         }
//       },
//       axisLabel: {
//         color: '#94a3b8'
//       },
//       splitLine: {
//         lineStyle: {
//           color: '#334155',
//           type: 'dashed'
//         }
//       }
//     },
//     series: [
//       {
//         name: 'Fraud',
//         type: 'line',
//         data: fraudCounts,
//         smooth: true,
//         symbol: 'circle',
//         symbolSize: 8,
//         lineStyle: {
//           width: 3,
//           color: '#ef4444'
//         },
//         itemStyle: {
//           color: '#ef4444',
//           borderWidth: 2,
//           borderColor: '#fff'
//         },
//         areaStyle: {
//           color: {
//             type: 'linear',
//             x: 0,
//             y: 0,
//             x2: 0,
//             y2: 1,
//             colorStops: [
//               { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
//               { offset: 1, color: 'rgba(239, 68, 68, 0.05)' }
//             ]
//           }
//         }
//       },
//       {
//         name: 'Legitimate',
//         type: 'line',
//         data: legitimateCounts,
//         smooth: true,
//         symbol: 'circle',
//         symbolSize: 8,
//         lineStyle: {
//           width: 3,
//           color: '#10b981'
//         },
//         itemStyle: {
//           color: '#10b981',
//           borderWidth: 2,
//           borderColor: '#fff'
//         },
//         areaStyle: {
//           color: {
//             type: 'linear',
//             x: 0,
//             y: 0,
//             x2: 0,
//             y2: 1,
//             colorStops: [
//               { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
//               { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
//             ]
//           }
//         }
//       }
//     ],
//     animation: true,
//     animationDuration: 1000,
//     animationEasing: 'cubicOut'
//   };

//   return (
//     <ReactECharts
//       option={option}
//       style={{ height: `${height}px`, width: '100%' }}
//       opts={{ renderer: 'canvas' }}
//       notMerge={true}
//       lazyUpdate={true}
//     />
//   );
// };

// export default EChartsLine;




















import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsLine = ({ data, title, height = 260 }) => {
  const safeArray = Array.isArray(data) ? data : [];

  const points = safeArray
    .map((item) => {
      if (!item) return null;
      const month = item.month || item.label || item.date;
      const fraud = Number(item.fraud ?? item.fraudCount);
      const legit = Number(item.legit ?? item.legitimate ?? item.legitCount);
      if (!month) return null;

      return {
        month: String(month),
        fraud: Number.isNaN(fraud) ? 0 : fraud,
        legit: Number.isNaN(legit) ? 0 : legit
      };
    })
    .filter(Boolean);

  if (!points.length) {
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
          border: '1px solid rgba(148, 163, 184, 0.3)'
        }}
      >
        No trend data available
      </div>
    );
  }

  const months = points.map((p) => p.month);
  const fraudSeries = points.map((p) => p.fraud);
  const legitSeries = points.map((p) => p.legit);

  const option = {
    title: {
      text: title || 'Monthly Fraud Trend',
      left: 'center',
      textStyle: { color: '#e5e7eb', fontSize: 14 }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15,23,42,0.95)',
      textStyle: { color: '#e5e7eb' }
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#cbd5f5' }
    },
    xAxis: {
      type: 'category',
      data: months,
      boundaryGap: false,
      axisLabel: { color: '#94a3b8', rotate: 35 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        name: 'Fraud',
        type: 'line',
        smooth: true,
        data: fraudSeries,
        symbol: 'circle',
        showSymbol: false,
        lineStyle: { color: '#ef4444' },
        itemStyle: { color: '#ef4444' }
      },
      {
        name: 'Legitimate',
        type: 'line',
        smooth: true,
        data: legitSeries,
        symbol: 'circle',
        showSymbol: false,
        lineStyle: { color: '#22c55e' },
        itemStyle: { color: '#22c55e' }
      }
    ]
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: `${height}px`, width: '100%' }}
    />
  );
};

export default EChartsLine;









