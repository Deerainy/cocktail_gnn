<template>
  <div class="generate">
    <section class="generate-header">
      <div class="generate-header-inner">
        <h1 class="generate-title">创新生成</h1>
        <p class="generate-subtitle">基于图结构优化的鸡尾酒配方创新</p>
      </div>
    </section>
    
    <section class="generate-content">
      <div class="generate-card card">
        <div class="generate-card-header">
          <h2 class="generate-card-title">生成模式</h2>
          <p class="generate-card-subtitle">选择一种生成方式</p>
        </div>
        <div class="generate-card-body">
          <div class="mode-selector">
            <button 
              class="mode-btn" 
              :class="{ active: selectedMode === 'constrained' }"
              @click="selectedMode = 'constrained'"
            >
              约束生成
            </button>
            <button 
              class="mode-btn" 
              :class="{ active: selectedMode === 'based' }"
              @click="selectedMode = 'based'"
            >
              基于已有配方生成
            </button>
          </div>
        </div>
      </div>
      
      <!-- 约束生成模式 -->
      <div v-if="selectedMode === 'constrained'" class="generate-card card">
        <div class="generate-card-header">
          <h2 class="generate-card-title">约束生成</h2>
          <p class="generate-card-subtitle">选择基酒和风味偏好</p>
        </div>
        <div class="generate-card-body">
          <div class="constraint-form">
            <div class="form-group">
              <label class="form-label">基酒</label>
              <select v-model="constraintForm.base" class="form-select">
                <option value="">请选择基酒</option>
                <option value="gin">金酒</option>
                <option value="vodka">伏特加</option>
                <option value="rum">朗姆酒</option>
                <option value="tequila">龙舌兰</option>
                <option value="whiskey">威士忌</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">风味偏好</label>
              <div class="flavor-preferences">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="constraintForm.flavors" value="citrus" />
                  <span>柑橘</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="constraintForm.flavors" value="herbal" />
                  <span>草本</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="constraintForm.flavors" value="sweet" />
                  <span>甜味</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="constraintForm.flavors" value="sour" />
                  <span>酸味</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="constraintForm.flavors" value="spicy" />
                  <span>辛辣</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="constraintForm.flavors" value="fruity" />
                  <span>果香</span>
                </label>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">酒精含量</label>
              <input 
                type="range" 
                v-model.number="constraintForm.alcohol" 
                min="10" 
                max="40" 
                step="5"
                class="form-range"
              >
              <span class="range-value">{{ constraintForm.alcohol }}%</span>
            </div>
            
            <button 
              class="btn btn-primary" 
              @click="generateConstrained" 
              :disabled="!constraintForm.base || constraintForm.flavors.length === 0"
            >
              {{ isLoading ? '生成中...' : '生成配方' }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- 基于已有配方生成模式 -->
      <div v-if="selectedMode === 'based'" class="generate-card card">
        <div class="generate-card-header">
          <h2 class="generate-card-title">基于已有配方生成</h2>
          <p class="generate-card-subtitle">从现有配方出发进行创新</p>
        </div>
        <div class="generate-card-body">
          <div class="based-form">
            <div class="form-group">
              <label class="form-label">选择基础配方</label>
              <select v-model="basedForm.recipe" class="form-select">
                <option value="">请选择配方</option>
                <option value="margarita">玛格丽特</option>
                <option value="old-fashioned">古典鸡尾酒</option>
                <option value="mojito">莫吉托</option>
                <option value="cosmopolitan"> cosmopolitan</option>
                <option value="negroni">内格罗尼</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">创新程度</label>
              <div class="innovation-level">
                <label class="radio-label">
                  <input type="radio" v-model="basedForm.level" value="conservative" />
                  <span>保守改进</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="basedForm.level" value="moderate" />
                  <span>适度创新</span>
                </label>
                <label class="radio-label">
                  <input type="radio" v-model="basedForm.level" value="radical" />
                  <span>激进创新</span>
                </label>
              </div>
            </div>
            
            <button 
              class="btn btn-primary" 
              @click="generateBased" 
              :disabled="!basedForm.recipe || !basedForm.level"
            >
              {{ isLoading ? '生成中...' : '生成变体' }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- 生成结果 -->
      <div v-if="generatedRecipes.length > 0" class="generate-card card">
        <div class="generate-card-header">
          <h2 class="generate-card-title">生成结果</h2>
          <p class="generate-card-subtitle">基于你的选择生成的配方</p>
        </div>
        <div class="generate-card-body">
          <div class="recipes-list">
            <div 
              v-for="(recipe, index) in generatedRecipes" 
              :key="index"
              class="recipe-item"
            >
              <div class="recipe-header">
                <h3 class="recipe-name">{{ recipe.name }}</h3>
                <div class="recipe-sqe">
                  <span class="sqe-label">SQE:</span>
                  <span class="sqe-value">{{ recipe.sqe.toFixed(2) }}</span>
                </div>
              </div>
              
              <div class="recipe-ingredients">
                <h4 class="ingredients-title">原料</h4>
                <div class="ingredients-list">
                  <div 
                    v-for="(ingredient, i) in recipe.ingredients" 
                    :key="i"
                    class="ingredient-item"
                  >
                    <span class="ingredient-name">{{ ingredient.name }}</span>
                    <span class="ingredient-ratio">{{ ingredient.ratio }}%</span>
                    <span class="ingredient-role">{{ ingredient.role }}</span>
                  </div>
                </div>
              </div>
              
              <div class="recipe-explanation">
                <h4 class="explanation-title">风味解释</h4>
                <p>{{ recipe.explanation }}</p>
              </div>
              
              <div class="recipe-actions">
                <button class="btn btn-sm btn-primary">查看详情</button>
                <button class="btn btn-sm btn-secondary">保存配方</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'GeneratorView',
  data() {
    return {
      selectedMode: 'constrained',
      constraintForm: {
        base: '',
        flavors: [],
        alcohol: 25
      },
      basedForm: {
        recipe: '',
        level: 'conservative'
      },
      generatedRecipes: [],
      isLoading: false
    }
  },
  methods: {
    generateConstrained() {
      this.isLoading = true
      // 模拟API调用
      setTimeout(() => {
        this.generatedRecipes = [
          {
            name: '柑橘金酒鸡尾酒',
            sqe: 0.85,
            ingredients: [
              { name: '金酒', ratio: 40, role: 'base' },
              { name: '柠檬汁', ratio: 20, role: 'acid' },
              { name: '橙皮利口酒', ratio: 15, role: 'sweetener' },
              { name: '苏打水', ratio: 20, role: 'diluent' },
              { name: '柠檬皮', ratio: 5, role: 'garnish' }
            ],
            explanation: '这款鸡尾酒以金酒为基酒，搭配新鲜柠檬汁和橙皮利口酒，创造出明亮的柑橘风味。苏打水的加入使口感更加清爽，整体平衡度良好，适合夏季饮用。'
          },
          {
            name: '草本金酒特调',
            sqe: 0.82,
            ingredients: [
              { name: '金酒', ratio: 45, role: 'base' },
              { name: '接骨木花利口酒', ratio: 15, role: 'sweetener' },
              { name: '青柠汁', ratio: 15, role: 'acid' },
              { name: '薄荷', ratio: 5, role: 'flavor' },
              { name: '苏打水', ratio: 20, role: 'diluent' }
            ],
            explanation: '这款鸡尾酒融合了金酒的草本特性与接骨木花的花香，青柠汁增添了酸度，薄荷则带来清新感。整体风味层次丰富，平衡度佳。'
          }
        ]
        this.isLoading = false
      }, 1500)
    },
    generateBased() {
      this.isLoading = true
      // 模拟API调用
      setTimeout(() => {
        this.generatedRecipes = [
          {
            name: '创新玛格丽特',
            sqe: 0.88,
            ingredients: [
              { name: '龙舌兰', ratio: 45, role: 'base' },
              { name: '青柠汁', ratio: 20, role: 'acid' },
              { name: '橙色利口酒', ratio: 15, role: 'sweetener' },
              { name: '盐边', ratio: 5, role: 'garnish' },
              { name: '西柚汁', ratio: 15, role: 'flavor' }
            ],
            explanation: '这款创新玛格丽特在传统配方基础上加入了西柚汁，增添了额外的果香层次。橙色利口酒替代了传统的君度酒，使风味更加丰富。整体平衡度良好，酸甜适中。'
          },
          {
            name: '烟熏玛格丽特',
            sqe: 0.84,
            ingredients: [
              { name: '梅斯卡尔', ratio: 45, role: 'base' },
              { name: '青柠汁', ratio: 20, role: 'acid' },
              { name: '君度酒', ratio: 15, role: 'sweetener' },
              { name: '盐边', ratio: 5, role: 'garnish' },
              { name: '辣椒盐', ratio: 5, role: 'flavor' },
              { name: '苏打水', ratio: 10, role: 'diluent' }
            ],
            explanation: '这款烟熏玛格丽特使用梅斯卡尔替代传统龙舌兰，带来独特的烟熏风味。辣椒盐的加入增添了微妙的辛辣感，与青柠的酸度形成有趣的对比。整体风味平衡，具有层次感。'
          }
        ]
        this.isLoading = false
      }, 1500)
    }
  }
}
</script>

<style scoped>
.generate {
  min-height: 100vh;
  background: var(--color-bg-1);
}

.generate-header {
  background: linear-gradient(135deg, var(--color-bg-2) 0%, var(--color-bg-3) 100%);
  padding: var(--spacing-xxl) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border-subtle);
}

.generate-header-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.generate-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-serif);
}

.generate-subtitle {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  max-width: 600px;
}

.generate-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
  display: grid;
  gap: var(--spacing-xl);
  grid-template-columns: 1fr;
}

.generate-card {
  padding: var(--spacing-xl);
}

.generate-card-header {
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-md);
}

.generate-card-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-200);
  margin-bottom: var(--spacing-xs);
  font-family: var(--font-serif);
}

.generate-card-subtitle {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.mode-selector {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.mode-btn {
  flex: 1;
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  color: var(--color-text-primary);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.mode-btn:hover {
  border-color: var(--color-gold-400);
  background: var(--color-bg-3);
}

.mode-btn.active {
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.1);
  color: var(--color-gold-300);
}

.constraint-form,
.based-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-label {
  font-weight: 500;
  color: var(--color-text-primary);
  font-size: 1rem;
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

.flavor-preferences {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  color: var(--color-text-primary);
}

.checkbox-label input[type="checkbox"] {
  accent-color: var(--color-gold-400);
}

.form-range {
  width: 100%;
  margin: var(--spacing-sm) 0;
}

.range-value {
  display: block;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-gold-300);
  font-weight: 600;
}

.innovation-level {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.radio-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  color: var(--color-text-primary);
}

.radio-label input[type="radio"] {
  accent-color: var(--color-gold-400);
}

.recipes-list {
  display: grid;
  gap: var(--spacing-lg);
}

.recipe-item {
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-2);
  transition: all var(--transition-normal);
}

.recipe-item:hover {
  border-color: var(--color-gold-400);
  background: var(--color-bg-3);
}

.recipe-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-subtle);
}

.recipe-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-gold-200);
  font-family: var(--font-serif);
}

.recipe-sqe {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.sqe-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.sqe-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-gold-300);
}

.recipe-ingredients,
.recipe-explanation {
  margin-bottom: var(--spacing-md);
}

.ingredients-title,
.explanation-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.ingredients-list {
  display: grid;
  gap: var(--spacing-sm);
}

.ingredient-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm);
  background: var(--color-bg-3);
  border-radius: var(--radius-sm);
}

.ingredient-name {
  flex: 1;
  font-weight: 500;
  color: var(--color-text-primary);
}

.ingredient-ratio {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.ingredient-role {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-2);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  color: var(--color-gold-300);
}

.recipe-explanation p {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

.recipe-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border-subtle);
}

.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .generate-header {
    padding: var(--spacing-xl) var(--spacing-md);
  }
  
  .generate-content {
    padding: var(--spacing-md);
  }
  
  .generate-card {
    padding: var(--spacing-lg);
  }
  
  .mode-selector {
    flex-direction: column;
  }
  
  .flavor-preferences {
    flex-direction: column;
  }
  
  .ingredient-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-xs);
  }
  
  .recipe-actions {
    flex-direction: column;
  }
}
</style>