<template>
  <el-card class="activity-card" shadow="never">
    <template #header>
      <div class="card-header">
        <h3 class="title">最近活动</h3>
        <el-button text type="primary" size="small">查看全部</el-button>
      </div>
    </template>

    <el-timeline>
      <el-timeline-item
        v-for="item in allActivities"
        :key="item.id"
        :timestamp="item.time"
        :type="item.type"
        :size="'normal'"
        placement="top"
      >
        <div class="activity-content">
          <p class="activity-text">{{ item.text }}</p>
          <p class="activity-detail" v-if="item.detail">{{ item.detail }}</p>
        </div>
      </el-timeline-item>

      <div v-if="allActivities.length === 0" style="padding: 20px 0;">
        <el-empty description="暂无活动记录" :image-size="60" />
      </div>
    </el-timeline>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { activities, type ActivityItem } from '@/composables/useBackendWs'

// 添加一些初始化的活动记录
const initialActivities = ref<ActivityItem[]>([
  {
    id: -1,
    text: '系统初始化完成',
    detail: 'WIFI标签管理系统已启动',
    time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
    type: 'info'
  },
  {
    id: -2,
    text: '仪表盘已加载',
    detail: '等待设备连接...',
    time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
    type: 'info'
  }
])

// 标记是否已显示过初始化记录
const hasShownInitial = ref(true)

// 组合活动记录：真实活动 + 初始化记录
const allActivities = computed(() => {
  const realActivities = activities.value.filter(act => act.id > 0)
  if (realActivities.length > 0) {
    // 有真实活动时，清理初始化记录
    if (hasShownInitial.value) {
      console.log('RecentActivity: 检测到真实设备活动，清理初始化记录')
      hasShownInitial.value = false
    }
    return realActivities
  }
  // 没有真实活动时，显示初始化记录
  return initialActivities.value
})

// 监控活动变化
watch(activities, (newActivities) => {
  const realCount = newActivities.filter(act => act.id > 0).length
  if (realCount > 0) {
    console.log(`RecentActivity: 检测到 ${realCount} 条真实活动记录`)
  }
}, { deep: true })

// 当页面加载时
onMounted(() => {
  console.log('RecentActivity: 组件已加载，活动记录总数:', activities.value.length)
  console.log('RecentActivity: 初始化记录:', initialActivities.value.length)
})
</script>

<style lang="scss" scoped>
.activity-card {
  border-radius: 16px !important;
  min-height: 340px;

  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--el-border-color-lighter); }
  :deep(.el-card__body) { padding: 12px 20px; max-height: 320px; overflow-y: auto; }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  .title { font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); margin: 0; }
}

.activity-content {
  .activity-text {
    font-size: 13.5px;
    color: var(--el-text-color-primary);
    margin: 0 0 4px;
    font-weight: 500;
  }
  .activity-detail {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin: 0;
    font-family: monospace;
  }
}

::deep(.el-timeline-item__timestamp) {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
</style>
