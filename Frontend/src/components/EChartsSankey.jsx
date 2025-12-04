import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsSankey = ({ data, title, height = 400 }) => {
  const rawNodes = Array.isArray(data?.nodes) ? data.nodes : [];
  const rawLinks = Array.isArray(data?.links) ? data.links : [];

  if (rawNodes.length === 0 || rawLinks.length === 0) {
    return (
      <div
        style={{
          height: `${height}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#94a3b8',
          fontSize: '0.9rem'
        }}
      >
        No flow data available
      </div>
    );
  }

  // Color palette
  const colors = [
    '#10b981', '#3b82f6', '#8b5cf6', '#ec4899',
    '#f59e0b', '#ef4444', '#06b6d4', '#14b8a6'
  ];

  const resolveNodeName = (nodeRef) => {
    if (typeof nodeRef === 'number') {
      return rawNodes[nodeRef]?.name ?? `node_${nodeRef}`;
    }
    return nodeRef;
  };

  // Normalize node data with colors
  const formattedNodes = rawNodes.map((node, index) => {
    const name = node.name || `node_${index}`;
    return {
      name,
      itemStyle: {
        color: node.nodeColor || colors[index % colors.length],
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        color: '#e2e8f0',
        fontWeight: 600
      }
    };
  });

  const nodeColorMap = formattedNodes.reduce((map, node) => {
    map[node.name] = node.itemStyle.color;
    return map;
  }, {});

  const nodeNameSet = new Set(formattedNodes.map(node => node.name));

  // Format links with colors
  const formattedLinks = rawLinks.map(link => {
    const sourceName = resolveNodeName(link.source);
    const targetName = resolveNodeName(link.target);
    if (!nodeNameSet.has(sourceName) || !nodeNameSet.has(targetName)) {
      return null;
    }
    return {
      source: sourceName,
      target: targetName,
      value: link.value,
      lineStyle: {
        color: link.color || nodeColorMap[sourceName] || colors[0],
        opacity: 0.4
      }
    };
  }).filter(Boolean);

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 41, 59, 0.95)',
      borderColor: '#334155',
      textStyle: {
        color: '#e2e8f0'
      }
    },
    series: [
      {
        type: 'sankey',
        data: formattedNodes,
        links: formattedLinks,
        emphasis: {
          focus: 'adjacency'
        },
        lineStyle: {
          curveness: 0.5
        },
        label: {
          fontSize: 12,
          fontWeight: 600
        },
        left: '5%',
        right: '20%',
        top: '5%',
        bottom: '10%',
        nodeWidth: 20,
        nodeGap: 12
      }
    ],
    animation: true,
    animationDuration: 1000,
    animationEasing: 'cubicOut'
  };

  return (
    <div style={{ width: '100%' }}>
      <ReactECharts
        option={option}
        style={{ height: `${height}px`, width: '100%' }}
        opts={{ renderer: 'canvas' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
};

export default EChartsSankey;
