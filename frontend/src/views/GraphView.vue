<template>
  <div class="graph">
    <section class="graph-header">
      <div class="graph-header-inner">
        <h1 class="graph-title">风味图谱</h1>
        <p class="graph-subtitle">探索原料之间的关联关系与替代可能性</p>
      </div>
    </section>
    
    <section class="graph-content">
      <div class="graph-card card">
        <div class="graph-card-header">
          <h2 class="graph-card-title">全局 Canonical 图</h2>
          <p class="graph-card-subtitle">展示所有原料之间的关系网络</p>
        </div>
        <div class="graph-card-body">
          <div class="graph-visualization">
            <div class="graph-controls">
              <div class="control-group">
                <label class="form-label">关系类型</label>
                <select v-model="relationType" class="form-select">
                  <option value="cooccurrence">共现关系</option>
                  <option value="similarity">风味相似性</option>
                  <option value="substitute">替代关系</option>
                </select>
              </div>
              <div class="control-group">
                <label class="form-label">筛选阈值</label>
                <input 
                  type="range" 
                  v-model.number="threshold" 
                  min="0" 
                  max="1" 
                  step="0.1"
                  class="form-range"
                >
                <span class="range-value">{{ threshold.toFixed(1) }}</span>
              </div>
            </div>
            <div class="graph-container">
              <div class="graph-placeholder">
                <svg class="graph-icon" viewBox="0 0 48 48" fill="none">
                  <path d="M24 8V40" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <path d="M8 24H40" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  <circle cx="24" cy="24" r="8" stroke="currentColor" stroke-width="2"/>
                </svg>
                <p>图谱可视化区域</p>
                <p class="graph-info">点击节点查看详细信息</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="selectedNode" class="graph-card card">
        <div class="graph-card-header">
          <h2 class="graph-card-title">节点详情</h2>
          <p class="graph-card-subtitle">{{ selectedNode.name }}</p>
        </div>
        <div class="graph-card-body">
          <div class="node-details">
            <div class="detail-item">
              <span class="detail-label">类型:</span>
              <span class="detail-value">{{ selectedNode.type }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">出现频率:</span>
              <span class="detail-value">{{ selectedNode.frequency }}次</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">度数中心性:</span>
              <span class="detail-value">{{ selectedNode.centrality.toFixed(3) }}</span>
            </div>
            
            <div class="section-title">邻居节点</div>
            <div class="neighbors-list">
              <div 
                v-for="neighbor in selectedNode.neighbors" 
                :key="neighbor.id"
                class="neighbor-item"
              >
                <span class="neighbor-name">{{ neighbor.name }}</span>
                <span class="neighbor-weight">{{ neighbor.weight.toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="section-title">替代候选</div>
            <div class="substitutes-list">
              <div 
                v-for="substitute in selectedNode.substitutes" 
                :key="substitute.id"
                class="substitute-item"
              >
                <span class="substitute-name">{{ substitute.name }}</span>
                <span class="substitute-similarity">{{ substitute.similarity.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="graph-card card">
        <div class="graph-card-header">
          <h2 class="graph-card-title">关系分析</h2>
          <p class="graph-card-subtitle">基于共现关系的统计分析</p>
        </div>
        <div class="graph-card-body">
          <div class="relation-stats">
            <div class="stat-item">
              <span class="stat-label">总原料数</span>
              <span class="stat-value">{{ stats.totalIngredients }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总关系数</span>
              <span class="stat-value">{{ stats.totalRelations }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">网络密度</span>
              <span class="stat-value">{{ stats.density.toFixed(3) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平均度数</span>
              <span class="stat-value">{{ stats.avgDegree.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'GraphView',
  data() {
    return {
      relationType: 'cooccurrence',
      threshold: 0.3,
      selectedNode: null,
      stats: {
        totalIngredients: 120,
        totalRelations: 856,
        density: 0.12,
        avgDegree: 14.27
      }
    }
  },
  mounted() {
    // 模拟点击节点
    setTimeout(() => {
      this.selectedNode = {
        id: 1,
        name: 'Tequila',
        type: 'Base Spirit',
        frequency: 156,
        centrality: 0.876,
        neighbors: [
          { id: 2, name: 'Lime Juice', weight: 0.92 },
          { id: 3, name: 'Triple Sec', weight: 0.88 },
          { id: 4, name: 'Salt', weight: 0.76 },
          { id: 5, name: 'Orange Juice', weight: 0.65 }
        ],
        substitutes: [
          { id: 6, name: 'Mezcal', similarity: 0.95 },
          { id: 7, name: 'Vodka', similarity: 0.60 },
          { id: 8, name: 'Gin', similarity: 0.45 }
        ]
      }
    }, 1000)
  }
}
</script>

<style scoped>
.graph {
  min-height: 100vh;
  background: var(--color-bg-1);
}

.graph-header {
  background: linear-gradient(135deg, var(--color-bg-2) 0%, var(--color-bg-3) 100%);
  padding: var(--spacing-xxl) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border-subtle);
}

.graph-header-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.graph-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-serif);
}

.graph-subtitle {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  max-width: 600px;
}

.graph-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
  display: grid;
  gap: var(--spacing-xl);
  grid-template-columns: 1fr;
}

.graph-card {
  padding: var(--spacing-xl);
}

.graph-card-header {
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-md);
}

.graph-card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-xs);
  font-family: var(--font-serif);
}

.graph-card-subtitle {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.graph-visualization {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.graph-controls {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  align-items: end;
}

.control-group {
  flex: 1;
  min-width: 200px;
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.form-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  color: var(--color-text-primary);
  font-size: 1rem;
  transition: all var(--transition-normal);
}

.form-select:focus {
  outline: none;
  border-color: var(--color-gold-400);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
}

.form-range {
  width: 100%;
  margin: var(--spacing-sm) 0;
}

.range-value {
  display: block;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-gold-300);
  font-weight: 600;
}

.graph-container {
  height: 600px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.graph-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  color: var(--color-text-tertiary);
  text-align: center;
}

.graph-icon {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.graph-info {
  font-size: 0.9rem;
  max-width: 300px;
}

.node-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.detail-label {
  color: var(--color-text-secondary);
}

.detail-value {
  font-weight: 600;
  color: var(--color-gold-300);
}

.section-title {
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  font-size: 1rem;
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-xs);
}

.neighbors-list,
.substitutes-list {
  display: grid;
  gap: var(--spacing-sm);
}

.neighbor-item,
.substitute-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.neighbor-name,
.substitute-name {
  color: var(--color-text-primary);
}

.neighbor-weight,
.substitute-similarity {
  font-weight: 600;
  color: var(--color-gold-300);
  font-size: 0.9rem;
}

.relation-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.stat-item {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-gold-300);
}

@media (max-width: 768px) {
  .graph-header {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .graph-content {
    padding: var(--spacing-md);
  }
  
  .graph-card {
    padding: var(--spacing-lg);
  }
  
  .graph-container {
    height: 400px;
  }
  
  .graph-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-group {
    min-width: auto;
  }
  
  .relation-stats {
    grid-template-columns: 1fr;
  }
}
</style>