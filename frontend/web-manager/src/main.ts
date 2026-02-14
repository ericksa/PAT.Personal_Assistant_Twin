import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Index from './views/Index.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Index },
  { path: '/chat', name: 'Chat', component: () => import('./views/Chat.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')