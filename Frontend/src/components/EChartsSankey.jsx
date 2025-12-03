import React from 'react';
import ReactECharts from 'echarts-for-react';

const EChartsSankey = ({ data, title, height = 400 }) => {
  const { nodes = [], links = [] } = data || {};

  // Color palette
  const colors = [
    '#10b981', '#3b82f6', '#8b5cf6', '#ec4899',
    '#f59e0b', '#ef4444', '#06b6d4', '#14b8a6'
  ];

  const resolveNodeName = (nodeRef) => {
    if (typeof nodeRef === 'number') {
      return nodes[nodeRef]?.name ?? `node_${nodeRef}`;
    }
    return nodeRef;
  };

  // Normalize node data with colors
  const formattedNodes = nodes.map((node, index) => {
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
  const formattedLinks = links.map(link => {
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
        top: '15%',
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
      {/* Legend */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '0.5rem',
        marginTop: '1rem',
        justifyContent: 'center'
      }}>
        {formattedNodes.map((node, idx) => (
          <div key={idx} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.25rem 0.75rem',
            backgroundColor: '#1e293b',
            borderRadius: '0.5rem',
            border: `2px solid ${node.itemStyle.color}`,
            fontSize: '0.85rem',
            fontWeight: 600,
            color: '#e2e8f0'
          }}>
            <div style={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: node.itemStyle.color
            }} />
            {node.name}
          </div>
        ))}
      </div>
    </div>
  );
};

export default EChartsSankey;
