<template>
  <aside class="sidebar" :class="{ collapsed: appStore.sidebarCollapsed }">
    <!-- Logo区域 -->
    <div class="sidebar-logo">
      <div class="logo-inner">
        <div class="logo-icon">
          <el-icon :size="22"><Connection /></el-icon>
        </div>
        <transition name="fade-slide">
          <span v-show="!appStore.sidebarCollapsed" class="logo-text">WIFI标签管理</span>
        </transition>
      </div>
    </div>

    <!-- 导航菜单 -->
    <el-scrollbar>
      <el-menu
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="true"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>

        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>

        <el-menu-item index="/devices">
          <el-icon><Monitor /></el-icon>
          <template #title>设备管理</template>
        </el-menu-item>

        <el-menu-item index="/template">
          <el-icon><Document /></el-icon>
          <template #title>数据更新</template>
        </el-menu-item>

        <el-menu-item index="/template/manage">
          <el-icon><Files /></el-icon>
          <template #title>模板管理</template>
        </el-menu-item>

        <el-menu-item index="/batch">
          <el-icon><Grid /></el-icon>
          <template #title>批量操作</template>
        </el-menu-item>

        <el-menu-item index="/monitor">
          <el-icon><DataLine /></el-icon>
          <template #title>实时监控</template>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>

    <!-- 底部版本 -->
    <div class="sidebar-footer">
      <span v-show="!appStore.sidebarCollapsed" class="version">v1.0.0</span>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Odometer, Monitor, Document, Files, Grid, DataLine, Connection, User } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)
</script>

<style lang="scss" scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
  border-right: 1px solid var(--el-border-color-lighter);
  transition: width 0.28s ease;
  flex-shrink: 0;
  overflow: hidden;

  &.collapsed { width: 64px; }
}

.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
  overflow: hidden;

  .logo-inner {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: fit-content;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .logo-text {
    font-size: 15px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    white-space: nowrap;
    letter-spacing: -0.3px;
  }
}

// 菜单样式覆盖
.sidebar-menu {
  border-right: none;
  padding: 8px;
  background: transparent !important;

  :deep(.el-menu-item) {
    height: 44px;
    line-height: 44px;
    border-radius: 10px;
    margin-bottom: 2px;
    color: var(--el-text-color-regular);

    &:hover { background-color: var(--el-fill-color-light); color: var(--el-color-primary); }

    &.is-active {
      background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1));
      color: #6366f1;
      font-weight: 600;
    }
  }

  // 折叠模式
  &.el-menu--collapse {
    :deep(.el-menu-item) {
      padding: 0 !important;
      justify-content: center;
    }
  }
}

.sidebar-footer {
  padding: 12px 16px;
  text-align: center;
  border-top: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;

  .version {
    font-size: 11px;
    color: var(--el-text-color-placeholder);
  }
}

// 过渡动画
.fade-slide-enter-active,
.fade-slide-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.fade-slide-enter-from,
.fade-slide-leave-to { opacity: 0; transform: translateX(-8px); }
</style>
