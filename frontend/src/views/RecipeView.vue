<template>
  <div class="recipe">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-bg">
        <div class="header-particles"></div>
        <div class="header-gradient"></div>
      </div>
      <div class="container">
        <div class="page-header-content">
          <h1 class="page-title">配方列表</h1>
          <p class="page-subtitle">探索所有可用的配方</p>
          <div class="header-stats">
            <div class="stat-item">
              <span class="stat-number">{{ recipes.length }}</span>
              <span class="stat-label">总配方数</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ filteredRecipes.length }}</span>
              <span class="stat-label">当前显示</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 搜索和筛选区域 -->
    <div class="search-filter-section">
      <div class="container">
        <div class="search-filter-content">
          <div class="search-box">
            <svg viewBox="0 0 20 20" fill="none" class="search-icon">
              <path d="M9 17C13.4183 17 17 13.4183 17 9C17 4.58172 13.4183 1 9 1C4.58172 1 1 4.58172 1 9C1 13.4183 4.58172 17 9 17Z" stroke="currentColor" stroke-width="1.5"/>
              <path d="M14 14L19 19" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索配方名称..." 
              class="search-input"
            >
          </div>
          <div class="filter-groups">
            <div class="filter-group">
              <label class="filter-label">配方类型</label>
              <div class="filter-options">
                <button 
                  class="filter-btn" 
                  :class="{ active: filterType === null }"
                  @click="filterType = null"
                >
                  全部
                </button>
                <div class="filter-btn-with-tooltip">
                  <button 
                    class="filter-btn" 
                    :class="{ active: filterType === 'Daiquiri' }"
                    @click="filterType = 'Daiquiri'"
                  >
                    代基里型
                  </button>
                  <div class="tooltip">
                    <h4>代基里型</h4>
                    <p>以基酒、酸味成分和甜味成分为核心，整体结构清晰，强调酸甜平衡与清爽口感。</p>
                  </div>
                </div>
                <div class="filter-btn-with-tooltip">
                  <button 
                    class="filter-btn" 
                    :class="{ active: filterType === 'Margarita' }"
                    @click="filterType = 'Margarita'"
                  >
                    玛格丽特型
                  </button>
                  <div class="tooltip">
                    <h4>玛格丽特型</h4>
                    <p>通常以龙舌兰类基酒、酸味成分和橙味利口酒为主要结构，具有较明显的酸甜层次和果香特征。</p>
                  </div>
                </div>
                <div class="filter-btn-with-tooltip">
                  <button 
                    class="filter-btn" 
                    :class="{ active: filterType === 'Old Fashioned' }"
                    @click="filterType = 'Old Fashioned'"
                  >
                    古典鸡尾酒型
                  </button>
                  <div class="tooltip">
                    <h4>古典鸡尾酒型</h4>
                    <p>以烈酒基底为主体，通常辅以少量甜味成分和苦味成分，整体风格浓郁、厚重，突出基酒本身的风味。</p>
                  </div>
                </div>
                <div class="filter-btn-with-tooltip">
                  <button 
                    class="filter-btn" 
                    :class="{ active: filterType === 'Sour' }"
                    @click="filterType = 'Sour'"
                  >
                    酸酒型
                  </button>
                  <div class="tooltip">
                    <h4>酸酒型</h4>
                    <p>强调酸味与甜味之间的平衡关系，常呈现明亮、清爽的口感结构，是许多经典鸡尾酒的重要基础类型。</p>
                  </div>
                </div>
                <div class="filter-btn-with-tooltip">
                  <button 
                    class="filter-btn" 
                    :class="{ active: filterType === 'Martini' }"
                    @click="filterType = 'Martini'"
                  >
                    马天尼型
                  </button>
                  <div class="tooltip">
                    <h4>马天尼型</h4>
                    <p>以烈酒和苦艾酒等成分构成，甜味较弱，整体风格偏干爽、直接，突出酒体强度与香气层次。</p>
                  </div>
                </div>
              </div>
            </div>
            <div class="filter-group">
              <label class="filter-label">酒精类型</label>
              <div class="filter-options">
                <button 
                  class="filter-btn" 
                  :class="{ active: alcoholFilter === null }"
                  @click="alcoholFilter = null"
                >
                  全部
                </button>
                <button 
                  class="filter-btn" 
                  :class="{ active: alcoholFilter === 'alcoholic' }"
                  @click="alcoholFilter = 'alcoholic'"
                >
                  含酒精
                </button>
                <button 
                  class="filter-btn" 
                  :class="{ active: alcoholFilter === 'non-alcoholic' }"
                  @click="alcoholFilter = 'non-alcoholic'"
                >
                  不含酒精
                </button>
              </div>
            </div>
            <div class="filter-group">
              <label class="filter-label">排序方式</label>
              <div class="filter-options">
                <button 
                  class="filter-btn" 
                  :class="{ active: sortBy === 'name' }"
                  @click="sortBy = 'name'"
                >
                  名称
                </button>
                <button 
                  class="filter-btn" 
                  :class="{ active: sortBy === 'recent' }"
                  @click="sortBy = 'recent'"
                >
                  最新
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载配方列表中...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">加载失败</h2>
      <p class="error-message">{{ error }}</p>
      <button class="btn btn-primary" @click="fetchRecipes">重新加载</button>
    </div>
    
    <!-- 配方卡片列表 -->
    <div v-else class="container">
      <div class="recipe-header">
        <div class="recipe-header-content">
          <h2 class="recipe-header-title">
            {{ filteredRecipes.length }} 个配方
            <span v-if="searchQuery || filterType || alcoholFilter" class="recipe-header-subtitle">
              (已筛选)
            </span>
          </h2>
        </div>
      </div>
      
      <div class="recipe-grid">
        <div 
          v-for="(recipe, index) in filteredRecipes" 
          :key="recipe.recipe_id"
          class="recipe-card"
          @click="navigateToDetails(recipe.recipe_id)"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="recipe-card-image">
            <img 
              :src="getRecipeImage(recipe.recipe_id)" 
              :alt="recipe.recipe_name_zh || recipe.name" 
              class="recipe-image"
              loading="lazy"
              @error="$event.target.src = require('@/assets/loss.png')"
            >
            <div class="recipe-card-badges">
              <span 
                class="badge" 
                :class="recipe.is_alcoholic ? 'badge-alcoholic' : 'badge-non-alcoholic'"
              >
                {{ recipe.is_alcoholic ? '含酒精' : '不含酒精' }}
              </span>
              <span class="badge badge-family">
                {{ getFamilyTranslation(recipe.family) }}
              </span>
            </div>
          </div>
          <div class="recipe-card-content">
            <h3 class="recipe-card-name">
              <span v-if="recipe.recipe_name_zh" class="name-zh">{{ recipe.recipe_name_zh }}</span>
              <span v-if="recipe.recipe_name_zh && recipe.name" class="name-separator"> / </span>
              <span v-if="recipe.name" class="name-en">{{ recipe.name }}</span>
            </h3>
            
            <!-- 标签显示 - 轮播形式 -->
            <div v-if="recipe.tags && recipe.tags.length > 0" class="recipe-card-tags">
              <div class="tags-carousel">
                <div class="tags-track" :style="{ transform: `translateX(-${carouselPosition[recipe.recipe_id] || 0}px)` }">
                  <span 
                    v-for="(tag, tagIndex) in recipe.tags" 
                    :key="tagIndex"
                    class="recipe-tag"
                  >
                    {{ getTagTranslation(tag) }}
                  </span>
                  <!-- 复制标签，实现无缝滚动效果 -->
                  <span 
                    v-for="(tag, tagIndex) in recipe.tags" 
                    :key="`copy-${tagIndex}`"
                    class="recipe-tag"
                  >
                    {{ getTagTranslation(tag) }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 基础信息显示 -->
            <div class="recipe-card-info">
              <div v-if="recipe.glass" class="info-item">
                <span class="info-label">酒杯</span>
                <span class="info-value">{{ recipe.glass }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">含酒精</span>
                <span class="info-value">{{ recipe.is_alcoholic ? '是' : '否' }}</span>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="recipe-card-actions">
              <button class="btn btn-outline btn-sm" @click.stop="navigateToDetails(recipe.recipe_id)">
                查看详情
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="filteredRecipes.length === 0" class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <h3 class="empty-state-title">没有找到配方</h3>
        <p class="empty-state-desc">
          尝试调整搜索条件或筛选选项，以找到更多配方。
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchAllRecipes } from '../api/recipeApi';

export default {
  name: 'RecipeView',
  data() {
    return {
      recipes: [],
      loading: false,
      error: null,
      searchQuery: '',
      filterType: null,
      alcoholFilter: null,
      sortBy: 'name',
      carouselPosition: {},
      carouselIntervals: {}
    };
  },
  computed: {
    filteredRecipes() {
      let filtered = this.recipes;
      
      // 搜索过滤
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        filtered = filtered.filter(recipe => {
          const nameZh = recipe.recipe_name_zh ? recipe.recipe_name_zh.toLowerCase() : '';
          const nameEn = recipe.name ? recipe.name.toLowerCase() : '';
          return nameZh.includes(query) || nameEn.includes(query);
        });
      }
      
      // 配方类型过滤
      if (this.filterType) {
        filtered = filtered.filter(recipe => {
          // 处理带-like后缀的情况
          const recipeFamily = recipe.family ? recipe.family.replace('-like', '') : '';
          return recipeFamily === this.filterType;
        });
      }
      
      // 酒精类型过滤
      if (this.alcoholFilter === 'alcoholic') {
        filtered = filtered.filter(recipe => recipe.is_alcoholic);
      } else if (this.alcoholFilter === 'non-alcoholic') {
        filtered = filtered.filter(recipe => !recipe.is_alcoholic);
      }
      
      // 排序
      if (this.sortBy === 'name') {
        filtered.sort((a, b) => {
          const nameA = a.recipe_name_zh || a.name || '';
          const nameB = b.recipe_name_zh || b.name || '';
          return nameA.localeCompare(nameB);
        });
      } else if (this.sortBy === 'recent') {
        // 假设配方有创建时间字段，如果没有则按ID排序
        filtered.sort((a, b) => {
          return b.recipe_id - a.recipe_id;
        });
      }
      
      return filtered;
    }
  },
  mounted() {
    this.fetchRecipes();
  },
  beforeUnmount() {
    // 组件销毁前停止所有轮播
    this.stopAllCarousels();
  },
  methods: {
    async fetchRecipes() {
      this.loading = true;
      try {
        this.recipes = await fetchAllRecipes();
        // 打印每个配方的family字段，检查前后端通信数据
        console.log('Recipes with family:', this.recipes.map(r => ({ id: r.recipe_id, name: r.name, family: r.family })));
        // 打印标签信息，检查是否有足够的标签需要滚动
        this.recipes.forEach(recipe => {
          if (recipe.tags && recipe.tags.length > 3) {
            console.log(`Recipe ${recipe.recipe_id} has ${recipe.tags.length} tags, needs carousel`);
          }
        });
        // 启动所有轮播
        this.startAllCarousels();
        console.log('Carousels started');
      } catch (error) {
        this.error = '获取配方列表失败';
        console.error('Error fetching recipes:', error);
      } finally {
        this.loading = false;
      }
    },
    navigateToDetails(recipeId) {
      this.$router.push({ path: '/visualization', query: { recipe_id: recipeId } });
    },
    getRecipeImage(id) {
      try {
        const imageId = id > 50 ? id - 50 : id;
        return require(`@/assets/recipe_image/${imageId}.png`)
      } catch (e) {
        return require('@/assets/loss.png')
      }
    },
    getTagTranslation(tag) {
      const tagMap = {
        'spirit': '烈酒',
        'mezcal': '梅斯卡尔',
        'sour': '酸味',
        'sweet': '甜味',
        'fruity': '果味',
        'refreshing': '清爽',
        'casual': '休闲',
        'modern': '现代',
        'bitter': '苦味',
        'aromatic': '芳香',
        'wine': '葡萄酒',
        'liqueur': '利口酒',
        'bitters': '苦味酒'
      };
      return tagMap[tag] || tag;
    },
    getFamilyTranslation(family) {
      const familyMap = {
        'Daiquiri': '代基里型',
        'Margarita': '玛格丽塔型',
        'Old Fashioned': '古典鸡尾酒型',
        'Sour': '酸酒型',
        'Martini': '马天尼型',
        'Daiquiri-like': '代基里型',
        'Margarita-like': '玛格丽塔型',
        'Old Fashioned-like': '古典鸡尾酒型',
        'Sour-like': '酸酒型',
        'Martini-like': '马天尼型'
      };
      return familyMap[family] || (family || '未知');
    },
    // 启动标签持续滚动
    startTagCarousel(recipeId) {
      // 清除之前的轮播定时器
      if (this.carouselIntervals[recipeId]) {
        clearInterval(this.carouselIntervals[recipeId]);
      }
      
      // 启动持续滚动
      let position = 0;
      const recipe = this.recipes.find(r => r.recipe_id === recipeId);
      if (!recipe || !recipe.tags || recipe.tags.length <= 3) return;
      
      // 计算实际的总宽度
      const tagWidth = 80; // 每个标签的大致宽度
      const gap = 8; // 标签之间的间隙
      const totalWidth = recipe.tags.length * (tagWidth + gap) - gap;
      
      this.carouselIntervals[recipeId] = setInterval(() => {
        position += 1; // 每次移动1px
        
        // 当滚动完所有标签后，重置位置
        if (position > totalWidth) {
          position = 0;
        }
        
        this.carouselPosition = {
          ...this.carouselPosition,
          [recipeId]: position
        };
      }, 20); // 每20毫秒移动一次，实现更平滑的滚动
    },
    // 停止标签滚动
    stopTagCarousel(recipeId) {
      if (this.carouselIntervals[recipeId]) {
        clearInterval(this.carouselIntervals[recipeId]);
        delete this.carouselIntervals[recipeId];
      }
    },
    // 为所有配方启动轮播
    startAllCarousels() {
      console.log('Starting carousels for recipes:', this.recipes.length);
      this.recipes.forEach(recipe => {
        if (recipe.tags && recipe.tags.length > 3) {
          console.log(`Starting carousel for recipe ${recipe.recipe_id}`);
          this.startTagCarousel(recipe.recipe_id);
        }
      });
    },
    // 停止所有轮播
    stopAllCarousels() {
      Object.keys(this.carouselIntervals).forEach(recipeId => {
        this.stopTagCarousel(recipeId);
      });
    }
  }
};
</script>

<style scoped>
.recipe {
  width: 100%;
  min-height: 100vh;
  background: var(--color-bg-0);
}

/* 页面头部样式 */
.page-header {
  position: relative;
  padding: var(--spacing-3xl) 0;
  overflow: hidden;
}

.page-header-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.header-particles {
  position: absolute;
  inset: 0;
  z-index: 1;
  overflow: hidden;
}

.header-particles::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle, rgba(212, 175, 55, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: particleFloat 20s linear infinite;
}

.header-gradient {
  position: absolute;
  inset: 0;
  z-index: 2;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.6) 50%, rgba(0, 0, 0, 0.8) 100%);
  animation: gradientShift 15s ease-in-out infinite;
}

@keyframes particleFloat {
  0% {
    transform: translateY(0) rotate(0deg);
  }
  100% {
    transform: translateY(-50px) rotate(360deg);
  }
}

@keyframes gradientShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.page-header-content {
  position: relative;
  z-index: 3;
  text-align: center;
}

.page-title {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-top:50px;
  margin-bottom: var(--spacing-md);
  letter-spacing: -0.02em;
  animation: fadeInUp 0.8s ease-out;
}

.page-subtitle {
  font-family: var(--font-body);
  font-size: 18px;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-2xl);
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

.header-stats {
  display: flex;
  justify-content: center;
  gap: var(--spacing-2xl);
  animation: fadeInUp 0.8s ease-out 0.4s both;
}

.header-stats .stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  background: rgba(212, 175, 55, 0.05);
  border: 1px solid var(--color-gold-400);
  border-radius: var(--radius-xl);
  transition: all 0.3s ease;
}

.header-stats .stat-item:hover {
  background: rgba(212, 175, 55, 0.1);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.3);
}

.header-stats .stat-number {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-xs);
}

.header-stats .stat-label {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
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

/* 搜索和筛选区域样式 */
.search-filter-section {
  padding: var(--spacing-2xl) 0;
  background: linear-gradient(135deg, rgba(26, 20, 16, 0.6), rgba(13, 10, 8, 0.8));
  border-bottom: 1px solid var(--color-border-subtle);
  backdrop-filter: blur(10px);
}

.search-filter-content {
  display: flex;
  gap: var(--spacing-xl);
  align-items: flex-start;
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 300px;
  position: relative;
  margin-bottom: var(--spacing-md);
}

.search-icon {
  position: absolute;
  left: var(--spacing-md);
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: var(--color-gold-400);
  transition: all 0.3s ease;
}

.search-input {
  width: 100%;
  padding: var(--spacing-md) var(--spacing-md) var(--spacing-md) 48px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  transition: all 0.3s ease;
  backdrop-filter: blur(5px);
}

.search-input::placeholder {
  color: var(--color-text-secondary);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-gold-400);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
}

.search-input:focus + .search-icon {
  color: var(--color-gold-300);
  transform: translateY(-50%) scale(1.1);
}

.filter-groups {
  display: flex;
  gap: var(--spacing-xl);
  flex-wrap: wrap;
  flex: 1;
  min-width: 300px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.filter-label {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-gold-400);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: var(--spacing-xs);
}

.filter-options {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.filter-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(5px);
}

.filter-btn:hover {
  border-color: var(--color-gold-400);
  color: var(--color-gold-300);
  background: rgba(212, 175, 55, 0.1);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.filter-btn.active {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  border-color: var(--color-gold-500);
  color: var(--color-bg-0);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
}

.filter-btn.active:hover {
  background: linear-gradient(135deg, var(--color-gold-600), var(--color-gold-500));
  border-color: var(--color-gold-600);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
}

/* 带注解的筛选按钮 */
.filter-btn-with-tooltip {
  position: relative;
  display: inline-block;
}

/* 注解气泡卡片 */
.tooltip {
  position: absolute;
  bottom: 120%;
  left: 50%;
  transform: translateX(-50%);
  width: 250px;
  padding: var(--spacing-md);
  background: rgba(0, 0, 0, 0.9);
  border: 1px solid var(--color-gold-400);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.3);
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

/* 注解气泡卡片的箭头 */
.tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border-width: 8px;
  border-style: solid;
  border-color: var(--color-gold-400) transparent transparent transparent;
}

/* 鼠标悬停时显示注解气泡卡片 */
.filter-btn-with-tooltip:hover .tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-8px);
}

/* 注解气泡卡片的标题 */
.tooltip h4 {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-xs);
  letter-spacing: 0.05em;
}

/* 注解气泡卡片的内容 */
.tooltip p {
  font-family: var(--font-body);
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-secondary);
  margin: 0;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .tooltip {
    width: 200px;
    font-size: 11px;
  }
}

/* 配方头部样式 */
.recipe-header {
  margin-bottom: var(--spacing-2xl);
  padding: var(--spacing-xl) 0;
  border-bottom: 1px solid var(--color-border-subtle);
}

.recipe-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-lg);
}

.recipe-header-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.recipe-header-subtitle {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-gold-400);
  font-weight: 500;
}

/* 配方卡片样式 */
.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-xl);
  padding: var(--spacing-2xl) 0;
}

.recipe-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  animation: fadeInUp 0.8s ease-out both;
  position: relative;
  backdrop-filter: blur(5px);
}

.recipe-card:hover {
  border-color: var(--color-gold-400);
  transform: translateY(-8px);
  box-shadow: 0 16px 32px rgba(212, 175, 55, 0.3);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
}

.recipe-card-image {
  position: relative;
  height: 200px;
  overflow: hidden;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.recipe-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.5s ease;
}

.recipe-card:hover .recipe-image {
  transform: scale(1.1);
}

.recipe-card-badges {
  position: absolute;
  top: var(--spacing-md);
  left: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  z-index: 10;
}

.badge {
  padding: 6px 12px;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  border-radius: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.badge-alcoholic {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
}

.badge-non-alcoholic {
  background: linear-gradient(135deg, #4ecdc4, #45b7aa);
  color: white;
}

.badge-source {
  background: linear-gradient(135deg, #ffd93d, #f9a825);
  color: #2d1c00;
  font-weight: 800;
}

.badge-family {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 600;
}

.recipe-card-content {
  padding: var(--spacing-lg);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.recipe-card-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  transition: all 0.3s ease;
  line-height: 1.3;
}

.recipe-card:hover .recipe-card-name {
  color: var(--color-gold-200);
}

.recipe-card-name .name-zh {
  color: var(--color-text-primary);
  font-weight: 600;
}

.recipe-card-name .name-en {
  color: var(--color-text-secondary);
  font-weight: 400;
  font-size: 0.9em;
}

.recipe-card-name .name-separator {
  color: var(--color-gold-400);
  margin: 0 0.25rem;
}

/* 标签样式 */
.recipe-card-tags {
  position: relative;
  overflow: hidden;
  width: 100%;
  animation: fadeInUp 0.8s ease-out 0.3s both;
  padding-bottom: 4px;
  height: 30px; /* 固定高度，确保标签能够垂直居中 */
  display: flex;
  align-items: center;
}

/* 轮播容器 */
.tags-carousel {
  width: 100%;
  overflow: hidden;
  position: relative;
  height: 100%;
}

/* 轮播轨道 */
.tags-track {
  display: flex;
  gap: 8px;
  transition: transform 0s linear;
  will-change: transform;
  height: 100%;
  align-items: center;
}

/* 标签样式 */
.recipe-tag {
  padding: 4px 12px;
  background: linear-gradient(135deg, #d4af37, #f9a825);
  color: #2d1c00;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  flex-shrink: 0;
  min-width: 80px;
  text-align: center;
}

.recipe-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
  background: linear-gradient(135deg, #f9a825, #d4af37);
}

/* 调整徽章样式，使其与标签在同一行显示 */
.recipe-card-tags .badge {
  margin-right: 0;
  white-space: nowrap;
  flex-shrink: 0;
}

.recipe-card-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 14px;
  color: var(--color-text-secondary);
  transition: all 0.3s ease;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-md);
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.recipe-card:hover .info-item {
  color: var(--color-text-primary);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(212, 175, 55, 0.2);
  transform: translateX(4px);
}

.info-icon {
  width: 18px;
  height: 18px;
  color: var(--color-gold-400);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.recipe-card:hover .info-icon {
  color: var(--color-gold-200);
  transform: scale(1.1);
}

.info-label {
  font-family: var(--font-body);
  font-weight: 600;
  color: var(--color-gold-400);
  margin-right: 8px;
  flex-shrink: 0;
}

.info-value {
  font-family: var(--font-body);
  flex: 1;
  color: var(--color-text-primary);
}

.recipe-card:hover .info-value {
  color: var(--color-text-primary);
}

.recipe-card:hover .info-text {
  color: var(--color-text-primary);
}

.recipe-card-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: auto;
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-subtle);
}

.recipe-card-actions .btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: 14px;
  transition: all 0.3s ease;
}

.recipe-card-actions .btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
}

.recipe-card-actions .btn-icon {
  width: 16px;
  height: 16px;
}

.recipe-card-actions .btn-primary {
  background: var(--color-gold-500);
  border: 1px solid var(--color-gold-500);
  color: var(--color-bg-0);
}

.recipe-card-actions .btn-primary:hover {
  background: var(--color-gold-600);
  border-color: var(--color-gold-600);
}

.recipe-card-actions .btn-outline {
  background: transparent;
  border: 1px solid var(--color-gold-400);
  color: var(--color-gold-400);
}

.recipe-card-actions .btn-outline:hover {
  background: var(--color-gold-400);
  color: var(--color-bg-0);
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: var(--spacing-3xl);
  text-align: center;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  backdrop-filter: blur(10px);
  transition: all var(--transition-normal);
  margin: var(--spacing-2xl) 0;
}

.empty-state:hover {
  border-color: var(--color-gold-300);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.02));
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.1);
}

.empty-state-icon {
  font-size: 64px;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
  transition: opacity var(--transition-normal);
}

.empty-state:hover .empty-state-icon {
  opacity: 0.8;
  transform: scale(1.1);
}

.empty-state-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  transition: color var(--transition-normal);
}

.empty-state:hover .empty-state-title {
  color: var(--color-gold-400);
}

.empty-state-desc {
  font-size: 14px;
  line-height: 1.6;
  max-width: 400px;
  color: var(--color-text-secondary);
  transition: color var(--transition-normal);
}

.empty-state:hover .empty-state-desc {
  color: var(--color-text-primary);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: var(--spacing-3xl);
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(212, 175, 55, 0.2);
  border-left-color: var(--color-gold-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-lg);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: var(--spacing-3xl);
  text-align: center;
}

.error-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-lg);
}

.error-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.error-message {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
  max-width: 600px;
}

.recipe-header {
  margin-bottom: var(--spacing-3xl);
}

.recipe-header-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-2xl);
  padding: var(--spacing-2xl);
}

.recipe-header-info {
  flex: 1;
}

.recipe-header-image {
  flex-shrink: 0;
  width: 300px;
  height: 200px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.recipe-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recipe-name {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-md);
  letter-spacing: -0.01em;
}

.recipe-subtitle {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
  line-height: 1.6;
}

.recipe-meta {
  display: flex;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

.recipe-meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(212, 175, 55, 0.05);
  border-radius: var(--radius-md);
}

.meta-icon {
  font-size: 16px;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-3xl);
}

.left-column,
.middle-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.ingredient-structure,
.sqe-analysis,
.flavor-distribution,
.key-flavors,
.local-graph,
.substitute-suggestions {
  padding: var(--spacing-2xl);
  border-radius: var(--radius-lg);
  background: var(--color-bg-1);
  border: 1px solid var(--color-border-subtle);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
  letter-spacing: -0.01em;
}

.ingredient-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.ingredient-item {
  padding: var(--spacing-md);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ingredient-item:hover {
  background: rgba(212, 175, 55, 0.08);
  border-color: var(--color-gold-400);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.1);
}

.ingredient-name {
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.ingredient-details {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.ingredient-amount {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.ingredient-role {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-gold-400);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: var(--radius-sm);
}

.ingredient-meta {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.ingredient-category,
.ingredient-abv {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.ingredient-canonical {
  display: flex;
  gap: var(--spacing-sm);
}

.canonical-name,
.anchor-name {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-style: italic;
}

.sqe-overall {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  background: rgba(212, 175, 55, 0.05);
  border-radius: var(--radius-md);
}

.sqe-score {
  text-align: center;
}

.score-number {
  display: block;
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 600;
  color: var(--color-gold-300);
  line-height: 1;
}

.score-label {
  display: block;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-sm);
}

.sqe-rank,
.sqe-confidence {
  text-align: center;
}

.rank-label,
.confidence-label {
  display: block;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-xs);
}

.rank-value,
.confidence-value {
  display: block;
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.sqe-components {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.component-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-name {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.component-score {
  font-family: var(--font-display);
  font-size: 16px;
  color: var(--color-gold-300);
  font-weight: 600;
}

.component-bar {
  width: 100%;
  height: 8px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 1s ease-out;
}

.synergy-bar {
  background: linear-gradient(90deg, #4CAF50, #81C784);
}

.conflict-bar {
  background: linear-gradient(90deg, #FF5252, #FF8A80);
}

.balance-bar {
  background: linear-gradient(90deg, #2196F3, #64B5F6);
}

.flavor-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
}

.radar-chart-container,
.role-chart-container {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(212, 175, 55, 0.05);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
}

.chart {
  width: 100%;
  height: 100%;
}

.balance-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border-subtle);
}

.balance-score .score-label {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
}

.balance-score .score-value {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-gold-300);
}

.key-flavor-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.key-flavor-item {
  padding: var(--spacing-md);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
}

.key-flavor-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.flavor-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-gold-500);
  color: var(--color-bg-0);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

.flavor-name {
  flex: 1;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.flavor-contribution {
  font-family: var(--font-display);
  font-size: 14px;
  color: var(--color-gold-300);
  font-weight: 600;
}

.contribution-bar {
  width: 100%;
  height: 6px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: var(--spacing-sm);
}

.contribution-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-gold-400), var(--color-gold-500));
  border-radius: 3px;
  transition: width 1s ease-out;
}

.flavor-metrics {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.metric {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.flavor-explanation {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.4;
  font-style: italic;
}

.local-graph-section {
  margin-bottom: var(--spacing-3xl);
}

.graph-controls {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.graph-control-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(212, 175, 55, 0.05);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.graph-control-btn:hover {
  background: rgba(212, 175, 55, 0.1);
  border-color: var(--color-gold-400);
  color: var(--color-gold-400);
}

.graph-control-btn.active {
  background: var(--color-gold-400);
  border-color: var(--color-gold-400);
  color: var(--color-bg-0);
}

.graph-container {
  height: 400px;
  background: rgba(212, 175, 55, 0.05);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
}

.substitute-section {
  margin-bottom: var(--spacing-3xl);
}

.substitute-prompt,
.substitute-loading {
  padding: var(--spacing-2xl);
  text-align: center;
  background: rgba(212, 175, 55, 0.05);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
}

.substitute-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.substitute-item {
  padding: var(--spacing-md);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
}

.substitute-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.substitute-name {
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.substitute-flag {
  font-family: var(--font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.substitute-flag.accept {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
}

.substitute-flag.reject {
  background: rgba(255, 82, 82, 0.1);
  color: #FF5252;
}

.substitute-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.substitute-roles {
  display: flex;
  gap: var(--spacing-md);
}

.role-item {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.substitute-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.substitute-score .score-label {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.substitute-score .score-value {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
}

.substitute-score .score-value.positive {
  color: #4CAF50;
}

.substitute-score .score-value.negative {
  color: #FF5252;
}

.substitute-explanation {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.4;
  font-style: italic;
}

.substitute-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.action-section {
  margin-bottom: var(--spacing-3xl);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
}

.btn {
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background: var(--color-gold-500);
  border: 1px solid var(--color-gold-500);
  color: var(--color-bg-0);
}

.btn-primary:hover {
  background: var(--color-gold-600);
  border-color: var(--color-gold-600);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--color-gold-400);
  color: var(--color-gold-400);
}

.btn-secondary:hover {
  background: var(--color-gold-400);
  color: var(--color-bg-0);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
}

.btn-outline:hover {
  background: rgba(212, 175, 55, 0.05);
  border-color: var(--color-gold-400);
  color: var(--color-gold-400);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: 12px;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .recipe-header-content {
    flex-direction: column;
    text-align: center;
  }
  
  .recipe-header-image {
    width: 100%;
    max-width: 400px;
  }
  
  .flavor-charts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .recipe {
    padding: var(--spacing-xl) 0;
  }
  
  .container {
    padding: 0 var(--spacing-md);
  }
  
  .recipe-header-content,
  .ingredient-structure,
  .sqe-analysis,
  .flavor-distribution,
  .key-flavors,
  .local-graph,
  .substitute-suggestions {
    padding: var(--spacing-xl);
  }
  
  .recipe-name {
    font-size: 28px;
  }
  
  .sqe-overall {
    flex-direction: column;
    gap: var(--spacing-lg);
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
  }
  
  .graph-container {
    height: 300px;
  }
}

.recipe-overview {
  margin-bottom: var(--spacing-3xl);
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.recipe-card-overview {
  padding: var(--spacing-xl);
  transition: all var(--transition-fast);
  cursor: pointer;
  border: 1px solid var(--color-border-subtle);
}

.recipe-card-overview:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2), 0 0 30px rgba(212, 175, 55, 0.15);
  border-color: var(--color-gold-400);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(184, 134, 11, 0.08) 100%);
  animation: cardGlow 2s ease-in-out infinite alternate;
}

@keyframes cardGlow {
  from {
    box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2), 0 0 30px rgba(212, 175, 55, 0.15);
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(184, 134, 11, 0.08) 100%);
  }
  to {
    box-shadow: 0 8px 24px rgba(212, 175, 55, 0.3), 0 0 40px rgba(212, 175, 55, 0.25);
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(184, 134, 11, 0.12) 100%);
  }
}

.recipe-card-overview-header {
  margin-bottom: var(--spacing-lg);
}

.recipe-card-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.01em;
}

.recipe-card-name .name-zh {
  color: var(--color-text-primary);
  font-weight: 600;
}

.recipe-card-name .name-en {
  color: var(--color-text-secondary);
  font-weight: 400;
  font-size: 0.9em;
}

.recipe-card-name .name-separator {
  color: var(--color-gold-400);
  margin: 0 0.25rem;
}

.recipe-card-meta {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.recipe-card-category,
.recipe-card-origin {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: var(--radius-sm);
}

.recipe-card-ingredients {
  margin-bottom: var(--spacing-lg);
}

.recipe-card-ingredient-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.recipe-card-ingredient-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: rgba(212, 175, 55, 0.04);
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.recipe-card-ingredient-name {
  font-family: var(--font-body);
  color: var(--color-text-primary);
}

.recipe-card-ingredient-amount {
  font-family: var(--font-body);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.recipe-card-ingredient-more {
  padding: var(--spacing-sm);
  text-align: center;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-style: italic;
}

.recipe-card-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-gold-400);
  color: var(--color-gold-400);
  transition: all var(--transition-fast);
}

.btn-outline:hover {
  background: var(--color-gold-400);
  color: var(--color-bg-0);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-md);
  font-size: 12px;
}

.page-header {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, rgba(184, 134, 11, 0.03) 100%);
  border-bottom: 1px solid var(--color-border-subtle);
  padding: var(--spacing-2xl) 0;
  margin-bottom: var(--spacing-3xl);
}

.page-header-content {
  text-align: center;
}

.page-title {
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl);
}

.recipe-selector {
  margin-bottom: var(--spacing-3xl);
  padding: var(--spacing-xl);
}

.recipe-selector-header {
  margin-bottom: var(--spacing-lg);
}

.recipe-selector-content {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
}

.recipe-select {
  flex: 1;
  padding: var(--spacing-md);
  background: rgba(212, 175, 55, 0.05);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  font-size: 14px;
}

.recipe-select option {
  background: var(--color-bg-2);
  color: var(--color-text-primary);
}

.recipe-showcase {
  margin-bottom: var(--spacing-3xl);
}

.recipe-card {
  padding: var(--spacing-2xl);
  display: flex;
  flex-direction: column;
}

.recipe-card-image {
  width: 100%;
  height: 200px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: var(--spacing-xl);
  background: rgba(212, 175, 55, 0.05);
}

.recipe-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.recipe-card:hover .recipe-image {
  transform: scale(1.05);
}

.recipe-card-header {
  margin-bottom: var(--spacing-xl);
  text-align: center;
}

.recipe-name {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.01em;
}

.recipe-meta {
  display: flex;
  justify-content: center;
  gap: var(--spacing-lg);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
}

.recipe-ingredients {
  margin-bottom: var(--spacing-xl);
}

.ingredients-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.ingredient-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.ingredient-item:hover {
  background: rgba(212, 175, 55, 0.08);
  border-color: var(--color-border-strong);
}

.ingredient-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.ingredient-name {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
}

.ingredient-role {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-gold-400);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 2px 8px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: var(--radius-sm);
}

.ingredient-amount {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.recipe-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-md);
}

.sqe-analysis {
  margin-bottom: var(--spacing-3xl);
}

.sqe-grid {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  gap: var(--spacing-lg);
}

.sqe-overall {
  padding: var(--spacing-xl);
  text-align: center;
}

.sqe-overall-score {
  margin: var(--spacing-lg) 0;
}

.score-number {
  display: block;
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 600;
  color: var(--color-gold-300);
  line-height: 1;
}

.score-label {
  display: block;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-top: var(--spacing-sm);
}

.sqe-overall-bar {
  margin-top: var(--spacing-lg);
}

.score-bar {
  width: 100%;
  height: 8px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-gold-400), var(--color-gold-500));
  border-radius: 4px;
  transition: width 1s ease-out;
}

.sqe-radar {
  padding: var(--spacing-xl);
}

.radar-chart {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.sqe-components {
  padding: var(--spacing-xl);
}

.component-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.component-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-name {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.component-score {
  font-family: var(--font-display);
  font-size: 16px;
  color: var(--color-gold-300);
  font-weight: 600;
}

.component-bar {
  width: 100%;
  height: 6px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 1s ease-out;
}

.synergy-bar {
  background: linear-gradient(90deg, #4CAF50, #81C784);
}

.conflict-bar {
  background: linear-gradient(90deg, #FF5252, #FF8A80);
}

.balance-bar {
  background: linear-gradient(90deg, #2196F3, #64B5F6);
}

.structure-explanation {
  margin-bottom: var(--spacing-3xl);
  padding: var(--spacing-2xl);
}

.explanation-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.explanation-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.explanation-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-gold-200);
}

.explanation-text {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.key-flavors {
  margin-bottom: var(--spacing-3xl);
}

.key-flavors-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.key-flavors-list {
  padding: var(--spacing-xl);
}

.flavor-ranking {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
}

.flavor-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.flavor-item:hover {
  background: rgba(212, 175, 55, 0.08);
  border-color: var(--color-border-strong);
}

.flavor-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-gold-500);
  color: var(--color-bg-0);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

.flavor-name {
  flex: 1;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
}

.flavor-importance {
  font-family: var(--font-display);
  font-size: 14px;
  color: var(--color-gold-300);
  font-weight: 600;
}

.local-graph {
  padding: var(--spacing-xl);
}

.graph-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  margin-top: var(--spacing-lg);
}

.section-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
}

.section-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  letter-spacing: -0.01em;
}

.section-subtitle {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.2em;
  margin-bottom: var(--spacing-lg);
}

.btn-icon {
  width: 18px;
  height: 18px;
}

@media (max-width: 1200px) {
  .sqe-grid {
    grid-template-columns: 1fr;
  }
  
  .key-flavors-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .recipe-selector-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .recipe-card {
    padding: var(--spacing-xl);
  }
  
  .recipe-name {
    font-size: 24px;
  }
  
  /* 页面头部响应式 */
  .page-title {
    font-size: 36px;
  }
  
  .page-subtitle {
    font-size: 16px;
  }
  
  .header-stats {
    flex-direction: column;
    gap: var(--spacing-md);
  }
  
  .header-stats .stat-item {
    padding: var(--spacing-md) var(--spacing-lg);
  }
  
  .header-stats .stat-number {
    font-size: 28px;
  }
  
  /* 搜索和筛选响应式 */
  .search-filter-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    min-width: auto;
  }
  
  .filter-options {
    justify-content: center;
  }
  
  /* 配方卡片响应式 */
  .recipe-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-lg);
  }
  
  .recipe-card-image {
    height: 200px;
  }
  
  .recipe-card-content {
    padding: var(--spacing-lg);
  }
  
  .recipe-card-name {
    font-size: 18px;
  }
  
  .recipe-card-actions .btn {
    padding: var(--spacing-xs) var(--spacing-md);
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: var(--spacing-2xl) 0;
  }
  
  .page-title {
    font-size: 28px;
  }
  
  .page-subtitle {
    font-size: 14px;
  }
  
  .header-stats .stat-number {
    font-size: 24px;
  }
  
  .header-stats .stat-label {
    font-size: 12px;
  }
  
  .recipe-card-image {
    height: 180px;
  }
  
  .recipe-card-name {
    font-size: 16px;
  }
  
  .info-text {
    font-size: 13px;
  }
}
</style>