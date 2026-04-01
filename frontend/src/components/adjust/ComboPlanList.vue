<template>
  <div class="combo-plan-list card">
    <div class="list-header">
      <h3 class="list-title">组合调整方案</h3>
      <div class="list-filters">
        <select 
          v-model="localFilters.accept_flag" 
          @change="handleFilterChange"
          class="filter-select"
        >
          <option :value="null">全部方案</option>
          <option :value="true">已接受</option>
          <option :value="false">已拒绝</option>
        </select>
      </div>
    </div>
    
    <div class="plan-count">
      共 {{ plans.length }} 个方案
    </div>
    
    <div class="plans-container">
      <div 
        v-for="plan in plans" 
        :key="plan.plan_id"
        :class="['plan-card', { 
          selected: selectedPlanId === plan.plan_id,
          accepted: plan.accept_flag 
        }]"
        @click="$emit('select', plan.plan_id)"
      >
        <div class="plan-header">
          <div class="plan-rank">
            <span class="rank-label">Rank</span>
            <span class="rank-number">{{ plan.rank_no }}</span>
          </div>
          <span :class="['plan-status', plan.accept_flag ? 'accept' : 'reject']">
            {{ plan.accept_flag ? '已接受' : '已拒绝' }}
          </span>
        </div>
        
        <div class="plan-title">
          {{ plan.summary_text || `${plan.target_canonical} → ${plan.candidate_canonical}` }}
        </div>
        
        <div class="plan-type">
          <span class="type-label">类型:</span>
          <span class="type-value">{{ plan.plan_type || '单步替代' }}</span>
        </div>
        
        <div class="plan-scores">
          <div class="score-item">
            <span class="score-label">SQE</span>
            <span class="score-value">{{ (plan.combo_sqe_total || 0).toFixed(3) }}</span>
          </div>
          <div class="score-item">
            <span class="score-label">ΔSQE</span>
            <span :class="['score-value', plan.delta_sqe_combo >= 0 ? 'positive' : 'negative']">
              {{ plan.delta_sqe_combo >= 0 ? '+' : '' }}{{ (plan.delta_sqe_combo || 0).toFixed(3) }}
            </span>
          </div>
        </div>
        
        <div class="plan-metrics">
          <div class="metric-item">
            <span class="metric-label">协同</span>
            <span :class="['metric-value', plan.delta_synergy_combo >= 0 ? 'positive' : 'negative']">
              {{ plan.delta_synergy_combo >= 0 ? '+' : '' }}{{ (plan.delta_synergy_combo || 0).toFixed(3) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="metric-label">冲突</span>
            <span :class="['metric-value', plan.delta_conflict_combo <= 0 ? 'positive' : 'negative']">
              {{ plan.delta_conflict_combo >= 0 ? '+' : '' }}{{ (plan.delta_conflict_combo || 0).toFixed(3) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="metric-label">平衡</span>
            <span :class="['metric-value', plan.delta_balance_combo >= 0 ? 'positive' : 'negative']">
              {{ plan.delta_balance_combo >= 0 ? '+' : '' }}{{ (plan.delta_balance_combo || 0).toFixed(3) }}
            </span>
          </div>
        </div>
        
        <div class="plan-tags" v-if="plan.trend_tags && plan.trend_tags.length > 0">
          <span 
            v-for="tag in plan.trend_tags" 
            :key="tag" 
            class="tag"
          >
            {{ tag }}
          </span>
        </div>
      </div>
      
      <div v-if="plans.length === 0" class="no-plans">
        <div class="no-plans-icon">📋</div>
        <p class="no-plans-text">暂无组合调整方案</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ComboPlanList',
  
  props: {
    plans: {
      type: Array,
      default: () => []
    },
    selectedPlanId: {
      type: Number,
      default: null
    },
    filters: {
      type: Object,
      default: () => ({})
    }
  },
  
  data() {
    return {
      localFilters: {
        accept_flag: null
      }
    }
  },
  
  watch: {
    filters: {
      handler(newFilters) {
        this.localFilters = { ...this.localFilters, ...newFilters }
      },
      immediate: true,
      deep: true
    }
  },
  
  methods: {
    handleFilterChange() {
      this.$emit('filter-change', this.localFilters)
    }
  }
}
</script>

<style scoped>
.combo-plan-list {
  padding: var(--spacing-lg);
  height: fit-content;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.list-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.filter-select {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-sm);
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.plan-count {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.plans-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  max-height: 600px;
  overflow-y: auto;
}

.plan-card {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s ease;
}

.plan-card:hover {
  border-color: var(--color-gold-400);
  transform: translateY(-2px);
}

.plan-card.selected {
  border-color: var(--color-gold-400);
  background: var(--color-bg-3);
}

.plan-card.accepted {
  border-left: 4px solid var(--color-success);
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.plan-rank {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.rank-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.rank-number {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-gold-400);
}

.plan-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
}

.plan-status.accept {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success);
}

.plan-status.reject {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-error);
}

.plan-title {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  line-height: 1.4;
}

.plan-type {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
  font-size: 0.85rem;
}

.type-label {
  color: var(--color-text-secondary);
}

.type-value {
  color: var(--color-text-primary);
  font-weight: 500;
}

.plan-scores {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.score-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.score-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.score-value.positive {
  color: var(--color-success);
}

.score-value.negative {
  color: var(--color-error);
}

.plan-metrics {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.metric-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.metric-value {
  font-size: 0.9rem;
  font-weight: 600;
}

.metric-value.positive {
  color: var(--color-success);
}

.metric-value.negative {
  color: var(--color-error);
}

.plan-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
}

.tag {
  padding: 2px var(--spacing-sm);
  background: var(--color-gold-400);
  color: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.no-plans {
  text-align: center;
  padding: var(--spacing-2xl);
}

.no-plans-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
}

.no-plans-text {
  color: var(--color-text-secondary);
}
</style>
