<template>
  <div class="visualization">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载配方数据中...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">加载失败</h2>
      <p class="error-message">{{ error }}</p>
      <button class="btn btn-primary" @click="fetchRecipeData">重新加载</button>
    </div>
    
    <!-- 配方内容 -->
    <template v-else>
      <!-- 页面头部 -->
      <header class="page-header">
        <div class="container">
          <div class="page-header-content">
            <h1 class="page-title">配方详情</h1>
            <p class="page-subtitle">深入分析配方的风味特性</p>
          </div>
        </div>
      </header>
      
      <!-- 配方头部信息区 -->
      <section class="recipe-header-section">
        <div class="container">
          <div class="recipe-header-card card">
            <div class="recipe-header-content">
              <div class="recipe-header-info">
                <h2 class="recipe-name">
                  <span v-if="recipe?.recipe_name_zh && recipe?.name" class="name-zh">{{ recipe.recipe_name_zh }}</span>
                  <span v-if="recipe?.recipe_name_zh && recipe?.name" class="name-separator"> / </span>
                  <span v-if="recipe?.name" class="name-en">{{ recipe.name }}</span>
                  <span v-if="!recipe?.recipe_name_zh && !recipe?.name">莫吉托</span>
                </h2>
                <p class="recipe-subtitle">{{ recipe?.instructions || '清爽型经典鸡尾酒' }}</p>
                <div class="recipe-meta">
                  <div class="recipe-meta-item">
                    <i class="meta-icon">🥃</i>
                    <span class="meta-label">玻璃类型</span>
                    <span class="meta-value">{{ recipe?.glass || '高ball杯' }}</span>
                  </div>
                  <div class="recipe-meta-item">
                    <i class="meta-icon">🏷️</i>
                    <span class="meta-label">标签</span>
                    <span class="meta-value">{{ recipe?.tags?.join(', ') || '经典, 清爽, 古巴' }}</span>
                  </div>
                  <div class="recipe-meta-item">
                    <i class="meta-icon">🍷</i>
                    <span class="meta-label">酒精含量</span>
                    <span class="meta-value">{{ recipe?.is_alcoholic ? '含酒精' : '无酒精' }}</span>
                  </div>
                </div>
              </div>
              <div class="recipe-header-image">
                <img 
                  :src="recipe?.image_url || 'https://example.com/margarita.jpg'" 
                  :alt="recipe?.name || '莫吉托'"
                  class="recipe-image"
                />
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- 主要内容区 -->
      <section class="main-content-section">
        <div class="container">
          <!-- 第一行：原料结构 + SQE分析 + 风味分布 + 关键风味识别 -->
          <div class="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
            <!-- 原料结构 -->
            <div class="lg:col-span-1">
              <div class="ingredient-structure card">
                <h3 class="card-title">原料结构</h3>
                <div class="ingredient-groups">
                  <div 
                    v-for="(group, type) in ingredientsByType" 
                    :key="type"
                    class="ingredient-group"
                  >
                    <div class="group-header">
                      <h4 class="group-title">{{ type }}</h4>
                      <span class="group-count">{{ group.length }} 种</span>
                    </div>
                    <div class="group-ingredients">
                      <div 
                        v-for="(ingredient, index) in group" 
                        :key="ingredient.ingredient_id || index"
                        :class="['ingredient-item', { selected: selectedIngredient?.ingredient?.ingredient_id === ingredient.ingredient?.ingredient_id || selectedIngredient === ingredient }]"
                        @click="selectIngredient(ingredient)"
                      >
                        <div class="ingredient-header">
                          <h5 class="ingredient-name">
                          <span v-if="ingredient.ingredient?.canonical_name_zh" class="name-zh">{{ ingredient.ingredient.canonical_name_zh }}</span>
                          <span v-if="ingredient.ingredient?.canonical_name_zh && ingredient.ingredient?.canonical_name" class="name-separator"> / </span>
                          <span v-if="ingredient.ingredient?.canonical_name" class="name-en">{{ ingredient.ingredient.canonical_name }}</span>
                          <span v-if="!ingredient.ingredient?.canonical_name_zh && !ingredient.ingredient?.canonical_name">{{ ingredient.ingredient?.name_norm || ingredient.raw_text }}</span>
                        </h5>
                        </div>
                        <div class="ingredient-info">
                          <span class="ingredient-amount">{{ ingredient.amount }} {{ ingredient.unit }}</span>
                          <span class="ingredient-category" v-if="ingredient.ingredient">{{ ingredient.ingredient.category }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              

            </div>
            
            <!-- SQE分析 + 风味分布 -->
            <div class="lg:col-span-2">
              <div class="combined-card card">
                <h3 class="card-title">SQE 分析</h3>
                <div class="sqe-overall">
                  <div class="sqe-score">
                    <span class="score-number">{{ (sqe?.final_sqe_total || 0.82) * 10 }}</span>
                    <span class="score-label">{{ getScoreLabel(sqe?.final_sqe_total || 0.82) }}</span>
                  </div>
                  <div class="sqe-stats">
                    <div class="stat-item">
                      <span class="stat-label">排名</span>
                      <span class="stat-value">{{ sqe?.rank_in_snapshot || 1 }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">置信度</span>
                      <span class="stat-value">{{ (sqe?.phaseC_confidence || 0.9) * 100 }}%</span>
                    </div>
                  </div>
                </div>
                <div class="sqe-triple-bar">
                  <div class="triple-bar-container">
                    <div class="triple-bar-fill synergy-fill" :style="{ width: sqePercentages.synergy + '%' }">
                      <span class="triple-value">{{ sqePercentages.synergy.toFixed(1) }}%</span>
                    </div>
                    <div class="triple-bar-fill conflict-fill" :style="{ width: sqePercentages.conflict + '%' }">
                      <span class="triple-value">{{ sqePercentages.conflict.toFixed(1) }}%</span>
                    </div>
                    <div class="triple-bar-fill balance-fill" :style="{ width: sqePercentages.balance + '%' }">
                      <span class="triple-value">{{ sqePercentages.balance.toFixed(1) }}%</span>
                    </div>
                  </div>
                  <div class="triple-bar-legend">
                    <div class="legend-item">
                      <div class="legend-color synergy-color"></div>
                      <span class="legend-text">协同性 (Synergy)</span>
                    </div>
                    <div class="legend-item">
                      <div class="legend-color conflict-color"></div>
                      <span class="legend-text">冲突度 (Conflict)</span>
                    </div>
                    <div class="legend-item">
                      <div class="legend-color balance-color"></div>
                      <span class="legend-text">平衡性 (Balance)</span>
                    </div>
                  </div>
                </div>
                
                <h3 class="card-title mt-4">风味分布</h3>
                <div class="flavor-charts">
                  <!-- 风味雷达图 -->
                  <div class="radar-chart-container">
                    <div ref="flavorRadarChart" class="radar-chart-echarts"></div>
                  </div>
                  <!-- 风味条形图 -->
                  <div class="flavor-bars-container">
                    <div class="flavor-bars">
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">酸味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_sour || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_sour || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">甜味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_sweet || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_sweet || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">苦味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_bitter || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_bitter || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">香气</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_aroma || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_aroma || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">果味</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_fruity || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_fruity || 0) * 100).toFixed(0) }}%</span>
                      </div>
                      <div class="flavor-bar-item">
                        <span class="flavor-bar-label">酒体</span>
                        <div class="flavor-bar">
                          <div class="flavor-bar-fill" :style="{ width: (balance?.f_body || 0) * 100 + '%' }"></div>
                        </div>
                        <span class="flavor-bar-value">{{ ((balance?.f_body || 0) * 100).toFixed(0) }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <h3 class="card-title mt-4">所有原料的风味贡献</h3>
                <div class="contribution-chart-container" style="height: 400px;">
                  <div ref="ingredientContributionChart" class="contribution-chart"></div>
                </div>
              </div>
            </div>
            
            <!-- 关键风味识别 -->
            <div class="lg:col-span-1">
              <div class="key-flavors card">
                <h3 class="card-title">关键风味识别</h3>
                <div class="key-flavor-list">
                  <div 
                    v-for="(node, index) in keyNodes" 
                    :key="node.canonical_id || index"
                    :class="['key-flavor-item', `rank-${node.rank_no}`]"
                  >
                    <div class="key-flavor-header">
                      <span class="flavor-rank">{{ node.rank_no }}</span>
                      <span class="flavor-name">
                      <span v-if="node.ingredient_name_zh" class="name-zh">{{ node.ingredient_name_zh }}</span>
                      <span v-if="node.ingredient_name_zh && node.ingredient_name" class="name-separator"> / </span>
                      <span v-if="node.ingredient_name" class="name-en">{{ node.ingredient_name }}</span>
                    </span>
                      <span class="flavor-contribution">{{ node.normalized_contribution.toFixed(2) }}</span>
                    </div>
                    <div class="contribution-bar">
                      <div class="contribution-fill" :style="{ width: (node.normalized_contribution * 100) + '%' }"></div>
                    </div>
                    <div class="flavor-metrics">
                      <span class="metric">协同: {{ (node.base_score || 0).toFixed(2) }}</span>
                      <span class="metric">贡献: {{ (node.learned_contribution || 0).toFixed(2) }}</span>
                      <span class="metric">占比: {{ (node.contribution_ratio || 0).toFixed(2) }}</span>
                    </div>
                    <div class="flavor-explanation" v-if="node.explanation">
                      <p>{{ node.explanation }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 第二行：结构解释图 -->
          <div class="local-graph-section mb-6">
            <RecipeLocalGraph 
              v-if="graphData"
              :graph-data="graphData"
              :ingredients="ingredients"
              @node-click="handleGraphNodeClick"
              @view-substitutes="handleViewSubstitutes"
            />
            <div v-else class="graph-placeholder card">
              <div class="graph-placeholder-icon">📊</div>
              <p class="graph-placeholder-text">加载中...</p>
              <p class="graph-placeholder-subtext">正在获取结构解释图数据</p>
            </div>
          </div>
          
          <!-- 第三行：组合调整入口 -->
          <div class="adjust-entry-section mb-6">
            <div class="adjust-entry-card card">
              <div class="entry-content">
                <div class="entry-icon">🔄</div>
                <div class="entry-info">
                  <h3 class="entry-title">组合调整分析</h3>
                  <p class="entry-description">
                    探索原料替代的多种可能性，通过单步替代和组合调整优化配方
                  </p>
                </div>
                <router-link 
                  :to="{ path: '/adjust', query: { recipe_id: recipe?.recipe_id } }"
                  class="btn btn-primary"
                >
                  进入组合调整工作台
                </router-link>
              </div>
            </div>
          </div>
          
          <!-- 底部：操作区 -->
          <div class="action-section">
            <div class="action-buttons">
              <router-link 
                :to="{ path: '/graph', query: { recipe_id: recipe?.recipe_id } }"
                class="btn btn-primary"
              >
                查看全局风味图谱
              </router-link>
              <router-link 
                :to="{ path: '/adjust', query: { recipe_id: recipe?.recipe_id, target_canonical_id: selectedIngredient?.ingredient?.canonical_id } }"
                class="btn btn-secondary"
                v-if="selectedIngredient"
              >
                替代这个原料
              </router-link>
              <router-link 
                :to="{ path: '/generate', query: { recipe_id: recipe?.recipe_id } }"
                class="btn btn-secondary"
              >
                基于此配方生成变体
              </router-link>
              <router-link 
                to="/recipe"
                class="btn btn-outline"
              >
                返回配方列表
              </router-link>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import { fetchRecipe, fetchIngredients, fetchSQE, fetchBalance, fetchKeyNodes, fetchSubstitutes, fetchGraph } from '../api/recipeApi';
import RecipeLocalGraph from '../components/RecipeLocalGraph.vue';
import * as echarts from 'echarts';

export default {
  name: 'VisualizationView',
  components: {
    RecipeLocalGraph
  },
  data() {
    return {
      recipe: null,
      ingredients: [],
      sqe: null,
      balance: null,
      keyNodes: [],
      substitutes: [],
      selectedIngredient: null,
      graphData: null,
      graphLayer: 'mixed',
      loading: false,
      error: null,
      flavorRadarChart: null,
      ingredientContributionChart: null
    };
  },
  mounted() {
    this.fetchRecipeData();
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
      if (this.flavorRadarChart) {
        this.flavorRadarChart.dispose();
      }
      if (this.ingredientContributionChart) {
        // 移除图例点击事件监听器
        this.ingredientContributionChart.off('legendselectchanged');
        this.ingredientContributionChart.dispose();
      }
      window.removeEventListener('resize', this.handleResize);
    },
  methods: {
    initFlavorRadarChart() {
      if (!this.$refs.flavorRadarChart) {
        console.warn('flavorRadarChart ref not found');
        return false;
      }
      
      try {
        if (this.flavorRadarChart) {
          this.flavorRadarChart.dispose();
        }
        this.flavorRadarChart = echarts.init(this.$refs.flavorRadarChart);
        return true;
      } catch (error) {
        console.error('Error initializing flavor radar chart:', error);
        return false;
      }
    },
    
    updateFlavorRadarChart() {
      if (!this.balance) {
        console.warn('Balance data not available');
        return;
      }
      
      if (!this.flavorRadarChart) {
        if (!this.initFlavorRadarChart()) return;
      }
      
      const flavorData = [
        this.balance?.f_sour || 0,
        this.balance?.f_sweet || 0,
        this.balance?.f_bitter || 0,
        this.balance?.f_aroma || 0,
        this.balance?.f_fruity || 0,
        this.balance?.f_body || 0
      ];
      
      const option = {
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderColor: '#d4af37',
          textStyle: {
            color: '#fff'
          },
          formatter: function(params) {
            const data = params[0];
            const dimensions = ['酸味', '甜味', '苦味', '香气', '果味', '酒体'];
            let result = '<div style="font-weight:bold;margin-bottom:5px;">风味分布</div>';
            data.value.forEach((val, idx) => {
              result += `<div style="display:flex;justify-content:space-between;gap:15px;">
                <span>${dimensions[idx]}:</span>
                <span style="font-weight:bold;color:#d4af37">${(val * 100).toFixed(1)}%</span>
              </div>`;
            });
            return result;
          }
        },
        radar: {
          indicator: [
            { name: '酸味', max: 1 },
            { name: '甜味', max: 1 },
            { name: '苦味', max: 1 },
            { name: '香气', max: 1 },
            { name: '果味', max: 1 },
            { name: '酒体', max: 1 }
          ],
          shape: 'polygon',
          splitNumber: 4,
          center: ['50%', '50%'],
          radius: '65%',
          axisName: {
            color: '#d4af37',
            fontSize: 12,
            fontWeight: 'bold'
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(212, 175, 55, 0.3)'
            }
          },
          splitArea: {
            show: true,
            areaStyle: {
              color: ['rgba(212, 175, 55, 0.05)', 'rgba(212, 175, 55, 0.1)']
            }
          },
          axisLine: {
            lineStyle: {
              color: 'rgba(212, 175, 55, 0.5)'
            }
          }
        },
        series: [
          {
            name: '风味分布',
            type: 'radar',
            data: [
              {
                value: flavorData,
                name: '当前配方',
                areaStyle: {
                  color: 'rgba(212, 175, 55, 0.3)'
                },
                lineStyle: {
                  color: '#d4af37',
                  width: 2
                },
                itemStyle: {
                  color: '#d4af37'
                }
              }
            ]
          }
        ]
      };
      
      try {
        this.flavorRadarChart.setOption(option);
        console.log('Flavor radar chart updated with data:', flavorData);
      } catch (error) {
        console.error('Error setting radar chart option:', error);
      }
    },
    
    handleResize() {
      if (this.flavorRadarChart) {
        this.flavorRadarChart.resize();
      }
    },
    
    async fetchRecipeData() {
      const recipeId = this.$route.query.recipe_id || '123';
      this.loading = true;
      try {
        const [recipeData, ingredientsData, sqeData, balanceData, keyNodesData, graphData] = await Promise.all([
          fetchRecipe(recipeId),
          fetchIngredients(recipeId),
          fetchSQE(recipeId),
          fetchBalance(recipeId),
          fetchKeyNodes(recipeId),
          fetchGraph(recipeId, this.graphLayer)
        ]);
        this.recipe = recipeData;
        this.ingredients = ingredientsData;
        this.sqe = sqeData;
        this.balance = balanceData;
        this.keyNodes = keyNodesData;
        this.graphData = graphData;
        
        // 等待DOM更新后初始化图表
        this.$nextTick(() => {
          // 确保数据已经完全加载
          if (this.ingredients && this.ingredients.length > 0) {
            // 延迟初始化，确保DOM完全渲染
            setTimeout(() => {
              try {
                console.log('开始初始化所有图表');
                this.initFlavorRadarChart();
                this.updateFlavorRadarChart();
                
                // 先确保DOM元素存在
                if (this.$refs.ingredientContributionChart) {
                  console.log('ingredientContributionChart ref found, initializing...');
                  this.initIngredientContributionChart();
                } else {
                  console.warn('ingredientContributionChart ref not found, will try again later');
                  // 再次尝试初始化
                  setTimeout(() => {
                    if (this.$refs.ingredientContributionChart) {
                      console.log('Retry: ingredientContributionChart ref found, initializing...');
                      this.initIngredientContributionChart();
                    } else {
                      console.error('Failed to find ingredientContributionChart ref after retry');
                    }
                  }, 500);
                }
              } catch (error) {
                console.error('Error initializing charts:', error);
                console.error('Error stack:', error.stack);
              }
            }, 300); // 增加延迟时间
          } else {
            console.warn('No ingredients data available, skipping chart initialization');
          }
        });
        
        // 调试：打印数据结构
        console.log('Recipe data:', recipeData);
        console.log('Ingredients data:', ingredientsData);
        console.log('Key nodes data:', keyNodesData);
        console.log('Graph data:', graphData);
        console.log('Graph data nodes:', graphData?.nodes);
        console.log('Graph data edges:', graphData?.edges);
      } catch (error) {
        this.error = '获取配方数据失败';
        console.error('Error fetching recipe data:', error);
      } finally {
        this.loading = false;
      }
    },
    async selectIngredient(ingredient) {
      this.selectedIngredient = ingredient;
      
      // 延迟更新原料贡献图表，而不是重新初始化
      this.$nextTick(() => {
        setTimeout(() => {
          if (this.ingredientContributionChart) {
            console.log('Updating ingredient contribution chart for selected ingredient');
            this.updateIngredientContributionChart();
          } else {
            console.log('Chart not initialized, initializing now');
            this.initIngredientContributionChart();
          }
        }, 100);
      });
      
      const recipeId = this.$route.query.recipe_id || '123';
      const targetCanonicalId = ingredient.ingredient?.canonical_id;
      if (targetCanonicalId) {
        const substitutes = await fetchSubstitutes(recipeId, targetCanonicalId);
        // 解析每个替代方案的 compatibility_score 和 summary
        this.substitutes = substitutes.map(substitute => {
          let compatibilityScore = 0.5; // 默认值
          let explanationSummary = substitute.explanation; // 默认值
          if (substitute.explanation) {
            try {
              const parsed = JSON.parse(substitute.explanation);
              if (parsed.compatibility_score) {
                compatibilityScore = parsed.compatibility_score;
              }
              if (parsed.summary) {
                explanationSummary = parsed.summary;
              }
            } catch (e) {
              console.error('解析 explanation 失败:', e);
            }
          }
          return {
            ...substitute,
            compatibility_score: compatibilityScore,
            explanation_summary: explanationSummary
          };
        });
        // 调试：打印替代方案数据结构
        console.log('Substitutes data:', this.substitutes);
        if (this.substitutes.length > 0) {
          console.log('First substitute:', this.substitutes[0]);
        }
      } else {
        this.substitutes = [];
      }
    },
    
    // 计算原料对风味维度的贡献
    getIngredientFlavorContribution(flavorType) {
      if (!this.selectedIngredient || !this.balance) return 0;
      
      // 获取原料在配方中的占比（基于用量）
      const totalAmount = this.ingredients.reduce((sum, ing) => sum + (parseFloat(ing.amount) || 0), 0);
      const ingredientAmount = parseFloat(this.selectedIngredient.amount) || 0;
      const amountRatio = totalAmount > 0 ? ingredientAmount / totalAmount : 0;
      
      // 获取原料的风味属性（如果有的话）
      const ingredient = this.selectedIngredient.ingredient;
      if (!ingredient) return amountRatio * 0.5; // 如果没有详细信息，按用量占比的50%计算
      
      // 根据原料类型和风味维度计算贡献
      const flavorMap = {
        'sour': ingredient.is_sour || ingredient.f_sour || 0,
        'sweet': ingredient.is_sweet || ingredient.f_sweet || 0,
        'bitter': ingredient.is_bitter || ingredient.f_bitter || 0,
        'aroma': ingredient.has_aroma || ingredient.f_aroma || 0,
        'fruity': ingredient.is_fruity || ingredient.f_fruity || 0,
        'body': ingredient.has_body || ingredient.f_body || 0
      };
      
      // 获取当前配方的总风味值
      const totalFlavor = this.balance[`f_${flavorType}`] || 0;
      
      // 计算贡献：原料风味属性 * 用量占比
      const ingredientFlavor = flavorMap[flavorType] || 0;
      const contribution = ingredientFlavor * amountRatio;
      
      // 如果配方总风味为0，返回原料自身的风味贡献
      if (totalFlavor === 0) return contribution;
      
      // 否则返回相对于配方总风味的贡献比例
      return Math.min(contribution / totalFlavor, 1);
    },
    
    // 计算原料的总贡献度
    getTotalContribution() {
      if (!this.selectedIngredient) return 0;
      
      const flavors = ['sour', 'sweet', 'bitter', 'aroma', 'fruity', 'body'];
      const totalContribution = flavors.reduce((sum, flavor) => {
        return sum + this.getIngredientFlavorContribution(flavor);
      }, 0);
      
      return Math.min(totalContribution / flavors.length, 1);
    },
    
    // 初始化原料贡献图表
    initIngredientContributionChart() {
      console.log('=== 开始初始化原料贡献图表 ===');
      
      if (!this.$refs.ingredientContributionChart) {
        console.warn('ingredientContributionChart ref not found');
        return false;
      }
      
      try {
        // 确保图表实例被正确dispose
        if (this.ingredientContributionChart) {
          try {
            console.log('Disposing existing chart instance');
            this.ingredientContributionChart.dispose();
          } catch (e) {
            console.warn('Error disposing chart:', e);
          }
          this.ingredientContributionChart = null;
        }
        
        // 重新初始化图表
        console.log('Initializing new chart instance');
        this.ingredientContributionChart = echarts.init(this.$refs.ingredientContributionChart);
        
        // 确保DOM元素存在且有尺寸
        const chartDom = this.$refs.ingredientContributionChart;
        console.log('Chart DOM element:', chartDom);
        console.log('Chart DOM dimensions:', {
          offsetWidth: chartDom?.offsetWidth,
          offsetHeight: chartDom?.offsetHeight,
          clientWidth: chartDom?.clientWidth,
          clientHeight: chartDom?.clientHeight
        });
        
        if (!chartDom || chartDom.offsetWidth === 0 || chartDom.offsetHeight === 0) {
          console.warn('Chart DOM element has no dimensions, skipping initialization');
          return false;
        }
        
        console.log('Chart DOM is ready, updating chart');
        this.updateIngredientContributionChart();
        return true;
      } catch (error) {
        console.error('Error initializing ingredient contribution chart:', error);
        console.error('Error stack:', error.stack);
        return false;
      }
    },
    
    // 更新原料贡献图表
    updateIngredientContributionChart() {
      console.log('=== 开始更新原料贡献图表 ===');
      
      // 确保图表实例存在
      if (!this.ingredientContributionChart) {
        console.warn('Ingredient contribution chart not initialized');
        return;
      }
      
      // 确保原料数据存在
      if (!this.ingredients || !Array.isArray(this.ingredients) || this.ingredients.length === 0) {
        console.warn('No ingredients data available');
        return;
      }
      
      try {
        const flavorTypes = ['sour', 'sweet', 'bitter', 'aroma', 'fruity', 'body'];
        const flavorNames = ['酸味', '甜味', '苦味', '香气', '果味', '酒体'];
        
        console.log('原料数据:', this.ingredients);
        
        // 为每个原料生成数据系列
        const series = [];
        
        this.ingredients.forEach((ingredient, index) => {
          console.log(`处理原料 ${index}:`, ingredient);
          
          // 跳过无效的原料项
          if (!ingredient) {
            console.log(`原料 ${index} 为空，跳过`);
            return;
          }
          
          const ingredientName = ingredient.ingredient?.canonical_name_zh || 
                                ingredient.ingredient?.canonical_name || 
                                ingredient.ingredient?.name_norm || 
                                ingredient.raw_text || 
                                `原料${index + 1}`;
          
          const data = flavorTypes.map(flavorType => {
            // 计算原料对该风味维度的贡献
            const totalAmount = this.ingredients.reduce((sum, ing) => sum + (parseFloat(ing.amount) || 0), 0);
            const ingredientAmount = parseFloat(ingredient.amount) || 0;
            const amountRatio = totalAmount > 0 ? ingredientAmount / totalAmount : 0;
            
            // 获取原料的风味属性
            const ingredientObj = ingredient.ingredient;
            if (!ingredientObj) {
              console.log(`原料 ${index} (${ingredientName}) 没有ingredient对象`);
              return 0;
            }
            
            // 从flavor_feature对象中获取风味属性
            const flavorFeature = ingredientObj.flavor_feature || {};
            
            const flavorMap = {
              'sour': flavorFeature.sour || 0,
              'sweet': flavorFeature.sweet || 0,
              'bitter': flavorFeature.bitter || 0,
              'aroma': flavorFeature.aroma || 0,
              'fruity': flavorFeature.fruity || 0,
              'body': flavorFeature.body || 0
            };
            
            const ingredientFlavor = flavorMap[flavorType] || 0;
            const result = ingredientFlavor * amountRatio;
            // 确保返回有效的数字
            const finalResult = isNaN(result) ? 0 : Math.max(0, result);
            console.log(`原料 ${index} (${ingredientName}) ${flavorType}: ${ingredientFlavor} * ${amountRatio} = ${finalResult}`);
            return finalResult;
          });
          
          console.log(`原料 ${index} (${ingredientName}) 数据:`, data);
          
          // 确保生成有效的series项
          if (ingredientName && data && data.length === flavorTypes.length) {
            series.push({
              name: ingredientName,
              type: 'bar',
              stack: 'total',
              emphasis: {
                focus: 'series'
              },
              data: data,
              // 添加id以确保ECharts能正确识别系列
              id: `ingredient-${index}`
            });
          }
        });
        
        // 确保series数组不为空且所有项都有效
        const validSeries = series.filter(Boolean).map((s, index) => {
          // 确保每个series都有完整的结构
          return {
            name: s.name || `系列${index}`,
            type: 'bar', // 固定为bar类型
            stack: 'total',
            emphasis: {
              focus: 'series'
            },
            data: s.data || [],
            id: s.id || `series-${index}`
          };
        });
        
        // 确保series数组不为空
        if (validSeries.length === 0) {
          console.warn('No valid series data, creating placeholder');
          // 创建一个空的占位系列
          validSeries.push({
            name: '无数据',
            type: 'bar',
            stack: 'total',
            data: [0, 0, 0, 0, 0, 0],
            id: 'placeholder-series'
          });
        }
        
        // 打印series数组，用于调试
        console.log('Ingredient contribution chart series:', JSON.stringify(validSeries, null, 2));
        
        // 创建一个简化的图表配置
        const option = {
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            },
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            borderColor: '#d4af37',
            textStyle: { color: '#fff' }
          },
          legend: {
            data: validSeries.map(s => s.name),
            textStyle: {
              color: '#d4af37'
            },
            bottom: 0,
            // 禁用图例点击事件，避免ECharts内部错误
            selectedMode: false
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '10%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: flavorNames,
            axisLabel: {
              color: '#d4af37'
            },
            axisLine: {
              lineStyle: {
                color: 'rgba(212, 175, 55, 0.3)'
              }
            }
          },
          yAxis: {
            type: 'value',
            name: '贡献度',
            nameTextStyle: {
              color: '#d4af37'
            },
            axisLabel: {
              color: '#d4af37',
              formatter: '{value}'
            },
            axisLine: {
              lineStyle: {
                color: 'rgba(212, 175, 55, 0.3)'
              }
            },
            splitLine: {
              lineStyle: {
                color: 'rgba(212, 175, 55, 0.1)'
              }
            }
          },
          series: validSeries
        };
        
        console.log('ECharts option:', JSON.stringify(option, null, 2));
        
        // 清除之前的配置，避免合并导致的问题
        this.ingredientContributionChart.clear();
        // 设置新的配置，使用replaceMerge确保完全替换
        this.ingredientContributionChart.setOption(option, true);
        console.log('=== 原料贡献图表更新成功 ===');
      } catch (error) {
        console.error('Error updating ingredient contribution chart:', error);
        console.error('Error stack:', error.stack);
      }
    },
    switchGraphLayer(layer) {
      this.graphLayer = layer;
      const recipeId = this.$route.query.recipe_id || '123';
      this.fetchGraphData(recipeId, layer);
    },
    async fetchGraphData(recipeId, layer) {
      try {
        this.graphData = await fetchGraph(recipeId, layer);
      } catch (error) {
        console.error('Error fetching graph data:', error);
        this.graphData = null;
      }
    },
    getScoreLabel(score) {
      if (score >= 0.9) return '卓越';
      if (score >= 0.8) return '优秀';
      if (score >= 0.7) return '良好';
      if (score >= 0.6) return '一般';
      return '需要改进';
    },
    handleGraphNodeClick(node) {
      const ingredient = this.ingredients.find(ing => 
        ing.ingredient?.canonical_id === node.canonical_id
      );
      if (ingredient) {
        this.selectIngredient(ingredient);
      }
    },
    handleViewSubstitutes(node) {
      const ingredient = this.ingredients.find(ing => 
        ing.ingredient?.canonical_id === node.canonical_id
      );
      if (ingredient) {
        this.selectIngredient(ingredient);
      }
    }
  },
  computed: {
    // 计算SQE百分比，确保总和为100%
    sqePercentages() {
      const synergy = this.sqe?.phaseB_synergy_score || 0.28883;
      const conflict = this.sqe?.phaseB_conflict_score || 1.14334;
      const balance = this.sqe?.phaseB_balance_score || 0.78;
      const total = synergy + conflict + balance;
      return {
        synergy: (synergy / total) * 100,
        conflict: (conflict / total) * 100,
        balance: (balance / total) * 100
      };
    },
    // 按类型分组原料
    ingredientsByType() {
      const grouped = {};
      this.ingredients.forEach(ingredient => {
        const type = ingredient.role || '其他';
        if (!grouped[type]) {
          grouped[type] = [];
        }
        grouped[type].push(ingredient);
      });
      return grouped;
    },
    parseExplanation(explanation) {
      try {
        // 尝试解析JSON格式的说明
        if (explanation && (explanation.startsWith('{') || explanation.startsWith('['))) {
          const parsed = JSON.parse(explanation);
          // 如果是对象，提取summary字段
          if (typeof parsed === 'object' && parsed.summary) {
            return parsed.summary;
          }
        }
        // 如果不是JSON或没有summary字段，直接返回
        return explanation;
      } catch (e) {
        // 解析失败，直接返回原始文本
        return explanation;
      }
    },
    getScore(substitute) {
      // 首先尝试从 explanation 中解析 compatibility_score
      if (substitute.explanation) {
        try {
          const parsed = JSON.parse(substitute.explanation);
          if (parsed.compatibility_score) {
            return parsed.compatibility_score;
          }
        } catch (e) {}
      }
      // 然后尝试其他字段
      const scoreFields = ['similarity_score', 'compatibility', 'score', 'similarity'];
      for (const field of scoreFields) {
        if (substitute[field] !== undefined && substitute[field] !== null) {
          return substitute[field];
        }
      }
      // 默认值
      return 0.5; // 默认50%
    },
    
    getScoreForSubstitute(substitute) {
      // 首先尝试从 explanation 中解析 compatibility_score
      if (substitute.explanation) {
        try {
          const parsed = JSON.parse(substitute.explanation);
          if (parsed.compatibility_score) {
            return parsed.compatibility_score;
          }
        } catch (e) {}
      }
      // 然后尝试其他字段
      const scoreFields = ['similarity_score', 'compatibility', 'score', 'similarity'];
      for (const field of scoreFields) {
        if (substitute[field] !== undefined && substitute[field] !== null) {
          return substitute[field];
        }
      }
      // 默认值
      return 0.5; // 默认50%
    }
  },
  computed: {
    // 计算SQE百分比，确保总和为100%
    sqePercentages() {
      const synergy = this.sqe?.phaseB_synergy_score || 0.28883;
      const conflict = this.sqe?.phaseB_conflict_score || 1.14334;
      const balance = this.sqe?.phaseB_balance_score || 0.78;
      const total = synergy + conflict + balance;
      return {
        synergy: (synergy / total) * 100,
        conflict: (conflict / total) * 100,
        balance: (balance / total) * 100
      };
    },
    // 按类型分组原料
    ingredientsByType() {
      const grouped = {};
      this.ingredients.forEach(ingredient => {
        const type = ingredient.role || '其他';
        if (!grouped[type]) {
          grouped[type] = [];
        }
        grouped[type].push(ingredient);
      });
      return grouped;
    },
    // 为每个替代方案计算评分
    scoreMap() {
      const map = {};
      (this.substitutes || []).forEach((substitute, index) => {
        // 首先尝试从 explanation 中解析 compatibility_score
        let score = 0.5; // 默认值
        if (substitute.explanation) {
          try {
            const parsed = JSON.parse(substitute.explanation);
            if (parsed.compatibility_score) {
              score = parsed.compatibility_score;
            }
          } catch (e) {}
        }
        // 然后尝试其他字段
        if (score === 0.5) {
          const scoreFields = ['similarity_score', 'compatibility', 'score', 'similarity'];
          for (const field of scoreFields) {
            if (substitute[field] !== undefined && substitute[field] !== null) {
              score = substitute[field];
              break;
            }
          }
        }
        // 使用 candidate_canonical_id 或 index 作为键
        map[substitute.candidate_canonical_id || index] = score;
      });
      return map;
    },
    sortedSubstitutes() {
      return [...(this.substitutes || [])].sort((a, b) => {
        // 首先按可接受性排序
        if (a.accept_flag && !b.accept_flag) return -1;
        if (!a.accept_flag && b.accept_flag) return 1;
        // 然后按相似度排序
        const similarityA = a.similarity_score || 0;
        const similarityB = b.similarity_score || 0;
        if (similarityA !== similarityB) {
          return similarityB - similarityA;
        }
        // 最后按SQE变化排序
        const sqeA = a.delta_sqe || 0;
        const sqeB = b.delta_sqe || 0;
        return sqeB - sqeA;
      });
    }
  }
};
</script>

<style scoped>
/* 全局样式 */
.visualization {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
  color: #e0e0e0;
}

/* 容器 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
  color: white;
  padding: 2rem 0;
  margin-bottom: 2rem;
}

.page-header-content {
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  font-family: 'Playfair Display', serif;
  letter-spacing: 1px;
}

.page-subtitle {
  font-size: 1.125rem;
  opacity: 0.9;
}

/* 卡片 */
.card {
  background: rgba(42, 42, 42, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 2px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  padding: 1.5rem;
  transition: all 0.3s ease;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(212, 175, 55, 0.15);
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(212, 175, 55, 0.3), 
    transparent
  );
}

.card::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(
    circle at 30% 30%,
    rgba(212, 175, 55, 0.05) 0%,
    transparent 50%
  );
  pointer-events: none;
}

.card:hover {
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.4),
    0 4px 12px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  transform: translateY(-4px);
  border-color: rgba(212, 175, 55, 0.3);
  background: rgba(42, 42, 42, 0.7);
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #d4af37;
  margin-bottom: 1.25rem;
  border-bottom: 2px solid rgba(212, 175, 55, 0.3);
  padding-bottom: 0.625rem;
  font-family: 'Playfair Display', serif;
  letter-spacing: 0.5px;
}

.mt-4 {
  margin-top: 1rem;
}

/* 网格布局 */
.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.lg\:grid-cols-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.lg\:col-span-1 {
  grid-column: span 1 / span 1;
}

.lg\:col-span-2 {
  grid-column: span 2 / span 2;
}

.gap-4 {
  gap: 1rem;
}

.mb-6 {
  margin-bottom: 1.5rem;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 4rem;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(212, 175, 55, 0.2);
  border-left-color: #d4af37;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1.5rem;
}

.loading-spinner.small {
  width: 30px;
  height: 30px;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 1rem;
  color: #999;
}

/* 错误状态 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: 4rem;
  text-align: center;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 0.75rem;
}

.error-message {
  font-size: 1rem;
  color: #999;
  margin-bottom: 2rem;
  max-width: 600px;
}

/* 配方头部 */
.recipe-header-section {
  margin-bottom: 2rem;
}

.recipe-header-content {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.recipe-header-info {
  flex: 1;
  min-width: 300px;
}

.recipe-name {
  font-size: 2rem;
  font-weight: 700;
  color: #d4af37;
  margin-bottom: 0.75rem;
  font-family: 'Playfair Display', serif;
  letter-spacing: 1px;
}

.recipe-subtitle {
  font-size: 1rem;
  color: #999;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.recipe-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.recipe-meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 8px;
  font-size: 0.875rem;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.meta-icon {
  font-size: 1.125rem;
}

.meta-label {
  color: #999;
  font-weight: 500;
}

.meta-value {
  color: #e0e0e0;
  font-weight: 600;
}

.recipe-header-image {
  flex-shrink: 0;
  width: 200px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 175, 55, 0.3);
}

.recipe-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.recipe-header-image:hover .recipe-image {
  transform: scale(1.05);
}

/* 原料结构 */
.ingredient-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.ingredient-item {
  padding: 0.875rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.ingredient-item:hover {
  background: rgba(212, 175, 55, 0.1);
  border-color: rgba(212, 175, 55, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.ingredient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.ingredient-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #e0e0e0;
}

.ingredient-role {
  padding: 0.1875rem 0.625rem;
  border-radius: 10px;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.role-base {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.role-acid {
  background: rgba(255, 152, 0, 0.1);
  color: #ff9800;
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.role-sweetener {
  background: rgba(233, 30, 99, 0.1);
  color: #e91e63;
  border: 1px solid rgba(233, 30, 99, 0.3);
}

.role-bitter {
  background: rgba(156, 39, 176, 0.1);
  color: #9c27b0;
  border: 1px solid rgba(156, 39, 176, 0.3);
}

.role-other {
  background: rgba(103, 58, 183, 0.1);
  color: #673ab7;
  border: 1px solid rgba(103, 58, 183, 0.3);
}

.ingredient-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.ingredient-amount {
  font-size: 0.8125rem;
  color: #999;
  font-weight: 500;
}

.ingredient-category {
  font-size: 0.75rem;
  color: #888;
  font-style: italic;
}

.ingredient-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.625rem;
}

.ingredient-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #888;
}

.ingredient-canonical {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #888;
  font-style: italic;
}

/* 原料分组样式 */
.ingredient-groups {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex: 1;
}

.ingredient-group {
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.ingredient-group:hover {
  border-color: rgba(212, 175, 55, 0.2);
  background: rgba(212, 175, 55, 0.08);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(212, 175, 55, 0.1);
  border-bottom: 1px solid rgba(212, 175, 55, 0.1);
}

.group-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #d4af37;
  margin: 0;
  font-family: 'Playfair Display', serif;
  letter-spacing: 0.5px;
}

.group-count {
  font-size: 0.75rem;
  color: #999;
  background: rgba(212, 175, 55, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

/* 结构解释图样式 */
.local-graph-section {
  width: 100%;
}

.local-graph {
  width: 100%;
}

.graph-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.graph-control-btn {
  padding: 0.5rem 1rem;
  background: rgba(212, 175, 55, 0.1);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.graph-control-btn:hover {
  background: rgba(212, 175, 55, 0.2);
  border-color: rgba(212, 175, 55, 0.5);
}

.graph-control-btn.active {
  background: rgba(212, 175, 55, 0.3);
  border-color: #d4af37;
  color: #d4af37;
}

.graph-control-separator {
  width: 1px;
  height: 1.5rem;
  background: rgba(212, 175, 55, 0.3);
  margin: 0 0.5rem;
}

.graph-container {
  position: relative;
  width: 100%;
  min-height: 400px;
  border-radius: 8px;
  overflow: visible;
}

.graph-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  background: rgba(212, 175, 55, 0.05);
  border: 1px dashed rgba(212, 175, 55, 0.3);
  border-radius: 8px;
}

.graph-placeholder-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.graph-placeholder-text {
  font-size: 1rem;
  color: #999;
  margin-bottom: 0.5rem;
}

.graph-placeholder-subtext {
  font-size: 0.875rem;
  color: #777;
}

.graph-canvas {
  width: 100%;
  height: 400px;
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
}

.graph-node {
  cursor: pointer;
  transition: opacity 0.3s ease;
}

.graph-node:hover circle {
  filter: brightness(1.2);
}

.graph-node.selected {
  opacity: 1;
}

.graph-node:not(.selected):not(.hovered) {
  opacity: 0.7;
}

.node-label {
  font-size: 0.75rem;
  font-weight: 600;
  fill: white;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
  pointer-events: none;
}

.node-role {
  font-size: 0.625rem;
  fill: #d4af37;
  font-weight: 500;
  pointer-events: none;
}

.node-contribution {
  font-size: 0.625rem;
  fill: #e0e0e0;
  font-weight: 500;
  pointer-events: none;
}

.edge-label {
  font-size: 0.625rem;
  fill: #999;
  pointer-events: none;
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 4px;
  border-radius: 3px;
}

.node-details {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.node-details-title {
  font-size: 1rem;
  font-weight: 600;
  color: #d4af37;
  margin-bottom: 0.75rem;
}

.node-details-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.metric-item {
  font-size: 0.875rem;
  color: #e0e0e0;
}

.node-details-actions {
  display: flex;
  gap: 0.5rem;
}

.edge-details {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(33, 150, 243, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.edge-details-title {
  font-size: 1rem;
  font-weight: 600;
  color: #2196f3;
  margin-bottom: 0.75rem;
}

.edge-details-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

/* 气泡提示样式 */
.node-tooltip,
.edge-tooltip {
  position: absolute;
  z-index: 1000;
  pointer-events: none;
  opacity: 1;
  transition: opacity 0.2s ease;
  will-change: opacity, left, top;
}

.tooltip-content {
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(212, 175, 55, 0.3);
  border-radius: 8px;
  padding: 1rem;
  min-width: 200px;
  max-width: 300px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.tooltip-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #d4af37;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
  padding-bottom: 0.5rem;
}

.tooltip-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.tooltip-actions {
  margin-top: 0.75rem;
  display: flex;
  justify-content: flex-end;
}

.tooltip-arrow {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid rgba(30, 30, 30, 0.95);
}

/* 按钮样式 */
.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(212, 175, 55, 0.3);
}

.btn-secondary {
  background: rgba(212, 175, 55, 0.2);
  color: #d4af37;
  border: 1px solid rgba(212, 175, 55, 0.3);
}

.btn-secondary:hover {
  background: rgba(212, 175, 55, 0.3);
  border-color: #d4af37;
}

.btn-outline {
  background: transparent;
  color: #e0e0e0;
  border: 1px solid rgba(212, 175, 55, 0.3);
}

.btn-outline:hover {
  background: rgba(212, 175, 55, 0.1);
  border-color: #d4af37;
  color: #d4af37;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

.group-ingredients {
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.ingredient-item {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
}

.ingredient-item:hover {
  border-color: rgba(212, 175, 55, 0.3);
  background: rgba(212, 175, 55, 0.05);
  transform: translateX(4px);
}

.ingredient-item.selected {
  border-color: #d4af37;
  background: rgba(212, 175, 55, 0.15);
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
}

.ingredient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.ingredient-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #e0e0e0;
  margin: 0;
  flex: 1;
}

.ingredient-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
  color: #999;
}

.ingredient-amount {
  font-weight: 500;
  color: #d4af37;
}

.ingredient-category {
  background: rgba(212, 175, 55, 0.1);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  border: 1px solid rgba(212, 175, 55, 0.2);
  font-size: 0.75rem;
  color: #888;
}

/* SQE分析 */
.combined-card {
  flex: 1;
}

.sqe-overall {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding: 1rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.sqe-score {
  text-align: center;
}

.score-number {
  display: block;
  font-size: 2.25rem;
  font-weight: 700;
  color: #d4af37;
  line-height: 1;
  font-family: 'Playfair Display', serif;
}

.score-label {
  display: block;
  font-size: 0.875rem;
  color: #999;
  margin-top: 0.5rem;
}

.sqe-stats {
  display: flex;
  gap: 1.5rem;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.8125rem;
  color: #999;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e0e0e0;
}

/* 三色条形图 */
.sqe-triple-bar {
  margin-bottom: 1.5rem;
}

.triple-bar-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.8125rem;
  color: #999;
}

.triple-label {
  font-weight: 500;
}

.synergy-label {
  color: #4caf50;
}

.conflict-label {
  color: #f44336;
}

.balance-label {
  color: #2196f3;
}

.triple-bar-container {
  display: flex;
  height: 32px;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(212, 175, 55, 0.2);
  width: 100%;
}

.triple-bar-fill {
  flex-shrink: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.8s ease-out;
}

.synergy-fill {
  background: linear-gradient(180deg, #4caf50, #81c784);
}

.conflict-fill {
  background: linear-gradient(180deg, #f44336, #e57373);
}

.balance-fill {
  background: linear-gradient(180deg, #2196f3, #64b5f6);
}

.triple-value {
  font-size: 0.6875rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.triple-bar-legend {
  display: flex;
  justify-content: space-between;
  margin-top: 0.75rem;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #999;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.synergy-color {
  background: linear-gradient(180deg, #4caf50, #81c784);
}

.conflict-color {
  background: linear-gradient(180deg, #f44336, #e57373);
}

.balance-color {
  background: linear-gradient(180deg, #2196f3, #64b5f6);
}

.legend-text {
  font-weight: 500;
}

/* 风味分布 */
.flavor-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.25rem;
}

.radar-chart-container,
.flavor-bars-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 8px;
  padding: 1.25rem;
  border: 1px solid rgba(212, 175, 55, 0.1);
}

.radar-chart-echarts {
  width: 100%;
  height: 100%;
  min-height: 280px;
}

.flavor-bars {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.flavor-bar-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.flavor-bar-label {
  flex: 0 0 40px;
  font-size: 0.875rem;
  color: #999;
  text-align: right;
}

.flavor-bar {
  flex: 1;
  height: 6px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.flavor-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #d4af37, #b8860b);
  border-radius: 3px;
  transition: width 1s ease-out;
}

.flavor-bar-value {
  flex: 0 0 40px;
  font-size: 0.875rem;
  color: #999;
  text-align: left;
}

.balance-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(212, 175, 55, 0.2);
}

/* 关键风味识别 */
.key-flavor-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.key-flavor-item {
  padding: 0.875rem;
  background: rgba(212, 175, 55, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(212, 175, 55, 0.1);
  transition: all 0.3s ease;
}

.key-flavor-item:hover {
  background: rgba(212, 175, 55, 0.1);
  border-color: rgba(212, 175, 55, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.rank-1 {
  border-left: 3px solid #d4af37;
}

.rank-2 {
  border-left: 3px solid #e6c568;
}

.rank-3 {
  border-left: 3px solid #f0d995;
}

.key-flavor-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.flavor-rank {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #d4af37;
  color: #2a2a2a;
  font-size: 0.6875rem;
  font-weight: 600;
  border-radius: 50%;
  flex-shrink: 0;
}

.flavor-name {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 600;
  color: #e0e0e0;
}

.flavor-contribution {
  font-size: 0.875rem;
  font-weight: 600;
  color: #d4af37;
}

.contribution-bar {
  width: 100%;
  height: 4px;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 2px;
  overflow: hidden;
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.contribution-fill {
  height: 100%;
  background: linear-gradient(90deg, #d4af37, #b8860b);
  border-radius: 2px;
  transition: width 1s ease-out;
}

.flavor-metrics {
  display: flex;
  gap: 1.25rem;
  font-size: 0.75rem;
  color: #888;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.metric {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.metric-label {
  font-weight: 500;
  color: #999;
}

.metric-value {
  font-weight: 600;
  color: #d4af37;
}

.flavor-explanation {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(212, 175, 55, 0.1);
  font-size: 0.75rem;
  line-height: 1.4;
  color: #999;
}

.flavor-explanation p {
  margin: 0;
}

/* 中英文名称样式 */
.name-zh {
  color: #e0e0e0;
  font-weight: 600;
}

.name-en {
  color: #999;
  font-weight: 400;
  font-size: 0.9em;
}

.name-separator {
  color: #d4af37;
  margin: 0 0.25rem;
}

/* 组合调整入口 */
.adjust-entry-section {
  margin-top: var(--spacing-xl);
}

.adjust-entry-card {
  padding: var(--spacing-xl);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.05), rgba(212, 175, 55, 0.02));
  border: 2px solid rgba(212, 175, 55, 0.2);
}

.entry-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-xl);
}

.entry-icon {
  font-size: 3rem;
  opacity: 0.8;
}

.entry-info {
  flex: 1;
}

.entry-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-serif);
}

.entry-description {
  font-size: 1rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* 操作区 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

/* 按钮 */
.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
}

.btn-primary {
  background: #d4af37;
  color: #2a2a2a;
  border-color: #d4af37;
  font-weight: 600;
}

.btn-primary:hover {
  background: #b8860b;
  border-color: #b8860b;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(212, 175, 55, 0.3);
}

.btn-secondary {
  background: transparent;
  color: #d4af37;
  border-color: #d4af37;
}

.btn-secondary:hover {
  background: #d4af37;
  color: #2a2a2a;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(212, 175, 55, 0.2);
}

.btn-outline {
  background: transparent;
  color: #999;
  border-color: #444;
}

.btn-outline:hover {
  background: #444;
  border-color: #d4af37;
  color: #d4af37;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

/* 原料风味贡献 */
.ingredient-flavor-contribution {
  margin-top: 1rem;
}

.contribution-chart-container {
  height: 200px;
  margin-bottom: 1rem;
}

.contribution-chart {
  width: 100%;
  height: 100%;
}

.contribution-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.contribution-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.contribution-label {
  flex: 0 0 50px;
  font-size: 0.875rem;
  color: #999;
  text-align: right;
}

.contribution-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.contribution-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease-out;
}

.contribution-value {
  flex: 0 0 50px;
  font-size: 0.875rem;
  color: #d4af37;
  font-weight: 600;
  text-align: left;
}

.contribution-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(212, 175, 55, 0.2);
}

.total-label {
  font-size: 1rem;
  color: #999;
}

.total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #d4af37;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .lg\:grid-cols-4 {
    grid-template-columns: 1fr;
  }
  
  .lg\:col-span-1,
  .lg\:col-span-2 {
    grid-column: span 1 / span 1;
  }
  
  .flavor-charts {
    grid-template-columns: 1fr;
  }
  
  .radar-chart-container,
  .flavor-bars-container {
    height: 250px;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 0 1rem;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .card {
    padding: 1.25rem;
  }
  
  .recipe-header-content {
    flex-direction: column;
    text-align: center;
  }
  
  .recipe-header-image {
    width: 100%;
    max-width: 250px;
  }
  
  .recipe-meta {
    justify-content: center;
  }
  
  .sqe-overall {
    flex-direction: column;
    gap: 1.5rem;
    text-align: center;
  }
  
  .sqe-stats {
    justify-content: center;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
  
  .flavor-charts {
    grid-template-columns: 1fr;
  }
  
  .radar-chart-container,
  .flavor-bars-container {
    height: 250px;
  }
}
</style>