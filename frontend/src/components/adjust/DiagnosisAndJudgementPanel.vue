<template>
  <div class="diagnosis-judgement-panel card">
    <h3 class="panel-title">诊断与判定</h3>
    
    <div class="panel-content">
      <div class="diagnosis-section">
        <h4 class="section-title">
          <span class="title-icon">🔍</span>
          单替代偏移诊断
        </h4>
        <div class="diagnosis-content">
          <div class="diagnosis-item" v-if="plan.delta_sqe_single < 0">
            <div class="diagnosis-indicator negative"></div>
            <div class="diagnosis-text">
              <strong>SQE 下降</strong>
              <p>单步替代后 SQE 下降了 {{ Math.abs(plan.delta_sqe_single || 0).toFixed(3) }}，需要组合调整来恢复</p>
            </div>
          </div>
          
          <div class="diagnosis-item" v-if="plan.delta_synergy_combo > 0">
            <div class="diagnosis-indicator positive"></div>
            <div class="diagnosis-text">
              <strong>协同性提升</strong>
              <p>组合调整后协同项上升了 {{ (plan.delta_synergy_combo || 0).toFixed(3) }}</p>
            </div>
          </div>
          
          <div class="diagnosis-item" v-if="plan.delta_conflict_combo < 0">
            <div class="diagnosis-indicator positive"></div>
            <div class="diagnosis-text">
              <strong>冲突度降低</strong>
              <p>组合调整后冲突项下降了 {{ Math.abs(plan.delta_conflict_combo || 0).toFixed(3) }}</p>
            </div>
          </div>
          
          <div class="diagnosis-item" v-if="plan.delta_balance_combo > 0">
            <div class="diagnosis-indicator positive"></div>
            <div class="diagnosis-text">
              <strong>平衡性改善</strong>
              <p>组合调整后平衡项提升了 {{ (plan.delta_balance_combo || 0).toFixed(3) }}</p>
            </div>
          </div>
          
          <div class="diagnosis-item" v-if="plan.repair_canonical">
            <div class="diagnosis-indicator info"></div>
            <div class="diagnosis-text">
              <strong>修复原料引入</strong>
              <p>引入 {{ plan.repair_canonical }} 作为修复原料，角色为 {{ plan.repair_role || 'N/A' }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="judgement-section">
        <h4 class="section-title">
          <span class="title-icon">⚖️</span>
          接受判定
        </h4>
        <div class="judgement-content">
          <div class="judgement-header">
            <div :class="['judgement-status', plan.accept_flag ? 'accept' : 'reject']">
              <span class="status-icon">{{ plan.accept_flag ? '✓' : '✗' }}</span>
              <span class="status-text">{{ plan.accept_flag ? '已接受' : '已拒绝' }}</span>
            </div>
            <div class="judgement-reason" v-if="plan.acceptance_info">
              <span class="reason-label">{{ plan.acceptance_info.reason_label }}</span>
            </div>
          </div>
          
          <div class="judgement-explanation" v-if="plan.acceptance_info">
            <p class="explanation-text">{{ plan.acceptance_info.reason_text }}</p>
          </div>
          
          <div class="judgement-explanation" v-else-if="plan.explanation">
            <p class="explanation-text">{{ plan.explanation }}</p>
          </div>
          
          <div class="judgement-criteria">
            <h5 class="criteria-title">判定依据</h5>
            <div class="criteria-list">
              <div class="criteria-item" :class="{ met: plan.delta_sqe_combo > 0 }">
                <span class="criteria-icon">{{ plan.delta_sqe_combo > 0 ? '✓' : '✗' }}</span>
                <span class="criteria-text">SQE 提升</span>
              </div>
              <div class="criteria-item" :class="{ met: plan.delta_synergy_combo > 0 }">
                <span class="criteria-icon">{{ plan.delta_synergy_combo > 0 ? '✓' : '✗' }}</span>
                <span class="criteria-text">协同增强</span>
              </div>
              <div class="criteria-item" :class="{ met: plan.delta_conflict_combo < 0 }">
                <span class="criteria-icon">{{ plan.delta_conflict_combo < 0 ? '✓' : '✗' }}</span>
                <span class="criteria-text">冲突缓解</span>
              </div>
              <div class="criteria-item" :class="{ met: plan.delta_balance_combo > 0 }">
                <span class="criteria-icon">{{ plan.delta_balance_combo > 0 ? '✓' : '✗' }}</span>
                <span class="criteria-text">平衡改善</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="summary-section" v-if="plan.judgement && plan.judgement.diagnosis">
        <h4 class="section-title">
          <span class="title-icon">📋</span>
          诊断摘要
        </h4>
        <div class="summary-list">
          <div 
            v-for="(item, index) in plan.judgement.diagnosis" 
            :key="index"
            class="summary-item"
          >
            <span class="summary-bullet">•</span>
            <span class="summary-text">{{ item }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DiagnosisAndJudgementPanel',
  
  props: {
    plan: {
      type: Object,
      required: true
    }
  }
}
</script>

<style scoped>
.diagnosis-judgement-panel {
  padding: var(--spacing-lg);
}

.panel-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.title-icon {
  font-size: 1.2rem;
}

.diagnosis-section,
.judgement-section,
.summary-section {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
}

.diagnosis-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.diagnosis-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
  border-left: 3px solid transparent;
}

.diagnosis-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}

.diagnosis-indicator.positive {
  background: var(--color-success);
}

.diagnosis-indicator.negative {
  background: var(--color-error);
}

.diagnosis-indicator.info {
  background: var(--color-gold-400);
}

.diagnosis-text {
  flex: 1;
}

.diagnosis-text strong {
  display: block;
  font-size: 0.95rem;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.diagnosis-text p {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
  margin: 0;
}

.judgement-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.judgement-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.judgement-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
}

.judgement-status.accept {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success);
}

.judgement-status.reject {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-error);
}

.status-icon {
  font-size: 1.2rem;
  font-weight: 700;
}

.status-text {
  font-size: 1rem;
  font-weight: 600;
}

.judgement-reason {
  padding: var(--spacing-xs) var(--spacing-md);
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
}

.reason-label {
  font-size: 0.9rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.judgement-explanation {
  padding: var(--spacing-md);
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
}

.explanation-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--color-text-primary);
  margin: 0;
}

.judgement-criteria {
  padding: var(--spacing-md);
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
}

.criteria-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
}

.criteria-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.criteria-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--border-radius-sm);
}

.criteria-item.met {
  background: rgba(76, 175, 80, 0.1);
}

.criteria-icon {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-secondary);
}

.criteria-item.met .criteria-icon {
  color: var(--color-success);
}

.criteria-text {
  font-size: 0.85rem;
  color: var(--color-text-primary);
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.summary-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
}

.summary-bullet {
  color: var(--color-gold-400);
  font-size: 1.2rem;
  line-height: 1.4;
}

.summary-text {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}
</style>
