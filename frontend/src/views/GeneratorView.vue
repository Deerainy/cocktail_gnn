<template>
  <div class="generate">
    <section class="generate-header">
      <div class="generate-header-inner">
        <h1 class="generate-title">创新生成</h1>
        <p class="generate-subtitle">基于图结构优化的鸡尾酒配方创新</p>
      </div>
    </section>
    
    <section class="generate-content">
      <InnovationGenerator />
    </section>
  </div>
</template>

<script>
import InnovationGenerator from '../components/innovation/InnovationGenerator.vue';

export default {
  name: 'GeneratorView',
  components: {
    InnovationGenerator
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