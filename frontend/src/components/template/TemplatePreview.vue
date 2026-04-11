<template>
  <div class="template-preview">
    <template v-if="templateInfo">
    <div class="preview-header">
      <h3><el-icon><View /></el-icon> 更新预览</h3>
      <el-tag type="warning">共 {{ devices.length }} 台设备</el-tag>
    </div>

    <el-alert
      title="请确认以下更新内容，确认无误后点击「执行」开始批量推送。"
      type="info"
      show-icon
      :closable="false"
      style="margin-bottom: 20px;"
    />

    <!-- 默认值预览卡片 -->
    <div class="preview-default">
      <h4>默认内容</h4>
      <div class="preview-fields">
        <div
          v-for="field in templateInfo.fields"
          :key="field.key"
          class="preview-field"
        >
          <span class="pf-label">{{ field.label }}</span>
          <span class="pf-value">{{ defaultData[field.key] ?? '(空)' }}</span>
        </div>
      </div>
    </div>

    <!-- 各设备预览 -->
    <el-collapse v-model="expandedDevices" class="device-preview-list">
      <el-collapse-item
        v-for="(dev, idx) in devices"
        :key="dev.mac"
        :name="dev.mac"
      >
        <template #title>
          <div class="collapse-title">
            <StatusBadge online :size="'small'" />
            <code>{{ dev.mac }}</code>
            <span class="dev-name">{{ dev.name }}</span>
            <el-tag v-if="dev.hasCustom" size="small" type="warning">有自定义覆盖</el-tag>
          </div>
        </template>

        <div class="preview-device-content">
          <div class="preview-fields">
            <div
              v-for="field in templateInfo.fields"
              :key="field.key"
              class="preview-field"
              :class="{ overridden: isOverridden(dev.mac, field.key) }"
            >
              <span class="pf-label">{{ field.label }}</span>
              <span class="pf-value">
                {{ getDeviceFieldValue(dev.mac, field.key) }}
              </span>
              <span v-if="isOverridden(dev.mac, field.key)" class="override-badge">自定义</span>
            </div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { View } from '@element-plus/icons-vue'
import type { TemplateInfo } from '@/types'
import StatusBadge from '@/components/common/StatusBadge.vue'

interface Props {
  templateInfo?: TemplateInfo | null
  devices: Array<{ mac: string; name: string; hasCustom: boolean }>
  defaultData?: Record<string, any>
  customOverrides?: Record<string, Record<string, any>>
}

const props = withDefaults(defineProps<Props>(), {
  templateInfo: () => null,
  defaultData: () => ({}),
  customOverrides: () => ({})
})

const expandedDevices = ref<string[]>([])

onMounted(() => {
  // 默认展开前3个
  expandedDevices.value = []
})

function getDeviceFieldValue(mac: string, key: string): string {
  if (props.customOverrides?.[mac]?.[key] !== undefined && props.customOverrides[mac][key] !== '') {
    return String(props.customOverrides[mac][key])
  }
  return props.defaultData[key] != null ? String(props.defaultData[key]) : '(空)'
}

function isOverridden(mac: string, key: string): boolean {
  return !!props.customOverrides?.[mac]?.[key]
}
</script>

<style lang="scss" scoped>
.template-preview { padding: 4px; }

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h3 { font-size: 16px; font-weight: 600; color: var(--el-text-color-primary); display: flex; align-items: center; gap: 6px; margin: 0; }
}

.preview-default,
.preview-device-content {
  background: var(--el-fill-color-extra-light);
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 12px;

  h4 { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); margin: 0 0 12px; }
}

.preview-fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.preview-field {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 14px;
  border-radius: 9px;
  background: var(--el-bg-color);
  border: 1px solid transparent;
  transition: all 0.2s;

  &.overridden {
    border-color: rgba(245,158,11,0.3);
    background: rgba(245,158,11,0.03);

    .pf-value { color: #d97706; font-weight: 500; }
  }

  .pf-label {
    font-size: 11.5px;
    color: var(--el-text-color-secondary);
  }
  .pf-value {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    word-break: break-all;
  }
  .override-badge {
    display: inline-block;
    font-size: 10px;
    color: #d97706;
    background: rgba(245,158,11,0.1);
    padding: 1px 7px;
    border-radius: 10px;
    align-self: flex-start;
  }
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 10px;
  code { font-family: monospace; font-size: 12px; }
  .dev-name { font-size: 13px; color: var(--el-text-color-secondary); }
}

.device-preview-list {
  :deep(.el-collapse-item__header) { font-size: 14px; border-radius: 10px; }
  :deep(.el-collapse-item__wrap) { border-radius: 0 0 10px 10px; }
}
</style>
