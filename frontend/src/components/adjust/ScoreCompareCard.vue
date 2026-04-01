<template>
  <div class="score-compare-card card">
    <h3 class="card-title">分数对比</h3>
    
    <div class="compare-section">
      <h4 class="section-title">总分变化</h4>
      <div class="total-score-comparison">
        <div class="score-box">
          <div class="score-label">原始 SQE</div>
          <div class="score-value">{{ (plan.old_sqe_total || 0).toFixed(3) }}</div>
        </div>
        
        <div class="score-arrow">
          <span class="arrow-icon">→</span>
          <span :class="['delta-badge', plan.delta_sqe_single >= 0 ? 'positive' : 'negative']">
            {{ plan.delta_sqe_single >= 0 ? '+' : '' }}{{ (plan.delta_sqe_single || 0).toFixed(3) }}
          </span>
        </div>
        
        <div class="score-box">
          <div class="score-label">单步替代</div>
          <div class="score-value">{{ (plan.single_sqe_total || 0).toFixed(3) }}</div>
        </div>
        
        <div class="score-arrow">
          <span class="arrow-icon">→</span>
          <span :class="['delta-badge', plan.delta_sqe_combo >= 0 ? 'positive' : 'negative']">
            {{ plan.delta_sqe_combo >= 0 ? '+' : '' }}{{ (plan.delta_sqe_combo || 0).toFixed(3) }}
          </span>
        </div>
        
        <div class="score-box highlight">
          <div class="score-label">组合调整</div>
          <div class="score-value">{{ (plan.combo_sqe_total || 0).toFixed(3) }}</div>
        </div>
      </div>
    </div>
    
    <div class="compare-section">
      <h4 class="section-title">结构项变化</h4>
      <div class="structure-changes">
        <div class="change-item">
          <div class="change-header">
            <span class="change-label">协同性 (Synergy)</span>
            <span :class="['change-value', plan.delta_synergy_combo >= 0 ? 'positive' : 'negative']">
              {{ plan.delta_synergy_combo >= 0 ? '+' : '' }}{{ (plan.delta_synergy_combo || 0).toFixed(3) }}
            </span>
          </div>
          <div class="change-bar-container">
            <div class="change-bar-bg"></div>
            <div 
              class="change-bar-fill positive" 
              v-if="plan.delta_synergy_combo >= 0"
              :style="{ width: getBarWidth(plan.delta_synergy_combo) + '%' }"
            ></div>
            <div 
              class="change-bar-fill negative" 
              v-else
              :style="{ width: getBarWidth(plan.delta_synergy_combo) + '%', left: 'auto', right: '50%' }"
            ></div>
          </div>
        </div>
        
        <div class="change-item">
          <div class="change-header">
            <span class="change-label">冲突度 (Conflict)</span>
            <span :class="['change-value', plan.delta_conflict_combo <= 0 ? 'positive' : 'negative']">
              {{ plan.delta_conflict_combo >= 0 ? '+' : '' }}{{ (plan.delta_conflict_combo || 0).toFixed(3) }}
            </span>
          </div>
          <div class="change-bar-container">
            <div class="change-bar-bg"></div>
            <div 
              class="change-bar-fill positive" 
              v-if="plan.delta_conflict_combo <= 0"
              :style="{ width: getBarWidth(plan.delta_conflict_combo) + '%' }"
            ></div>
            <div 
              class="change-bar-fill negative" 
              v-else
              :style="{ width: getBarWidth(plan.delta_conflict_combo) + '%', left: 'auto', right: '50%' }"
            ></div>
          </div>
        </div>
        
        <div class="change-item">
          <div class="change-header">
            <span class="change-label">平衡性 (Balance)</span>
            <span :class="['change-value', plan.delta_balance_combo >= 0 ? 'positive' : 'negative']">
              {{ plan.delta_balance_combo >= 0 ? '+' : '' }}{{ (plan.delta_balance_combo || 0).toFixed(3) }}
            </span>
          </div>
          <div class="change-bar-container">
            <div class="change-bar-bg"></div>
            <div 
              class="change-bar-fill positive" 
              v-if="plan.delta_balance_combo >= 0"
              :style="{ width: getBarWidth(plan.delta_balance_combo) + '%' }"
            ></div>
            <div 
              class="change-bar-fill negative" 
              v-else
              :style="{ width: getBarWidth(plan.delta_balance_combo) + '%', left: 'auto', right: '50%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="trend-summary">
      <div class="trend-item" v-if="plan.delta_sqe_combo > 0">
        <span class="trend-icon">📈</span>
        <span class="trend-text">SQE 提升</span>
      </div>
      <div class="trend-item" v-if="plan.delta_synergy_combo > 0">
        <span class="trend-icon">🤝</span>
        <span class="trend-text">协同增强</span>
      </div>
      <div class="trend-item" v-if="plan.delta_conflict_combo < 0">
        <span class="trend-icon">✨</span>
        <span class="trend-text">冲突缓解</span>
      </div>
      <div class="trend-item" v-if="plan.delta_balance_combo > 0">
        <span class="trend-icon">⚖️</span>
        <span class="trend-text">平衡改善</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScoreCompareCard',
  
  props: {
    plan: {
      type: Object,
      required: true
    },
    overview: {
      type: Object,
      required: true
    }
  },
  
  methods: {
    getBarWidth(value) {
      const absValue = Math.abs(value || 0)
      return Math.min(100, absValue * 500)
    }
  }
}
</script>

<style scoped>
.score-compare-card {
  padding: var(--spacing-lg);
}

.card-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.compare-section {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.total-score-comparison {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.score-box {
  flex: 1;
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
  text-align: center;
}

.score-box.highlight {
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-600));
  color: var(--color-bg-1);
}

.score-label {
  font-size: 0.85rem;
  margin-bottom: var(--spacing-xs);
  opacity: 0.8;
}

.score-value {
  font-size: 1.5rem;
  font-weight: 700;
}

.score-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.arrow-icon {
  font-size: 1.5rem;
  color: var(--color-text-secondary);
}

.delta-badge {
  padding: 2px var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
}

.delta-badge.positive {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success);
}

.delta-badge.negative {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-error);
}

.structure-changes {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.change-item {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
}

.change-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.change-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.change-value {
  font-size: 1rem;
  font-weight: 600;
}

.change-value.positive {
  color: var(--color-success);
}

.change-value.negative {
  color: var(--color-error);
}

.change-bar-container {
  position: relative;
  height: 8px;
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
  overflow: hidden;
}

.change-bar-bg {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--color-text-secondary);
}

.change-bar-fill {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  height: 100%;
  border-radius: var(--border-radius-sm);
  transition: width 0.3s ease;
}

.change-bar-fill.positive {
  background: var(--color-success);
}

.change-bar-fill.negative {
  background: var(--color-error);
}

.trend-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.trend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius-sm);
}

.trend-icon {
  font-size: 1rem;
}

.trend-text {
  font-size: 0.9rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

@media (max-width: 768px) {
  .total-score-comparison {
    flex-direction: column;
  }
  
  .score-arrow {
    flex-direction: row;
  }
}
</style>
