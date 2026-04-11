<template>
  <div class="device-selector">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          placeholder="搜索设备MAC/名称..."
          clearable
          :prefix-icon="Search"
          style="width: 200px;"
        />
        <span class="selected-count">
          已选择 <strong>{{ selectedMacs.length }}</strong> 台设备
        </span>
        <el-button 
          v-if="selectedMacs.length > 0"
          text 
          size="small" 
          type="primary"
          @click="handleAddMore"
          style="margin-left: 8px;"
        >
          <el-icon><Plus /></el-icon> 添加更多
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-button-group>
          <el-button 
            text 
            size="small" 
            @click="handleSelectAll" 
            :disabled="filteredDevices.length === 0"
          >
            {{ isAllSelected ? '取消全选' : '全选当前页' }}
          </el-button>
          <el-button 
            text 
            size="small" 
            type="primary"
            @click="handleSelectOnline"
            :disabled="!hasOnlineDevices"
          >
            选择所有在线设备
          </el-button>
          <el-button 
            text 
            size="small" 
            type="danger" 
            @click="handleClearAll" 
            :disabled="selectedMacs.length === 0"
          >
            清空选择
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 设备列表 (表格) -->
    <template v-else-if="filteredDevices.length > 0">
      <div class="device-list-wrap">
        <el-table
          ref="tableRef"
          :data="filteredDevices"
          :row-key="(row: any) => row.mac"
          highlight-current-row
          height="320"
          @selection-change="handleSelectionChange"
          class="device-table"
        >
          <el-table-column type="selection" width="42" align="center" />
          <el-table-column label="设备名称" prop="name" min-width="90" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="MAC地址" prop="mac" min-width="155">
            <template #default="{ row }">
              <code class="mac-code">{{ row.mac }}</code>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_online ? 'success' : 'info'" size="small" effect="dark">
                {{ row.is_online ? '在线' : '离线' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 底部已选摘要 -->
      <div v-if="selectedMacs.length > 0" class="selected-summary">
        <div class="summary-header">
          <div class="summary-left">
            <el-button
              size="small"
              type="primary"
              plain
              @click="handleConfirmSelection"
              :disabled="selectedMacs.length === 0"
              class="confirm-btn"
            >
              <el-icon><Check /></el-icon> 确认选择
            </el-button>
            <span class="summary-title">已选 {{ selectedMacs.length }} 台</span>
          </div>
          <div class="summary-actions">
            <el-button 
              size="small" 
              type="danger" 
              plain
              @click="handleClearAll"
            >
              清空
            </el-button>
          </div>
        </div>
        
        <div class="summary-chips">
          <el-tag
            v-for="mac in selectedMacs"
            :key="mac"
            closable
            size="small"
            effect="plain"
            @close="removeMac(mac)"
            class="chip-item"
            :type="getDeviceStatus(mac) === 'online' ? 'success' : 'info'"
          >
            <el-icon v-if="getDeviceStatus(mac) === 'online'" size="12" style="margin-right: 4px;">
              <CircleCheck />
            </el-icon>
            {{ deviceNameMap[mac] || mac }}
          </el-tag>
        </div>
        
        <div class="summary-stats">
          <span class="stat-item">
            <span class="stat-label">在线:</span>
            <span class="stat-value online">{{ getOnlineCount() }}</span>
          </span>
          <span class="stat-item">
            <span class="stat-label">离线:</span>
            <span class="stat-value offline">{{ getOfflineCount() }}</span>
          </span>
        </div>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty :description="keyword ? '未找到匹配的设备' : '暂无可用设备'">
        <el-button v-if="keyword" text @click="keyword = ''">清除搜索</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Search, Plus, Check, CircleCheck } from '@element-plus/icons-vue'
import { ElTable, ElMessage } from 'element-plus'
import { useDeviceStore } from '@/stores/device'

// 防抖函数（优化频繁调用）
function debounce<T extends (...args: any[]) => any>(fn: T, delay = 100): T {
  let timer: NodeJS.Timeout | null = null
  return ((...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }) as T
}

const props = withDefaults(defineProps<{
  selectedMacs?: string[]
  preSelected?: string[]
}>(), {
  selectedMacs: () => [],
  preSelected: () => [],
})

const emit = defineEmits<{
  'update:selectedMacs': [value: string[]]
  confirm: [macs: string[]]
  'push-device': [device: any]
}>()

const deviceStore = useDeviceStore()
const tableRef = ref<InstanceType<typeof ElTable>>()
const keyword = ref('')
const loading = ref(false)

// 内部选中列表（双向绑定）
const internalSelection = computed({
  get: () => props.selectedMacs,
  set: (val) => emit('update:selectedMacs', val),
})

// 过滤后的设备列表（模糊查询：MAC / 名称）
const filteredDevices = computed(() => {
  const list = deviceStore.devices
  if (!keyword.value.trim()) return list
  const kw = keyword.value.trim().toLowerCase()
  // 支持模糊匹配：输入任意子串即可命中，多关键词空格分隔（AND）
  const keywords = kw.split(/\s+/).filter(Boolean)
  return list.filter((d: any) =>
    keywords.every(k => 
      d.mac?.toLowerCase().includes(k) ||
      d.name?.toLowerCase().includes(k)
    )
  )
})

// 在线设备列表
const onlineDevices = computed(() => {
  return deviceStore.devices.filter((d: any) => d.is_online)
})

const hasOnlineDevices = computed(() => onlineDevices.value.length > 0)

// 设备名称映射（用于底部标签）
const deviceNameMap = computed(() => {
  const map: Record<string, string> = {}
  for (const d of deviceStore.devices) {
    if (d.name && d.mac) map[d.mac] = d.name
  }
  return map
})

// 是否全部选中
const isAllSelected = computed(() => {
  return filteredDevices.value.length > 0 &&
    filteredDevices.value.every((d: any) => internalSelection.value.includes(d.mac))
})

function handleSelectionChange(rows: any[]) {
  emit('update:selectedMacs', rows.map((r: any) => r.mac))
}

/** 同步表格勾选状态到当前 selectedMacs（优化性能版） */
function syncTableSelection() {
  nextTick(() => {
    const table = tableRef.value
    if (!table) return
    
    const selectedSet = new Set(internalSelection.value)
    
    // 智能同步：只更新状态变化的行，避免全量 clearSelection
    for (const row of filteredDevices.value) {
      const shouldSelected = selectedSet.has(row.mac)
      const isSelected = table.getSelection()?.some(sel => sel.mac === row.mac) || false
      
      if (shouldSelected !== isSelected) {
        table.toggleRowSelection(row, shouldSelected)
      }
    }
  })
}

function handleSelectAll() {
  if (isAllSelected.value) {
    // 取消全选：保留不在当前过滤列表中的已选项
    const currentMacs = new Set(filteredDevices.value.map((d: any) => d.mac))
    const newSelection = internalSelection.value.filter(m => !currentMacs.has(m))
    emit('update:selectedMacs', newSelection)
    ElMessage.info('已取消选择当前页所有设备')
    // 批量更新后同步一次
    nextTick(() => {
      const table = tableRef.value
      if (table) {
        table.clearSelection()
        // 对于取消全选，直接清空更快
        for (const row of filteredDevices.value) {
          table.toggleRowSelection(row, false)
        }
      }
    })
  } else {
    // 全选：合并当前过滤结果
    const existing = new Set(internalSelection.value)
    const addCount = filteredDevices.value.filter(d => !existing.has(d.mac)).length
    const rowsToSelect = []
    
    for (const d of filteredDevices.value) {
      if (!existing.has(d.mac)) {
        existing.add(d.mac)
        rowsToSelect.push(d)
      }
    }
    
    emit('update:selectedMacs', Array.from(existing))
    ElMessage.success(`已添加 ${addCount} 台设备到选择列表`)
    
    // 批量选中：只选中新增的行，避免操作已选中的
    if (rowsToSelect.length > 0) {
      nextTick(() => {
        const table = tableRef.value
        if (table) {
          for (const row of rowsToSelect) {
            table.toggleRowSelection(row, true)
          }
        }
      })
    }
  }
}

function handleSelectOnline() {
  const existing = new Set(internalSelection.value)
  const onlineMacs = onlineDevices.value.map(d => d.mac)
  const newOnlineDevices = onlineMacs.filter(mac => !existing.has(mac))

  if (newOnlineDevices.length === 0) {
    ElMessage.info('所有在线设备都已选择')
    return
  }

  // 找出需要选中的在线设备行
  const rowsToSelect = []
  for (const d of deviceStore.devices) {
    if (d.is_online && !existing.has(d.mac)) {
      existing.add(d.mac)
      rowsToSelect.push(d)
    }
  }

  emit('update:selectedMacs', Array.from(existing))
  ElMessage.success(`已选择 ${newOnlineDevices.length} 台在线设备`)
  
  // 批量选中新增的在线设备
  if (rowsToSelect.length > 0) {
    nextTick(() => {
      const table = tableRef.value
      if (table) {
        for (const row of rowsToSelect) {
          table.toggleRowSelection(row, true)
        }
      }
    })
  }
}

function handleAddMore() {
  ElMessage.info('继续选择更多设备，当前已选择 ' + internalSelection.value.length + ' 台')
}

function handleClearAll() {
  emit('update:selectedMacs', [])
  ElMessage.info('已清空所有选择')
  // 直接清空表格选择，不需要逐行操作
  nextTick(() => {
    tableRef.value?.clearSelection()
  })
}

function removeMac(mac: string) {
  emit('update:selectedMacs', internalSelection.value.filter(m => m !== mac))
  ElMessage.info('已移除设备: ' + (deviceNameMap.value[mac] || mac))
}

function getDeviceStatus(mac: string): string {
  const device = deviceStore.devices.find((d: any) => d.mac === mac)
  return device?.is_online ? 'online' : 'offline'
}

function getOnlineCount(): number {
  return internalSelection.value.filter(mac => getDeviceStatus(mac) === 'online').length
}

function getOfflineCount(): number {
  return internalSelection.value.filter(mac => getDeviceStatus(mac) !== 'online').length
}

function handleConfirmSelection() {
  emit('confirm', internalSelection.value)
  ElMessage.success(`已确认选择 ${internalSelection.value.length} 台设备`)
}


onMounted(async () => {
  loading.value = true
  try {
    await deviceStore.fetchDevices()
  } finally {
    loading.value = false
  }
})

// 选中列表变化时同步表格勾选（处理外部修改：如底部chip删除）
const debouncedSyncSelection = debounce(syncTableSelection, 50)
watch(() => internalSelection.value, () => {
  debouncedSyncSelection()
}, { deep: false })
</script>

<style lang="scss" scoped>
.device-selector { padding: 4px; }

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  flex-wrap: wrap;
  gap: 10px;

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 14px;
  }
  .toolbar-right { display: flex; gap: 6px; }
}

.selected-count {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  strong { color: var(--el-color-primary); }
}

.loading-state { padding: 20px; }

.device-list-wrap {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;

  .device-table {
    :deep(.el-table__header th) {
      background-color: var(--el-fill-color-light);
      padding: 8px 0;
      font-size: 12.5px;
    }

    :deep(.el-table__body td) {
      padding: 7px 0;
      vertical-align: middle;
    }

    :deep(.el-table__row) {
      --el-table-row-hover-bg-color: var(--el-fill-color-light);
    }
  }
}

.mac-code {
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  font-size: 12px;
  color: var(--el-text-color-regular);
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.selected-summary {
  margin-top: 12px;
  padding: 10px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-extra-light);

  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;

    .summary-left {
      display: flex;
      align-items: center;
      gap: 10px;

      .confirm-btn {
        font-weight: 600;
      }
    }
    
    .summary-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
    
    .summary-actions {
      display: flex;
      gap: 6px;
    }
  }

  .summary-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
  }
  
  .chip-item { font-family: monospace; font-size: 11px; }

  .summary-stats {
    display: flex;
    gap: 16px;
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 13px;
      
      .stat-label {
        color: var(--el-text-color-secondary);
      }
      
      .stat-value {
        font-weight: 600;
        
        &.online { color: #22c55e; }
        &.offline { color: #ef4444; }
      }
    }
  }
}

.empty-state { padding: 40px 0; }

/* ═══ 移动端响应式 ═══ */
@media (max-width: 768px) {
  .device-selector { padding: 2px; }

  .toolbar {
    margin-bottom: 8px;
    gap: 6px;

    .toolbar-left {
      flex-wrap: wrap;
      gap: 6px;

      .el-input { width: 100% !important; }
      .selected-count {
        width: 100%;
        text-align: center;
        font-size: 12px;
      }
      /* 移动端隐藏"添加更多"按钮，节省空间 */
      .el-button[style*="margin-left"] { display: none; }
    }

    .toolbar-right {
      width: 100%;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 4px;

      .el-button-group {
        display: contents;
      }
      .el-button-group > .el-button {
        font-size: 11px;
        padding: 5px 3px !important;
        border-radius: 8px !important;
        white-space: nowrap;
      }
    }
  }

  .device-list-wrap {
    border-radius: 10px;

    :deep(.device-table) {
      font-size: 12px;

      .el-table__header th,
      .el-table__body td {
        padding: 5px 4px;
        white-space: nowrap;
      }

      .mac-code {
        font-size: 10.5px;
      }

      .el-tag { transform: scale(0.85); transform-origin: left center; }
    }
  }

  .selected-summary {
    padding: 8px 10px;

    .summary-header {
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;

      .summary-left {
        width: 100%;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }

      .summary-actions {
        justify-content: flex-end;
      }
    }

    .summary-chips {
      gap: 3px;
      .chip-item { font-size: 9.5px; padding: 0 4px; }
    }

    .summary-stats { gap: 10px; font-size: 12px; }
  }
}
</style>
