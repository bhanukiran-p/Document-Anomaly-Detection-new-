// import React, { useEffect, useState } from 'react';
// import ReactECharts from 'echarts-for-react';
// import * as echarts from 'echarts';

// // Try multiple sources for the geo JSON file
// const LOCAL_MAP_URL = `${process.env.PUBLIC_URL || ''}/custom.geo.json`;
// const BACKEND_MAP_URL = 'http://localhost:5001/custom.geo.json'; // Backend route serves this file
// const REMOTE_MAP_URL = 'https://cdn.jsdelivr.net/npm/echarts@5/map/json/world.json';
// const LOCAL_MAP_NAME = 'custom_world';

// const EChartsGeo = ({ data, title, height = 400 }) => {
//   const [mapLoaded, setMapLoaded] = useState(false);
//   const [mapName, setMapName] = useState('world');
//   const [mapError, setMapError] = useState(null);

//   useEffect(() => {
//     let isMounted = true;

//     const registerMapIfNeeded = async (url, name) => {
//       const existingMap = echarts.getMap(name);
//       if (existingMap) {
//         console.log(`Map '${name}' already registered`);
//         return;
//       }
//       console.log(`Attempting to load map from: ${url}`);
//       try {
//         const response = await fetch(url, {
//           cache: 'force-cache',
//           mode: 'cors'
//         });
//         if (!response.ok) {
//           throw new Error(`Failed to load map: ${response.status} ${response.statusText}`);
//         }
//         const geoJson = await response.json();
//         console.log(`Successfully loaded map data from ${url}, registering as '${name}'`);
//         echarts.registerMap(name, geoJson);
//         return true;
//       } catch (error) {
//         console.error(`Failed to load map from ${url}:`, error);
//         throw error;
//       }
//     };

//     const loadMapData = async () => {
//       // Try local public folder first, then backend route, then CDN
//       const sources = [
//         { url: LOCAL_MAP_URL, name: LOCAL_MAP_NAME, description: 'Local public folder' },
//         { url: BACKEND_MAP_URL, name: LOCAL_MAP_NAME, description: 'Backend API' },
//         { url: REMOTE_MAP_URL, name: 'world', description: 'CDN fallback' }
//       ];

//       for (let i = 0; i < sources.length; i++) {
//         const source = sources[i];
//         try {
//           console.log(`Trying source ${i + 1}/${sources.length}: ${source.description}`);
//           await registerMapIfNeeded(source.url, source.name);
//           if (isMounted) {
//             console.log(`Successfully loaded map: ${source.description}`);
//             setMapName(source.name);
//             setMapLoaded(true);
//             setMapError(null);
//             return; // Success, exit early
//           }
//         } catch (err) {
//           console.warn(`Source ${i + 1}/${sources.length} failed (${source.description}):`, err.message);
//           // Continue to next source
//           if (i === sources.length - 1) {
//             // Last source failed
//             console.error('All map sources failed');
//             if (isMounted) {
//               setMapError('Unable to load map data from any source. Please check your network connection.');
//               setMapLoaded(false);
//             }
//           }
//         }
//       }
//     };

//     loadMapData();

//     return () => {
//       isMounted = false;
//     };
//   }, []);

//   if (mapError) {
//     return (
//       <div style={{
//         height: `${height}px`,
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         color: '#f87171',
//         fontSize: '0.9rem'
//       }}>
//         {mapError}
//       </div>
//     );
//   }

//   if (!mapLoaded) {
//     return (
//       <div style={{
//         height: `${height}px`,
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         color: '#94a3b8',
//         fontSize: '0.9rem'
//       }}>
//         Loading map data...
//       </div>
//     );
//   }

//   // Validate and convert data
//   if (!data || !Array.isArray(data) || data.length === 0) {
//     console.warn('EChartsGeo: No data provided');
//     return (
//       <div style={{
//         height: `${height}px`,
//         display: 'flex',
//         alignItems: 'center',
//         justifyContent: 'center',
//         color: '#94a3b8',
//         fontSize: '0.9rem'
//       }}>
//         No location data available
//       </div>
//     );
//   }

//   console.log('EChartsGeo: Processing data points:', data.length);

//   // Convert lat/lng to ECharts format with validation
//   const geoData = data
//     .filter(point => {
//       if (!point || typeof point !== 'object') {
//         console.warn('EChartsGeo: Invalid point data', point);
//         return false;
//       }
//       if (point.lng == null || point.lat == null) {
//         console.warn('EChartsGeo: Point missing coordinates', point);
//         return false;
//       }
//       const lng = parseFloat(point.lng);
//       const lat = parseFloat(point.lat);
//       if (isNaN(lng) || isNaN(lat)) {
//         console.warn('EChartsGeo: Invalid coordinates', point);
//         return false;
//       }
//       // Validate coordinate ranges
//       if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
//         console.warn('EChartsGeo: Coordinates out of range', { lat, lng, point });
//         return false;
//       }
//       return true;
//     })
//     .map(point => {
//       const city = point.city || 'Unknown';
//       const country = point.country || 'Unknown';
//       const count = point.count != null ? parseFloat(point.count) || 0 : 0;
//       return {
//         name: `${city}, ${country}`,
//         value: [
//           parseFloat(point.lng),
//           parseFloat(point.lat),
//           count
//         ],
//         itemStyle: {
//           color: '#ef4444'
//         }
//       };
//     });

//   console.log('EChartsGeo: Valid data points after filtering:', geoData.length);

//   if (geoData.length === 0) {
//     return (
//       <div style={{
//         height: `${height}px`,
//         display: 'flex',
//         flexDirection: 'column',
//         alignItems: 'center',
//         justifyContent: 'center',
//         color: '#94a3b8',
//         fontSize: '0.9rem'
//       }}>
//         <div>No valid location data available</div>
//         <div style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: '#64748b' }}>
//           {data.length} data point(s) provided but none had valid coordinates
//         </div>
//       </div>
//     );
//   }

//   // Calculate symbol sizes ahead of time to avoid issues in formatter
//   const counts = geoData.map(p => (p.value && p.value[2]) || 0).filter(c => c > 0);
//   const maxCount = counts.length > 0 ? Math.max(...counts) : 1;

//   const option = {
//     title: {
//       text: title,
//       left: 'center',
//       top: 10,
//       textStyle: {
//         color: '#e2e8f0',
//         fontSize: 14,
//         fontWeight: 600
//       }
//     },
//     tooltip: {
//       trigger: 'item',
//       formatter: (params) => {
//         try {
//           if (!params || !params.value) return '';
//           const value = params.value;
//           if (Array.isArray(value) && value.length >= 3) {
//             const name = params.name || 'Unknown';
//             const count = value[2] || 0;
//             return `<strong>${name}</strong><br/>Transactions: ${count}`;
//           }
//           return params.name || 'Unknown';
//         } catch (e) {
//           console.error('Tooltip formatter error:', e);
//           return '';
//         }
//       },
//       backgroundColor: 'rgba(30, 41, 59, 0.95)',
//       borderColor: '#334155',
//       textStyle: {
//         color: '#e2e8f0'
//       }
//     },
//     geo: {
//       map: mapName,
//       roam: true,
//       selectedMode: false,  // Completely disable selection
//       itemStyle: {
//         areaColor: '#1e293b',
//         borderColor: '#475569'
//       },
//       emphasis: {
//         disabled: true,
//         itemStyle: {
//           areaColor: '#1e293b'
//         },
//         label: {
//           show: false
//         }
//       },
//       select: {
//         disabled: true
//       },
//       top: '15%',
//       bottom: '10%',
//       silent: true,  // Disable mouse events on the map itself
//       regions: []  // Empty regions to prevent region data access
//     },
//     series: [
//       {
//         name: 'Fraud Hotspots',
//         type: 'scatter',
//         coordinateSystem: 'geo',
//         data: geoData,
//         symbolSize: function(val) {
//           try {
//             if (!val || !Array.isArray(val) || val.length < 3) {
//               return 15;
//             }
//             const currentCount = val[2] || 0;
//             if (maxCount === 0) return 15;
//             return Math.max(15, Math.min(40, 15 + (currentCount / maxCount) * 25));
//           } catch (e) {
//             console.error('symbolSize error:', e);
//             return 15;
//           }
//         },
//         itemStyle: {
//           color: '#ef4444',
//           shadowBlur: 20,
//           shadowColor: 'rgba(239, 68, 68, 0.8)'
//         },
//         emphasis: {
//           focus: 'self',
//           itemStyle: {
//             color: '#dc2626',
//             shadowBlur: 30,
//             shadowColor: 'rgba(239, 68, 68, 1)',
//             borderColor: '#fff',
//             borderWidth: 2
//           },
//           scale: 1.2
//         },
//         zlevel: 2,
//         silent: false  // Enable mouse events on scatter points
//       }
//     ],
//     animation: true,
//     animationDuration: 1000,
//     animationEasing: 'cubicOut'
//   };

//   console.log('EChartsGeo: Rendering chart with config:', {
//     mapName,
//     dataPoints: geoData.length,
//     maxCount,
//     sampleData: geoData[0]
//   });

//   return (
//     <div
//       style={{ height: `${height}px`, width: '100%', position: 'relative' }}
//       className="echarts-geo-container"
//     >
//       <ReactECharts
//         option={option}
//         style={{ height: '100%', width: '100%', position: 'relative', zIndex: 2 }}
//         opts={{
//           renderer: 'canvas',
//           locale: 'en',
//           useDirtyRect: false
//         }}
//         notMerge={false}
//         lazyUpdate={false}
//       />
//     </div>
//   );
// };

// export default EChartsGeo;

































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
          console.warn(`Map fetch failed from ${url}: ${response.status} ${response.statusText}`);
          throw new Error(`Map fetch failed: ${response.status}`);
        }
        const geoJson = await response.json();
        if (!geoJson || typeof geoJson !== 'object' || !geoJson.features) {
          console.error('Invalid geoJSON format from', url);
          throw new Error('Invalid geoJSON format');
        }

        echarts.registerMap(name, geoJson);
        console.log(`Map '${name}' registered successfully`);

        if (isMounted) {
          setMapName(name);
          setMapLoaded(true);
          setMapError(null);
        }
      } catch (error) {
        console.error(`Failed to load map from ${url}:`, error);
        throw error;
      }
    };

    const loadMapData = async () => {
      const sources = [
        { url: LOCAL_MAP_URL, name: LOCAL_MAP_NAME },
        { url: BACKEND_MAP_URL, name: LOCAL_MAP_NAME },
        { url: REMOTE_MAP_URL, name: 'world' }
      ];

      for (let i = 0; i < sources.length; i++) {
        const { url, name } = sources[i];
        try {
          await registerMapIfNeeded(url, name);
          console.log(`Using map source: ${url}`);
          if (isMounted) {
            setMapName(name);
            setMapLoaded(true);
            setMapError(null);
          }
          break;
        } catch (error) {
          console.warn(`Map source failed: ${url}`, error);
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
      return true;
    })
    .map(point => {
      const lng = parseFloat(point.lng);
      const lat = parseFloat(point.lat);
      const count = parseInt(point.count || point.value || 0, 10);

      return {
        name: point.city || point.location || `${lat.toFixed(2)}, ${lng.toFixed(2)}`,
        value: [lng, lat, isNaN(count) ? 0 : count],
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(15, 23, 42, 0.8)'
        }
      };
    });

  if (!geoData || geoData.length === 0) {
    console.warn('EChartsGeo: No valid data points after processing');
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

  // Calculate symbol sizes and colors ahead of time
  const counts = geoData.map(p => (p.value && p.value[2]) || 0).filter(c => c > 0);
  const maxCount = counts.length > 0 ? Math.max(...counts) : 1;
  const minCount = counts.length > 0 ? Math.min(...counts) : 0;

  // Function to get color based on transaction count
  const getColorByCount = (count) => {
    const normalized = maxCount > minCount ? (count - minCount) / (maxCount - minCount) : 0.5;

    if (normalized > 0.75) return '#dc2626'; // High: Dark red
    if (normalized > 0.5) return '#ef4444';  // Medium-high: Red
    if (normalized > 0.25) return '#f97316'; // Medium: Orange
    return '#fb923c';                         // Low: Light orange
  };

  const option = {
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove|click',
      confine: true,
      formatter: (params) => {
        try {
          // Only show tooltip for scatter series data, not geo map
          if (!params) return '';
          if (params.componentType !== 'series') return '';
          if (params.seriesType !== 'scatter') return '';
          if (!params.data) return '';
          if (!params.value || !Array.isArray(params.value)) return '';

          const value = params.value;
          if (value.length >= 3) {
            const name = params.name || 'Unknown';
            const count = value[2] || 0;
            return `<strong>${name}</strong><br/>Transactions: ${count}`;
          }
          return '';
        } catch (e) {
          console.error('Tooltip formatter error:', e);
          return '';
        }
      },
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: '#1e293b',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    geo: {
      map: mapName,
      roam: true,
      zoom: 1.3,
      center: [0, 20],
      label: {
        show: false
      },
      itemStyle: {
        areaColor: '#0a0f1e',
        borderColor: '#1e293b',
        borderWidth: 0.8
      },
      emphasis: {
        disabled: true,
        itemStyle: {
          areaColor: '#0a0f1e'
        },
        label: {
          show: false
        }
      },
      select: {
        disabled: true,
        itemStyle: {
          areaColor: '#0a0f1e'
        }
      },
      selectedMode: false,
      top: '5%',
      bottom: '8%',
      silent: true
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
              return 12;
            }
            const currentCount = val[2] || 0;
            if (maxCount === 0) return 12;

            // More pronounced size differences
            const normalized = (currentCount - minCount) / (maxCount - minCount || 1);
            return Math.max(12, Math.min(50, 12 + normalized * 38));
          } catch (e) {
            console.error('symbolSize error:', e);
            return 12;
          }
        },
        itemStyle: {
          color: function(params) {
            try {
              if (!params || !params.value || !Array.isArray(params.value)) {
                return '#fb923c';
              }
              const count = params.value[2] || 0;
              return getColorByCount(count);
            } catch (e) {
              console.error('Color error:', e);
              return '#fb923c';
            }
          },
          opacity: 0.85,
          shadowBlur: 8,
          shadowColor: 'rgba(220, 38, 38, 0.4)',
          borderColor: 'rgba(255, 255, 255, 0.3)',
          borderWidth: 1
        },
        emphasis: {
          scale: 1.3,
          itemStyle: {
            opacity: 1,
            shadowBlur: 15,
            shadowColor: 'rgba(220, 38, 38, 0.8)',
            borderColor: '#fff',
            borderWidth: 2
          }
        }
      }
    ],
    visualMap: {
      show: true,
      min: minCount,
      max: maxCount,
      text: ['High', 'Low'],
      realtime: false,
      calculable: false,
      inRange: {
        color: ['#fb923c', '#f97316', '#ef4444', '#dc2626']
      },
      textStyle: {
        color: '#94a3b8',
        fontSize: 11
      },
      orient: 'horizontal',
      left: 'center',
      bottom: '2%',
      itemWidth: 20,
      itemHeight: 10,
      formatter: function(value) {
        return Math.round(value);
      }
    }
  };

  console.log('EChartsGeo: Final option prepared:', {
    mapName,
    dataPoints: geoData.length,
    maxCount,
    sampleData: geoData[0]
  });

  const onEvents = {
    // Prevent errors from geo component interactions
    click: (params) => {
      try {
        if (params && params.componentType === 'series' && params.seriesType === 'scatter') {
          console.log('Clicked scatter point:', params.name);
        }
      } catch (e) {
        // Silently ignore click errors
      }
    },
    mousemove: (params) => {
      try {
        // Only handle mousemove for scatter points, not geo regions
        if (!params || params.componentType !== 'series' || params.seriesType !== 'scatter') {
          return false; // Stop propagation for non-scatter elements
        }
      } catch (e) {
        return false;
      }
    }
  };

  return (
    <div
      style={{ height: `${height}px`, width: '100%', position: 'relative' }}
      className="echarts-geo-container"
    >
      <ReactECharts
        option={option}
        style={{ height: '100%', width: '100%', position: 'relative', zIndex: 2 }}
        opts={{
          renderer: 'canvas',
          locale: 'en',
          useDirtyRect: false
        }}
        onEvents={onEvents}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
};

export default EChartsGeo;
