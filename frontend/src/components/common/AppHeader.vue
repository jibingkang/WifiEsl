<template>
  <header class="app-header">
    <!-- 左侧: 折叠按钮 + 面包屑 -->
    <div class="header-left">
      <button class="collapse-btn" @click="appStore.toggleSidebar">
        <el-icon :size="18"><Fold v-if="!appStore.sidebarCollapsed" /><Expand v-else /></el-icon>
      </button>
      <el-breadcrumb separator="/" class="breadcrumb">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="$route.meta?.title as string">
          {{ $route.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 右侧: 操作区 -->
    <div class="header-right">
      <!-- 全局搜索 -->
      <el-tooltip content="全局搜索" placement="bottom" :show-after="500">
        <button class="icon-btn" @click="showSearch = true">
          <el-icon :size="17"><Search /></el-icon>
        </button>
      </el-tooltip>

      <!-- MQTT连接状态指示 -->
      <div class="mqtt-status" :class="{ connected: mqttConnected }">
        <span class="dot" />
        <span class="label">{{ mqttConnected ? '已连接' : '未连接' }}</span>
      </div>

      <!-- 刷新按钮 -->
      <el-tooltip content="刷新数据" placement="bottom" :show-after="500">
        <button class="icon-btn" @click="$emit('refresh')">
          <el-icon :size="17"><Refresh /></el-icon>
        </button>
      </el-tooltip>

      <!-- 全屏 -->
      <el-tooltip content="全屏切换" placement="bottom" :show-after="500">
        <button class="icon-btn" @click="toggleFullscreen">
          <el-icon :size="17"><FullScreen /></el-icon>
        </button>
      </el-tooltip>

      <el-divider direction="vertical" />

      <!-- 主题切换 -->
      <ThemeToggle size="small" />

      <!-- 用户菜单 -->
      <UserDropdown />
    </div>

    <!-- 搜索对话框 -->
    <el-dialog v-model="showSearch" title="全局搜索" width="480px" top="10vh" append-to-body>
      <el-input
        v-model="searchQuery"
        placeholder="搜索设备MAC地址、名称..."
        size="large"
        clearable
        autofocus
        :prefix-icon="Search"
        @keyup.enter="handleSearch"
      />
      <template #footer>
        <el-button @click="showSearch = false">取消</el-button>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
      </template>
    </el-dialog>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Fold, Expand, Search, Refresh, FullScreen } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import ThemeToggle from './ThemeToggle.vue'
import UserDropdown from './UserDropdown.vue'
import { useBackendWs } from '@/composables/useBackendWs'

defineEmits<{
  refresh: []
}>()

const appStore = useAppStore()
const router = useRouter()

const showSearch = ref(false)
const searchQuery = ref('')
const { mqttConnected } = useBackendWs()

function handleSearch() {
  if (searchQuery.value.trim()) {
    showSearch.value = false
    router.push({ path: '/devices', query: { keyword: searchQuery.value.trim() } })
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen()
  else document.exitFullscreen()
}
</script>

<style lang="scss" scoped>
.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;

  .collapse-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border: none;
    background: transparent;
    border-radius: 9px;
    cursor: pointer;
    color: var(--el-text-color-primary);
    transition: all 0.2s;

    &:hover { background: var(--el-fill-color); }
  }

  .breadcrumb {
    display: none;
  }
}

@media (min-width: 768px) { .header-left .breadcrumb { display: block; } }

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  border-radius: 9px;
  cursor: pointer;
  color: var(--el-text-color-secondary);
  transition: all 0.2s;

  &:hover { background: var(--el-fill-color); color: var(--el-text-color-primary); }
}

.mqtt-status {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 20px;
  background: var(--el-fill-color-light);
  font-size: 12px;

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #94a3b8;
  }

  &.connected .dot { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }

  .label { color: var(--el-text-color-secondary); }
}

html.dark {
  .mqtt-status { background: rgba(255,255,255,0.06); }
}
</style>
