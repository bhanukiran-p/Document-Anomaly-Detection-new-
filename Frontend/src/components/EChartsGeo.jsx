import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';

const EChartsGeo = ({ data, title, height = 400 }) => {
  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    // Load world map GeoJSON
    fetch('https://cdn.jsdelivr.net/npm/echarts@5/map/json/world.json')
      .then(response => response.json())
      .then(worldMapData => {
        echarts.registerMap('world', worldMapData);
        setMapLoaded(true);
      })
      .catch(err => {
        console.error('Failed to load world map:', err);
      });
  }, []);

  if (!mapLoaded) {
    return (
      <div style={{
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#94a3b8',
        fontSize: '0.9rem'
      }}>
        Loading world map...
      </div>
    );
  }

  // Convert lat/lng to ECharts format
  const geoData = data.map(point => ({
    name: `${point.city}, ${point.country}`,
    value: [point.lng, point.lat, point.count],
    itemStyle: {
      color: '#ef4444'
    }
  }));

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
      formatter: (params) => {
        if (params.value) {
          return `${params.name}<br/>Transactions: ${params.value[2]}`;
        }
        return params.name;
      },
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    geo: {
      map: 'world',
      roam: true,
      itemStyle: {
        areaColor: '#1e293b',
        borderColor: '#475569'
      },
      emphasis: {
        itemStyle: {
          areaColor: '#334155'
        },
        label: {
          show: false
        }
      },
      top: '15%',
      bottom: '10%'
    },
    series: [
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        data: geoData,
        symbolSize: (val) => {
          const maxCount = Math.max(...data.map(p => p.count));
          return Math.max(15, Math.min(40, 15 + (val[2] / maxCount) * 25));
        },
        itemStyle: {
          color: '#ef4444',
          shadowBlur: 20,
          shadowColor: 'rgba(239, 68, 68, 0.8)'
        },
        emphasis: {
          itemStyle: {
            color: '#dc2626',
            shadowBlur: 30,
            shadowColor: 'rgba(239, 68, 68, 1)'
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

export default EChartsGeo;
