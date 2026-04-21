<template>
  <div class="process-flow-container">
    <a-card title="处理流程" class="process-flow-card">
      <template #extra>
        <a-button type="text" size="small" @click="toggleAll">
          {{ allExpanded ? '全部折叠' : '全部展开' }}
        </a-button>
      </template>
      
      <a-timeline v-if="trace && trace.visualization_steps">
        <a-timeline-item
          v-for="(step, index) in trace.visualization_steps"
          :key="step.name"
          :color="getStatusColor(step.status)"
        >
          <div class="step-item">
            <div class="step-header">
              <div class="step-title">
                <span class="step-number">{{ index + 1 }}</span>
                <h3>{{ step.title }}</h3>
                <a-tag :color="getStatusTagColor(step.status)" class="step-status">
                  {{ getStatusText(step.status) }}
                </a-tag>
              </div>
              <a-button
                type="text"
                size="small"
                @click="toggleStep(step.name)"
                class="toggle-button"
              >
                <template #icon>
                  <DownOutlined v-if="expandedStep !== step.name" />
                  <UpOutlined v-else />
                </template>
              </a-button>
            </div>
            
            <a-collapse v-model:activeKey="activeKeys" v-if="expandedStep === step.name" class="step-collapse">
              <a-collapse-panel key="1" header="详细信息" class="step-detail-panel">
                <StepDetail :step="step" />
              </a-collapse-panel>
            </a-collapse>
          </div>
        </a-timeline-item>
      </a-timeline>
      
      <a-empty v-else description="暂无流程数据" />
    </a-card>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { DownOutlined, UpOutlined } from '@ant-design/icons-vue';
import StepDetail from './StepDetail.vue';

export default {
  name: 'ProcessFlow',
  components: {
    DownOutlined,
    UpOutlined,
    StepDetail
  },
  props: {
    trace: {
      type: Object,
      default: null
    }
  },
  setup(props) {
    const expandedStep = ref(null);
    const activeKeys = ref(['1']);
    const allExpanded = ref(false);

    const toggleStep = (stepName) => {
      expandedStep.value = expandedStep.value === stepName ? null : stepName;
    };

    const toggleAll = () => {
      allExpanded.value = !allExpanded.value;
      if (allExpanded.value && props.trace && props.trace.visualization_steps) {
        expandedStep.value = props.trace.visualization_steps[0].name;
      } else {
        expandedStep.value = null;
      }
    };

    const getStatusColor = (status) => {
      switch (status) {
        case 'success': return 'green';
        case 'error': return 'red';
        case 'running': return 'blue';
        case 'skipped': return 'gray';
        default: return 'gray';
      }
    };

    const getStatusTagColor = (status) => {
      switch (status) {
        case 'success': return 'success';
        case 'error': return 'error';
        case 'running': return 'processing';
        case 'skipped': return 'default';
        default: return 'default';
      }
    };

    const getStatusText = (status) => {
      switch (status) {
        case 'success': return '成功';
        case 'error': return '失败';
        case 'running': return '处理中';
        case 'skipped': return '跳过';
        default: return '未知';
      }
    };

    return {
      expandedStep,
      activeKeys,
      allExpanded,
      toggleStep,
      toggleAll,
      getStatusColor,
      getStatusTagColor,
      getStatusText
    };
  }
};
</script>

<style scoped>
.process-flow-container {
  margin-top: var(--spacing-lg);
}

.process-flow-card {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.process-flow-card :deep(.ant-card-head) {
  border-bottom: 1px solid var(--color-border-subtle);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
}

.process-flow-card :deep(.ant-card-head-title) {
  font-weight: 600;
  color: var(--color-gold-200);
}

.step-item {
  padding: var(--spacing-sm) 0;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-md);
}

.step-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex: 1;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, var(--color-gold-400) 0%, var(--color-gold-500) 100%);
  color: #000;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-title h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.step-status {
  font-size: 12px;
  flex-shrink: 0;
}

.toggle-button {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.toggle-button:hover {
  color: var(--color-gold-400);
}

.step-collapse {
  margin-top: var(--spacing-sm);
  border: none;
  background: transparent;
}

.step-collapse :deep(.ant-collapse-item) {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.step-collapse :deep(.ant-collapse-header) {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-surface-elevated);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.step-collapse :deep(.ant-collapse-content) {
  background: var(--color-surface-elevated);
  border-top: 1px solid var(--color-border-subtle);
}

.step-collapse :deep(.ant-collapse-content-box) {
  padding: var(--spacing-md);
}

.step-detail-panel {
  border: none;
}
</style>