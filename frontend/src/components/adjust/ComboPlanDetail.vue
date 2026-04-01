<template>
  <div class="combo-plan-detail card">
    <div class="detail-header">
      <h3 class="detail-title">方案详情</h3>
      <span :class="['detail-status', plan.accept_flag ? 'accept' : 'reject']">
        {{ plan.accept_flag ? '✓ 已接受' : '✗ 已拒绝' }}
      </span>
    </div>
    
    <div class="detail-content">
      <div class="detail-section">
        <h4 class="section-title">方案信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">方案ID</span>
            <span class="info-value">{{ plan.plan_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">排名</span>
            <span class="info-value rank">{{ plan.rank_no }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">方案类型</span>
            <span class="info-value">{{ plan.plan_type || '单步替代' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">原因代码</span>
            <span class="info-value code">{{ plan.reason_code || 'N/A' }}</span>
          </div>
        </div>
      </div>
      
      <div class="detail-section">
        <h4 class="section-title">替代信息</h4>
        <div class="replacement-info">
          <div class="replacement-item">
            <span class="replacement-label">目标原料</span>
            <span class="replacement-value">{{ plan.target_canonical }}</span>
          </div>
          <div class="replacement-arrow">→</div>
          <div class="replacement-item">
            <span class="replacement-label">候选原料</span>
            <span class="replacement-value">{{ plan.candidate_canonical }}</span>
          </div>
        </div>
        
        <div v-if="plan.repair_canonical" class="repair-info">
          <div class="repair-item">
            <span class="repair-label">修复原料</span>
            <span class="repair-value">{{ plan.repair_canonical }}</span>
          </div>
          <div class="repair-item">
            <span class="repair-label">修复角色</span>
            <span class="repair-value">{{ plan.repair_role || 'N/A' }}</span>
          </div>
          <div class="repair-item">
            <span class="repair-label">修复因子</span>
            <span class="repair-value">{{ (plan.repair_factor || 1.0).toFixed(2) }}</span>
          </div>
        </div>
      </div>
      
      <div class="detail-section">
        <h4 class="section-title">SQE评分对比</h4>
        <div class="sqe-comparison">
          <div class="sqe-bar-item">
            <div class="sqe-bar-label">原始配方</div>
            <div class="sqe-bar-container">
              <div class="sqe-bar-fill original" :style="{ width: getSqePercentage(plan.old_sqe_total) + '%' }"></div>
            </div>
            <div class="sqe-bar-value">{{ (plan.old_sqe_total || 0).toFixed(3) }}</div>
          </div>
          <div class="sqe-bar-item">
            <div class="sqe-bar-label">单步替代</div>
            <div class="sqe-bar-container">
              <div class="sqe-bar-fill single" :style="{ width: getSqePercentage(plan.single_sqe_total) + '%' }"></div>
            </div>
            <div class="sqe-bar-value">{{ (plan.single_sqe_total || 0).toFixed(3) }}</div>
          </div>
          <div class="sqe-bar-item">
            <div class="sqe-bar-label">组合调整</div>
            <div class="sqe-bar-container">
              <div class="sqe-bar-fill combo" :style="{ width: getSqePercentage(plan.combo_sqe_total) + '%' }"></div>
            </div>
            <div class="sqe-bar-value">{{ (plan.combo_sqe_total || 0).toFixed(3) }}</div>
          </div>
        </div>
      </div>
      
      <div class="detail-section" v-if="plan.explanation">
        <h4 class="section-title">方案说明</h4>
        <p class="explanation-text">{{ plan.explanation }}</p>
      </div>
      
      <div class="detail-section" v-if="plan.judgement">
        <h4 class="section-title">判定说明</h4>
        <div class="judgement-content">
          <p class="judgement-text">{{ plan.judgement.judgement_text }}</p>
          <div class="diagnosis-list" v-if="plan.judgement.diagnosis && plan.judgement.diagnosis.length > 0">
            <div 
              v-for="(item, index) in plan.judgement.diagnosis" 
              :key="index"
              class="diagnosis-item"
            >
              <span class="diagnosis-icon">•</span>
              <span class="diagnosis-text">{{ item }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ComboPlanDetail',
  
  props: {
    plan: {
      type: Object,
      required: true
    }
  },
  
  methods: {
    getSqePercentage(value) {
      if (!value) return 0
      return Math.min(100, Math.max(0, value * 100))
    }
  }
}
</script>

<style scoped>
.combo-plan-detail {
  padding: var(--spacing-lg);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 2px solid var(--color-border);
}

.detail-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.detail-status {
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: 0.9rem;
  font-weight: 600;
}

.detail-status.accept {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success);
}

.detail-status.reject {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-error);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.detail-section {
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

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.info-value {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.info-value.rank {
  color: var(--color-gold-400);
  font-size: 1.2rem;
  font-weight: 700;
}

.info-value.code {
  font-family: monospace;
  background: var(--color-bg-1);
  padding: 2px var(--spacing-xs);
  border-radius: var(--border-radius-sm);
}

.replacement-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
}

.replacement-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.replacement-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.replacement-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.replacement-arrow {
  font-size: 1.5rem;
  color: var(--color-gold-400);
}

.repair-info {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--color-gold-400);
}

.repair-item {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
}

.repair-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.repair-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

.sqe-comparison {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.sqe-bar-item {
  display: grid;
  grid-template-columns: 100px 1fr 80px;
  align-items: center;
  gap: var(--spacing-md);
}

.sqe-bar-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.sqe-bar-container {
  height: 24px;
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
  overflow: hidden;
}

.sqe-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.sqe-bar-fill.original {
  background: var(--color-text-secondary);
}

.sqe-bar-fill.single {
  background: var(--color-warning);
}

.sqe-bar-fill.combo {
  background: linear-gradient(90deg, var(--color-gold-400), var(--color-gold-600));
}

.sqe-bar-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: right;
}

.explanation-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.judgement-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.judgement-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.diagnosis-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.diagnosis-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
}

.diagnosis-icon {
  color: var(--color-gold-400);
  font-size: 1.2rem;
  line-height: 1.4;
}

.diagnosis-text {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}
</style>
