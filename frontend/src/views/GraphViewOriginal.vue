<template>
  <div class="flavor-graph">
    <header class="graph-header">
      <div class="container">
        <div class="header-content">
          <h1 class="page-title">风味图谱</h1>
          <p class="page-subtitle">探索原料之间的共现、相似与兼容关系</p>
        </div>
      </div>
    </header>

    <main class="graph-main">
      <div class="container">
        <div class="graph-layout">
          <aside class="graph-sidebar">
            <div class="sidebar-card card">
              <h3 class="sidebar-title">图层控制</h3>
              <div class="layer-buttons">
                <button 
                  v-for="layer in layers" 
                  :key="layer.value"
                  :class="['layer-btn', { active: currentLayer === layer.value }]"
                  @click="changeLayer(layer.value)"
                >
                  {{ layer.label }}
                </button>
              </div>
            </div>

            <div class="sidebar-card card">
              <h3 class="sidebar-title">类型筛选</h3>
              <div class="filter-options">
                <div 
                  v-for="type in ingredientTypes" 
                  :key="type.value"
                  class="filter-checkbox"
                >
                  <input 
                    type="checkbox" 
                    :value="type.value"
                    v-model="selectedTypes"
                    @change="applyFilters"
                    :id="`type-${type.value}`"
                  >
                  <label :for="`type-${type.value}`" class="filter-label">{{ type.label }}</label>
                </div>
              </div>
              <div style="margin-top: 10px; padding: 10px; background: var(--color-bg-3); border-radius: 4px; font-size: 0.85rem; color: var(--color-text-secondary);">
                <strong>当前选择:</strong> {{ selectedTypes.length > 0 ? selectedTypes.join(', ') : '无' }}
              </div>
            </div>

            <div class="sidebar-card card">
              <h3 class="sidebar-title">阈值控制</h3>
              <div class="threshold-control">
                <div class="control-item">
                  <label class="control-label">边权阈值</label>
                  <input 
                    type="range" 
                    v-model.number="minWeight" 
                    min="0" 
                    max="1" 
                    step="0.05"
                    class="control-range"
                    @change="applyFilters"
                  >
                  <span class="control-value">{{ minWeight.toFixed(2) }}</span>
                </div>
                <div class="control-item">
                  <label class="control-label">频次阈值</label>
                  <input 
                    type="range" 
                    v-model.number="minFreq" 
                    min="0" 
                    max="100" 
                    step="5"
                    class="control-range"
                    @change="applyFilters"
                  >
                  <span class="control-value">{{ minFreq }}</span>
                </div>
              </div>
            </div>

            <div class="sidebar-card card">
              <h3 class="sidebar-title">搜索</h3>
              <div class="search-box">
                <input 
                  type="text" 
                  v-model="searchKeyword"
                  placeholder="输入原料名称..."
                  class="search-input"
                  @input="handleSearch"
                >
                <button 
                  class="search-btn"
                  @click="handleSearch"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="M21 21l-4.35-4.35"/>
                  </svg>
                </button>
              </div>
            </div>
          </aside>

          <section class="graph-content">
            <div class="graph-container card">
              <div class="graph-toolbar">
                <div class="toolbar-info">
                  <span class="info-label">当前图层:</span>
                  <span class="info-value">{{ getLayerLabel(currentLayer) }}</span>
                </div>
                <div class="toolbar-stats">
                  <span class="stat-item">节点: {{ graphData.nodes.length }}</span>
                  <span class="stat-item">边: {{ graphData.edges.length }}</span>
                </div>
                <div class="toolbar-actions">
                  <button 
                    class="btn btn-primary"
                    @click="enterPathAnalysisMode"
                  >
                    路径分析
                  </button>
                  <div class="export-dropdown">
                    <button class="btn btn-secondary dropdown-toggle">
                      导出
                    </button>
                    <div class="dropdown-menu">
                      <button @click="exportData('csv')" class="dropdown-item">导出为CSV</button>
                      <button @click="exportData('json')" class="dropdown-item">导出为JSON</button>
                      <button @click="exportData('png')" class="dropdown-item">导出为PNG</button>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="graph-visualization">
                <div v-if="loading" class="graph-loading">
                  <div class="loading-spinner"></div>
                  <p>加载图谱数据中...</p>
                </div>
                <div v-else-if="error" class="graph-error">
                  <div class="error-icon">⚠️</div>
                  <p>{{ error }}</p>
                  <button class="btn btn-primary" @click="fetchGraphData">重新加载</button>
                </div>
                <div v-else class="graph-canvas">
                  <div ref="graphCanvas" class="echarts-container"></div>
                </div>
              </div>
            </div>
          </section>

          <aside class="graph-details">
            <div v-if="selectedNodes.length > 0" class="details-card card">
              <div class="details-header">
                <h3 class="details-title">原料对比</h3>
                <button class="close-btn" @click="clearSelection">×</button>
              </div>
              
              <div class="compare-nodes">
                <div 
                  v-for="(node, index) in selectedNodes" 
                  :key="node.id"
                  class="compare-node-item"
                >
                  <div class="node-info">
                    <h4 class="node-name">
                      <span v-if="node.label_zh" class="name-zh">{{ node.label_zh }}</span>
                      <span v-if="node.label_zh && node.label" class="name-separator"> / </span>
                      <span v-if="node.label" class="name-en">{{ node.label }}</span>
                    </h4>
                    <div class="node-meta">
                      <span class="meta-tag">{{ node.ingredient_type }}</span>
                      <span class="meta-tag">{{ node.role }}</span>
                    </div>
                  </div>
                  <button 
                    class="remove-node-btn"
                    @click="removeCompareNode(node.id)"
                  >
                    ×
                  </button>
                </div>
              </div>
              
              <div class="compare-actions">
                <button 
                  class="btn btn-primary"
                  @click="compareNodes"
                  :disabled="selectedNodes.length < 2"
                >
                  对比选中原料
                </button>
                <button 
                  class="btn btn-secondary"
                  @click="clearSelection"
                >
                  清除选择
                </button>
              </div>
            </div>
            
            <div v-else-if="pathAnalysisMode" class="details-card card">
              <div class="details-header">
                <h3 class="details-title">路径分析</h3>
                <button class="close-btn" @click="exitPathAnalysisMode">×</button>
              </div>
              
              <div class="path-analysis-form">
                <div class="form-group">
                  <label class="form-label">起点原料</label>
                  <select 
                    v-model="pathStartNode"
                    class="form-select"
                    @change="fetchNodeDetails(pathStartNode)"
                  >
                    <option value="">选择起点</option>
                    <option 
                      v-for="node in graphData.nodes" 
                      :key="node.id"
                      :value="node.id"
                    >
                      {{ node.label_zh || node.label }}
                    </option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label class="form-label">终点原料</label>
                  <select 
                    v-model="pathEndNode"
                    class="form-select"
                    @change="fetchNodeDetails(pathEndNode)"
                  >
                    <option value="">选择终点</option>
                    <option 
                      v-for="node in graphData.nodes" 
                      :key="node.id"
                      :value="node.id"
                    >
                      {{ node.label_zh || node.label }}
                    </option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label class="form-label">路径长度</label>
                  <select v-model="pathMaxLength" class="form-select">
                    <option value="2">2步</option>
                    <option value="3">3步</option>
                    <option value="4">4步</option>
                    <option value="5">5步</option>
                  </select>
                </div>
                
                <button 
                  class="btn btn-primary full-width"
                  @click="analyzePath"
                  :disabled="!pathStartNode || !pathEndNode || pathStartNode === pathEndNode"
                >
                  分析路径
                </button>
              </div>
              
              <div v-if="paths.length > 0" class="path-results">
                <h4 class="section-title">分析结果</h4>
                <div class="path-list">
                  <div 
                    v-for="(path, index) in paths" 
                    :key="index"
                    class="path-item"
                    @click="highlightPath(path)"
                  >
                    <div class="path-info">
                      <span class="path-number">路径 {{ index + 1 }}</span>
                      <span class="path-length">长度: {{ path.length - 1 }}步</span>
                    </div>
                    <div class="path-nodes">
                      {{ path.map(node => node.label_zh || node.label).join(' → ') }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else-if="selectedNode" class="details-card card">
              <div class="details-header">
                <h3 class="details-title">节点详情</h3>
                <button class="close-btn" @click="clearSelection">×</button>
              </div>
              
              <div class="node-basic-info">
                <h4 class="node-name">
                  <span v-if="selectedNode.label_zh" class="name-zh">{{ selectedNode.label_zh }}</span>
                  <span v-if="selectedNode.label_zh && selectedNode.label" class="name-separator"> / </span>
                  <span v-if="selectedNode.label" class="name-en">{{ selectedNode.label }}</span>
                </h4>
                <div class="node-meta">
                  <span class="meta-tag">{{ selectedNode.ingredient_type }}</span>
                  <span class="meta-tag">{{ selectedNode.role }}</span>
                  <span v-if="selectedNode.is_key_node" class="meta-tag key-node">关键节点</span>
                </div>
              </div>

              <div class="node-stats">
                <div class="stat-row">
                  <span class="stat-label">出现频次:</span>
                  <span class="stat-value">{{ selectedNode.freq }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">重要性分数:</span>
                  <span class="stat-value">{{ selectedNode.importance_score?.toFixed(3) || 'N/A' }}</span>
                </div>
              </div>

              <div v-if="selectedNode.anchor" class="anchor-section">
                <h4 class="section-title">Anchor 信息</h4>
                <div class="anchor-info">
                  <div class="anchor-row">
                    <span class="anchor-label">Anchor 名称:</span>
                    <span class="anchor-value">{{ selectedNode.anchor.anchor_name }}</span>
                  </div>
                  <div class="anchor-row">
                    <span class="anchor-label">来源:</span>
                    <span class="anchor-value">{{ selectedNode.anchor.anchor_source }}</span>
                  </div>
                  <div class="anchor-row">
                    <span class="anchor-label">匹配置信度:</span>
                    <span class="anchor-value">{{ selectedNode.anchor?.match_confidence ? (selectedNode.anchor.match_confidence * 100).toFixed(1) : 'N/A' }}%</span>
                  </div>
                </div>
              </div>

              <div v-if="selectedNode.features" class="flavor-features">
                <h4 class="section-title">风味特征</h4>
                <div class="feature-bars">
                  <div class="feature-bar">
                    <span class="feature-label">酸味</span>
                    <div class="feature-progress">
                      <div class="feature-fill" :style="{ width: (selectedNode.features.sour || 0) * 100 + '%' }"></div>
                    </div>
                    <span class="feature-value">{{ ((selectedNode.features.sour || 0) * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="feature-bar">
                    <span class="feature-label">甜味</span>
                    <div class="feature-progress">
                      <div class="feature-fill" :style="{ width: (selectedNode.features.sweet || 0) * 100 + '%' }"></div>
                    </div>
                    <span class="feature-value">{{ ((selectedNode.features.sweet || 0) * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="feature-bar">
                    <span class="feature-label">苦味</span>
                    <div class="feature-progress">
                      <div class="feature-fill" :style="{ width: (selectedNode.features.bitter || 0) * 100 + '%' }"></div>
                    </div>
                    <span class="feature-value">{{ ((selectedNode.features.bitter || 0) * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="feature-bar">
                    <span class="feature-label">香气</span>
                    <div class="feature-progress">
                      <div class="feature-fill" :style="{ width: (selectedNode.features.aroma || 0) * 100 + '%' }"></div>
                    </div>
                    <span class="feature-value">{{ ((selectedNode.features.aroma || 0) * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="feature-bar">
                    <span class="feature-label">果味</span>
                    <div class="feature-progress">
                      <div class="feature-fill" :style="{ width: (selectedNode.features.fruity || 0) * 100 + '%' }"></div>
                    </div>
                    <span class="feature-value">{{ ((selectedNode.features.fruity || 0) * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="feature-bar">
                    <span class="feature-label">酒体</span>
                    <div class="feature-progress">
                      <div class="feature-fill" :style="{ width: (selectedNode.features.body || 0) * 100 + '%' }"></div>
                    </div>
                    <span class="feature-value">{{ ((selectedNode.features.body || 0) * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </div>

              <div v-if="selectedNode.top_neighbors && selectedNode.top_neighbors.length > 0" class="neighbors-section">
                <h4 class="section-title">Top 邻居</h4>
                <div class="neighbors-list">
                  <div 
                    v-for="neighbor in selectedNode.top_neighbors.slice(0, 5)" 
                    :key="neighbor.id"
                    class="neighbor-item"
                  >
                    <span class="neighbor-name">{{ neighbor.label }}</span>
                    <span class="neighbor-weight">{{ neighbor.weight?.toFixed(2) || 'N/A' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="selectedEdge" class="details-card card">
              <div class="details-header">
                <h3 class="details-title">边详情</h3>
                <button class="close-btn" @click="clearSelection">×</button>
              </div>
              
              <div class="edge-basic-info">
                <div class="edge-nodes">
                  <span class="edge-node">
                    <span v-if="selectedEdge.source.label_zh" class="name-zh">{{ selectedEdge.source.label_zh }}</span>
                    <span v-if="selectedEdge.source.label_zh && selectedEdge.source.label" class="name-separator"> / </span>
                    <span v-if="selectedEdge.source.label" class="name-en">{{ selectedEdge.source.label }}</span>
                  </span>
                  <span class="edge-arrow">→</span>
                  <span class="edge-node">
                    <span v-if="selectedEdge.target.label_zh" class="name-zh">{{ selectedEdge.target.label_zh }}</span>
                    <span v-if="selectedEdge.target.label_zh && selectedEdge.target.label" class="name-separator"> / </span>
                    <span v-if="selectedEdge.target.label" class="name-en">{{ selectedEdge.target.label }}</span>
                  </span>
                </div>
                <div class="edge-meta">
                  <span class="meta-tag">{{ getLayerLabel(currentLayer) }}</span>
                  <span class="meta-tag">权重: {{ selectedEdge.weight?.toFixed(2) || 'N/A' }}</span>
                </div>
              </div>

              <div v-if="selectedEdge.metrics" class="edge-metrics">
                <h4 class="section-title">详细指标</h4>
                <div class="metrics-grid">
                  <div 
                    v-for="(value, key) in selectedEdge.metrics" 
                    :key="key"
                    class="metric-item"
                  >
                    <span class="metric-label">{{ formatMetricKey(key) }}:</span>
                    <span class="metric-value">{{ formatMetricValue(value) }}</span>
                  </div>
                </div>
              </div>

              <div v-if="selectedEdge.summary" class="edge-summary">
                <h4 class="section-title">说明</h4>
                <p class="summary-text">{{ selectedEdge.summary }}</p>
              </div>
            </div>

            <div v-else class="details-placeholder card">
              <div class="placeholder-icon">📊</div>
              <p>点击图谱中的节点或边查看详细信息</p>
              <p class="placeholder-hint">可选择多个节点进行对比分析</p>
            </div>
          </aside>
        </div>

        <section class="graph-stats-section">
          <div class="stats-grid">
            <div class="stat-card card">
              <h3 class="stat-card-title">Top 原料榜</h3>
              <div class="stat-list">
                <div 
                  v-for="(item, index) in topNodes.slice(0, 10)" 
                  :key="item.id"
                  class="stat-list-item"
                >
                  <span class="stat-rank">{{ index + 1 }}</span>
                  <span class="stat-name">{{ item.label }}</span>
                  <span class="stat-score">{{ item.score?.toFixed(3) || 'N/A' }}</span>
                </div>
              </div>
            </div>

            <div class="stat-card card">
              <h3 class="stat-card-title">高频 Anchor 榜</h3>
              <div class="stat-list">
                <div 
                  v-for="(item, index) in topAnchors.slice(0, 10)" 
                  :key="item.anchor_name"
                  class="stat-list-item"
                >
                  <span class="stat-rank">{{ index + 1 }}</span>
                  <span class="stat-name">{{ item.anchor_name }}</span>
                  <span class="stat-count">{{ item.count }}</span>
                </div>
              </div>
            </div>

            <div class="stat-card card">
              <h3 class="stat-card-title">关键节点榜</h3>
              <div class="stat-list">
                <div 
                  v-for="(item, index) in keyNodes.slice(0, 10)" 
                  :key="item.id"
                  class="stat-list-item"
                >
                  <span class="stat-rank">{{ index + 1 }}</span>
                  <span class="stat-name">{{ item.label }}</span>
                  <span class="stat-score">{{ item.importance_score?.toFixed(3) || 'N/A' }}</span>
                </div>
              </div>
            </div>

            <div class="stat-card card">
              <h3 class="stat-card-title">图层统计摘要</h3>
              <div class="summary-stats">
                <div class="summary-item">
                  <span class="summary-label">总节点数:</span>
                  <span class="summary-value">{{ graphStats.summary?.node_count || 0 }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">总边数:</span>
                  <span class="summary-value">{{ graphStats.summary?.edge_count || 0 }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">平均度数:</span>
                  <span class="summary-value">{{ graphStats.summary?.avg_degree?.toFixed(2) || 'N/A' }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">最大边权:</span>
                  <span class="summary-value">{{ graphStats.summary?.max_weight?.toFixed(2) || 'N/A' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 添加图表区域 -->
          <div class="charts-grid">
        <div class="chart-card card">
          <h3 class="stat-card-title">原料类型分布</h3>
          <div ref="typeDistributionChart" class="chart-container"></div>
        </div>
        <div class="chart-card card">
          <h3 class="stat-card-title">风味特征雷达图</h3>
          <div ref="flavorRadarChart" class="chart-container"></div>
        </div>
        <div v-if="selectedNodes.length >= 2" class="chart-card card compare-chart-card">
          <h3 class="stat-card-title">原料风味对比</h3>
          <div ref="compareChart" class="chart-container"></div>
        </div>
      </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'GraphView',
  components: {},
  data() {
    return {
      loading: false,
      error: null,
      
      currentLayer: 'compat',
      layers: [
        { value: 'compat', label: '兼容' },
        { value: 'cooccur', label: '共现' },
        { value: 'flavor', label: '相似' }
      ],
      
      selectedTypes: [],
      ingredientTypes: [
        { value: 'spirit', label: '烈酒' },
        { value: 'liqueur', label: '利口酒' },
        { value: 'juice', label: '果汁' },
        { value: 'syrup', label: '糖浆' },
        { value: 'bitters', label: '苦精' },
        { value: 'garnish', label: '装饰' },
        { value: 'other', label: '其他' }
      ],
      
      minWeight: 0.0,
      minFreq: 0,
      searchKeyword: '',
      
      graphData: {
        nodes: [],
        edges: []
      },
      
      chart: null,
      
      selectedNode: null,
      selectedEdge: null,
      
      // 图表实例
      typeDistributionChart: null,
      flavorRadarChart: null,
      compareChart: null, // 原料对比图表实例
      
      // 用于原料对比
      selectedNodes: [],
      maxCompareNodes: 4, // 最多对比4个原料
      
      // 用于路径分析
      pathAnalysisMode: false,
      pathStartNode: '',
      pathEndNode: '',
      pathMaxLength: 3,
      paths: [],
      
      graphStats: {
        summary: {},
        top_nodes: [],
        top_freq: [],
        top_anchors: []
      },
      
      // 性能优化相关
      dataCache: null,
      cacheExpiry: 3600000, // 1小时缓存
      isProcessing: false, // 防止重复请求
      searchTimer: null, // 搜索防抖定时器
      filterTimer: null // 筛选防抖定时器
    }
  },
  
  computed: {
    topNodes() {
      return this.graphStats.top_nodes || []
    },
    
    topAnchors() {
      return this.graphStats.top_anchors || []
    },
    
    keyNodes() {
      return this.graphData.nodes.filter(node => node.is_key_node) || []
    }
  },
  
  mounted() {
    this.fetchGraphData()
    this.fetchGraphStats()
    
    // 添加点击空白区域清除选择的事件
    document.addEventListener('click', (e) => {
      const graphCanvas = this.$refs.graphCanvas
      if (graphCanvas && !graphCanvas.contains(e.target)) {
        this.clearSelection()
      }
    })
  },
  
  beforeUnmount() {
    if (this.chart) {
      this.chart.dispose()
    }
    if (this.typeDistributionChart) {
      this.typeDistributionChart.dispose()
    }
    if (this.flavorRadarChart) {
      this.flavorRadarChart.dispose()
    }
    if (this.compareChart) {
      this.compareChart.dispose()
    }
  },
  
  methods: {
    async fetchGraphData() {
      if (this.isProcessing) {
        return
      }
      
      this.loading = true
      this.error = null
      this.isProcessing = true
      
      try {
        // 生成缓存键
        const cacheKey = this.getCacheKey()
        
        // 尝试从缓存中获取数据
        const cachedData = this.getFromCache(cacheKey)
        if (cachedData) {
          console.log('使用缓存数据:', cachedData)
          this.graphData = cachedData
          this.loading = false
          this.isProcessing = false
          await this.$nextTick()
          this.initChart()
          this.initTypeDistributionChart()
          this.initFlavorRadarChart()
          return
        }
        
        const params = new URLSearchParams({
          layer: this.currentLayer,
          min_weight: this.minWeight,
          min_freq: this.minFreq,
          limit_nodes: 100
        })
        
        if (this.selectedTypes.length > 0) {
          params.append('ingredient_type', this.selectedTypes.join(','))
        }
        
        if (this.searchKeyword) {
          params.append('keyword', this.searchKeyword)
        }
        
        console.log('Fetching graph data with params:', params.toString())
        const response = await fetch(`http://127.0.0.1:8000/api/flavor-graph/graph?${params}`)
        console.log('Response status:', response.status)
        const data = await response.json()
        console.log('Response data:', data)
        
        if (data.code === 0) {
          this.graphData = {
            nodes: (data.data.nodes || []).map(node => ({
              id: String(node.id),
              name: node.label,
              label: node.label,
              label_zh: node.label_zh,
              ingredient_type: node.ingredient_type,
              role: node.role,
              freq: node.freq,
              importance_score: node.importance_score,
              is_key_node: node.is_key_node
            })),
            edges: (data.data.edges || []).map(edge => ({
              source: String(edge.source),
              target: String(edge.target),
              value: edge.weight
            }))
          }
          
          // 保存数据到缓存
          this.saveToCache(cacheKey, this.graphData)
          
          console.log('Graph data:', this.graphData)
          this.loading = false
          this.isProcessing = false
          await this.$nextTick()
          this.initChart()
          this.initTypeDistributionChart()
          this.initFlavorRadarChart()
        } else {
          this.error = data.message || '获取图谱数据失败'
          console.error('Error fetching graph data:', this.error)
          this.loading = false
          this.isProcessing = false
        }
      } catch (err) {
        console.error('获取图谱数据失败:', err)
        this.error = '网络错误，请检查后端服务是否启动'
        this.loading = false
        this.isProcessing = false
      }
    },
    
    async fetchGraphStats() {
      try {
        const params = new URLSearchParams({
          layer: this.currentLayer
        })
        
        if (this.selectedTypes.length > 0) {
          params.append('ingredient_type', this.selectedTypes.join(','))
        }
        
        const response = await fetch(`http://127.0.0.1:8000/api/flavor-graph/stats?${params}`)
        const data = await response.json()
        
        if (data.code === 0) {
          this.graphStats = data.data
        }
      } catch (err) {
        console.error('获取图谱统计失败:', err)
      }
    },
    
    async fetchNodeDetails(nodeId) {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/flavor-graph/nodes/${nodeId}`)
        const data = await response.json()
        
        if (data.code === 0) {
          return data.data
        }
      } catch (err) {
        console.error('获取节点详情失败:', err)
      }
      return null
    },
    
    async fetchEdgeDetails(sourceId, targetId) {
      try {
        const params = new URLSearchParams({
          source: sourceId,
          target: targetId,
          layer: this.currentLayer
        })
        
        const response = await fetch(`http://127.0.0.1:8000/api/flavor-graph/edges/detail?${params}`)
        const data = await response.json()
        
        if (data.code === 0) {
          return data.data
        }
      } catch (err) {
        console.error('获取边详情失败:', err)
      }
      return null
    },
    
    clearSelection() {
      this.selectedNode = null
      this.selectedEdge = null
      this.selectedNodes = []
      
      // 清除echarts中的选中状态
      if (this.chart) {
        this.chart.dispatchAction({
          type: 'downplay',
          seriesIndex: 0
        })
      }
    },
    
    getLayerLabel(layer) {
      const layerMap = {
        compat: '兼容关系',
        cooccur: '共现关系',
        flavor: '相似关系'
      }
      return layerMap[layer] || layer
    },
    
    getIngredientTypeLabel(type) {
      const typeMap = {
        spirit: '烈酒',
        liqueur: '利口酒',
        juice: '果汁',
        syrup: '糖浆',
        bitters: '苦精',
        garnish: '装饰',
        other: '其他'
      }
      return typeMap[type] || type
    },
    
    initChart() {
      if (this.chart) {
        this.chart.dispose()
      }
      
      const container = this.$refs.graphCanvas
      console.log('Chart container:', container)
      if (!container) return
      
      console.log('Container dimensions:', {
        width: container.offsetWidth,
        height: container.offsetHeight
      })
      
      this.chart = echarts.init(container)
      
      // 定义原料类型颜色映射
      const ingredientTypeColors = {
        spirit: '#FF6B6B',    // 烈酒 - 红色
        liqueur: '#4ECDC4',   // 利口酒 - 青色
        juice: '#45B7D1',     // 果汁 - 蓝色
        syrup: '#96CEB4',     // 糖浆 - 绿色
        bitters: '#FFEAA7',   // 苦精 - 黄色
        garnish: '#DDA0DD',   // 装饰 - 紫色
        other: '#95A5A6'      // 其他 - 灰色
      }
      
      // 定义图层颜色映射
      const layerColors = {
        compat: '#4CAF50',     // 兼容 - 绿色
        cooccur: '#2196F3',    // 共现 - 蓝色
        flavor: '#FF9800'      // 相似 - 橙色
      }
      
      const option = {
        title: {
          text: '风味图谱',
          subtext: this.getLayerLabel(this.currentLayer),
          left: 'center',
          textStyle: {
            color: '#D4AF37'
          },
          subtextStyle: {
            color: '#999'
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            if (params.dataType === 'node') {
              return `
                <div style="font-weight: bold; margin-bottom: 5px; color: ${ingredientTypeColors[params.data.ingredient_type] || '#95A5A6'}">${params.data.name}</div>
                <div>类型: ${params.data.ingredient_type || '未知'}</div>
                <div>角色: ${params.data.role || '未知'}</div>
                <div>频次: ${params.data.freq || 0}</div>
                <div>重要性: ${params.data.importance_score?.toFixed(3) || 'N/A'}</div>
                ${params.data.is_key_node ? '<div style="color: #D4AF37;">关键节点</div>' : ''}
              `
            } else if (params.dataType === 'edge') {
              return `
                <div>关系类型: ${this.getLayerLabel(this.currentLayer)}</div>
                <div>权重: ${params.data.value?.toFixed(2) || 'N/A'}</div>
              `
            }
          }
        },
        legend: {
          type: 'scroll',
          orient: 'horizontal',
          bottom: 10,
          data: Object.keys(ingredientTypeColors).map(type => ({
            name: this.getIngredientTypeLabel(type),
            icon: 'circle',
            textStyle: {
              color: '#D4AF37'
            }
          })),
          selectedMode: false
        },
        animationDurationUpdate: 1500,
        animationEasingUpdate: 'quinticInOut',
        series: [
          {
            type: 'graph',
            layout: 'force',
            data: this.graphData.nodes.map(node => ({
              id: node.id,
              name: node.label,
              label: {
                show: true,
                position: 'right',
                formatter: '{b}',
                fontSize: 12,
                color: '#D4AF37'
              },
              symbolSize: node.is_key_node ? 30 : Math.max(15, Math.min(25, (node.freq || 0) / 10 + 10)),
              itemStyle: {
                color: ingredientTypeColors[node.ingredient_type] || '#95A5A6',
                borderColor: '#fff',
                borderWidth: 2,
                shadowBlur: 10,
                shadowColor: ingredientTypeColors[node.ingredient_type] || '#95A5A6'
              },
              emphasis: {
                itemStyle: {
                  borderColor: '#fff',
                  borderWidth: 3,
                  shadowBlur: 20,
                  shadowColor: '#D4AF37'
                },
                label: {
                  show: true,
                  fontSize: 14,
                  fontWeight: 'bold'
                }
              },
              ...node
            })),
            links: this.graphData.edges.map(edge => ({
              source: edge.source,
              target: edge.target,
              lineStyle: {
                width: Math.max(1, edge.value * 10),
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 1,
                  y2: 0,
                  colorStops: [{
                    offset: 0,
                    color: layerColors[this.currentLayer] || '#999'
                  }, {
                    offset: 1,
                    color: layerColors[this.currentLayer] || '#999'
                  }],
                  global: false
                },
                opacity: Math.max(0.3, edge.value),
                curveness: 0.1
              },
              emphasis: {
                lineStyle: {
                  width: Math.max(2, edge.value * 15),
                  opacity: 1
                }
              },
              ...edge
            })),
            roam: true,
            force: {
              repulsion: 1000,
              edgeLength: [80, 120],
              gravity: 0.1
            },
            focusNodeAdjacency: true,
            lineStyle: {
              opacity: 0.6,
              width: 2,
              curveness: 0.1
            }
          }
        ]
      }
      
      console.log('Chart option:', option)
      
      // 处理空数据情况
      if (this.graphData.nodes.length === 0) {
        option.title.subtext = `${this.getLayerLabel(this.currentLayer)} - 无数据`
        option.series[0].data = []
        option.series[0].links = []
      }
      
      this.chart.setOption(option)
      
      // 添加点击事件
      this.chart.on('click', (params) => {
        console.log('Chart click event:', params)
        if (params.dataType === 'node') {
          this.handleNodeClick(params.data)
        } else if (params.dataType === 'edge') {
          this.handleEdgeClick(params.data)
        }
      })
      
      // 添加悬停事件
      this.chart.on('mouseover', (params) => {
        if (params.dataType === 'node') {
          this.chart.dispatchAction({
            type: 'highlight',
            seriesIndex: 0,
            dataIndex: params.dataIndex
          })
        }
      })
      
      this.chart.on('mouseout', (params) => {
        if (params.dataType === 'node') {
          this.chart.dispatchAction({
            type: 'downplay',
            seriesIndex: 0
          })
        }
      })
      
      // 响应式调整
      window.addEventListener('resize', () => {
        console.log('Window resize event')
        if (this.chart) {
          this.chart.resize()
        }
      })
    },
    
    handleNodeClick(node) {
      this.selectedEdge = null
      this.selectedNode = node
      
      // 支持多原料选择
      if (!this.selectedNodes.find(n => n.id === node.id)) {
        if (this.selectedNodes.length >= this.maxCompareNodes) {
          alert(`最多只能选择${this.maxCompareNodes}个原料进行对比`)
          return
        }
        this.selectedNodes.push(node)
        console.log('Selected nodes:', this.selectedNodes)
        
        // 异步获取节点详情
        this.fetchNodeDetails(node.id).then(detail => {
          if (detail) {
            const index = this.selectedNodes.findIndex(n => n.id === node.id)
            if (index !== -1) {
              this.selectedNodes[index] = { ...node, ...detail }
            }
            this.selectedNode = { ...node, ...detail }
          }
        })
      }
    },
    
    handleEdgeClick(edge) {
      this.selectedNode = null
      this.selectedEdge = edge
      
      this.fetchEdgeDetails(edge.source, edge.target).then(detail => {
        if (detail) {
          this.selectedEdge = { ...edge, ...detail }
        }
      })
    },
    
    changeLayer(layer) {
      if (this.currentLayer === layer) return
      this.currentLayer = layer
      this.clearSelection()
      this.clearCache()
      this.fetchGraphData()
      this.fetchGraphStats()
    },
    
    applyFilters() {
      if (this.filterTimer) {
        clearTimeout(this.filterTimer)
      }
      this.filterTimer = setTimeout(() => {
        this.clearSelection()
        this.clearCache()
        this.fetchGraphData()
      }, 300)
    },
    
    handleSearch() {
      if (this.searchTimer) {
        clearTimeout(this.searchTimer)
      }
      this.searchTimer = setTimeout(() => {
        this.clearSelection()
        this.clearCache()
        this.fetchGraphData()
      }, 500)
    },
    
    formatMetricKey(key) {
      const keyMap = {
        compat_score: '兼容分数',
        role_bonus: '角色加成',
        taste_complement_score: '口味互补分数',
        anchor_bonus: 'Anchor加成',
        cooccur_bonus: '共现加成',
        penalty_score: '惩罚分数',
        co_count: '共现次数',
        pmi: 'PMI值',
        weight: '权重',
        cosine_sim: '余弦相似度',
        l2_distance: 'L2距离'
      }
      return keyMap[key] || key
    },
    
    formatMetricValue(value) {
      if (typeof value === 'number') {
        return value.toFixed(3)
      }
      return value
    },
    
    getCacheKey() {
      const types = [...this.selectedTypes].sort().join(',')
      return `graph_data_${this.currentLayer}_${this.minWeight}_${this.minFreq}_${types}_${this.searchKeyword}`
    },
    
    getFromCache(key) {
      try {
        const cached = localStorage.getItem(key)
        if (cached) {
          const data = JSON.parse(cached)
          const now = Date.now()
          if (data.timestamp && (now - data.timestamp) < 24 * 60 * 60 * 1000) {
            return data.content
          }
        }
      } catch (err) {
        console.error('读取缓存失败:', err)
      }
      return null
    },
    
    saveToCache(key, data) {
      try {
        const cacheData = {
          timestamp: Date.now(),
          content: data
        }
        localStorage.setItem(key, JSON.stringify(cacheData))
        console.log('数据已保存到缓存:', key)
      } catch (err) {
        console.error('保存缓存失败:', err)
      }
    },
    
    clearCache() {
      try {
        const keys = Object.keys(localStorage)
        keys.forEach(key => {
          if (key.startsWith('graph_data_')) {
            localStorage.removeItem(key)
            console.log('清除缓存:', key)
          }
        })
      } catch (err) {
        console.error('清除缓存失败:', err)
      }
    },
    
    // 初始化原料类型分布饼图
    initTypeDistributionChart() {
      if (!this.$refs.typeDistributionChart) {
        console.warn('typeDistributionChart ref not found')
        return
      }
      
      if (this.typeDistributionChart) {
        this.typeDistributionChart.dispose()
      }
      
      this.typeDistributionChart = echarts.init(this.$refs.typeDistributionChart)
      
      // 计算原料类型分布
      const typeCounts = {}
      this.graphData.nodes.forEach(node => {
        const type = node.ingredient_type || 'other'
        typeCounts[type] = (typeCounts[type] || 0) + 1
      })
      
      const data = Object.entries(typeCounts).map(([type, count]) => ({
        name: this.getIngredientTypeLabel(type),
        value: count
      }))
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: {
            color: '#D4AF37'
          }
        },
        series: [
          {
            name: '原料类型',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: data
          }
        ]
      }
      
      this.typeDistributionChart.setOption(option)
      
      // 响应式调整
      window.addEventListener('resize', () => {
        if (this.typeDistributionChart) {
          this.typeDistributionChart.resize()
        }
      })
    },
    
    // 初始化风味特征雷达图
    initFlavorRadarChart() {
      if (!this.$refs.flavorRadarChart) {
        console.warn('flavorRadarChart ref not found')
        return
      }
      
      if (this.flavorRadarChart) {
        this.flavorRadarChart.dispose()
      }
      
      this.flavorRadarChart = echarts.init(this.$refs.flavorRadarChart)
      
      // 初始数据
      const averageFlavors = {
        sour: 0,
        sweet: 0,
        bitter: 0,
        aroma: 0,
        fruity: 0,
        body: 0
      }
      
      const option = {
        tooltip: {},
        radar: {
          indicator: [
            { name: '酸味', max: 1 },
            { name: '甜味', max: 1 },
            { name: '苦味', max: 1 },
            { name: '香气', max: 1 },
            { name: '果味', max: 1 },
            { name: '酒体', max: 1 }
          ],
          splitArea: {
            areaStyle: {
              color: ['rgba(212, 175, 55, 0.1)', 'rgba(212, 175, 55, 0.2)']
            }
          },
          axisLine: {
            lineStyle: {
              color: 'rgba(212, 175, 55, 0.5)'
            }
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(212, 175, 55, 0.5)'
            }
          }
        },
        series: [
          {
            name: '风味特征',
            type: 'radar',
            data: [
              {
                value: [
                  averageFlavors.sour || 0,
                  averageFlavors.sweet || 0,
                  averageFlavors.bitter || 0,
                  averageFlavors.aroma || 0,
                  averageFlavors.fruity || 0,
                  averageFlavors.body || 0
                ],
                name: '平均风味特征',
                areaStyle: {
                  color: 'rgba(212, 175, 55, 0.3)'
                },
                lineStyle: {
                  color: '#D4AF37'
                },
                itemStyle: {
                  color: '#D4AF37'
                }
              }
            ]
          }
        ]
      }
      
      this.flavorRadarChart.setOption(option)
      
      // 异步获取风味特征数据
      this.fetchFlavorData().then(averageFlavors => {
        if (this.flavorRadarChart) {
          this.flavorRadarChart.setOption({
            series: [
              {
                data: [
                  {
                    value: [
                      averageFlavors.sour || 0,
                      averageFlavors.sweet || 0,
                      averageFlavors.bitter || 0,
                      averageFlavors.aroma || 0,
                      averageFlavors.fruity || 0,
                      averageFlavors.body || 0
                    ]
                  }
                ]
              }
            ]
          })
        }
      })
      
      // 响应式调整
      window.addEventListener('resize', () => {
        if (this.flavorRadarChart) {
          this.flavorRadarChart.resize()
        }
      })
    },
    
    // 异步获取风味数据
    async fetchFlavorData() {
      const flavorSums = {
        sour: 0,
        sweet: 0,
        bitter: 0,
        aroma: 0,
        fruity: 0,
        body: 0
      }
      let count = 0
      
      // 收集所有节点的风味特征
      for (const node of this.graphData.nodes) {
        const nodeDetails = await this.fetchNodeDetails(node.id)
        if (nodeDetails && nodeDetails.features) {
          for (const [key, value] of Object.entries(nodeDetails.features)) {
            if (flavorSums[key] !== undefined) {
              flavorSums[key] += value
            }
          }
          count++
        }
      }
      
      // 计算平均值
      const averageFlavors = {}
      for (const [key, sum] of Object.entries(flavorSums)) {
        averageFlavors[key] = count > 0 ? sum / count : 0
      }
      
      return averageFlavors
    },
    
    // 从对比列表中移除节点
    removeCompareNode(nodeId) {
      this.selectedNodes = this.selectedNodes.filter(node => node.id !== nodeId)
      if (this.selectedNodes.length === 0) {
        this.clearSelection()
      }
    },
    
    // 对比选中的原料
    compareNodes() {
      if (this.selectedNodes.length < 2) {
        return
      }
      
      this.initCompareChart()
    },
    
    // 初始化原料对比图表
    initCompareChart() {
      if (!this.$refs.compareChart) {
        console.warn('compareChart ref not found')
        return
      }
      
      // 等待DOM更新
      this.$nextTick(() => {
        if (this.compareChart) {
          this.compareChart.dispose()
        }
        
        this.compareChart = echarts.init(this.$refs.compareChart)
        
        const flavorTypes = ['sour', 'sweet', 'bitter', 'aroma', 'fruity', 'body']
        const flavorLabels = ['酸味', '甜味', '苦味', '香气', '果味', '酒体']
        
        const series = this.selectedNodes.map((node, index) => {
          const colors = ['#D4AF37', '#8B4513', '#4682B4', '#32CD32']
          return {
            name: node.label_zh || node.label,
            type: 'radar',
            data: [
              {
                value: flavorTypes.map(type => node.features?.[type] || 0),
                name: node.label_zh || node.label,
                areaStyle: {
                  color: colors[index % colors.length] + '33'
                },
                lineStyle: {
                  color: colors[index % colors.length]
                },
                itemStyle: {
                  color: colors[index % colors.length]
                }
              }
            ]
          }
        })
        
        const option = {
          tooltip: {},
          legend: {
            data: this.selectedNodes.map(node => node.label_zh || node.label),
            bottom: 0
          },
          radar: {
            indicator: flavorLabels.map((label, index) => ({
              name: label,
              max: 1
            })),
            splitArea: {
              areaStyle: {
                color: ['rgba(212, 175, 55, 0.1)', 'rgba(212, 175, 55, 0.2)']
              }
            },
            axisLine: {
              lineStyle: {
                color: 'rgba(212, 175, 55, 0.5)'
              }
            },
            splitLine: {
              lineStyle: {
                color: 'rgba(212, 175, 55, 0.5)'
              }
            }
          },
          series: series
        }
        
        this.compareChart.setOption(option)
        
        // 响应式调整
        window.addEventListener('resize', () => {
          if (this.compareChart) {
            this.compareChart.resize()
          }
        })
      })
    },
    
    // 进入路径分析模式
    enterPathAnalysisMode() {
      this.pathAnalysisMode = true
      this.selectedNode = null
      this.selectedEdge = null
      this.selectedNodes = []
    },
    
    // 退出路径分析模式
    exitPathAnalysisMode() {
      this.pathAnalysisMode = false
      this.pathStartNode = ''
      this.pathEndNode = ''
      this.paths = []
      this.clearSelection()
    },
    
    // 分析路径
    analyzePath() {
      if (!this.pathStartNode || !this.pathEndNode || this.pathStartNode === this.pathEndNode) {
        return
      }
      
      this.paths = this.findPaths(this.pathStartNode, this.pathEndNode, this.pathMaxLength)
      console.log('Found paths:', this.paths)
    },
    
    // 查找路径的核心算法
    findPaths(startId, endId, maxLength) {
      const paths = []
      const visited = new Set()
      
      // 深度优先搜索
      const dfs = (currentId, currentPath) => {
        if (currentPath.length > maxLength) {
          return
        }
        
        if (currentId === endId) {
          paths.push(currentPath.map(id => this.graphData.nodes.find(n => n.id === id)))
          return
        }
        
        visited.add(currentId)
        
        // 查找从当前节点出发的所有边
        const edges = this.graphData.edges.filter(edge => 
          edge.source.id === currentId || edge.source === currentId
        )
        
        for (const edge of edges) {
          const nextId = typeof edge.target === 'object' ? edge.target.id : edge.target
          if (!visited.has(nextId) && currentPath.length < maxLength) {
            dfs(nextId, [...currentPath, nextId])
          }
        }
        
        visited.delete(currentId)
      }
      
      dfs(startId, [startId])
      return paths
    },
    
    // 高亮显示路径
    highlightPath(path) {
      if (!this.chart) {
        return
      }
      
      // 清除之前的高亮
      this.chart.dispatchAction({
        type: 'downplay',
        seriesIndex: 0
      })
      
      // 高亮路径上的节点
      for (const node of path) {
        this.chart.dispatchAction({
          type: 'highlight',
          seriesIndex: 0,
          dataIndex: this.graphData.nodes.findIndex(n => n.id === node.id)
        })
      }
      
      // 高亮路径上的边
      for (let i = 0; i < path.length - 1; i++) {
        const sourceId = path[i].id
        const targetId = path[i + 1].id
        const edgeIndex = this.graphData.edges.findIndex(edge => 
          (edge.source.id === sourceId || edge.source === sourceId) &&
          (edge.target.id === targetId || edge.target === targetId)
        )
        
        if (edgeIndex !== -1) {
          this.chart.dispatchAction({
            type: 'highlight',
            seriesIndex: 0,
            dataIndex: edgeIndex
          })
        }
      }
    },
    
    // 导出数据
    exportData(format) {
      switch (format) {
        case 'csv':
          this.exportToCSV()
          break
        case 'json':
          this.exportToJSON()
          break
        case 'png':
          this.exportToPNG()
          break
        default:
          break
      }
    },
    
    // 导出为CSV
    exportToCSV() {
      // 准备节点数据
      const nodesCSV = [['ID', '标签(中文)', '标签(英文)', '类型', '角色', '频次', '重要性分数']]
      this.graphData.nodes.forEach(node => {
        nodesCSV.push([
          node.id,
          node.label_zh || '',
          node.label || '',
          node.ingredient_type || '',
          node.role || '',
          node.freq || 0,
          node.importance_score || 0
        ])
      })
      
      // 准备边数据
      const edgesCSV = [['源节点', '目标节点', '权重', '类型']]
      this.graphData.edges.forEach(edge => {
        const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source
        const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target
        edgesCSV.push([
          sourceId,
          targetId,
          edge.weight || 0,
          edge.type || ''
        ])
      })
      
      // 合并CSV数据
      const csvContent = [
        '节点数据',
        nodesCSV.map(row => row.join(',')).join('\n'),
        '',
        '边数据',
        edgesCSV.map(row => row.join(',')).join('\n')
      ].join('\n')
      
      // 创建下载链接
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `flavor-graph-${new Date().toISOString().slice(0, 10)}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    
    // 导出为JSON
    exportToJSON() {
      const exportData = {
        nodes: this.graphData.nodes,
        edges: this.graphData.edges,
        stats: this.graphStats,
        exportDate: new Date().toISOString()
      }
      
      const jsonContent = JSON.stringify(exportData, null, 2)
      const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `flavor-graph-${new Date().toISOString().slice(0, 10)}.json`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    
    // 导出为PNG
    exportToPNG() {
      if (this.chart) {
        const url = this.chart.getDataURL({
          pixelRatio: 2,
          backgroundColor: '#121212'
        })
        
        const link = document.createElement('a')
        link.setAttribute('href', url)
        link.setAttribute('download', `flavor-graph-${new Date().toISOString().slice(0, 10)}.png`)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
    }
  }
</script>

<style scoped>
.flavor-graph {
  min-height: 100vh;
  background: var(--color-bg-1);
}

.graph-header {
  background: linear-gradient(135deg, var(--color-bg-2) 0%, var(--color-bg-3) 100%);
  padding: var(--spacing-xxl) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border-subtle);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-serif);
}

.page-subtitle {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  max-width: 600px;
}

.graph-main {
  padding: var(--spacing-xl) 0;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl);
}

.graph-layout {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.graph-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.sidebar-card {
  padding: var(--spacing-lg);
}

.sidebar-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-md);
  font-family: var(--font-serif);
}

.layer-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.layer-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  color: var(--color-text-primary);
  font-size: 0.95rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  text-align: left;
}

.layer-btn:hover {
  border-color: var(--color-gold-400);
  background: var(--color-bg-3);
}

.layer-btn.active {
  background: var(--color-gold-400);
  color: var(--color-bg-1);
  border-color: var(--color-gold-400);
  font-weight: 600;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) 0;
}

.filter-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--color-gold-400);
}

.filter-checkbox label {
  cursor: pointer;
  user-select: none;
}

.filter-label {
  color: var(--color-text-primary);
  font-size: 0.95rem;
}

.threshold-control {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.control-label {
  font-size: 0.9rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.control-range {
  width: 100%;
  height: 6px;
  background: var(--color-bg-3);
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
}

.control-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: var(--color-gold-400);
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.control-range::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  background: var(--color-gold-300);
}

.control-value {
  font-size: 0.9rem;
  color: var(--color-gold-300);
  font-weight: 600;
  text-align: right;
}

.search-box {
  display: flex;
  gap: var(--spacing-sm);
}

.search-input {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  color: var(--color-text-primary);
  font-size: 0.95rem;
  transition: all var(--transition-normal);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-gold-400);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
}

.search-btn {
  padding: var(--spacing-sm);
  background: var(--color-gold-400);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-bg-1);
  cursor: pointer;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-btn:hover {
  background: var(--color-gold-300);
}

.graph-content {
  display: flex;
  flex-direction: column;
}

.graph-container {
  padding: var(--spacing-lg);
  min-height: 700px;
}

.graph-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-subtle);
}

.toolbar-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.info-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.info-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-gold-300);
}

.toolbar-stats {
  display: flex;
  gap: var(--spacing-md);
}

.stat-item {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.graph-visualization {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 600px;
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.graph-loading,
.graph-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  color: var(--color-text-secondary);
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-bg-3);
  border-top-color: var(--color-gold-400);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-icon {
  font-size: 2rem;
}

.graph-canvas {
  width: 100%;
  height: 600px;
}

.echarts-container {
  width: 100%;
  height: 100%;
}

.graph-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.details-card {
  padding: var(--spacing-lg);
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-subtle);
}

.details-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold-200);
  font-family: var(--font-serif);
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: var(--color-bg-3);
  color: var(--color-text-secondary);
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  transition: all var(--transition-normal);
}

.close-btn:hover {
  background: var(--color-gold-400);
  color: var(--color-bg-1);
}

.node-basic-info {
  margin-bottom: var(--spacing-lg);
}

.node-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.name-zh {
  color: var(--color-gold-200);
}

.name-en {
  color: var(--color-text-primary);
}

.name-separator {
  color: var(--color-text-tertiary);
  margin: 0 var(--spacing-xs);
}

.node-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.meta-tag {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-3);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.meta-tag.key-node {
  background: rgba(212, 175, 55, 0.2);
  color: var(--color-gold-300);
  font-weight: 600;
}

.node-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.stat-value {
  color: var(--color-gold-300);
  font-weight: 600;
}

.anchor-section {
  margin-bottom: var(--spacing-lg);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border-subtle);
}

.anchor-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.anchor-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
}

.anchor-label {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.anchor-value {
  color: var(--color-text-primary);
  font-weight: 500;
}

.flavor-features {
  margin-bottom: var(--spacing-lg);
}

.feature-bars {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.feature-bar {
  display: grid;
  grid-template-columns: 40px 1fr 50px;
  align-items: center;
  gap: var(--spacing-sm);
}

.feature-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.feature-progress {
  height: 8px;
  background: var(--color-bg-3);
  border-radius: 4px;
  overflow: hidden;
}

.feature-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-gold-400), var(--color-gold-300));
  transition: width var(--transition-normal);
}

.feature-value {
  font-size: 0.85rem;
  color: var(--color-gold-300);
  font-weight: 600;
  text-align: right;
}

.neighbors-section {
  margin-bottom: var(--spacing-lg);
}

.neighbors-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.neighbor-item {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
}

.neighbor-name {
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.neighbor-weight {
  color: var(--color-gold-300);
  font-weight: 600;
  font-size: 0.9rem;
}

.edge-basic-info {
  margin-bottom: var(--spacing-lg);
}

.edge-nodes {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
  flex-wrap: wrap;
}

.edge-node {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.edge-arrow {
  color: var(--color-gold-300);
}

.edge-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.edge-metrics {
  margin-bottom: var(--spacing-lg);
}

.metrics-grid {
  display: grid;
  gap: var(--spacing-xs);
}

.metric-item {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
}

.metric-label {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
}

.metric-value {
  color: var(--color-gold-300);
  font-weight: 600;
  font-size: 0.9rem;
}

.edge-summary {
  margin-bottom: var(--spacing-lg);
}

.summary-text {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

.details-placeholder {
  padding: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  text-align: center;
  color: var(--color-text-tertiary);
}

.placeholder-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.graph-stats-section {
  margin-top: var(--spacing-xl);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
  margin-top: var(--spacing-xl);
}

.chart-card {
  padding: var(--spacing-lg);
}

.compare-chart-card {
  grid-column: 1 / -1;
}

.chart-container {
  width: 100%;
  height: 400px;
  margin-top: var(--spacing-md);
}

/* 原料对比样式 */
.compare-nodes {
  margin: var(--spacing-md) 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.compare-node-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
}

.compare-node-item .node-info {
  flex: 1;
}

.compare-node-item .node-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-primary);
}

.compare-node-item .node-meta {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.remove-node-btn {
  background: var(--color-danger);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-node-btn:hover {
  background: var(--color-danger-hover);
  transform: scale(1.1);
}

.compare-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.compare-actions .btn {
  flex: 1;
}

.placeholder-hint {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
}

/* 路径分析样式 */
.path-analysis-form {
  margin: var(--spacing-md) 0;
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 600;
  color: var(--color-text-primary);
}

.form-select {
  width: 100%;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  background: var(--color-bg-1);
  color: var(--color-text-primary);
  font-size: 1rem;
}

.form-select:focus {
  outline: none;
  border-color: var(--color-gold-200);
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2);
}

.btn.full-width {
  width: 100%;
}

.path-results {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border-subtle);
}

.path-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.path-item {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: all 0.2s ease;
}

.path-item:hover {
  background: var(--color-bg-3);
  border-color: var(--color-gold-200);
}

.path-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
}

.path-number {
  font-weight: 600;
  color: var(--color-gold-200);
}

.path-length {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.path-nodes {
  font-size: 0.9rem;
  line-height: 1.4;
  color: var(--color-text-primary);
}

/* 工具栏样式 */
.toolbar-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.stat-card {
  padding: var(--spacing-lg);
}

.stat-card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-md);
  font-family: var(--font-serif);
}

.stat-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.stat-list-item {
  display: grid;
  grid-template-columns: 30px 1fr 60px;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
}

.stat-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-gold-400);
  color: var(--color-bg-1);
  border-radius: 50%;
  font-size: 0.8rem;
  font-weight: 600;
}

.stat-name {
  color: var(--color-text-primary);
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-score,
.stat-count {
  color: var(--color-gold-300);
  font-weight: 600;
  font-size: 0.9rem;
  text-align: right;
}

.summary-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
}

.summary-label {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.summary-value {
  color: var(--color-gold-300);
  font-weight: 600;
}

.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  font-weight: 500;
}

.btn-primary {
  background: var(--color-gold-400);
  color: var(--color-bg-1);
}

.btn-primary:hover {
  background: var(--color-gold-300);
}

/* 导出下拉菜单样式 */
.export-dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-toggle {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.dropdown-toggle::after {
  content: '▼';
  font-size: 0.8rem;
  margin-left: var(--spacing-xs);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--spacing-xs);
  background: var(--color-bg-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 150px;
  z-index: 1000;
  display: none;
}

.export-dropdown:hover .dropdown-menu {
  display: block;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  font-size: 0.9rem;
  color: var(--color-text-primary);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.dropdown-item:hover {
  background: var(--color-bg-3);
  color: var(--color-gold-200);
}

.card {
  background: var(--color-bg-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

@media (max-width: 1200px) {
  .graph-layout {
    grid-template-columns: 240px 1fr 280px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .page-subtitle {
    font-size: 1rem;
  }
}

@media (max-width: 992px) {
  .graph-layout {
    grid-template-columns: 1fr;
  }
  
  .graph-sidebar {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
  
  .graph-details {
    max-height: 500px;
  }
  
  .details-card {
    max-height: 400px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .graph-container {
    min-height: 500px;
  }
  
  .graph-toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .toolbar-info,
  .toolbar-stats,
  .toolbar-actions {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 768px) {
  .graph-header {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .container {
    padding: 0 var(--spacing-md);
  }
  
  .page-title {
    font-size: 1.8rem;
  }
  
  .page-subtitle {
    font-size: 1rem;
  }
  
  .graph-sidebar {
    grid-template-columns: 1fr;
  }
  
  .graph-container {
    min-height: 450px;
  }
  
  .chart-container {
    height: 350px;
  }
  
  .details-card {
    padding: var(--spacing-md);
  }
  
  .sidebar-card {
    padding: var(--spacing-md);
  }
  
  .stat-card {
    padding: var(--spacing-md);
  }
  
  .chart-card {
    padding: var(--spacing-md);
  }
  
  .compare-actions {
    flex-direction: column;
  }
  
  .stat-list-item {
    grid-template-columns: 30px 1fr;
  }
  
  .stat-score,
  .stat-count {
    display: none;
  }
}

@media (max-width: 480px) {
  .graph-header {
    padding: var(--spacing-lg) var(--spacing-sm);
  }
  
  .container {
    padding: 0 var(--spacing-sm);
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .page-subtitle {
    font-size: 0.9rem;
  }
  
  .graph-main {
    padding: var(--spacing-lg) 0;
  }
  
  .graph-container {
    min-height: 400px;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .details-card {
    padding: var(--spacing-sm);
  }
  
  .sidebar-card {
    padding: var(--spacing-sm);
  }
  
  .stat-card {
    padding: var(--spacing-sm);
  }
  
  .chart-card {
    padding: var(--spacing-sm);
  }
  
  .btn {
    font-size: 0.9rem;
    padding: var(--spacing-xs) var(--spacing-sm);
  }
  
  .control-range {
    margin-bottom: var(--spacing-xs);
  }
  
  .feature-label {
    width: 35px;
    font-size: 0.8rem;
  }
  
  .feature-value {
    width: 35px;
    font-size: 0.8rem;
  }
  
  .stat-list-item {
    grid-template-columns: 25px 1fr;
    gap: var(--spacing-xs);
  }
  
  .stat-rank {
    width: 20px;
    height: 20px;
    font-size: 0.7rem;
  }
  
  .stat-name {
    font-size: 0.8rem;
  }
  
  .node-name {
    font-size: 1rem;
  }
  
  .details-title {
    font-size: 1.1rem;
  }
  
  .section-title {
    font-size: 0.9rem;
  }
}
</style>