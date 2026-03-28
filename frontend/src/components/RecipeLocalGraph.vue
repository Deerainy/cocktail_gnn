<template>
  <div class="recipe-local-graph">
    <div class="graph-header">
      <h3 class="graph-title">结构解释图</h3>
      <div class="graph-controls">
        <button 
          v-for="layer in graphLayers" 
          :key="layer.value"
          :class="['graph-control-btn', { active: graphLayer === layer.value }]"
          @click="switchGraphLayer(layer.value)"
        >
          {{ layer.label }}
        </button>
        <div class="graph-control-separator"></div>
        <div class="graph-control-separator"></div>
        <button 
          :class="['graph-control-btn', { active: showOnlyKeyNodes }]"
          @click="toggleKeyNodes"
        >
          只看关键节点
        </button>
        <div class="graph-control-separator"></div>
        <button 
          :class="['graph-control-btn', { active: showEnglish }]"
          @click="toggleLanguage"
        >
          {{ showEnglish ? '中文' : 'English' }}
        </button>
      </div>
    </div>
    <div class="graph-info">
      <div class="info-item">
        <span class="info-label">图表说明：</span>
        <span class="info-text">节点大小表示贡献比例，颜色表示角色类型，金色边框为关键节点</span>
      </div>
      <div class="info-item">
        <span class="info-label">关系类型：</span>
        <span class="info-text">
          <span class="info-tag" style="background-color: #d4af37;">兼容</span> - 成分之间搭配和谐
          <span class="info-tag" style="background-color: #66a3ff;">共现</span> - 经常一起使用
          <span class="info-tag" style="background-color: #4bc0c0;">风味</span> - 风味互补
        </span>
      </div>
      <div class="info-item">
        <span class="info-label">角色类型：</span>
        <span class="info-text">
          <span class="info-tag" style="background-color: #d4af37;">基酒</span>
          <span class="info-tag" style="background-color: #ff9f40;">酸味剂</span>
          <span class="info-tag" style="background-color: #66a3ff;">甜味剂</span>
          <span class="info-tag" style="background-color: #4bc0c0;">苦味剂</span>
          <span class="info-tag" style="background-color: #9966ff;">修饰剂</span>
          <span class="info-tag" style="background-color: #ff6384;">装饰</span>
        </span>
      </div>
    </div>
    <div class="graph-container">
      <div ref="chartRef" style="width: 100%; height: 100%;"></div>
    </div>
    <div v-if="selectedNode" class="node-detail-panel">
      <h4 class="detail-title">{{ selectedNode.text }}</h4>
      <div class="detail-metrics">
        <div class="metric-row">
          <span class="metric-label">角色</span>
          <span class="metric-value">{{ getRoleLabel(selectedNode.role) }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">贡献比例</span>
          <span class="metric-value">{{ ((selectedNode.contribution_ratio || 0) * 100).toFixed(0) }}%</span>
        </div>
        <div class="metric-row" v-if="selectedNode.synergy_contrib !== undefined && selectedNode.synergy_contrib >= 0">
          <span class="metric-label">协同性</span>
          <span class="metric-value">{{ (selectedNode.synergy_contrib || 0).toFixed(2) }}</span>
        </div>
        <div class="metric-row" v-if="selectedNode.conflict_contrib !== undefined && selectedNode.conflict_contrib >= 0">
          <span class="metric-label">冲突度</span>
          <span class="metric-value">{{ (selectedNode.conflict_contrib || 0).toFixed(2) }}</span>
        </div>
        <div class="metric-row" v-if="selectedNode.balance_contrib !== undefined && selectedNode.balance_contrib >= 0">
          <span class="metric-label">平衡性</span>
          <span class="metric-value">{{ (selectedNode.balance_contrib || 0).toFixed(2) }}</span>
        </div>
      </div>
      <div class="detail-explanation" v-if="selectedNode.explanation">
        <h5 class="explanation-title">说明</h5>
        <p class="explanation-text">{{ selectedNode.explanation }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';

export default defineComponent({
  name: 'RecipeLocalGraph',
  props: {
    graphData: {
      type: Object,
      default: () => ({ nodes: [], edges: [] })
    },
    ingredients: {
      type: Array,
      default: () => []
    }
  },
  emits: ['node-click', 'view-substitutes'],
  setup(props, { emit }) {
    const chartRef = ref(null);
    const chart = ref(null);
    const graphLayer = ref('mixed');
    const showOnlyKeyNodes = ref(false);
    const selectedNode = ref(null);
    const showEnglish = ref(false);
    
    const graphLayers = [
      { label: '兼容性', value: 'compat' },
      { label: '共现性', value: 'cooccur' },
      { label: '风味', value: 'flavor' },
      { label: '混合', value: 'mixed' }
    ];
    
    const getFilteredData = () => {
      if (!props.graphData) {
        return { nodes: [], edges: [] };
      }
      
      // 创建 ingredients 映射表，只使用 canonical_id
      const ingredientMap = new Map();
      (props.ingredients || []).forEach(ingredient => {
        if (ingredient.ingredient && ingredient.ingredient.canonical_id) {
          const canonicalId = String(ingredient.ingredient.canonical_id);
          ingredientMap.set(canonicalId, ingredient.ingredient);
        }
      });
      
      console.log('Ingredients:', props.ingredients);
      console.log('Ingredient Map:', Array.from(ingredientMap.entries()));
      
      let nodes = (props.graphData.nodes || [])
        .filter(node => node && node.id !== undefined && node.id !== null)
        .map(node => {
          // 从 ingredients 中获取名称
          const nodeId = String(node.id);
          const ingredient = ingredientMap.get(nodeId);
          
          // 尝试多种字段获取中文名称
          const chineseName = ingredient?.canonical_name_zh || node.ingredient_name_zh || node.label_zh || node.name_zh;
          // 尝试多种字段获取英文名称
          const englishName = ingredient?.canonical_name || node.ingredient_name || node.label || node.name;
          
          // 参考 VisualizationView.vue 的显示方式：中文 / 英文
          let displayText = '';
          if (chineseName && englishName) {
            displayText = `${chineseName} / ${englishName}`;
          } else if (chineseName) {
            displayText = chineseName;
          } else if (englishName) {
            displayText = englishName;
          } else {
            displayText = node.name || node.label || `Node ${nodeId}`;
          }
          
          console.log('Node ID:', nodeId);
          console.log('Ingredient for node:', ingredient);
          console.log('Chinese Name:', chineseName);
          console.log('English Name:', englishName);
          console.log('Display Text:', displayText);
          
          return {
            id: nodeId,
            text: displayText,
            role: node.role || 'other',
            contribution_ratio: node.contribution_ratio || 0,
            synergy_contrib: node.synergy_contrib,
            conflict_contrib: node.conflict_contrib,
            balance_contrib: node.balance_contrib,
            explanation: node.explanation,
            is_key_node: node.is_key_node || false
          };
        });
      
      let edges = (props.graphData.edges || [])
        .filter(edge => edge && edge.source !== undefined && edge.source !== null && edge.target !== undefined && edge.target !== null)
        .map(edge => ({
          source: String(edge.source),
          target: String(edge.target),
          type: edge.type || 'compat',
          weight: edge.weight || 0
        }));
      
      if (showOnlyKeyNodes.value) {
        nodes = nodes.filter(node => node.is_key_node);
        const keyNodeIds = nodes.map(node => node.id);
        edges = edges.filter(edge => 
          edge.source && edge.target && 
          keyNodeIds.includes(edge.source) && keyNodeIds.includes(edge.target)
        );
      }
      
      if (graphLayer.value !== 'mixed') {
        const filteredEdges = edges.filter(edge => 
          edge.type === graphLayer.value && 
          edge.source && edge.target
        );
        edges = filteredEdges.length > 0 ? filteredEdges : edges;
      }
      
      console.log('过滤后 nodes:', nodes);
      console.log('过滤后 edges:', edges);
      
      return { nodes, edges };
    };
    
    const getNodeColor = (node) => {
      const colors = {
        'base': '#d4af37',
        'base_spirit': '#d4af37',
        'acid': '#ff9f40',
        'sweetener': '#66a3ff',
        'bitter': '#4bc0c0',
        'bitters': '#4bc0c0',
        'modifier': '#9966ff',
        'garnish': '#ff6384',
        'other': '#8c8c8c'
      };
      return colors[node.role] || colors['other'];
    };
    
    const getEdgeColor = (edge) => {
      const colors = {
        'compat': '#d4af37',
        'cooccur': '#66a3ff',
        'flavor': '#4bc0c0',
        'mixed': '#9966ff'
      };
      return colors[edge.type] || colors['compat'];
    };
    
    const getEdgeWidth = (edge) => {
      const weight = edge.weight || 0;
      return 1 + Math.min(weight * 3, 3);
    };
    
    const getEdgeLabel = (edge) => {
      const typeLabels = {
        'compat': '兼容',
        'cooccur': '共现',
        'flavor': '风味',
        'mixed': '混合'
      };
      const typeLabel = typeLabels[edge.type] || edge.type;
      const weight = edge.weight || 0;
      if (weight < 0) return '';
      return `${typeLabel}: ${weight.toFixed(2)}`;
    };
    
    const getRoleLabel = (role) => {
      const labels = {
        'base': '基酒',
        'base_spirit': '基酒',
        'acid': '酸味剂',
        'sweetener': '甜味剂',
        'bitter': '苦味剂',
        'bitters': '苦味剂',
        'modifier': '修饰剂',
        'garnish': '装饰',
        'other': '其他'
      };
      return labels[role] || labels['other'];
    };
    
    const initChart = () => {
      if (chart.value) {
        chart.value.dispose();
      }
      
      if (chartRef.value) {
        chart.value = echarts.init(chartRef.value);
        updateChart();
        
        // 监听点击事件
        chart.value.on('click', (params) => {
          if (params.dataType === 'node') {
            const node = params.data;
            selectedNode.value = {
              id: node.id,
              text: node.name,
              role: node.role,
              contribution_ratio: node.contribution_ratio,
              synergy_contrib: node.synergy_contrib,
              conflict_contrib: node.conflict_contrib,
              balance_contrib: node.balance_contrib,
              explanation: node.explanation,
              is_key_node: node.is_key_node
            };
            emit('node-click', selectedNode.value);
          }
        });
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => {
          chart.value?.resize();
        });
      }
    };
    
    const updateChart = () => {
      const { nodes, edges } = getFilteredData();
      
      if (!chart.value) return;
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(25, 25, 25, 0.9)',
          borderColor: 'rgba(212, 175, 55, 0.5)',
          borderWidth: 1,
          textStyle: {
            color: '#ffffff',
            fontSize: 12
          },
          formatter: (params) => {
            if (params.dataType === 'node') {
              const node = params.data;
              return `
                <div style="font-weight: bold; margin-bottom: 8px; color: ${getNodeColor(node)}">${node.name}</div>
                <div style="margin-bottom: 4px;">角色: ${getRoleLabel(node.role)}</div>
                <div style="margin-bottom: 4px;">贡献比例: ${((node.contribution_ratio || 0) * 100).toFixed(0)}%</div>
                ${node.is_key_node ? '<div style="color: #d4af37;">关键节点</div>' : ''}
              `;
            } else if (params.dataType === 'edge') {
              const edge = params.data;
              const typeExplanations = {
                'compat': '成分之间搭配和谐',
                'cooccur': '经常一起使用',
                'flavor': '风味互补',
                'mixed': '混合关系'
              };
              const explanation = typeExplanations[edge.type] || '关系';
              return `
                <div style="font-weight: bold; margin-bottom: 8px; color: ${getEdgeColor(edge)}">${getEdgeLabel(edge)}</div>
                <div style="font-size: 11px; color: #cccccc;">${explanation}</div>
              `;
            }
            return '';
          }
        },
        series: [{
          type: 'graph',
          layout: 'force',
          data: nodes.map(node => ({
            id: node.id,
            name: node.text || 'Unnamed',
            value: node.contribution_ratio || 0,
            symbolSize: 25 + (node.contribution_ratio || 0) * 30,
            itemStyle: {
              color: getNodeColor(node),
              borderColor: node.is_key_node ? '#d4af37' : 'rgba(212, 175, 55, 0.3)',
              borderWidth: node.is_key_node ? 3 : 1,
              shadowColor: node.is_key_node ? '#d4af37' : 'rgba(0, 0, 0, 0.3)',
              shadowBlur: node.is_key_node ? 15 : 5
            },
            label: {
              show: true,
              position: 'right',
              formatter: '{b}',
              fontSize: 14,
              color: '#ffffff',
              fontWeight: node.is_key_node ? 'bold' : 'normal',
              textShadowColor: 'rgba(0, 0, 0, 0.8)',
              textShadowBlur: 3
            },
            role: node.role,
            contribution_ratio: node.contribution_ratio,
            synergy_contrib: node.synergy_contrib,
            conflict_contrib: node.conflict_contrib,
            balance_contrib: node.balance_contrib,
            explanation: node.explanation,
            is_key_node: node.is_key_node
          })),
          links: edges.map((edge, index) => ({
            source: edge.source,
            target: edge.target,
            label: {
              show: true,
              formatter: getEdgeLabel(edge),
              fontSize: 9,
              color: '#cccccc',
              backgroundColor: 'rgba(25, 25, 25, 0.7)',
              borderColor: getEdgeColor(edge),
              borderWidth: 1,
              padding: [2, 4, 2, 4],
              borderRadius: 2,
              position: 'middle',
              distance: 20
            },
            lineStyle: {
              color: getEdgeColor(edge),
              width: getEdgeWidth(edge),
              curveness: 0.3 + (index % 3) * 0.1,
              type: 'solid',
              shadowColor: 'rgba(0, 0, 0, 0.5)',
              shadowBlur: 5
            },
            emphasis: {
              lineStyle: {
                width: getEdgeWidth(edge) + 2,
                shadowBlur: 10
              }
            },
            type: edge.type,
            weight: edge.weight
          })),
          force: {
            repulsion: 2000,
            edgeLength: 200,
            gravity: 0.1,
            friction: 0.2
          },
          roam: true,
          focusNodeAdjacency: true,
          lineStyle: {
            opacity: 0.8
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4
            }
          }
        }]
      };
      
      chart.value.setOption(option);
    };
    
    const switchGraphLayer = (layer) => {
      graphLayer.value = layer;
      updateChart();
    };
    
    const toggleKeyNodes = () => {
      showOnlyKeyNodes.value = !showOnlyKeyNodes.value;
      updateChart();
    };
    
    const toggleLanguage = () => {
      showEnglish.value = !showEnglish.value;
      updateChart();
    };
    
    const viewSubstitutes = () => {
      if (selectedNode.value) {
        emit('view-substitutes', selectedNode.value);
      }
    };
    
    onMounted(() => {
      nextTick(() => {
        initChart();
      });
    });
    
    watch(() => props.graphData, () => {
      updateChart();
    }, { deep: true });
    
    return {
      chartRef,
      graphLayer,
      showOnlyKeyNodes,
      showEnglish,
      selectedNode,
      graphLayers,
      switchGraphLayer,
      toggleKeyNodes,
      toggleLanguage,
      viewSubstitutes,
      getRoleLabel
    };
  }
});
</script>

<style scoped>
.recipe-local-graph {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding: 1rem;
  background: rgba(25, 25, 25, 0.85);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.25);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.graph-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #d4af37;
  margin: 0;
  font-family: 'Playfair Display', serif;
  letter-spacing: 0.5px;
  text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
}

.graph-controls {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.graph-control-btn {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(184, 134, 11, 0.1) 100%);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 4px;
  color: #c0c0c0;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.graph-control-btn:hover {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(184, 134, 11, 0.2) 100%);
  border-color: rgba(212, 175, 55, 0.6);
  color: #d4af37;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.graph-control-btn.active {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.3) 0%, rgba(184, 134, 11, 0.3) 100%);
  border-color: rgba(212, 175, 55, 0.8);
  color: #d4af37;
  box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
}

.graph-control-separator {
  width: 1px;
  height: 2rem;
  background: linear-gradient(180deg, transparent 0%, rgba(212, 175, 55, 0.3) 50%, transparent 100%);
  margin: 0 0.6rem;
}

.graph-info {
  background: rgba(25, 25, 25, 0.85);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.25);
  padding: 1rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.info-item {
  display: flex;
  margin-bottom: 0.5rem;
  align-items: center;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-label {
  font-size: 0.9rem;
  color: #d4af37;
  font-weight: 600;
  margin-right: 1rem;
  min-width: 80px;
}

.info-text {
  font-size: 0.85rem;
  color: #cccccc;
  line-height: 1.4;
  flex: 1;
}

.info-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  color: #ffffff;
  margin-right: 8px;
  font-weight: 600;
  margin-bottom: 4px;
}

.graph-container {
  position: relative;
  width: 100%;
  height: 650px;
  border-radius: 8px;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(20, 20, 20, 0.8) 0%, rgba(10, 10, 10, 0.9) 100%);
  border: 1px solid rgba(212, 175, 55, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.node-detail-panel {
  background: rgba(25, 25, 25, 0.9);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 0.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.detail-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #d4af37;
  margin: 0 0 1.25rem 0;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
  padding-bottom: 0.75rem;
  text-shadow: 0 0 8px rgba(212, 175, 55, 0.2);
}

.detail-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(212, 175, 55, 0.1);
  transition: all 0.2s ease;
}

.metric-row:hover {
  border-bottom-color: rgba(212, 175, 55, 0.3);
}

.metric-label {
  font-size: 0.9rem;
  color: #888;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 0.9rem;
  color: #d0d0d0;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.detail-explanation {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 6px;
  border-left: 3px solid rgba(212, 175, 55, 0.5);
}

.explanation-title {
  font-size: 1rem;
  font-weight: 600;
  color: #d4af37;
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.explanation-text {
  font-size: 0.9rem;
  color: #b0b0b0;
  line-height: 1.6;
  margin: 0;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .graph-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .graph-controls {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .graph-info {
    padding: 0.75rem;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .info-label {
    margin-right: 0;
    margin-bottom: 0.25rem;
  }
  
  .graph-container {
    height: 450px;
  }
}
</style>
