<template>
  <el-card class="actions-card" shadow="never">
    <template #header>
      <h3 class="title">快捷操作</h3>
    </template>

    <div class="actions-grid">
      <button
        v-for="action in actions"
        :key="action.key"
        class="action-btn"
        :class="{ disabled: action.disabled }"
        :disabled="action.disabled"
        @click="handleAction(action)"
      >
        <div class="action-icon" :style="{ background: action.gradient }">
          <el-icon :size="20"><component :is="action.icon" /></el-icon>
        </div>
        <span class="action-name">{{ action.label }}</span>
      </button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Document, Upload, Download, Refresh, Setting
} from '@element-plus/icons-vue'

defineEmits<{
  actionExecuted: []
}>()

const router = useRouter()

const actions = [
  { key: 'add', label: '添加设备', icon: Plus, gradient: 'linear-gradient(135deg,#6366f1,#818cf8)', disabled: false },
  { key: 'template', label: '数据更新', icon: Document, gradient: 'linear-gradient(135deg,#8b5cf6,#a78bfa)', disabled: false },
  { key: 'import', label: '导入数据', icon: Upload, gradient: 'linear-gradient(135deg,#22c55e,#4ade80)', disabled: false },
  { key: 'export', label: '导出数据', icon: Download, gradient: 'linear-gradient(135deg,#3b82f6,#60a5fa)', disabled: false },
  { key: 'refresh', label: '刷新状态', icon: Refresh, gradient: 'linear-gradient(135deg,#f59e0b,#fbbf24)', disabled: false },
  { key: 'settings', label: '系统设置', icon: Setting, gradient: 'linear-gradient(135deg,#94a3b8,#cbd5e1)', disabled: true },
]

async function handleAction(action: typeof actions[number]) {
  switch (action.key) {
    case 'add':
      router.push('/devices')
      break
    case 'template':
      router.push('/template')
      break
    case 'refresh':
      ElMessage.success('正在刷新设备状态...')
      break
    case 'export':
      ElMessage.info('导出功能开发中')
      break
    case 'import':
      ElMessage.info('导入功能开发中')
      break
    case 'settings':
      ElMessage.info('设置功能开发中')
      break
  }
}
</script>

<style lang="scss" scoped>
.actions-card {
  border-radius: 16px !important;
  min-height: 340px;

  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--el-border-color-lighter); }
  :deep(.el-card__body) { padding: 16px; }
}

.title { font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); margin: 0; }

.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 14px;
  background: transparent;
  cursor: pointer;
  transition: all 0.25s ease;

  &:hover:not(.disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.06);
    border-color: var(--el-color-primary-light-5);
  }

  &.disabled { opacity: 0.45; cursor: not-allowed; }

  .action-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .action-name {
    font-size: 12.5px;
    font-weight: 500;
    color: var(--el-text-color-regular);
  }
}

@media (max-width: 480px) {
  .actions-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
