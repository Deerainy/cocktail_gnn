<template>
  <div class="home">
    <section class="hero">
      <div class="hero-bg">
        <!-- 动态背景效果 -->
        <div class="hero-particles"></div>
        <div class="hero-gradient"></div>
      </div>
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
              <router-link to="/recipe" class="btn btn-primary hero-btn-primary">
                <svg class="btn-icon" viewBox="0 0 20 20" fill="none">
                  <path d="M10 3L10 17M3 10H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                开始配方分析
              </router-link>
              <router-link to="/about" class="btn btn-secondary hero-btn-secondary">
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
          <div v-for="(feature, index) in features" :key="feature.id" class="feature-card card" :style="{ animationDelay: `${index * 0.1}s` }">
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
                  <span class="selector-option active" @click="selectOption('base', 'gin')">金酒</span>
                  <span class="selector-option" @click="selectOption('base', 'whiskey')">威士忌</span>
                  <span class="selector-option" @click="selectOption('base', 'rum')">朗姆酒</span>
                </div>
              </div>
              <div class="selector-item">
                <span class="selector-label">选择风味偏好</span>
                <div class="selector-options">
                  <span class="selector-option active" @click="selectOption('flavor', 'citrus')">柑橘</span>
                  <span class="selector-option" @click="selectOption('flavor', 'herb')">草本</span>
                  <span class="selector-option" @click="selectOption('flavor', 'flower')">花香</span>
                </div>
              </div>
              <div class="selector-item">
                <span class="selector-label">选择口感特征</span>
                <div class="selector-options">
                  <span class="selector-option" @click="selectOption('texture', 'fresh')">清爽</span>
                  <span class="selector-option active" @click="selectOption('texture', 'rich')">浓郁</span>
                  <span class="selector-option" @click="selectOption('texture', 'soft')">柔和</span>
                </div>
              </div>
              <button class="btn btn-primary showcase-btn" style="width: 100%;" @click="generateCocktail">
                <svg class="btn-icon" viewBox="0 0 20 20" fill="none">
                  <path d="M10 3V17M3 10H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                生成鸡尾酒组合
              </button>
            </div>
            <div class="showcase-result" v-if="showResult">
              <div class="result-card">
                <h3 class="result-title">生成结果</h3>
                <div class="result-content">
                  <div class="result-item">
                    <span class="result-label">推荐配方：</span>
                    <span class="result-value">{{ generatedCocktail.name }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-label">主要原料：</span>
                    <span class="result-value">{{ generatedCocktail.ingredients }}</span>
                  </div>
                  <div class="result-item">
                    <span class="result-label">风味特征：</span>
                    <span class="result-value">{{ generatedCocktail.flavor }}</span>
                  </div>
                  <router-link to="/recipe" class="result-link">查看详细配方</router-link>
                </div>
              </div>
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
                  <span 
                    v-for="(node, index) in graphNodes" 
                    :key="index" 
                    class="graph-node" 
                    :class="`node-${node.type}`" 
                    :style="{ 
                      animationDelay: `${index * 0.1}s`,
                      top: node.top,
                      left: node.left
                    }"
                  >
                    {{ node.name }}
                  </span>
                </div>
                <svg class="graph-lines" viewBox="0 0 400 300">
                  <line v-for="(line, index) in graphLines" :key="index" :x1="line.x1" :y1="line.y1" :x2="line.x2" :y2="line.y2" stroke="rgba(212,175,55,0.3)" stroke-width="1.5" stroke-dasharray="4"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="stats">
      <div class="container">
        <div class="section-header text-center" style="margin-bottom: var(--spacing-2xl);">
          <h2 class="section-title">系统特色与数据</h2>
          <p class="section-desc">基于图结构的智能风味组合系统</p>
        </div>
        <div class="stats-grid">
          <div class="stats-left">
            <div class="stat-list">
              <div class="stat-item" v-for="(stat, index) in stats" :key="stat.id" :style="{ animationDelay: `${index * 0.2}s` }">
                <div class="stat-icon">
                  <svg :viewBox="stat.iconBox" fill="none">
                    <path :d="stat.iconPath" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path v-if="stat.iconPath2" :d="stat.iconPath2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <path v-if="stat.iconPath3" :d="stat.iconPath3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle v-if="stat.iconCircle" :cx="stat.iconCircle.cx" :cy="stat.iconCircle.cy" :r="stat.iconCircle.r" fill="currentColor"/>
                  </svg>
                  <div class="stat-number">{{ stat.value }}</div>
                </div>
                <div>
                  <h4 class="stat-label">{{ stat.title }}</h4>
                  <p class="stat-desc">{{ stat.description }}</p>
                </div>
              </div>
            </div>
          </div>
          <div class="stats-right">
            <div class="glass-showcase">
              <div class="glass-container">
                <svg viewBox="0 0 200 260" fill="none" class="glass-svg">
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
                <div class="glass-bubbles">
                  <div class="bubble" v-for="n in 10" :key="n" :style="{ animationDelay: `${n * 0.2}s` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 最近生成的配方模块 -->
    <section class="recent-recipes">
      <div class="container">
        <div class="section-header text-center" style="margin-bottom: var(--spacing-2xl);">
          <h2 class="section-title">最近生成的配方</h2>
          <p class="section-desc">探索系统智能生成的创意鸡尾酒配方</p>
        </div>
        <div class="recipes-grid">
          <div class="recipe-card" v-for="(recipe, index) in recentRecipes" :key="recipe.id" :style="{ animationDelay: `${index * 0.1}s` }">
            <div class="recipe-image">
              <div class="recipe-badge">{{ recipe.base }}</div>
              <div class="recipe-thumbnail" :style="{ backgroundImage: `url(${recipe.image})` }" loading="lazy"></div>
            </div>
            <div class="recipe-content">
              <h3 class="recipe-title">{{ recipe.name }}</h3>
              <p class="recipe-description">{{ recipe.description }}</p>
              <div class="recipe-ingredients">
                <span class="ingredient-tag" v-for="ingredient in recipe.ingredients" :key="ingredient">{{ ingredient }}</span>
              </div>
              <div class="recipe-actions">
                <router-link :to="`/recipe?id=${recipe.id}`" class="btn btn-secondary">查看详情</router-link>
                <button class="btn btn-outline" @click="generateSimilar(recipe.id)">生成类似配方</button>
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
      ],
      // 展示区相关数据
      selectedOptions: {
        base: 'gin',
        flavor: 'citrus',
        texture: 'rich'
      },
      showResult: false,
      generatedCocktail: {
        name: '金汤力鸡尾酒',
        ingredients: '金酒、汤力水、柠檬角',
        flavor: '清爽、柑橘味、微苦'
      },
      // 图谱节点数据
      graphNodes: [
        { name: '苦精', type: 'primary', top: '25%', left: '50%' },
        { name: '柑橘', type: 'secondary', top: '45%', left: '25%' },
        { name: '糖浆', type: 'secondary', top: '45%', left: '75%' },
        { name: '甜', type: 'tertiary', top: '70%', left: '35%' },
        { name: '烟熏', type: 'primary', top: '70%', left: '65%' },
        { name: '柠檬', type: 'tertiary', top: '15%', left: '30%' },
        { name: '薄荷', type: 'secondary', top: '15%', left: '70%' },
        { name: '蜂蜜', type: 'primary', top: '85%', left: '50%' },
        { name: '香草', type: 'tertiary', top: '45%', left: '50%' }
      ],
      // 图谱连线数据
      graphLines: [
        { x1: 100, y1: 80, x2: 200, y2: 150 },
        { x1: 300, y1: 80, x2: 200, y2: 150 },
        { x1: 50, y1: 180, x2: 200, y2: 150 },
        { x1: 350, y1: 180, x2: 200, y2: 150 },
        { x1: 100, y1: 240, x2: 200, y2: 150 },
        { x1: 300, y1: 240, x2: 200, y2: 150 },
        { x1: 200, y1: 60, x2: 200, y2: 150 }
      ],
      // 统计数据
      stats: [
        {
          id: 1,
          title: '图结构建模',
          description: '将风味关系建模为图结构，精准刻画风味关联',
          value: '200+',
          iconBox: '0 0 24 24',
          iconPath: 'M12 2L2 7L12 12L22 7L12 2Z',
          iconPath2: 'M2 17L12 22L22 17',
          iconPath3: 'M2 12L12 17L22 12'
        },
        {
          id: 2,
          title: '智能优化算法',
          description: '采用图优化算法寻找最佳风味组合路径',
          value: '95%',
          iconBox: '0 0 24 24',
          iconPath: 'M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z',
          iconPath2: 'M8 12L11 15L16 9'
        },
        {
          id: 3,
          title: '可视化探索',
          description: '直观展示风味网络，支持交互式探索分析',
          value: '150+',
          iconBox: '0 0 24 24',
          iconPath: 'M15 12C15 13.6569 13.6569 15 12 15C10.3431 15 9 13.6569 9 12C9 10.3431 10.3431 9 12 9C13.6569 9 15 10.3431 15 12Z',
          iconPath2: 'M12 3V5M12 19V21M3 12H5M19 12H21M19.0711 4.92893L17.6569 6.34315M6.34315 17.6569L4.92893 19.0711M4.92893 4.92893L6.34315 6.34315M17.6569 17.6569L19.0711 19.0711'
        },
        {
          id: 4,
          title: '创意配方生成',
          description: '突破传统搭配逻辑，激发创新调酒灵感',
          value: '500+',
          iconBox: '0 0 24 24',
          iconPath: 'M9.663 17H4.5L8.5 5H15.5L19.5 17H14.337',
          iconPath2: 'M12 9V13',
          iconCircle: { cx: 12, cy: 15, r: 1 }
        }
      ],
      // 最近生成的配方数据
      recentRecipes: [
        {
          id: 1,
          name: '金汤力鸡尾酒',
          description: '经典的金酒与汤力水组合，清爽宜人，适合夏季饮用',
          base: '金酒',
          ingredients: ['金酒', '汤力水', '柠檬角', '冰块'],
          image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=gin%20and%20tonic%20cocktail%20in%20a%20tall%20glass%20with%20lemon%20wedge&image_size=square_hd'
        },
        {
          id: 2,
          name: '老式鸡尾酒',
          description: '经典的威士忌鸡尾酒，口感浓郁，适合慢慢品味',
          base: '威士忌',
          ingredients: ['威士忌', '糖', '苦精', '橙皮'],
          image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=old%20fashioned%20cocktail%20in%20a%20rocks%20glass%20with%20orange%20twist&image_size=square_hd'
        },
        {
          id: 3,
          name: '莫吉托',
          description: '清爽的朗姆酒鸡尾酒，带有薄荷和青柠的清新风味',
          base: '朗姆酒',
          ingredients: ['朗姆酒', '薄荷叶', '糖', '青柠汁', '苏打水'],
          image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=mojito%20cocktail%20in%20a%20tall%20glass%20with%20mint%20leaves&image_size=square_hd'
        },
        {
          id: 4,
          name: '马天尼',
          description: '优雅的琴酒鸡尾酒，口感干冽，适合正式场合',
          base: '金酒',
          ingredients: ['金酒', '干苦艾酒', '橄榄'],
          image: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=martini%20cocktail%20in%20a%20coupe%20glass%20with%20olive&image_size=square_hd'
        }
      ]
    };
  },
  mounted() {
    // 预加载图片
    this.preloadImages();
    // 初始化滚动动画
    this.initScrollAnimations();
  },
  methods: {
    // 初始化滚动动画
    initScrollAnimations() {
      const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
      };

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            observer.unobserve(entry.target);
          }
        });
      }, observerOptions);

      // 观察需要动画的元素
      document.querySelectorAll('.section-header, .feature-card, .stat-item, .recipe-card').forEach(el => {
        observer.observe(el);
      });
    },
    // 预加载图片
    preloadImages() {
      // 预加载配方图片
      this.recentRecipes.forEach(recipe => {
        const img = new Image();
        img.src = recipe.image;
      });
    },
    // 选择选项
    selectOption(category, value) {
      this.selectedOptions[category] = value;
      // 这里可以添加根据选择更新图谱的逻辑
    },
    // 生成鸡尾酒
    generateCocktail() {
      // 模拟生成过程
      this.showResult = false;
      // 模拟延迟，显示生成过程
      setTimeout(() => {
        // 根据选择生成不同的鸡尾酒
        const cocktails = {
          'gin-citrus-rich': {
            name: '金汤力鸡尾酒',
            ingredients: '金酒、汤力水、柠檬角',
            flavor: '清爽、柑橘味、微苦'
          },
          'whiskey-herb-rich': {
            name: '老式鸡尾酒',
            ingredients: '威士忌、糖、苦精',
            flavor: '浓郁、草本味、烟熏'
          },
          'rum-flower-soft': {
            name: '莫吉托',
            ingredients: '朗姆酒、薄荷叶、糖、青柠汁',
            flavor: '柔和、花香、清爽'
          }
        };
        
        const key = `${this.selectedOptions.base}-${this.selectedOptions.flavor}-${this.selectedOptions.texture}`;
        this.generatedCocktail = cocktails[key] || cocktails['gin-citrus-rich'];
        this.showResult = true;
      }, 1000);
    },
    // 生成类似配方
    generateSimilar(recipeId) {
      // 这里可以添加生成类似配方的逻辑
      console.log('生成类似配方:', recipeId);
      // 跳转到生成页面
      this.$router.push('/generator');
    }
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

}

/* 动态粒子效果 */
.hero-particles {
  position: absolute;
  inset: 0;
  z-index: 1;
  overflow: hidden;
}

.hero-particles::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle, rgba(212, 175, 55, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: particleFloat 20s linear infinite;
}

/* 渐变叠加层 */
.hero-gradient {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.6) 50%, rgba(0, 0, 0, 0.8) 100%);
}

/* 按钮动画效果 */
.hero-btn-primary {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.hero-btn-primary::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.hero-btn-primary:hover::before {
  left: 100%;
}

.hero-btn-secondary {
  position: relative;
  transition: all 0.3s ease;
}

.hero-btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(212, 175, 55, 0.3);
}

/* 标题动画效果 */
.hero-title {
  position: relative;
  animation: fadeInUp 1s ease-out;
}

.hero-subtitle {
  animation: fadeInUp 1s ease-out 0.3s both;
}

.hero-actions {
  animation: fadeInUp 1s ease-out 0.6s both;
}

/* 动画关键帧 */
@keyframes particleFloat {
  0% {
    transform: translateY(0) rotate(0deg);
  }
  100% {
    transform: translateY(-50px) rotate(360deg);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
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
  background: linear-gradient(135deg, rgba(26, 20, 16, 1) 0%, rgba(34, 24, 18, 1) 100%);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-xl);
  margin-top: var(--spacing-2xl);
}

.feature-card {
  padding: var(--spacing-2xl);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  animation: featureCardFadeIn 0.8s ease-out both;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.1), transparent);
  transition: left 0.5s ease;
}

.feature-card:hover::before {
  left: 100%;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 32px rgba(212, 175, 55, 0.2);
  border-color: var(--color-gold-400);
}

.feature-icon {
  width: 64px;
  height: 64px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(212, 175, 55, 0.05));
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-xl);
  transition: all 0.3s ease;
}

.feature-card:hover .feature-icon {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.1));
  border-color: var(--color-gold-400);
  transform: scale(1.05);
}

.feature-icon svg {
  width: 100%;
  height: 100%;
}

.feature-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-md) 0;
  transition: color 0.3s ease;
}

.feature-card:hover .feature-title {
  color: var(--color-gold-200);
}

.feature-desc {
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-xl) 0;
  transition: color 0.3s ease;
}

.feature-card:hover .feature-desc {
  color: var(--color-text-primary);
}

.feature-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gold-300);
  text-decoration: none;
  transition: all 0.3s ease;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-gold-400);
  border-radius: var(--radius-md);
}

.feature-link:hover {
  color: var(--color-bg-0);
  background: var(--color-gold-400);
  gap: 12px;
  transform: translateX(4px);
}

.feature-link svg {
  width: 16px;
  height: 16px;
  transition: transform 0.3s ease;
}

.feature-link:hover svg {
  transform: translateX(2px);
}

/* 特性卡片动画 */
@keyframes featureCardFadeIn {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.showcase {
  padding: var(--spacing-3xl) 0;
  background: linear-gradient(135deg, rgba(34, 24, 18, 1) 0%, rgba(26, 20, 16, 1) 100%);
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
  font-size: 32px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  letter-spacing: -0.01em;
  animation: fadeInUp 0.8s ease-out;
}

.section-desc {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.6;
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

.selector {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  animation: fadeInUp 0.8s ease-out 0.4s both;
}

.selector-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.selector-label {
  font-family: var(--font-body);
  font-size: 14px;
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
  font-size: 14px;
  color: var(--color-text-secondary);
  background: rgba(212, 175, 55, 0.05);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.selector-option::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.2), transparent);
  transition: left 0.5s ease;
}

.selector-option:hover::before {
  left: 100%;
}

.selector-option:hover {
  border-color: var(--color-gold-400);
  color: var(--color-gold-200);
  transform: translateY(-2px);
}

.selector-option.active {
  background: rgba(212, 175, 55, 0.12);
  border-color: var(--color-gold-400);
  color: var(--color-gold-200);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
}

/* 生成按钮样式 */
.showcase-btn {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.showcase-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.showcase-btn:hover::before {
  left: 100%;
}

.showcase-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(212, 175, 55, 0.4);
}

/* 生成结果样式 */
.showcase-result {
  margin-top: var(--spacing-xl);
  animation: fadeInUp 0.8s ease-out;
}

.result-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  transition: all 0.3s ease;
}

.result-card:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2);
}

.result-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-gold-200);
  margin: 0 0 var(--spacing-lg) 0;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.result-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.result-label {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.result-value {
  font-family: var(--font-body);
  font-size: 15px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.result-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-gold-300);
  text-decoration: none;
  transition: all 0.3s ease;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-gold-400);
  border-radius: var(--radius-md);
  align-self: flex-start;
  margin-top: var(--spacing-sm);
}

.result-link:hover {
  color: var(--color-bg-0);
  background: var(--color-gold-400);
  transform: translateX(4px);
}

/* 图谱预览样式 */
.graph-preview {
  padding: var(--spacing-2xl);
  height: 100%;
  min-height: 480px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  transition: all 0.3s ease;
  animation: fadeInUp 0.8s ease-out 0.6s both;
}

.graph-preview:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2);
}

.graph-header {
  margin-bottom: var(--spacing-lg);
}

.graph-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.graph-title svg {
  width: 24px;
  height: 24px;
  color: var(--color-gold-300);
}

.graph-content {
  position: relative;
  height: 360px;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, rgba(212, 175, 55, 0.02) 100%);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.graph-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 25% 25%, rgba(212, 175, 55, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(212, 175, 55, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
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
  transition: all 0.3s ease;
  animation: nodeFadeIn 0.8s ease-out both;
}

.graph-node:hover {
  transform: translate(-50%, -50%) scale(1.1);
  z-index: 10;
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

/* 节点动画 */
@keyframes nodeFadeIn {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.5);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

.stats {
  padding: var(--spacing-3xl) 0;
  background: linear-gradient(135deg, rgba(26, 20, 16, 1) 0%, rgba(34, 24, 18, 1) 100%);
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
  padding: var(--spacing-xl);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  transition: all 0.3s ease;
  animation: fadeInUp 0.8s ease-out both;
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.1), transparent);
  transition: left 0.5s ease;
}

.stat-item:hover::before {
  left: 100%;
}

.stat-item:hover {
  background: rgba(212, 175, 55, 0.08);
  border-color: var(--color-gold-400);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2);
}

.stat-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid var(--color-gold-400);
  border-radius: 50%;
  transition: all 0.3s ease;
}

.stat-item:hover .stat-icon {
  background: rgba(212, 175, 55, 0.2);
  transform: scale(1.1);
}

.stat-icon svg {
  width: 32px;
  height: 32px;
  color: var(--color-gold-300);
  transition: all 0.3s ease;
}

.stat-item:hover .stat-icon svg {
  color: var(--color-gold-200);
  transform: scale(1.2);
}

.stat-number {
  position: absolute;
  bottom: -8px;
  right: -8px;
  padding: 4px 8px;
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-bg-0);
  background: var(--color-gold-400);
  border-radius: var(--radius-md);
  animation: countUp 2s ease-out;
}

.stat-label {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
  transition: all 0.3s ease;
}

.stat-item:hover .stat-label {
  color: var(--color-gold-200);
}

.stat-desc {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
  transition: all 0.3s ease;
}

.stat-item:hover .stat-desc {
  color: var(--color-text-primary);
}

.glass-showcase {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 400px;
}

.glass-container {
  position: relative;
  width: 100%;
  max-width: 280px;
  animation: fadeInUp 0.8s ease-out 0.6s both;
}

.glass-svg {
  width: 100%;
  height: auto;
  filter: drop-shadow(0 30px 60px rgba(0, 0, 0, 0.5));
  animation: float 3s ease-in-out infinite;
}

.glass-bubbles {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 100px;
  pointer-events: none;
}

.bubble {
  position: absolute;
  width: 8px;
  height: 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: bubbleRise 3s ease-in-out infinite;
}

.bubble:nth-child(1) {
  top: 80%;
  left: 20%;
}

.bubble:nth-child(2) {
  top: 60%;
  left: 60%;
}

.bubble:nth-child(3) {
  top: 40%;
  left: 30%;
}

.bubble:nth-child(4) {
  top: 20%;
  left: 70%;
}

.bubble:nth-child(5) {
  top: 70%;
  left: 50%;
}

.bubble:nth-child(6) {
  top: 50%;
  left: 10%;
}

.bubble:nth-child(7) {
  top: 30%;
  left: 40%;
}

.bubble:nth-child(8) {
  top: 10%;
  left: 60%;
}

.bubble:nth-child(9) {
  top: 60%;
  left: 80%;
}

.bubble:nth-child(10) {
  top: 40%;
  left: 20%;
}

/* 动画效果 */
@keyframes countUp {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes bubbleRise {
  0% {
    opacity: 0;
    transform: translateY(0) scale(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-40px) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateY(-80px) scale(0.5);
  }
}

/* 最近生成的配方模块 */
.recent-recipes {
  padding: var(--spacing-3xl) 0;
  background: linear-gradient(135deg, rgba(34, 24, 18, 1) 0%, rgba(26, 20, 16, 1) 100%);
}

.recipes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-xl);
}

.recipe-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  overflow: hidden;
  transition: all 0.3s ease;
  animation: fadeInUp 0.8s ease-out both;
  position: relative;
}

.recipe-card:hover {
  border-color: var(--color-gold-400);
  transform: translateY(-8px);
  box-shadow: 0 12px 32px rgba(212, 175, 55, 0.3);
}

.recipe-image {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.recipe-thumbnail {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  transition: all 0.5s ease;
  opacity: 0;
  animation: fadeIn 0.8s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(1.1);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.recipe-card:hover .recipe-thumbnail {
  transform: scale(1.1);
}

.recipe-badge {
  position: absolute;
  top: var(--spacing-md);
  left: var(--spacing-md);
  padding: var(--spacing-xs) var(--spacing-sm);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-bg-0);
  background: var(--color-gold-400);
  border-radius: var(--radius-md);
  z-index: 1;
}

.recipe-content {
  padding: var(--spacing-xl);
}

.recipe-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  transition: all 0.3s ease;
}

.recipe-card:hover .recipe-title {
  color: var(--color-gold-200);
}

.recipe-description {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-lg) 0;
  line-height: 1.6;
  transition: all 0.3s ease;
}

.recipe-card:hover .recipe-description {
  color: var(--color-text-primary);
}

.recipe-ingredients {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-lg);
}

.ingredient-tag {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-gold-300);
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid var(--color-gold-400);
  border-radius: var(--radius-md);
  transition: all 0.3s ease;
}

.recipe-card:hover .ingredient-tag {
  background: rgba(212, 175, 55, 0.2);
  color: var(--color-gold-200);
}

.recipe-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.recipe-actions .btn {
  flex: 1;
  font-size: 13px;
  padding: var(--spacing-sm) var(--spacing-md);
  transition: all 0.3s ease;
}

.recipe-actions .btn-secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
}

.recipe-actions .btn-outline {
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  background: transparent;
}

.recipe-actions .btn-outline:hover {
  border-color: var(--color-gold-400);
  color: var(--color-gold-300);
  background: rgba(212, 175, 55, 0.1);
  transform: translateY(-2px);
}

/* 微动画和过渡效果 */
/* 滚动动画 */
.section-header, .feature-card, .stat-item, .recipe-card {
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.8s ease-out;
}

.section-header.animate-in, .feature-card.animate-in, .stat-item.animate-in, .recipe-card.animate-in {
  opacity: 1;
  transform: translateY(0);
}

/* 按钮点击效果 */
.btn {
  position: relative;
  overflow: hidden;
}

.btn:active {
  transform: scale(0.98);
  transition: transform 0.1s ease;
}

/* 卡片悬停效果增强 */
.feature-card {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 16px 32px rgba(212, 175, 55, 0.3);
}

/* 文本悬停效果 */
.section-title, .feature-title, .stat-label, .recipe-title {
  transition: all 0.3s ease;
}

.section-title:hover, .feature-title:hover, .stat-label:hover, .recipe-title:hover {
  color: var(--color-gold-200);
  text-shadow: 0 0 20px rgba(212, 175, 55, 0.3);
}

/* 图标悬停效果 */
.feature-icon, .stat-icon {
  transition: all 0.4s ease;
}

.feature-card:hover .feature-icon, .stat-item:hover .stat-icon {
  transform: scale(1.2) rotate(5deg);
}

/* 选择器选项动画 */
.selector-option {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.selector-option:hover {
  transform: translateY(-3px) scale(1.05);
}

.selector-option.active {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
}

/* 图谱节点动画 */
.graph-node {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.graph-node:hover {
  transform: translate(-50%, -50%) scale(1.2);
  box-shadow: 0 8px 20px rgba(212, 175, 55, 0.4);
  z-index: 10;
}

/* 数字增长动画 */
.stat-number {
  animation: countUp 2s ease-out;
}

@keyframes countUp {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 背景渐变动画 */
.hero-gradient {
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.6) 50%, rgba(0, 0, 0, 0.8) 100%);
  animation: gradientShift 15s ease-in-out infinite;
}

@keyframes gradientShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .container {
    padding: 0 var(--spacing-lg);
  }
  
  .showcase-split {
    grid-template-columns: 1fr;
    gap: var(--spacing-xl);
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-xl);
  }
  
  .glass-showcase {
    min-height: 300px;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 0 var(--spacing-md);
  }
  
  .hero-content {
    text-align: center;
    padding: var(--spacing-2xl) var(--spacing-md);
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .hero-subtitle {
    font-size: 16px;
  }
  
  .hero-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .hero-buttons .btn {
    width: 100%;
    max-width: 280px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-lg);
  }
  
  .feature-card {
    padding: var(--spacing-lg);
  }
  
  .showcase {
    padding: var(--spacing-2xl) 0;
  }
  
  .section-title {
    font-size: 24px;
  }
  
  .section-desc {
    font-size: 14px;
  }
  
  .selector-options {
    justify-content: center;
  }
  
  .graph-preview {
    min-height: 380px;
  }
  
  .stats {
    padding: var(--spacing-2xl) 0;
  }
  
  .stat-item {
    padding: var(--spacing-lg);
  }
  
  .stat-icon {
    width: 56px;
    height: 56px;
  }
  
  .stat-icon svg {
    width: 28px;
    height: 28px;
  }
  
  .recent-recipes {
    padding: var(--spacing-2xl) 0;
  }
  
  .recipes-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-lg);
  }
  
  .recipe-card {
    max-width: 100%;
  }
  
  .recipe-actions {
    flex-direction: column;
  }
  
  .recipe-actions .btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 28px;
  }
  
  .hero-subtitle {
    font-size: 14px;
  }
  
  .section-title {
    font-size: 20px;
  }
  
  .section-desc {
    font-size: 13px;
  }
  
  .selector-option {
    font-size: 13px;
    padding: var(--spacing-xs) var(--spacing-sm);
  }
  
  .graph-preview {
    min-height: 320px;
    padding: var(--spacing-lg);
  }
  
  .graph-content {
    height: 260px;
  }
  
  .stat-item {
    flex-direction: column;
    text-align: center;
    gap: var(--spacing-md);
  }
  
  .recipe-content {
    padding: var(--spacing-lg);
  }
  
  .recipe-title {
    font-size: 18px;
  }
  
  .recipe-description {
    font-size: 13px;
  }
}
</style>
