<template>
  <div class="task-history">
    <el-empty v-if="tasks.length === 0" description="暂无执行记录" :image-size="80" />
    <el-timeline v-else>
      <el-timeline-item
        v-for="task in tasks"
        :key="task.id"
        :timestamp="task.time"
        :type="task.status === 'success' ? 'success' : task.status === 'failed' ? 'danger' : 'warning'"
        placement="top"
      >
        <div class="task-card" @click="showDetail(task)">
          <div class="task-header">
            <span class="task-name">{{ task.name }}</span>
            <el-tag size="small" :type="statusTagType(task.status)">{{ statusLabel(task.status) }}</el-tag>
          </div>
          <p class="task-desc">{{ task.description }}</p>
          <div class="task-stats">
            <span>{{ task.total }} 台设备</span>
            <span>成功 {{ task.success }} / 失败 {{ task.failed }}</span>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface TaskItem {
  id: string
  name: string
  description: string
  time: string
  status: 'success' | 'failed' | 'partial' | 'running'
  total: number
  success: number
  failed: number
}

const tasks = ref<TaskItem[]>([
  // 模拟数据，实际从后端获取
])

function statusLabel(s: string): string {
  return { success: '成功', failed: '失败', partial: '部分成功', running: '执行中' }[s] ?? s
}
function statusTagType(s: string): any {
  return { success: 'success', failed: 'danger', partial: 'warning', running: '' }[s] ?? 'info'
}
function showDetail(_t: TaskItem) {
  // TODO: 显示详情弹窗
}
</script>

<style lang="scss" scoped>
.task-history { padding: 10px 4px; }
.task-card {
  padding: 14px 18px;
  border-radius: 11px;
  background: var(--el-fill-color-extra-light);
  cursor: pointer;
  transition: all 0.2s;

  &:hover { background: var(--el-fill-color); transform: translateX(3px); }
}
.task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.task-name { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); }
.task-desc { font-size: 13px; color: var(--el-text-color-secondary); margin: 0 0 8px; }
.task-stats { display: flex; gap: 16px; font-size: 12px; color: var(--el-text-color-placeholder); }
</style>
