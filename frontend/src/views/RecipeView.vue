<template>
  <div class="recipe">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="container">
        <div class="page-header-content">
          <h1 class="page-title">配方列表</h1>
          <p class="page-subtitle">探索所有可用的配方</p>
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
      <div class="recipe-grid">
        <div 
          v-for="recipe in recipes" 
          :key="recipe.recipe_id"
          class="recipe-card card"
          @click="navigateToDetails(recipe.recipe_id)"
        >
          <div class="recipe-card-header">
            <h3 class="recipe-card-name">{{ recipe.name }}</h3>
            <div class="recipe-card-meta">
              <span class="recipe-card-category">{{ recipe.source || '未知来源' }}</span>
              <span class="recipe-card-origin">{{ recipe.is_alcoholic ? '含酒精' : '无酒精' }}</span>
            </div>
          </div>
          <div class="recipe-card-ingredients">
            <div class="recipe-card-ingredient-list">
              <div class="recipe-card-ingredient-item">
                <span class="recipe-card-ingredient-name">玻璃类型</span>
                <span class="recipe-card-ingredient-amount">{{ recipe.glass || '未指定' }}</span>
              </div>
              <div class="recipe-card-ingredient-item">
                <span class="recipe-card-ingredient-name">标签</span>
                <span class="recipe-card-ingredient-amount">{{ recipe.tags || '无' }}</span>
              </div>
            </div>
          </div>
          <div class="recipe-card-actions">
            <button class="btn btn-sm btn-outline" @click.stop="navigateToDetails(recipe.recipe_id)">
              查看详情
            </button>
          </div>
        </div>
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
      error: null
    };
  },
  mounted() {
    this.fetchRecipes();
  },
  methods: {
    async fetchRecipes() {
      this.loading = true;
      try {
        this.recipes = await fetchAllRecipes();
      } catch (error) {
        this.error = '获取配方列表失败';
        console.error('Error fetching recipes:', error);
      } finally {
        this.loading = false;
      }
    },
    navigateToDetails(recipeId) {
      this.$router.push({ path: '/visualization', query: { recipe_id: recipeId } });
    }
  }
};
</script>

<style scoped>
.recipe {
  width: 100%;
  padding: var(--spacing-3xl) 0;
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
}
</style>