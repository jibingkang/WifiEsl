<template>
  <div class="device-data-table">
    <!-- 桌面端：表格 -->
    <div v-if="devices.length > 0" class="table-scroll desktop-table">
      <table class="edit-table">
        <thead>
          <tr>
            <th class="col-check">
              <el-checkbox
                :model-value="isAllChecked"
                :indeterminate="isPartialChecked"
                @change="toggleAll"
              />
            </th>
            <th class="col-name">设备</th>
            <th class="col-device-status">设备状态</th>
            <th class="col-update-status">更新状态</th>
            <th class="col-sent-at">开始时间</th>
            <th class="col-finished-at">结束时间</th>
            <th
              v-for="field in templateInfo.fields"
              :key="'h-' + field.key"
              class="col-field"
              :class="{ 'field-required': field.required }"
            >
              {{ field.label }}{{ field.required ? '*' : '' }}
            </th>
            <th class="col-action">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="dev in devices"
            :key="dev.mac"
            :class="{ 'has-custom': hasAnyValue(dev.mac), checked: isChecked(dev.mac) }"
          >
            <!-- checkbox -->
            <td class="col-check">
              <el-checkbox
                :model-value="isChecked(dev.mac)"
                @change="(v: boolean) => toggleCheck(dev.mac, v)"
              />
            </td>

            <!-- 设备名+MAC -->
            <td class="col-name">
              <span class="dev-name">{{ dev.name }}</span>
              <code class="mac-code">{{ dev.mac }}</code>
            </td>

            <!-- 设备在线状态（单列） -->
            <td class="col-device-status">
              <div class="device-status-cell">
                <span
                  class="status-dot"
                  :class="{ online: dev.status === 'online' }"
                  :title="dev.status === 'online' ? '设备在线' : '设备离线'"
                />
                <span class="status-text" :class="{ 'text-online': dev.status === 'online', 'text-offline': dev.status !== 'online' }">
                  {{ dev.status === 'online' ? '在线' : '离线' }}
                </span>
              </div>
            </td>

            <!-- 更新状态（只显示标签，不含时间） -->
            <td class="col-update-status">
              <el-tag
                v-if="dev.updateStatus && dev.updateStatus !== 'pending'"
                :type="updateTagType(dev.updateStatus)"
                size="small"
                class="update-tag"
              >{{ updateLabel(dev.updateStatus) }}</el-tag>
              <span v-else class="pending-text">待推送</span>
            </td>

            <!-- 开始时间 -->
            <td class="col-sent-at">
              <span v-if="dev.sentAt" class="time-cell" :title="'开始: ' + dev.sentAt">{{ formatTimeShort(dev.sentAt) }}</span>
              <span v-else class="empty-cell">-</span>
            </td>

            <!-- 结束时间 -->
            <td class="col-finished-at">
              <span v-if="dev.finishedAt" class="time-cell finished" :title="'完成: ' + dev.finishedAt">{{ formatTimeShort(dev.finishedAt) }}</span>
              <span v-else class="empty-cell">-</span>
            </td>

            <!-- 每个字段可编辑 -->
            <td
              v-for="field in templateInfo.fields"
              :key="dev.mac + '-' + field.key"
              class="col-field"
              :class="{ 'is-custom': isOverridden(dev.mac, field.key) }"
            >
              <input
                type="text"
                class="cell-input"
                :value="getEffective(dev.mac, field.key)"
                :placeholder="defaultPlaceholder(field)"
                @focus="onFocus(dev.mac, field.key)"
                @blur="onBlur(dev.mac, field.key, $event)"
                @keydown.enter="($event.target as HTMLInputElement).blur()"
              />
              <button
                v-if="isOverridden(dev.mac, field.key)"
                class="cell-clear"
                title="恢复默认值"
                @click.stop="clearField(dev.mac, field.key)"
              >&#x2715;</button>
            </td>

            <!-- 操作列 -->
            <td class="col-action">
              <div class="action-btns">
                <button class="btn-push" title="推送到该设备" :class="{ disabled: dev.status !== 'online' }" @click="$emit('pushDevice', dev)">
                  推送
                </button>
                <button class="btn-remove" title="从更新列表移除该设备" @click="$emit('removeBinding', dev)">
                  移除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 移动端：卡片列表 -->
    <div v-if="devices.length > 0" class="mobile-card-list">
      <div
        v-for="dev in devices"
        :key="'m-' + dev.mac"
        class="device-card"
        :class="{ 'is-checked': isChecked(dev.mac), 'has-custom': hasAnyValue(dev.mac) }"
      >
        <!-- 卡片头部：checkbox + 设备名 + 状态 -->
        <div class="card-header">
          <el-checkbox
            :model-value="isChecked(dev.mac)"
            @change="(v: boolean) => toggleCheck(dev.mac, v)"
          />
          <div class="card-device-info">
            <span class="card-dev-name">{{ dev.name }}</span>
            <code class="card-mac">{{ dev.mac }}</code>
          </div>
          <div class="card-status-group">
            <span
              class="status-dot"
              :class="{ online: dev.status === 'online' }"
              :title="dev.status === 'online' ? '在线' : '离线'"
            />
            <el-tag
              v-if="dev.updateStatus && dev.updateStatus !== 'pending'"
              :type="updateTagType(dev.updateStatus)"
              size="small"
              class="card-update-tag"
            >{{ updateLabel(dev.updateStatus) }}</el-tag>
            <span v-else class="card-pending">待推送</span>
          </div>
        </div>

        <!-- 卡片内容：字段编辑 -->
        <div class="card-fields">
          <div
            v-for="field in templateInfo.fields"
            :key="dev.mac + '-mf-' + field.key"
            class="card-field-row"
            :class="{ 'is-custom': isOverridden(dev.mac, field.key) }"
          >
            <label class="field-label">{{ field.label }}{{ field.required ? '*' : '' }}</label>
            <div class="field-input-wrap">
              <input
                type="text"
                class="cell-input card-input"
                :value="getEffective(dev.mac, field.key)"
                :placeholder="defaultPlaceholder(field)"
                @focus="onFocus(dev.mac, field.key)"
                @blur="onBlur(dev.mac, field.key, $event)"
                @keydown.enter="($event.target as HTMLInputElement).blur()"
              />
              <button
                v-if="isOverridden(dev.mac, field.key)"
                class="cell-clear card-clear"
                title="恢复默认值"
                @click.stop="clearField(dev.mac, field.key)"
              >&#x2715;</button>
            </div>
          </div>
        </div>

        <!-- 卡片底部：操作按钮 -->
        <div class="card-actions">
          <button
            class="btn-push"
            :class="{ disabled: dev.status !== 'online' }"
            @click="$emit('pushDevice', dev)"
          >推送</button>
          <button class="btn-remove" @click="$emit('removeBinding', dev)">移除</button>
        </div>
      </div>
    </div>

    <!-- 底部工具条 -->
    <div v-if="devices.length > 0" class="table-footer-bar">
      <div class="footer-left">
        <el-button size="small" text type="primary" @click="$emit('update:checkedMacs', devices.map(d => d.mac))">
          全选
        </el-button>
        <el-button size="small" text @click="$emit('update:checkedMacs', [])">
          清除选择
        </el-button>
      </div>
      <div class="footer-right">
        <span class="custom-hint" v-if="customCount > 0">
          <AlertCircle :size="12" /> {{ customCount }} 台有自定义数据
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, AlertCircle } from 'lucide-vue-next'
import type { TemplateInfo } from '@/types'

const props = withDefaults(defineProps<{
  templateInfo: TemplateInfo
  devices: Array<{ mac: string; name: string; status: string; hasCustom: boolean; updateStatus?: string; errorMsg?: string; sentAt?: string; finishedAt?: string }>
  defaultData: Record<string, any>
  customOverrides: Record<string, Record<string, any>>
  checkedMacs: string[]
}>(), {
  checkedMacs: () => [],
})

const emit = defineEmits<{
  'update:checkedMacs': [val: string[]]
  'update:customOverrides': [val: Record<string, Record<string, any>>]
  removeDevice: [mac: string]
  pushDevice: [dev: any]
  removeBinding: [dev: any]
}>()

// ── 调试：监听 customOverrides 变化 ──
watch(() => props.customOverrides, (newVal, oldVal) => {
  console.log('[DeviceDataTable] customOverrides 变化:', {
    new: JSON.parse(JSON.stringify(newVal)),
    old: JSON.parse(JSON.stringify(oldVal))
  })
}, { deep: true })

// ── Checkbox 逻辑 ──
const isAllChecked = computed(() =>
  props.devices.length > 0 && props.checkedMacs.length === props.devices.length
)

const isPartialChecked = computed(() =>
  props.checkedMacs.length > 0 && props.checkedMacs.length < props.devices.length
)

function isChecked(mac: string): boolean {
  return props.checkedMacs.includes(mac)
}

function toggleCheck(mac: string, checked: boolean) {
  const list = [...props.checkedMacs]
  if (checked) {
    if (!list.includes(mac)) list.push(mac)
  } else {
    const idx = list.indexOf(mac)
    if (idx >= 0) list.splice(idx, 1)
  }
  emit('update:checkedMacs', list)
}

function toggleAll(checked: boolean) {
  emit('update:checkedMacs', checked ? props.devices.map(d => d.mac) : [])
}

// ── 统计 ──
const customCount = computed(() =>
  props.devices.filter(d => props.customOverrides[d.mac] && Object.values(props.customOverrides[d.mac]).some(v => v !== '' && v != null)).length
)

// ── 数据读取 ──
function getEffective(mac: string, key: string): string {
  if (props.customOverrides[mac]?.[key] != null && props.customOverrides[mac][key] !== '') {
    return String(props.customOverrides[mac][key])
  }
  if (props.defaultData[key] != null) return String(props.defaultData[key])
  return ''
}

function defaultPlaceholder(field: any): string {
  const v = props.defaultData[field.key]
  return (v != null ? String(v) : '') || '(空)'
}

function isOverridden(mac: string, key: string): boolean {
  const o = props.customOverrides[mac]
  if (!o) return false
  const v = o[key]
  return v !== undefined && v !== ''
}

function hasAnyValue(mac: string): boolean {
  const o = props.customOverrides[mac]
  if (!o) return false
  for (const k of Object.keys(o)) {
    const v = o[k]
    if (v !== '' && v != null) return true
  }
  return false
}

// ── 更新状态标签 ──

const UPDATE_STATUS_MAP: Record<string, { label: string; type: 'info' | 'warning' | 'success' | 'danger' }> = {
  pending: { label: '待推送', type: 'info' },
  sent: { label: '正在更新', type: 'warning' },
  success: { label: '更新成功', type: 'success' },
  failed:  { label: '更新失败', type: 'danger' },
}

function updateTagType(status: string): 'info' | 'warning' | 'success' | 'danger' {
  return UPDATE_STATUS_MAP[status]?.type ?? 'info'
}
function updateLabel(status: string): string {
  return UPDATE_STATUS_MAP[status]?.label ?? status
}

/** 格式化时间字符串为短格式 HH:mm:ss */
function formatTimeShort(timeStr?: string): string {
  if (!timeStr) return ''
  // 只取时间部分
  const parts = timeStr.split(' ')
  return parts.length > 1 ? parts[1].substring(0, 8) : timeStr.substring(11, 19)
}

// ── 编辑操作 ──
const _originalMap = ref<Record<string, string>>({})

function onFocus(mac: string, key: string) {
  _originalMap.value[mac + '::' + key] = getEffective(mac, key)
}

function onBlur(mac: string, key: string, event: FocusEvent) {
  const input = event.target as HTMLInputElement
  const newValue = input.value.trim()
  const fullKey = mac + '::' + key
  const original = _originalMap.value[fullKey]

  // 值没变则跳过
  if (newValue === original) {
    delete _originalMap.value[fullKey]
    return
  }

  const defaultVal = (props.defaultData[key] != null) ? String(props.defaultData[key]) : ''
  if (newValue === defaultVal || newValue === '') {
    clearField(mac, key)
  } else {
    const ov: any = {}
    for (const k of Object.keys(props.customOverrides)) {
      ov[k] = Object.assign({}, props.customOverrides[k])
    }
    if (!ov[mac]) ov[mac] = {}
    ov[mac][key] = newValue
    emit('update:customOverrides', ov)
  }
  delete _originalMap.value[fullKey]
}

function clearField(mac: string, key: string) {
  const ov: any = {}
  for (const k of Object.keys(props.customOverrides)) {
    ov[k] = Object.assign({}, props.customOverrides[k])
  }
  if (ov[mac]) {
    delete ov[mac][key]
    if (Object.keys(ov[mac]).length === 0) delete ov[mac]
  }
  emit('update:customOverrides', ov)
}
</script>

<style scoped>
.device-data-table {
  display: flex;
  flex-direction: column;
}

/* 滚动区域 */
.table-scroll {
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid #e8ecf1;
}

/* 表格 */
.edit-table {
  width: 100%;
  min-width: 520px; /* 缩小到适配更多屏幕 */
  border-collapse: collapse;
  font-size: 12.5px;

  th {
    background: #f8fafc;
    padding: 10px 8px;
    font-weight: 600;
    color: #475569;
    text-align: left;
    white-space: nowrap;
    border-bottom: 2px solid #e2e8f0;
    position: sticky;
    top: 0;
    z-index: 2;
    &.field-required { color: #d97706; }
  }

  td {
    padding: 3px 6px;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: middle;
    white-space: nowrap;
  }

  tr:hover td { background: #fafbfc; }
  tr.has-custom > td { background: rgba(245,158,11,0.03); }
  tr.has-custom:hover td { background: rgba(245,158,11,0.06); }
  tr.checked > td { background: rgba(99,102,241,0.04); }
}

/* 列宽 */
.col-check { width: 38px; text-align: center; }
.col-name {
  position: sticky;
  left: 0;
  background: white;
  z-index: 1;
  min-width: 120px;
}
.col-mac { /* 已合并到 col-name */ }
.col-device-status { min-width: 70px; text-align: center; vertical-align: middle; }
.col-update-status { min-width: 80px; text-align: center; vertical-align: middle; }
.col-sent-at { min-width: 85px; text-align: center; vertical-align: middle; }
.col-finished-at { min-width: 85px; text-align: center; vertical-align: middle; }
.col-field { min-width: 90px; position: relative; }
.col-action { min-width: 95px; text-align: center; }

/* 设备名 */
.dev-name { display: block; font-weight: 500; font-size: 13px; color: #334155; }
.mac-code {
  display: block;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 10.5px;
  color: #94a3b8;
  margin-top: 1px;
}

/* 状态圆点 */
.status-dot {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #cbd5e1;
  &.online { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.4); }
}
/* 设备状态列 */
.device-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}
/* 更新状态列 */
.update-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}
/* 时间单元格 */
.time-cell, .empty-cell {
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  white-space: nowrap;
}
.time-cell { color: #6b7280; }
.time-cell.finished { color: #374151; }
.empty-cell { color: #d1d5db; }
/* 在线/离线文字 */
.status-text {
  font-size: 11.5px;
  font-weight: 500;
  &.text-online { color: #16a34a; }
  &.text-offline { color: #94a3b8; }
}
/* 更新标签 */
.update-tag {
  font-size: 10px;
  height: 18px;
  line-height: 18px;
  padding: 0 5px;
}
.pending-text {
  font-size: 11px;
  color: #9ca3af;
}
/* 时间文字 */
.time-text {
  font-size: 9.5px;
  color: #a1a1aa;
  font-family: ui-monospace, SFMono-Regular, monospace;
  margin-left: 2px;
  &.finished { color: #6b7280; }
}

/* 可编辑单元格 */
.cell-input {
  width: 100%;
  padding: 5px 20px 5px 7px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 12.5px;
  color: #1e293b;
  background: transparent;
  outline: none;
  transition: all 0.15s ease;
  box-sizing: border-box;

  &:hover { border-color: #d1d5db; background: white; }
  &:focus {
    border-color: #6366f1;
    background: white;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.1);
  }
  &::placeholder { color: #c8ccd4; font-size: 11.5px; }
}

td.is-custom .cell-input {
  color: #b45309;
  font-weight: 500;
  background: rgba(245,158,11,0.04);
  border-color: rgba(245,158,11,0.15);
  &:hover, &:focus { background: rgba(245,158,11,0.08); border-color: #f59e0b; }
}

.cell-clear {
  position: absolute;
  right: 3px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: #fef2f2;
  color: #ef4444;
  cursor: pointer;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
  &:hover { background: #fee2e2; }
}
.col-field:hover .cell-clear { opacity: 1; }

/* 操作列 */
.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.btn-push, .btn-remove {
  padding: 3px 8px;
  border-radius: 5px;
  border: 1px solid transparent;
  font-size: 11.5px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;

  &.disabled { opacity: 0.4; cursor: not-allowed; }
}

.btn-push {
  background: rgba(99,102,241,0.08);
  color: #6366f1;
  &:hover:not(.disabled) { background: rgba(99,102,241,0.16); }
}

.btn-remove {
  background: rgba(107,114,128,0.08);
  color: #64748b;
  &:hover { background: rgba(107,114,128,0.16); }
}

/* 底部工具条 */
.table-footer-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding: 8px 4px;
}
.footer-left {
  display: flex;
  align-items: center;
  gap: 4px;
}
.custom-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #f59e0b;
}

/* ═══ 移动端：卡片列表 ═══ */
@media screen and (max-width: 768px) {
  /* 隐藏桌面表格，显示卡片列表 */
  .desktop-table { display: none !important; }
  .mobile-card-list {
    display: flex !important;
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }

  .device-data-table {
    width: 100%;
  }

  .device-card {
    background: white;
    border-radius: 12px;
    border: 1.5px solid #e8ecf1;
    padding: 14px;
    transition: border-color 0.2s;

    &.is-checked {
      border-color: #6366f1;
      background: rgba(99,102,241,0.02);
    }

    &.has-custom {
      border-color: #f59e0b;
      background: rgba(245,158,11,0.015);
    }
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;

    :deep(.el-checkbox) { --el-checkbox-font-size: 15px; }
  }

  .card-device-info {
    flex: 1;
    min-width: 0;
  }

  .card-dev-name {
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: #334155;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .card-mac {
    display: block;
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 11px;
    color: #94a3b8;
    margin-top: 1px;
  }

  .card-status-group {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }

  .card-update-tag {
    font-size: 10.5px !important;
    height: 20px !important;
    line-height: 20px !important;
    padding: 0 7px !important;
  }

  .card-pending {
    font-size: 11px;
    color: #9ca3af;
    padding: 2px 7px;
    background: rgba(156,175,195,0.08);
    border-radius: 10px;
  }

  .card-fields {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 4px;
  }

  .card-field-row {
    display: flex;
    align-items: center;
    gap: 10px;

    &.is-custom .field-label { color: #b45309; }
  }

  .field-label {
    width: 70px;
    flex-shrink: 0;
    font-size: 13px;
    font-weight: 500;
    color: #475569;

    &::after { content: ':'; }
  }

  .field-input-wrap {
    flex: 1;
    position: relative;
  }

  .card-input {
    width: 100%;
    padding: 8px 26px 8px 10px;
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    font-size: 13.5px;
    color: #1e293b;
    background: #f8fafc;
    outline: none;
    box-sizing: border-box;
    transition: all 0.15s ease;

    &:focus {
      border-color: #6366f1;
      background: white;
      box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
    }

    &::placeholder { color: #c8ccd4; font-size: 12px; }
  }

  td.is-custom .card-input,
  .card-field-row.is-custom .card-input {
    color: #b45309;
    font-weight: 500;
    background: rgba(245,158,11,0.05);
    border-color: rgba(245,158,11,0.25);
    &:focus { border-color: #f59e0b; box-shadow: 0 0 0 3px rgba(245,158,11,0.1); }
  }

  .card-clear {
    position: absolute;
    right: 5px;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: none;
    background: #fef2f2;
    color: #ef4444;
    cursor: pointer;
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 1; /* 移动端始终可见 */
    &:hover { background: #fee2e2; }
  }

  .card-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 12px;
    padding-top: 10px;
    border-top: 1px solid #f1f5f9;
  }

  .btn-push, .btn-remove {
    padding: 7px 16px;
    border-radius: 8px;
    font-size: 13px;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;

    &.disabled { opacity: 0.4; cursor: not-allowed; }
  }

  .btn-push {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    box-shadow: 0 2px 8px rgba(99,102,241,0.25);
    &:hover:not(.disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99,102,241,0.35); }
  }

  .btn-remove {
    background: rgba(107,114,128,0.06);
    color: #64748b;
    border: 1px solid #e2e8f0;
    &:hover { background: rgba(107,114,128,0.12); }
  }

  /* 底部工具条移动端适配 */
  .table-footer-bar {
    flex-wrap: wrap;
    gap: 8px;
  }

  .footer-left { flex-wrap: wrap; }
}

/* 桌面端默认隐藏卡片列表 */
.mobile-card-list { display: none; }
</style>
