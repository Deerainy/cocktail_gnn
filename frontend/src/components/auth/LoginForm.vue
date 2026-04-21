<template>
  <div class="login-form">
    <h2 class="form-title">用户登录</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="username">用户名</label>
        <input 
          type="text" 
          id="username" 
          v-model="formData.username" 
          required 
          placeholder="请输入用户名"
        >
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input 
          type="password" 
          id="password" 
          v-model="formData.password" 
          required 
          placeholder="请输入密码"
        >
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <button type="button" class="btn-secondary" @click="$emit('switchToRegister')">
          注册新账号
        </button>
      </div>
      <div v-if="error" class="form-error">
        {{ error }}
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: 'LoginForm',
  emits: ['switchToRegister', 'loginSuccess'],
  data() {
    return {
      formData: {
        username: '',
        password: ''
      },
      loading: false,
      error: ''
    };
  },
  methods: {
    async handleLogin() {
      this.loading = true;
      this.error = '';
      
      try {
        // 模拟登录请求
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 模拟成功响应
        const user = {
          id: 1,
          username: this.formData.username,
          role: 'admin',
          token: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...' // 模拟token
        };
        
        // 存储用户信息到本地存储
        localStorage.setItem('user', JSON.stringify(user));
        
        this.$emit('loginSuccess', user);
      } catch (err) {
        this.error = '登录失败，请检查用户名和密码';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.login-form {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 400px;
  width: 100%;
}

.form-title {
  color: var(--color-gold-200);
  font-family: var(--font-display);
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  text-align: center;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-primary);
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-gold-400);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-primary {
  flex: 1;
  padding: 0.75rem;
  background: var(--color-gold-500);
  color: var(--color-bg-primary);
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-gold-400);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background: var(--color-gold-700);
  cursor: not-allowed;
}

.btn-secondary {
  flex: 1;
  padding: 0.75rem;
  background: transparent;
  color: var(--color-gold-300);
  border: 1px solid var(--color-gold-500);
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(212, 175, 55, 0.1);
}

.form-error {
  margin-top: 1rem;
  padding: 0.75rem;
  background: rgba(255, 87, 34, 0.1);
  border: 1px solid rgba(255, 87, 34, 0.3);
  border-radius: 6px;
  color: #ff5722;
  font-size: 0.9rem;
}
</style>