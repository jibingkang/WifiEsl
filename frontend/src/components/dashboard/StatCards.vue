<template>
  <div class="stat-cards">
    <div v-for="(card, idx) in cards" :key="card.key" class="stat-card" :style="{ animationDelay: `${idx * 80}ms` }">
      <div class="card-icon" :style="{ background: card.gradient }">
        <el-icon :size="22"><component :is="card.icon" /></el-icon>
      </div>
      <div class="card-info">
        <p class="card-value">{{ animatedValues[card.key] ?? card.value }}</p>
        <p class="card-label">{{ card.label }}</p>
      </div>
      <div class="card-trend" :class="{ up: card.trendUp, down: !card.trendUp && card.trend != null }">
        <span v-if="card.trend != null">{{ card.trendUp ? '+' : '' }}{{ card.trend }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Monitor, Connection, Warning, CircleCheck } from '@element-plus/icons-vue'
import { useDeviceStore } from '@/stores/device'
import { formatNumber } from '@/utils/format'

const deviceStore = useDeviceStore()

const cards = computed(() => {
  const devList = deviceStore.devices ?? []
  const onlineCount = devList.filter(d => d.is_online).length
  const offlineCount = devList.filter(d => !d.is_online).length
  const lowBattery = devList.filter(d => d.voltage && d.voltage < 3000 && d.is_online)
  const weakSignal = devList.filter(d => d.rssi && d.rssi < -70 && d.is_online)

  return [
    {
      key: 'total',
      label: '设备总数',
      value: formatNumber(devList.length),
      icon: Monitor,
      gradient: 'linear-gradient(135deg, #6366f1, #818cf8)',
      trend: 12.5, trendUp: true,
    },
    {
      key: 'online',
      label: '在线设备',
      value: formatNumber(onlineCount),
      icon: Connection,
      gradient: 'linear-gradient(135deg, #22c55e, #4ade80)',
      trend: 5.2, trendUp: true,
    },
    {
      key: 'offline',
      label: '离线设备',
      value: formatNumber(offlineCount),
      icon: Monitor,
      gradient: 'linear-gradient(135deg, #ef4444, #f87171)',
      trend: -3.8, trendUp: false,
    },
    {
      key: 'alert',
      label: '告警数量',
      value: String(lowBattery.length + weakSignal.length),
      icon: Warning,
      gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
      trend: null, trendUp: false,
    },
  ]
})

// 简单的数字动画
const animatedValues = ref<Record<string, string>>({})

function animateValue(key: string, targetStr: string) {
  const num = parseInt(targetStr.replace(/,/g, ''))
  if (isNaN(num)) return

  const duration = 800
  const start = performance.now()
  const fromVal = parseInt(animatedValues.value[key]?.replace(/,/g, '') || '0') || 0

  function step(now: number) {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    // easeOutCubic
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = Math.round(fromVal + (num - fromVal) * eased)
    animatedValues.value[key] = formatNumber(current)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

watch(
  () => cards.value,
  (newCards) => {
    newCards.forEach(c => animateValue(c.key, c.value))
  },
  { immediate: true, deep: true }
)

onMounted(() => {
  cards.value.forEach(c => animateValue(c.key, c.value))
})
</script>

<style lang="scss" scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  border-radius: 16px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: var(--el-box-shadow-lighter);
  transition: all 0.25s ease;
  animation: cardIn 0.5s ease both;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.1);
  }

  .card-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
  }

  .card-info {
    .card-value {
      font-size: 26px;
      font-weight: 700;
      color: var(--el-text-color-primary);
      line-height: 1.2;
      margin: 0 0 2px;
    }

    .card-label {
      font-size: 13px;
      color: var(--el-text-color-secondary);
      margin: 0;
    }
  }

  .card-trend {
    margin-left: auto;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 20px;

    &.up { background: #ecfdf5; color: #059669; }
    &.down { background: #fef2f2; color: #dc2626; }
  }
}

html.dark .stat-card {
  border-color: rgba(255,255,255,0.06);
  &:hover { box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15); }
  .card-trend.up { background: rgba(34,197,94,0.12); }
  .card-trend.down { background: rgba(239,68,68,0.12); }
}

@keyframes cardIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

// 响应式
@media (max-width: 992px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .stat-cards { grid-template-columns: 1fr; }
  .stat-card { padding: 16px; }
  .card-info .card-value { font-size: 22px; }
}
</style>
