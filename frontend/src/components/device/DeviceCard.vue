<template>
  <div class="device-card" :class="{ offline: !device.is_online }">
    <!-- 头部 -->
    <div class="card-head">
      <StatusBadge :online="device.is_online" size="large" />
      <div class="card-info">
        <p class="device-name">{{ device.name || '未命名' }}</p>
        <p class="device-mac">{{ formatMac(device.mac) }}</p>
      </div>
    </div>

    <!-- 状态指标 -->
    <div class="card-stats">
      <div class="stat-item">
        <span class="stat-label">电量</span>
        <span class="stat-value" :class="{ low: device.is_online && device.voltage && device.voltage < 350 }">
          {{ device.voltage != null ? formatVolt(device.voltage) : '--' }}
        </span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-label">信号</span>
        <span class="stat-value" :class="{ weak: device.rssi != null && device.rssi < -70 }">
          {{ device.rssi != null ? `${device.rssi}dBm` : '--' }}
        </span>
      </div>
      <div class="stat-divider" />
      <div class="stat-item">
        <span class="stat-label">IP</span>
        <span class="stat-value ip">{{ device.ip || '--' }}</span>
      </div>
    </div>

    <!-- 类型标签 -->
    <div class="card-tags">
      <el-tag size="small" effect="plain">{{ DEVICE_TYPES[device.device_type ?? ''] || device.device_type }}</el-tag>
      <el-tag size="small" effect="plain" type="info">{{ SCREEN_TYPES[device.screen_type ?? ''] || device.screen_type }}</el-tag>
    </div>

    <!-- 操作按钮 -->
    <div class="card-actions">
      <button class="act-btn primary" @click="$emit('control', { action: 'control', device })">
        <el-icon><Setting /></el-icon> 控制
      </button>
      <button class="act-btn" @click="$emit('control', { action: 'detail', device })">
        详情
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Setting } from '@element-plus/icons-vue'
import type { Device } from '@/types'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatMac, formatVolt } from '@/utils/format'
import { DEVICE_TYPES, SCREEN_TYPES } from '@/utils/constants'

defineProps<{ device: Device }>()
defineEmits<{
  control: [payload: { action: string; device: Device }]
}>()
</script>

<style lang="scss" scoped>
.device-card {
  padding: 18px;
  border-radius: 14px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  transition: all 0.25s ease;

  &:hover { box-shadow: 0 6px 24px rgba(99,102,241,0.08); border-color: rgba(99,102,241,0.2); }
  &.offline { opacity: 0.75; }
}

.card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;

  .device-name { font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); margin: 0 0 2px; }
  .device-mac { font-family: monospace; font-size: 12px; color: var(--el-text-color-secondary); margin: 0; }
}

.card-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 10px;
  background: var(--el-fill-color-extra-light);
  margin-bottom: 14px;

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    gap: 3px;
    .stat-label { font-size: 11px; color: var(--el-text-color-placeholder); }
    .stat-value { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); &.low { color: #ef4444; } &.weak { color: #f59e0b; } &.ip { font-family: monospace; font-size: 12px; font-weight: normal; } }
  }
  .stat-divider { width: 1px; height: 28px; background: var(--el-border-color-lighter); }
}

.card-tags { display: flex; gap: 6px; margin-bottom: 14px; }

.card-actions { display: flex; gap: 8px; }
.act-btn {
  flex: 1;
  height: 36px;
  border: 1px solid var(--el-border-color);
  border-radius: 9px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--el-text-color-regular);

  &:hover { background: var(--el-fill-color-light); }
  &.primary { color: #6366f1; border-color: rgba(99,102,241,0.3); &:hover { background: rgba(99,102,241,0.08); } }
}
</style>
