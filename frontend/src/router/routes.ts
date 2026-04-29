import type { RouteRecordRaw } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 布局组件
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import BlankLayout from '@/layouts/BlankLayout.vue'
import FullScreenLayout from '@/layouts/FullScreenLayout.vue'

// 扩展 RouteMeta 类型
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    icon?: string
    layout?: any
    requiresAuth?: boolean
    affix?: boolean
    roles?: string[]  // 允许访问的角色白名单
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { layout: BlankLayout, title: '登录', requiresAuth: false },
  },
  {
    path: '/',
    component: DefaultLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '仪表盘', icon: 'Odometer', affix: true },
      },
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/user/UserListView.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['admin', 'user'] },
      },
      {
        path: 'devices',
        name: 'DeviceList',
        component: () => import('@/views/device/DeviceListView.vue'),
        meta: { title: '设备管理', icon: 'Monitor', roles: ['admin', 'user'] },
      },
      {
        path: 'template',
        name: 'DataUpdate',
        redirect: '/template/update',
        meta: { title: '数据管理', icon: 'Document' },
        children: [
          {
            path: '',
            redirect: '/template/update',
          },
          {
            path: 'update',
            name: 'DataUpdateMain',
            component: () => import('@/views/template/TemplateUpdateView.vue'),
            meta: { roles: ['admin', 'user', 'operator'] },
          },
          {
            path: 'history',
            name: 'UpdateHistory',
            component: () => import('@/views/template/HistoryPage.vue'),
            meta: { title: '更新历史', roles: ['admin', 'user', 'operator'] },
          },
        ],
      },
      {
        path: 'template/manage',
        name: 'TemplateManage',
        component: () => import('@/views/template/TemplateManageView.vue'),
        meta: { title: '模板管理', icon: 'Files', roles: ['admin', 'user'] },
      },
      {
        path: 'batch',
        name: 'BatchEdit',
        component: () => import('@/views/batch/BatchEditView.vue'),
        meta: { title: '批量操作', icon: 'Files', roles: ['admin', 'user'] },
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: FullScreenLayout,
        redirect: '/monitor/view',
        meta: { title: '实时监控', icon: 'DataLine', roles: ['admin', 'user', 'operator'] },
        children: [
          {
            path: 'view',
            name: 'MonitorView',
            component: () => import('@/views/monitor/MonitorView.vue'),
          },
        ],
      },
    ],
  },
  {
    // 404
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404View.vue'),
    meta: { layout: BlankLayout, title: '404' },
  },
]

export default routes

/**
 * 路由守卫配置
 */
export function setupRouterGuards(routerInstance: any) {
  const authStore = () => import('@/stores/auth').then(m => m.useAuthStore())
  
  routerInstance.beforeEach(async (to, _from, next) => {
    NProgress.start()
    
    // 设置页面标题
    if (to.meta?.title) {
      document.title = `${to.meta.title} - WIFI标签管理系统`
    }
    
    // 检查是否需要认证
    const requiresAuth = to.meta?.requiresAuth !== false
    
    if (requiresAuth) {
      const store = await authStore()
      
      // 检查登录状态
      const isAuthenticated = store.isAuthenticated || store.checkAuth()
      
      if (!isAuthenticated) {
        // 未登录，跳转到登录页
        next({
          name: 'Login',
          query: { redirect: to.fullPath },
        })
        return
      }

      // 角色权限检查
      if (to.meta?.roles?.length) {
        const role = store.getUserRole()
        if (!to.meta.roles.includes(role)) {
          // 无权访问，重定向到仪表盘
          next({ name: 'Dashboard' })
          return
        }
      }
    }
    
    next()
  })
  
  routerInstance.afterEach(() => {
    NProgress.done()
  })
}
