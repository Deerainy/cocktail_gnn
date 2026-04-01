<template>
  <div class="adjust-view">
    <div v-if="loading && !recipes" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载配方列表中...</p>
    </div>
    
    <div v-else-if="error && !recipes" class="error-container">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">加载失败</h2>
      <p class="error-message">{{ error }}</p>
      <button class="btn btn-primary" @click="fetchRecipes">重新加载</button>
    </div>
    
    <div v-else-if="!recipeId && recipes.length > 0" class="recipe-select-container">
      <div class="recipe-select-card card">
        <h2 class="select-title">选择配方</h2>
        <p class="select-description">请选择一个配方进行组合调整分析</p>
        <div class="recipe-list">
          <div 
            v-for="recipe in recipes" 
            :key="recipe.recipe_id"
            class="recipe-item"
            @click="selectRecipe(recipe.recipe_id)"
          >
            <div class="recipe-info">
              <h3 class="recipe-name">{{ recipe.name }}</h3>
              <p class="recipe-source">{{ recipe.source }}</p>
            </div>
            <div class="recipe-action">
              <span class="action-icon">→</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <template v-else-if="recipeId">
      <header class="page-header">
        <div class="container">
          <div class="page-header-content">
            <h1 class="page-title">配方调整分析工作台</h1>
            <p class="page-subtitle">探索配方优化的多种可能性</p>
          </div>
        </div>
      </header>
      
      <main class="adjust-main">
        <div class="container">
          <div class="adjust-tabs">
            <button 
              :class="['tab-button', { active: activeTab === 'single' }]"
              @click="switchTab('single')"
            >
              <span class="tab-icon">🔄</span>
              <span class="tab-label">单个替代调整</span>
            </button>
            <button 
              :class="['tab-button', { active: activeTab === 'combo' }]"
              @click="switchTab('combo')"
            >
              <span class="tab-icon">🔧</span>
              <span class="tab-label">组合调整</span>
            </button>
          </div>
          
          <div v-if="activeTab === 'single'" class="single-adjust-content">
            <div v-if="!recipeId" class="no-data-container">
              <div class="no-data-icon">📋</div>
              <p class="no-data-text">请先选择一个配方</p>
              <p class="no-data-subtext">从左侧选择一个配方开始分析</p>
            </div>
            
            <div v-else>
              <!-- 原料选择器 -->
              <div class="ingredient-selector">
                <h3 class="selector-title">选择目标原料</h3>
                <div v-if="loadingIngredients" class="loading-container">
                  <div class="loading-spinner"></div>
                  <p class="loading-text">加载原料中...</p>
                </div>
                <div v-else-if="ingredients.length === 0" class="no-data-container">
                  <div class="no-data-icon">🥃</div>
                  <p class="no-data-text">暂无原料数据</p>
                  <p class="no-data-subtext">该配方可能没有原料信息</p>
                </div>
                <div v-else class="ingredients-grid">
                  <div 
                    v-for="ingredient in ingredients" 
                    :key="ingredient.ingredient_id"
                    :class="['ingredient-card', { selected: selectedIngredient && selectedIngredient.ingredient_id === ingredient.ingredient_id }]"
                    @click="selectIngredient(ingredient)"
                  >
                    <div class="ingredient-name">{{ ingredient.ingredient?.name || ingredient.ingredient_id }}</div>
                    <div class="ingredient-role">{{ ingredient.role }}</div>
                    <div class="ingredient-amount">{{ ingredient.amount }} {{ ingredient.unit }}</div>
                    <div class="ingredient-canonical" v-if="ingredient.ingredient?.canonical_id">
                      Canonical: {{ ingredient.ingredient.canonical_id }}
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 替代方案列表 -->
              <div v-if="selectedIngredient">
                <div v-if="loadingSubstitutes" class="loading-container">
                  <div class="loading-spinner"></div>
                  <p class="loading-text">加载替代方案中...</p>
                </div>
                
                <div v-else-if="substitutesError" class="error-container">
                  <div class="error-icon">⚠️</div>
                  <h2 class="error-title">加载失败</h2>
                  <p class="error-message">{{ substitutesError }}</p>
                  <button class="btn btn-primary" @click="refreshSubstitutes">重新加载</button>
                </div>
                
                <div v-else-if="substitutes.length === 0" class="no-data-container">
                  <div class="no-data-icon">📋</div>
                  <p class="no-data-text">暂无替代方案</p>
                  <p class="no-data-subtext">请选择一个原料查看替代方案</p>
                </div>
                
                <div v-else class="substitutes-container">
                  <div class="substitutes-header">
                    <h3 class="substitutes-title">替代方案列表</h3>
                    <div class="substitutes-count">共 {{ substitutes.length }} 个方案</div>
                  </div>
                  
                  <div class="substitutes-list">
                    <div 
                      v-for="substitute in substitutes" 
                      :key="substitute.id"
                      :class="['substitute-card', { 
                        selected: selectedSubstituteId === substitute.id,
                        accepted: substitute.accept_flag 
                      }]"
                      @click="selectSubstitute(substitute.id)"
                    >
                      <div class="substitute-header">
                        <div class="substitute-rank">
                          <span class="rank-label">Rank</span>
                          <span class="rank-number">{{ substitute.rank_no }}</span>
                        </div>
                        <span :class="['substitute-status', substitute.accept_flag ? 'accept' : 'reject']">
                          {{ substitute.accept_flag ? '已接受' : '已拒绝' }}
                        </span>
                      </div>
                      
                      <div class="substitute-title">
                        {{ substitute.candidate_name || substitute.candidate_canonical_id || '未知原料' }}
                      </div>
                      
                      <div class="substitute-info">
                        <div class="info-item">
                          <span class="info-label">目标原料:</span>
                          <span class="info-value">{{ selectedIngredient?.ingredient?.name || selectedIngredient?.ingredient_id || '未知' }}</span>
                        </div>
                        <div class="info-item">
                          <span class="info-label">候选原料:</span>
                          <span class="info-value">{{ substitute.candidate_name || substitute.candidate_canonical_id || '未知' }}</span>
                        </div>
                      </div>
                      
                      <div class="substitute-scores">
                        <div class="score-item">
                          <span class="score-label">SQE</span>
                          <span class="score-value">{{ (substitute.score_breakdown?.new_sqe_total || substitute.new_sqe_total || 0).toFixed(3) }}</span>
                        </div>
                        <div class="score-item">
                          <span class="score-label">ΔSQE</span>
                          <span :class="['score-value', (substitute.score_breakdown?.delta_sqe || substitute.delta_sqe || 0) >= 0 ? 'positive' : 'negative']">
                            {{ (substitute.score_breakdown?.delta_sqe || substitute.delta_sqe || 0) >= 0 ? '+' : '' }}{{ (substitute.score_breakdown?.delta_sqe || substitute.delta_sqe || 0).toFixed(3) }}
                          </span>
                        </div>
                      </div>
                      
                      <div class="substitute-metrics">
                        <div class="metric-item">
                          <span class="metric-label">协同</span>
                          <span :class="['metric-value', (substitute.score_breakdown?.delta_synergy || 0) >= 0 ? 'positive' : 'negative']">
                            {{ (substitute.score_breakdown?.delta_synergy || 0) >= 0 ? '+' : '' }}{{ (substitute.score_breakdown?.delta_synergy || 0).toFixed(3) }}
                          </span>
                        </div>
                        <div class="metric-item">
                          <span class="metric-label">冲突</span>
                          <span :class="['metric-value', (substitute.score_breakdown?.delta_conflict || 0) <= 0 ? 'positive' : 'negative']">
                            {{ (substitute.score_breakdown?.delta_conflict || 0) >= 0 ? '+' : '' }}{{ (substitute.score_breakdown?.delta_conflict || 0).toFixed(3) }}
                          </span>
                        </div>
                        <div class="metric-item">
                          <span class="metric-label">平衡</span>
                          <span :class="['metric-value', (substitute.score_breakdown?.delta_balance || 0) >= 0 ? 'positive' : 'negative']">
                            {{ (substitute.score_breakdown?.delta_balance || 0) >= 0 ? '+' : '' }}{{ (substitute.score_breakdown?.delta_balance || 0).toFixed(3) }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="activeTab === 'combo'" class="combo-adjust-content">
            <ComboAdjustOverview 
              v-if="overview"
              :overview="overview"
            />
            
            <StageComparisonBar 
              v-if="overview"
              :overview="overview"
              :selected-plan="selectedPlan"
            />
            
            <div v-if="plans.length === 0" class="no-combo-plans">
              <div class="no-plans-icon">🔍</div>
              <h3 class="no-plans-title">未发现合理的组合调整方案</h3>
              <p class="no-plans-description">
                我们分析了当前配方的各种可能组合，
                但没有找到能够显著提升配方质量的调整方案。
              </p>
              <div class="no-plans-suggestions">
                <h4>建议：</h4>
                <ul>
                  <li>尝试选择不同的配方进行分析</li>
                  <li>考虑使用单个替代调整功能</li>
                  <li>检查原料数据是否完整</li>
                </ul>
              </div>
            </div>
            
            <div v-else class="main-content-area">
              <div class="left-panel">
                <ComboPlanList 
                  :plans="plans"
                  :selected-plan-id="selectedPlanId"
                  :filters="filters"
                  @select="handleSelectPlan"
                  @filter-change="handleFilterChange"
                />
              </div>
              
              <div class="right-panel">
                <ComboPlanDetail 
                  v-if="selectedPlan"
                  :plan="selectedPlan"
                />
                
                <ScoreCompareCard 
                  v-if="selectedPlan"
                  :plan="selectedPlan"
                  :overview="overview"
                />
                
                <DiagnosisAndJudgementPanel 
                  v-if="selectedPlan"
                  :plan="selectedPlan"
                />
              </div>
            </div>
            
            <ComboStepTimeline 
              v-if="selectedPlan && selectedPlan.steps"
              :steps="selectedPlan.steps"
            />
          </div>
        </div>
      </main>
    </template>
  </div>
</template>

<script>
import ComboAdjustOverview from '@/components/adjust/ComboAdjustOverview.vue'
import StageComparisonBar from '@/components/adjust/StageComparisonBar.vue'
import ComboPlanList from '@/components/adjust/ComboPlanList.vue'
import ComboPlanDetail from '@/components/adjust/ComboPlanDetail.vue'
import ScoreCompareCard from '@/components/adjust/ScoreCompareCard.vue'
import ComboStepTimeline from '@/components/adjust/ComboStepTimeline.vue'
import DiagnosisAndJudgementPanel from '@/components/adjust/DiagnosisAndJudgementPanel.vue'

export default {
  name: 'AdjustView',
  
  components: {
    ComboAdjustOverview,
    StageComparisonBar,
    ComboPlanList,
    ComboPlanDetail,
    ScoreCompareCard,
    ComboStepTimeline,
    DiagnosisAndJudgementPanel
  },
  
  data() {
    return {
      loading: false,
      error: null,
      overview: null,
      plans: [],
      recipes: [],
      selectedPlanId: null,
      selectedPlan: null,
      activeTab: 'combo',
      substitutes: [],
      selectedSubstituteId: null,
      selectedSubstitute: null,
      loadingSubstitutes: false,
      substitutesError: null,
      ingredients: [],
      selectedIngredient: null,
      loadingIngredients: false,
      filters: {
        accept_flag: null,
        target_canonical_id: null,
        snapshot_id: null,
        model_version: null
      }
    }
  },
  
  computed: {
    recipeId() {
      return this.$route.query.recipe_id
    },
    targetCanonicalId() {
      return this.$route.query.target_canonical_id
    }
  },
  
  watch: {
    recipeId: {
      handler(newRecipeId) {
        if (newRecipeId) {
          this.fetchOverview()
          this.fetchPlans()
          if (this.activeTab === 'single') {
            this.fetchIngredients()
          }
        } else {
          this.fetchRecipes()
        }
      },
      immediate: true
    },
    targetCanonicalId: {
      handler(newTargetId) {
        if (newTargetId && this.recipeId) {
          // 自动切换到单个替代调整标签
          this.activeTab = 'single'
          this.filters.target_canonical_id = newTargetId
          // 先获取原料列表，然后选择对应的原料
          this.fetchIngredients().then(() => {
            if (this.ingredients.length > 0) {
              const ingredient = this.ingredients.find(ing => 
                ing.ingredient && ing.ingredient.canonical_id === newTargetId
              )
              if (ingredient) {
                this.selectedIngredient = ingredient
                this.fetchSubstitutes()
              }
            }
          })
        }
      },
      immediate: true
    }
  },
  
  mounted() {
    // 初始化时由watch处理
  },
  
  methods: {
    async fetchOverview() {
      if (!this.recipeId) {
        this.error = '缺少配方ID参数'
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/recipes/${this.recipeId}/combo-adjust/overview`)
        const data = await response.json()
        
        if (data.code === 0) {
          this.overview = data.data
          
          if (this.targetCanonicalId) {
            this.filters.target_canonical_id = this.targetCanonicalId
          }
        } else {
          this.error = data.message || '获取概览数据失败'
        }
      } catch (err) {
        console.error('获取概览数据失败:', err)
        this.error = '网络请求失败，请检查后端服务是否正常运行'
      } finally {
        this.loading = false
      }
    },
    
    async fetchPlans() {
      if (!this.recipeId) return
      
      try {
        const params = new URLSearchParams()
        params.append('ordering', '-accept_flag,rank_no')
        
        if (this.filters.accept_flag !== null) {
          params.append('accept_flag', this.filters.accept_flag)
        }
        if (this.filters.target_canonical_id) {
          params.append('target_canonical_id', this.filters.target_canonical_id)
        }
        if (this.filters.snapshot_id) {
          params.append('snapshot_id', this.filters.snapshot_id)
        }
        if (this.filters.model_version) {
          params.append('model_version', this.filters.model_version)
        }
        
        const response = await fetch(`http://127.0.0.1:8000/api/recipes/${this.recipeId}/combo-adjust/plans?${params}`)
        const data = await response.json()
        
        if (data.code === 0) {
          this.plans = data.data
          
          if (this.plans.length > 0 && !this.selectedPlanId) {
            this.handleSelectPlan(this.plans[0].plan_id)
          }
        }
      } catch (err) {
        console.error('获取方案列表失败:', err)
      }
    },
    
    async handleSelectPlan(planId) {
      this.selectedPlanId = planId
      
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/combo-adjust/plans/${planId}`)
        const data = await response.json()
        
        if (data.code === 0) {
          this.selectedPlan = data.data
        }
      } catch (err) {
        console.error('获取方案详情失败:', err)
      }
    },
    
    handleFilterChange(newFilters) {
      this.filters = { ...this.filters, ...newFilters }
      this.fetchPlans()
    },
    
    async fetchRecipes() {
      this.loading = true
      this.error = null
      
      try {
        const response = await fetch('http://127.0.0.1:8000/api/recipes')
        const data = await response.json()
        
        if (data.code === 0) {
          this.recipes = data.data
        } else {
          this.error = data.message || '获取配方列表失败'
        }
      } catch (err) {
        console.error('获取配方列表失败:', err)
        this.error = '网络请求失败，请检查后端服务是否正常运行'
      } finally {
        this.loading = false
      }
    },
    
    selectRecipe(recipeId) {
      this.$router.push({
        path: '/adjust',
        query: {
          recipe_id: recipeId
        }
      })
    },
    
    switchTab(tab) {
      this.activeTab = tab
      if (tab === 'single') {
        this.fetchIngredients()
      }
    },
    
    async fetchSubstitutes() {
      if (!this.recipeId) return
      
      if (!this.filters.target_canonical_id) {
        this.substitutesError = '缺少目标原料参数，请先选择一个目标原料'
        this.loadingSubstitutes = false
        return
      }
      
      this.loadingSubstitutes = true
      this.substitutesError = null
      
      try {
        const params = new URLSearchParams()
        params.append('target_canonical_id', this.filters.target_canonical_id)
        
        const response = await fetch(`http://127.0.0.1:8000/api/recipes/${this.recipeId}/substitutes?${params}`)
        const data = await response.json()
        
        if (data.code === 0) {
          this.substitutes = data.data
          
          if (this.substitutes.length > 0 && !this.selectedSubstituteId) {
            this.selectSubstitute(this.substitutes[0].id)
          }
        } else {
          this.substitutesError = data.message || '获取替代方案失败'
        }
      } catch (err) {
        console.error('获取替代方案失败:', err)
        this.substitutesError = '网络请求失败，请检查后端服务是否正常运行'
      } finally {
        this.loadingSubstitutes = false
      }
    },
    
    selectSubstitute(substituteId) {
      this.selectedSubstituteId = substituteId
      this.selectedSubstitute = this.substitutes.find(s => s.id === substituteId)
    },
    
    async fetchIngredients() {
      if (!this.recipeId) return Promise.resolve()
      
      this.loadingIngredients = true
      
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/recipes/${this.recipeId}/ingredients`)
        const data = await response.json()
        
        if (data.code === 0) {
          this.ingredients = data.data
        }
      } catch (err) {
        console.error('获取原料列表失败:', err)
      } finally {
        this.loadingIngredients = false
      }
      
      return Promise.resolve()
    },
    
    selectIngredient(ingredient) {
      this.selectedIngredient = ingredient
      if (ingredient.ingredient && ingredient.ingredient.canonical_id) {
        this.filters.target_canonical_id = ingredient.ingredient.canonical_id
        this.fetchSubstitutes()
      } else {
        this.substitutesError = '原料缺少canonical_id信息'
        this.substitutes = []
      }
    },
    
    refreshSubstitutes() {
      this.fetchSubstitutes()
    }
  }
}
</script>

<style scoped>
.adjust-view {
  min-height: 100vh;
  background: var(--color-bg-1);
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: var(--spacing-2xl);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-border);
  border-top-color: var(--color-gold-400);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: var(--spacing-lg);
  color: var(--color-text-secondary);
  font-size: 1.1rem;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: var(--spacing-lg);
}

.error-title {
  color: var(--color-text-primary);
  font-size: 1.5rem;
  margin-bottom: var(--spacing-md);
}

.error-message {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
  text-align: center;
  max-width: 600px;
}

.page-header {
  background: linear-gradient(135deg, var(--color-bg-2) 0%, var(--color-bg-3) 100%);
  padding: var(--spacing-2xl) 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--spacing-xl);
}

.page-header-content {
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-serif);
}

.page-subtitle {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
}

.adjust-main {
  padding-bottom: var(--spacing-2xl);
}

.adjust-tabs {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
}

.tab-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-xl);
  background: transparent;
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  color: var(--color-text-secondary);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-button:hover {
  border-color: var(--color-gold-400);
  color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.05);
}

.tab-button.active {
  background: var(--color-gold-400);
  border-color: var(--color-gold-400);
  color: var(--color-bg-1);
}

.tab-icon {
  font-size: 1.2rem;
}

.tab-label {
  font-size: 1rem;
  font-weight: 500;
}

.single-adjust-content {
  animation: fadeIn 0.3s ease;
}

.combo-adjust-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.no-data-container {
  text-align: center;
  padding: var(--spacing-2xl);
}

.no-data-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
}

.no-data-text {
  color: var(--color-text-primary);
  font-size: 1.2rem;
  margin-bottom: var(--spacing-sm);
}

.no-data-subtext {
  color: var(--color-text-secondary);
  font-size: 1rem;
}

.substitutes-container {
  animation: fadeIn 0.3s ease;
}

.substitutes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
}

.substitutes-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.substitutes-count {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.substitutes-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  max-height: 600px;
  overflow-y: auto;
}

.substitute-card {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s ease;
}

.substitute-card:hover {
  border-color: var(--color-gold-400);
  transform: translateY(-2px);
}

.substitute-card.selected {
  border-color: var(--color-gold-400);
  background: var(--color-bg-3);
}

.substitute-card.accepted {
  border-left: 4px solid var(--color-success);
}

.substitute-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.substitute-rank {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.rank-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.rank-number {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-gold-400);
}

.substitute-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
}

.substitute-status.accept {
  background: rgba(76, 175, 80, 0.2);
  color: var(--color-success);
}

.substitute-status.reject {
  background: rgba(244, 67, 54, 0.2);
  color: var(--color-error);
}

.substitute-title {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
  line-height: 1.4;
}

.substitute-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-sm);
}

.info-item {
  display: flex;
  gap: var(--spacing-xs);
}

.info-label {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.info-value {
  color: var(--color-text-primary);
  font-weight: 500;
  font-size: 0.9rem;
}

.substitute-scores {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--color-bg-1);
  border-radius: var(--border-radius-sm);
}

.score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.score-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.score-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.score-value.positive {
  color: var(--color-success);
}

.score-value.negative {
  color: var(--color-error);
}

.substitute-metrics {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
}

.metric-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.metric-value {
  font-size: 0.9rem;
  font-weight: 600;
}

.metric-value.positive {
  color: var(--color-success);
}

.metric-value.negative {
  color: var(--color-error);
}

.ingredient-selector {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--color-bg-2);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
}

.selector-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.selector-title:before {
  content: '🥃';
  font-size: 1.3rem;
}

.ingredients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.ingredient-card {
  padding: var(--spacing-md);
  background: linear-gradient(135deg, var(--color-bg-1), rgba(212, 175, 55, 0.05));
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.ingredient-card:hover {
  border-color: var(--color-gold-400);
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.ingredient-card.selected {
  border-color: var(--color-gold-400);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1), rgba(212, 175, 55, 0.2));
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
}

.ingredient-card.selected:before {
  content: '✓';
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  background: var(--color-gold-400);
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

.ingredient-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.ingredient-role {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xs);
  text-transform: capitalize;
}

.ingredient-amount {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-gold-400);
  margin-bottom: var(--spacing-xs);
}

.ingredient-canonical {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-family: var(--font-mono);
  background: rgba(212, 175, 55, 0.1);
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  margin-top: var(--spacing-xs);
}

.main-content-area {
  display: grid;
  grid-template-columns: 35% 65%;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.left-panel {
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.right-panel {
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

@media (max-width: 1200px) {
  .main-content-area {
    grid-template-columns: 1fr;
  }
}

.recipe-select-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  padding: var(--spacing-2xl);
  background: linear-gradient(135deg, var(--color-bg-1), var(--color-bg-2));
}

.recipe-select-card {
  background: linear-gradient(135deg, var(--color-bg-2), rgba(212, 175, 55, 0.05));
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--spacing-2xl);
  max-width: 800px;
  width: 100%;
  border: 2px solid var(--color-border);
  text-align: center;
}

.select-title {
  color: var(--color-gold-200);
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: var(--spacing-md);
  text-align: center;
  font-family: var(--font-serif);
  display: block;
  border-bottom: none;
  padding-bottom: 0;
}

.select-title:before {
  display: none;
}

.select-description {
  color: var(--color-text-secondary);
  text-align: center;
  margin-bottom: var(--spacing-xl);
  font-size: 1.1rem;
  line-height: 1.5;
}

.recipe-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  max-height: 500px;
  overflow-y: auto;
  padding: var(--spacing-md);
  background: var(--color-bg-1);
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
}

.recipe-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  background: var(--color-bg-1);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.recipe-item:hover {
  background: linear-gradient(135deg, var(--color-bg-1), rgba(212, 175, 55, 0.1));
  border-color: var(--color-gold-400);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.recipe-info {
  flex: 1;
  text-align: left;
}

.recipe-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.recipe-source {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.recipe-action {
  color: var(--color-gold-400);
  font-size: 1.5rem;
  font-weight: bold;
  transition: transform 0.3s ease;
}

.recipe-item:hover .recipe-action {
  transform: translateX(5px);
}

/* 组合调整空状态 */
.no-combo-plans {
  text-align: center;
  padding: var(--spacing-3xl) var(--spacing-xl);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.05), rgba(212, 175, 55, 0.1));
  border: 2px dashed var(--color-gold-300);
  border-radius: var(--border-radius-lg);
  margin: var(--spacing-xl) 0;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.no-plans-icon {
  font-size: 4rem;
  margin-bottom: var(--spacing-lg);
  opacity: 0.7;
}

.no-plans-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
  font-family: var(--font-serif);
}

.no-plans-description {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--spacing-xl);
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.no-plans-suggestions {
  text-align: left;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
  background: var(--color-bg-1);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-border);
}

.no-plans-suggestions h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.no-plans-suggestions ul {
  list-style: none;
  padding: 0;
}

.no-plans-suggestions li {
  font-size: 0.95rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-sm);
  padding-left: var(--spacing-lg);
  position: relative;
  line-height: 1.4;
}

.no-plans-suggestions li:before {
  content: '•';
  color: var(--color-gold-400);
  font-weight: bold;
  position: absolute;
  left: 0;
  top: 0;
}

/* 整体布局美化 */
.adjust-view {
  min-height: 100vh;
  background: var(--color-bg-1);
  color: var(--color-text-primary);
}

.page-header {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: white;
  padding: var(--spacing-3xl) 0;
  margin-bottom: var(--spacing-xl);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.page-header:before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPgogIDxkZWZzPgogICAgPHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+CiAgICAgIDxwYXRoIGQ9Ik0gNDAgMCBMIDAgMCAwIDQwIiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMSIgb3BhY2l0eT0iMC4xIi8+CiAgICA8L3BhdHRlcm4+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiIC8+Cjwvc3ZnPg==');
  opacity: 0.3;
}

.page-header-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 800px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl);
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: var(--spacing-md);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-family: var(--font-serif);
}

.page-subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  line-height: 1.5;
}

.adjust-main {
  padding-bottom: var(--spacing-3xl);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-xl);
}

.adjust-tabs {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
  background: var(--color-bg-2);
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.tab-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  font-weight: 500;
  font-family: var(--font-sans);
}

.tab-button:hover {
  background: rgba(212, 175, 55, 0.1);
  color: var(--color-gold-400);
  transform: translateY(-1px);
}

.tab-button.active {
  background: var(--color-gold-400);
  color: white;
  box-shadow: 0 2px 4px rgba(212, 175, 55, 0.3);
  transform: translateY(-1px);
}

.tab-icon {
  font-size: 1.2rem;
}

/* 单个替代调整布局 */
.single-adjust-content {
  background: var(--color-bg-2);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-border);
}

.substitutes-list {
  margin-top: var(--spacing-xl);
}

.substitutes-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.substitutes-title:before {
  content: '🔄';
  font-size: 1.3rem;
}

.substitutes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--spacing-lg);
}

.substitute-card {
  background: linear-gradient(135deg, var(--color-bg-1), rgba(212, 175, 55, 0.05));
  border: 2px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  transition: all 0.3s ease;
  position: relative;
}

.substitute-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  border-color: var(--color-gold-300);
}

/* 组合调整布局 */
.combo-adjust-content {
  background: var(--color-bg-2);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-border);
}

/* 加载和错误状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-4xl);
  text-align: center;
  background: var(--color-bg-2);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--color-border);
  margin: var(--spacing-xl) auto;
  max-width: 400px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(212, 175, 55, 0.3);
  border-radius: 50%;
  border-top: 4px solid var(--color-gold-400);
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-lg);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 1rem;
  color: var(--color-text-secondary);
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-3xl);
  text-align: center;
  background: rgba(244, 67, 54, 0.05);
  border: 2px dashed var(--color-error);
  border-radius: var(--border-radius-lg);
  max-width: 600px;
  margin: var(--spacing-xl) auto;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-lg);
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-error);
  margin-bottom: var(--spacing-md);
}

.error-message {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xl);
  max-width: 400px;
  line-height: 1.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }
  
  .adjust-tabs {
    flex-direction: column;
  }
  
  .tab-button {
    width: 100%;
  }
  
  .ingredients-grid {
    grid-template-columns: 1fr;
  }
  
  .substitutes-grid {
    grid-template-columns: 1fr;
  }
  
  .container {
    padding: 0 var(--spacing-md);
  }
  
  .single-adjust-content,
  .combo-adjust-content {
    padding: var(--spacing-lg);
  }
  
  .recipe-select-card {
    padding: var(--spacing-xl);
  }
  
  .no-combo-plans {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .recipe-select-container {
    padding: var(--spacing-lg);
  }
  
  .select-title {
    font-size: 1.5rem;
  }
  
  .recipe-item {
    padding: var(--spacing-md);
  }
}
</style>
