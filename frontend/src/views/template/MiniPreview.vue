<template>
  <div class="mini-preview">
    <!-- 默认值摘要 -->
    <div class="preview-default">
      <h4>默认内容</h4>
      <div class="field-grid">
        <div v-for="field in templateInfo.fields" :key="field.key" class="pf-item">
          <span class="pf-lbl">{{ field.label }}</span>
          <span class="pf-val">{{ defaultData[field.key] ?? '(空)' }}</span>
        </div>
      </div>
    </div>

    <!-- 各设备最终数据预览 -->
    <div class="device-preview-list">
      <div
        v-for="(dev, idx) in safeDevices.slice(0, showAll ? 999 : 5)"
        :key="dev.mac"
        class="dev-card"
      >
        <div class="dev-card-header">
          <span class="dev-mac"><code>{{ dev.mac }}</code></span>
          <span class="dev-name-text">{{ dev.name }}</span>
          <el-tag v-if="dev.hasCustom" size="small" type="warning" effect="plain" round>自定义</el-tag>
        </div>
        <div class="dev-fields">
          <div
            v-for="field in templateInfo.fields.slice(0, 4)"
            :key="field.key"
            class="dv-field"
            :class="{ custom: isOverridden(dev.mac, field.key) }"
          >
            <span class="dv-lbl">{{ field.label }}</span>
            <span class="dv-val">{{ getFieldValue(dev.mac, field.key) }}</span>
          </div>
        </div>
      </div>
    </div>

    <button
      v-if="safeDevices.length > 5"
      class="show-more-btn"
      @click="showAll = !showAll"
    >
      {{ showAll ? '收起' : `查看全部 ${safeDevices.length} 台` }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { TemplateInfo } from '@/types'

const props = defineProps<{
  templateInfo: TemplateInfo
  devices: Array<{ mac: string; name: string; hasCustom: boolean }>
  defaultData: Record<string, any>
  customOverrides: Record<string, Record<string, any>>
}>()

const showAll = ref(false)

const safeDevices = computed(() => props.devices ?? [])

function getFieldValue(mac: string, key: string): string {
  if (props.customOverrides?.[mac]?.[key]) return String(props.customOverrides[mac][key])
  return props.defaultData[key] != null ? String(props.defaultData[key]) : '(空)'
}

function isOverridden(mac: string, key: string): boolean {
  return !!props.customOverrides?.[mac]?.[key]
}
</script>

<style scoped>
.mini-preview {
  padding: 4px 0;
}

.preview-default {
  margin-bottom: 16px;
  h4 {
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    margin: 0 0 10px;
  }
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}
.pf-item {
  background: #f8fafc;
  border-radius: 8px;
  padding: 8px 12px;
  border: 1px solid #f1f5f9;
}
.pf-lbl { font-size: 11px; color: #94a3b8; display: block; margin-bottom: 2px; }
.pf-val { font-size: 13px; font-weight: 500; color: #1e293b; word-break: break-all; }

.device-preview-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dev-card {
  background: #fafafa;
  border-radius: 10px;
  padding: 10px 14px;
  border: 1px solid #f0f0f0;
}
.dev-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  code {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 11px;
    color: #6366f1;
  }
  .dev-name-text { font-size: 12px; color: #64748b; }
}
.dev-fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 6px;
}
.dv-field {
  display: flex;
  flex-direction: column;
  gap: 1px;
  &.custom {
    .dv-val { color: #d97706; font-weight: 500; }
  }
}
.dv-lbl { font-size: 10.5px; color: #a1a1aa; }
.dv-val { font-size: 12.5px; color: #3f3f46; word-break: break-all; }

.show-more-btn {
  width: 100%;
  padding: 8px;
  margin-top: 8px;
  border: 1px dashed #e2e8f0;
  border-radius: 8px;
  background: none;
  color: #6366f1;
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { background: rgba(99,102,241,0.05); border-color: #6366f1; }
}
</style>
