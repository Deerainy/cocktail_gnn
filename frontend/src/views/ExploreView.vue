<template>
  <div class="page">
    <div class="page-header">
      <div class="container">
        <div class="page-header-content">
          <h1 class="page-title">风味探索</h1>
          <p class="page-subtitle">浏览基酒、辅料与风味特征数据库</p>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="explore-tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['tab-button', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.name }}
        </button>
      </div>
      <div class="card">
        <div v-if="activeTab === 'spirits'" class="content-grid-3">
          <div v-for="item in spirits" :key="item.id" class="item-card">
            <div class="item-icon">{{ item.emoji }}</div>
            <h3 class="item-title">{{ item.name }}</h3>
            <p class="item-desc">{{ item.description }}</p>
          </div>
        </div>
        <div v-else-if="activeTab === 'ingredients'" class="content-grid-3">
          <div v-for="item in ingredients" :key="item.id" class="item-card">
            <div class="item-icon">{{ item.emoji }}</div>
            <h3 class="item-title">{{ item.name }}</h3>
            <p class="item-desc">{{ item.description }}</p>
          </div>
        </div>
        <div v-else-if="activeTab === 'flavors'" class="content-grid-3">
          <div v-for="item in flavors" :key="item.id" class="item-card">
            <div class="item-icon">{{ item.emoji }}</div>
            <h3 class="item-title">{{ item.name }}</h3>
            <p class="item-desc">{{ item.description }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ExploreView',
  data() {
    return {
      activeTab: 'spirits',
      tabs: [
        { id: 'spirits', name: '基酒' },
        { id: 'ingredients', name: '辅料' },
        { id: 'flavors', name: '风味特征' }
      ],
      spirits: [
        { id: 1, emoji: '🍸', name: '金酒', description: '杜松子香气，清澈明亮' },
        { id: 2, emoji: '🥃', name: '威士忌', description: '烟熏麦芽，醇厚馥郁' },
        { id: 3, emoji: '🍹', name: '朗姆酒', description: '甘蔗香甜，热情奔放' },
        { id: 4, emoji: '🍋', name: '伏特加', description: '纯净无色，中性顺滑' },
        { id: 5, emoji: '🌿', name: '龙舌兰', description: '植物辛香，独特个性' },
        { id: 6, emoji: '🍊', name: '白兰地', description: '葡萄陈酿，优雅圆润' }
      ],
      ingredients: [
        { id: 1, emoji: '🍋', name: '柠檬', description: '清新酸爽，提味必备' },
        { id: 2, emoji: '🍊', name: '橙', description: '香甜多汁，风味丰富' },
        { id: 3, emoji: '🌿', name: '薄荷', description: '清凉提神，香气独特' },
        { id: 4, emoji: '🍯', name: '糖浆', description: '增加甜味，调和口感' },
        { id: 5, emoji: '🥚', name: '蛋清', description: '丝滑质地，丰盈泡沫' },
        { id: 6, emoji: '💧', name: '苦精', description: '点睛之笔，层次提升' }
      ],
      flavors: [
        { id: 1, emoji: '🍊', name: '柑橘', description: '柠檬、橙、葡萄柚' },
        { id: 2, emoji: '🌸', name: '花香', description: '玫瑰、茉莉、橙花' },
        { id: 3, emoji: '🌿', name: '草本', description: '薄荷、罗勒、迷迭香' },
        { id: 4, emoji: '🍫', name: '香甜', description: '焦糖、巧克力、香草' },
        { id: 5, emoji: '🌰', name: '坚果', description: '杏仁、核桃、榛子' },
        { id: 6, emoji: '🔥', name: '烟熏', description: '泥煤、烘烤、木质' }
      ]
    };
  }
};
</script>

<style scoped>
.page {
  width: 100%;
  padding-bottom: var(--spacing-3xl);
}

.page-header {
  padding: var(--spacing-3xl) 0 var(--spacing-2xl) 0;
  border-bottom: 1px solid var(--color-border-subtle);
}

.page-header-content {
  text-align: center;
}

.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl);
}

.explore-tabs {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-2xl);
  margin-bottom: var(--spacing-xl);
}

.tab-button {
  padding: var(--spacing-sm) var(--spacing-lg);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-button:hover {
  color: var(--color-gold-200);
  border-color: var(--color-border-strong);
}

.tab-button.active {
  color: var(--color-gold-200);
  background: rgba(212, 175, 55, 0.1);
  border-color: var(--color-gold-400);
}

.card {
  padding: var(--spacing-xl);
}

.content-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}

.item-card {
  padding: var(--spacing-xl);
  text-align: center;
  background: rgba(212, 175, 55, 0.04);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
}

.item-card:hover {
  background: rgba(212, 175, 55, 0.08);
  border-color: var(--color-border-strong);
  transform: translateY(-2px);
}

.item-icon {
  font-size: 40px;
  margin-bottom: var(--spacing-md);
}

.item-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.item-desc {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.6;
}
</style>
