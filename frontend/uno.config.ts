import { defineConfig, presetUno, presetAttributify, transformerDirectives } from 'unocss'

export default defineConfig({
  shortcuts: {
    // 布局快捷类
    'flex-center': 'flex items-center justify-center',
    'flex-between': 'flex items-center justify-between',
    'flex-col-center': 'flex flex-col items-center justify-center',
    
    // 卡片基础样式
    'card-base': 'bg-[var(--el-bg-color)] rounded-xl border border-solid border-[var(--el-border-color-lighter)] shadow-sm hover:shadow-md transition-all duration-300',
    'card-hover': 'hover:-translate-y-0.5',
  },
  
  theme: {
    colors: {
      primary: '#6366f1',
      'primary-light': '#818cf8',
      'primary-dark': '#4f46e5',
      success: '#10b981',
      warning: '#f59e0b',
      danger: '#ef4444',
      info: '#3b82f6',
    },
  },
  
  presets: [
    presetUno(),
    presetAttributify(),
  ],
  
  transformers: [
    transformerDirectives(),
  ],
  
  safelist: [
    // 确保动态类名不会被purge
    'i-carbon-sun',
    'i-carbon-moon',
    'i-heroicons-solid:device-phone-mobile',
    'i-heroicons-solid:computer-desktop',
  ],
})
