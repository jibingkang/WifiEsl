<template>
  <div class="device-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">设备管理</h2>
        <p class="page-desc">管理和控制所有WIFI标签设备</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="handleAdd">添加设备</el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <DeviceFilterBar v-model:filters="filters" @search="handleSearch" @reset="handleReset" />

    <!-- 操作栏 (选中后显示) -->
    <transition name="slide-fade">
      <div v-if="selectedMacs.length > 0" class="batch-bar">
        <span class="selected-count">已选 {{ selectedMacs.length }} 台设备</span>
        <div class="batch-actions">
          <el-button size="small" :icon="Document" type="primary" plain @click="handleBatchTemplate">
            批量数据更新
          </el-button>
          <el-button size="small" :icon="Delete" type="danger" plain @click="handleBatchDelete">
            批量删除
          </el-button>
          <el-button size="small" text @click="clearSelection">取消选择</el-button>
        </div>
      </div>
    </transition>

    <!-- 桌面端: 表格视图 -->
    <DeviceTable
      v-show="!isMobile"
      :devices="deviceStore.devices ?? []"
      :loading="deviceStore.loading"
      :total="deviceStore.total ?? 0"
      v-model:selected-macs="selectedMacs"
      @selection-change="onSelectionChange"
      @control="handleControl"
      @row-click="handleRowClick"
      @pagination-change="onPaginationChange"
    />

    <!-- 移动端: 卡片视图 -->
    <div v-show="isMobile" class="device-cards">
      <TransitionGroup name="card-list">
        <DeviceCard
          v-for="device in (deviceStore.devices ?? [])"
          :key="device.id"
          :device="device"
          @control="handleControl"
        />
      </TransitionGroup>

      <!-- 移动端分页 -->
      <div v-if="deviceStore.total > 0" class="mobile-pagination">
        <el-pagination
          size="small"
          layout="prev, pager, next"
          :total="deviceStore.total"
          :current-page="deviceStore.currentPage"
          :page-size="deviceStore.pageSize"
          @current-change="(p) => deviceStore.currentPage = p"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!deviceStore.loading && (deviceStore.devices ?? []).length === 0" class="empty-state">
      <el-empty description="暂无设备数据">
        <el-button type="primary" @click="handleAdd">添加第一台设备</el-button>
      </el-empty>
    </div>

    <!-- 控制面板抽屉 -->
    <DeviceControlPanel
      v-model:visible="controlPanelVisible"
      :device="controlTargetDevice"
    />

    <!-- 设备详情抽屉 -->
    <DeviceDetailDrawer
      v-model:visible="detailDrawerVisible"
      :device="detailDevice"
    />

    <!-- 添加/编辑对话框 -->
    <DeviceEditDialog
      v-model:visible="editDialogVisible"
      :device-id="editDeviceId"
      @saved="refreshDevices"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, Delete } from '@element-plus/icons-vue'
import { useDeviceStore } from '@/stores/device'
import { deviceApi } from '@/api/device'
import { useResponsive } from '@/composables/useResponsive'
import DeviceFilterBar from '@/components/device/DeviceFilterBar.vue'
import DeviceTable from '@/components/device/DeviceTable.vue'
import DeviceCard from '@/components/device/DeviceCard.vue'
import DeviceControlPanel from '@/components/device/DeviceControlPanel.vue'
import DeviceDetailDrawer from '@/components/device/DeviceDetailDrawer.vue'
import DeviceEditDialog from '@/components/device/DeviceEditDialog.vue'

const router = useRouter()
const deviceStore = useDeviceStore()
const { isMobile } = useResponsive()

// 筛选条件
let filters = reactive({
  keyword: '',
  status: '' as string,
  deviceType: '',
  screenType: '',
})

// 选中
const selectedMacs = ref<string[]>([])

// 抽屉/弹窗状态
const controlPanelVisible = ref(false)
const controlTargetDevice = ref<any>(null)
const detailDrawerVisible = ref(false)
const detailDevice = ref<any>(null)
const editDialogVisible = ref(false)
const editDeviceId = ref<string | null>(null)

/** 加载设备 */
function refreshDevices() {
  deviceStore.fetchDevices(filters as any)
}

/** 搜索 */
function handleSearch() {
  deviceStore.currentPage = 1
  refreshDevices()
}

/** 重置筛选 */
function handleReset() {
  Object.assign(filters, { keyword: '', status: '', deviceType: '', screenType: '' })
  deviceStore.currentPage = 1
  refreshDevices()
}

/** 选择变化 */
function onSelectionChange(macs: string[]) {
  selectedMacs.value = macs
}

/** 分页变化 */
function onPaginationChange({ page, pageSize }: { page: number; pageSize: number }) {
  deviceStore.currentPage = page
  deviceStore.pageSize = pageSize
  refreshDevices()
}

/** 行点击 */
function handleRowClick(device: any) {
  detailDevice.value = device
  detailDrawerVisible.value = true
}

/** 控制操作 */
async function handleControl({ action, device }: { action: string; device: any }) {
  // 删除：二次确认
  if (action === 'delete') {
    await ElMessageBox.confirm(
      `确定要删除设备「${device.name || device.mac}」吗？删除后无法恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
    try {
      await deviceApi.deleteDevice(device.id)
      ElMessage.success('设备已删除')
      refreshDevices()
    } catch (e: any) {
      ElMessage.error(e.message || '删除失败')
    }
    return
  }

  // 单设备推送：跳转到模板更新页面
  if (action === 'push') {
    router.push({
      path: '/template',
      query: { macs: device.mac },
    })
    ElMessage.info(`正在为 ${device.name || device.mac} 准备推送...`)
    return
  }

  // 编辑/详情：打开设备详情抽屉
  if (action === 'edit') {
    detailDevice.value = device
    detailDrawerVisible.value = true
    return
  }

  // 其他操作（控制面板）：打开控制面板
  controlTargetDevice.value = device
  controlPanelVisible.value = true
}

/** 添加设备 */
function handleAdd() {
  editDeviceId.value = null
  editDialogVisible.value = true
}

/** 批量数据更新 */
function handleBatchTemplate() {
  router.push({
    path: '/template',
    query: { macs: selectedMacs.value.join(',') },
  })
}

/** 批量删除 */
async function handleBatchDelete() {
  await ElMessageBox.confirm(
    `确定要删除选中的 ${selectedMacs.value.length} 台设备吗？此操作不可恢复！`,
    '批量删除确认',
    { type: 'warning', confirmButtonText: '确定删除全部', cancelButtonText: '取消' }
  )
  let successCount = 0
  for (const mac of selectedMacs.value) {
    const d = deviceStore.devices.find((d: any) => d.mac === mac)
    if (d?.id) {
      try { await deviceApi.deleteDevice(d.id); successCount++ } catch (e: any) { console.error(`删除 ${mac} 失败`, e) }
    }
  }
  if (successCount > 0) ElMessage.success(`成功删除 ${successCount} 台设备`)
  selectedMacs.value = []
  refreshDevices()
}

function clearSelection() {
  selectedMacs.value = []
}

onMounted(() => {
  refreshDevices()
})
</script>

<style lang="scss" scoped>
.device-list { padding: 0 4px; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;

  .page-title { font-size: 22px; font-weight: 700; color: var(--el-text-color-primary); margin: 0 0 4px; }
  .page-desc { font-size: 14px; color: var(--el-text-color-secondary); margin: 0; }
}

.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  margin-bottom: 12px;
  border-radius: 11px;
  background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(139,92,246,0.06));
  border: 1px solid rgba(99,102,241,0.15);

  .selected-count { font-size: 13px; font-weight: 600; color: #6366f1; }
  .batch-actions { display: flex; gap: 8px; }
}

.device-cards { padding: 4px 0; }

.mobile-pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.slide-fade-enter-active { transition: all 0.25s ease; }
.slide-fade-leave-active { transition: all 0.2s ease; }
.slide-fade-enter-from { opacity: 0; transform: translateY(-8px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-8px); }

.card-list-enter-active,
.card-list-leave-active { transition: all 0.3s ease; }
.card-list-enter-from { opacity: 0; transform: translateY(12px); }
.card-list-leave-to { opacity: 0; transform: translateX(-20px); }
</style>
