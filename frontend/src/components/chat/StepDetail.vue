<template>
  <div class="step-detail">
    <template v-if="step.name === 'input_analysis'">
      <div class="detail-section">
        <h4>输入分析</h4>
        <a-descriptions bordered :column="1" size="small">
          <a-descriptions-item label="原始问题">
            {{ step.data.original_question }}
          </a-descriptions-item>
          <a-descriptions-item label="规范化问题">
            {{ step.data.normalized_question }}
          </a-descriptions-item>
          <a-descriptions-item label="语言识别">
            <a-tag color="blue">{{ step.data.language }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </template>

    <template v-else-if="step.name === 'entity_recognition'">
      <div class="detail-section">
        <h4>实体识别</h4>
        <a-descriptions bordered :column="2" size="small">
          <a-descriptions-item label="命中方式">
            <a-tag color="purple">{{ step.data.hit_method }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="需要审核">
            <a-tag :color="step.data.needs_review ? 'orange' : 'green'">
              {{ step.data.needs_review ? '是' : '否' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
        
        <div class="entities-list">
          <h5>识别到的实体</h5>
          <a-table
            :dataSource="step.data.entities"
            :columns="entityColumns"
            :pagination="false"
            size="small"
            :scroll="{ y: 200 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'type'">
                <a-tag color="cyan">{{ record.type }}</a-tag>
              </template>
              <template v-else-if="column.key === 'confidence'">
                <a-progress
                  :percent="Math.round(record.confidence * 100)"
                  size="small"
                  :stroke-color="getConfidenceColor(record.confidence)"
                />
              </template>
            </template>
          </a-table>
        </div>
      </div>
    </template>

    <template v-else-if="step.name === 'intent_classification'">
      <div class="detail-section">
        <h4>意图分类</h4>
        <a-descriptions bordered :column="1" size="small">
          <a-descriptions-item label="最终意图">
            <a-tag color="green" style="font-size: 14px; padding: 4px 12px;">
              {{ step.data.final_intent }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="候选意图">
            <a-space wrap>
              <a-tag v-for="intent in step.data.candidate_intents" :key="intent" color="blue">
                {{ intent }}
              </a-tag>
            </a-space>
          </a-descriptions-item>
          <a-descriptions-item label="回退机制">
            <a-tag :color="step.data.used_fallback ? 'orange' : 'green'">
              {{ step.data.used_fallback ? '已启用' : '未启用' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </template>

    <template v-else-if="step.name === 'action_execution'">
      <div class="detail-section">
        <h4>动作执行</h4>
        <a-descriptions bordered :column="1" size="small">
          <a-descriptions-item label="选择的动作">
            <a-tag color="purple">{{ step.data.action }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="调用的工具">
            <a-tag color="cyan">{{ step.data.tool }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="参数">
            <pre class="params-display">{{ JSON.stringify(step.data.params, null, 2) }}</pre>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </template>

    <template v-else-if="step.name === 'retrieval_and_generation'">
      <div class="detail-section">
        <h4>检索与生成</h4>
        <a-descriptions bordered :column="2" size="small">
          <a-descriptions-item label="数据库类型">
            <a-tag color="blue">{{ step.data.database_type }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="结果数量">
            <a-tag color="green">{{ step.data.result_count }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>
        
        <div class="final-answer">
          <h5>最终回答</h5>
          <a-alert
            :message="step.data.final_answer"
            type="info"
            show-icon
          />
        </div>
        
        <div v-if="step.data.error_reason" class="error-reason">
          <h5>失败原因</h5>
          <a-alert
            :message="step.data.error_reason"
            type="error"
            show-icon
          />
        </div>
      </div>
    </template>

    <template v-else>
      <a-empty description="无详细信息" />
    </template>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'StepDetail',
  props: {
    step: {
      type: Object,
      required: true
    }
  },
  setup() {
    const entityColumns = [
      {
        title: '实体文本',
        dataIndex: 'text',
        key: 'text',
        width: '40%'
      },
      {
        title: '实体类型',
        dataIndex: 'type',
        key: 'type',
        width: '30%'
      },
      {
        title: '置信度',
        dataIndex: 'confidence',
        key: 'confidence',
        width: '30%'
      }
    ];

    const getConfidenceColor = (confidence) => {
      if (confidence >= 0.8) return '#52c41a';
      if (confidence >= 0.6) return '#faad14';
      return '#f5222d';
    };

    return {
      entityColumns,
      getConfidenceColor
    };
  }
};
</script>

<style scoped>
.step-detail {
  background: var(--color-surface-elevated);
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.detail-section h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-gold-200);
  padding-bottom: var(--spacing-xs);
  border-bottom: 1px solid var(--color-border-subtle);
}

.detail-section h5 {
  margin: var(--spacing-sm) 0 var(--spacing-xs) 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.entities-list {
  margin-top: var(--spacing-sm);
}

.params-display {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
  font-size: 12px;
  color: var(--color-text-primary);
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.final-answer {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.final-answer h5 {
  margin-top: 0;
  margin-bottom: var(--spacing-sm);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gold-300);
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

.error-reason {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md);
  background: rgba(245, 34, 45, 0.05);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.error-reason h5 {
  margin-top: 0;
  margin-bottom: var(--spacing-sm);
  font-size: 14px;
  font-weight: 600;
  color: #ff4d4f;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

:deep(.ant-descriptions-item-label) {
  background: rgba(212, 175, 55, 0.05);
  font-weight: 500;
  color: var(--color-text-secondary);
}

:deep(.ant-descriptions-item-content) {
  color: var(--color-text-primary);
}

:deep(.ant-table) {
  font-size: 13px;
}

:deep(.ant-table-thead > tr > th) {
  background: rgba(212, 175, 55, 0.05);
  font-weight: 600;
  color: var(--color-text-secondary);
}

:deep(.ant-table-tbody > tr > td) {
  color: var(--color-text-primary);
}

:deep(.ant-alert-info) {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.1) 0%, rgba(24, 144, 255, 0.05) 100%);
  border-color: rgba(24, 144, 255, 0.3);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

:deep(.ant-alert-info .ant-alert-message) {
  color: #ffffff;
  font-weight: 500;
  line-height: 1.5;
}

:deep(.ant-alert-error) {
  background: linear-gradient(135deg, rgba(245, 34, 45, 0.1) 0%, rgba(245, 34, 45, 0.05) 100%);
  border-color: rgba(245, 34, 45, 0.3);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(245, 34, 45, 0.1);
}

:deep(.ant-alert-error .ant-alert-message) {
  color: #ffffff;
  font-weight: 500;
  line-height: 1.5;
}
</style>