<template>
  <div class="page">
    <div class="page-header">
      <div class="container">
        <div class="page-header-content">
          <h1 class="page-title">系统介绍</h1>
          <p class="page-subtitle">了解系统背景、核心功能与技术架构</p>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="content-grid">
        <div class="main-content">
          <div class="card">
            <h2 class="section-title">项目背景</h2>
            <p class="text">
              鸡尾酒是一种融合科学与艺术的饮品，其风味组合的设计需要丰富的专业知识和创造力。
              本系统旨在通过图结构优化技术，帮助调酒师和爱好者探索更多可能性。
            </p>
            <p class="text">
              传统的鸡尾酒配方设计往往依赖经验传承和有限的尝试，
              而本系统通过数据驱动的方法，能够系统性地探索风味空间，发现创新组合。
            </p>
          </div>
          <div class="card">
            <h2 class="section-title">核心功能</h2>
            <div class="feature-list">
              <div class="feature-item">
                <div class="feature-icon-small">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="feature-text">
                  <h3 class="feature-title">风味数据库</h3>
                  <p class="feature-desc">收录丰富的基酒、辅料和风味特征数据</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon-small">
                  <svg viewBox="0 0 24 24" fill="none">
                    <circle cx="8" cy="8" r="3" stroke="currentColor" stroke-width="1.5"/>
                    <circle cx="16" cy="16" r="3" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M10.5 9.5L13.5 14.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="feature-text">
                  <h3 class="feature-title">图结构建模</h3>
                  <p class="feature-desc">将原料和风味关系建模为图结构</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon-small">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div class="feature-text">
                  <h3 class="feature-title">智能优化算法</h3>
                  <p class="feature-desc">基于图优化生成最优风味组合</p>
                </div>
              </div>
              <div class="feature-item">
                <div class="feature-icon-small">
                  <svg viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="3" width="7" height="7" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="14" y="3" width="7" height="7" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="3" y="14" width="7" height="7" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="14" y="14" width="7" height="7" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                </div>
                <div class="feature-text">
                  <h3 class="feature-title">可视化探索</h3>
                  <p class="feature-desc">直观展示风味网络和组合结果</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="sidebar">
          <div class="card">
            <h3 class="sidebar-title">技术架构</h3>
            <div class="tech-stack">
              <div class="tech-item">
                <span class="tech-label">前端</span>
                <span class="tech-value">Vue 3</span>
              </div>
              <div class="tech-item">
                <span class="tech-label">后端</span>
                <span class="tech-value">Spring Boot</span>
              </div>
              <div class="tech-item">
                <span class="tech-label">图算法</span>
                <span class="tech-value">NetworkX / JGraphT</span>
              </div>
              <div class="tech-item">
                <span class="tech-label">可视化</span>
                <span class="tech-value">D3.js / ECharts</span>
              </div>
            </div>
          </div>
          <div class="card">
            <h3 class="sidebar-title">快速导航</h3>
            <div class="quick-links">
              <router-link to="/graph" class="quick-link">图结构优化</router-link>
              <router-link to="/explore" class="quick-link">风味探索</router-link>
              <router-link to="/generator" class="quick-link">组合生成</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'IntroductionView'
};
</script>

<style scoped>
.page {
  width: 100%;
  padding-bottom: var(--spacing-3xl);
}

.page-header {
  padding: var(--spacing-3xl) 0 var(--spacing-2xl) 0;
  border-bottom: 1px solid var(--color-border-subtle);
}

.page-header-content {
  text-align: center;
}

.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl);
}

.content-grid {
  display: grid;
  grid-template-columns: 1.8fr 1fr;
  gap: var(--spacing-xl);
  margin-top: var(--spacing-2xl);
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.card {
  padding: var(--spacing-xl);
}

.section-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-lg) 0;
}

.text {
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-md) 0;
}

.text:last-child {
  margin-bottom: 0;
}

.feature-list {
  display: grid;
  gap: var(--spacing-lg);
}

.feature-item {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
  padding: var(--spacing-lg);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
}

.feature-item:hover {
  background: rgba(212, 175, 55, 0.08);
  border-color: var(--color-border-strong);
}

.feature-icon-small {
  width: 40px;
  height: 40px;
  padding: 8px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: var(--radius-md);
  color: var(--color-gold-300);
  flex-shrink: 0;
}

.feature-icon-small svg {
  width: 100%;
  height: 100%;
}

.feature-text {
  flex: 1;
}

.feature-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px 0;
}

.feature-desc {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.sidebar-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-lg) 0;
}

.tech-stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.tech-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-subtle);
}

.tech-item:last-child {
  border-bottom: none;
}

.tech-label {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.tech-value {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--color-gold-300);
}

.quick-links {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.quick-link {
  padding: var(--spacing-md);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-fast);
}

.quick-link:hover {
  color: var(--color-gold-200);
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.08);
}
</style>
