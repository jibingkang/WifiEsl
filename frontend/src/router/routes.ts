import type { RouteRecordRaw } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// 布局组件
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import BlankLayout from '@/layouts/BlankLayout.vue'
import FullScreenLayout from '@/layouts/FullScreenLayout.vue'

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
        path: 'devices',
        name: 'DeviceList',
        component: () => import('@/views/device/DeviceListView.vue'),
        meta: { title: '设备管理', icon: 'Monitor' },
      },
      {
        path: 'template',
        name: 'DataUpdate',
        redirect: '/template/update',
        meta: { title: '数据更新', icon: 'Document' },
        children: [
          {
            path: '',
            redirect: '/template/update',
          },
          {
            path: 'update',
            name: 'DataUpdateMain',
            component: () => import('@/views/template/TemplateUpdateView.vue'),
          },
          {
            path: 'history',
            name: 'UpdateHistory',
            component: () => import('@/views/template/HistoryPage.vue'),
            meta: { title: '更新历史' },
          },
        ],
      },
      {
        path: 'template/manage',
        name: 'TemplateManage',
        component: () => import('@/views/template/TemplateManageView.vue'),
        meta: { title: '模板管理', icon: 'Files' },
      },
      {
        path: 'batch',
        name: 'BatchEdit',
        component: () => import('@/views/batch/BatchEditView.vue'),
        meta: { title: '批量操作', icon: 'Files' },
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: FullScreenLayout,
        redirect: '/monitor/view',
        meta: { title: '实时监控', icon: 'DataLine' },
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
  const userStore = () => import('@/stores/user').then(m => m.useUserStore())
  
  routerInstance.beforeEach(async (to, _from, next) => {
    NProgress.start()
    
    // 设置页面标题
    if (to.meta?.title) {
      document.title = `${to.meta.title} - WIFI标签管理系统`
    }
    
    // 检查是否需要认证
    const requiresAuth = to.meta?.requiresAuth !== false
    
    if (requiresAuth) {
      const store = await userStore()
      
      if (!store.token) {
        // 未登录，跳转到登录页
        next({
          name: 'Login',
          query: { redirect: to.fullPath },
        })
        return
      }
    }
    
    next()
  })
  
  routerInstance.afterEach(() => {
    NProgress.done()
  })
}
