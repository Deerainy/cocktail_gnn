<template>
  <div class="combo-step-timeline card">
    <h3 class="timeline-title">操作步骤序列</h3>
    
    <div class="timeline-container">
      <div 
        v-for="(step, index) in steps" 
        :key="step.step_id || index"
        class="timeline-item"
      >
        <div class="timeline-marker">
          <div class="marker-circle">{{ step.step_no || index + 1 }}</div>
          <div class="marker-line" v-if="index < steps.length - 1"></div>
        </div>
        
        <div class="timeline-content">
          <div class="step-header">
            <div class="step-type-badge" :class="getStepTypeClass(step.op_type)">
              {{ getStepTypeLabel(step.op_type) }}
            </div>
            <div class="step-sqe-change">
              <span class="sqe-label">SQE变化:</span>
              <span :class="['sqe-value', step.delta_sqe >= 0 ? 'positive' : 'negative']">
                {{ step.delta_sqe >= 0 ? '+' : '' }}{{ (step.delta_sqe || 0).toFixed(3) }}
              </span>
            </div>
          </div>
          
          <div class="step-body">
            <div class="step-description">
              <p class="step-text">{{ step.step_text || getStepDescription(step) }}</p>
            </div>
            
            <div class="step-details">
              <div class="detail-item" v-if="step.target_ingredient">
                <span class="detail-label">目标原料:</span>
                <span class="detail-value">{{ step.target_ingredient }}</span>
              </div>
              <div class="detail-item" v-if="step.candidate_ingredient">
                <span class="detail-label">候选原料:</span>
                <span class="detail-value">{{ step.candidate_ingredient }}</span>
              </div>
              <div class="detail-item" v-if="step.role_info">
                <span class="detail-label">角色:</span>
                <span class="detail-value">{{ step.role_info }}</span>
              </div>
              <div class="detail-item" v-if="step.amount_factor">
                <span class="detail-label">比例因子:</span>
                <span class="detail-value">{{ step.amount_factor.toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="step-sqes">
              <div class="sqe-item">
                <span class="sqe-label">调整前</span>
                <span class="sqe-value">{{ (step.before_sqe_total || 0).toFixed(3) }}</span>
              </div>
              <div class="sqe-arrow">→</div>
              <div class="sqe-item">
                <span class="sqe-label">调整后</span>
                <span class="sqe-value">{{ (step.after_sqe_total || 0).toFixed(3) }}</span>
              </div>
            </div>
            
            <div class="step-note" v-if="step.note">
              <span class="note-icon">💡</span>
              <span class="note-text">{{ step.note }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="steps.length === 0" class="no-steps">
        <div class="no-steps-icon">📝</div>
        <p class="no-steps-text">暂无操作步骤</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ComboStepTimeline',
  
  props: {
    steps: {
      type: Array,
      default: () => []
    }
  },
  
  methods: {
    getStepTypeClass(opType) {
      const typeMap = {
        'replace': 'replace',
        'add': 'add',
        'remove': 'remove',
        'adjust': 'adjust'
      }
      return typeMap[opType] || 'default'
    },
    
    getStepTypeLabel(opType) {
      const labelMap = {
        'replace': '替换',
        'add': '添加',
        'remove': '移除',
        'adjust': '调整'
      }
      return labelMap[opType] || opType
    },
    
    getStepDescription(step) {
      if (step.op_type === 'replace') {
        return `将 ${step.target_ingredient || '原料'} 替换为 ${step.candidate_ingredient || '新原料'}`
      } else if (step.op_type === 'add') {
        return `添加 ${step.candidate_ingredient || '新原料'}`
      } else if (step.op_type === 'remove') {
        return `移除 ${step.target_ingredient || '原料'}`
      } else if (step.op_type === 'adjust') {
        return `调整 ${step.target_ingredient || '原料'} 的比例`
      }
      return '执行操作'
    }
  }
}
</script>

<style scoped>
.combo-step-timeline {
  padding: var(--spacing-xl);
}

.timeline-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xl);
}

.timeline-container {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  gap: var(--spacing-lg);
  position: relative;
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.marker-circle {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-600));
  color: var(--color-bg-1);
  border-radius: 50%;
  font-size: 1.1rem;
  font-weight: 700;
  z-index: 1;
}

.marker-line {
  width: 3px;
  flex: 1;
  background: linear-gradient(180deg, var(--color-gold-400), var(--color-border));
  margin: var(--spacing-sm) 0;
}

.timeline-content {
  flex: 1;
  padding-bottom: var(--spacing-xl);
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.step-type-badge {
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: 0.9rem;
  font-weight: 600;
}

.step-type-badge.replace {
  background: rgba(33, 150, 243, 0.2);
  color: #2196F3;
}

.step-type-badge.add {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success);
}

.step-type-badge.remove {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-error);
}

.step-type-badge.adjust {
  background: rgba(255, 152, 0, 0.2);
  color: #FF9800;
}

.step-type-badge.default {
  background: var(--color-bg-2);
  color: var(--color-text-primary);
}

.step-sqe-change {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.sqe-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.sqe-value {
  font-size: 1rem;
  font-weight: 600;
}

.sqe-value.positive {
  color: var(--color-success);
}

.sqe-value.negative {
  color: var(--color-error);
}

.step-body {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--color-gold-400);
}

.step-description {
  margin-bottom: var(--spacing-md);
}

.step-text {
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.step-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-sm);
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.detail-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.detail-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.step-sqes {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm);
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
  margin-bottom: var(--spacing-md);
}

.sqe-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.sqe-arrow {
  font-size: 1.2rem;
  color: var(--color-text-secondary);
}

.step-note {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: rgba(255, 193, 7, 0.1);
  border-radius: var(--border-radius-sm);
  border-left: 3px solid #FFC107;
}

.note-icon {
  font-size: 1rem;
}

.note-text {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.no-steps {
  text-align: center;
  padding: var(--spacing-2xl);
}

.no-steps-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
}

.no-steps-text {
  color: var(--color-text-secondary);
}
</style>
