<template>
  <div class="app">
    <header class="header">
      <div class="header-inner">
        <div class="brand">
                  <img class="brand-logo" src="@/assets/logo.png" alt="Cocktail System Logo">
                </div>
        <nav class="nav">
          <router-link 
            v-for="item in navItems" 
            :key="item.path"
            :to="item.path"
            class="nav-link"
            :class="{ active: $route.path === item.path }"
          >
            {{ item.name }}
          </router-link>
        </nav>
      </div>
    </header>
    
    <main class="main">
      <router-view />
    </main>
    
    <footer class="footer">
      <div class="footer-inner">
        <div class="footer-left">
          <span class="footer-logo">COCKTAIL & JAZZ</span>
          <span class="footer-desc">基于图结构优化的鸡尾酒风味组合生成系统 © 2026</span>
        </div>
        <div class="footer-right">
          <span class="footer-text">让数据科学遇见调酒艺术 · 探索风味的无限可能</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      navItems: [
        { name: '首页', path: '/' },
        { name: '配方分析', path: '/recipe' },
        { name: '风味图谱', path: '/graph' },
        { name: '组合调整', path: '/adjust' },
        { name: '创新生成', path: '/generate' },
        { name: '关于系统', path: '/about' }
      ]
    };
  }
};
</script>

<style>
@import './styles/jazz-theme.css';

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: transparent;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-sm) var(--spacing-xl);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-xl);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  flex-shrink: 0;
}

.brand-logo {
  width: 100px;
  height: 45px;
  margin-left: -20px;
  flex-shrink: 0;
}

.brand-icon {
  width: 40px;
  height: 40px;
  color: var(--color-gold-400);
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-gold-200);
  letter-spacing: 0.02em;
}

.brand-subtitle {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-text-tertiary);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.nav {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.nav-link {
  position: relative;
  padding: calc(var(--spacing-sm) + 2px) var(--spacing-md);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  letter-spacing: 0.03em;
  display: flex;
  align-items: center;
  height: 100%;
  min-height: 44px;
}

.nav-link::before {
  content: '';
  position: absolute;
  bottom: 8px;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--color-gold-400);
  transform: translateX(-50%);
  transition: width var(--transition-normal);
  border-radius: 1px;
}

.nav-link:hover {
  color: var(--color-gold-200);
  /* background: rgba(212, 175, 55, 0.1); */
  transform: translateY(-1px);
}

.nav-link:hover::before {
  width: 24px;
}

.nav-link.active {
  color: var(--color-gold-200);
  /* background: rgba(212, 175, 55, 0.15);
  box-shadow: 0 2px 8px rgba(212, 175, 55, 0.1); */
}

.nav-link.active::before {
  width: 24px;
}

.main {
  flex: 1;
  width: 100%;
}

.footer {
  border-top: 1px solid var(--color-border-subtle);
  background: linear-gradient(0deg, rgba(10, 7, 5, 0.98) 0%, rgba(10, 7, 5, 0.95) 100%);
  margin-top: auto;
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-xl);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-xl);
}

.footer-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.footer-logo {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-gold-300);
  letter-spacing: 0.08em;
}

.footer-desc {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.footer-right {
  text-align: right;
}

.footer-text {
  font-family: var(--font-display);
  font-size: 14px;
  color: var(--color-text-secondary);
  font-style: italic;
}
</style>
