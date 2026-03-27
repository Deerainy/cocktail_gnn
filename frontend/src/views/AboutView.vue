<template>
  <div class="about">
    <section class="about-header">
      <div class="about-header-inner">
        <h1 class="about-title">关于系统</h1>
        <p class="about-subtitle">基于图结构优化的鸡尾酒风味组合生成系统</p>
      </div>
    </section>
    
    <section class="about-content">
      <div class="about-card card">
        <div class="about-card-header">
          <h2 class="about-card-title">技术路线图</h2>
        </div>
        <div class="about-card-body">
          <div class="roadmap">
            <div class="roadmap-item">
              <div class="roadmap-step">01</div>
              <div class="roadmap-content">
                <h3 class="roadmap-title">数据采集与预处理</h3>
                <p class="roadmap-desc">收集鸡尾酒配方数据，进行规范化处理，提取原料和风味特征</p>
              </div>
            </div>
            <div class="roadmap-item">
              <div class="roadmap-step">02</div>
              <div class="roadmap-content">
                <h3 class="roadmap-title">图结构构建</h3>
                <p class="roadmap-desc">基于原料共现关系和风味相似性构建图结构，节点为原料，边为关系强度</p>
              </div>
            </div>
            <div class="roadmap-item">
              <div class="roadmap-step">03</div>
              <div class="roadmap-content">
                <h3 class="roadmap-title">SQE 评分模型</h3>
                <p class="roadmap-desc">构建协同、冲突、平衡三大组件的评分模型，计算配方的整体SQE得分</p>
              </div>
            </div>
            <div class="roadmap-item">
              <div class="roadmap-step">04</div>
              <div class="roadmap-content">
                <h3 class="roadmap-title">优化算法</h3>
                <p class="roadmap-desc">基于图结构和SQE模型，开发原料替代和配方优化算法</p>
              </div>
            </div>
            <div class="roadmap-item">
              <div class="roadmap-step">05</div>
              <div class="roadmap-content">
                <h3 class="roadmap-title">前端实现</h3>
                <p class="roadmap-desc">开发交互式前端界面，实现配方分析、风味图谱、组合调整等功能</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="about-card card">
        <div class="about-card-header">
          <h2 class="about-card-title">SQE 方法说明</h2>
        </div>
        <div class="about-card-body">
          <div class="sqe-method">
            <div class="sqe-component">
              <h3 class="component-title">协同 (Synergy)</h3>
              <p class="component-desc">衡量原料之间的风味协同效应，计算不同原料组合产生的正面交互</p>
              <div class="component-details">
                <span class="detail-item">计算方法: 基于历史配方中原料共现频率和用户评价</span>
                <span class="detail-item">权重: 40%</span>
              </div>
            </div>
            <div class="sqe-component">
              <h3 class="component-title">冲突 (Conflict)</h3>
              <p class="component-desc">评估原料之间的风味冲突，识别可能产生负面交互的组合</p>
              <div class="component-details">
                <span class="detail-item">计算方法: 基于风味特征的不兼容性分析</span>
                <span class="detail-item">权重: 30%</span>
              </div>
            </div>
            <div class="sqe-component">
              <h3 class="component-title">平衡 (Balance)</h3>
              <p class="component-desc">分析配方中各原料的比例和角色平衡，确保整体口感协调</p>
              <div class="component-details">
                <span class="detail-item">计算方法: 基于原料比例分布和角色多样性</span>
                <span class="detail-item">权重: 30%</span>
              </div>
            </div>
            <div class="sqe-formula">
              <h3 class="formula-title">SQE 计算公式</h3>
              <div class="formula-content">
                <p>SQE(G) = 0.4 × Synergy + 0.3 × (1 - Conflict) + 0.3 × Balance</p>
                <p>其中，各组件得分范围均为 0-1，SQE 总得分范围为 0-1</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="about-card card">
        <div class="about-card-header">
          <h2 class="about-card-title">图建模流程</h2>
        </div>
        <div class="about-card-body">
          <div class="graph-modeling">
            <div class="modeling-step">
              <h3 class="step-title">1. 节点定义</h3>
              <p class="step-desc">每个原料作为图中的一个节点，包含原料名称、类型、风味特征等属性</p>
            </div>
            <div class="modeling-step">
              <h3 class="step-title">2. 边的构建</h3>
              <p class="step-desc">基于原料共现关系和风味相似性构建边，边的权重表示关系强度</p>
            </div>
            <div class="modeling-step">
              <h3 class="step-title">3. 权重计算</h3>
              <p class="step-desc">综合考虑共现频率、风味相似度、用户评价等因素计算边的权重</p>
            </div>
            <div class="modeling-step">
              <h3 class="step-title">4. 图的优化</h3>
              <p class="step-desc">使用社区检测、中心性分析等方法优化图结构，识别重要节点和子图</p>
            </div>
            <div class="modeling-step">
              <h3 class="step-title">5. 应用场景</h3>
              <p class="step-desc">基于图结构实现原料替代推荐、配方生成、风味分析等功能</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="about-card card">
        <div class="about-card-header">
          <h2 class="about-card-title">数据来源</h2>
        </div>
        <div class="about-card-body">
          <div class="data-sources">
            <div class="source-item">
              <h3 class="source-title">公开配方数据库</h3>
              <p class="source-desc">收集了超过 5000 个经典和现代鸡尾酒配方</p>
            </div>
            <div class="source-item">
              <h3 class="source-title">专业调酒书籍</h3>
              <p class="source-desc">参考权威调酒书籍中的配方和风味搭配原则</p>
            </div>
            <div class="source-item">
              <h3 class="source-title">用户评价数据</h3>
              <p class="source-desc">收集用户对鸡尾酒的评价和反馈，用于优化模型</p>
            </div>
            <div class="source-item">
              <h3 class="source-title">风味特征数据库</h3>
              <p class="source-desc">构建原料的风味特征数据库，包括香气、口感、风味轮廓等</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="about-card card">
        <div class="about-card-header">
          <h2 class="about-card-title">系统架构</h2>
        </div>
        <div class="about-card-body">
          <div class="system-architecture">
            <div class="architecture-layer">
              <h3 class="layer-title">前端层</h3>
              <p class="layer-desc">基于 Vue.js 构建的交互式界面，包括配方分析、风味图谱、组合调整、创新生成等模块</p>
              <div class="layer-tech">
                <span class="tech-tag">Vue.js 3</span>
                <span class="tech-tag">Vue Router</span>
                <span class="tech-tag">CSS Variables</span>
                <span class="tech-tag">Responsive Design</span>
              </div>
            </div>
            <div class="architecture-layer">
              <h3 class="layer-title">后端层</h3>
              <p class="layer-desc">提供 API 接口，处理数据请求，执行图算法和优化计算</p>
              <div class="layer-tech">
                <span class="tech-tag">Spring Boot</span>
                <span class="tech-tag">Java</span>
                <span class="tech-tag">RESTful API</span>
              </div>
            </div>
            <div class="architecture-layer">
              <h3 class="layer-title">算法层</h3>
              <p class="layer-desc">实现图结构构建、SQE 评分、原料替代推荐、配方生成等核心算法</p>
              <div class="layer-tech">
                <span class="tech-tag">图算法</span>
                <span class="tech-tag">机器学习</span>
                <span class="tech-tag">优化算法</span>
              </div>
            </div>
            <div class="architecture-layer">
              <h3 class="layer-title">数据层</h3>
              <p class="layer-desc">存储配方数据、原料数据、图结构数据等</p>
              <div class="layer-tech">
                <span class="tech-tag">关系型数据库</span>
                <span class="tech-tag">图数据库</span>
                <span class="tech-tag">缓存</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="about-card card">
        <div class="about-card-header">
          <h2 class="about-card-title">用户界面</h2>
        </div>
        <div class="about-card-body">
          <div class="ui-design">
            <div class="ui-section">
              <h3 class="section-title">设计理念</h3>
              <p class="section-desc">采用爵士酒吧风格，营造温馨、专业的氛围，使用深棕色背景和金色点缀，体现鸡尾酒文化的优雅与精致</p>
            </div>
            <div class="ui-section">
              <h3 class="section-title">色彩方案</h3>
              <div class="color-palette">
                <div class="color-item">
                  <div class="color-swatch" style="background: var(--color-bg-0);"></div>
                  <span class="color-name">深棕色背景</span>
                </div>
                <div class="color-item">
                  <div class="color-swatch" style="background: var(--color-gold-400);"></div>
                  <span class="color-name">金色强调</span>
                </div>
                <div class="color-item">
                  <div class="color-swatch" style="background: var(--color-text-primary);"></div>
                  <span class="color-name">主要文字</span>
                </div>
                <div class="color-item">
                  <div class="color-swatch" style="background: var(--color-text-secondary);"></div>
                  <span class="color-name">次要文字</span>
                </div>
              </div>
            </div>
            <div class="ui-section">
              <h3 class="section-title">交互设计</h3>
              <p class="section-desc">注重用户体验，提供直观的操作界面，包括拖拽交互、实时反馈、动画过渡等，使复杂的数据分析变得易于理解</p>
            </div>
            <div class="ui-section">
              <h3 class="section-title">响应式布局</h3>
              <p class="section-desc">适配不同屏幕尺寸，从桌面端到移动端都能提供良好的用户体验，确保系统在各种设备上都能正常运行</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'AboutView'
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
  display: grid;
  gap: var(--spacing-xl);
  grid-template-columns: 1fr;
}

.about-card {
  padding: var(--spacing-xl);
}

.about-card-header {
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-md);
}

.about-card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-xs);
  font-family: var(--font-serif);
}

/* 技术路线图 */
.roadmap {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.roadmap-item {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.roadmap-step {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-gold-400);
  color: var(--color-bg-0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.roadmap-content {
  flex: 1;
}

.roadmap-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.roadmap-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* SQE 方法说明 */
.sqe-method {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.sqe-component {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.component-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-sm);
}

.component-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-bottom: var(--spacing-sm);
}

.component-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.detail-item {
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
}

.sqe-formula {
  padding: var(--spacing-md);
  background: rgba(212, 175, 55, 0.1);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-gold-400);
}

.formula-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-sm);
}

.formula-content p {
  font-size: 0.9rem;
  color: var(--color-text-primary);
  line-height: 1.5;
  margin: 0 0 var(--spacing-sm) 0;
}

.formula-content p:last-child {
  margin-bottom: 0;
}

/* 图建模流程 */
.graph-modeling {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.modeling-step {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.step-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.step-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 数据来源 */
.data-sources {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
}

.source-item {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.source-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.source-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* 系统架构 */
.system-architecture {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.architecture-layer {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.layer-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-sm);
}

.layer-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-bottom: var(--spacing-sm);
}

.layer-tech {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.tech-tag {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-3);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  color: var(--color-gold-300);
}

/* 用户界面 */
.ui-design {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.ui-section {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.section-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.color-palette {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-top: var(--spacing-sm);
}

.color-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.color-swatch {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.color-name {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  text-align: center;
}

@media (max-width: 768px) {
  .about-header {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .about-content {
    padding: var(--spacing-md);
  }
  
  .about-card {
    padding: var(--spacing-lg);
  }
  
  .roadmap-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .roadmap-step {
    align-self: flex-start;
  }
  
  .data-sources {
    grid-template-columns: 1fr;
  }
  
  .color-palette {
    justify-content: center;
  }
}
</style>