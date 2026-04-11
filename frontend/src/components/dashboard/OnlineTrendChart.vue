<template>
  <el-card class="chart-card" shadow="never">
    <template #header>
      <div class="card-header">
        <h3 class="title">在线趋势 (24h)</h3>
        <el-tag size="small" type="success">实时</el-tag>
      </div>
    </template>
    <div ref="chartRef" class="chart-container" />
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useDeviceStore } from '@/stores/device'

const deviceStore = useDeviceStore()
const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

/**
 * 生成模拟的24小时趋势数据 (实际项目中从后端API或MQTT历史数据获取)
 */
function generateTrendData() {
  const now = new Date()
  const times: string[] = []
  const onlineData: number[] = []
  const totalData: number[] = []

  for (let i = 23; i >= 0; i--) {
    const hour = new Date(now.getTime() - i * 3600000)
    times.push(`${hour.getHours().toString().padStart(2, '0')}:00`)

    // 模拟波动数据（实际项目替换为真实统计）
    const base = deviceStore.onlineCount || 0
    const variance = Math.floor(Math.random() * (base > 0 ? base * 0.1 : 5))
    onlineData.push(base + variance)
    totalData.push(deviceStore.devices.length || base + variance + Math.floor(Math.random() * 3))
  }

  return { times, onlineData, totalData }
}

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)

  const { times, onlineData, totalData } = generateTrendData()

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    grid: { left: 48, right: 16, top: 12, bottom: 28 },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: { lineStyle: { color: 'var(--el-border-color)' } },
      axisLabel: { fontSize: 11, color: 'var(--el-text-color-secondary)' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'var(--el-border-color-lighter)', type: 'dashed' } },
      axisLabel: { fontSize: 11, color: 'var(--el-text-color-secondary)' },
    },
    series: [
      {
        name: '在线数',
        type: 'line',
        smooth: true,
        data: onlineData,
        lineStyle: { width: 3, color: '#22c55e' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34,197,94,0.25)' },
            { offset: 1, color: 'rgba(34,197,94,0.02)' },
          ]),
        },
        itemStyle: { color: '#22c55e' },
        symbolSize: 6,
      },
      {
        name: '总设备数',
        type: 'line',
        smooth: true,
        data: totalData,
        lineStyle: { width: 2, color: '#6366f1', type: 'dashed' },
        itemStyle: { color: '#6366f1' },
        symbolSize: 4,
      },
    ],
  })
}

onMounted(initChart)
onUnmounted(() => chartInstance?.dispose())

let resizeObserver: ResizeObserver | null = null
onMounted(() => {
  if (!chartRef.value) return
  resizeObserver = new ResizeObserver(() => chartInstance?.resize())
  resizeObserver.observe(chartRef.value)
})
onUnmounted(() => resizeObserver?.disconnect())
</script>

<style lang="scss" scoped>
.chart-card {
  border-radius: 16px !important;
  min-height: 380px;

  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--el-border-color-lighter); }
  :deep(.el-card__body) { padding: 12px; }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title { font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); margin: 0; }
}

.chart-container { width: 100%; height: 300px; }
</style>
