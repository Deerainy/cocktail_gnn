<template>
  <div class="chat-history-container">
    <a-list
      :data-source="messages"
      class="message-list"
      :locale="{ emptyText: '暂无对话记录' }"
    >
      <template #renderItem="{ item }">
        <a-list-item :class="['message-item', item.type]">
          <div class="message-wrapper">
            <div class="message-avatar">
              <a-avatar v-if="item.type === 'user'" :size="40" :src="guestAvatar" />
              <a-avatar v-else :size="40" :src="bartenderAvatar" />
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="message-sender">{{ item.type === 'user' ? '客人' : '酒保' }}</span>
                <span class="message-time">{{ formatTime(item.timestamp) }}</span>
              </div>
              <div class="message-text" v-html="renderMarkdown(item.content)"></div>
              <!-- 显示推荐的recipe卡片 -->
              <div v-if="item.recommendations && item.recommendations.length > 0" class="message-recommendations">
                <div class="recommendations-title">推荐饮品：</div>
                <div class="recommendations-grid">
                  <div 
                    v-for="(recipe, index) in item.recommendations" 
                    :key="recipe.recipe_id"
                    class="recipe-card-mini"
                    @click="navigateToRecipe(recipe.recipe_id)"
                  >
                    <div class="recipe-card-image">
                      <img 
                        :src="getRecipeImage(recipe.recipe_id)" 
                        :alt="recipe.recipe_name_zh || recipe.name" 
                        class="recipe-image"
                        @error="$event.target.src = require('@/assets/loss.png')"
                      >
                    </div>
                    <div class="recipe-card-content">
                      <h4 class="recipe-card-name">
                        <span v-if="recipe.recipe_name_zh" class="name-zh">{{ recipe.recipe_name_zh }}</span>
                        <span v-if="recipe.recipe_name_zh && recipe.name" class="name-separator"> / </span>
                        <span v-if="recipe.name" class="name-en">{{ recipe.name }}</span>
                      </h4>
                      <div class="recipe-card-info">
                        <div v-if="recipe.glass" class="info-item">
                          <span class="info-label">酒杯</span>
                          <span class="info-value">{{ recipe.glass }}</span>
                        </div>
                        <div class="info-item">
                          <span class="info-label">含酒精</span>
                          <span class="info-value">{{ recipe.is_alcoholic ? '否' : '是' }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-list-item>
      </template>
    </a-list>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue';
import { UserOutlined, RobotOutlined } from '@ant-design/icons-vue';
import { marked } from 'marked';
import guestAvatar from '@/assets/客人头像.png'
import bartenderAvatar from '@/assets/酒保头像.png'
import background from '@/assets/对话背景.png'

export default {
  name: 'ChatHistory',
  components: {
    UserOutlined,
    RobotOutlined
  },
  props: {
    messages: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const formatTime = (timestamp) => {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now - date;

      if (diff < 60000) {
        return '刚刚';
      } else if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`;
      } else if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`;
      } else {
        return date.toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
    };

    const renderMarkdown = (content) => {
      if (!content) return '';
      
      // 配置marked选项
      marked.setOptions({
        breaks: true, // 支持换行符
        gfm: true // 支持GitHub风格的Markdown
      });
      
      // 渲染markdown
      return marked(content);
    };

    const navigateToRecipe = (recipeId) => {
      window.location.href = `/visualization?recipe_id=${recipeId}`;
    };

    const getRecipeImage = (id) => {
      try {
        const imageId = id > 50 ? id - 50 : id;
        return require(`@/assets/recipe_image/${imageId}.png`)
      } catch (e) {
        return require('@/assets/loss.png')
      }
    };

    return {
      formatTime,
      renderMarkdown,
      navigateToRecipe,
      getRecipeImage,
      guestAvatar,
      bartenderAvatar,
      background
    };
  }
};
</script>

<style scoped>
/* 全局动画 */
@keyframes messageFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.chat-history-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
  background: url('@/assets/对话背景.png') no-repeat center center;
  background-size: cover;
}

.message-list {
  background: transparent;
}

.message-item {
  border: none;
  padding: var(--spacing-md) 0;
  background: transparent;
  animation: messageFadeIn 0.5s ease-out;
}

.message-item.user {
  justify-content: flex-end;
  animation: slideInRight 0.5s ease-out;
}

.message-item.system {
  animation: slideInLeft 0.5s ease-out;
}

.message-item.user .message-wrapper {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
  color: #000000;
  border-radius: var(--radius-lg) var(--radius-lg) 0 var(--radius-lg);
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.3);
  position: relative;
  overflow: hidden;
}

/* 添加装饰元素 */
.message-item.user .message-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
}

.message-item.system .message-content {
  background: linear-gradient(135deg, rgba(26, 20, 16, 0.9) 0%, rgba(26, 20, 16, 0.95) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) 0;
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
}

/* 添加装饰元素 */
.message-item.system .message-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
}

.message-wrapper {
  display: flex;
  gap: var(--spacing-md);
  max-width: 75%;
  word-break: break-word;
}

.message-avatar {
  flex-shrink: 0;
  transition: all var(--transition-normal);
}

.message-avatar:hover {
  transform: scale(1.1);
}

.message-content {
  padding: var(--spacing-md);
  min-width: 200px;
  max-width: 100%;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  transition: all var(--transition-normal);
}

.message-content:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.2) !important;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
  font-size: 12px;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

.message-sender {
  font-weight: 600;
  color: #ffffff;
  text-transform: uppercase;
}

.message-time {
  color: #cccccc;
  font-size: 11px;
  animation: pulse 2s infinite;
}

.message-text {
  font-size: 16px;
  line-height: 1.6;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  font-weight: 500;
  position: relative;
  z-index: 1;
  max-width: 100%;
}

/* Markdown样式 */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4),
.message-text :deep(h5),
.message-text :deep(h6) {
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.3;
  font-family: var(--font-display);
  color: var(--color-gold-300);
}

.message-text :deep(h1) {
  font-size: 1.5em;
}

.message-text :deep(h2) {
  font-size: 1.3em;
}

.message-text :deep(h3) {
  font-size: 1.1em;
}

.message-text :deep(p) {
  margin: 0.5em 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.message-text :deep(li) {
  margin: 0.3em 0;
  position: relative;
}

.message-text :deep(ul li::before) {
  content: '•';
  color: var(--color-gold-400);
  font-weight: bold;
  position: absolute;
  left: -1em;
}

.message-text :deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
}

.message-text :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
  margin: 0.5em 0;
  border: 1px solid var(--color-border-subtle);
}

.message-text :deep(pre code) {
  background: transparent;
  padding: 0;
}

.message-text :deep(blockquote) {
  border-left: 3px solid var(--color-gold-400);
  padding-left: 1em;
  margin: 0.5em 0;
  color: var(--color-text-secondary);
  font-style: italic;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.message-text :deep(strong) {
  font-weight: 600;
  color: var(--color-gold-300);
}

.message-text :deep(em) {
  font-style: italic;
  color: var(--color-text-secondary);
}

.message-text :deep(a) {
  color: var(--color-gold-400);
  text-decoration: none;
  transition: all var(--transition-normal);
  position: relative;
}

.message-text :deep(a::after) {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--color-gold-400);
  transition: width 0.3s ease;
}

.message-text :deep(a:hover::after) {
  width: 100%;
}

.message-text :deep(a:hover) {
  color: var(--color-gold-300);
}

.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid var(--color-border-subtle);
  padding: 0.5em;
  text-align: left;
}

.message-text :deep(th) {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
  font-weight: 600;
  color: var(--color-gold-300);
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(26, 20, 16, 0.5);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-500));
  border-radius: 4px;
  transition: all var(--transition-normal);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, var(--color-gold-300), var(--color-gold-400));
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

/* 推荐卡片样式 */
.message-recommendations {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid rgba(212, 175, 55, 0.2);
  animation: messageFadeIn 0.8s ease-out;
}

.recommendations-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gold-300);
  margin-bottom: var(--spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  position: relative;
  display: inline-block;
}

.recommendations-title::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, var(--color-gold-400), transparent);
}

.recommendations-grid {
  display: flex;
  gap: var(--spacing-sm);
  overflow-x: auto;
  padding-bottom: var(--spacing-xs);
  scrollbar-width: thin;
  scrollbar-color: rgba(212, 175, 55, 0.3) transparent;
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
}

.recommendations-grid::-webkit-scrollbar {
  height: 6px;
}

.recommendations-grid::-webkit-scrollbar-track {
  background: rgba(26, 20, 16, 0.5);
  border-radius: 3px;
}

.recommendations-grid::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-500));
  border-radius: 3px;
  transition: all var(--transition-normal);
}

.recommendations-grid::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, var(--color-gold-300), var(--color-gold-400));
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

.recipe-card-mini {
  flex: 0 0 200px;
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.9) 0%, rgba(26, 20, 16, 0.95) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

/* 添加装饰元素 */
.recipe-card-mini::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
}

.recipe-card-mini:hover {
  border-color: var(--color-gold-400);
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(212, 175, 55, 0.25);
}

.recipe-card-mini .recipe-card-image {
  height: 120px;
  overflow: hidden;
  position: relative;
}

.recipe-card-mini .recipe-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.recipe-card-mini:hover .recipe-image {
  transform: scale(1.1);
}

/* 添加悬停效果 */
.recipe-card-mini .recipe-card-image::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.recipe-card-mini:hover .recipe-card-image::after {
  opacity: 1;
}

.recipe-card-mini .recipe-card-content {
  padding: var(--spacing-sm);
  position: relative;
  z-index: 1;
}

.recipe-card-mini .recipe-card-name {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
  transition: color 0.3s ease;
  line-height: 1.3;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.recipe-card-mini:hover .recipe-card-name {
  color: var(--color-gold-300);
}

.recipe-card-mini .recipe-card-name .name-zh {
  color: var(--color-text-primary);
  font-weight: 600;
}

.recipe-card-mini .recipe-card-name .name-en {
  color: var(--color-text-secondary);
  font-weight: 400;
  font-size: 0.8em;
}

.recipe-card-mini .recipe-card-name .name-separator {
  color: var(--color-gold-400);
  margin: 0 0.1em;
}

.recipe-card-mini .recipe-card-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.recipe-card-mini .info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-secondary);
  padding: 6px 8px;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.05) 0%, rgba(212, 175, 55, 0.02) 100%);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(212, 175, 55, 0.1);
  transition: all 0.3s ease;
}

.recipe-card-mini:hover .info-item {
  border-color: var(--color-gold-400);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
}

.recipe-card-mini .info-label {
  font-weight: 600;
  color: var(--color-gold-400);
  flex-shrink: 0;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.recipe-card-mini .info-value {
  flex: 1;
  color: var(--color-text-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-wrapper {
    max-width: 85%;
  }
  
  .recipe-card-mini {
    flex: 0 0 160px;
  }
  
  .recipe-card-mini .recipe-card-image {
    height: 100px;
  }
  
  .recipe-card-mini .recipe-card-name {
    font-size: 12px;
    height: 36px;
  }
  
  .recipe-card-mini .info-item {
    font-size: 10px;
    padding: 4px 6px;
  }
}
</style>
