<template>
  <div class="default-layout" :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
      <!-- Logo区域 -->
      <div class="sidebar-logo" @click="$router.push('/')">
        <div class="logo-icon">
          <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="40" height="40" rx="10" fill="url(#logo-gradient)" />
            <path d="M12 28V14h3l5 9 5-9h3v14h-3v-8l-4.5 7h-1L15 20v8h-3z" fill="white" />
            <defs>
              <linearGradient id="logo-gradient" x1="0" y1="0" x2="40" y2="40">
                <stop stop-color="#6366f1" />
                <stop offset="1" stop-color="#8b5cf6" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <transition name="fade">
          <span v-show="!appStore.sidebarCollapsed" class="logo-text">WIFI标签</span>
        </transition>
      </div>

      <!-- 导航菜单 -->
      <el-scrollbar class="sidebar-menu-wrap">
        <el-menu
          :default-active="activeMenu"
          :collapse="appStore.sidebarCollapsed"
          router
          :collapse-transition="false"
          class="sidebar-menu"
        >
          <template v-for="item in menuItems" :key="item.path">
            <el-menu-item :index="item.path">
              <component :is="item.icon" class="menu-icon" />
              <template #title>
                <span>{{ item.title }}</span>
              </template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>

      <!-- 底部信息 -->
      <div class="sidebar-footer">
        <div v-if="!appStore.sidebarCollapsed" class="version-info">
          <div class="version-line" title="前端版本">FE v{{ frontendVersion }}</div>
          <div class="version-line" title="后端版本">BE v{{ backendVersion || '...' }}</div>
          <div class="version-line build-time" title="前端编译时间">{{ buildTime }}</div>
          <div v-if="backendStartTime" class="version-line build-time" title="后端启动时间">↑ {{ backendStartTime }}</div>
        </div>
      </div>
    </aside>

    <!-- 遮罩层（移动端） -->
    <div 
      v-if="isMobile && !appStore.sidebarCollapsed" 
      class="sidebar-overlay"
      @click="appStore.toggleSidebar()"
    />

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶栏 -->
      <header class="header">
        <div class="header-left">
          <!-- 折叠按钮 -->
          <el-button 
            class="collapse-btn" 
            @click="appStore.toggleSidebar()"
          >
            <PanelLeftClose v-if="!appStore.sidebarCollapsed" :size="20" />
            <PanelLeftOpen v-else :size="20" />
          </el-button>

          <!-- 面包屑 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta?.title">
              {{ currentRoute.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 搜索 -->
          <el-input
            v-model="searchText"
            placeholder="搜索..."
            class="search-box"
            prefix-icon="Search"
            clearable
            size="default"
          />

          <!-- MQTT连接状态 -->
          <el-tooltip content="MQTT连接状态" placement="bottom">
            <div class="mqtt-status" :class="{ connected: mqttConnected }">
              <span class="status-dot" />
              <span v-if="!isMobile" class="status-text">{{ mqttConnected ? '已连接' : '未连接' }}</span>
            </div>
          </el-tooltip>

          <!-- 主题切换 -->
          <ThemeToggle />

          <!-- 全屏 -->
          <el-tooltip content="全屏" placement="bottom">
            <el-button text circle @click="toggleFullscreen">
              <FullScreen />
            </el-button>
          </el-tooltip>

          <!-- 用户下拉 -->
          <el-dropdown trigger="click" @command="handleUserCommand">
            <div class="user-avatar">
              <el-avatar :size="32" icon="UserFilled" :style="avatarStyle" />
              <div v-if="!isMobile" class="user-info">
                <span class="user-name">{{ authStore.userInfo?.username || '用户' }}</span>
                <el-tag :type="roleTagType" size="small" class="role-tag">{{ roleLabel }}</el-tag>
              </div>
              <ArrowDown class="arrow-icon" />
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <User /> 个人信息
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <SwitchButton /> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="main-content">
        <router-view v-slot="{ Component, route }">
          <transition name="slide-fade" mode="out-in">
            <component :is="Component" :key="route.path" class="page-content" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- 个人信息弹窗 -->
    <el-dialog v-model="profileVisible" title="个人信息" width="480px" @close="handleProfileClose">
      <div v-loading="profileLoading" class="profile-content">
        <template v-if="profileData">
          <div class="profile-header">
            <el-avatar :size="64" icon="UserFilled" :style="avatarStyle" />
            <div class="profile-header-info">
              <h3>{{ profileData.username }}</h3>
              <el-tag :type="roleTagType" size="default">{{ roleLabel }}</el-tag>
            </div>
          </div>
          <el-descriptions :column="1" border class="profile-desc">
            <el-descriptions-item label="用户ID">{{ profileData.id }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ profileData.username }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ roleLabel }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="profileData.status === 'active' ? 'success' : 'danger'" size="small">
                {{ profileData.status === 'active' ? '正常' : '禁用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="WIFI用户名">{{ profileData.wifi_username || '-' }}</el-descriptions-item>
            <el-descriptions-item label="WIFI地址">{{ profileData.wifi_base_url || '-' }}</el-descriptions-item>
            <el-descriptions-item label="MQTT Broker">{{ profileData.wifi_mqtt_broker || '-' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ profileData.created_at || '-' }}</el-descriptions-item>
            <el-descriptions-item v-if="profileData.parent_user_id" label="所属上级ID">{{ profileData.parent_user_id }}</el-descriptions-item>
          </el-descriptions>
        </template>
        <el-empty v-else-if="!profileLoading" description="获取信息失败" />
      </div>
      <template #footer>
        <el-button @click="profileVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 设备告警弹窗（登录后自动弹出） -->
    <el-dialog
      v-model="alertVisibleRef"
      title=""
      width="560px"
      :close-on-click-modal="true"
      class="device-alert-dialog"
    >
      <div class="alert-dialog-body">
        <!-- 全部正常 -->
        <template v-if="allNormalRef">
          <div class="alert-header">
            <div class="alert-icon-wrap success">
              <CheckCircle :size="24" />
            </div>
            <div class="alert-title-group">
              <h3 class="alert-title">设备状态正常</h3>
              <p class="alert-subtitle">所有设备运行正常，无需关注</p>
            </div>
          </div>
        </template>

        <!-- 有异常 -->
        <template v-else>
          <!-- 标题区 -->
          <div class="alert-header">
            <div class="alert-icon-wrap warning">
              <AlertTriangle :size="24" />
            </div>
            <div class="alert-title-group">
              <h3 class="alert-title">设备状态告警</h3>
              <p class="alert-subtitle">系统检测到以下设备需要关注</p>
            </div>
          </div>

          <!-- 离线设备 -->
          <div v-if="alertDataRef?.offline_count" class="alert-section offline">
            <div class="section-header">
              <WifiOff :size="16" />
              <span class="section-title">离线设备 ({{ alertDataRef.offline_count }}台)</span>
            </div>
            <div class="device-list">
              <div
                v-for="dev in alertDataRef.offline_devices"
                :key="dev.mac"
                class="device-card"
              >
                <div class="device-info">
                  <span class="device-mac">{{ dev.mac }}</span>
                  <span v-if="dev.name && dev.name !== dev.mac" class="device-name">{{ dev.name }}</span>
                  <span v-if="dev.voltage != null && dev.voltage !== 0" class="device-volt">{{ formatVolt(dev.voltage) }}</span>
                  <el-tag size="small" type="danger" class="device-tag">离线</el-tag>
                </div>
                <div v-if="dev.last_seen_at" class="device-meta">
                  最后在线: {{ formatRelativeTime(dev.last_seen_at) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 低电量设备 -->
          <div v-if="alertDataRef?.low_battery_count" class="alert-section low-battery">
            <div class="section-header">
              <BatteryLow :size="16" />
              <span class="section-title">低电量 ({{ alertDataRef.low_battery_count }}台)</span>
            </div>
            <div class="device-list">
              <div
                v-for="dev in alertDataRef.low_battery_devices"
                :key="dev.mac"
                class="device-card"
              >
                <div class="device-info">
                  <span class="device-mac">{{ dev.mac }}</span>
                  <span v-if="dev.name && dev.name !== dev.mac" class="device-name">{{ dev.name }}</span>
                  <span v-if="dev.voltage != null && dev.voltage !== 0" class="device-volt low">{{ formatVolt(dev.voltage) }}</span>
                  <el-tag size="small" :type="dev.is_online ? 'success' : 'danger'" class="device-tag">
                    {{ dev.is_online ? '在线' : '离线' }}
                  </el-tag>
                </div>
                <div v-if="dev.last_seen_at" class="device-meta">
                  {{ formatRelativeTime(dev.last_seen_at) }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <template #footer>
        <div class="alert-footer">
          <el-button @click="loginAlert.dismissAlert()">知道了</el-button>
          <el-button v-if="!allNormalRef" type="primary" @click="goToMonitor">
            <Monitor :size="14" style="margin-right: 4px;" />
            查看详情
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Search, FullScreen, UserFilled,
  ArrowDown, User, SwitchButton,
  Odometer, Monitor, Document, FolderOpened, TrendCharts, Clock
} from '@element-plus/icons-vue'
import { PanelLeftClose, PanelLeftOpen, AlertTriangle, WifiOff, BatteryLow, CheckCircle } from 'lucide-vue-next'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import { useBackendWs } from '@/composables/useBackendWs'
import { useLoginAlert } from '@/composables/useLoginAlert'
import { formatVolt, formatRelativeTime } from '@/utils/format'
import service from '@/api/index'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const { mqttConnected } = useBackendWs()
const loginAlert = useLoginAlert()
const { alertVisible: alertVisibleRef, alertData: alertDataRef, allNormal: allNormalRef } = loginAlert

// 版本信息
const frontendVersion = __APP_VERSION__
const buildTime = __BUILD_TIME__
const backendVersion = ref('')
const backendStartTime = ref('')

// 状态
const searchText = ref('')
const isMobile = ref(window.innerWidth < 768)

// 计算属性
const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)

// 角色相关
const roleLabel = computed(() => {
  const roleMap: Record<string, string> = { admin: '管理员', user: '用户', operator: '操作员' }
  return roleMap[authStore.getUserRole()] || '用户'
})
const roleTagType = computed(() => {
  const typeMap: Record<string, string> = { admin: 'danger', user: 'warning', operator: 'info' }
  return typeMap[authStore.getUserRole()] || 'info'
})
const avatarStyle = computed(() => {
  const colorMap: Record<string, string> = { admin: '#f56c6c', user: '#e6a23c', operator: '#909399' }
  return { backgroundColor: colorMap[authStore.getUserRole()] || '#409eff' }
})

// 个人信息弹窗
const profileVisible = ref(false)
const profileLoading = ref(false)
const profileData = ref<any>(null)

async function openProfile() {
  profileVisible.value = true
  profileLoading.value = true
  try {
    const { authApi } = await import('@/api/auth')
    const data = await authApi.getProfile()
    profileData.value = data
  } catch (e) {
    console.warn('获取个人信息失败:', e)
  } finally {
    profileLoading.value = false
  }
}

function handleProfileClose() {
  profileVisible.value = false
  profileData.value = null
}

// 菜单项（按角色过滤）
const menuItems = computed(() => {
  const role = authStore.getUserRole()
  const allMenus = [
    { path: '/dashboard', title: '仪表盘', icon: Odometer, roles: ['admin', 'user', 'operator'] },
    { path: '/users', title: '用户管理', icon: User, roles: ['admin', 'user'] },
    { path: '/devices', title: '设备管理', icon: Monitor, roles: ['admin', 'user'] },
    { path: '/template/update', title: '数据更新', icon: Document, roles: ['admin', 'user', 'operator'] },
    { path: '/template/history', title: '更新历史', icon: Clock, roles: ['admin', 'user', 'operator'] },
    { path: '/template/manage', title: '模板管理', icon: FolderOpened, roles: ['admin', 'user'] },
    { path: '/batch', title: '批量操作', icon: TrendCharts, roles: ['admin', 'user'] },
    { path: '/monitor', title: '实时监控', icon: Monitor, roles: ['admin', 'user', 'operator'] },
  ]
  return allMenus.filter(m => !m.roles || m.roles.includes(role))
})

// 方法
function handleUserCommand(command: string) {
  switch (command) {
    case 'profile':
      openProfile()
      break
    case 'logout':
      loginAlert.resetCheck()
      authStore.logout()
      router.push('/login')
      break
  }
}

/** 跳转到监控页并关闭告警弹窗 */
function goToMonitor() {
  alertVisibleRef.value = false
  router.push('/monitor')
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

function handleResize() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 获取后端版本信息
  service.get('/system/info').then((d: any) => {
    if (d) {
      backendVersion.value = d.version || ''
      backendStartTime.value = d.startTime || ''
    }
  }).catch(() => {})
  // 登录后自动检查设备告警（每次会话只弹一次）
  loginAlert.checkAlerts()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.default-layout {
  display: flex;
  min-height: 100vh;
  
  &.sidebar-collapsed .sidebar {
    width: $sidebar-collapsed-width;
    
    .logo-text,
    .version-info,
    .el-sub-menu__title span {
      display: none;
    }
  }
}

// ==================== 侧边栏 ====================
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: $sidebar-width;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width $transition-base;

  .sidebar-logo {
    height: $header-height;
    padding: 0 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    border-bottom: 1px solid var(--el-border-color-lighter);
    overflow: hidden;

    .logo-icon {
      width: 32px;
      height: 32px;
      flex-shrink: 0;

      svg {
        width: 100%;
        height: 100%;
      }
    }

    .logo-text {
      font-size: $font-size-lg;
      font-weight: 700;
      background: $primary-gradient;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      white-space: nowrap;
    }
  }

  .sidebar-menu-wrap {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .sidebar-menu {
    border-right: none !important;
    background: transparent !important;

    .el-menu-item {
      height: 44px;
      line-height: 44px;
      margin-bottom: 4px;
      border-radius: $radius-sm;
      
      &:hover {
        background-color: var(--el-fill-color-light);
      }

      &.is-active {
        background: linear-gradient(135deg, rgba($primary-color, 0.1), rgba($primary-dark, 0.05));
        color: $primary-color;
        
        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 4px;
          bottom: 4px;
          width: 3px;
          background: $primary-gradient;
          border-radius: 2px;
        }
      }

      .menu-icon {
        font-size: 16px;
        width: 1em !important;
        height: 1em !important;
        max-width: 16px;
        max-height: 16px;
      }
    }
  }

  .sidebar-footer {
    padding: 12px 16px;
    border-top: 1px solid var(--el-border-color-lighter);

    .version-info {
      font-size: $font-size-xs;
      color: var(--el-text-color-placeholder);
      text-align: center;
      line-height: 1.6;

      .version-line {
        white-space: nowrap;
      }

      .build-time {
        font-size: 10px;
        opacity: 0.7;
      }
    }
  }
}

// 移动端遮罩
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 99;
}

// ==================== 主内容区 ====================
.main-container {
  flex: 1;
  margin-left: $sidebar-width;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left $transition-base;
}

.sidebar-collapsed .main-container {
  margin-left: $sidebar-collapsed-width;
}

// ==================== 顶栏 ====================
.header {
  position: sticky;
  top: 0;
  z-index: 50;
  height: $header-height;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .collapse-btn {
      padding: 8px;
      font-size: 20px;
      color: var(--el-text-color-primary) !important;
      background: var(--el-fill-color-light) !important;
      border: 1px solid var(--el-border-color) !important;
      border-radius: 8px;
      &:hover {
        color: var(--el-color-primary) !important;
        background: var(--el-color-primary-light-9) !important;
        border-color: var(--el-color-primary-light-7) !important;
      }
    }

    .breadcrumb {
      font-size: $font-size-base;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;

    .search-box {
      width: 200px;

      :deep(.el-input__wrapper) {
        border-radius: 20px;
      }
    }

    .mqtt-status {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: $font-size-xs;
      background: var(--el-fill-color-light);
      transition: all $transition-fast;

      &.connected {
        background: rgba($success-color, 0.1);
        color: $success-color;

        .status-dot {
          background: $success-color;
        }
      }

      .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--el-text-color-placeholder);
        animation: pulse 2s infinite;
      }

      .status-text {
        white-space: nowrap;
      }
    }

    .user-avatar {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 20px;
      transition: background $transition-fast;

      &:hover {
        background: var(--el-fill-color-light);
      }

      .user-info {
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .user-name {
        font-size: $font-size-sm;
        max-width: 80px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .role-tag {
        font-size: 10px;
        padding: 0 4px;
        height: 18px;
        line-height: 18px;
        border-radius: 4px;
      }

      .arrow-icon {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// ==================== 内容区 ====================
.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--el-bg-color-page);

  .page-content {
    min-height: calc(100vh - #{$header-height} - 48px); // 减去padding
  }
}

// ==================== 个人信息弹窗 ====================
.profile-content {
  .profile-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);

    .profile-header-info {
      h3 {
        margin: 0 0 4px;
        font-size: 18px;
        font-weight: 600;
      }
    }
  }

  .profile-desc {
    margin-top: 12px;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

// 响应式
@media (max-width: $breakpoint-md) {
  .sidebar {
    transform: translateX(-100%);
    box-shadow: $shadow-lg;
    
    &:not(.collapsed) {
      transform: translateX(0);
    }
  }
  
  .main-container {
    margin-left: 0 !important;
  }
  
  .header {
    padding: 0 16px;
    
    .header-right .search-box {
      display: none; // 移动端隐藏搜索
    }
  }
  
  .main-content {
    padding: 16px;
  }
}

// ==================== 设备告警弹窗 ====================
.device-alert-dialog {
  :deep(.el-dialog__header) {
    display: none; // 隐藏默认标题栏
  }

  :deep(.el-dialog__body) {
    padding: 24px;
  }
}

.alert-dialog-body {
  min-height: 80px;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;

  .alert-icon-wrap {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.warning {
      background: linear-gradient(135deg, rgba(#f59e0b, 0.15), rgba(#ef4444, 0.1));
      color: #f59e0b;
    }

    &.success {
      background: linear-gradient(135deg, rgba(#10b981, 0.15), rgba(#34d399, 0.1));
      color: #10b981;
    }
  }

  .alert-title-group {
    .alert-title {
      margin: 0 0 4px;
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .alert-subtitle {
      margin: 0;
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }
  }
}

.alert-section {
  margin-bottom: 16px;
  border-radius: 10px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);

  &.offline {
    background: linear-gradient(135deg, rgba(#ef4444, 0.04), rgba(#ef4444, 0.02));
    border-color: rgba(#ef4444, 0.12);
  }

  &.low-battery {
    background: linear-gradient(135deg, rgba(#f59e0b, 0.06), rgba(#f59e0b, 0.02));
    border-color: rgba(#f59e0b, 0.15);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    color: var(--el-text-color-primary);

    .section-title {
      font-weight: 600;
      font-size: 13px;
    }
  }

  &.offline .section-header { color: #ef4444; }
  &.low-battery .section-header { color: #d97706; }

  .device-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 180px;
    overflow-y: auto;
  }
}

.device-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.6);
  transition: background $transition-fast;

  &:hover {
    background: rgba(255, 255, 255, 1);
  }

  .device-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .device-mac {
    font-size: 13px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  }

  .device-name {
    font-size: 13px;
    color: var(--el-text-color-regular);
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .device-volt {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;

    &.low {
      color: #d97706;
      font-weight: 500;
    }
  }

  .device-tag {
    transform: scale(0.85);
  }

  .device-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    padding-left: 2px;

    > span {
      white-space: nowrap;
    }
  }
}

.alert-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
