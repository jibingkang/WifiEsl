/**
 * 响应式断点检测 composable
 */
import { ref, onMounted, onUnmounted, computed } from 'vue'

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

const BREAKPOINTS: Record<Breakpoint, number> = {
  xs: 480,
  sm: 768,
  md: 992,
  lg: 1200,
  xl: 1920,
}

let width = ref(window.innerWidth)

function updateWidth() {
  width.value = window.innerWidth
}

export function useResponsive() {
  onMounted(() => window.addEventListener('resize', updateWidth, { passive: true }))
  onUnmounted(() => window.removeEventListener('resize', updateWidth))

  const breakpoint = computed<Breakpoint>(() => {
    if (width.value >= BREAKPOINTS.xl) return 'xl'
    if (width.value >= BREAKPOINTS.lg) return 'lg'
    if (width.value >= BREAKPOINTS.md) return 'md'
    if (width.value >= BREAKPOINTS.sm) return 'sm'
    return 'xs'
  })

  /** 是否移动端 (<768px) */
  const isMobile = computed(() => width.value < BREAKPOINTS.sm)

  /** 是否平板 (>=768 且 <1200) */
  const isTablet = computed(() => width.value >= BREAKPOINTS.sm && width.value < BREAKPOINTS.lg)

  /** 是否桌面端 (>=1200) */
  const isDesktop = computed(() => width.value >= BREAKPOINTS.lg)

  return {
    width: computed(() => width.value),
    breakpoint,
    isMobile,
    isTablet,
    isDesktop,
  }
}
