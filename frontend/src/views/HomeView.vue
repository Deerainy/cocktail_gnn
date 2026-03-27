<template>
  <div class="home">
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-inner">
          <div class="hero-text">
            <p class="hero-kicker">GRAPH-BASED COCKTAIL FLAVOR COMBINATION GENERATION</p>
            <h1 class="hero-title">
              基于图结构优化的<br>
              <span class="hero-title-accent">鸡尾酒风味组合生成系统</span>
            </h1>
            <p class="hero-subtitle">"喝着葡萄酒，看看月亮 ，想想月亮见证过的所有文明。"<br>—— 奥马尔·海亚姆， 《鲁拜集》</p>
            <div class="hero-actions">
                      <router-link to="/recipe" class="btn btn-primary">
                        <svg class="btn-icon" viewBox="0 0 20 20" fill="none">
                          <path d="M10 3L10 17M3 10L17 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                        开始配方分析
                      </router-link>
                      <router-link to="/about" class="btn btn-secondary">
                        <svg class="btn-icon" viewBox="0 0 20 20" fill="none">
                          <path d="M5 4.5H15M5 10H15M5 15.5H12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                        了解系统原理
                      </router-link>
                    </div>
                  
          </div>
        </div>
      </div>
    </section>

    <section class="features">
      <div class="container">
                          <!-- 场景导航 -->
                  <div class="scenarios">
                    <h3 class="scenarios-title">使用场景</h3>
                    <div class="scenarios-grid">
                      <!-- 场景1 -->
                      <div class="scenario-item">
                        <div class="scenario-icon">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                            <path d="M2 17l10 5 10-5"/>
                            <path d="M2 12l10 5 10-5"/>
                          </svg>
                        </div>
                        <h4 class="scenario-title">想知道一杯酒为什么好喝？</h4>
                        <p class="scenario-desc">进入“配方分析”，查看该 recipe 的原料结构、关键风味节点与 SQE 评分。</p>
                        <router-link to="/recipe" class="scenario-link">去配方分析</router-link>
                      </div>
                      
                      <!-- 场景2 -->
                      <div class="scenario-item">
                        <div class="scenario-icon">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                            <polyline points="17 21 17 13 7 13 7 21"/>
                            <polyline points="7 3 7 8 15 8"/>
                          </svg>
                        </div>
                        <h4 class="scenario-title">缺少某个原料但想保留风味？</h4>
                        <p class="scenario-desc">先在“配方分析”选中目标 recipe，再进入“组合调整”，系统会推荐替代方案。</p>
                        <router-link to="/adjust" class="scenario-link">从配方进入替代</router-link>
                      </div>
                      
                      <!-- 场景3 -->
                      <div class="scenario-item">
                        <div class="scenario-icon">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="8" x2="12" y2="12"/>
                            <line x1="12" y1="16" x2="12.01" y2="16"/>
                          </svg>
                        </div>
                        <h4 class="scenario-title">只有这些材料，能做出什么？</h4>
                        <p class="scenario-desc">进入“创新生成”，输入现有材料与风味偏好，系统会给出候选组合。</p>
                        <router-link to="/generate" class="scenario-link">根据材料开始生成</router-link>
                      </div>
                    </div>
                  </div>
        <div class="features-grid">
          <div v-for="feature in features" :key="feature.id" class="feature-card card">
            <div class="feature-icon">
              <svg viewBox="0 0 32 32" fill="none">
                <path :d="feature.iconPath" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.description }}</p>
            <router-link :to="feature.path" class="feature-link">
              进入页面
              <svg viewBox="0 0 16 16" fill="none">
                <path d="M6 4L11 8L6 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <section class="showcase">
      <div class="container">
        <div class="showcase-split">
          <div class="showcase-left">
            <div class="section-header">
              <h2 class="section-title">风味组合生成体验</h2>
              <p class="section-desc">选择偏好，系统将为您智能生成独特鸡尾酒组合</p>
            </div>
            <div class="selector">
              <div class="selector-item">
                <span class="selector-label">选择基酒类型</span>
                <div class="selector-options">
                  <span class="selector-option active">金酒</span>
                  <span class="selector-option">威士忌</span>
                  <span class="selector-option">朗姆酒</span>
                </div>
              </div>
              <div class="selector-item">
                <span class="selector-label">选择风味偏好</span>
                <div class="selector-options">
                  <span class="selector-option active">柑橘</span>
                  <span class="selector-option">草本</span>
                  <span class="selector-option">花香</span>
                </div>
              </div>
              <div class="selector-item">
                <span class="selector-label">选择口感特征</span>
                <div class="selector-options">
                  <span class="selector-option">清爽</span>
                  <span class="selector-option active">浓郁</span>
                  <span class="selector-option">柔和</span>
                </div>
              </div>
              <button class="btn btn-primary" style="width: 100%;">
                <svg class="btn-icon" viewBox="0 0 20 20" fill="none">
                  <path d="M10 3V17M3 10H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                生成鸡尾酒组合
              </button>
            </div>
          </div>
          <div class="showcase-right">
            <div class="graph-preview card">
              <div class="graph-header">
                <div class="graph-title">
                  <svg viewBox="0 0 20 20" fill="none">
                    <circle cx="6" cy="6" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                    <circle cx="14" cy="6" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                    <circle cx="10" cy="14" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                    <path d="M7.8 7.2L10 11.5M12.2 7.2L10 11.5M8 6H12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                  可视化风味图谱
                </div>
              </div>
              <div class="graph-content">
                <div class="graph-nodes">
                  <span class="graph-node node-primary">苦精</span>
                  <span class="graph-node node-secondary">柑橘</span>
                  <span class="graph-node node-secondary">糖浆</span>
                  <span class="graph-node node-tertiary">甜</span>
                  <span class="graph-node node-primary">烟熏</span>
                  <span class="graph-node node-tertiary">柠檬</span>
                  <span class="graph-node node-secondary">薄荷</span>
                  <span class="graph-node node-primary">蜂蜜</span>
                  <span class="graph-node node-tertiary">香草</span>
                </div>
                <svg class="graph-lines" viewBox="0 0 400 300">
                  <line x1="100" y1="80" x2="200" y2="150" stroke="rgba(212,175,55,0.2)" stroke-width="1"/>
                  <line x1="300" y1="80" x2="200" y2="150" stroke="rgba(212,175,55,0.2)" stroke-width="1"/>
                  <line x1="50" y1="180" x2="200" y2="150" stroke="rgba(212,175,55,0.15)" stroke-width="1"/>
                  <line x1="350" y1="180" x2="200" y2="150" stroke="rgba(212,175,55,0.15)" stroke-width="1"/>
                  <line x1="100" y1="240" x2="200" y2="150" stroke="rgba(212,175,55,0.15)" stroke-width="1"/>
                  <line x1="300" y1="240" x2="200" y2="150" stroke="rgba(212,175,55,0.15)" stroke-width="1"/>
                  <line x1="200" y1="60" x2="200" y2="150" stroke="rgba(212,175,55,0.15)" stroke-width="1"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="stats">
      <div class="container">
        <div class="stats-grid">
          <div class="stats-left">
            <div class="section-header">
              <h2 class="section-title">系统特色</h2>
            </div>
            <div class="stat-list">
              <div class="stat-item">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div>
                  <h4 class="stat-label">图结构建模</h4>
                  <p class="stat-desc">将风味关系建模为图结构，精准刻画风味关联</p>
                </div>
              </div>
              <div class="stat-item">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M8 12L11 15L16 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div>
                  <h4 class="stat-label">智能优化算法</h4>
                  <p class="stat-desc">采用图优化算法寻找最佳风味组合路径</p>
                </div>
              </div>
              <div class="stat-item">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M15 12C15 13.6569 13.6569 15 12 15C10.3431 15 9 13.6569 9 12C9 10.3431 10.3431 9 12 9C13.6569 9 15 10.3431 15 12Z" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M12 3V5M12 19V21M3 12H5M19 12H21M19.0711 4.92893L17.6569 6.34315M6.34315 17.6569L4.92893 19.0711M4.92893 4.92893L6.34315 6.34315M17.6569 17.6569L19.0711 19.0711" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                <div>
                  <h4 class="stat-label">可视化探索</h4>
                  <p class="stat-desc">直观展示风味网络，支持交互式探索分析</p>
                </div>
              </div>
              <div class="stat-item">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M9.663 17H4.5L8.5 5H15.5L19.5 17H14.337" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M12 9V13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  <circle cx="12" cy="15" r="1" fill="currentColor"/>
                </svg>
                <div>
                  <h4 class="stat-label">创意配方生成</h4>
                  <p class="stat-desc">突破传统搭配逻辑，激发创新调酒灵感</p>
                </div>
              </div>
            </div>
          </div>
          <div class="stats-right">
            <div class="glass-showcase">
              <svg viewBox="0 0 200 260" fill="none">
                <path d="M50 240L60 60H140L150 240H50Z" fill="url(#glassGradient)" stroke="rgba(212,175,55,0.3)" stroke-width="1.5"/>
                <path d="M60 180C60 180 100 160 140 180V240H60V180Z" fill="url(#drinkGradient)"/>
                <defs>
                  <linearGradient id="glassGradient" x1="60" y1="60" x2="140" y2="240">
                    <stop offset="0%" stop-color="rgba(247,232,200,0.08)"/>
                    <stop offset="50%" stop-color="rgba(247,232,200,0.03)"/>
                    <stop offset="100%" stop-color="rgba(247,232,200,0.08)"/>
                  </linearGradient>
                  <linearGradient id="drinkGradient" x1="100" y1="160" x2="100" y2="240">
                    <stop offset="0%" stop-color="#d4af37"/>
                    <stop offset="100%" stop-color="#8f6809"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'HomeView',
  data() {
    return {
      features: [
        {
          id: 1,
          title: '系统介绍',
          description: '了解系统背景、功能模块与技术架构',
          path: '/introduction',
          iconPath: 'M4 16L8 8L12 12L16 4L20 16M4 20H20'
        },
        {
          id: 2,
          title: '图结构优化',
          description: '探索风味图谱构建与优化算法原理',
          path: '/graph',
          iconPath: 'M8 8C9.65685 8 11 6.65685 11 5C11 3.34315 9.65685 2 8 2C6.34315 2 5 3.34315 5 5C5 6.65685 6.34315 8 8 8ZM8 8V12M8 12L12 16M8 12L4 16M16 10C17.6569 10 19 8.65685 19 7C19 5.34315 17.6569 4 16 4C14.3431 4 13 5.34315 13 7C13 8.65685 14.3431 10 16 10ZM12 20C13.6569 20 15 18.6569 15 17C15 15.3431 13.6569 14 12 14C10.3431 14 9 15.3431 9 17C9 18.6569 10.3431 20 12 20Z'
        },
        {
          id: 3,
          title: '风味探索',
          description: '浏览基酒、辅料与风味特征数据库',
          path: '/explore',
          iconPath: 'M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8ZM2 12H6M18 12H22M12 2V6M12 18V22'
        },
        {
          id: 4,
          title: '组合生成',
          description: '基于图优化算法智能生成鸡尾酒配方',
          path: '/generator',
          iconPath: 'M19 3H5C3.89543 3 3 3.89543 3 5V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V5C21 3.89543 20.1046 3 19 3ZM9 9H15V15H9V9Z'
        }
      ]
    };
  }
};
</script>

<style scoped>
.home {
  width: 100%;
  background: var(--color-bg-0);
  min-height: 100vh;
}

.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
}

.hero-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('@/assets/jazz-bar-bg.jpg');
  background-size: cover;
  background-position: center;
  mix-blend-mode: overlay;
}

.hero-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(212, 175, 55, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 30%, rgba(184, 134, 11, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 40% 80%, rgba(212, 175, 55, 0.06) 0%, transparent 35%),
    radial-gradient(circle at 60% 20%, rgba(212, 175, 55, 0.07) 0%, transparent 45%),
    radial-gradient(circle at 90% 70%, rgba(184, 134, 11, 0.05) 0%, transparent 30%);
  animation: waveAnimation 20s ease-in-out infinite;
}

.hero-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('@/assets/jazz-bar-bg.jpg');
  background-size: cover;
  background-position: center;
  mix-blend-mode: overlay;
  animation: backgroundShift 30s ease-in-out infinite;
}

@keyframes waveAnimation {
  0% {
    transform: translateY(0) translateX(0);
  }
  25% {
    transform: translateY(-10px) translateX(5px);
  }
  50% {
    transform: translateY(0) translateX(10px);
  }
  75% {
    transform: translateY(10px) translateX(5px);
  }
  100% {
    transform: translateY(0) translateX(0);
  }
}

@keyframes backgroundShift {
  0% {
    transform: scale(1) rotate(0deg);
  }
  25% {
    transform: scale(1.02) rotate(0.5deg);
  }
  50% {
    transform: scale(1.01) rotate(0deg);
  }
  75% {
    transform: scale(1.03) rotate(-0.5deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
  }
}

.hero-content {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: var(--spacing-3xl) var(--spacing-xl);
  margin-top: 130px;
  margin-left: 180px;
}

.hero-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-3xl);
  align-items: center;
  padding-left: var(--spacing-2xl);
  padding-right: var(--spacing-xl);
}

.hero-kicker {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-gold-400);
  text-transform: uppercase;
  letter-spacing: 0.2em;
  margin-bottom: var(--spacing-md);
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(36px, 5vw, 56px);
  font-weight: 600;
  line-height: 1.1;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-md) 0;
  letter-spacing: -0.02em;
}

.hero-title-accent {
  background: linear-gradient(135deg, var(--color-gold-200) 0%, var(--color-gold-400) 50%, var(--color-gold-500) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-xl) 0;
  max-width: 540px;
}

.hero-actions {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-2xl);
}

/* 场景导航样式 */
.scenarios {
  margin-top: var(--spacing-3xl);
}

.scenarios-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-xl);
  letter-spacing: 0.02em;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}

.scenario-item {
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.8) 0%, rgba(26, 20, 16, 0.9) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  transition: all var(--transition-normal);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.scenario-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(212, 175, 55, 0.15);
  border-color: var(--color-gold-400);
}

.scenario-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-300));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--spacing-lg);
  color: var(--color-bg-0);
}

.scenario-icon svg {
  width: 24px;
  height: 24px;
}

.scenario-item h4 {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  line-height: 1.4;
}

.scenario-desc {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--spacing-lg);
}

.scenario-link {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gold-300);
  text-decoration: none;
  transition: all var(--transition-fast);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-gold-400);
  border-radius: var(--radius-md);
}

.scenario-link:hover {
  background: var(--color-gold-400);
  color: var(--color-bg-0);
  transform: translateX(4px);
}

.scenario-link::after {
  content: '→';
  font-size: 12px;
  transition: transform var(--transition-fast);
}

.scenario-link:hover::after {
  transform: translateX(2px);
}

.btn-icon {
  width: 18px;
  height: 18px;
}



.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl);
}

.features {
  padding: var(--spacing-3xl) 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-lg);
}

.feature-card {
  padding: var(--spacing-xl);
}

.feature-icon {
  width: 48px;
  height: 48px;
  padding: 10px;
  background: rgba(212, 175, 55, 0.08);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-lg);
}

.feature-icon svg {
  width: 100%;
  height: 100%;
}

.feature-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.feature-desc {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-lg) 0;
}

.feature-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gold-300);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.feature-link:hover {
  color: var(--color-gold-200);
  gap: 10px;
}

.feature-link svg {
  width: 16px;
  height: 16px;
}

.showcase {
  padding: var(--spacing-3xl) 0;
}

.showcase-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-2xl);
  align-items: start;
}

.section-header {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  letter-spacing: -0.01em;
}

.section-desc {
  font-family: var(--font-body);
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.6;
}

.selector {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.selector-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.selector-label {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.selector-options {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.selector-option {
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-secondary);
  background: rgba(212, 175, 55, 0.05);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.selector-option:hover {
  border-color: var(--color-border-strong);
  color: var(--color-gold-200);
}

.selector-option.active {
  background: rgba(212, 175, 55, 0.12);
  border-color: var(--color-gold-400);
  color: var(--color-gold-200);
}

.graph-preview {
  padding: var(--spacing-xl);
  height: 100%;
  min-height: 420px;
}

.graph-header {
  margin-bottom: var(--spacing-lg);
}

.graph-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.graph-title svg {
  width: 20px;
  height: 20px;
  color: var(--color-gold-300);
}

.graph-content {
  position: relative;
  height: 320px;
}

.graph-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.graph-nodes {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
}

.graph-node {
  position: absolute;
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-body);
  font-size: 13px;
  border-radius: var(--radius-md);
  transform: translate(-50%, -50%);
  white-space: nowrap;
}

.node-primary {
  background: rgba(212, 175, 55, 0.15);
  color: var(--color-gold-200);
  border: 1px solid var(--color-gold-400);
}

.node-secondary {
  background: rgba(255, 152, 0, 0.12);
  color: var(--color-gold-300);
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.node-tertiary {
  background: rgba(212, 175, 55, 0.08);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-subtle);
}

.graph-node:nth-child(1) { top: 25%; left: 50%; }
.graph-node:nth-child(2) { top: 45%; left: 25%; }
.graph-node:nth-child(3) { top: 45%; left: 75%; }
.graph-node:nth-child(4) { top: 70%; left: 35%; }
.graph-node:nth-child(5) { top: 70%; left: 65%; }
.graph-node:nth-child(6) { top: 15%; left: 30%; }
.graph-node:nth-child(7) { top: 15%; left: 70%; }
.graph-node:nth-child(8) { top: 85%; left: 50%; }
.graph-node:nth-child(9) { top: 45%; left: 50%; }

.stats {
  padding: var(--spacing-3xl) 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: var(--spacing-3xl);
  align-items: center;
}

.stat-list {
  display: grid;
  gap: var(--spacing-lg);
}

.stat-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
}

.stat-item:hover {
  background: rgba(212, 175, 55, 0.08);
  border-color: var(--color-border-strong);
}

.stat-item svg {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  color: var(--color-gold-300);
}

.stat-label {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px 0;
}

.stat-desc {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.glass-showcase {
  display: flex;
  justify-content: center;
  align-items: center;
}

.glass-showcase svg {
  width: 100%;
  max-width: 260px;
  filter: drop-shadow(0 30px 60px rgba(0, 0, 0, 0.5));
}
</style>
