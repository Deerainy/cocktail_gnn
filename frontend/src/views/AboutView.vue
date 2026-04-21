<template>
  <div class="about">
    <section class="about-header">
      <div class="about-header-inner">
        <h1 class="about-title">关于系统</h1>
        <p class="about-subtitle">基于图结构优化的鸡尾酒风味组合生成系统</p>
      </div>
    </section>
    
    <section class="about-content">
      <div class="about-tabs">
        <div class="tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
            class="tab-button"
          >
            {{ tab.title }}
          </button>
        </div>
        
        <div class="tab-content">
          <!-- 核心功能与技术 -->
          <div v-if="activeTab === 'core'" class="tab-pane">
            <h2 class="tab-title">核心功能与技术</h2>
            <div class="feature-grid">
              <div class="feature-item">
                <div class="feature-icon">
                  <span class="icon-number">01</span>
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">数据采集与预处理</h3>
                  <p class="feature-desc">收集5000+鸡尾酒配方，提取原料和风味特征</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon">
                  <span class="icon-number">02</span>
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">图结构构建</h3>
                  <p class="feature-desc">基于原料共现关系和风味相似性构建图结构</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon">
                  <span class="icon-number">03</span>
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">SQE 评分模型</h3>
                  <p class="feature-desc">协同、冲突、平衡三大组件的综合评分</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon">
                  <span class="icon-number">04</span>
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">优化算法</h3>
                  <p class="feature-desc">原料替代和配方优化的智能算法</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon">
                  <span class="icon-number">05</span>
                </div>
                <div class="feature-content">
                  <h3 class="feature-title">交互式前端</h3>
                  <p class="feature-desc">配方分析、风味图谱、组合调整等功能</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- SQE 方法与图建模 -->
          <div v-if="activeTab === 'sqe'" class="tab-pane">
            <h2 class="tab-title">SQE 方法与图建模</h2>
            <div class="method-modeling-grid">
              <div class="method-section">
                <h3 class="section-title">SQE 评分方法</h3>
                <div class="sqe-components">
                  <div class="sqe-component">
                    <h4 class="component-title">协同 (40%)</h4>
                    <p class="component-desc">衡量原料之间的风味协同效应</p>
                  </div>
                  <div class="sqe-component">
                    <h4 class="component-title">冲突 (30%)</h4>
                    <p class="component-desc">评估原料之间的风味冲突</p>
                  </div>
                  <div class="sqe-component">
                    <h4 class="component-title">平衡 (30%)</h4>
                    <p class="component-desc">分析配方中各原料的比例和角色平衡</p>
                  </div>
                </div>
                <div class="sqe-formula">
                  <p class="formula">SQE(G) = 0.4 × Synergy + 0.3 × (1 - Conflict) + 0.3 × Balance</p>
                </div>
              </div>
              <div class="modeling-section">
                <h3 class="section-title">图建模流程</h3>
                <div class="modeling-steps">
                  <div class="modeling-step">
                    <span class="step-number">1</span>
                    <p class="step-desc">节点定义：原料作为图中的节点</p>
                  </div>
                  <div class="modeling-step">
                    <span class="step-number">2</span>
                    <p class="step-desc">边的构建：基于原料关系强度</p>
                  </div>
                  <div class="modeling-step">
                    <span class="step-number">3</span>
                    <p class="step-desc">权重计算：综合多种因素</p>
                  </div>
                  <div class="modeling-step">
                    <span class="step-number">4</span>
                    <p class="step-desc">图的优化：识别重要节点和子图</p>
                  </div>
                  <div class="modeling-step">
                    <span class="step-number">5</span>
                    <p class="step-desc">应用场景：原料替代、配方生成</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 系统架构与数据 -->
          <div v-if="activeTab === 'architecture'" class="tab-pane">
            <h2 class="tab-title">系统架构与数据</h2>
            <div class="architecture-data-grid">
              <div class="architecture-section">
                <h3 class="section-title">系统架构</h3>
                <div class="architecture-layers">
                  <div class="architecture-layer">
                    <h4 class="layer-title">前端层</h4>
                    <div class="layer-tech">
                      <span class="tech-tag">Vue.js 3</span>
                      <span class="tech-tag">Vue Router</span>
                      <span class="tech-tag">CSS Variables</span>
                    </div>
                  </div>
                  <div class="architecture-layer">
                    <h4 class="layer-title">后端层</h4>
                    <div class="layer-tech">
                      <span class="tech-tag">Spring Boot</span>
                      <span class="tech-tag">Java</span>
                      <span class="tech-tag">RESTful API</span>
                    </div>
                  </div>
                  <div class="architecture-layer">
                    <h4 class="layer-title">算法层</h4>
                    <div class="layer-tech">
                      <span class="tech-tag">图算法</span>
                      <span class="tech-tag">机器学习</span>
                      <span class="tech-tag">优化算法</span>
                    </div>
                  </div>
                  <div class="architecture-layer">
                    <h4 class="layer-title">数据层</h4>
                    <div class="layer-tech">
                      <span class="tech-tag">关系型数据库</span>
                      <span class="tech-tag">图数据库</span>
                      <span class="tech-tag">缓存</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="data-section">
                <h3 class="section-title">数据来源</h3>
                <div class="data-sources">
                  <div class="source-item">
                    <h4 class="source-title">公开配方数据库</h4>
                    <p class="source-desc">5000+ 经典和现代鸡尾酒配方</p>
                  </div>
                  <div class="source-item">
                    <h4 class="source-title">专业调酒书籍</h4>
                    <p class="source-desc">权威调酒书籍中的配方和原则</p>
                  </div>
                  <div class="source-item">
                    <h4 class="source-title">用户评价数据</h4>
                    <p class="source-desc">用户对鸡尾酒的评价和反馈</p>
                  </div>
                  <div class="source-item">
                    <h4 class="source-title">风味特征数据库</h4>
                    <p class="source-desc">原料的风味特征数据</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 用户界面 -->
          <div v-if="activeTab === 'ui'" class="tab-pane">
            <h2 class="tab-title">用户界面</h2>
            <div class="ui-grid">
              <div class="ui-item">
                <h3 class="ui-title">设计理念</h3>
                <p class="ui-desc">爵士酒吧风格，深棕色背景和金色点缀，体现鸡尾酒文化的优雅与精致</p>
              </div>
              <div class="ui-item">
                <h3 class="ui-title">交互设计</h3>
                <p class="ui-desc">直观的操作界面，包括拖拽交互、实时反馈、动画过渡等</p>
              </div>
              <div class="ui-item">
                <h3 class="ui-title">响应式布局</h3>
                <p class="ui-desc">适配不同屏幕尺寸，从桌面端到移动端都能提供良好的用户体验</p>
              </div>
              <div class="ui-item">
                <h3 class="ui-title">色彩方案</h3>
                <div class="color-palette">
                  <div class="color-item">
                    <div class="color-swatch" style="background: var(--color-bg-0);"></div>
                    <span class="color-name">深棕色</span>
                  </div>
                  <div class="color-item">
                    <div class="color-swatch" style="background: var(--color-gold-400);"></div>
                    <span class="color-name">金色</span>
                  </div>
                  <div class="color-item">
                    <div class="color-swatch" style="background: var(--color-text-primary);"></div>
                    <span class="color-name">主文字</span>
                  </div>
                  <div class="color-item">
                    <div class="color-swatch" style="background: var(--color-text-secondary);"></div>
                    <span class="color-name">次文字</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'AboutView',
  data() {
    return {
      activeTab: 'core',
      tabs: [
        { id: 'core', title: '核心功能与技术' },
        { id: 'sqe', title: 'SQE 方法与图建模' },
        { id: 'architecture', title: '系统架构与数据' },
        { id: 'ui', title: '用户界面' }
      ]
    };
  }
}
</script>

<style scoped>
.about {
  min-height: 100vh;
  background: var(--color-bg-1);
}

.about-header {
  background: linear-gradient(135deg, var(--color-bg-2) 0%, var(--color-bg-3) 100%);
  padding: var(--spacing-xxl) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border-subtle);
}

.about-header-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.about-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-serif);
}

.about-subtitle {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  max-width: 600px;
}

.about-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
}

/* 选项卡样式 */
.about-tabs {
  background: var(--color-bg-2);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.tabs {
  display: flex;
  background: var(--color-bg-3);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.tab-button {
  padding: var(--spacing-md) var(--spacing-lg);
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
  white-space: nowrap;
}

.tab-button:hover {
  color: var(--color-gold-300);
  background: rgba(212, 175, 55, 0.05);
}

.tab-button.active {
  color: var(--color-gold-200);
  border-bottom-color: var(--color-gold-400);
  background: var(--color-bg-2);
}

.tab-content {
  padding: var(--spacing-xl);
}

.tab-pane {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tab-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-lg);
  font-family: var(--font-serif);
}

/* 核心功能与技术 */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-md);
}

.feature-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.1);
  border-color: var(--color-gold-400);
}

.feature-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-300));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-number {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-bg-0);
}

.feature-content {
  flex: 1;
}

.feature-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.feature-desc {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

/* SQE 方法与图建模 */
.method-modeling-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.method-section,
.modeling-section {
  padding: var(--spacing-md);
  background: var(--color-bg-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.method-section:hover,
.modeling-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.1);
  border-color: var(--color-gold-400);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-md);
  font-family: var(--font-serif);
}

/* SQE 方法 */
.sqe-components {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.sqe-component {
  padding: var(--spacing-sm);
  background: var(--color-bg-0);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.component-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.component-desc {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.sqe-formula {
  padding: var(--spacing-sm);
  background: rgba(212, 175, 55, 0.1);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-gold-400);
}

.formula {
  font-size: 0.9rem;
  color: var(--color-text-primary);
  text-align: center;
  margin: 0;
}

/* 图建模流程 */
.modeling-steps {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.modeling-step {
  display: flex;
  gap: var(--spacing-sm);
  align-items: flex-start;
  padding: var(--spacing-sm);
  background: var(--color-bg-0);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-gold-400);
  color: var(--color-bg-0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}

.step-desc {
  flex: 1;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin: 0;
}

/* 系统架构与数据 */
.architecture-data-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.architecture-section,
.data-section {
  padding: var(--spacing-md);
  background: var(--color-bg-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.architecture-section:hover,
.data-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.1);
  border-color: var(--color-gold-400);
}

/* 系统架构 */
.architecture-layers {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.architecture-layer {
  padding: var(--spacing-sm);
  background: var(--color-bg-0);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.layer-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.layer-tech {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.tech-tag {
  padding: 2px 8px;
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: var(--color-gold-300);
  border: 1px solid var(--color-gold-400);
}

/* 数据来源 */
.data-sources {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.source-item {
  padding: var(--spacing-sm);
  background: var(--color-bg-0);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.source-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.source-desc {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin: 0;
}

/* 用户界面 */
.ui-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
}

.ui-item {
  padding: var(--spacing-md);
  background: var(--color-bg-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.ui-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.1);
  border-color: var(--color-gold-400);
}

.ui-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.ui-desc {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin: 0;
}

/* 色彩方案 */
.color-palette {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.color-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.color-swatch {
  width: 50px;
  height: 50px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.color-name {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .method-modeling-grid,
  .architecture-data-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .about-header {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .about-content {
    padding: var(--spacing-md);
  }
  
  .tabs {
    flex-direction: column;
  }
  
  .tab-button {
    text-align: left;
    border-bottom: 1px solid var(--color-border);
    border-left: 3px solid transparent;
  }
  
  .tab-button.active {
    border-left-color: var(--color-gold-400);
    border-bottom-color: var(--color-border);
  }
  
  .tab-content {
    padding: var(--spacing-lg);
  }
  
  .feature-grid,
  .ui-grid {
    grid-template-columns: 1fr;
  }
  
  .color-palette {
    justify-content: center;
  }
}
</style>