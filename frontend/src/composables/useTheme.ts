/**
 * 主题切换 composable
 * 支持: light / dark / auto(跟随系统)
 */
import { ref, computed, watch, onMounted } from 'vue'
import { setStorage, getStorage, StorageKeys } from '@/utils/storage'

type ThemeMode = 'light' | 'dark' | 'auto'

const mode = ref<ThemeMode>(getStorage(StorageKeys.THEME, 'auto'))
const isDark = ref(false)

/**
 * 检测系统主题偏好
 */
function getSystemPrefersDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

/**
 * 应用主题到 document.documentElement
 */
function applyTheme(dark: boolean) {
  document.documentElement.classList.toggle('dark', dark)
  isDark.value = dark
}

/**
 * 初始化主题
 */
function initTheme() {
  if (mode.value === 'auto') {
    applyTheme(getSystemPrefersDark())
    // 监听系统变化
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', (e) => {
        if (mode.value === 'auto') applyTheme(e.matches)
      })
  } else {
    applyTheme(mode.value === 'dark')
  }
}

// 组件挂载时初始化
onMounted(initTheme)

export function useTheme() {
  /**
   * 切换主题
   */
  function toggleTheme(newMode?: ThemeMode) {
    if (newMode) {
      mode.value = newMode
    } else {
      // 循环切换: light → dark → auto → light
      const modes: ThemeMode[] = ['light', 'dark', 'auto']
      const idx = modes.indexOf(mode.value)
      mode.value = modes[(idx + 1) % modes.length]
    }

    setStorage(StorageKeys.THEME, mode.value)

    if (mode.value === 'auto') {
      applyTheme(getSystemPrefersDark())
    } else {
      applyTheme(mode.value === 'dark')
    }
  }

  return {
    mode,
    isDark: computed(() => isDark.value),
    toggleTheme,
  }
}
