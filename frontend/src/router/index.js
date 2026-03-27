import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import RecipeView from '../views/RecipeView.vue';
import VisualizationView from '../views/VisualizationView.vue';
import AdjustView from '../views/AdjustView.vue';
import GraphView from '../views/GraphView.vue';
import GeneratorView from '../views/GeneratorView.vue';
import AboutView from '../views/AboutView.vue';

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/recipe', name: 'recipe', component: RecipeView },
  { path: '/visualization', name: 'visualization', component: VisualizationView },
  { path: '/adjust', name: 'adjust', component: AdjustView },
  { path: '/graph', name: 'graph', component: GraphView },
  { path: '/generate', name: 'generate', component: GeneratorView },
  { path: '/about', name: 'about', component: AboutView }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  }
});

export default router;
