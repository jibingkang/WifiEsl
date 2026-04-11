<template>
  <div class="batch-edit">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">批量编辑</h2>
        <p class="page-desc">Excel式表格批量修改设备数据，支持导入导出</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Upload" @click="importVisible = true">导入数据</el-button>
        <el-button type="primary" :icon="Download" @click="handleExport">导出数据</el-button>
      </div>
    </div>

    <!-- Tab导航 -->
    <el-tabs v-model="activeTab" type="border-card" class="batch-tabs">
      <!-- 批量设备信息编辑 -->
      <el-tab-pane label="设备信息" name="devices">
        <BatchEditGrid
          :columns="deviceColumns"
          :data="tableData"
          :loading="loading"
          @cell-change="handleCellChange"
        />
      </el-tab-pane>

      <!-- 批量模板字段编辑 -->
      <el-tab-pane label="模板内容" name="templates">
        <div class="tab-placeholder">
          <el-empty description="选择模板后可在此处批量编辑模板字段">
            <el-select placeholder="请先选择一个模板" style="width: 260px;">
              <el-option v-for="t in templates" :key="t.tid" :label="t.tname" :value="t.tid" />
            </el-select>
          </el-empty>
        </div>
      </el-tab-pane>

      <!-- 操作历史 -->
      <el-tab-pane label="执行记录" name="history">
        <TaskHistory />
      </el-tab-pane>
    </el-tabs>

    <!-- 导入对话框 -->
    <ImportDialog
      v-model:visible="importVisible"
      @imported="handleImported"
    />

    <!-- 导出对话框 -->
    <ExportDialog
      v-model:visible="exportVisible"
      @confirm="doExport"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import { useDeviceStore } from '@/stores/device'
import BatchEditGrid from '@/components/batch/BatchEditGrid.vue'
import ImportDialog from '@/components/batch/ImportDialog.vue'
import ExportDialog from '@/components/batch/ExportDialog.vue'
import TaskHistory from '@/components/batch/TaskHistory.vue'

const deviceStore = useDeviceStore()
const loading = ref(false)
const activeTab = ref('devices')
const importVisible = ref(false)
const exportVisible = ref(false)

// 设备列定义 (可编辑)
const deviceColumns = [
  { prop: 'mac', label: 'MAC地址', width: 170, editable: false },
  { prop: 'name', label: '名称', width: 140, editable: true },
  { prop: 'ip', label: 'IP地址', width: 140, editable: true },
  { prop: 'device_type', label: '设备类型', width: 120, editable: true, type: 'select' },
  { prop: 'screen_type', label: '屏幕类型', width: 110, editable: true, type: 'select' },
]

// 表格数据
const tableData = ref<Array<Record<string, any>>>([])

// 模板列表(模拟)
const templates = ref([
  { tid: 'tpl_001', tname: '会议模板' },
  { tid: 'tpl_002', tname: '商品价签' },
])

/** 加载数据 */
async function loadData() {
  loading.value = true
  try {
    await deviceStore.fetchDevices()
    tableData.value = (deviceStore.devices ?? []).map(d => ({
      id: d.id,
      mac: d.mac,
      name: d.name || '',
      ip: d.ip || '',
      device_type: d.device_type || '',
      screen_type: d.screen_type || '',
      _changed: false, // 内部标记是否被修改过
    }))
  } finally {
    loading.value = false
  }
}

/** 单元格变化 */
function handleCellChange({ row, column, value }: { row: Record<string, any>; column: string; value: any }) {
  row._changed = true
  // TODO: 可做防抖保存或标记为待提交
}

/** 导出 */
function handleExport() {
  if (tableData.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  exportVisible.value = true
}

/** 确认导出 */
function doExport(format: string) {
  // TODO: 调用导出API
  ElMessage.success(`正在导出 ${format} 格式...`)
  exportVisible.value = false
}

/** 导入完成 */
function handleImported(count: number) {
  ElMessage.success(`成功导入 ${count} 条记录`)
  loadData()
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.batch-edit { padding: 0 4px; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;

  .page-title { font-size: 22px; font-weight: 700; color: var(--el-text-color-primary); margin: 0 0 4px; }
  .page-desc { font-size: 14px; color: var(--el-text-color-secondary); margin: 0; }
}

.batch-tabs {
  border-radius: 16px !important;
  overflow: hidden;
}

.tab-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 360px;
}
</style>
