import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const THEME_KEY = 'wifi_esl_theme'

export type ThemeMode = 'light' | 'dark' | 'auto'
type ResolvedTheme = 'light' | 'dark'

export const useAppStore = defineStore('app', () => {
  // 状态
  const theme = ref<ThemeMode>((localStorage.getItem(THEME_KEY) as ThemeMode) || 'auto')
  const sidebarCollapsed = ref(false)
  const resolvedTheme = ref<ResolvedTheme>('light')

  /**
   * 初始化主题
   */
  function initTheme() {
    applyTheme()
    
    // 监听系统主题变化
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', () => {
        if (theme.value === 'auto') {
          applyTheme()
        }
      })
    }
    
    // 响应式侧边栏（移动端默认折叠）
    checkMobileSidebar()
    window.addEventListener('resize', checkMobileSidebar)
  }

  /**
   * 应用主题到DOM
   */
  function applyTheme() {
    let resolved: ResolvedTheme
    
    if (theme.value === 'auto') {
      // 跟随系统
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    } else {
      resolved = theme.value
    }
    
    resolvedTheme.value = resolved
    document.documentElement.setAttribute('data-theme', resolved)
    document.documentElement.classList.toggle('dark', resolved === 'dark')
  }

  /**
   * 切换主题
   */
  function toggleTheme(newTheme?: ThemeMode) {
    if (newTheme) {
      theme.value = newTheme
    } else {
      // 循环切换: auto -> light -> dark -> auto
      const modes: ThemeMode[] = ['auto', 'light', 'dark']
      const currentIndex = modes.indexOf(theme.value)
      theme.value = modes[(currentIndex + 1) % modes.length]
    }
    
    localStorage.setItem(THEME_KEY, theme.value)
    applyTheme()
  }

  /**
   * 检测是否为移动端，自动折叠侧边栏
   */
  function checkMobileSidebar() {
    if (window.innerWidth < 768) {
      sidebarCollapsed.value = true
    }
  }

  /**
   * 切换侧边栏
   */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    theme,
    resolvedTheme,
    sidebarCollapsed,
    initTheme,
    toggleTheme,
    toggleSidebar,
  }
})
