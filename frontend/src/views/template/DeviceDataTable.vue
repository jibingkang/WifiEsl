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
          <template v-for="dev in devices" :key="'dev-' + dev.mac">
            <!-- 主设备行 -->
            <tr
              :class="{ 'has-custom': hasAnyValue(dev.mac), checked: isChecked(dev.mac), 'row-expanded': expandedMacs.includes(dev.mac) }"
            >
              <!-- checkbox + 折叠按钮 + 行选择radio -->
              <td class="col-check">
                <div class="check-expand-wrap">
                  <button
                    v-if="(dev.rowCount ?? 0) > 0 || dev.rows?.length"
                    class="btn-expand"
                    :class="{ expanded: expandedMacs.includes(dev.mac) }"
                    @click.stop="toggleExpand(dev.mac)"
                  >
                    <ChevronRight :size="12" />
                  </button>
                  <span v-else class="expand-placeholder" />
                  <el-checkbox
                    :model-value="isChecked(dev.mac)"
                    @change="(v: boolean) => toggleCheck(dev.mac, v)"
                  />
                  <input
                    v-if="dev.rows && dev.rows.length > 0"
                    type="radio"
                    :name="'row-select-' + dev.mac"
                    :checked="selectedRowIds[dev.mac] === dev.rows[0].id"
                    @change="selectRow(dev.mac, dev.rows[0].id)"
                    class="row-radio row-radio-main"
                    title="切换到第1行数据"
                  />
                </div>
              </td>

              <!-- 设备名+MAC -->
              <td class="col-name">
                <span class="dev-name">{{ dev.name }}</span>
                <code class="mac-code">{{ dev.mac }}</code>
                <span v-if="(dev.rowCount ?? 0) > 0 || dev.rows?.length" class="row-badge">{{ dev.rowCount ?? dev.rows?.length }} 行数据</span>
                <span v-if="dev.rows && dev.rows.length > 1" class="active-row-tag">显示 #{{ getActiveRowIndex(dev.mac) }}</span>
              </td>

              <!-- 设备在线状态+电量 -->
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
                <div v-if="dev.voltage" class="device-battery">
                  {{ formatVoltage(dev.voltage) }}
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

              <!-- 每个字段可编辑（主行：编辑当前选中行的数据） -->
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

            <!-- 子表行（折叠展示，包含第1行在内的所有行） -->
            <template v-if="expandedMacs.includes(dev.mac) && dev.rows && dev.rows.length > 0">
              <tr
                v-for="(row, rowIndex) in dev.rows"
                :key="'row-' + dev.mac + '-' + row.id"
                class="sub-row"
                :class="{ 'row-selected': selectedRowIds[dev.mac] === row.id, 'sub-row-first': rowIndex === 0 }"
              >
                <td class="col-check sub-check">
                  <div class="sub-row-indent">
                    <input
                      type="radio"
                      :name="'row-select-' + dev.mac"
                      :checked="selectedRowIds[dev.mac] === row.id"
                      @change="selectRow(dev.mac, row.id)"
                      class="row-radio"
                      :title="'切换到此行数据'"
                    />
                    <span v-if="rowIndex === 0" class="sub-row-marker sub-row-marker-first" />
                    <span v-else class="sub-row-marker" />
                    <span class="sub-row-index">#{{ rowIndex + 1 }}</span>
                  </div>
                </td>
                <td colspan="5" class="sub-info-cell">
                  <span class="sub-row-label">数据行 {{ rowIndex + 1 }}</span>
                  <span v-if="rowIndex === 0" class="sub-row-first-tag">主行</span>
                  <span class="sub-row-time">{{ formatTimeShort(row.created_at) }}</span>
                </td>
                <!-- 子行字段编辑 -->
                <td
                  v-for="field in templateInfo.fields"
                  :key="'sr-' + dev.mac + '-' + row.id + '-' + field.key"
                  class="col-field sub-field"
                  :class="{ 'is-custom': isRowOverridden(row.id, field.key) }"
                >
                  <input
                    type="text"
                    class="cell-input sub-input"
                    :value="getRowEffective(row, field.key)"
                    :placeholder="defaultPlaceholder(field)"
                    @focus="onRowFocus(row.id, field.key, getRowEffective(row, field.key))"
                    @blur="onRowBlur(row.id, dev.mac, dev.taskId, field.key, $event)"
                    @keydown.enter="($event.target as HTMLInputElement).blur()"
                  />
                  <button
                    v-if="isRowOverridden(row.id, field.key)"
                    class="cell-clear"
                    title="恢复默认值"
                    @click.stop="clearRowField(row.id, dev.mac, field.key)"
                  >&#x2715;</button>
                </td>
                <!-- 子行操作列 -->
                <td class="col-action sub-action">
                  <div class="action-btns">
                    <button
                      class="btn-push-sub"
                      :class="{ disabled: dev.status !== 'online' }"
                      title="仅推送此行数据到设备"
                      @click="$emit('pushRow', dev, row)"
                    >推送此行</button>
                    <button class="btn-remove-sub" title="删除此数据行" @click="handleDeleteRow(row.id, dev.mac, dev.taskId)">删除</button>
                  </div>
                </td>
              </tr>
            </template>
          </template>
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
        <!-- 卡片头部 -->
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
          <!-- 折叠按钮 -->
          <button
            v-if="dev.rows && dev.rows.length > 0"
            class="card-expand-btn"
            :class="{ expanded: expandedMacs.includes(dev.mac) }"
            @click="toggleExpand(dev.mac)"
          >
            <ChevronRight :size="14" />
          </button>
        </div>

        <!-- 卡片内容：主行字段编辑 -->
        <div class="card-fields">
          <div v-if="dev.rows && dev.rows.length > 1" class="card-active-row-hint">
            当前显示 #{{ getActiveRowIndex(dev.mac) }} 行数据
          </div>
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

        <!-- 卡片子行区域 -->
        <div v-if="expandedMacs.includes(dev.mac) && dev.rows && dev.rows.length > 0" class="card-sub-rows">
          <div class="card-sub-header">多行数据 ({{ dev.rows.length }} 条)</div>
          <div
            v-for="(row, rowIndex) in dev.rows"
            :key="'mr-' + dev.mac + '-' + row.id"
            class="card-sub-item"
            :class="{ 'sub-item-active': selectedRowIds[dev.mac] === row.id }"
          >
            <div class="card-sub-title">
              <input
                type="radio"
                :name="'mob-row-select-' + dev.mac"
                :checked="selectedRowIds[dev.mac] === row.id"
                @change="selectRow(dev.mac, row.id)"
                class="row-radio row-radio-mob"
                :title="'切换到此行数据'"
              />
              <span class="sub-tag">#{{ rowIndex + 1 }}</span>
              <span v-if="rowIndex === 0" class="sub-row-first-tag-mob">主行</span>
              <button class="btn-remove-sub" @click="handleDeleteRow(row.id, dev.mac, dev.taskId)">删除</button>
            </div>
            <div
              v-for="field in templateInfo.fields"
              :key="'msr-' + row.id + '-' + field.key"
              class="card-field-row sub-field-row"
              :class="{ 'is-custom': isRowOverridden(row.id, field.key) }"
            >
              <label class="field-label sub-label">{{ field.label }}</label>
              <div class="field-input-wrap">
                <input
                  type="text"
                  class="cell-input card-input"
                  :value="getRowEffective(row, field.key)"
                  :placeholder="defaultPlaceholder(field)"
                  @focus="onRowFocus(row.id, field.key, getRowEffective(row, field.key))"
                  @blur="onRowBlur(row.id, dev.mac, dev.taskId, field.key, $event)"
                  @keydown.enter="($event.target as HTMLInputElement).blur()"
                />
                <button
                  v-if="isRowOverridden(row.id, field.key)"
                  class="cell-clear card-clear"
                  title="恢复默认值"
                  @click.stop="clearRowField(row.id, dev.mac, field.key)"
                >&#x2715;</button>
              </div>
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
import { X, AlertCircle, ChevronRight, Plus, Trash2 } from 'lucide-vue-next'
import type { TemplateInfo } from '@/types'
import { formatVoltage } from '@/utils/format'
import { taskApi } from '@/api/task'

const props = withDefaults(defineProps<{
  templateInfo: TemplateInfo
  devices: Array<{ mac: string; name: string; status: string; hasCustom: boolean; updateStatus?: string; errorMsg?: string; sentAt?: string; finishedAt?: string; voltage?: number; id?: number; taskId?: number; rowCount?: number; rows?: Array<{ id: number; task_device_id: number; sort_order: number; custom_data: string | Record<string, any>; created_at: string }> }>
  defaultData: Record<string, any>
  customOverrides: Record<string, Record<string, any>>
  checkedMacs: string[]
  selectedRows?: Record<string, number> // mac -> row_id
}>(), {
  checkedMacs: () => [],
  selectedRows: () => ({}),
})

const emit = defineEmits<{
  'update:checkedMacs': [val: string[]]
  'update:customOverrides': [val: Record<string, Record<string, any>>]
  'update:selectedRows': [val: Record<string, number>] // mac -> row_id
  removeDevice: [mac: string]
  pushDevice: [dev: any]
  removeBinding: [dev: any]
  pushRow: [dev: any, row: any] // 推送指定行
  dataChanged: [] // 数据变更（增删子行等），通知父组件刷新
}>()

// ── 折叠状态管理 ──
const expandedMacs = ref<string[]>([])

// ── 行选择状态管理 ──
// 使用内部 ref 管理，避免与父组件双向同步导致递归更新
const selectedRowIds = ref<Record<string, number>>({})

// 标记是否正在同步中，防止递归
let _syncingFromParent = false

// 同步父组件传入的 selectedRows（仅父→子方向）
watch(() => props.selectedRows, (val) => {
  if (_syncingFromParent) return
  _syncingFromParent = true
  try {
    if (val) {
      selectedRowIds.value = { ...val }
    }
  } finally {
    _syncingFromParent = false
  }
}, { immediate: true, deep: true })

// 初始化默认选中第一行（仅当该设备没有选中行时）
watch(() => props.devices, (devices) => {
  let changed = false
  devices.forEach(dev => {
    if (dev.rows && dev.rows.length > 0 && !selectedRowIds.value[dev.mac]) {
      selectedRowIds.value[dev.mac] = dev.rows[0].id
      changed = true
    }
  })
  // 只在确实有变化时才通知父组件
  if (changed) {
    emit('update:selectedRows', { ...selectedRowIds.value })
  }
}, { immediate: true, deep: true })

// 同步到父组件（仅子→父方向，不再监听 deep 变化避免递归）
function _syncToParent() {
  emit('update:selectedRows', { ...selectedRowIds.value })
}

function selectRow(mac: string, rowId: number) {
  const oldRowId = selectedRowIds.value[mac]

  // 如果行没变，无需处理
  if (oldRowId === rowId) return

  // 1. Flush 旧行的 customOverrides 缓存到后端
  if (oldRowId) {
    _flushMainEditsToRow(mac, oldRowId)
  }

  // 2. 切换选中行
  selectedRowIds.value = { ...selectedRowIds.value, [mac]: rowId }

  // 3. 用新行数据重新填充 customOverrides[mac]
  _loadRowToOverrides(mac, rowId)

  _syncToParent()
}

/**
 * 将主行 customOverrides[mac] 的缓存数据持久化到后端对应子行
 */
function _flushMainEditsToRow(mac: string, rowId: number) {
  const overrides = props.customOverrides[mac]
  if (!overrides || Object.keys(overrides).length === 0) return

  // 找到旧行，合并缓存数据
  const dev = props.devices.find(d => d.mac === mac)
  const row = dev?.rows?.find((r: any) => r.id === rowId)
  if (!row) return

  const currentData = parseRowCustomData(row)
  for (const [k, v] of Object.entries(overrides)) {
    if (v !== '' && v != null) {
      currentData[k] = v
    } else {
      delete currentData[k]
    }
  }
  taskApi.updateDeviceRow(rowId, currentData).catch((e: any) => {
    console.error('[DeviceDataTable] flush旧行缓存失败:', e)
  })
}

/**
 * 从后端子行数据加载到 customOverrides[mac] 缓存
 */
function _loadRowToOverrides(mac: string, rowId: number) {
  const dev = props.devices.find(d => d.mac === mac)
  const row = dev?.rows?.find((r: any) => r.id === rowId)
  if (!row) {
    // 没有对应子行，清空缓存
    if (props.customOverrides[mac]) {
      const ov: any = {}
      for (const k of Object.keys(props.customOverrides)) {
        if (k !== mac) ov[k] = Object.assign({}, props.customOverrides[k])
      }
      emit('update:customOverrides', ov)
    }
    return
  }

  const rowData = parseRowCustomData(row)
  const newMacOverrides: Record<string, any> = {}
  for (const [k, v] of Object.entries(rowData)) {
    // 只缓存与默认值不同的字段
    const defaultVal = props.defaultData[k] != null ? String(props.defaultData[k]) : ''
    if (String(v) !== defaultVal && v !== '' && v != null) {
      newMacOverrides[k] = v
    }
  }

  const ov: any = {}
  for (const k of Object.keys(props.customOverrides)) {
    if (k !== mac) ov[k] = Object.assign({}, props.customOverrides[k])
  }
  // 只有选中行有覆盖数据时才设置，否则不保留旧行残留
  if (Object.keys(newMacOverrides).length > 0) {
    ov[mac] = { ...newMacOverrides }
  }
  emit('update:customOverrides', ov)
}

function getSelectedRowId(mac: string): number | undefined {
  return selectedRowIds.value[mac]
}

function toggleExpand(mac: string) {
  const idx = expandedMacs.value.indexOf(mac)
  if (idx >= 0) {
    expandedMacs.value.splice(idx, 1)
  } else {
    expandedMacs.value.push(mac)
  }
}

// ── 子行编辑状态 ──
// 使用复合 key "rowId::fieldKey" 存储子行的临时覆盖数据
const rowEdits = ref<Record<string, Record<string, string>>>({})

function getRowKey(rowId: number): string {
  return 'r_' + rowId
}

// ── 调试监听 ──
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

// ── 主行数据读取（跟随当前选中行） ──

/** 获取设备当前选中的子表行对象，如果没有选中则回退到第1行 */
function getActiveRow(mac: string) {
  const dev = props.devices.find(d => d.mac === mac)
  if (!dev?.rows || dev.rows.length === 0) return null
  const selectedId = selectedRowIds.value[mac]
  if (selectedId) {
    const found = dev.rows.find((r: any) => r.id === selectedId)
    if (found) return found
  }
  return dev.rows[0]
}

/** 获取设备当前选中行在 rows 中的序号（1-based），用于 UI 指示 */
function getActiveRowIndex(mac: string): number {
  const dev = props.devices.find(d => d.mac === mac)
  if (!dev?.rows || dev.rows.length === 0) return 1
  const selectedId = selectedRowIds.value[mac]
  if (selectedId) {
    const idx = dev.rows.findIndex((r: any) => r.id === selectedId)
    if (idx >= 0) return idx + 1
  }
  return 1
}

function getEffective(mac: string, key: string): string {
  // 1. 优先看本地编辑缓存
  if (props.customOverrides[mac]?.[key] != null && props.customOverrides[mac][key] !== '') {
    return String(props.customOverrides[mac][key])
  }

  // 2. 如果有子表行，显示当前选中行的数据（而非固定第1行）
  const activeRow = getActiveRow(mac)
  if (activeRow) {
    const rowData = parseRowCustomData(activeRow)
    if (rowData[key] != null && rowData[key] !== '') {
      return String(rowData[key])
    }
  }

  // 3. 最后显示默认值
  if (props.defaultData[key] != null) return String(props.defaultData[key])
  return ''
}

function defaultPlaceholder(field: any): string {
  const v = props.defaultData[field.key]
  return (v != null ? String(v) : '') || '(空)'
}

function isOverridden(mac: string, key: string): boolean {
  // 1. 先看本地编辑缓存
  const o = props.customOverrides[mac]
  if (o && o[key] !== undefined && o[key] !== '') return true

  // 2. 再看当前选中行的数据是否覆盖默认值
  const activeRow = getActiveRow(mac)
  if (activeRow) {
    const rowData = parseRowCustomData(activeRow)
    const defaultVal = props.defaultData[key] != null ? String(props.defaultData[key]) : ''
    if (rowData[key] != null && String(rowData[key]) !== '' && String(rowData[key]) !== defaultVal) {
      return true
    }
  }

  return false
}

function hasAnyValue(mac: string): boolean {
  const o = props.customOverrides[mac]
  if (o) {
    for (const k of Object.keys(o)) {
      const v = o[k]
      if (v !== '' && v != null) return true
    }
  }

  // 还需检查选中行是否有覆盖默认值的数据
  const activeRow = getActiveRow(mac)
  if (activeRow) {
    const rowData = parseRowCustomData(activeRow)
    for (const k of Object.keys(rowData)) {
      const defaultVal = props.defaultData[k] != null ? String(props.defaultData[k]) : ''
      if (rowData[k] != null && String(rowData[k]) !== '' && String(rowData[k]) !== defaultVal) {
        return true
      }
    }
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
  const parts = timeStr.split(' ')
  return parts.length > 1 ? parts[1].substring(0, 8) : timeStr.substring(11, 19)
}

// ── 主行编辑操作 ──
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

  // 更新 customOverrides（前端缓存）
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

  // 同步更新当前选中行的 custom_data
  const activeRow = getActiveRow(mac)
  if (activeRow) {
    const currentData = parseRowCustomData(activeRow)
    if (newValue === defaultVal || newValue === '') {
      delete currentData[key]
    } else {
      currentData[key] = newValue
    }
    taskApi.updateDeviceRow(activeRow.id, currentData).catch((e: any) => {
      console.error('[DeviceDataTable] 同步更新选中行失败:', e)
    })
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

  // 同步清除当前选中行对应字段
  const activeRow = getActiveRow(mac)
  if (activeRow) {
    const currentData = parseRowCustomData(activeRow)
    delete currentData[key]
    taskApi.updateDeviceRow(activeRow.id, currentData).catch((e: any) => {
      console.error('[DeviceDataTable] 同步清除选中行字段失败:', e)
    })
  }
}

// ════════════════════ 子行操作 ════════════════════

/**
 * 解析子行 custom_data 为对象
 */
function parseRowCustomData(row: any): Record<string, any> {
  const cd = row.custom_data
  if (typeof cd === 'string') {
    try { return JSON.parse(cd) } catch { return {} }
  }
  return cd || {}
}

/**
 * 获取子行某字段的有效值（先看本地编辑缓存，再看原始数据，最后看默认值）
 */
function getRowEffective(row: any, key: string): string {
  const rk = getRowKey(row.id)
  const edit = rowEdits.value[rk]?.[key]
  if (edit !== undefined && edit !== '') return edit

  const data = parseRowCustomData(row)
  if (data[key] != null && data[key] !== '') return String(data[key])

  if (props.defaultData[key] != null) return String(props.defaultData[key])
  return ''
}

/**
 * 判断子行某字段是否有自定义覆盖
 */
function isRowOverridden(rowId: number, key: string): boolean {
  const rk = getRowKey(rowId)
  const edit = rowEdits.value[rk]?.[key]
  if (edit !== undefined && edit !== '') return true
  // 还需要检查原始 row 数据中是否有覆盖...这里简化为只检查 edits
  return false
}

/** 子行 focus 记录原值 */
function onRowFocus(rowId: number, key: string, currentValue: string) {
  const fullKey = 'row_' + rowId + '::' + key
  _originalMap.value[fullKey] = currentValue
}

/** 子行 blur 保存 */
async function onRowBlur(rowId: number, mac: string, _taskId: number | undefined, key: string, event: FocusEvent) {
  const input = event.target as HTMLInputElement
  const newValue = input.value.trim()
  const fullKey = 'row_' + rowId + '::' + key
  const original = _originalMap.value[fullKey]

  if (newValue === original) {
    delete _originalMap.value[fullKey]
    return
  }

  // 更新本地编辑缓存
  const rk = getRowKey(rowId)
  if (!rowEdits.value[rk]) rowEdits.value[rk] = {}
  rowEdits.value[rk][key] = newValue

  // 调用 API 更新到后端
  try {
    // 先获取该行现有的完整数据（从DOM反查或从props获取）
    const currentData: Record<string, any> = {}

    // 从当前设备的rows中找到对应row，获取现有数据
    const dev = props.devices.find(d => d.mac === mac)
    const row = dev?.rows?.find((r: any) => r.id === rowId)
    if (row) {
      const existingData = parseRowCustomData(row)
      Object.assign(currentData, existingData)
    }

    // 合并所有编辑值
    if (rowEdits.value[rk]) {
      for (const [k, v] of Object.entries(rowEdits.value[rk])) {
        currentData[k] = v
      }
    }
    await taskApi.updateDeviceRow(rowId, currentData)
  } catch (e) {
    console.error('[DeviceDataTable] 更新子行失败:', e)
  }

  delete _originalMap.value[fullKey]
}

/** 清除子行某个字段的编辑 */
async function clearRowField(rowId: number, mac: string, key: string) {
  const rk = getRowKey(rowId)
  if (rowEdits.value[rk]) {
    delete rowEdits.value[rk][key]
    if (Object.keys(rowEdits.value[rk]).length === 0) delete rowEdits.value[rk]
  }

  try {
    // 重新构建当前行数据（保留现有数据，删除指定字段）
    const currentData: Record<string, any> = {}

    // 从当前设备的rows中找到对应row，获取现有数据
    const dev = props.devices.find(d => d.mac === mac)
    const row = dev?.rows?.find((r: any) => r.id === rowId)
    if (row) {
      const existingData = parseRowCustomData(row)
      Object.assign(currentData, existingData)
    }

    // 删除被清除的字段
    delete currentData[key]

    // 合并其他编辑值
    if (rowEdits.value[rk]) {
      for (const [k, v] of Object.entries(rowEdits.value[rk])) {
        currentData[k] = v
      }
    }
    await taskApi.updateDeviceRow(rowId, currentData)
  } catch (e) {
    console.error('[DeviceDataTable] 清除子行字段失败:', e)
  }
}

/** 删除子行 */
async function handleDeleteRow(rowId: number, _mac: string, _taskId: number | undefined) {
  try {
    await taskApi.deleteDeviceRow(rowId)
    // 通知父组件刷新数据
    emit('dataChanged')
  } catch (e) {
    console.error('[DeviceDataTable] 删除子行失败:', e)
  }
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
  min-width: 520px;
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
.col-check { width: 50px; text-align: center; }
.col-name {
  position: sticky;
  left: 0;
  background: white;
  z-index: 1;
  min-width: 140px;
}
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
.device-battery {
  font-size: 11px;
  color: #22c55e;
  margin-top: 4px;
  text-align: center;
}

/* 行数徽章 */
.row-badge {
  display: inline-block;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  margin-top: 3px;
  font-weight: 500;
}

/* 当前选中行指示标签 */
.active-row-tag {
  display: inline-block;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  margin-top: 3px;
  margin-left: 4px;
  font-weight: 600;
  font-family: ui-monospace, SFMono-Regular, monospace;
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
.device-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}
.time-cell, .empty-cell {
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  white-space: nowrap;
}
.time-cell { color: #6b7280; }
.time-cell.finished { color: #374151; }
.empty-cell { color: #d1d5db; }
.status-text {
  font-size: 11.5px;
  font-weight: 500;
  &.text-online { color: #16a34a; }
  &.text-offline { color: #94a3b8; }
}
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

/* ═══ 折叠/展开按钮 ═══ */
.check-expand-wrap {
  display: flex;
  align-items: center;
  gap: 2px;
  justify-content: center;
}

.expand-placeholder {
  display: inline-block;
  width: 16px;
}

.btn-expand {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;

  &:hover { background: #f1f5f9; color: #6366f1; }
  &.expanded {
    transform: rotate(90deg);
    color: #6366f1;
  }
}

tr.row-expanded > td.col-name { border-left: 3px solid #6366f1; }

/* ═══ 子行样式 ═══ */
.sub-row {
  background: linear-gradient(135deg, #fafbff, #f8f0ff) !important;
  &:hover td { background: rgba(139,92,246,0.04) !important; }
}

.sub-check {
  border-left: 3px solid #a78bfa;
}

.sub-row-indent {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-left: 16px;
}

.sub-row-marker {
  display: inline-block;
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(to bottom, #8b5cf6, #a78bfa);
}

.sub-row-index {
  font-size: 10px;
  font-weight: 600;
  color: #8b5cf6;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.sub-info-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 4px !important;
}

.sub-row-label {
  font-size: 11.5px;
  font-weight: 500;
  color: #6d28d9;
}

.sub-row-time {
  font-size: 10px;
  color: #c4b5fd;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

/* 子表第1行（与主行关联） */
.sub-row-first {
  background: linear-gradient(135deg, #fffbeb, #fef3c7) !important;

  .sub-row-marker-first {
    display: inline-block;
    width: 3px;
    height: 14px;
    border-radius: 2px;
    background: linear-gradient(to bottom, #f59e0b, #d97706);
  }

  &:hover td { background: rgba(245,158,11,0.04) !important; }

  &.row-selected {
    background: linear-gradient(135deg, #fef08a, #fde047) !important;
    td {
      border-top: 1px solid rgba(245,158,11,0.25);
    }
  }
}

/* 第1行"主行"标签 */
.sub-row-first-tag {
  display: inline-block;
  font-size: 10px;
  padding: 0px 6px;
  border-radius: 6px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  font-weight: 600;
  line-height: 16px;
}

.sub-field { background: rgba(139,92,246,0.02) !important; }

.sub-input {
  background: rgba(255,255,255,0.7);
  border-color: rgba(139,92,246,0.15);

  &:hover { border-color: #a78bfa; background: white; }
  &:focus {
    border-color: #8b5cf6;
    background: white;
    box-shadow: 0 0 0 2px rgba(139,92,246,0.12);
  }
}

td.is-custom.sub-field .sub-input {
  color: #7c3aed;
  font-weight: 500;
  background: rgba(139,92,246,0.05);
  border-color: rgba(139,92,246,0.25);
  &:focus { border-color: #7c3aed; box-shadow: 0 0 0 3px rgba(124,58,237,0.12); }
}

.btn-remove-sub {
  padding: 2px 7px;
  border-radius: 5px;
  border: 1px solid transparent;
  font-size: 10.5px;
  cursor: pointer;
  color: #ef4444;
  background: rgba(239,68,68,0.06);
  transition: all 0.15s;
  white-space: nowrap;

  &:hover { background: rgba(239,68,68,0.14); }
}

/* ═══ 子行选择样式 ═══ */
.row-radio {
  width: 14px;
  height: 14px;
  cursor: pointer;
  accent-color: #8b5cf6;
}

.row-radio-main {
  accent-color: #6366f1;
}

/* 移动端子行radio */
.row-radio-mob {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.sub-row.row-selected {
  background: linear-gradient(135deg, #f3e8ff, #e9d5ff) !important;
  td {
    border-top: 1px solid rgba(139,92,246,0.2);
    border-bottom: 1px solid rgba(139,92,246,0.2);
  }
}

.btn-push-sub {
  padding: 2px 8px;
  border-radius: 5px;
  border: 1px solid transparent;
  font-size: 10.5px;
  cursor: pointer;
  color: #059669;
  background: rgba(16,185,129,0.08);
  transition: all 0.15s;
  white-space: nowrap;
  margin-right: 6px;

  &:hover {
    background: rgba(16,185,129,0.16);
  }

  &.disabled {
    color: #9ca3af;
    background: rgba(156,163,175,0.1);
    cursor: not-allowed;
  }
}

/* ═══ 移动端：卡片列表 ═══ */
@media screen and (max-width: 768px) {
  .desktop-table { display: none !important; }
  .mobile-card-list {
    display: flex !important;
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }

  .device-data-table { width: 100%; }

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

  .card-expand-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 6px;
    border: 1.5px solid #e2e8f0;
    background: #f8fafc;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;

    &:hover { border-color: #a78bfa; color: #8b5cf6; background: #faf5ff; }
    &.expanded { transform: rotate(90deg); color: #8b5cf6; border-color: #c4b5fd; background: #f5f0ff; }
  }

  .card-fields {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 4px;
  }

  .card-active-row-hint {
    font-size: 11px;
    font-weight: 600;
    color: #d97706;
    background: rgba(245,158,11,0.08);
    padding: 3px 8px;
    border-radius: 6px;
    text-align: center;
    margin-bottom: 2px;
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
    opacity: 1;
    &:hover { background: #fee2e2; }
  }

  /* 移动端子行区域 */
  .card-sub-rows {
    margin-top: 8px;
    padding: 12px;
    border-radius: 10px;
    background: linear-gradient(135deg, #fafbff, #f8f0ff);
    border: 1.5px solid #ede9fe;
  }

  .card-sub-header {
    font-size: 12px;
    font-weight: 600;
    color: #7c3aed;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e9d5ff;
  }

  .card-sub-item {
    padding: 10px 0;
    border-bottom: 1px dashed #e9d5ff;

    &:last-child { border-bottom: none; }
  }

  .card-sub-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .sub-tag {
    font-size: 11px;
    font-weight: 600;
    color: #fff;
    background: linear-gradient(135deg, #8b5cf6, #a78bfa);
    padding: 2px 8px;
    border-radius: 6px;
  }

  /* 移动端第1行"主行"标签 */
  .sub-row-first-tag-mob {
    font-size: 10px;
    padding: 1px 6px;
    border-radius: 5px;
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: white;
    font-weight: 600;
    line-height: 16px;
  }

  /* 移动端选中行高亮 */
  .sub-item-active {
    background: rgba(139,92,246,0.04) !important;
    border-left: 3px solid #8b5cf6;
    padding-left: 10px;
    border-radius: 6px;
  }

  .sub-field-row .field-label {
    color: #7c3aed;
    font-size: 12px;
    width: 60px;
  }

  .sub-label::after { content: ':'; }

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

  .table-footer-bar { flex-wrap: wrap; gap: 8px; }
  .footer-left { flex-wrap: wrap; }
}

/* 桌面端默认隐藏卡片列表 */
.mobile-card-list { display: none; }
</style>
