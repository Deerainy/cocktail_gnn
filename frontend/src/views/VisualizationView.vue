<template>
  <div class="visualization">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载配方数据中...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">加载失败</h2>
      <p class="error-message">{{ error }}</p>
      <button class="btn btn-primary" @click="fetchRecipeData">重新加载</button>
    </div>
    
    <!-- 配方内容 -->
    <template v-else>
      <!-- 页面头部 -->
      <header class="page-header">
        <div class="container">
          <div class="page-header-content">
            <h1 class="page-title">配方详情</h1>
            <p class="page-subtitle">深入分析配方的风味特性</p>
          </div>
        </div>
      </header>
      
      <!-- 配方头部信息区 -->
      <section class="recipe-header-section">
        <div class="container">
          <div class="recipe-header-card card">
            <div class="recipe-header-content">
              <div class="recipe-header-info">
                <h2 class="recipe-name">{{ recipe?.name || '莫吉托' }}</h2>
                <p class="recipe-subtitle">{{ recipe?.instructions || '清爽型经典鸡尾酒' }}</p>
                <div class="recipe-meta">
                  <div class="recipe-meta-item">
                    <i class="meta-icon">🥃</i>
                    <span class="meta-label">玻璃类型</span>
                    <span class="meta-value">{{ recipe?.glass || '高ball杯' }}</span>
                  </div>
                  <div class="recipe-meta-item">
                    <i class="meta-icon">🏷️</i>
                    <span class="meta-label">标签</span>
                    <span class="meta-value">{{ recipe?.tags?.join(', ') || '经典, 清爽, 古巴' }}</span>
                  </div>
                  <div class="recipe-meta-item">
                    <i class="meta-icon">🍷</i>
                    <span class="meta-label">酒精含量</span>
                    <span class="meta-value">{{ recipe?.is_alcoholic ? '含酒精' : '无酒精' }}</span>
                  </div>
                </div>
              </div>
              <div class="recipe-header-image">
                <img 
                  :src="recipe?.image_url || 'https://example.com/margarita.jpg'" 
                  :alt="recipe?.name || '莫吉托'"
                  class="recipe-image"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- 主要内容区 -->
      <section class="main-content-section">
        <div class="container">
          <!-- 第一行：原料结构 + SQE分析 + 风味分布 + 关键风味识别 -->
          <div class="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
            <!-- 原料结构 -->
            <div class="lg:col-span-1">
              <div class="ingredient-structure card">
                <h3 class="card-title">原料结构</h3>
                <div class="ingredient-list">
                  <div 
                    v-for="(ingredient, index) in ingredients" 
                    :key="ingredient.ingredient_id || index"
                    class="ingredient-item"
                    @click="selectIngredient(ingredient)"
                  >
                    <div class="ingredient-header">
                      <h4 class="ingredient-name">{{ ingredient.ingredient?.name_norm || ingredient.raw_text }}</h4>
                      <span :class="['ingredient-role', `role-${ingredient.role}`]">{{ ingredient.role }}</span>
                    </div>
                    <div class="ingredient-info">
                      <span class="ingredient-amount">{{ ingredient.amount }} {{ ingredient.unit }}</span>
                      <span class="ingredient-category" v-if="ingredient.ingredient">{{ ingredient.ingredient.category }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- SQE分析 + 风味分布 -->
            <div class="lg:col-span-2">
              <div class="combined-card card">
                <h3 class="card-title">SQE 分析</h3>
                <div class="sqe-overall">
                  <div class="sqe-score">
                    <span class="score-number">{{ (sqe?.final_sqe_total || 0.82) * 10 }}</span>
                    <span class="score-label">{{ getScoreLabel(sqe?.final_sqe_total || 0.82) }}</span>
                  </div>
                  <div class="sqe-stats">
                    <div class="stat-item">
                      <span class="stat-label">排名</span>
                      <span class="stat-value">{{ sqe?.rank_in_snapshot || 1 }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">置信度</span>
                      <span class="stat-value">{{ (sqe?.phaseC_confidence || 0.9) * 100 }}%</span>
                    </div>
                  </div>
                </div>
                <div class="sqe-triple-bar">
                  <div class="triple-bar-labels">
                    <span class="triple-label synergy-label">协同性</span>
                    <span class="triple-label conflict-label">冲突度</span>
                    <span class="triple-label balance-label">平衡性</span>
                  </div>
                  <div class="triple-bar-container">
                    <div class="triple-bar-fill synergy-fill" :style="{ width: (sqe?.phaseB_synergy_score || 0.28883) * 100 + '%' }">
                      <span class="triple-value">{{ ((sqe?.phaseB_synergy_score || 0.28883) * 100).toFixed(1) }}%</span>
                    </div>
                    <div class="triple-bar-fill conflict-fill" :style="{ width: (sqe?.phaseB_conflict_score || 1.14334) * 100 + '%' }">
                      <span class="triple-value">{{ ((sqe?.phaseB_conflict_score || 1.14334) * 100).toFixed(1) }}%</span>
                    </div>
                    <div class="triple-bar-fill balance-fill" :style="{ width: (sqe?.phaseB_balance_score || 0.78) * 100 + '%' }">
                      <span class="triple-value">{{ ((sqe?.phaseB_balance_score || 0.78) * 100).toFixed(1) }}%</span>
                    </div>
                  </div>
                  <div class="triple-bar-legend">
                    <div class="legend-item">
                      <div class="legend-color synergy-color"></div>
                      <span class="legend-text">协同性 (Synergy)</span>
                    </div>
                    <div class="legend-item">
                      <div class="legend-color conflict-color"></div>
                      <span class="legend-text">冲突度 (Conflict)</span>
                    </div>
                    <div class="legend-item">
                      <div class="legend-color balance-color"></div>
                      <span class="legend-text">平衡性 (Balance)</span>
                    </div>
                  </div>
                </div>
                
                <h3 class="card-title mt-4">风味分布</h3>
                <div class="flavor-charts">
                  <!-- 风味雷达图 -->
                  <div class="radar-chart-container">
                    <div class="radar-chart">
                      <div class="radar-chart-grid">
                        <div class="radar-chart-circle"></div>
                        <div class="radar-chart-circle"></div>
                        <div class="radar-chart-circle"></div>
                        <div class="radar-chart-line"></div>
                        <div class="radar-chart-line"></div>
                        <div class="radar-chart-line"></div>
                        <div class="radar-chart-line"></div>
                        <div class="radar-chart-line"></div>
                        <div class="radar-chart-line"></div>
                      </div>
                      <div class="radar-chart-data" :style="getRadarChartStyle()"></div>
                      <div class="radar-chart-labels">
                        <div class="radar-label">酸味</div>
                        <div class="radar-label">甜味</div>
                        <div class="radar-label">苦味</div>
                        <div class="radar-label">香气</div>
                        <div class="radar-label">果味</div>
                        <div class="radar-label">酒体</div>
                      </div>
                    </div>
                  </div>
                  <!-- 风味条形图 -->
                  <div class="flavor-bars-container">
                    <div class="flavor-bars">
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">酸味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_sour || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_sour || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">甜味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_sweet || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_sweet || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">苦味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_bitter || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_bitter || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">香气</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_aroma || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_aroma || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">果味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_fruity || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_fruity || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">酒体</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_body || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_body || 0) * 100).toFixed(0) }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 关键风味识别 -->
            <div class="lg:col-span-1">
              <div class="key-flavors card">
                <h3 class="card-title">关键风味识别</h3>
                <div class="key-flavor-list">
                  <div 
                    v-for="(node, index) in keyNodes" 
                    :key="node.canonical_id || index"
                    :class="['key-flavor-item', `rank-${node.rank_no}`]"
                  >
                    <div class="key-flavor-header">
                      <span class="flavor-rank">{{ node.rank_no }}</span>
                      <span class="flavor-name">{{ node.ingredient_name }}</span>
                      <span class="flavor-contribution">{{ node.normalized_contribution.toFixed(2) }}</span>
                    </div>
                    <div class="contribution-bar">
                      <div class="contribution-fill" :style="{ width: (node.normalized_contribution * 100) + '%' }"></div>
                    </div>
                    <div class="flavor-metrics">
                      <span class="metric">协同: {{ (node.base_score || 0).toFixed(2) }}</span>
                      <span class="metric">贡献: {{ (node.learned_contribution || 0).toFixed(2) }}</span>
                      <span class="metric">占比: {{ (node.contribution_ratio || 0).toFixed(2) }}</span>
                    </div>
                    <div class="flavor-explanation" v-if="node.explanation">
                      <p>{{ node.explanation }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 第二行：局部风味关系图 -->
          <div class="local-graph-section mb-6">
            <div class="local-graph card">
              <h3 class="card-title">局部风味关系图</h3>
              <div class="graph-controls">
                <button 
                  v-for="layer in graphLayers" 
                  :key="layer.value"
                  :class="['graph-control-btn', { active: graphLayer === layer.value }]"
                  @click="switchGraphLayer(layer.value)"
                >
                  {{ layer.label }}
                </button>
              </div>
              <div class="graph-container">
                <div class="graph-placeholder">
                  <div class="graph-placeholder-icon">📊</div>
                  <p class="graph-placeholder-text">风味关系图</p>
                  <p class="graph-placeholder-subtext">选择不同视图查看风味关系</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 第三行：替代建议 -->
          <div class="substitute-section mb-6">
            <div class="substitute-suggestions card">
              <h3 class="card-title">替代建议</h3>
              <div v-if="!selectedIngredient" class="substitute-prompt">
                <div class="prompt-icon">🔄</div>
                <p class="prompt-text">点击上方原料列表中的任意原料，查看可能的替代建议</p>
              </div>
              <div v-else-if="substitutes.length === 0" class="substitute-loading">
                <div class="loading-spinner small"></div>
                <p class="loading-text">加载替代建议中...</p>
              </div>
              <div v-else class="substitute-list">
                <div 
                  v-for="(substitute, index) in substitutes" 
                  :key="substitute.candidate_canonical_id || index"
                  class="substitute-item"
                >
                  <div class="substitute-header">
                    <span class="substitute-name">{{ substitute.candidate_name || '金朗姆酒' }}</span>
                    <span :class="['substitute-flag', substitute.accept_flag ? 'accept' : 'reject']">
                      {{ substitute.accept_flag ? '可接受' : '不推荐' }}
                    </span>
                  </div>
                  <div class="substitute-details">
                    <div class="substitute-roles">
                      <span class="role-item">原角色: {{ substitute.target_role }}</span>
                      <span class="role-item">新角色: {{ substitute.candidate_role }}</span>
                    </div>
                    <div class="substitute-score">
                      <span class="score-label">SQE变化:</span>
                      <span :class="['score-value', substitute.delta_sqe >= 0 ? 'positive' : 'negative']">
                        {{ substitute.delta_sqe >= 0 ? '+' : '' }}{{ substitute.delta_sqe.toFixed(2) }}
                      </span>
                    </div>
                    <div class="substitute-explanation" v-if="substitute.explanation">
                      <p>{{ substitute.explanation }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 底部：操作区 -->
          <div class="action-section">
            <div class="action-buttons">
              <router-link 
                :to="{ path: '/graph', query: { recipe_id: recipe?.recipe_id } }"
                class="btn btn-primary"
              >
                查看全局风味图谱
              </router-link>
              <router-link 
                :to="{ path: '/adjust', query: { recipe_id: recipe?.recipe_id, target_canonical_id: selectedIngredient?.ingredient?.canonical_id } }"
                class="btn btn-secondary"
                v-if="selectedIngredient"
              >
                替代这个原料
              </router-link>
              <router-link 
                :to="{ path: '/generate', query: { recipe_id: recipe?.recipe_id } }"
                class="btn btn-secondary"
              >
                基于此配方生成变体
              </router-link>
              <router-link 
                to="/recipe"
                class="btn btn-outline"
              >
                返回配方列表
              </router-link>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import { fetchRecipe, fetchIngredients, fetchSQE, fetchBalance, fetchKeyNodes, fetchSubstitutes } from '../api/recipeApi';

export default {
  name: 'VisualizationView',
  data() {
    return {
      recipe: null,
      ingredients: [],
      sqe: null,
      balance: null,
      keyNodes: [],
      substitutes: [],
      selectedIngredient: null,
      graphLayer: 'compat',
      graphLayers: [
        { label: '兼容性', value: 'compat' },
        { label: '共现性', value: 'cooccur' },
        { label: '风味', value: 'flavor' },
        { label: '混合', value: 'mixed' }
      ],
      loading: false,
      error: null
    };
  },
  mounted() {
    this.fetchRecipeData();
  },
  methods: {
    async fetchRecipeData() {
      const recipeId = this.$route.query.recipe_id || '123';
      this.loading = true;
      try {
        const [recipeData, ingredientsData, sqeData, balanceData, keyNodesData] = await Promise.all([
          fetchRecipe(recipeId),
          fetchIngredients(recipeId),
          fetchSQE(recipeId),
          fetchBalance(recipeId),
          fetchKeyNodes(recipeId)
        ]);
        this.recipe = recipeData;
        this.ingredients = ingredientsData;
        this.sqe = sqeData;
        this.balance = balanceData;
        this.keyNodes = keyNodesData;
      } catch (error) {
        this.error = '获取配方数据失败';
        console.error('Error fetching recipe data:', error);
      } finally {
        this.loading = false;
      }
    },
    async selectIngredient(ingredient) {
      this.selectedIngredient = ingredient;
      const recipeId = this.$route.query.recipe_id || '123';
      const targetCanonicalId = ingredient.ingredient?.canonical_id;
      if (targetCanonicalId) {
        this.substitutes = await fetchSubstitutes(recipeId, targetCanonicalId);
      } else {
        this.substitutes = [];
      }
    },
    switchGraphLayer(layer) {
      this.graphLayer = layer;
      // 这里可以添加获取图谱数据的逻辑
    },
    getScoreLabel(score) {
      if (score >= 0.9) return '卓越';
      if (score >= 0.8) return '优秀';
      if (score >= 0.7) return '良好';
      if (score >= 0.6) return '一般';
      return '需要改进';
    },
    getRadarChartStyle() {
      const center = 50;
      const radius = 45;
      const flavors = [
        this.balance?.f_sour || 0,
        this.balance?.f_sweet || 0,
        this.balance?.f_bitter || 0,
        this.balance?.f_aroma || 0,
        this.balance?.f_fruity || 0,
        this.balance?.f_body || 0
      ];
      
      const points = flavors.map((value, index) => {
        const angle = (Math.PI * 2 / 6) * index - Math.PI / 2;
        const x = center + radius * value * Math.cos(angle);
        const y = center + radius * value * Math.sin(angle);
        return `${x}% ${y}%`;
      });
      
      return {
        clipPath: `polygon(${points.join(', ')})`
      };
    }
  }
};
</script>

<style scoped>
/* 全局样式 */
.visualization {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  color: #e0e0e0;
}

/* 容器 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
  color: white;
  padding: 2rem 0;
  margin-bottom: 2rem;
}

.page-header-content {
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  font-family: 'Playfair Display', serif;
  letter-spacing: 1px;
}

.page-subtitle {
  font-size: 1.125rem;
  opacity: 0.9;
}

/* 卡片 */
.card {
  background: #2a2a2a;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3), 0 1px 3px rgba(0, 0, 0, 0.2);
  padding: 1.5rem;
  transition: all 0.3s ease;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.card:hover {
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.4), 0 4px 6px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
  border-color: rgba(212, 175, 55, 0.4);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #d4af37;
  margin-bottom: 1.25rem;
  border-bottom: 2px solid rgba(212, 175, 55, 0.3);
  padding-bottom: 0.625rem;
  font-family: 'Playfair Display', serif;
  letter-spacing: 0.5px;
}

.mt-4 {
  margin-top: 1rem;
}

/* 网格布局 */
.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.lg\:grid-cols-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.lg\:col-span-1 {
  grid-column: span 1 / span 1;
}

.lg\:col-span-2 {
  grid-column: span 2 / span 2;
}

.gap-4 {
  gap: 1rem;
}

.mb-6 {
  margin-bottom: 1.5rem;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 4rem;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(212, 175, 55, 0.2);
  border-left-color: #d4af37;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1.5rem;
}

.loading-spinner.small {
  width: 30px;
  height: 30px;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 1rem;
  color: #999;
}

/* 错误状态 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 4rem;
  text-align: center;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 0.75rem;
}

.error-message {
  font-size: 1rem;
  color: #999;
  margin-bottom: 2rem;
  max-width: 600px;
}

/* 配方头部 */
.recipe-header-section {
  margin-bottom: 2rem;
}

.recipe-header-content {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.recipe-header-info {
  flex: 1;
  min-width: 300px;
}

.recipe-name {
  font-size: 2rem;
  font-weight: 700;
  color: #d4af37;
  margin-bottom: 0.75rem;
  font-family: 'Playfair Display', serif;
  letter-spacing: 1px;
}

.recipe-subtitle {
  font-size: 1rem;
  color: #999;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.recipe-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.recipe-meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.meta-icon {
  font-size: 1.125rem;
}

.meta-label {
  color: #999;
  font-weight: 500;
}

.meta-value {
  color: #e0e0e0;
  font-weight: 600;
}

.recipe-header-image {
  flex-shrink: 0;
  width: 200px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.3);
}

.recipe-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.recipe-header-image:hover .recipe-image {
  transform: scale(1.05);
}

/* 原料结构 */
.ingredient-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.ingredient-item {
  padding: 0.875rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.ingredient-item:hover {
  background: rgba(212, 175, 55, 0.1);
  border-color: rgba(212, 175, 55, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.ingredient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.ingredient-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #e0e0e0;
}

.ingredient-role {
  padding: 0.1875rem 0.625rem;
  border-radius: 10px;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.role-base {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.role-acid {
  background: rgba(255, 152, 0, 0.1);
  color: #ff9800;
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.role-sweetener {
  background: rgba(233, 30, 99, 0.1);
  color: #e91e63;
  border: 1px solid rgba(233, 30, 99, 0.3);
}

.role-bitter {
  background: rgba(156, 39, 176, 0.1);
  color: #9c27b0;
  border: 1px solid rgba(156, 39, 176, 0.3);
}

.role-other {
  background: rgba(103, 58, 183, 0.1);
  color: #673ab7;
  border: 1px solid rgba(103, 58, 183, 0.3);
}

.ingredient-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.ingredient-amount {
  font-size: 0.8125rem;
  color: #999;
  font-weight: 500;
}

.ingredient-category {
  font-size: 0.75rem;
  color: #888;
  font-style: italic;
}

.ingredient-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.625rem;
}

.ingredient-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #888;
}

.ingredient-canonical {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #888;
  font-style: italic;
}

/* SQE分析 */
.combined-card {
  flex: 1;
}

.sqe-overall {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding: 1rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.sqe-score {
  text-align: center;
}

.score-number {
  display: block;
  font-size: 2.25rem;
  font-weight: 700;
  color: #d4af37;
  line-height: 1;
  font-family: 'Playfair Display', serif;
}

.score-label {
  display: block;
  font-size: 0.875rem;
  color: #999;
  margin-top: 0.5rem;
}

.sqe-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.8125rem;
  color: #999;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e0e0e0;
}

/* 三色条形图 */
.sqe-triple-bar {
  margin-bottom: 1.5rem;
}

.triple-bar-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.8125rem;
  color: #999;
}

.triple-label {
  font-weight: 500;
}

.synergy-label {
  color: #4caf50;
}

.conflict-label {
  color: #f44336;
}

.balance-label {
  color: #2196f3;
}

.triple-bar-container {
  display: flex;
  height: 32px;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(212, 175, 55, 0.2);
  width: 100%;
}

.triple-bar-fill {
  flex-shrink: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.8s ease-out;
}

.synergy-fill {
  background: linear-gradient(180deg, #4caf50, #81c784);
}

.conflict-fill {
  background: linear-gradient(180deg, #f44336, #e57373);
}

.balance-fill {
  background: linear-gradient(180deg, #2196f3, #64b5f6);
}

.triple-value {
  font-size: 0.6875rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.triple-bar-legend {
  display: flex;
  justify-content: space-between;
  margin-top: 0.75rem;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #999;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.synergy-color {
  background: linear-gradient(180deg, #4caf50, #81c784);
}

.conflict-color {
  background: linear-gradient(180deg, #f44336, #e57373);
}

.balance-color {
  background: linear-gradient(180deg, #2196f3, #64b5f6);
}

.legend-text {
  font-weight: 500;
}

/* 风味分布 */
.flavor-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.25rem;
}

.radar-chart-container,
.flavor-bars-container {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  padding: 1.25rem;
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.radar-chart {
  position: relative;
  width: 100%;
  height: 100%;
}

.radar-chart-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-chart-circle {
  position: absolute;
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 50%;
}

.radar-chart-circle:nth-child(1) {
  width: 80%;
  height: 80%;
}

.radar-chart-circle:nth-child(2) {
  width: 60%;
  height: 60%;
}

.radar-chart-circle:nth-child(3) {
  width: 40%;
  height: 40%;
}

.radar-chart-line {
  position: absolute;
  width: 100%;
  height: 1px;
  background: rgba(212, 175, 55, 0.3);
  transform-origin: center center;
}

.radar-chart-line:nth-child(4) {
  transform: rotate(0deg);
}

.radar-chart-line:nth-child(5) {
  transform: rotate(60deg);
}

.radar-chart-line:nth-child(6) {
  transform: rotate(120deg);
}

.radar-chart-line:nth-child(7) {
  transform: rotate(180deg);
}

.radar-chart-line:nth-child(8) {
  transform: rotate(240deg);
}

.radar-chart-line:nth-child(9) {
  transform: rotate(300deg);
}

.radar-chart-data {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(212, 175, 55, 0.3);
  transition: clip-path 1s ease-out;
  opacity: 0.8;
}

.radar-chart-labels {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.radar-label {
  position: absolute;
  font-size: 0.875rem;
  color: #999;
  transform: translate(-50%, -50%);
}

.radar-label:nth-child(1) {
  top: 5%;
  left: 50%;
}

.radar-label:nth-child(2) {
  top: 50%;
  left: 95%;
}

.radar-label:nth-child(3) {
  top: 95%;
  left: 75%;
}

.radar-label:nth-child(4) {
  top: 95%;
  left: 25%;
}

.radar-label:nth-child(5) {
  top: 50%;
  left: 5%;
}

.radar-label:nth-child(6) {
  top: 5%;
  left: 50%;
}

.flavor-bars {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.flavor-bar-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.flavor-bar-label {
  flex: 0 0 40px;
  font-size: 0.875rem;
  color: #999;
  text-align: right;
}

.flavor-bar {
  flex: 1;
  height: 6px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.flavor-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #d4af37, #b8860b);
  border-radius: 3px;
  transition: width 1s ease-out;
}

.flavor-bar-value {
  flex: 0 0 40px;
  font-size: 0.875rem;
  color: #999;
  text-align: left;
}

.balance-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(212, 175, 55, 0.2);
}

/* 关键风味识别 */
.key-flavor-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.key-flavor-item {
  padding: 0.875rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.1);
  transition: all 0.3s ease;
}

.key-flavor-item:hover {
  background: rgba(212, 175, 55, 0.1);
  border-color: rgba(212, 175, 55, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.rank-1 {
  border-left: 3px solid #d4af37;
}

.rank-2 {
  border-left: 3px solid #e6c568;
}

.rank-3 {
  border-left: 3px solid #f0d995;
}

.key-flavor-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.flavor-rank {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #d4af37;
  color: #2a2a2a;
  font-size: 0.6875rem;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

.flavor-name {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 600;
  color: #e0e0e0;
}

.flavor-contribution {
  font-size: 0.875rem;
  font-weight: 600;
  color: #d4af37;
}

.contribution-bar {
  width: 100%;
  height: 4px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 2px;
  overflow: hidden;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.contribution-fill {
  height: 100%;
  background: linear-gradient(90deg, #d4af37, #b8860b);
  border-radius: 2px;
  transition: width 1s ease-out;
}

.flavor-metrics {
  display: flex;
  gap: 1.25rem;
  font-size: 0.75rem;
  color: #888;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.metric {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.metric-label {
  font-weight: 500;
  color: #999;
}

.metric-value {
  font-weight: 600;
  color: #d4af37;
}

.flavor-explanation {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(212, 175, 55, 0.1);
  font-size: 0.75rem;
  line-height: 1.4;
  color: #999;
}

.flavor-explanation p {
  margin: 0;
}

/* 局部风味关系图 */
.graph-controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.graph-control-btn {
  padding: 0.5rem 1rem;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.2);
  border-radius: 6px;
  font-size: 0.875rem;
  color: #999;
  cursor: pointer;
  transition: all 0.3s ease;
}

.graph-control-btn:hover {
  background: rgba(212, 175, 55, 0.2);
  border-color: #d4af37;
  color: #e0e0e0;
}

.graph-control-btn.active {
  background: #d4af37;
  border-color: #d4af37;
  color: #2a2a2a;
  font-weight: 500;
}

.graph-container {
  height: 350px;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.graph-placeholder {
  text-align: center;
}

.graph-placeholder-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.3;
}

.graph-placeholder-text {
  font-size: 1.125rem;
  color: #999;
  margin-bottom: 0.5rem;
}

.graph-placeholder-subtext {
  font-size: 0.875rem;
  color: #888;
}

/* 替代建议 */
.substitute-prompt,
.substitute-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem;
  text-align: center;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.prompt-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.3;
}

.prompt-text {
  font-size: 1rem;
  color: #999;
  max-width: 400px;
}

.substitute-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.substitute-item {
  padding: 1.25rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.1);
  transition: all 0.3s ease;
}

.substitute-item:hover {
  background: rgba(212, 175, 55, 0.1);
  border-color: rgba(212, 175, 55, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.substitute-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.625rem;
}

.substitute-name {
  font-size: 1rem;
  font-weight: 600;
  color: #e0e0e0;
}

.substitute-flag {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.substitute-flag.accept {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.substitute-flag.reject {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.substitute-details {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.substitute-roles {
  display: flex;
  gap: 1.25rem;
  font-size: 0.875rem;
  color: #999;
  flex-wrap: wrap;
}

.substitute-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.625rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.substitute-explanation {
  font-size: 0.875rem;
  color: #888;
  line-height: 1.5;
  font-style: italic;
}

/* 操作区 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

/* 按钮 */
.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
}

.btn-primary {
  background: #d4af37;
  color: #2a2a2a;
  border-color: #d4af37;
  font-weight: 600;
}

.btn-primary:hover {
  background: #b8860b;
  border-color: #b8860b;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(212, 175, 55, 0.3);
}

.btn-secondary {
  background: transparent;
  color: #d4af37;
  border-color: #d4af37;
}

.btn-secondary:hover {
  background: #d4af37;
  color: #2a2a2a;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(212, 175, 55, 0.2);
}

.btn-outline {
  background: transparent;
  color: #999;
  border-color: #444;
}

.btn-outline:hover {
  background: #444;
  border-color: #d4af37;
  color: #d4af37;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .lg\:grid-cols-4 {
    grid-template-columns: 1fr;
  }
  
  .lg\:col-span-1,
  .lg\:col-span-2 {
    grid-column: span 1 / span 1;
  }
  
  .flavor-charts {
    grid-template-columns: 1fr;
  }
  
  .radar-chart-container,
  .flavor-bars-container {
    height: 250px;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 0 1rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .card {
    padding: 1.25rem;
  }
  
  .recipe-header-content {
    flex-direction: column;
    text-align: center;
  }
  
  .recipe-header-image {
    width: 100%;
    max-width: 250px;
  }
  
  .recipe-meta {
    justify-content: center;
  }
  
  .sqe-overall {
    flex-direction: column;
    gap: 1.5rem;
    text-align: center;
  }
  
  .sqe-stats {
    justify-content: center;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>