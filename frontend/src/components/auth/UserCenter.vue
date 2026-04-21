<template>
  <div class="user-center">
    <div v-if="user" class="user-info">
      <div class="user-avatar" @click="toggleMenu">{{ user.username.charAt(0).toUpperCase() }}</div>
      <div class="user-menu" v-if="showMenu">
        <div class="menu-item">{{ user.username }}</div>
        <div class="menu-divider"></div>
        <div class="menu-item" @click="goToAdmin">后台管理</div>
        <div class="menu-item" @click="logout">退出登录</div>
      </div>
    </div>
    <div v-else class="login-register">
      <button class="btn-login" @click="showAuthModal = true">登录/注册</button>
    </div>
    
    <!-- 认证模态框 -->
    <div v-if="showAuthModal" class="auth-modal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ isLogin ? '用户登录' : '用户注册' }}</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <LoginForm 
            v-if="isLogin" 
            @switchToRegister="isLogin = false" 
            @loginSuccess="handleAuthSuccess"
          />
          <RegisterForm 
            v-else 
            @switchToLogin="isLogin = true" 
            @registerSuccess="handleAuthSuccess"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import LoginForm from './LoginForm.vue';
import RegisterForm from './RegisterForm.vue';

export default {
  name: 'UserCenter',
  components: {
    LoginForm,
    RegisterForm
  },
  data() {
    return {
      user: null,
      showMenu: false,
      showAuthModal: false,
      isLogin: true
    };
  },
  mounted() {
    this.loadUser();
    // 添加点击外部关闭菜单的事件监听
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    // 移除事件监听
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    loadUser() {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        this.user = JSON.parse(userStr);
      }
    },
    toggleMenu() {
      this.showMenu = !this.showMenu;
    },
    closeMenu() {
      this.showMenu = false;
    },
    closeModal() {
      this.showAuthModal = false;
    },
    handleClickOutside(event) {
      const userCenter = this.$el;
      if (userCenter && !userCenter.contains(event.target)) {
        this.showMenu = false;
      }
    },
    handleAuthSuccess(user) {
      this.user = user;
      this.showAuthModal = false;
    },
    logout() {
      localStorage.removeItem('user');
      this.user = null;
      this.showMenu = false;
    },
    goToAdmin() {
      this.$router.push('/admin');
      this.showMenu = false;
    }
  }
};
</script>

<style scoped>
.user-center {
  position: relative;
}

.user-info {
  position: relative;
  cursor: pointer;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-gold-500);
  color: var(--color-bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s ease;
}

.user-avatar:hover {
  background: var(--color-gold-400);
  transform: scale(1.05);
}

.user-menu {
  position: absolute;
  top: 50px;
  right: 0;
  background: rgba(20, 15, 10, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.5rem 0;
  min-width: 150px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  z-index: 1000;
}

.menu-item {
  padding: 0.75rem 1rem;
  color: var(--color-text-secondary);
  transition: all 0.3s ease;
  cursor: pointer;
}

.menu-item:hover {
  background: rgba(212, 175, 55, 0.1);
  color: var(--color-gold-200);
}

.menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 0.5rem 0;
}

.login-register {
  display: flex;
  align-items: center;
}

.btn-login {
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--color-gold-300);
  border: 1px solid var(--color-gold-500);
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-login:hover {
  background: rgba(212, 175, 55, 0.1);
}

.auth-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: rgba(20, 15, 10, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  max-width: 450px;
  width: 100%;
  margin: 2rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  color: var(--color-gold-200);
  font-family: var(--font-display);
  font-size: 1.25rem;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 1.5rem;
  cursor: pointer;
  transition: color 0.3s ease;
}

.close-btn:hover {
  color: var(--color-gold-200);
}

.modal-body {
  padding: 2rem;
  display: flex;
  justify-content: center;
}
</style>