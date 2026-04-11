<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">仪表盘</h2>
        <p class="page-desc">实时掌握所有WIFI标签设备状态</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="handleRefresh" :loading="deviceStore.loading">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <StatCards />

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="14">
        <DeviceChart />
      </el-col>
      <el-col :xs="24" :lg="10">
        <OnlineTrendChart />
      </el-col>
    </el-row>

    <!-- 底部区域 -->
    <el-row :gutter="20" class="bottom-row">
      <el-col :xs="24" :lg="14">
        <RecentActivity />
      </el-col>
      <el-col :xs="24" :lg="10">
        <QuickActions @action-executed="handleRefresh" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useDeviceStore } from '@/stores/device'
import { useBackendWs } from '@/composables/useBackendWs'
import StatCards from '@/components/dashboard/StatCards.vue'
import DeviceChart from '@/components/dashboard/DeviceChart.vue'
import OnlineTrendChart from '@/components/dashboard/OnlineTrendChart.vue'
import RecentActivity from '@/components/dashboard/RecentActivity.vue'
import QuickActions from '@/components/dashboard/QuickActions.vue'

const deviceStore = useDeviceStore()
// 初始化WebSocket连接，确保能接收设备状态更新
const { mqttConnected } = useBackendWs()

onMounted(() => {
  deviceStore.fetchDevices()
  console.log('DashboardView: WebSocket连接状态 - MQTT连接:', mqttConnected.value)
})

function handleRefresh() {
  deviceStore.fetchDevices()
}
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 0 4px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  .page-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    margin: 0 0 4px;
  }

  .page-desc {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.chart-row,
.bottom-row {
  margin-bottom: 20px;
}
</style>
