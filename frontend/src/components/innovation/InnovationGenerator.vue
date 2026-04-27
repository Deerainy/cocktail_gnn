<template>
  <div class="innovation-generator">
    <!-- 顶部标题区域 -->
    <div class="hero-section">
      <h1 class="main-title">创新风味组合生成</h1>
      <p class="main-subtitle">基于结构分析的个性化搭配生成</p>
      <div class="hero-accent"></div>
    </div>
    
    <!-- 主内容卡片 -->
    <div class="main-card">
      <!-- 基础原料选择 -->
      <div class="form-group">
        <div class="group-header">
          <h3 class="group-title">基础原料</h3>
          <p class="group-description">选择最多3个基础原料作为鸡尾酒的核心成分</p>
        </div>
        <div class="ingredient-selector">
          <a-tag
            v-for="ingredient in selectedIngredients"
            :key="ingredient.id"
            closable
            @close="removeIngredient(ingredient)"
            class="selected-ingredient"
          >
            {{ ingredient.name_zh || ingredient.name }}
          </a-tag>
          <a-button
            v-if="selectedIngredients.length < 3"
            type="primary"
            @click="openIngredientModal"
            class="add-ingredient-btn"
          >
            <template #icon>
              <plus-outlined />
            </template>
            添加原料
          </a-button>
          <a-alert
            v-if="selectedIngredients.length === 0"
            type="warning"
            show-icon
            message="请至少选择一个基础原料"
          />
        </div>
      </div>
      
      <!-- 应用场景选择 -->
      <div class="form-group">
        <div class="group-header">
          <h3 class="group-title">应用场景</h3>
          <p class="group-description">选择适合的饮用场景，优化配方推荐</p>
        </div>
        <div class="scene-selector">
          <a-tag
            v-for="(label, value) in sceneOptions"
            :key="value"
            :class="{ active: scene === value }"
            @click="scene = value"
          >
            {{ label }}
          </a-tag>
        </div>
      </div>
      
      <!-- 风味偏好调整 -->
      <div class="form-group">
        <div class="group-header">
          <h3 class="group-title">风味偏好</h3>
          <p class="group-description">调整各风味维度的强度，打造个性化口感</p>
        </div>
        <div class="flavor-container">
          <div class="flavor-adjustments">
            <div
              v-for="flavor in flavorTypes"
              :key="flavor.key"
              class="flavor-slider"
            >
              <div class="slider-container">
                <label class="flavor-label">{{ flavor.label }}</label>
                <a-slider
                  v-model:value="flavorPreferences[flavor.key]"
                  :min="0"
                  :max="100"
                  :class="['custom-slider', `slider-${flavor.key}`]"
                />
                <span class="flavor-value">{{ flavorPreferences[flavor.key] }}%</span>
              </div>
            </div>
          </div>
          <div class="flavor-chart">
            <div ref="flavorChartRef" class="chart-container"></div>
          </div>
        </div>
      </div>
      
      <!-- 生成按钮 -->
      <div class="action-section">
        <a-button
          type="primary"
          size="large"
          @click="generateCombinations"
          :loading="loading"
          :disabled="selectedIngredients.length === 0"
          class="generate-button"
        >
          <template #icon>
            <sync-outlined v-if="loading" />
            <fire-outlined v-else />
          </template>
          {{ loading ? '生成中...' : '生成酒单' }}
        </a-button>
      </div>
    </div>
    
    <!-- 生成结果 -->
    <div v-if="combinations.length > 0" class="results-section">
      <h2 class="results-title">生成的酒单</h2>
      <div class="combinations-grid">
        <div
          v-for="(combo, index) in combinations"
          :key="index"
          class="combination-card"
          @click="openComboModal(combo)"
        >
          <div class="card-header">
            <h4 class="combo-name">{{ combo.recipe_name || combo.suggested_name || '未知配方' }}</h4>
            <div class="combo-rank">#{{ index + 1 }}</div>
          </div>
          
          <div class="card-badge">
            <a-tag class="creativity-badge">{{ combo.creativity_level }}创意</a-tag>
          </div>
          
          <div class="card-body">
            <!-- 原料列表 -->
            <div class="ingredients-list">
              <h5 class="list-title">原料</h5>
              <div
                v-for="(ing, ingIndex) in combo.ingredients"
                :key="ing.id"
                class="ingredient-item"
              >
                <span class="ingredient-name">{{ ing.name_zh || ing.name }}</span>
                <span class="ingredient-role">{{ getRoleName(ing.role) }}</span>
              </div>
            </div>
            
            <!-- 风味特征 -->
            <div class="flavor-profile">
              <h5 class="list-title">风味特征</h5>
              <div class="flavor-bars">
                <div
                  v-for="(value, key) in combo.flavor_profile"
                  :key="key"
                  class="flavor-bar"
                >
                  <span class="flavor-key">{{ flavorMap[key] }}</span>
                  <div class="bar-container">
                    <div
                      class="bar-fill"
                      :style="{ width: (value * 100) + '%' }"
                    ></div>
                  </div>
                  <span class="flavor-value">{{ Math.round(value * 100) }}%</span>
                </div>
              </div>
            </div>
            
            <!-- 比例建议 -->
            <div class="proportions">
              <h5 class="list-title">建议比例</h5>
              <div class="proportion-list">
                <div
                  v-for="(proportion, pIndex) in combo.proportions"
                  :key="pIndex"
                  class="proportion-item"
                >
                  <span class="proportion-name">{{ getIngredientName(proportion.ingredient_id, combo.ingredients) }}</span>
                  <span class="proportion-value">{{ proportion.proportion }}%</span>
                </div>
              </div>
            </div>
            
            <!-- 做法 -->
            <div class="recipe">
              <h5 class="list-title">制作方法</h5>
              <div class="recipe-content" v-html="renderMarkdown(combo.recipe)"></div>
            </div>
          </div>
          
          <div class="card-footer">
            <a-button type="link" @click.stop="shareCombination(combo)">分享</a-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 原料选择模态框 -->
    <a-modal
      v-model:open="showIngredientModal"
      title="选择原料"
      width="800px"
      class="dark-modal"
    >
      <div class="ingredient-modal">
        <a-input
          v-model:value="ingredientSearch"
          placeholder="搜索原料"
          class="search-input"
          @input="filterIngredients"
        >
          <template #prefix>
            <search-outlined />
          </template>
        </a-input>
        
        <div class="ingredient-categories">
          <a-tag
            v-for="category in ingredientCategories"
            :key="category"
            :class="{ active: selectedCategory === category }"
            @click="selectedCategory = category; filterIngredients()"
          >
            {{ category === 'all' ? '全部' : getRoleName(category) }}
          </a-tag>
        </div>
        
        <div class="ingredient-list">
          <div v-if="loadingIngredients" class="loading-state">
            <a-spin tip="加载原料数据中..." />
          </div>
          <div v-else-if="filteredIngredients.length === 0" class="empty-state">
            <p>没有找到匹配的原料</p>
          </div>
          <div
            v-else
            v-for="ingredient in filteredIngredients"
            :key="ingredient.id"
            class="ingredient-option"
            @click="addIngredient(ingredient)"
          >
            <div class="option-info">
              <div class="option-name">{{ ingredient.name_zh || ingredient.name }}</div>
              <div class="option-role">{{ getRoleName(ingredient.role) }}</div>
            </div>
            <a-checkbox
              :checked="isIngredientSelected(ingredient.id)"
              @change="(e) => handleIngredientCheck(ingredient, e.target.checked)"
            />
          </div>
        </div>
      </div>
    </a-modal>
    
    <!-- 方案详情模态框 -->
    <a-modal
      v-model:open="showComboModal"
      :title="selectedCombo?.recipe_name || selectedCombo?.suggested_name || '方案详情'"
      width="800px"
      class="dark-modal"
    >
      <div v-if="selectedCombo" class="combo-detail">
        <div class="detail-header">
          <div class="detail-rank">#{{ combinations.indexOf(selectedCombo) + 1 }}</div>
          <a-tag class="creativity-badge">{{ selectedCombo.creativity_level }}创意</a-tag>
        </div>
        

        
        <!-- 做法 -->
        <div class="detail-section">
          <h5 class="detail-title">制作方法</h5>
          <div class="detail-recipe-content" v-html="renderMarkdown(selectedCombo.recipe)"></div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { PlusOutlined, FireOutlined, SyncOutlined, SearchOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { marked } from 'marked';
import * as echarts from 'echarts';
import graphApi from '@/api/graphApi';

// 原料数据将从API获取

export default {
  name: 'InnovationGenerator',
  components: {
    PlusOutlined,
    FireOutlined,
    SyncOutlined,
    SearchOutlined
  },
  setup() {
    // 状态管理
    const selectedIngredients = ref([]);
    const scene = ref('general');
    const creativityLevel = ref(2);
    const flavorPreferences = ref({
      sour: 50,
      sweet: 50,
      bitter: 50,
      aroma: 50,
      fruity: 50,
      body: 50
    });
    const loading = ref(false);
    const combinations = ref([]);
    
    // 方案详情模态框
    const showComboModal = ref(false);
    const selectedCombo = ref(null);
    
    // 原料选择模态框
    const showIngredientModal = ref(false);
    const ingredientSearch = ref('');
    const selectedCategory = ref('all');
    const ingredients = ref([]);
    const loadingIngredients = ref(false);
    
    // 饼图相关
    const flavorChartRef = ref(null);
    let flavorChart = null;
    
    // 数据映射
    const creativityLabels = {
      1: '保守 - 基于传统搭配',
      2: '适中 - 平衡创新与传统',
      3: '激进 - 大胆尝试新组合'
    };
    
    // 渲染 markdown 格式的做法
    const renderMarkdown = (text) => {
      if (!text) return '暂无做法';
      return marked(text);
    };
    
    // 从recipe中提取配方名
    const extractRecipeName = (recipe) => {
      if (!recipe) return '未知配方';
      
      // 尝试从recipe中提取配方名
      // 查找类似 "鸡尾酒名称：xxx" 或 "名称：xxx" 或 "Cocktail Name: xxx" 的模式
      const namePatterns = [
        /(?:鸡尾酒名称|名称|Cocktail Name):\s*(.+)/i,
        /^#\s*(.+)/, // 查找Markdown标题
        /名为[\s"']*(.+?)[\s"']*的/i // 处理开场白中的配方名
      ];
      
      for (const pattern of namePatterns) {
        const match = recipe.match(pattern);
        if (match && match[1]) {
          return match[1].trim();
        }
      }
      
      return '未知配方';
    };
    
    const flavorMap = {
      sour: '酸味',
      sweet: '甜味',
      bitter: '苦味',
      aroma: '香气',
      fruity: '果香',
      body: '酒体'
    };
    
    const flavorTypes = [
      { key: 'sour', label: '酸味' },
      { key: 'sweet', label: '甜味' },
      { key: 'bitter', label: '苦味' },
      { key: 'aroma', label: '香气' },
      { key: 'fruity', label: '果香' },
      { key: 'body', label: '酒体' }
    ];
    
    const sceneOptions = {
      general: '通用',
      party: '派对',
      casual: '休闲',
      formal: '正式',
      summer: '夏季',
      winter: '冬季'
    };
    
    const ingredientCategories = ['all', 'spirit', 'liqueur', 'juice', 'syrup', 'bitters', 'fortified_wine', 'other'];
    
    // 原料类型中英文映射
    const roleMap = {
      'spirit': '烈酒',
      'liqueur': '利口酒',
      'juice': '果汁',
      'syrup': '糖浆',
      'bitters': '苦精',
      'fortified_wine': '加强酒',
      'other': '其他'
    };
    
    // 获取原料类型的中文名称
    const getRoleName = (role) => {
      return roleMap[role] || role;
    };
    
    // 计算属性
    const filteredIngredients = computed(() => {
      let result = ingredients.value;
      
      // 按类别过滤
      if (selectedCategory.value !== 'all') {
        result = result.filter(ing => ing.role === selectedCategory.value);
      }
      
      // 按搜索词过滤
      if (ingredientSearch.value) {
        const searchLower = ingredientSearch.value.toLowerCase();
        result = result.filter(ing => 
          (ing.name && ing.name.toLowerCase().includes(searchLower)) ||
          (ing.name_zh && ing.name_zh.toLowerCase().includes(searchLower))
        );
      }
      
      return result;
    });
    
    // 从API获取原料数据
    const fetchIngredients = async () => {
      // 如果已经有原料数据，直接返回
      if (ingredients.value.length > 0) {
        return;
      }
      
      loadingIngredients.value = true;
      try {
        console.log('开始获取原料数据...');
        // 减少获取的原料数量，提高加载速度
        const response = await graphApi.getRankings({ limit: 200 });
        
        if (response.data.code === 0) {
          // 首先处理top_ingredients
          const ingredientsFromTop = (response.data.data.top_ingredients || []).map(ingredient => ({
            id: ingredient.id,
            name: ingredient.name,
            name_zh: ingredient.name_zh,
            role: ingredient.role,
            type: ingredient.ingredient_type
          }));
          
          // 然后处理top_canonicals
          const ingredientsFromCanonicals = (response.data.data.top_canonicals || []).map(ingredient => ({
            id: `c_${ingredient.canonical_id}`,
            name: ingredient.canonical_name,
            name_zh: ingredient.canonical_name_zh,
            role: ingredient.role,
            type: ingredient.ingredient_type
          }));
          
          // 合并并去重
          const allIngredients = [...ingredientsFromTop, ...ingredientsFromCanonicals];
          
          // 去重
          const uniqueIngredients = [];
          const seenIds = new Set();
          
          for (const ingredient of allIngredients) {
            if (ingredient.id && !seenIds.has(ingredient.id)) {
              seenIds.add(ingredient.id);
              uniqueIngredients.push(ingredient);
            }
          }
          
          ingredients.value = uniqueIngredients;
        } else {
          console.error('API返回错误:', response.data.message);
          message.error('获取原料数据失败');
        }
      } catch (error) {
        console.error('获取原料数据失败:', error);
        message.error('获取原料数据失败，请重试');
      } finally {
        loadingIngredients.value = false;
      }
    };
    
    // 当打开原料选择模态框时才获取原料数据
    const openIngredientModal = () => {
      showIngredientModal.value = true;
      // 打开模态框时获取原料数据
      fetchIngredients();
    };
    
    // 初始化风味偏好饼图
    const initFlavorChart = () => {
      if (flavorChartRef.value) {
        flavorChart = echarts.init(flavorChartRef.value);
        updateFlavorChart();
        
        // 监听窗口大小变化，调整饼图大小
        window.addEventListener('resize', () => {
          flavorChart?.resize();
        });
      }
    };
    
    // 更新风味偏好饼图
    const updateFlavorChart = () => {
      if (!flavorChart) return;
      
      const data = flavorTypes.map(flavor => ({
        name: flavor.label,
        value: flavorPreferences.value[flavor.key],
        itemStyle: {
          color: getFlavorColor(flavor.key)
        }
      })).filter(item => item.value > 0);
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}%'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          textStyle: {
            color: '#e8e6e3'
          }
        },
        series: [
          {
            name: '风味偏好',
            type: 'pie',
            radius: ['35%', '80%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 12,
              borderColor: '#1a1410',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 18,
                fontWeight: 'bold',
                color: '#e8e6e3'
              }
            },
            labelLine: {
              show: false
            },
            data: data
          }
        ]
      };
      
      flavorChart.setOption(option);
    };
    
    // 获取风味对应的颜色
    const getFlavorColor = (key) => {
      const colorMap = {
        sour: '#FF6B6B',
        sweet: '#4ECDC4',
        bitter: '#45B7D1',
        aroma: '#96CEB4',
        fruity: '#FFEAA7',
        body: '#DDA0DD'
      };
      return colorMap[key] || '#d4af37';
    };
    
    // 方法
    const addIngredient = (ingredient) => {
      if (selectedIngredients.value.length >= 3) {
        message.warning('最多只能选择3个基础原料');
        return;
      }
      
      if (!isIngredientSelected(ingredient.id)) {
        selectedIngredients.value.push(ingredient);
        message.success(`已添加 ${ingredient.name_zh || ingredient.name}`);
      }
    };
    
    const removeIngredient = (ingredient) => {
      const index = selectedIngredients.value.findIndex(ing => ing.id === ingredient.id);
      if (index > -1) {
        selectedIngredients.value.splice(index, 1);
        message.success(`已移除 ${ingredient.name_zh || ingredient.name}`);
      }
    };
    
    const isIngredientSelected = (ingredientId) => {
      return selectedIngredients.value.some(ing => ing.id === ingredientId);
    };
    
    const handleIngredientCheck = (ingredient, checked) => {
      if (checked) {
        addIngredient(ingredient);
      } else {
        removeIngredient(ingredient);
      }
    };
    
    const filterIngredients = () => {
      // 已在computed中处理
    };
    
    const generateCombinations = async () => {
      if (selectedIngredients.value.length === 0) {
        message.error('请至少选择一个基础原料');
        return;
      }
      
      loading.value = true;
      
      try {
        // 准备请求参数
        const requestData = {
          base_ingredients: selectedIngredients.value.map(ing => ing.id.replace('c_', '')),
          scene: scene.value,
          flavor_preferences: flavorPreferences.value
        };
        
        console.log('发送生成请求:', requestData);
        
        // 调用后端创新生成API
        const apiUrl = 'http://localhost:8000/api/innovation/generate';
        console.log('发送请求到:', apiUrl);
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });
        
        console.log('响应状态:', response.status);
        console.log('响应状态文本:', response.statusText);
        console.log('响应URL:', response.url);
        
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        console.log('响应内容类型:', contentType);
        
        if (!contentType || !contentType.includes('application/json')) {
          // 如果不是 JSON 响应，读取文本内容
          const text = await response.text();
          console.error('非 JSON 响应:', text);
          message.error('生成失败: 服务器返回了非 JSON 响应');
          return;
        }
        
        const data = await response.json();
        console.log('API响应:', data);
        
        if (data.code === 0) {
          // 使用后端返回的真实数据
          combinations.value = data.data.generated_combinations || [];
          message.success('酒单生成成功！');
        } else {
          message.error('生成失败: ' + (data.message || '未知错误'));
        }
      } catch (error) {
        console.error('生成失败:', error);
        message.error('生成失败，请重试');
      } finally {
        loading.value = false;
      }
    };
    
    const getIngredientName = (ingredientId, comboIngredients) => {
      const ingredient = comboIngredients.find(ing => ing.id === ingredientId);
      return ingredient ? (ingredient.name_zh || ingredient.name) : ingredientId;
    };
    
    const shareCombination = (combo) => {
      // 生成分享链接
      const shareUrl = `${window.location.origin}${window.location.pathname}?recipe_id=${combo.id || 'generated'}`;
      
      // 复制到剪贴板
      navigator.clipboard.writeText(shareUrl)
        .then(() => {
          message.success('分享链接已复制到剪贴板');
        })
        .catch(err => {
          console.error('复制失败:', err);
          message.error('复制失败，请手动复制链接');
        });
    };
    
    const openComboModal = (combo) => {
      selectedCombo.value = combo;
      showComboModal.value = true;
    };
    
    // 监听风味偏好变化，更新饼图
    watch(
      () => flavorPreferences.value,
      () => {
        updateFlavorChart();
      },
      { deep: true }
    );
    
    // 组件挂载时初始化饼图
    onMounted(() => {
      nextTick(() => {
        initFlavorChart();
      });
    });
    
    return {
      selectedIngredients,
      scene,
      creativityLevel,
      flavorPreferences,
      loading,
      combinations,
      showIngredientModal,
      ingredientSearch,
      selectedCategory,
      ingredients,
      loadingIngredients,
      filteredIngredients,
      ingredientCategories,
      creativityLabels,
      flavorMap,
      sceneOptions,
      flavorTypes,
      flavorChartRef,
      showComboModal,
      selectedCombo,
      renderMarkdown,
      extractRecipeName,
      openIngredientModal,
      openComboModal,
      addIngredient,
      removeIngredient,
      isIngredientSelected,
      handleIngredientCheck,
      filterIngredients,
      generateCombinations,
      getIngredientName,
      shareCombination,
      getRoleName
    };
  }
};
</script>

<style scoped>
/* 全局变量 */
:root {
  --bg-primary: #0d0a08;
  --bg-secondary: #1a1410;
  --bg-card: rgba(26, 20, 16, 0.9);
  --color-gold-100: rgba(212, 175, 55, 0.1);
  --color-gold-200: rgba(212, 175, 55, 0.2);
  --color-gold-300: rgba(212, 175, 55, 0.6);
  --color-gold-400: #d4af37;
  --color-gold-500: #b8941f;
  --color-accent-1: #ff6b6b;
  --color-accent-2: #4ecdc4;
  --color-accent-3: #45b7d1;
  --color-text-primary: #e8e6e3;
  --color-text-secondary: #a8a399;
  --color-text-tertiary: #7a756b;
  --color-border-subtle: rgba(212, 175, 55, 0.2);
  --color-border-strong: rgba(212, 175, 55, 0.4);
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --spacing-xs: 8px;
  --spacing-sm: 16px;
  --spacing-md: 24px;
  --spacing-lg: 32px;
  --spacing-xl: 48px;
  --spacing-2xl: 64px;
  --font-display: 'Playfair Display', serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.4);
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 28px;
  --font-size-4xl: 36px;
  --font-size-5xl: 42px;
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.6;
  --letter-spacing-tight: -0.025em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.05em;
  --letter-spacing-wider: 0.15em;
}

.innovation-generator {
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  min-height: 100vh;
  padding: var(--spacing-xl) var(--spacing-lg);
  position: relative;
  font-family: var(--font-body);
  color: var(--color-text-primary);
  overflow-x: hidden;
}

/* 增强的背景纹理 */
.innovation-generator::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 80%, rgba(212, 175, 55, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 107, 107, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(78, 205, 196, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 60% 60%, rgba(69, 183, 209, 0.03) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

/* 顶部标题区域 */
.hero-section {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
  position: relative;
  z-index: 1;
  padding: var(--spacing-xl) 0;
}

.main-title {
  font-family: var(--font-display);
  font-size: var(--font-size-5xl);
  font-weight: 700;
  color: var(--color-gold-400);
  margin-bottom: var(--spacing-md);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wider);
  text-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
  position: relative;
  display: inline-block;
  line-height: var(--line-height-tight);
}

.main-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 10%;
  right: 10%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
  border-radius: 1px;
  transform: scaleX(0);
  transition: transform var(--transition-normal);
}

.hero-section:hover .main-title::after {
  transform: scaleX(1);
}

.main-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0 0 var(--spacing-lg) 0;
  letter-spacing: var(--letter-spacing-wide);
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: var(--line-height-relaxed);
}

.hero-accent {
  width: 160px;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
  margin: 0 auto;
  border-radius: 2px;
  position: relative;
  overflow: hidden;
}

.hero-accent::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.8), transparent);
  animation: shimmer 3s infinite;
}

@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}

/* 主内容卡片 */
.main-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl);
  border: 1px solid var(--color-border-subtle);
  margin-bottom: var(--spacing-2xl);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow-lg);
  position: relative;
  z-index: 1;
  transition: all var(--transition-normal);
  overflow: hidden;
}

.main-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-accent-1), var(--color-accent-2), var(--color-accent-3));
  transform: scaleX(0);
  transition: transform var(--transition-normal);
}

.main-card:hover {
  border-color: var(--color-gold-300);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
  transform: translateY(-4px);
}

.main-card:hover::before {
  transform: scaleX(1);
}

/* 表单组 */
.form-group {
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-xl);
  border-bottom: 1px solid var(--color-border-subtle);
  position: relative;
  transition: all var(--transition-normal);
}

.form-group:hover {
  border-color: var(--color-border-strong);
}

.form-group:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.group-header {
  margin-bottom: var(--spacing-lg);
  position: relative;
}

.group-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-gold-400);
  margin-bottom: var(--spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: inline-block;
  position: relative;
}

.group-title::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 0;
  width: 40px;
  height: 2px;
  background: var(--color-gold-400);
  border-radius: 1px;
  transition: width var(--transition-normal);
}

.form-group:hover .group-title::after {
  width: 80px;
}

.group-description {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.6;
  max-width: 600px;
}

/* 原料选择 */
.ingredient-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  align-items: center;
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.ingredient-selector:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.03);
}

.selected-ingredient {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  color: #000000;
  font-weight: 600;
  border: none;
  border-radius: var(--radius-sm);
  padding: 6px 16px;
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.selected-ingredient::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left var(--transition-normal);
}

.selected-ingredient:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
}

.selected-ingredient:hover::before {
  left: 100%;
}

.add-ingredient-btn {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  border: none;
  color: #000000;
  font-weight: 600;
  border-radius: var(--radius-sm);
  transition: all var(--transition-normal);
  padding: 10px 20px;
  position: relative;
  overflow: hidden;
}

.add-ingredient-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left var(--transition-normal);
}

.add-ingredient-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(212, 175, 55, 0.4);
}

.add-ingredient-btn:hover::before {
  left: 100%;
}

/* 场景选择 */
.scene-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.scene-selector:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.03);
}

.scene-selector .ant-tag {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-primary);
  border-radius: var(--radius-sm);
  padding: 8px 18px;
  transition: all var(--transition-normal);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  font-weight: 500;
}

.scene-selector .ant-tag::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.2), transparent);
  transition: left var(--transition-normal);
}

.scene-selector .ant-tag:hover {
  border-color: var(--color-gold-300);
  color: var(--color-gold-400);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.scene-selector .ant-tag:hover::before {
  left: 100%;
}

.scene-selector .ant-tag.active {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  color: #000000;
  border: none;
  font-weight: 600;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
}

.scene-selector .ant-tag.active::before {
  left: 100%;
}

/* 风味偏好容器 */
.flavor-container {
  display: flex;
  gap: var(--spacing-xl);
  margin-top: var(--spacing-md);
  align-items: flex-start;
  flex-wrap: wrap;
  padding: var(--spacing-md);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.flavor-container:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.03);
}

.flavor-adjustments {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.flavor-slider {
  transition: all var(--transition-normal);
  margin-bottom: var(--spacing-sm);
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--color-border-subtle);
}

.flavor-slider:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.03);
}

.slider-container {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.flavor-label {
  color: var(--color-text-primary);
  font-weight: 500;
  font-size: 14px;
  letter-spacing: 0.05em;
  min-width: 70px;
  text-transform: capitalize;
}

.flavor-value {
  color: var(--color-gold-400);
  font-weight: 600;
  font-size: 14px;
  min-width: 60px;
  text-align: right;
  background: rgba(212, 175, 55, 0.1);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

/* 饼图容器 */
.flavor-chart {
  width: 350px;
  height: 350px;
  flex-shrink: 0;
  transition: all var(--transition-normal);
  position: relative;
}

.flavor-chart:hover {
  transform: scale(1.03);
  filter: drop-shadow(0 8px 24px rgba(212, 175, 55, 0.2));
}

.chart-container {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-md);
  background: rgba(26, 20, 16, 0.9);
  border: 1px solid var(--color-border-subtle);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--color-accent-1), var(--color-accent-2), var(--color-accent-3), var(--color-accent-1));
  transform: scaleX(0);
  transition: transform var(--transition-normal);
  background-size: 200% 100%;
  animation: gradientAnimation 3s linear infinite;
}

.chart-container:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-lg);
  background: rgba(26, 20, 16, 0.95);
}

.chart-container:hover::before {
  transform: scaleX(1);
}

/* 图表标题 */
.chart-title {
  position: absolute;
  top: var(--spacing-sm);
  left: 50%;
  transform: translateX(-50%);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  letter-spacing: var(--letter-spacing-wide);
  text-transform: uppercase;
  background: rgba(13, 10, 8, 0.8);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
  z-index: 10;
  transition: all var(--transition-normal);
}

.chart-container:hover .chart-title {
  color: var(--color-gold-400);
  border-color: var(--color-gold-300);
}

/* 图表加载动画 */
.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-subtle);
  border-top: 3px solid var(--color-gold-400);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  z-index: 5;
}

@keyframes gradientAnimation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes spin {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

/* 自定义滑块样式 */
.custom-slider {
  flex: 1;
  max-width: 350px;
}

:deep(.custom-slider .ant-slider-track) {
  height: 8px;
  border-radius: 4px;
  box-shadow: 0 0 8px rgba(212, 175, 55, 0.4);
  transition: all var(--transition-normal);
}

:deep(.custom-slider .ant-slider-rail) {
  background: rgba(255, 255, 255, 0.1);
  height: 8px;
  border-radius: 4px;
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

:deep(.custom-slider .ant-slider-handle) {
  background: var(--color-gold-400);
  border: 3px solid var(--bg-secondary);
  width: 20px;
  height: 20px;
  margin-top: -7px;
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.6);
  transition: all var(--transition-normal);
  border-radius: 50%;
  position: relative;
  overflow: hidden;
}

:deep(.custom-slider .ant-slider-handle::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left var(--transition-normal);
}

:deep(.custom-slider .ant-slider-handle:hover) {
  transform: scale(1.3);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.6);
}

:deep(.custom-slider .ant-slider-handle:hover::before) {
  left: 100%;
}

:deep(.custom-slider .ant-slider-handle:focus) {
  box-shadow: 0 0 0 3px var(--color-gold-300);
  transform: scale(1.2);
}

/* 风味类型滑块颜色 */
:deep(.slider-sour .ant-slider-track) {
  background: #FF6B6B;
}

:deep(.slider-sweet .ant-slider-track) {
  background: #4ECDC4;
}

:deep(.slider-bitter .ant-slider-track) {
  background: #45B7D1;
}

:deep(.slider-aroma .ant-slider-track) {
  background: #96CEB4;
}

:deep(.slider-fruity .ant-slider-track) {
  background: #FFEAA7;
}

:deep(.slider-body .ant-slider-track) {
  background: #DDA0DD;
}

:deep(.slider-sour .ant-slider-handle) {
  background: #FF6B6B !important;
}

:deep(.slider-sweet .ant-slider-handle) {
  background: #4ECDC4 !important;
}

:deep(.slider-bitter .ant-slider-handle) {
  background: #45B7D1 !important;
}

:deep(.slider-aroma .ant-slider-handle) {
  background: #96CEB4 !important;
}

:deep(.slider-fruity .ant-slider-handle) {
  background: #FFEAA7 !important;
}

:deep(.slider-body .ant-slider-handle) {
  background: #DDA0DD !important;
}

/* 生成按钮 */
.action-section {
  display: flex;
  justify-content: center;
  margin-top: var(--spacing-xl);
  padding-top: var(--spacing-xl);
  border-top: 1px solid var(--color-border-subtle);
  position: relative;
}

.action-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 20%;
  right: 20%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-border-strong), transparent);
}

.generate-button {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  border: none;
  color: #000000;
  font-weight: 700;
  padding: var(--spacing-lg) var(--spacing-2xl);
  font-size: 18px;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  border-radius: var(--radius-lg);
  transition: all var(--transition-normal);
  box-shadow: 0 8px 24px rgba(212, 175, 55, 0.4);
  min-width: 280px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
}

.generate-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left var(--transition-slow);
}

.generate-button:hover:not(:disabled) {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(212, 175, 55, 0.5);
}

.generate-button:hover:not(:disabled)::before {
  left: 100%;
}

.generate-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.generate-button:active:not(:disabled) {
  transform: translateY(-2px) scale(0.98);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
  transition: all 0.1s ease;
}

/* 交互反馈增强 */
.ant-tag {
  transition: all var(--transition-normal);
}

.ant-btn {
  transition: all var(--transition-normal);
}

.ant-input {
  transition: all var(--transition-normal);
}

.ant-input:hover {
  border-color: var(--color-gold-300);
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.1);
}

.ant-input:focus {
  border-color: var(--color-gold-400);
  box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2);
}

.ant-checkbox:hover .ant-checkbox-inner {
  border-color: var(--color-gold-300);
}

.ant-checkbox-checked .ant-checkbox-inner {
  background-color: var(--color-gold-400);
  border-color: var(--color-gold-400);
}

.ant-modal {
  transition: all var(--transition-normal);
}

.ant-modal-content {
  transition: all var(--transition-normal);
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--color-gold-400);
  border-radius: 4px;
  transition: all var(--transition-fast);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-gold-300);
  transform: scaleX(1.2);
}

/* 选择文本样式 */
::selection {
  background: var(--color-gold-400);
  color: #000000;
}

::-moz-selection {
  background: var(--color-gold-400);
  color: #000000;
}

/* 方案详情模态框 */
.combo-detail {
  padding: var(--spacing-md) 0;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-subtle);
}

.detail-rank {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.1);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.detail-section {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
}

.detail-title {
  font-family: var(--font-display);
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--color-gold-400);
  margin-bottom: var(--spacing-md);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.detail-item:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.03);
}

.detail-name {
  font-weight: 500;
  color: var(--color-text-primary);
}

.detail-role {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  background: rgba(212, 175, 55, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.detail-flavor-bars {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-flavor-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.detail-flavor-key {
  min-width: 80px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.detail-bar-container {
  flex: 1;
  height: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--color-border-subtle);
}

.detail-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-gold-500), var(--color-gold-400));
  border-radius: 6px;
  transition: width var(--transition-normal);
}

.detail-flavor-value {
  min-width: 60px;
  text-align: right;
  font-weight: 600;
  color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.detail-proportion-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-proportion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.detail-proportion-item:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.03);
}

.detail-proportion-name {
  font-weight: 500;
  color: var(--color-text-primary);
}

.detail-proportion-value {
  font-weight: 600;
  color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.detail-recipe-content {
  padding: var(--spacing-lg);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  line-height: var(--line-height-relaxed);
  color: var(--color-text-primary);
  font-family: var(--font-body);
}

.detail-recipe-content h1,
.detail-recipe-content h2,
.detail-recipe-content h3 {
  color: var(--color-gold-400);
  margin-top: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  font-family: var(--font-display);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-sm);
}

.detail-recipe-content h1 {
  font-size: var(--font-size-xl);
}

.detail-recipe-content h2 {
  font-size: var(--font-size-lg);
}

.detail-recipe-content h3 {
  font-size: var(--font-size-md);
}

.detail-recipe-content p {
  margin-bottom: var(--spacing-md);
  text-align: justify;
}

.detail-recipe-content ul,
.detail-recipe-content ol {
  margin-bottom: var(--spacing-md);
  padding-left: var(--spacing-xl);
}

.detail-recipe-content li {
  margin-bottom: var(--spacing-sm);
  position: relative;
}

.detail-recipe-content ul li::before {
  content: '•';
  color: var(--color-gold-400);
  font-weight: bold;
  position: absolute;
  left: -20px;
}

.detail-recipe-content ol li {
  counter-increment: list-item;
}

.detail-recipe-content ol li::before {
  content: counter(list-item) '.';
  color: var(--color-gold-400);
  font-weight: bold;
  position: absolute;
  left: -25px;
}

.detail-recipe-content strong {
  color: var(--color-gold-400);
  font-weight: 600;
}

.detail-recipe-content em {
  color: var(--color-text-secondary);
  font-style: italic;
}

.detail-recipe-content hr {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-border-strong), transparent);
  margin: var(--spacing-lg) 0;
}

/* 生成结果 */
.results-section {
  margin-top: var(--spacing-2xl);
  position: relative;
  z-index: 1;
  padding: var(--spacing-xl) 0;
}

.results-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--color-gold-400);
  margin-bottom: var(--spacing-xl);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-align: center;
  position: relative;
  display: inline-block;
  left: 50%;
  transform: translateX(-50%);
}

.results-title::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 10%;
  right: 10%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
  border-radius: 1px;
  transform: scaleX(0);
  transition: transform var(--transition-normal);
}

.results-section:hover .results-title::after {
  transform: scaleX(1);
}

.combinations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--spacing-xl);
  margin-top: var(--spacing-xl);
  padding: 0 var(--spacing-sm);
}

/* 布局辅助类 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flex-column {
  display: flex;
  flex-direction: column;
}

.gap-sm {
  gap: var(--spacing-sm);
}

.gap-md {
  gap: var(--spacing-md);
}

.gap-lg {
  gap: var(--spacing-lg);
}

.combination-card {
  background: var(--bg-card);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-normal);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: relative;
  box-shadow: var(--shadow-md);
  cursor: pointer;
  max-height: 600px;
  display: flex;
  flex-direction: column;
}

.combination-card:hover {
  border-color: var(--color-gold-300);
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
}

.combination-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-accent-1), var(--color-accent-2), var(--color-accent-3));
  transform: scaleX(0);
  transition: transform var(--transition-normal);
}

.combination-card:hover {
  border-color: var(--color-gold-300);
  transform: translateY(-10px);
  box-shadow: var(--shadow-lg);
}

.combination-card:hover::before {
  transform: scaleX(1);
}

.card-header {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  padding: var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.card-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left var(--transition-normal);
}

.combination-card:hover .card-header::before {
  left: 100%;
}

.card-badge {
  position: absolute;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  z-index: 1;
}

.creativity-badge {
  background: rgba(0, 0, 0, 0.2);
  color: #000000;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: var(--radius-sm);
  padding: 4px 12px;
  font-size: 12px;
  transition: all var(--transition-fast);
}

.creativity-badge:hover {
  background: rgba(0, 0, 0, 0.3);
  transform: scale(1.05);
}

.combo-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: #000000;
  margin: 0;
  letter-spacing: 0.05em;
  flex: 1;
  padding-right: 80px;
}

.combo-rank {
  background: rgba(0, 0, 0, 0.2);
  color: #000000;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  transition: all var(--transition-fast);
}

.combo-rank:hover {
  background: rgba(0, 0, 0, 0.3);
  transform: scale(1.05);
}

.card-body {
  padding: var(--spacing-lg);
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}

.list-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-gold-400);
  margin-bottom: var(--spacing-md);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-sm);
  position: relative;
}

.list-title::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 40px;
  height: 2px;
  background: var(--color-gold-400);
  border-radius: 1px;
  transition: width var(--transition-normal);
}

.combination-card:hover .list-title::after {
  width: 80px;
}

.ingredients-list {
  margin-bottom: var(--spacing-lg);
}

.ingredient-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-sm);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.ingredient-item:hover {
  border-color: var(--color-gold-300);
  background: rgba(212, 175, 55, 0.05);
  transform: translateX(4px);
}

.ingredient-name {
  color: var(--color-text-primary);
  font-weight: 500;
}

.ingredient-role {
  color: var(--color-gold-400);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(212, 175, 55, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.flavor-profile {
  margin-bottom: var(--spacing-lg);
}

.flavor-bars {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.flavor-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.flavor-bar:hover {
  border-color: var(--color-border-strong);
  background: rgba(255, 255, 255, 0.03);
}

.flavor-key {
  width: 70px;
  color: var(--color-text-secondary);
  font-size: 12px;
  text-transform: capitalize;
  font-weight: 500;
}

.bar-container {
  flex: 1;
  height: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 5px;
  overflow: hidden;
  border: 1px solid var(--color-border-subtle);
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-gold-400), var(--color-gold-500));
  transition: width var(--transition-slow);
  border-radius: 4px;
}

.flavor-value {
  width: 50px;
  text-align: right;
  color: var(--color-gold-400);
  font-size: 12px;
  font-weight: 600;
  background: rgba(212, 175, 55, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.proportions {
  margin-bottom: var(--spacing-lg);
}

.proportion-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.proportion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
}

.proportion-item:hover {
  border-color: var(--color-gold-300);
  background: rgba(212, 175, 55, 0.05);
  transform: translateX(4px);
}

.proportion-name {
  color: var(--color-text-primary);
  font-size: 12px;
  font-weight: 500;
}

.proportion-value {
  color: var(--color-gold-400);
  font-weight: 600;
  font-size: 12px;
  background: rgba(212, 175, 55, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
}

.recipe {
  margin-bottom: var(--spacing-lg);
}

.recipe-content {
  color: var(--color-text-primary);
  font-size: 13px;
  line-height: 1.6;
  background: rgba(255, 255, 255, 0.02);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-subtle);
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
  transition: all var(--transition-normal);
  position: relative;
}

.recipe-content:hover {
  border-color: var(--color-gold-300);
  background: rgba(212, 175, 55, 0.05);
}

.recipe-content::-webkit-scrollbar {
  width: 6px;
}

.recipe-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.recipe-content::-webkit-scrollbar-thumb {
  background: var(--color-gold-400);
  border-radius: 3px;
  transition: all var(--transition-fast);
}

.recipe-content::-webkit-scrollbar-thumb:hover {
  background: var(--color-gold-300);
  transform: scaleX(1.2);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border-subtle);
  background: linear-gradient(135deg, rgba(26, 20, 16, 0.95), rgba(34, 24, 18, 0.95));
  transition: all var(--transition-normal);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
}

.combination-card:hover .card-footer {
  border-color: var(--color-border-strong);
  box-shadow: 0 -4px 16px rgba(212, 175, 55, 0.1);
}

.card-footer-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.card-footer-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.card-footer .ant-btn {
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-md);
  font-weight: 500;
}

.card-footer .ant-btn-link {
  color: var(--color-gold-400);
  font-weight: 500;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.card-footer .ant-btn-link::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: var(--color-gold-400);
  transform: scaleX(0);
  transition: transform var(--transition-normal);
}

.card-footer .ant-btn-link:hover {
  color: var(--color-gold-300);
  text-decoration: none;
  transform: translateY(-2px);
}

.card-footer .ant-btn-link:hover::before {
  transform: scaleX(1);
}

.card-footer .ant-btn-primary {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  border: none;
  color: #000000;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
  transition: all var(--transition-normal);
}

.card-footer .ant-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
}

.card-footer .ant-btn-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
}

/* 原料选择模态框 */
.ingredient-modal {
  max-height: 600px;
  overflow-y: auto;
  padding: var(--spacing-sm);
  background: linear-gradient(135deg, rgba(26, 20, 16, 0.95), rgba(34, 24, 18, 0.95));
  border-radius: var(--radius-lg);
}

.search-input {
  margin-bottom: var(--spacing-md);
  transition: all var(--transition-normal);
  border-radius: var(--radius-md);
}

.search-input:hover {
  box-shadow: 0 0 0 2px var(--color-gold-300);
}

.ingredient-categories {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-md);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
  backdrop-filter: blur(10px);
}

.ingredient-categories:hover {
  border-color: var(--color-border-strong);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.02));
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.1);
}

.ingredient-categories .ant-tag {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-primary);
  border-radius: var(--radius-sm);
  padding: 8px 18px;
  transition: all var(--transition-normal);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  font-weight: 500;
  backdrop-filter: blur(5px);
}

.ingredient-categories .ant-tag::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.2), transparent);
  transition: left var(--transition-normal);
}

.ingredient-categories .ant-tag:hover {
  border-color: var(--color-gold-300);
  color: var(--color-gold-400);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.ingredient-categories .ant-tag:hover::before {
  left: 100%;
}

.ingredient-categories .ant-tag.active {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400));
  color: #000000;
  border: none;
  font-weight: 600;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
}

.ingredient-categories .ant-tag.active::before {
  left: 100%;
}

.ingredient-list {
  max-height: 400px;
  overflow-y: auto;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
  backdrop-filter: blur(10px);
}

.ingredient-list::-webkit-scrollbar {
  width: 6px;
}

.ingredient-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.ingredient-list::-webkit-scrollbar-thumb {
  background: var(--color-gold-400);
  border-radius: 3px;
  transition: all var(--transition-fast);
}

.ingredient-list::-webkit-scrollbar-thumb:hover {
  background: var(--color-gold-300);
  transform: scaleX(1.2);
}

.ingredient-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.01);
}

.ingredient-option::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.1), transparent);
  transition: left var(--transition-normal);
}

.ingredient-option:hover {
  background: rgba(212, 175, 55, 0.1);
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(212, 175, 55, 0.1);
}

.ingredient-option:hover::before {
  left: 100%;
}

.ingredient-option:last-child {
  border-bottom: none;
}

.option-info {
  flex: 1;
  padding-right: var(--spacing-md);
}

.option-name {
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
  font-size: 14px;
  transition: color var(--transition-normal);
}

.ingredient-option:hover .option-name {
  color: var(--color-gold-400);
}

.option-role {
  font-size: 12px;
  color: var(--color-text-secondary);
  background: rgba(212, 175, 55, 0.1);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  display: inline-block;
  transition: all var(--transition-normal);
  border: 1px solid var(--color-border-subtle);
}

.ingredient-option:hover .option-role {
  background: rgba(212, 175, 55, 0.2);
  border-color: var(--color-gold-300);
  color: var(--color-gold-400);
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--spacing-xl);
  min-height: 200px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  backdrop-filter: blur(10px);
  position: relative;
  overflow: hidden;
}

.loading-state::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.1), transparent);
  animation: loadingAnimation 1.5s ease-in-out infinite;
}

@keyframes loadingAnimation {
  0% { left: -100%; }
  100% { left: 100%; }
}

.empty-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: var(--spacing-xl);
  min-height: 200px;
  color: var(--color-text-secondary);
  text-align: center;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  backdrop-filter: blur(10px);
  transition: all var(--transition-normal);
}

.empty-state:hover {
  border-color: var(--color-gold-300);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.02));
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.1);
}

.empty-state-icon {
  width: 64px;
  height: 64px;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
  transition: opacity var(--transition-normal);
}

.empty-state:hover .empty-state-icon {
  opacity: 0.8;
}

.empty-state-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  transition: color var(--transition-normal);
}

.empty-state:hover .empty-state-title {
  color: var(--color-gold-400);
}

.empty-state-desc {
  font-size: 14px;
  line-height: 1.6;
  max-width: 300px;
  transition: color var(--transition-normal);
}

.empty-state:hover .empty-state-desc {
  color: var(--color-text-primary);
}

/* 深色模态框 */
:deep(.dark-modal) {
  background: rgba(13, 10, 8, 0.95) !important;
  border: 1px solid var(--color-border-subtle) !important;
  border-radius: var(--radius-lg) !important;
}

:deep(.dark-modal .ant-modal-content) {
  background: rgba(26, 20, 16, 0.95) !important;
  border: 1px solid var(--color-border-subtle) !important;
  border-radius: var(--radius-lg) !important;
}

:deep(.dark-modal .ant-modal-header) {
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%) !important;
  border-bottom: 1px solid var(--color-border-subtle) !important;
}

:deep(.dark-modal .ant-modal-title) {
  color: var(--color-gold-400) !important;
  font-family: var(--font-display) !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

:deep(.dark-modal .ant-modal-body) {
  background: rgba(26, 20, 16, 0.95) !important;
  color: var(--color-text-primary) !important;
}

:deep(.dark-modal .ant-input) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid var(--color-border-subtle) !important;
  color: var(--color-text-primary) !important;
  border-radius: var(--radius-sm) !important;
}

:deep(.dark-modal .ant-input::placeholder) {
  color: var(--color-text-secondary) !important;
}

:deep(.dark-modal .ant-checkbox-checked .ant-checkbox-inner) {
  background-color: var(--color-gold-400) !important;
  border-color: var(--color-gold-400) !important;
}

:deep(.dark-modal .ant-checkbox-inner) {
  border-color: var(--color-border-subtle) !important;
  background: rgba(255, 255, 255, 0.05) !important;
}

:deep(.dark-modal .ant-modal-footer) {
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%) !important;
  border-top: 1px solid var(--color-border-subtle) !important;
}

:deep(.dark-modal .ant-btn) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid var(--color-border-subtle) !important;
  color: var(--color-text-primary) !important;
  border-radius: var(--radius-sm) !important;
}

:deep(.dark-modal .ant-btn-primary) {
  background: linear-gradient(135deg, var(--color-gold-500), var(--color-gold-400)) !important;
  border: none !important;
  color: #000000 !important;
  font-weight: 600 !important;
}

/* 确保模态框遮罩也是深色 */
:deep(.dark-modal .ant-modal-mask) {
  background: rgba(0, 0, 0, 0.8) !important;
}

/* 全局动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes float {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
  100% {
    transform: translateY(0px);
  }
}

/* 应用动画效果 */
.hero-section {
  animation: fadeIn 1s ease-out;
}

.main-card {
  animation: fadeIn 1s ease-out 0.2s both;
}

.results-section {
  animation: fadeIn 1s ease-out 0.4s both;
}

.combination-card {
  animation: fadeIn 0.8s ease-out;
  animation-fill-mode: both;
}

.combination-card:nth-child(1) {
  animation-delay: 0.1s;
}

.combination-card:nth-child(2) {
  animation-delay: 0.2s;
}

.combination-card:nth-child(3) {
  animation-delay: 0.3s;
}

.combination-card:nth-child(4) {
  animation-delay: 0.4s;
}

.generate-button {
  animation: pulse 2s infinite;
}

.generate-button:hover {
  animation: none;
}

/* 响应式设计 */
@media (max-width: 1440px) {
  .innovation-generator {
    padding: var(--spacing-lg);
  }
  
  .main-title {
    font-size: 36px;
  }
  
  .combinations-grid {
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: var(--spacing-lg);
  }
  
  .flavor-chart {
    width: 300px;
    height: 300px;
  }
}

@media (max-width: 1200px) {
  .main-card {
    padding: var(--spacing-lg);
  }
  
  .flavor-container {
    flex-direction: column;
    align-items: center;
  }
  
  .flavor-chart {
    width: 100%;
    max-width: 400px;
    height: 350px;
    margin: 0 auto;
  }
  
  .combinations-grid {
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  }
}

@media (max-width: 768px) {
  .innovation-generator {
    padding: var(--spacing-md);
  }
  
  .main-title {
    font-size: 28px;
  }
  
  .main-subtitle {
    font-size: 16px;
  }
  
  .main-card {
    padding: var(--spacing-md);
  }
  
  .form-group {
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
  }
  
  .combinations-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-lg);
    padding: 0;
  }
  
  .slider-container {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .custom-slider {
    width: 100%;
    max-width: 100%;
  }
  
  .flavor-value {
    align-self: flex-end;
    min-width: auto;
  }
  
  .generate-button {
    padding: var(--spacing-md) var(--spacing-lg);
    font-size: 16px;
  }
  
  .scene-selector {
    justify-content: center;
  }
  
  .ingredient-selector {
    justify-content: center;
  }
  
  .flavor-container {
    flex-direction: column;
  }
  
  .flavor-chart {
    width: 100%;
    max-width: 300px;
    height: 300px;
    margin: 0 auto;
  }
}

@media (max-width: 480px) {
  .innovation-generator {
    padding: var(--spacing-sm);
  }
  
  .main-title {
    font-size: 24px;
  }
  
  .main-subtitle {
    font-size: 14px;
  }
  
  .main-card {
    padding: var(--spacing-sm);
  }
  
  .form-group {
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
  }
  
  .ingredient-selector {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .scene-selector {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .scene-selector .ant-tag {
    width: 100%;
    text-align: center;
  }
  
  .generate-button {
    min-width: 200px;
    font-size: 16px;
    padding: var(--spacing-md) var(--spacing-lg);
  }
  
  .card-header {
    padding: var(--spacing-md);
  }
  
  .combo-name {
    font-size: 16px;
  }
  
  .card-body {
    padding: var(--spacing-md);
  }
  
  .card-footer {
    flex-direction: column;
    align-items: flex-end;
  }
}
</style>
