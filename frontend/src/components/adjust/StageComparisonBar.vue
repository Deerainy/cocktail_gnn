<template>
  <div class="stage-comparison-bar card">
    <h3 class="bar-title">三阶段对比流程</h3>
    
    <div class="stages-container">
      <div class="stage-item" :class="{ active: true }">
        <div class="stage-number">1</div>
        <div class="stage-content">
          <div class="stage-name">原始配方</div>
          <div class="stage-score">{{ (overview.original_sqe?.final_sqe_total || 0).toFixed(3) }}</div>
          <div class="stage-label">Baseline</div>
        </div>
      </div>
      
      <div class="stage-connector">
        <div class="connector-line"></div>
        <div class="connector-arrow">→</div>
        <div class="connector-delta" v-if="selectedPlan">
          <span :class="['delta-value', selectedPlan.delta_sqe_single >= 0 ? 'positive' : 'negative']">
            {{ selectedPlan.delta_sqe_single >= 0 ? '+' : '' }}{{ (selectedPlan.delta_sqe_single || 0).toFixed(3) }}
          </span>
        </div>
      </div>
      
      <div class="stage-item" :class="{ active: selectedPlan }">
        <div class="stage-number">2</div>
        <div class="stage-content">
          <div class="stage-name">单步替代</div>
          <div class="stage-score">{{ (selectedPlan?.single_sqe_total || overview.best_plan_summary?.single_sqe_total || 0).toFixed(3) }}</div>
          <div class="stage-label">Single Replace</div>
        </div>
      </div>
      
      <div class="stage-connector">
        <div class="connector-line"></div>
        <div class="connector-arrow">→</div>
        <div class="connector-delta" v-if="selectedPlan">
          <span :class="['delta-value', selectedPlan.delta_sqe_combo >= 0 ? 'positive' : 'negative']">
            {{ selectedPlan.delta_sqe_combo >= 0 ? '+' : '' }}{{ (selectedPlan.delta_sqe_combo || 0).toFixed(3) }}
          </span>
        </div>
      </div>
      
      <div class="stage-item highlight" :class="{ active: selectedPlan }">
        <div class="stage-number">3</div>
        <div class="stage-content">
          <div class="stage-name">组合调整</div>
          <div class="stage-score">{{ (selectedPlan?.combo_sqe_total || overview.best_plan_summary?.combo_sqe_total || 0).toFixed(3) }}</div>
          <div class="stage-label">Combo Adjust</div>
        </div>
      </div>
    </div>
    
    <div class="stage-explanation" v-if="selectedPlan">
      <div class="explanation-item">
        <span class="explanation-label">协同变化:</span>
        <span :class="['explanation-value', selectedPlan.delta_synergy_combo >= 0 ? 'positive' : 'negative']">
          {{ selectedPlan.delta_synergy_combo >= 0 ? '+' : '' }}{{ (selectedPlan.delta_synergy_combo || 0).toFixed(3) }}
        </span>
      </div>
      <div class="explanation-item">
        <span class="explanation-label">冲突变化:</span>
        <span :class="['explanation-value', selectedPlan.delta_conflict_combo <= 0 ? 'positive' : 'negative']">
          {{ selectedPlan.delta_conflict_combo >= 0 ? '+' : '' }}{{ (selectedPlan.delta_conflict_combo || 0).toFixed(3) }}
        </span>
      </div>
      <div class="explanation-item">
        <span class="explanation-label">平衡变化:</span>
        <span :class="['explanation-value', selectedPlan.delta_balance_combo >= 0 ? 'positive' : 'negative']">
          {{ selectedPlan.delta_balance_combo >= 0 ? '+' : '' }}{{ (selectedPlan.delta_balance_combo || 0).toFixed(3) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StageComparisonBar',
  
  props: {
    overview: {
      type: Object,
      required: true
    },
    selectedPlan: {
      type: Object,
      default: null
    }
  }
}
</script>

<style scoped>
.stage-comparison-bar {
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.bar-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
  text-align: center;
}

.stages-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.stage-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-2);
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  min-width: 180px;
  transition: all 0.3s ease;
}

.stage-item.active {
  border-color: var(--color-gold-400);
}

.stage-item.highlight {
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-600));
  border-color: var(--color-gold-600);
  color: var(--color-bg-1);
}

.stage-number {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-3);
  border-radius: 50%;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.stage-item.highlight .stage-number {
  background: rgba(255, 255, 255, 0.3);
  color: var(--color-bg-1);
}

.stage-content {
  flex: 1;
}

.stage-name {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: var(--spacing-xs);
}

.stage-score {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: var(--spacing-xs);
}

.stage-label {
  font-size: 0.75rem;
  opacity: 0.7;
  text-transform: uppercase;
}

.stage-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.connector-line {
  width: 40px;
  height: 2px;
  background: var(--color-border);
}

.connector-arrow {
  font-size: 1.2rem;
  color: var(--color-text-secondary);
}

.connector-delta {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--border-radius-sm);
  font-size: 0.85rem;
}

.delta-value {
  font-weight: 600;
}

.delta-value.positive {
  color: var(--color-success);
}

.delta-value.negative {
  color: var(--color-error);
}

.stage-explanation {
  display: flex;
  justify-content: center;
  gap: var(--spacing-xl);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.explanation-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.explanation-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.explanation-value {
  font-size: 1rem;
  font-weight: 600;
}

.explanation-value.positive {
  color: var(--color-success);
}

.explanation-value.negative {
  color: var(--color-error);
}

@media (max-width: 768px) {
  .stages-container {
    flex-direction: column;
  }
  
  .stage-connector {
    flex-direction: row;
    transform: rotate(90deg);
  }
  
  .stage-explanation {
    flex-direction: column;
    align-items: center;
  }
}
</style>
