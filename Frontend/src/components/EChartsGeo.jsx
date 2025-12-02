import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';

// Try multiple sources for the geo JSON file
const LOCAL_MAP_URL = `${process.env.PUBLIC_URL || ''}/custom.geo.json`;
const BACKEND_MAP_URL = 'http://localhost:5001/custom.geo.json'; // Backend route serves this file
const REMOTE_MAP_URL = 'https://cdn.jsdelivr.net/npm/echarts@5/map/json/world.json';
const LOCAL_MAP_NAME = 'custom_world';

const EChartsGeo = ({ data, title, height = 400 }) => {
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapName, setMapName] = useState('world');
  const [mapError, setMapError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const registerMapIfNeeded = async (url, name) => {
      const existingMap = echarts.getMap(name);
      if (existingMap) {
        console.log(`Map '${name}' already registered`);
        return;
      }
      console.log(`Attempting to load map from: ${url}`);
      try {
        const response = await fetch(url, {
          cache: 'force-cache',
          mode: 'cors'
        });
        if (!response.ok) {
          throw new Error(`Failed to load map: ${response.status} ${response.statusText}`);
        }
        const geoJson = await response.json();
        console.log(`Successfully loaded map data from ${url}, registering as '${name}'`);
        echarts.registerMap(name, geoJson);
        return true;
      } catch (error) {
        console.error(`Failed to load map from ${url}:`, error);
        throw error;
      }
    };

    const loadMapData = async () => {
      // Try local public folder first, then backend route, then CDN
      const sources = [
        { url: LOCAL_MAP_URL, name: LOCAL_MAP_NAME, description: 'Local public folder' },
        { url: BACKEND_MAP_URL, name: LOCAL_MAP_NAME, description: 'Backend API' },
        { url: REMOTE_MAP_URL, name: 'world', description: 'CDN fallback' }
      ];

      for (let i = 0; i < sources.length; i++) {
        const source = sources[i];
        try {
          console.log(`Trying source ${i + 1}/${sources.length}: ${source.description}`);
          await registerMapIfNeeded(source.url, source.name);
          if (isMounted) {
            console.log(`Successfully loaded map: ${source.description}`);
            setMapName(source.name);
            setMapLoaded(true);
            setMapError(null);
            return; // Success, exit early
          }
        } catch (err) {
          console.warn(`Source ${i + 1}/${sources.length} failed (${source.description}):`, err.message);
          // Continue to next source
          if (i === sources.length - 1) {
            // Last source failed
            console.error('All map sources failed');
            if (isMounted) {
              setMapError('Unable to load map data from any source. Please check your network connection.');
              setMapLoaded(false);
            }
          }
        }
      }
    };

    loadMapData();

    return () => {
      isMounted = false;
    };
  }, []);

  if (mapError) {
    return (
      <div style={{
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#f87171',
        fontSize: '0.9rem'
      }}>
        {mapError}
      </div>
    );
  }

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
        Loading map data...
      </div>
    );
  }

  // Validate and convert data
  if (!data || !Array.isArray(data) || data.length === 0) {
    console.warn('EChartsGeo: No data provided');
    return (
      <div style={{
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#94a3b8',
        fontSize: '0.9rem'
      }}>
        No location data available
      </div>
    );
  }

  console.log('EChartsGeo: Processing data points:', data.length);

  // Convert lat/lng to ECharts format with validation
  const geoData = data
    .filter(point => {
      if (!point || typeof point !== 'object') {
        console.warn('EChartsGeo: Invalid point data', point);
        return false;
      }
      if (point.lng == null || point.lat == null) {
        console.warn('EChartsGeo: Point missing coordinates', point);
        return false;
      }
      const lng = parseFloat(point.lng);
      const lat = parseFloat(point.lat);
      if (isNaN(lng) || isNaN(lat)) {
        console.warn('EChartsGeo: Invalid coordinates', point);
        return false;
      }
      // Validate coordinate ranges
      if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
        console.warn('EChartsGeo: Coordinates out of range', { lat, lng, point });
        return false;
      }
      return true;
    })
    .map(point => {
      const city = point.city || 'Unknown';
      const country = point.country || 'Unknown';
      const count = point.count != null ? parseFloat(point.count) || 0 : 0;
      return {
        name: `${city}, ${country}`,
        value: [
          parseFloat(point.lng),
          parseFloat(point.lat),
          count
        ],
        itemStyle: {
          color: '#ef4444'
        }
      };
    });

  console.log('EChartsGeo: Valid data points after filtering:', geoData.length);

  if (geoData.length === 0) {
    return (
      <div style={{
        height: `${height}px`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#94a3b8',
        fontSize: '0.9rem'
      }}>
        <div>No valid location data available</div>
        <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: '#64748b' }}>
          {data.length} data point(s) provided but none had valid coordinates
        </div>
      </div>
    );
  }

  // Calculate symbol sizes ahead of time to avoid issues in formatter
  const counts = geoData.map(p => (p.value && p.value[2]) || 0).filter(c => c > 0);
  const maxCount = counts.length > 0 ? Math.max(...counts) : 1;

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
        try {
          if (!params || !params.value) return '';
          const value = params.value;
          if (Array.isArray(value) && value.length >= 3) {
            const name = params.name || 'Unknown';
            const count = value[2] || 0;
            return `<strong>${name}</strong><br/>Transactions: ${count}`;
          }
          return params.name || 'Unknown';
        } catch (e) {
          console.error('Tooltip formatter error:', e);
          return '';
        }
      },
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    geo: {
      map: mapName,
      roam: true,
      selectedMode: false,  // Completely disable selection
      itemStyle: {
        areaColor: '#1e293b',
        borderColor: '#475569'
      },
      emphasis: {
        disabled: true,
        itemStyle: {
          areaColor: '#1e293b'
        },
        label: {
          show: false
        }
      },
      select: {
        disabled: true
      },
      top: '15%',
      bottom: '10%',
      silent: true  // Disable mouse events on the map itself
    },
    series: [
      {
        name: 'Fraud Hotspots',
        type: 'scatter',
        coordinateSystem: 'geo',
        data: geoData,
        symbolSize: function(val) {
          try {
            if (!val || !Array.isArray(val) || val.length < 3) {
              return 15;
            }
            const currentCount = val[2] || 0;
            if (maxCount === 0) return 15;
            return Math.max(15, Math.min(40, 15 + (currentCount / maxCount) * 25));
          } catch (e) {
            console.error('symbolSize error:', e);
            return 15;
          }
        },
        itemStyle: {
          color: '#ef4444',
          shadowBlur: 20,
          shadowColor: 'rgba(239, 68, 68, 0.8)'
        },
        emphasis: {
          focus: 'self',
          itemStyle: {
            color: '#dc2626',
            shadowBlur: 30,
            shadowColor: 'rgba(239, 68, 68, 1)',
            borderColor: '#fff',
            borderWidth: 2
          },
          scale: 1.2
        },
        zlevel: 2,
        silent: false  // Enable mouse events on scatter points
      }
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut'
  };

  console.log('EChartsGeo: Rendering chart with config:', {
    mapName,
    dataPoints: geoData.length,
    maxCount,
    sampleData: geoData[0]
  });

  return (
    <div
      style={{ height: `${height}px`, width: '100%', position: 'relative' }}
      className="echarts-geo-container"
    >
      <style>{`
        .echarts-geo-container .echarts-for-react div[_echarts_instance_] svg path[name] {
          pointer-events: none !important;
        }
        .echarts-geo-container .echarts-for-react div[_echarts_instance_] svg g[clip-path] path {
          pointer-events: none !important;
        }
      `}</style>
      <ReactECharts
        option={option}
        style={{ height: '100%', width: '100%' }}
        opts={{
          renderer: 'canvas',
          locale: 'en',
          useDirtyRect: false
        }}
        notMerge={false}
        lazyUpdate={false}
        onChartReady={(chartInstance) => {
          console.log('EChartsGeo: Chart ready');

          // Completely disable all map interactions
          try {
            // Override the getDataParams method to prevent errors
            const originalGetDataParams = chartInstance.getModel().getComponent('geo', 0).getDataParams;
            if (originalGetDataParams) {
              chartInstance.getModel().getComponent('geo', 0).getDataParams = function() {
                return null;
              };
            }
          } catch (e) {
            console.warn('Could not override getDataParams:', e);
          }

          // Disable all event handlers on the geo component
          try {
            chartInstance.off('click');
            chartInstance.off('mouseover');
            chartInstance.off('mouseout');
            chartInstance.off('mousemove');
          } catch (e) {
            console.warn('Could not disable event handlers:', e);
          }
        }}
        onEvents={{
          // Prevent all events from bubbling
          click: (params) => {
            if (params.componentType === 'geo') {
              return false;
            }
          },
          mouseover: (params) => {
            if (params.componentType === 'geo') {
              return false;
            }
          },
          mouseout: (params) => {
            if (params.componentType === 'geo') {
              return false;
            }
          }
        }}
      />
    </div>
  );
};

export default EChartsGeo;
