import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Writer from '@/views/Writer.vue'
import { useAuthStore } from '@/store/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      component: Login
    },
    {
      path: '/writer',
      component: Writer
    }
  ]
})

// 路由守卫：未登录不能进写作页
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.path === '/writer' && !auth.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
