// import React from 'react';
// import ReactECharts from 'echarts-for-react';

// const EChartsDonut = ({ data, title, height = 220 }) => {
//   const safeData = Array.isArray(data)
//     ? data
//         .map((item) => {
//           if (!item) return null;
//           const value = Number(item.value);
//           const label = item.label || item.name;
//           if (!label || Number.isNaN(value)) return null;
//           return { label, value };
//         })
//         .filter(Boolean)
//     : [];

//   if (safeData.length === 0) {
//     return (
//       <div
//         style={{
//           height: `${height}px`,
//           display: 'flex',
//           alignItems: 'center',
//           justifyContent: 'center',
//           color: '#94a3b8',
//           fontSize: '0.9rem'
//         }}
//       >
//         No distribution data available
//       </div>
//     );
//   }

//   const option = {
//     tooltip: {
//       trigger: 'item',
//       formatter: '{b}: {c} ({d}%)',
//       backgroundColor: 'rgba(30, 41, 59, 0.95)',
//       borderColor: '#334155',
//       textStyle: {
//         color: '#e2e8f0'
//       }
//     },
//     legend: {
//       bottom: 10,
//       left: 'center',
//       textStyle: {
//         color: '#94a3b8'
//       },
//       itemGap: 20
//     },
//     series: [
//       {
//         name: 'Transactions',
//         type: 'pie',
//         radius: ['45%', '70%'], // Donut shape
//         center: ['50%', '50%'],
//         avoidLabelOverlap: true,
//         itemStyle: {
//           borderRadius: 8,
//           borderColor: '#0f172a',
//           borderWidth: 2
//         },
//         label: {
//           show: true,
//           position: 'outside',
//           formatter: '{b}\n{d}%',
//           color: '#e2e8f0',
//           fontSize: 12,
//           fontWeight: 600
//         },
//         labelLine: {
//           show: true,
//           lineStyle: {
//             color: '#475569'
//           }
//         },
//         emphasis: {
//           itemStyle: {
//             shadowBlur: 20,
//             shadowOffsetX: 0,
//             shadowColor: 'rgba(0, 0, 0, 0.5)'
//           },
//           label: {
//             show: true,
//             fontSize: 14,
//             fontWeight: 'bold'
//           }
//         },
//         data: safeData.map((item) => ({
//           value: item.value,
//           name: item.label,
//           itemStyle: {
//             color: item.label === 'Fraud' ? '#ef4444' : '#10b981'
//           }
//         }))
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

// export default EChartsDonut;















import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsDonut = ({ data, title, height = 220 }) => {
  const safeData = Array.isArray(data)
    ? data
        .map((item) => {
          if (!item) return null;
          const value = Number(item.value ?? item.count ?? item.total);
          const label = item.label || item.name;
          if (!label || Number.isNaN(value)) return null;

          // 🎨 Apply color based on label
          let color = '#64748b'; // default
          if (label.toLowerCase().includes('fraud')) color = '#ef4444';
          if (label.toLowerCase().includes('legit')) color = '#22c55e';

          return { name: label, value, itemStyle: { color } };
        })
        .filter(Boolean)
    : [];

  if (!safeData.length) {
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
        No distribution data available
      </div>
    );
  }

  const option = {
    title: {
      text: title || 'Fraud vs Legitimate Distribution',
      left: 'center',
      top: 10,
      textStyle: {
        color: '#e5e7eb',
        fontSize: 14,
        fontWeight: 500
      }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15,23,42,0.95)',
      borderColor: 'rgba(148,163,184,0.4)',
      borderWidth: 1,
      textStyle: { color: '#e5e7eb', fontSize: 12 }
    },
    legend: {
      bottom: 0,
      textStyle: {
        color: '#cbd5f5',
        fontSize: 11
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#0f172a',
          borderWidth: 2
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            color: '#e5e7eb',
            formatter: (p) => `${p.name}\n${p.percent.toFixed(1)}%`
          }
        },
        data: safeData
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

export default EChartsDonut;
