<template>
  <el-card class="chart-card" shadow="never">
    <template #header>
      <div class="card-header">
        <h3 class="title">设备分布概览</h3>
        <el-radio-group v-model="chartType" size="small">
          <el-radio-button value="type">按类型</el-radio-button>
          <el-radio-button value="screen">按屏幕</el-radio-button>
          <el-radio-button value="status">按状态</el-radio-button>
        </el-radio-group>
      </div>
    </template>
    <div ref="chartRef" class="chart-container" v-if="!isEmpty" />
    <div v-if="isEmpty" class="empty-state">
      <el-empty description="暂无设备数据" :image-size="100" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useDeviceStore } from '@/stores/device'
import { DEVICE_TYPES, SCREEN_TYPES } from '@/utils/constants'

const deviceStore = useDeviceStore()
const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null
const chartType = ref<'type' | 'screen' | 'status'>('type')

const isEmpty = computed(() => (deviceStore.devices ?? []).length === 0)

/** 根据当前类型获取图表数据 */
function getChartData() {
  const devices = deviceStore.devices

  switch (chartType.value) {
    case 'type': {
      const map: Record<string, number> = {}
      devices.forEach(d => {
        const type = d.device_type || 'unknown'
        map[type] = (map[type] || 0) + 1
      })
      return {
        data: Object.entries(map).map(([name, value]) => ({
          name: DEVICE_TYPES[name] ?? name,
          value,
        })),
        colors: ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd'],
      }
    }
    case 'screen': {
      const map: Record<string, number> = {}
      devices.forEach(d => {
        const type = d.screen_type || 'unknown'
        map[type] = (map[type] || 0) + 1
      })
      return {
        data: Object.entries(map).map(([name, value]) => ({
          name: SCREEN_TYPES[name] ?? name,
          value,
        })),
        colors: ['#22c55e', '#f59e0b', '#3b82f6', '#94a3b8'],
      }
    }
    case 'status': {
      return {
        data: [
          { name: '在线', value: deviceStore.onlineCount },
          { name: '离线', value: deviceStore.offlineCount },
        ],
        colors: ['#22c55e', '#94a3b8'],
      }
    }
    default:
      return { data: [], colors: [] }
  }
}

/** 渲染/更新图表 */
function renderChart() {
  if (!chartInstance || !chartRef.value) return

  const { data, colors } = getChartData()

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#eee',
      textStyle: { color: '#333' },
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { fontSize: 13, color: 'var(--el-text-color-secondary)' },
      itemWidth: 14,
      itemHeight: 14,
      itemGap: 16,
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['38%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' },
          itemShadowBlur: 10,
        },
        data: data.map((item, i) => ({ name: item.name, itemStyle: { color: colors[i % colors.length] }, value: item.value })),
        animationType: 'scale',
        animationEasing: 'elasticOut',
      },
    ],
  }, true)
}

/** 初始化图表 */
function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  renderChart()
}

watch(chartType, () => nextTick(renderChart))
watch(isEmpty, (val) => { if (!val) nextTick(initChart) })

onMounted(() => nextTick(initChart))
onUnmounted(() => chartInstance?.dispose())

// 响应窗口大小变化
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

  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  :deep(.el-card__body) { padding: 12px; }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .title {
    font-size: 15px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0;
  }
}

.chart-container {
  width: 100%;
  height: 300px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 260px;
}
</style>
