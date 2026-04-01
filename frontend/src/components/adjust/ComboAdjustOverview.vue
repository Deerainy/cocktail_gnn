<template>
  <div class="combo-adjust-overview card">
    <div class="overview-header">
      <h2 class="overview-title">配方概览</h2>
      <div class="recipe-name">
        <span v-if="overview.recipe?.recipe_name_zh" class="name-zh">{{ overview.recipe.recipe_name_zh }}</span>
        <span v-if="overview.recipe?.recipe_name_zh && overview.recipe?.name" class="name-separator"> / </span>
        <span v-if="overview.recipe?.name" class="name-en">{{ overview.recipe.name }}</span>
      </div>
    </div>
    
    <div class="overview-content">
      <div class="info-section">
        <h3 class="section-title">原始原料</h3>
        <div class="ingredients-summary">
          <div 
            v-for="(ingredient, index) in overview.original_ingredients?.slice(0, 5)" 
            :key="ingredient.ingredient_id || index"
            class="ingredient-chip"
          >
            <span v-if="ingredient.ingredient?.canonical_name_zh">{{ ingredient.ingredient.canonical_name_zh }}</span>
            <span v-else-if="ingredient.ingredient?.canonical_name">{{ ingredient.ingredient.canonical_name }}</span>
            <span v-else>{{ ingredient.raw_text }}</span>
          </div>
          <div v-if="overview.original_ingredients?.length > 5" class="ingredient-chip more">
            +{{ overview.original_ingredients.length - 5 }} 更多
          </div>
        </div>
      </div>
      
      <div class="info-section">
        <h3 class="section-title">目标替代原料</h3>
        <div class="target-info">
          <div class="target-item" v-if="overview.best_plan_summary">
            <span class="target-label">目标:</span>
            <span class="target-value">{{ overview.best_plan_summary.target_canonical }}</span>
          </div>
          <div class="target-item" v-if="overview.best_plan_summary">
            <span class="target-label">候选:</span>
            <span class="target-value">{{ overview.best_plan_summary.candidate_canonical }}</span>
          </div>
        </div>
      </div>
      
      <div class="sqe-section">
        <h3 class="section-title">SQE评分对比</h3>
        <div class="sqe-comparison">
          <div class="sqe-item">
            <div class="sqe-label">原始配方</div>
            <div class="sqe-value">{{ (overview.original_sqe?.final_sqe_total || 0).toFixed(3) }}</div>
          </div>
          <div class="sqe-arrow">→</div>
          <div class="sqe-item" v-if="overview.best_plan_summary">
            <div class="sqe-label">单步替代</div>
            <div class="sqe-value">{{ (overview.best_plan_summary.single_sqe_total || 0).toFixed(3) }}</div>
          </div>
          <div class="sqe-arrow">→</div>
          <div class="sqe-item highlight" v-if="overview.best_plan_summary">
            <div class="sqe-label">组合调整</div>
            <div class="sqe-value">{{ (overview.best_plan_summary.combo_sqe_total || 0).toFixed(3) }}</div>
          </div>
        </div>
      </div>
      
      <div class="stats-section">
        <div class="stat-item">
          <span class="stat-label">总方案数</span>
          <span class="stat-value">{{ overview.total_plans || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已接受</span>
          <span class="stat-value accepted">{{ overview.accepted_plans || 0 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ComboAdjustOverview',
  
  props: {
    overview: {
      type: Object,
      required: true
    }
  }
}
</script>

<style scoped>
.combo-adjust-overview {
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 2px solid var(--color-border);
}

.overview-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-200);
  font-family: var(--font-serif);
}

.recipe-name {
  font-size: 1.2rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.name-zh {
  color: var(--color-text-primary);
}

.name-separator {
  color: var(--color-text-secondary);
  margin: 0 var(--spacing-xs);
}

.name-en {
  color: var(--color-text-secondary);
  font-style: italic;
}

.overview-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-xl);
}

.info-section,
.sqe-section,
.stats-section {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.ingredients-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.ingredient-chip {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-3);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  font-size: 0.9rem;
  color: var(--color-text-primary);
}

.ingredient-chip.more {
  background: var(--color-gold-400);
  color: var(--color-bg-1);
  font-weight: 500;
}

.target-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.target-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.target-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  min-width: 60px;
}

.target-value {
  font-size: 1rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.sqe-comparison {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.sqe-item {
  flex: 1;
  text-align: center;
  padding: var(--spacing-md);
  background: var(--color-bg-3);
  border-radius: var(--border-radius);
}

.sqe-item.highlight {
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-600));
  color: var(--color-bg-1);
}

.sqe-label {
  font-size: 0.85rem;
  margin-bottom: var(--spacing-xs);
  opacity: 0.8;
}

.sqe-value {
  font-size: 1.3rem;
  font-weight: 700;
}

.sqe-arrow {
  font-size: 1.5rem;
  color: var(--color-text-secondary);
}

.stats-section {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.stat-value.accepted {
  color: var(--color-success);
}
</style>
