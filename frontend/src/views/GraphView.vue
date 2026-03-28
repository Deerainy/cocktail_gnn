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
                <label 
                  v-for="type in ingredientTypes" 
                  :key="type.value"
                  class="filter-checkbox"
                >
                  <input 
                    type="checkbox" 
                    :value="type.value"
                    v-model="selectedTypes"
                    @change="applyFilters"
                  >
                  <span class="filter-label">{{ type.label }}</span>
                </label>
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
            <div v-if="selectedNode" class="details-card card">
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
                    <span class="anchor-value">{{ (selectedNode.anchor.match_confidence * 100).toFixed(1) }}%</span>
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
                    <span class="neighbor-weight">{{ neighbor.weight.toFixed(2) }}</span>
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
                  <span class="meta-tag">权重: {{ selectedEdge.weight.toFixed(2) }}</span>
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
                  <span class="stat-score">{{ item.score.toFixed(3) }}</span>
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
      
      graphStats: {
        summary: {},
        top_nodes: [],
        top_freq: [],
        top_anchors: []
      }
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
  
  methods: {
    async fetchGraphData() {
      this.loading = true
      this.error = null
      
      try {
        // 生成缓存键
        const cacheKey = this.getCacheKey()
        
        // 尝试从缓存中获取数据
        const cachedData = this.getFromCache(cacheKey)
        if (cachedData) {
          console.log('使用缓存数据:', cachedData)
          this.graphData = cachedData
          this.loading = false
          await this.$nextTick()
          this.initChart()
          return
        }
        
        const params = new URLSearchParams({
          layer: this.currentLayer,
          min_weight: this.minWeight,
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
            nodes: data.data.nodes.map(node => ({
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
            edges: data.data.edges.map(edge => ({
              source: String(edge.source),
              target: String(edge.target),
              value: edge.weight
            }))
          }
          
          // 保存数据到缓存
          this.saveToCache(cacheKey, this.graphData)
          
          console.log('Graph data:', this.graphData)
          this.loading = false
          await this.$nextTick()
          this.initChart()
        } else {
          this.error = data.message || '获取图谱数据失败'
          console.error('Error fetching graph data:', this.error)
          this.loading = false
        }
      } catch (err) {
        console.error('获取图谱数据失败:', err)
        this.error = '网络错误，请检查后端服务是否启动'
        this.loading = false
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
      this.nodeDetails = null
      this.edgeDetails = null
      
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
      
      const option = {
        title: {
          text: '风味图谱',
          subtext: this.getLayerLabel(this.currentLayer),
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            if (params.dataType === 'node') {
              return `
                <div style="font-weight: bold; margin-bottom: 5px;">${params.data.name}</div>
                <div>类型: ${params.data.ingredient_type || '未知'}</div>
                <div>角色: ${params.data.role || '未知'}</div>
                <div>频次: ${params.data.freq || 0}</div>
                ${params.data.is_key_node ? '<div style="color: #D4AF37;">关键节点</div>' : ''}
              `
            } else if (params.dataType === 'edge') {
              return `
                <div>权重: ${params.data.value.toFixed(2)}</div>
              `
            }
          }
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
              symbolSize: node.is_key_node ? 30 : 20,
              itemStyle: {
                color: node.is_key_node ? '#FFA500' : '#D4AF37'
              },
              ...node
            })),
            links: this.graphData.edges.map(edge => ({
              source: edge.source,
              target: edge.target,
              lineStyle: {
                width: edge.value * 5,
                color: '#999999'
              },
              ...edge
            })),
            roam: true,
            label: {
              show: true,
              position: 'right',
              formatter: '{b}'
            },
            lineStyle: {
              opacity: 0.9,
              width: 2,
              curveness: 0.1
            },
            force: {
              repulsion: 1000,
              edgeLength: [80, 120]
            }
          }
        ]
      }
      
      console.log('Chart option:', option)
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
      
      this.fetchNodeDetails(node.id).then(detail => {
        if (detail) {
          this.selectedNode = { ...node, ...detail }
        }
      })
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
      this.currentLayer = layer
      this.clearSelection()
      this.fetchGraphData()
      this.fetchGraphStats()
    },
    
    applyFilters() {
      this.clearSelection()
      this.fetchGraphData()
      this.fetchGraphStats()
    },
    
    handleSearch() {
      this.clearSelection()
      this.fetchGraphData()
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
      const types = this.selectedTypes.sort().join(',')
      return `graph_data_${this.currentLayer}_${this.minWeight}_${types}_${this.searchKeyword}`
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
  cursor: pointer;
  padding: var(--spacing-xs) 0;
}

.filter-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--color-gold-400);
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
}

@media (max-width: 768px) {
  .graph-header {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .container {
    padding: 0 var(--spacing-md);
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .page-subtitle {
    font-size: 1rem;
  }
  
  .graph-sidebar {
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
  
  .stat-list-item {
    grid-template-columns: 30px 1fr;
  }
  
  .stat-score,
  .stat-count {
    display: none;
  }
}
</style>