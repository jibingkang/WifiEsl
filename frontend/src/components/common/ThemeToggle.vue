<template>
  <el-tooltip :content="tooltipText" placement="bottom">
    <button class="theme-toggle" @click="appStore.toggleTheme()">
      <Transition name="theme-icon" mode="out-in">
        <svg 
          v-if="isDark" 
          key="moon"
          viewBox="0 0 24 24" 
          fill="currentColor"
          class="toggle-icon"
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
        <svg
          v-else
          key="sun"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          class="toggle-icon"
        >
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
      </Transition>
    </button>
  </el-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

const isDark = computed(() => appStore.resolvedTheme === 'dark')

const tooltipText = computed(() => {
  switch (appStore.theme) {
    case 'light': return '浅色模式'
    case 'dark': return '深色模式'
    default: return `跟随系统 (当前: ${isDark.value ? '深' : '浅'})`
  }
})
</script>

<style scoped lang="scss">
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: var(--el-fill-color-light);
  cursor: pointer;
  transition: all 200ms ease;
  
  &:hover {
    background: var(--el-fill-color);
    transform: scale(1.05);
  }
  
  &:active {
    transform: scale(0.95);
  }
}

.toggle-icon {
  width: 18px;
  height: 18px;
  color: var(--el-text-color-primary);
}

// 图标切换动画
.theme-icon-enter-active,
.theme-icon-leave-active {
  transition: all 250ms ease;
}
.theme-icon-enter-from,
.theme-icon-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.8);
}
</style>
