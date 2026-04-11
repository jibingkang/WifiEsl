<template>
  <div class="device-table-wrap">
    <el-table
      ref="tableRef"
      :data="devices"
      :loading="loading"
      row-key="mac"
      stripe
      highlight-current-row
      style="width: 100%"
      @selection-change="onSelectionChange"
      @row-click="(_, row) => $emit('rowClick', row)"
    >
      <!-- 多选列 -->
      <el-table-column type="selection" width="46" align="center" />

      <!-- MAC地址 -->
      <el-table-column prop="mac" label="MAC地址" min-width="170" show-overflow-tooltip fixed>
        <template #default="{ row }">
          <span class="mac-text">{{ formatMac(row.mac) }}</span>
        </template>
      </el-table-column>

      <!-- 名称/IP -->
      <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ row.name || '--' }}</template>
      </el-table-column>

      <el-table-column prop="ip" label="IP地址" min-width="130" show-overflow-tooltip>
        <template #default="{ row }">{{ row.ip || '--' }}</template>
      </el-table-column>

      <!-- 在线状态 -->
      <el-table-column prop="is_online" label="状态" width="90" align="center">
        <template #default="{ row }">
          <StatusBadge :online="row.is_online" />
        </template>
      </el-table-column>

      <!-- 电量 -->
      <el-table-column prop="voltage" label="电量" width="110" sortable align="center">
        <template #default="{ row }">
          <span v-if="row.voltage" :class="{ 'low-battery': row.is_online && row.voltage < 3000 }">
            {{ formatVoltage(row.voltage) }}
          </span>
          <span v-else>--</span>
        </template>
      </el-table-column>

      <!-- 信号强度 -->
      <el-table-column prop="rssi" label="信号" width="90" sortable align="center">
        <template #default="{ row }">
          <span v-if="row.rssi != null" :class="{ 'weak-signal': row.rssi < -70 }">
            {{ row.rssi }} dBm
          </span>
          <span v-else>--</span>
        </template>
      </el-table-column>

      <!-- 设备类型 -->
      <el-table-column prop="device_type" label="类型" width="110" align="center">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ DEVICE_TYPES[row.device_type] ?? row.device_type }}</el-tag>
        </template>
      </el-table-column>

      <!-- 屏幕类型 -->
      <el-table-column prop="screen_type" label="屏幕" width="95" align="center">
        <template #default="{ row }">
          <span>{{ SCREEN_TYPES[row.screen_type] ?? row.screen_type }}</span>
        </template>
      </el-table-column>

      <!-- 最后更新时间 -->
      <el-table-column prop="updated_at" label="更新时间" min-width="150" sortable show-overflow-tooltip>
        <template #default="{ row }">
          <span class="time-text">{{ formatRelativeTime(row.updated_at) }}</span>
        </template>
      </el-table-column>

      <!-- 操作 -->
      <el-table-column label="操作" width="220" align="center" fixed="right">
        <template #default="{ row }">
          <div class="action-group">
            <el-button text type="primary" size="small" @click.stop="$emit('control', { action: 'push', device: row })">
              推送
            </el-button>
            <el-button text type="primary" size="small" @click.stop="$emit('control', { action: 'edit', device: row })">
              编辑
            </el-button>
            <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, row)">
              <el-button text size="small"><el-icon><MoreFilled /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="reboot">重启设备</el-dropdown-item>
                  <el-dropdown-item command="battery">查询电量</el-dropdown-item>
                  <el-dropdown-item command="led">LED灯</el-dropdown-item>
                  <el-dropdown-item command="template" divided>应用模板</el-dropdown-item>
                  <el-dropdown-item command="delete" style="color: #ef4444;">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="(s) => emit('paginationChange', { page: currentPage, pageSize: s })"
        @current-change="(p) => emit('paginationChange', { page: p, pageSize: pageSize })"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MoreFilled } from '@element-plus/icons-vue'
import type { Device } from '@/types'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatMac, formatVoltage, formatRelativeTime } from '@/utils/format'
import { DEVICE_TYPES, SCREEN_TYPES } from '@/utils/constants'

defineProps<{
  devices: Device[]
  loading: boolean
  total?: number
  selectedMacs?: string[]
}>()

const emit = defineEmits<{
  selectionChange: [macs: string[]]
  control: [payload: { action: string; device: Device }]
  rowClick: [device: Device]
  paginationChange: [params: { page: number; pageSize: number }]
}>()

const tableRef = ref()
const currentPage = ref(1)
const pageSize = ref(20)

function onSelectionChange(rows: Device[]) {
  emit('selectionChange', rows.map(r => r.mac))
}

function handleCommand(command: string, device: Device) {
  emit('control', { action: command, device })
}
</script>

<style lang="scss" scoped>
.device-table-wrap {
  background: var(--el-bg-color);
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);

  :deep(.el-table) {
    --el-table-border-color: var(--el-border-color-lighter);
  }

  :deep(.el-table th.el-table__cell) {
    background: var(--el-fill-color-extra-light);
    font-weight: 600;
    font-size: 13px;
    color: var(--el-text-color-primary);
  }
}

.action-group { display: flex; justify-content: center; align-items: center; gap: 2px; }

.mac-text { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 13px; letter-spacing: 0.3px; }

.time-text { font-size: 13px; color: var(--el-text-color-secondary); }

.low-battery { color: #ef4444; font-weight: 600; }
.weak-signal { color: #f59e0b; font-weight: 600; }

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 14px 20px;
}
</style>
