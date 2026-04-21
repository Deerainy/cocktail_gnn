<template>
  <div class="chat-input-container">
    <!-- 提问模板 -->
    <div class="chat-templates" v-if="!loading">
      <div class="template-tags">
        <a-tag 
          v-for="(template, index) in templates" 
          :key="index"
          class="template-tag"
          @click="selectTemplate(template.text)"
        >
          {{ template.text }}
        </a-tag>
      </div>
    </div>
    
    <a-textarea
      v-model:value="inputValue"
      :placeholder="placeholder"
      :auto-size="{ minRows: 3, maxRows: 6 }"
      @keydown.enter.exact="handleSend"
      :disabled="loading"
      class="chat-textarea"
    />
    <div class="chat-input-actions">
      <span class="char-count">{{ inputValue.length }} / 500</span>
      <a-button
        type="primary"
        :loading="loading"
        :disabled="!inputValue.trim()"
        @click="handleSend"
        class="send-button"
      >
        发送
      </a-button>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue';

export default {
  name: 'ChatInput',
  props: {
    placeholder: {
      type: String,
      default: '请输入您的问题...'
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['send'],
  setup(props, { emit }) {
    const inputValue = ref('');
    
    // 提问模板
    const templates = [
      { text: '推荐一款适合夏天的鸡尾酒' },
      { text: '苦精可以换成什么' },
      { text: 'Flor de Amaras的配方是什么' },
      { text: '适合初学者的鸡尾酒有哪些' },
      { text: '家里只有朗姆酒，能做什么鸡尾酒' },
      { text: '适合聚会的鸡尾酒推荐' },
      { text: '甜的鸡尾酒有哪些' },
      { text: '苦精可以去哪里买' }
    ];

    const handleSend = () => {
      if (!inputValue.value.trim() || props.loading) return;
      emit('send', inputValue.value);
      inputValue.value = '';
    };

    const selectTemplate = (templateText) => {
      inputValue.value = templateText;
    };

    watch(inputValue, (newValue) => {
      if (newValue.length > 500) {
        inputValue.value = newValue.slice(0, 500);
      }
    });

    return {
      inputValue,
      handleSend,
      templates,
      selectTemplate
    };
  }
};
</script>

<style scoped>
/* 全局动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-input-container {
  background: linear-gradient(135deg, rgba(26, 20, 16, 0.9) 0%, rgba(26, 20, 16, 0.95) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
  animation: slideInUp 0.5s ease-out;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

/* 添加装饰元素 */
.chat-input-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
  animation: pulse 3s infinite;
}

.chat-input-container:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2);
  transform: translateY(-2px);
}

.chat-templates {
  margin-bottom: var(--spacing-sm);
  text-align: left;
  position: relative;
  z-index: 1;
}

.template-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  max-height: 80px;
  overflow-y: auto;
  padding-right: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.template-tags:hover {
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.05);
}

.template-tag {
  cursor: pointer !important;
  transition: all var(--transition-normal) !important;
  font-size: 12px !important;
  padding: 6px 14px !important;
  border-radius: 20px !important;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%) !important;
  border: 1px solid rgba(212, 175, 55, 0.3) !important;
  color: var(--color-gold-300) !important;
  font-family: var(--font-display) !important;
  letter-spacing: 0.05em !important;
  position: relative;
  overflow: hidden;
}

.template-tag::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.template-tag:hover::before {
  left: 100%;
}

.template-tag:hover {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%) !important;
  border-color: var(--color-gold-400) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2) !important;
}

/* 自定义滚动条 */
.template-tags::-webkit-scrollbar {
  width: 6px;
}

.template-tags::-webkit-scrollbar-track {
  background: rgba(26, 20, 16, 0.5);
  border-radius: 3px;
}

.template-tags::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-500));
  border-radius: 3px;
  transition: all var(--transition-normal);
}

.template-tags::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, var(--color-gold-300), var(--color-gold-400));
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

.chat-textarea {
  border: none;
  box-shadow: none;
  resize: none;
  font-size: 16px;
  line-height: 1.6;
  color: #ffffff !important;
  background: transparent !important;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
  position: relative;
  z-index: 1;
  transition: all var(--transition-normal);
}

.chat-textarea:focus {
  border: none;
  box-shadow: none;
  outline: none;
}

.chat-textarea::placeholder {
  color: #999999 !important;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
  opacity: 0.7;
}

.chat-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing-sm);
  position: relative;
  z-index: 1;
}

.char-count {
  font-size: 12px;
  color: #cccccc;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
  transition: all var(--transition-normal);
}

.char-count:hover {
  color: var(--color-gold-300);
}

.send-button {
  min-width: 100px;
  height: 40px;
  background: linear-gradient(135deg, var(--color-gold-500) 0%, var(--color-gold-400) 50%, var(--color-gold-300) 100%) !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  transition: all var(--transition-normal) !important;
  color: #000000 !important;
  font-family: var(--font-display) !important;
  letter-spacing: 0.05em !important;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.3);
}

.send-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.send-button:hover:not(:disabled)::before {
  left: 100%;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.4) !important;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-input-container {
    padding: var(--spacing-sm);
  }
  
  .template-tag {
    font-size: 11px !important;
    padding: 4px 12px !important;
  }
  
  .send-button {
    min-width: 80px;
    height: 36px;
  }
}
</style>