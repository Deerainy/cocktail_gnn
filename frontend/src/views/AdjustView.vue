<template>
  <div class="adjust">
    <section class="adjust-header">
      <div class="adjust-header-inner">
        <h1 class="adjust-title">组合调整</h1>
        <p class="adjust-subtitle">优化你的鸡尾酒配方，提升风味体验</p>
      </div>
    </section>
    
    <section class="adjust-content">
      <div class="adjust-card card">
        <div class="adjust-card-header">
          <h2 class="adjust-card-title">选择配方</h2>
        </div>
        <div class="adjust-card-body">
          <div class="recipe-selector">
            <label class="form-label">从配方分析中选择</label>
            <select v-model="selectedRecipe" class="form-select">
              <option value="">请选择一个配方</option>
              <option v-for="recipe in recipes" :key="recipe.id" :value="recipe">
                {{ recipe.name }}
              </option>
            </select>
          </div>
        </div>
      </div>
      
      <div v-if="selectedRecipe" class="adjust-card card">
        <div class="adjust-card-header">
          <h2 class="adjust-card-title">当前配方</h2>
        </div>
        <div class="adjust-card-body">
          <div class="recipe-info">
            <h3 class="recipe-name">{{ selectedRecipe.name }}</h3>
            <div class="ingredients-list">
              <div 
                v-for="(ingredient, index) in selectedRecipe.ingredients" 
                :key="index"
                class="ingredient-item"
                @click="selectIngredient(ingredient)"
                :class="{ active: selectedIngredient && selectedIngredient.id === ingredient.id }"
              >
                <div class="ingredient-name">{{ ingredient.name }}</div>
                <div class="ingredient-role">{{ ingredient.role }}</div>
                <div class="ingredient-ratio">{{ ingredient.ratio }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="selectedIngredient" class="adjust-card card">
        <div class="adjust-card-header">
          <h2 class="adjust-card-title">原料调整</h2>
          <div class="adjust-card-subtitle">当前选择：{{ selectedIngredient.name }}</div>
        </div>
        <div class="adjust-card-body">
          <div class="adjust-options">
            <button 
              class="btn btn-primary" 
              @click="showSubstitutes"
              :disabled="isLoading"
            >
              {{ isLoading ? '加载中...' : '寻找替代原料' }}
            </button>
            <button 
              class="btn btn-secondary" 
              @click="optimizeIngredient"
              :disabled="isLoading"
            >
              {{ isLoading ? '加载中...' : '优化比例' }}
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="substitutes.length > 0" class="adjust-card card">
        <div class="adjust-card-header">
          <h2 class="adjust-card-title">替代候选</h2>
          <div class="adjust-card-subtitle">基于风味相似性和ΔSQE排序</div>
        </div>
        <div class="adjust-card-body">
          <div class="substitutes-list">
            <div 
              v-for="(substitute, index) in substitutes" 
              :key="index"
              class="substitute-item"
              :class="{ recommended: substitute.accept_flag }"
            >
              <div class="substitute-info">
                <div class="substitute-name">{{ substitute.name }}</div>
                <div class="substitute-similarity">相似度: {{ substitute.similarity }}%</div>
              </div>
              <div class="substitute-sqe">
                <div class="sqe-change" :class="substitute.delta_sqe >= 0 ? 'positive' : 'negative'">
                  ΔSQE: {{ substitute.delta_sqe > 0 ? '+' : '' }}{{ substitute.delta_sqe.toFixed(2) }}
                </div>
              </div>
              <div class="substitute-explanation">
                <p>{{ substitute.explanation }}</p>
              </div>
              <div class="substitute-actions">
                <button class="btn btn-sm btn-primary">应用</button>
                <button class="btn btn-sm btn-secondary">查看详情</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="optimizationResult" class="adjust-card card">
        <div class="adjust-card-header">
          <h2 class="adjust-card-title">优化结果</h2>
        </div>
        <div class="adjust-card-body">
          <div class="optimization-info">
            <div class="optimization-item">
              <span class="optimization-label">建议比例:</span>
              <span class="optimization-value">{{ optimizationResult.suggested_ratio }}%</span>
            </div>
            <div class="optimization-item">
              <span class="optimization-label">原始比例:</span>
              <span class="optimization-value">{{ optimizationResult.original_ratio }}%</span>
            </div>
            <div class="optimization-item">
              <span class="optimization-label">ΔSQE:</span>
              <span class="optimization-value" :class="optimizationResult.delta_sqe >= 0 ? 'positive' : 'negative'">
                {{ optimizationResult.delta_sqe > 0 ? '+' : '' }}{{ optimizationResult.delta_sqe.toFixed(2) }}
              </span>
            </div>
            <div class="optimization-explanation">
              <p>{{ optimizationResult.explanation }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'AdjustView',
  data() {
    return {
      recipes: [
        {
          id: 1,
          name: 'Margarita',
          ingredients: [
            { id: 1, name: 'Tequila', role: 'base', ratio: 50 },
            { id: 2, name: 'Triple Sec', role: 'sweetener', ratio: 25 },
            { id: 3, name: 'Lime Juice', role: 'acid', ratio: 25 }
          ]
        },
        {
          id: 2,
          name: 'Old Fashioned',
          ingredients: [
            { id: 4, name: 'Bourbon', role: 'base', ratio: 80 },
            { id: 5, name: 'Sugar', role: 'sweetener', ratio: 10 },
            { id: 6, name: 'Bitters', role: 'flavor', ratio: 10 }
          ]
        },
        {
          id: 3,
          name: 'Mojito',
          ingredients: [
            { id: 7, name: 'Rum', role: 'base', ratio: 60 },
            { id: 8, name: 'Lime Juice', role: 'acid', ratio: 20 },
            { id: 9, name: 'Sugar', role: 'sweetener', ratio: 10 },
            { id: 10, name: 'Mint', role: 'flavor', ratio: 10 }
          ]
        }
      ],
      selectedRecipe: null,
      selectedIngredient: null,
      substitutes: [],
      optimizationResult: null,
      isLoading: false
    }
  },
  methods: {
    selectIngredient(ingredient) {
      this.selectedIngredient = ingredient
      this.substitutes = []
      this.optimizationResult = null
    },
    showSubstitutes() {
      this.isLoading = true
      // 模拟API调用
      setTimeout(() => {
        this.substitutes = [
          {
            name: 'Mezcal',
            similarity: 85,
            delta_sqe: 0.05,
            accept_flag: true,
            explanation: 'Mezcal 与 Tequila 风味相似，但带有独特的烟熏味，可以为 Margarita 增添层次感。'
          },
          {
            name: 'Vodka',
            similarity: 60,
            delta_sqe: -0.12,
            accept_flag: false,
            explanation: 'Vodka 味道较淡，会减弱 Margarita 的独特风味。'
          },
          {
            name: 'Gin',
            similarity: 50,
            delta_sqe: -0.20,
            accept_flag: false,
            explanation: 'Gin 的 juniper 风味与 Margarita 的柑橘味可能产生冲突。'
          }
        ]
        this.isLoading = false
      }, 1000)
    },
    optimizeIngredient() {
      this.isLoading = true
      // 模拟API调用
      setTimeout(() => {
        this.optimizationResult = {
          suggested_ratio: 55,
          original_ratio: this.selectedIngredient.ratio,
          delta_sqe: 0.08,
          explanation: '增加 Tequila 的比例可以增强鸡尾酒的主体风味，提升整体协调性。'
        }
        this.isLoading = false
      }, 1000)
    }
  }
}
</script>

<style scoped>
.adjust {
  min-height: 100vh;
  background: var(--color-bg-1);
}

.adjust-header {
  background: linear-gradient(135deg, var(--color-bg-2) 0%, var(--color-bg-3) 100%);
  padding: var(--spacing-xxl) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border-subtle);
}

.adjust-header-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.adjust-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-serif);
}

.adjust-subtitle {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  max-width: 600px;
}

.adjust-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
  display: grid;
  gap: var(--spacing-xl);
  grid-template-columns: 1fr;
}

.adjust-card {
  padding: var(--spacing-xl);
}

.adjust-card-header {
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-md);
}

.adjust-card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-xs);
  font-family: var(--font-serif);
}

.adjust-card-subtitle {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.recipe-selector {
  margin-bottom: var(--spacing-lg);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.form-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  color: var(--color-text-primary);
  font-size: 1rem;
  transition: all var(--transition-normal);
}

.form-select:focus {
  outline: none;
  border-color: var(--color-gold-400);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
}

.recipe-name {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-md);
  font-family: var(--font-serif);
}

.ingredients-list {
  display: grid;
  gap: var(--spacing-sm);
}

.ingredient-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.ingredient-item:hover {
  border-color: var(--color-gold-400);
  background: var(--color-bg-3);
}

.ingredient-item.active {
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.1);
}

.ingredient-name {
  flex: 1;
  font-weight: 500;
  color: var(--color-text-primary);
}

.ingredient-role {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-3);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  color: var(--color-gold-300);
  margin: 0 var(--spacing-md);
}

.ingredient-ratio {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.adjust-options {
  display: flex;
  gap: var(--spacing-md);
}

.substitutes-list {
  display: grid;
  gap: var(--spacing-md);
}

.substitute-item {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  transition: all var(--transition-normal);
}

.substitute-item.recommended {
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.05);
}

.substitute-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.substitute-name {
  font-weight: 500;
  color: var(--color-text-primary);
}

.substitute-similarity {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.substitute-sqe {
  margin-bottom: var(--spacing-sm);
}

.sqe-change {
  font-weight: 600;
  font-size: 1.1rem;
}

.sqe-change.positive {
  color: #4caf50;
}

.sqe-change.negative {
  color: #f44336;
}

.substitute-explanation {
  margin-bottom: var(--spacing-md);
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.substitute-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.optimization-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.optimization-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
}

.optimization-label {
  color: var(--color-text-secondary);
}

.optimization-value {
  font-weight: 600;
  color: var(--color-text-primary);
}

.optimization-value.positive {
  color: #4caf50;
}

.optimization-value.negative {
  color: #f44336;
}

.optimization-explanation {
  padding: var(--spacing-md);
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .adjust-header {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .adjust-content {
    padding: var(--spacing-md);
  }
  
  .adjust-card {
    padding: var(--spacing-lg);
  }
  
  .adjust-options {
    flex-direction: column;
  }
  
  .ingredient-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .ingredient-role {
    margin: 0;
  }
}
</style>