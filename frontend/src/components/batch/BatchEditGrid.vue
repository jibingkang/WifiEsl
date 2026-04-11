<template>
  <div class="batch-grid">
    <!-- 工具栏 -->
    <div class="grid-toolbar">
      <div class="toolbar-left">
        <span class="info">共 <b>{{ data.length }}</b> 条数据</span>
        <span v-if="changedCount > 0" class="changed-info">
          已修改 <b>{{ changedCount }}</b> 处
        </span>
      </div>
      <div class="toolbar-right">
        <el-button size="small" text :icon="CopyDocument" @click="copySelectedCells">
          复制选中单元格
        </el-button>
        <el-button size="small" text @click="fillColumn">列填充</el-button>
        <el-button size="small" text type="danger" @click="clearSelectedCells">清空选中</el-button>
        <el-divider direction="vertical" />
        <el-button size="small" type="primary" plain :disabled="changedCount === 0" @click="$emit('save')">
          保存更改
        </el-button>
      </div>
    </div>

    <!-- 可编辑表格 -->
    <el-table
      ref="tableRef"
      :data="filteredData"
      :loading="loading"
      border
      stripe
      height="500"
      highlight-current-row
      cell-class-name="editable-cell"
      @cell-dblclick="handleDblClick"
      @selection-change="(rows) => selectedRows = rows"
    >
      <el-table-column type="selection" width="46" align="center" fixed />

      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth ?? undefined"
        show-overflow-tooltip
        :fixed="col.fixed"
      >
        <template #default="{ row, $index }">
          <!-- 可编辑单元格 -->
          <template v-if="col.editable && editingCell === `${$index}-${col.prop}`">
            <component
              :is="getInputComponent(col.type)"
              v-model="row[col.prop]"
              size="small"
              autofocus
              :placeholder="'请输入'"
              @blur="editingCell = null; emitChange(row, col.prop, row[col.prop])"
              @keyup.enter="editingCell = null"
            >
              <template v-if="col.type === 'select'" #default>
                <el-option
                  v-for="opt in getSelectOptions(col.prop)"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </template>
            </component>
          </template>
          <!-- 只读显示 -->
          <template v-else>
            <span
              :class="{
                'changed-cell': row._changed && col.editable,
                'monospace': col.prop === 'mac',
                'editable-hint': col.editable,
              }"
            >{{ formatCellValue(row[col.prop], col) }}</span>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 底部提示 -->
    <div class="grid-footer">
      <span><kbd>双击</kbd> 编辑单元格 | <kbd>Tab</kbd> 切换下一列</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { CopyDocument } from '@element-plus/icons-vue'
import { formatMac } from '@/utils/format'
import { DEVICE_TYPES, SCREEN_TYPES } from '@/utils/constants'

interface ColumnDef {
  prop: string
  label: string
  width?: number
  minWidth?: number
  fixed?: boolean | string
  editable?: boolean
  type?: string
}

const props = defineProps<{
  columns: ColumnDef[]
  data: Array<Record<string, any>>
  loading: boolean
}>()

const emit = defineEmits<{
  cellChange: [payload: { row: Record<string, any>; column: string; value: any }]
  save: []
}>()

const tableRef = ref()
const editingCell = ref<string | null>(null)
const selectedRows = ref<any[]>([])

const filteredData = computed(() => props.data)

const changedCount = computed(() =>
  props.data.filter(d => d._changed).length
)

/** 双击进入编辑模式 */
function handleDblClick({ row, column }: any) {
  const colDef = props.columns.find(c => c.prop === column.property)
  if (!colDef?.editable) return
  editingCell.value = `${column.index}-${column.property}`
}

/** 发送单元格变更事件 */
function emitChange(row: Record<string, any>, column: string, value: any) {
  emit('cellChange', { row, column, value })
}

/** 获取输入组件 */
function getInputComponent(type?: string): string {
  switch (type) {
    case 'select': return 'ElSelect'
    case 'number': return 'ElInputNumber'
    default: return 'ElInput'
  }
}

/** 获取下拉选项 */
function getSelectOptions(prop: string): Array<{ label: string; value: string }> {
  if (prop === 'device_type') {
    return Object.entries(DEVICE_TYPES).map(([v, l]) => ({ label: l, value: v }))
  }
  if (prop === 'screen_type') {
    return Object.entries(SCREEN_TYPES).map(([v, l]) => ({ label: l, value: v }))
  }
  return []
}

/** 格式化显示值 */
function formatCellValue(val: any, _col: ColumnDef): string {
  if (val == null || val === '') return '--'
  return String(val)
}

function copySelectedCells() {
  // TODO: 复制到剪贴板
}
function fillColumn() {
  // TODO: 弹出对话框选择填充值和目标列
}
function clearSelectedCells() {
  selectedRows.value.forEach(row => {
    for (const key of Object.keys(row)) {
      if (key !== '_changed' && key !== 'id' && key !== 'mac') row[key] = ''
    }
    row._changed = true
  })
}
</script>

<style lang="scss" scoped>
.batch-grid {
  background: var(--el-bg-color);
  border-radius: 12px;
}

.grid-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);

  .toolbar-left { display: flex; gap: 16px; align-items: center; }
  .info { font-size: 13px; color: var(--el-text-color-secondary); b { color: var(--el-text-color-primary); } }
  .changed-info { font-size: 13px; color: #d97706; b { font-weight: 700; } }

  .toolbar-right { display: flex; align-items: center; }
}

.grid-footer {
  padding: 8px 16px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  text-align: center;
  kbd {
    background: var(--el-fill-color-light);
    padding: 1px 5px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 11.5px;
  }
}

.monospace { font-family: monospace; font-size: 13px; }
.changed-cell { color: #d97706; font-weight: 600; }
.editable-hint { cursor: pointer; &:hover { color: #6366f1; text-decoration: underline; } }

:deep(.editable-cell) { cursor: default; }
</style>
