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
          <span>v1.0.0</span>
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
            text 
            @click="appStore.toggleSidebar()"
          >
            <Fold v-if="!appStore.sidebarCollapsed" />
            <Expand v-else />
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
              <el-avatar :size="32" icon="UserFilled" />
              <span v-if="!isMobile" class="user-name">{{ authStore.userInfo?.username || '管理员' }}</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Fold, Expand, Search, FullScreen, UserFilled,
  ArrowDown, User, SwitchButton,
  Odometer, Monitor, Document, FolderOpened, TrendCharts, Clock
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import { useBackendWs } from '@/composables/useBackendWs'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const { mqttConnected } = useBackendWs()

// 状态
const searchText = ref('')
const isMobile = ref(window.innerWidth < 768)

// 计算属性
const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)

// 菜单项
const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: Odometer },
  { path: '/users', title: '用户管理', icon: User },
  { path: '/devices', title: '设备管理', icon: Monitor },
  { path: '/template/update', title: '数据更新', icon: Document },
  { path: '/template/history', title: '更新历史', icon: Clock },
  { path: '/template/manage', title: '模板管理', icon: FolderOpened },
  { path: '/batch', title: '批量操作', icon: TrendCharts },
  { path: '/monitor', title: '实时监控', icon: Monitor },
]

// 方法
function handleUserCommand(command: string) {
  switch (command) {
    case 'profile':
      // TODO: 打开个人信息弹窗
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      break
  }
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
    padding: 16px;
    border-top: 1px solid var(--el-border-color-lighter);

    .version-info {
      font-size: $font-size-xs;
      color: var(--el-text-color-placeholder);
      text-align: center;
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
      font-size: 18px;
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

      .user-name {
        font-size: $font-size-sm;
        max-width: 80px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
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
</style>
