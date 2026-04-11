<template>
  <el-tag 
    :type="tagType" 
    :effect="effect"
    :size="size"
    round
    class="status-badge"
  >
    <span class="status-dot" :class="statusClass" />
    {{ label }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  /** 兼容两种用法: status='online'|'offline' 或 online=true|false */
  status?: 'online' | 'offline' | 'weak' | 'unknown'
  /** 布尔值模式（与 status 二选一） */
  online?: boolean | number
  size?: 'small' | 'default' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'default',
})

/** 内部状态值: 优先用 status prop，否则从 online 推导 */
const resolvedStatus = computed(() => {
  if (props.status) return props.status
  if (props.online === true || props.online === 1) return 'online'
  if (props.online === false || props.online === 0) return 'offline'
  return 'unknown'
})

const label = computed(() => {
  const map = { online: '在线', offline: '离线', weak: '弱信号', unknown: '未知' }
  return map[resolvedStatus.value]
})

const tagType = computed(() => {
  const map = { online: 'success', offline: 'danger', weak: 'warning', unknown: 'info' }
  return map[resolvedStatus.value] as any
})

const effect = 'light' as const

const statusClass = `status-${resolvedStatus.value}`
</script>

<style scoped lang="scss">
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    
    &.status-online {
      background: #10b981;
      box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
      animation: pulse-green 2s infinite;
    }
    
    &.status-offline {
      background: #ef4444;
    }
    
    &.status-weak {
      background: #f59e0b;
      animation: pulse-yellow 2s infinite;
    }
    
    &.status-unknown {
      background: #9ca3af;
    }
  }
}

@keyframes pulse-green {
  0%, 100% { opacity: 1; box-shadow: 0 0 6px rgba(16, 185, 129, 0.5); }
  50% { opacity: 0.7; box-shadow: 0 0 3px rgba(16, 185, 129, 0.3); }
}
@keyframes pulse-yellow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
