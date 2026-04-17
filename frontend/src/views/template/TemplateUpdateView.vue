<template>
  <div class="simple-workspace">
    <!-- ═══ 顶栏工具条 ═══ -->
    <header class="top-toolbar">
      <div class="toolbar-left">
        <!-- 任务选择器 -->
        <div class="task-switcher">
          <div class="selector-label">
            <ListTodo :size="16" />
            <span class="label-text">选择任务：</span>
            <el-tooltip
              content="选择一个已创建的更新任务，或创建新任务。任务用于管理批量设备推送"
              placement="bottom"
              effect="light"
            >
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <el-select
            v-model="currentTaskId"
            size="default"
            placeholder="请选择一个任务或创建新任务"
            clearable
            @change="handleTaskChange"
          >
            <el-option
              v-for="t in taskList"
              :key="t.id"
              :label="t.name || `任务${t.id}`"
              :value="t.id"
            >
              <span style="display:flex;justify-content:space-between;align-items:center">
                <span>{{ t.name || `任务${t.id}` }}</span>
                <el-tag :type="taskStatusTagType(t.status)" size="small" style="margin-left:8px">{{ taskStatusLabel(t.status) }}</el-tag>
              </span>
            </el-option>
          </el-select>
          <el-button size="default" @click="showCreateTaskDialog = true">+ 新建</el-button>
        </div>

        <!-- 模板切换 -->
        <div v-if="availableTemplates.length > 0" class="tpl-switcher" style="margin-left: 12px; padding-left: 12px; border-left: 1px solid #e2e8f0;">
          <div class="selector-label">
            <LayoutTemplate :size="16" />
            <span class="label-text">选择模板：</span>
            <el-tooltip
              content="选择要推送到设备的模板，模板定义了设备屏幕显示的内容格式"
              placement="bottom"
              effect="light"
            >
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <el-select
            v-model="selectedTid"
            size="default"
            placeholder="请选择要使用的模板"
            @change="handleTemplateChange"
          >
            <el-option
              v-for="tpl in availableTemplates"
              :key="tpl.tid"
              :label="tpl.tname"
              :value="tpl.tid"
            />
          </el-select>
        </div>
      </div>

      <div class="toolbar-right">
        <el-button type="primary" @click="showDevicePicker = true" :disabled="!currentTaskId && !selectedTid">
          <Plus :size="14" /> 添加设备
        </el-button>
        <el-button text type="primary" @click="$router.push('/template/history')">
          <Clock :size="15" /> 历史记录
        </el-button>
      </div>
    </header>

    <!-- 无模板空态 -->
    <div v-if="availableTemplates.length === 0" class="empty-state-card">
      <div class="empty-icon-wrap">
        <LayoutTemplate :size="48" />
      </div>
      <h2>暂无可用模板</h2>
      <p>请先在模板管理中创建一个模板，再回来更新设备数据</p>
      <el-button type="primary" size="large" @click="$router.push('/template/manage')">
        <Files :size="16" /> 去创建模板
      </el-button>
    </div>

    <!-- 主工作区（有任务且有模板时） -->
    <template v-if="(currentTaskId || selectedTemplate) && !!selectedTemplate">
      <!-- 默认值编辑区 - 折叠面板 -->
      <el-collapse v-model="activeCollapse" class="generic-data-collapse">
        <el-collapse-item name="genericData">
          <template #title>
            <div class="collapse-title-bar">
              <div class="collapse-title-left">
                <Pencil :size="16" />
                <span class="collapse-title-text">通用数据设置</span>
                <span class="field-summary">{{ fieldSummaryText }}</span>
              </div>
              <span class="card-hint collapse-hint">修改后所有设备自动继承</span>
            </div>
          </template>

          <div class="collapse-content-wrap">
          <WorkspaceForm
            :key="selectedTemplate?.tid || 'no-template'"
            :template-info="selectedTemplate!"
            :default-data="defaultData"
            @update:default-data="defaultData = $event"
          />
            <div class="form-footer-tip">
              <Info :size="13" />
              <span>下方表格可为每台设备单独修改不同数据</span>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 设备数据表格（含checkbox + 状态列） -->
      <section class="card device-table-card">
        <div class="card-header-row">
          <h3><Smartphone :size="16" /> 设备列表</h3>
          <div class="header-right-badges">
            <span class="device-count-badge">共 {{ selectedMacs.length }} 台</span>
            <span class="badge-sent">正在更新 {{ taskProgress.sent }}</span>
            <span class="badge-success">更新成功 {{ taskProgress.success }}</span>
            <span class="badge-failed">更新失败 {{ taskProgress.failed }}</span>
            <el-divider direction="vertical" />
            <el-button v-if="selectedMacs.length > 0" type="primary" text size="small" @click="exportToExcel">
              <Download :size="14" /> 导出Excel
            </el-button>
            <el-button type="primary" text size="small" @click="showImportDialog = true" :disabled="!selectedTemplate">
              <Upload :size="14" /> 导入Excel
            </el-button>
          </div>
        </div>

        <!-- 操作行：已选数量 + 推送按钮 -->
        <div v-if="selectedMacs.length > 0" class="table-action-row">
          <span class="check-info">已选 {{ checkedCount }} / {{ selectedMacs.length }} 台设备</span>
          <el-button
            type="primary"
            size="large"
            :disabled="!canPush"
            :loading="executing"
            class="push-btn"
            @click="executePush"
          >
            <Send :size="16" /> 推送到 {{ checkedCount }} 台设备
          </el-button>
        </div>

        <!-- 设备筛选工具栏 -->
        <div v-if="selectedMacs.length > 0" class="device-filter-toolbar">
          <el-input
            v-model="filterKeyword"
            placeholder="筛选设备（MAC/名称/字段值）..."
            clearable
            style="width: 320px;"
            size="default"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <span class="filter-result-info">
            {{ filterKeyword ? `已筛选出 ${filteredDeviceTableData.length} 台设备` : `共 ${selectedMacs.length} 台设备` }}
          </span>
        </div>

        <DeviceDataTable
          :key="tableRefreshKey"
          v-model:checked-macs="checkedMacs"
          v-model:selected-rows="selectedRowIds"
          :template-info="selectedTemplate!"
          :devices="filteredDeviceTableData"
          :default-data="defaultData"
          :custom-overrides="customOverrides"
          @update:custom-overrides="customOverrides = $event"
          @remove-device="removeMac"
          @push-device="handlePushTableDevice"
          @push-row="handlePushRow"
          @remove-binding="handleRemoveTableDevice"
          @data-changed="handleDataChanged"
        />

        <!-- 无设备提示 -->
        <div v-if="selectedMacs.length === 0" class="empty-devices">
          <Smartphone :size="28" />
          <p>尚未添加设备</p>
          <el-button type="primary" text @click="showDevicePicker = true">
            点击添加设备 →
          </el-button>
        </div>
      </section>
    </template>

    <!-- 设备选择弹窗 -->
    <el-dialog
      v-model="showDevicePicker"
      title="选择设备"
      :width="isMobile ? '100%' : '520px'"
      class="device-picker-dialog"
      destroy-on-close
      append-to-body
      :fullscreen="isMobile"
    >
      <DeviceSelectorDialog
        v-if="showDevicePicker"
        :pre-selected="[...selectedMacs]"
        @confirm="handleDeviceConfirm"
        @push-device="handlePushSingleDevice"
      />
    </el-dialog>

    <!-- 新建任务弹窗 -->
    <el-dialog
      v-model="showCreateTaskDialog"
      title="新建更新任务"
      width="480px"
      destroy-on-close
      append-to-body
    >
      <el-form label-position="top">
        <el-form-item label="任务名称" required>
          <el-input v-model="newTaskName" placeholder="如：A区商品更新、价格批量修改" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="选择模板" required>
          <el-select v-model="newTaskTid" placeholder="请选择模板" style="width:100%" size="large">
            <el-option
              v-for="tpl in availableTemplates"
              :key="tpl.tid"
              :label="`${tpl.tname} (${tpl.tid})`"
              :value="tpl.tid"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateTaskDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!newTaskTid" @click="createNewTask" :loading="creatingTask">
          创建并开始
        </el-button>
      </template>
    </el-dialog>

    <!-- Excel导入弹窗 -->
    <el-dialog
      v-model="showImportDialog"
      title="导入设备列表"
      width="520px"
      destroy-on-close
      append-to-body
    >
      <div class="import-dialog-content">
        <el-alert
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          <template #title>
            <div style="line-height: 1.6;">
              <p>1. 支持导入包含MAC地址和模板字段数据的Excel文件</p>
              <p>2. 第一行为表头，必须包含"MAC地址"列</p>
              <p>3. 已存在的设备将更新自定义数据，新设备将添加到任务</p>
            </div>
          </template>
        </el-alert>
        
        <div class="template-download-row" style="margin-bottom: 16px;">
          <el-button type="primary" text @click="downloadImportTemplate">
            <Download :size="14" style="margin-right: 4px;" /> 下载导入模板
          </el-button>
        </div>
        
        <el-upload
          v-model:file-list="importFileList"
          drag
          accept=".xlsx,.xls"
          :auto-upload="false"
          :on-change="handleImport"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><Upload /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              请上传 .xlsx 或 .xls 格式的Excel文件
            </div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="showImportDialog = false; importFileList = []">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElNotification, ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import {
  Clock, Files, LayoutTemplate, Plus, Pencil, Smartphone,
  Send, Info, ListTodo, Download, Upload,
} from 'lucide-vue-next'
import { Search } from '@element-plus/icons-vue'
import { useTemplate } from '@/composables/useTemplate'
import { useDeviceStore } from '@/stores/device'
import { deviceApi } from '@/api/device'
import { taskApi, type TaskSummary, type TaskDetail } from '@/api/task'
import { onWsMessage, offWsMessage } from '@/composables/useBackendWs'
import type { TemplateInfo } from '@/types'

import WorkspaceForm from './WorkspaceForm.vue'
import DeviceDataTable from './DeviceDataTable.vue'
import DeviceSelectorDialog from '@/components/template/DeviceSelectorDialog.vue'

const route = useRoute()
const templateStore = useTemplate()
const deviceStore = useDeviceStore()

// ════════════ 任务系统（新增） ════════════
const currentTaskId = ref<number | null>(null)
const taskList = ref<TaskSummary[]>([])
const taskDetail = ref<TaskDetail | null>(null)
const showCreateTaskDialog = ref(false)
const newTaskName = ref('')
const newTaskTid = ref('')
const creatingTask = ref(false)

// ════════════ Excel导入导出 ════════════
const showImportDialog = ref(false)
const importFileList = ref<any[]>([])
const importing = ref(false)
const tableRefreshKey = ref(0)  // 用于强制刷新表格

// ── 模板 ──
const selectedTid = ref<string>('')
const selectedTemplate = ref<TemplateInfo | null>(null)
const availableTemplates = computed(() => templateStore.templates.value)

// ── 设备（从任务DB派生） ──
const selectedMacs = computed(() =>
  (taskDetail.value?.devices ?? []).map((d: any) => d.mac)
)
const checkedMacs = ref<string[]>([])
const selectedRowIds = ref<Record<string, number>>({}) // mac -> row_id，记录每个设备选中的行
const showDevicePicker = ref(false)
const isMobile = ref(window.innerWidth <= 768)
const filterKeyword = ref('')  // 设备筛选关键词（MAC/名称/字段值）

// 响应式监听屏幕尺寸
window.addEventListener('resize', () => {
  isMobile.value = window.innerWidth <= 768
})

// ── 表单数据 ──
const defaultData = ref<Record<string, any>>({})
const customOverrides = ref<Record<string, Record<string, any>>>({})

// ── 模板数据缓存 (为每个模板单独存储数据) ──
const templateDataCache = ref<Record<string, {
  defaultData: Record<string, any>,
  customOverrides: Record<string, Record<string, any>>,
  selectedRowIds: Record<string, number>
}>>({})

// ── 折叠面板 ──
const activeCollapse = ref<string[]>([])

// ── 推送状态 ──
const executing = ref(false)

// ── 轮询：推送后定期拉取任务进度 ──
let pollTimer: ReturnType<typeof setInterval> | null = null

/** 启动轮询：每3秒拉一次，直到全部设备有结果（无sent） */
function startProgressPolling() {
  stopProgressPolling()
  pollTimer = setInterval(async () => {
    if (!currentTaskId.value) return stopProgressPolling()
    await _refreshTaskFromServer()

    // 全部完成则停止
    if (taskDetail.value?.status === 'completed') {
      stopProgressPolling()
    }
  }, 3000)
}

function stopProgressPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

// ── 草稿（保留兼容） ──
const DRAFT_KEY = 'wifi_esl_update_draft_v2'
const LAST_TASK_KEY = 'wifi_esl_last_task_id'

// ── URL 预选 ──
const preSelectedMacs = computed(() => {
  const p = route.query.macs as string
  return p ? p.split(',').filter(m => m.length > 0) : []
})

// ── 计算属性 ──
const canPush = computed(() =>
  (currentTaskId.value || selectedTemplate.value) &&
  checkedCount.value > 0 &&
  !executing.value
  // 去掉了 status !== 'completed'，允许重新推送
)

const checkedCount = computed(() => checkedMacs.value.length)

const fieldSummaryText = computed(() => {
  const fields = selectedTemplate.value?.fields ?? []
  const total = fields.length
  if (total === 0) return '暂无字段'
  const filled = fields.filter(f => {
    const val = defaultData.value[f.key]
    return val !== undefined && val !== null && val !== ''
  }).length
  return `已填写 ${filled}/${total} 个字段`
})

/** 根据关键词筛选设备 */
const filteredDeviceTableData = computed(() => {
  const devices = selectedMacs.value.map(mac => {
    // 从任务设备列表获取 update_status 和 子表数据
    const taskDev = taskDetail.value?.devices.find((d: any) => d.mac === mac)
    // 从设备列表获取电量信息
    const deviceInfo = deviceStore.devices.find((d: any) => d.mac === mac)
    return {
      id: taskDev?.id,
      taskId: currentTaskId.value ?? undefined,
      mac,
      name: getDeviceName(mac),
      status: getDeviceStatus(mac),
      hasCustom: !!customOverrides.value[mac],
      updateStatus: taskDev?.update_status || 'pending',
      errorMsg: taskDev?.error_msg || '',
      sentAt: taskDev?.sent_at || '',
      finishedAt: taskDev?.finished_at || '',
      voltage: deviceInfo?.voltage,
      rowCount: taskDev?.rows?.length || 0,
      rows: taskDev?.rows || [],
      // 为筛选准备字段值
      fieldValues: Object.keys(customOverrides.value[mac] || {}).reduce((acc, key) => {
        acc[key] = customOverrides.value[mac][key] || defaultData.value[key] || ''
        return acc
      }, {} as Record<string, any>),
    }
  })
  
  // 如果没有筛选关键词，返回所有设备
  if (!filterKeyword.value.trim()) {
    return devices
  }
  
  const kw = filterKeyword.value.trim().toLowerCase()
  // 支持模糊查询：MAC、设备名、字段值
  return devices.filter(dev => {
    // 1. 检查 MAC 地址
    if (dev.mac.toLowerCase().includes(kw)) return true
    
    // 2. 检查设备名称
    if (dev.name.toLowerCase().includes(kw)) return true
    
    // 3. 检查自定义字段值
    const fieldValues = Object.values(dev.fieldValues || {})
    for (const val of fieldValues) {
      if (String(val).toLowerCase().includes(kw)) return true
    }
    
    return false
  })
})

/** 任务进度统计 */
const taskProgress = computed(() => {
  if (!taskDetail.value?.progress) return { pending: 0, sent: 0, success: 0, failed: 0 }
  return taskDetail.value.progress
})

function getDeviceName(mac: string): string {
  const d = deviceStore.devices.find((d: any) => d.mac === mac)
  return d?.name || mac
}

function getDeviceStatus(mac: string): string {
  const d = deviceStore.devices.find((d: any) => d.mac === mac)
  return d?.is_online ? 'online' : 'offline'
}

function removeMac(mac: string) {
  checkedMacs.value = checkedMacs.value.filter(m => m !== mac)
}

// ════════════ 任务操作（新增）════════════

/** 任务级状态 → 标签类型（用于任务列表下拉） */
function taskStatusTagType(status: string): 'info' | 'warning' | 'success' | 'danger' {
  switch (status) {
    case 'draft': return 'info'
    case 'pending': return 'info'
    case 'sent': return 'warning'
    case 'completed': return 'success'
    case 'cancelled': return 'danger'
    default: return 'info'
  }
}
/** 任务级状态 → 中文标签 */
function taskStatusLabel(s: string): string {
  const map: Record<string, string> = { draft: '待执行', pending: '待推送', sent: '执行中', completed: '已完成', cancelled: '已取消' }
  return map[s] || s
}

/** 加载任务列表 */
async function fetchTaskList() {
  try {
    const res: any = await taskApi.getTaskList({ page: 1, pageSize: 100 })
    taskList.value = res?.items || []
  } catch (e) {
    console.warn('加载任务列表失败:', e)
  }
}

/** 加载单个任务详情并恢复工作区 */
async function loadTaskDetail(taskId: number) {
  try {
    const res: any = await taskApi.getTaskDetail(taskId)
    // 响应拦截器已解包，res 直接就是 data
    const detail: TaskDetail = res
    taskDetail.value = detail

    // 恢复模板
    selectedTid.value = detail.tid
    const tpl = availableTemplates.value.find(t => t.tid === detail.tid)
    if (tpl) {
      selectedTemplate.value = tpl
    }

    // 恢复默认数据
    try {
      const dd = (detail as any).default_data
      if (dd && typeof dd === 'string') {
        defaultData.value = JSON.parse(dd)
      } else if (dd && typeof dd === 'object') {
        defaultData.value = dd
      }
    } catch (e) {
      console.warn('恢复默认数据失败:', e)
      defaultData.value = {}
    }

    // 恢复自定义数据覆盖
    const devices = detail.devices || []
    const overrides: Record<string, any> = {}
    for (const d of devices) {
      try {
        const cd = d.custom_data
        if (cd && typeof cd === 'string') {
          overrides[d.mac] = JSON.parse(cd)
        } else if (cd && typeof cd === 'object') {
          overrides[d.mac] = cd
        }
      } catch (e) {
        console.warn(`恢复设备 ${d.mac} 自定义数据失败:`, e)
      }
    }
    customOverrides.value = overrides

    // 初始化选中行：优先从 localStorage 草稿恢复，再降级到模板缓存，最后默认第1行
    _initSelectedRowIds(devices, taskId)

    // ⭐ 重要：将加载的数据保存到模板缓存（含行选择）
    if (selectedTemplate.value?.tid) {
      _saveTemplateCache()
      console.log(`任务加载: 保存模板 ${selectedTemplate.value.tid} 的数据到缓存`)
    }

    // ⭐ 重要：清空勾选状态，不要默认全选
    checkedMacs.value = []
    // 清空筛选关键词
    filterKeyword.value = ''
  } catch (e: any) {
    console.error('加载任务详情失败:', e)
    ElMessage.error('加载任务详情失败')
  }
}


/** 仅刷新任务进度（不覆盖自定义数据/表单数据），供轮询和WS回调使用 */
async function _refreshTaskFromServer() {
  if (!currentTaskId.value || !taskDetail.value) return
  try {
    const res: any = await taskApi.getTaskDetail(currentTaskId.value)
    // 只更新设备状态相关字段，保留本地表单状态
    if (taskDetail.value && res?.devices) {
      taskDetail.value.status = res.status
      taskDetail.value.progress = res.progress
      for (const dev of res.devices) {
        const local = (taskDetail.value.devices as any[]).find((d: any) => d.mac === dev.mac)
        if (local) {
          local.update_status = dev.update_status
          local.error_msg = dev.error_msg || ''
          local.sent_at = dev.sent_at || ''
          local.finished_at = dev.finished_at || ''
        }
      }
    }
  } catch { /* 静默失败 */ }
}

/** 切换任务 */
async function handleTaskChange(taskId: number | undefined | null) {
  if (!taskId) {
    currentTaskId.value = null
    taskDetail.value = null
    selectedTid.value = ''
    selectedTemplate.value = null
    selectedMacs // 触发计算属性清空
    return
  }

  currentTaskId.value = taskId
  await loadTaskDetail(taskId)
}

/** 新建任务 */
async function createNewTask() {
  if (!newTaskTid.value) {
    ElMessage.warning('请选择模板')
    return
  }
  creatingTask.value = true
  try {
    const res: any = await taskApi.createTask({
      name: newTaskName.value.trim() || `更新任务`,
      tid: newTaskTid.value,
    })
    // 响应拦截器已解包，res 直接就是 data 内容
    const detail = res
    if (!detail?.id) {
      console.error('创建任务返回异常:', res)
      throw new Error('服务器返回数据格式异常')
    }
    showCreateTaskDialog.value = false
    currentTaskId.value = detail.id
    taskDetail.value = detail

    // 设置模板
    selectedTid.value = detail.tid
    const tpl = availableTemplates.value.find(t => t.tid === detail.tid)
    if (tpl) selectedTemplate.value = tpl

    // 初始化空数据
    defaultData.value = {}
    customOverrides.value = {}
    checkedMacs.value = []
    resetFormData()

    // 刷新任务列表
    await fetchTaskList()
    localStorage.setItem(LAST_TASK_KEY, String(detail.id))

    ElMessage.success(`任务"${detail.name}"创建成功`)
  } catch (e: any) {
    console.error('创建任务失败:', e)
    ElMessage.error(`创建失败: ${e.message || '未知错误'}`)
  } finally {
    creatingTask.value = false
  }
}

// ════════════ 模板切换 ════════════

async function handleTemplateChange(tid: string) {
  console.log(`=== 开始模板切换: ${tid} ===`)
  const tpl = availableTemplates.value.find(t => t.tid === tid)
  if (!tpl) return
  
  // 检查是否正在切换模板
  if (selectedTemplate.value?.tid !== tid) {
    console.log(`从模板 ${selectedTemplate.value?.tid || '(无)'} 切换到 ${tid}`)
    
    // 有任务时，确认是否切换模板
    if (currentTaskId.value) {
      try {
        await ElMessageBox.confirm(
          `切换模板将会影响所有设备的数据。确定要将模板从「${selectedTemplate.value?.tname || ''}」切换到「${tpl.tname}」吗？`,
          '切换模板确认',
          {
            confirmButtonText: '确认切换',
            cancelButtonText: '取消',
            type: 'warning',
            distinguishCancelAndClose: true
          }
        )
      } catch {
        // 用户取消切换，恢复原来的tid
        selectedTid.value = selectedTemplate.value?.tid || ''
        return
      }
    }
    
    // 1. 保存当前模板的数据到缓存（含行选择）
    if (selectedTemplate.value?.tid) {
      console.log(`保存当前模板 ${selectedTemplate.value.tid} 的数据到缓存`)
      console.log('保存的数据:', defaultData.value)
      _saveTemplateCache()
    } else {
      console.log('当前没有选中模板，无需保存缓存')
    }
    
    // 2. 检查目标模板是否有缓存数据
    let targetDefaultData: Record<string, any> = {}
    let targetCustomOverrides: Record<string, Record<string, any>> = {}
    let targetSelectedRowIds: Record<string, number> = {}
    
    if (templateDataCache.value[tid]) {
      // 从缓存恢复数据
      console.log(`从缓存恢复模板 ${tid} 的数据`)
      console.log('缓存中的数据:', templateDataCache.value[tid].defaultData)
      targetDefaultData = { ...templateDataCache.value[tid].defaultData }
      targetCustomOverrides = { ...templateDataCache.value[tid].customOverrides }
      targetSelectedRowIds = { ...templateDataCache.value[tid].selectedRowIds }
    } else {
      // 没有缓存，使用新模板的默认值初始化
      console.log(`模板 ${tid} 没有缓存数据，使用默认值初始化`)
      const fields = tpl.fields || []
      console.log(`模板有 ${fields.length} 个字段`)
      for (const field of fields) {
        if (field.default_value != null && field.default_value !== '') {
          targetDefaultData[field.key] = field.default_value
        }
      }
    }
    
    console.log('目标数据准备完成:', targetDefaultData)
    
    // 3. 更新模板，使用新的对象引用确保组件重新渲染
    selectedTemplate.value = { ...tpl }
    
    // 4. 应用数据 - 使用更激进的方式确保数据更新
    // 创建全新的响应式对象，确保引用变化
    const newDefaultData = { ...targetDefaultData }
    const newCustomOverrides = { ...targetCustomOverrides }
    
    console.log('设置新数据:')
    console.log('新数据对象:', newDefaultData)
    console.log('当前数据:', defaultData.value)
    
    // 关键步骤：先清空，再设置，确保变化被检测到
    defaultData.value = {}
    customOverrides.value = {}
    
    // 等待一个tick，确保清空操作生效
    await nextTick()
    
    // 然后设置新数据
    defaultData.value = newDefaultData
    customOverrides.value = newCustomOverrides
    
    // 恢复选中行（从缓存或默认第1行）
    const currentDevices = taskDetail.value?.devices ?? []
    if (Object.keys(targetSelectedRowIds).length > 0) {
      // 验证缓存的 row_id 仍有效
      const valid: Record<string, number> = {}
      for (const d of currentDevices) {
        if (d.rows && d.rows.length > 0) {
          const cachedId = targetSelectedRowIds[d.mac]
          valid[d.mac] = d.rows.find((r: any) => r.id === cachedId) ? cachedId : d.rows[0].id
        }
      }
      selectedRowIds.value = valid
    } else {
      _initSelectedRowIds(currentDevices, currentTaskId.value ?? undefined)
    }
    
    // 再次等待DOM更新
    await nextTick()
    
    // 强制触发一次额外更新，确保WorkspaceForm能获取到数据
    if (Object.keys(newDefaultData).length > 0) {
      console.log('强制触发数据更新检查...')
      const temp = { ...defaultData.value }
      defaultData.value = {}
      await nextTick()
      defaultData.value = temp
    }
    
    console.log('最终数据状态:', defaultData.value)
    
    console.log(`模板切换完成: ${tpl.tname}`)
    console.log(`设置的数据:`, { ...targetDefaultData })
    console.log(`缓存状态:`, templateDataCache.value)
    
    // 5. 如果有任务，更新任务中的模板信息
    if (currentTaskId.value) {
      try {
        await taskApi.updateTask(currentTaskId.value, { 
          tid: tid,
          default_data: defaultData.value 
        })
        
        // 更新每台设备的自定义数据
        for (const [mac, overrides] of Object.entries(customOverrides.value)) {
          try {
            await taskApi.updateTaskDeviceData(currentTaskId.value, mac, overrides)
          } catch (e) {
            console.warn(`保存设备 ${mac} 的数据失败:`, e)
          }
        }
        
        ElMessage.success('模板已切换，数据已恢复并保存')
      } catch (e: any) {
        console.warn('更新任务模板失败:', e)
        ElMessage.warning('模板已切换但任务更新失败')
      }
    } else {
      ElMessage.success('模板已切换，数据已恢复')
    }
  }
}



/** 自动选中第一个可用的任务 */
function autoSelectTask() {
  if (taskList.value.length > 0) {
    const firstTask = taskList.value.sort((a: TaskSummary, b: TaskSummary) => b.id - a.id)[0] // 按ID倒序，选最新的任务
    currentTaskId.value = firstTask.id
    loadTaskDetail(firstTask.id)
    console.log(`自动选中任务: ${firstTask.name || firstTask.id}`)
  }
}

/** 自动选中第一个模板 */
function autoSelectTemplate() {
  if (availableTemplates.value.length > 0 && !currentTaskId.value) {
    const first = availableTemplates.value[0]
    selectedTid.value = first.tid
    handleTemplateChange(first.tid)
    console.log(`自动选中模板: ${first.tname}`)
  }
}

/** 调试函数：打印当前模板和数据状态 */
function debugTemplateState() {
  console.log('=== 模板状态调试 ===')
  console.log('当前模板ID:', selectedTemplate.value?.tid)
  console.log('当前模板名称:', selectedTemplate.value?.tname)
  console.log('默认数据:', defaultData.value)
  console.log('自定义覆盖数据:', customOverrides.value)
  console.log('缓存中的模板ID:', Object.keys(templateDataCache.value))
  
  if (selectedTemplate.value?.tid && templateDataCache.value[selectedTemplate.value.tid]) {
    console.log('当前模板缓存数据:', templateDataCache.value[selectedTemplate.value.tid])
  }
  
  // 检查WorkspaceForm是否能看到数据
  console.log('=== WorkspaceForm数据检查 ===')
  const workspaceFormData = defaultData.value
  console.log('传递到WorkspaceForm的数据:', workspaceFormData)
  
  if (selectedTemplate.value?.fields) {
    console.log('模板字段数量:', selectedTemplate.value.fields.length)
    selectedTemplate.value.fields.forEach(field => {
      console.log(`字段 [${field.key}]: ${workspaceFormData[field.key] || '(空)'}`)
    })
  }
}

function resetFormData(tpl?: TemplateInfo | null) {
  const t = tpl ?? selectedTemplate.value
  defaultData.value = {}
  customOverrides.value = {}
  if (t?.fields) {
    for (const f of t.fields) {
      if (f.default_value != null && f.default_value !== '') {
        defaultData.value[f.key] = f.default_value
      }
    }
  }
}

// ════════════ 设备确认（改为写入任务表）════════════

async function handleDeviceConfirm(macs: string[]) {
  if (!currentTaskId.value) {
    ElMessage.warning('请先选择或创建一个更新任务')
    return
  }

  // 写入 task_devices 表
  try {
    await taskApi.addTaskDevices(currentTaskId.value, macs)
    // 刷新任务详情以获取新设备列表
    await loadTaskDetail(currentTaskId.value)
    showDevicePicker.value = false
    ElMessage.success(`已添加 ${macs.length} 台设备到当前任务`)
  } catch (e: any) {
    console.warn('添加设备失败:', e)
    ElMessage.warning('添加设备失败')
  }
}

// ════════════ 推送执行（改为任务推送）════════════

async function executePush() {
  if (!currentTaskId.value) {
    ElMessage.warning('请先选择一个更新任务')
    return
  }
  if (checkedCount.value === 0) return

  // 添加确认提示
  try {
    await ElMessageBox.confirm(
      `确定要将模板数据推送到选中的 ${checkedCount.value} 台设备吗？`,
      '批量推送确认',
      {
        confirmButtonText: '确认推送',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--warning'
      }
    )
  } catch {
    // 用户取消
    return
  }

  executing.value = true

  try {
    // 先保存默认数据
    try {
      await taskApi.updateTask(currentTaskId.value, { default_data: defaultData.value })
      // 保存自定义数据覆盖
      for (const mac of checkedMacs.value) {
        if (customOverrides.value[mac]) {
          await taskApi.updateTaskDeviceData(currentTaskId.value, mac, customOverrides.value[mac])
        }
      }
    } catch (saveErr: any) {
      console.warn('推送前保存数据失败:', saveErr)
    }

    // 构建行选择参数：只包含已选中设备的行选择
    const rowSelections: Record<string, number> = {}
    for (const mac of checkedMacs.value) {
      if (selectedRowIds.value[mac]) {
        rowSelections[mac] = selectedRowIds.value[mac]
      }
    }

    // 调用任务执行接口，传递选中的设备列表和行选择
    const result: any = await taskApi.executeTask(currentTaskId.value, {
      macs: checkedMacs.value,
      rowSelections: Object.keys(rowSelections).length > 0 ? rowSelections : undefined
    })
    const data = result

    if (data.results && data.total > 0) {
      // 正常推送结果处理...
      const { success, failed, results } = data

      if (failed === 0) {
        ElNotification({
          title: '推送已发出',
          message: `全部 ${success} 台设备正在等待回执...`,
          type: 'success',
          duration: 5000,
          position: 'top-right',
        })
      } else {
        const failMacs = results
          .filter((r: any) => !r.success)
          .map((r: any) => r.mac)
          .join(', ')

        ElNotification({
          title: '部分发送失败',
          message: `成功 ${success} 台，发送失败 ${failed} 台\n${failMacs}`,
          type: 'warning',
          duration: 8000,
          position: 'top-right',
        })
      }

      // 失败的设备取消勾选
      for (const r of results) {
        if (!r.success) checkedMacs.value = checkedMacs.value.filter((m: string) => m !== r.mac)
      }

      // 刷新任务详情和进度
      if (currentTaskId.value) {
        await loadTaskDetail(currentTaskId.value)
        // 启动轮询：每3秒刷新直到全部完成
        startProgressPolling()
      }
    } else if (data.total === 0) {
      ElMessage.warning('没有可推送的设备（所有设备已更新完成或正在等待回执）')
    } else {
      ElNotification({
        title: '推送异常',
        message: '服务器返回格式异常，请稍后重试',
        type: 'error',
        duration: 5000,
      })
    }
  } catch (e: any) {
    console.error('推送异常:', e)
    ElNotification({
      title: '推送失败',
      message: e.message || '网络请求异常',
      type: 'error',
      duration: 5000,
    })
  } finally {
    executing.value = false
  }
}

/** 单台设备推送（设备选择器） — 使用单设备推送函数 */
async function handlePushSingleDevice(device: any) {
  if (!currentTaskId.value) {
    ElMessage.warning('请先选择或创建一个更新任务')
    return
  }
  const mac = device.mac
  const name = device.name || mac

  // 保存该设备的自定义数据（如果有）
  if (customOverrides.value[mac] && currentTaskId.value) {
    try { await taskApi.updateTaskDeviceData(currentTaskId.value, mac, customOverrides.value[mac]) } catch {}
  }

  try {
    // ⭐ 使用单设备推送函数
    await executeSingleDevicePush(mac, name)
  } catch (e: any) {
    console.error('单设备推送失败:', e)
    ElMessage.error(`推送「${name}」失败`)
  }
}

/** 设备列表操作列 - 推送（表格行按钮）— 单设备推送 */
async function handlePushTableDevice(dev: any) {
  if (dev.status !== 'online') {
    ElMessage.warning('设备离线，无法推送')
    return
  }
  if (!currentTaskId.value) {
    ElMessage.warning('请先选择一个更新任务')
    return
  }
  const name = dev.name || dev.mac
  try {
    await ElMessageBox.confirm(
      `确定要将当前模板数据推送到设备「${name}」吗？`,
      '推送确认',
      { confirmButtonText: '确认推送', cancelButtonText: '取消', type: 'info' }
    )

    // 保存自定义数据
    if (customOverrides.value[dev.mac]) {
      try { await taskApi.updateTaskDeviceData(currentTaskId.value, dev.mac, customOverrides.value[dev.mac]) } catch {}
    }

    // ⭐ 单设备推送：直接调用单设备推送接口
    await executeSingleDevicePush(dev.mac, name)
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(`推送「${name}」失败`)
    }
  }
}

/** 单设备推送（核心实现） - 直接调用设备推送接口 */
async function executeSingleDevicePush(mac: string, deviceName?: string) {
  if (!selectedTemplate.value?.tid) {
    ElMessage.warning('请先选择一个模板')
    return
  }
  
  const name = deviceName || mac
  const templateId = selectedTemplate.value.tid
  const templateName = selectedTemplate.value.tname || templateId
  
  executing.value = true
  
  try {
    // 1. 保存自定义数据（如果设备在任务中）
    if (currentTaskId.value && customOverrides.value[mac]) {
      try {
        await taskApi.updateTaskDeviceData(currentTaskId.value, mac, customOverrides.value[mac])
      } catch (saveErr) {
        console.warn('保存自定义数据失败:', saveErr)
      }
    }
    
    // 2. 准备推送数据（合并默认数据和自定义数据）
    const pushData = { ...defaultData.value }
    if (customOverrides.value[mac]) {
      Object.assign(pushData, customOverrides.value[mac])
    }
    
    // 3. 直接调用单设备推送接口
    ElMessage.info(`正在向「${name}」推送模板...`)
    
    try {
      const result = await deviceApi.applyTemplate(mac, templateId, pushData)
      
      if (result.code === 20000) {
        // 4. 如果设备在任务中，尝试更新状态（非必需，推送已成功）
        if (currentTaskId.value) {
          try {
            // 尝试标记为发送中状态（后端接口可能有问题）
            await taskApi.updateTaskDeviceStatus(currentTaskId.value, mac, 'sent')
            // 启动进度轮询
            startProgressPolling()
            ElMessage.success(`已向「${name}」发送推送指令`)
          } catch (statusErr) {
            console.warn('更新任务设备状态失败（不影响推送）:', statusErr)
            // 推送成功，即使状态更新失败，也显示成功
            ElMessage.success(`已向「${name}」发送推送指令（状态更新异常，不影响推送）`)
          }
        } else {
          // 不在任务中，但推送成功
          ElMessage.success(`已向「${name}」发送推送指令（独立推送）`)
        }
      } else {
        ElMessage.error(`「${name}」推送失败: ${result.message || '未知错误'}`)
        // 如果设备在任务中，标记为失败状态
        if (currentTaskId.value) {
          try {
            await taskApi.updateTaskDeviceStatus(currentTaskId.value, mac, 'failed', result.message || '推送失败')
          } catch {}
        }
      }
    } catch (e: any) {
      console.error('单设备推送失败:', e)
      ElMessage.error(`「${name}」推送失败: ${e.message || '网络错误'}`)
      // 如果设备在任务中，标记为失败状态
      if (currentTaskId.value) {
        try {
          await taskApi.updateTaskDeviceStatus(currentTaskId.value, mac, 'failed', e.message || '网络错误')
        } catch {}
      }
    }
    
  } catch (e: any) {
    console.error('单设备推送失败:', e)
    ElMessage.error(`推送「${name}」失败: ${e.message || '未知错误'}`)
  } finally {
    executing.value = false
  }
}

/** 子表数据变更（增删行等），刷新任务详情 */
async function handleDataChanged() {
  if (currentTaskId.value) {
    await loadTaskDetail(currentTaskId.value)
  }
}

/** 推送指定行的数据到设备 */
async function handlePushRow(dev: any, row: any) {
  if (dev.status !== 'online') {
    ElMessage.warning('设备离线，无法推送')
    return
  }
  if (!currentTaskId.value) {
    ElMessage.warning('请先选择一个更新任务')
    return
  }
  if (!selectedTemplate.value?.tid) {
    ElMessage.warning('请先选择一个模板')
    return
  }

  const name = dev.name || dev.mac
  try {
    const rowIndex = row.sort_order !== undefined ? row.sort_order + 1 : (dev.rows?.findIndex((r: any) => r.id === row.id) ?? 0) + 1
    await ElMessageBox.confirm(
      `确定要将「数据行 #${rowIndex}」推送到设备「${name}」吗？`,
      '推送确认',
      { confirmButtonText: '确认推送', cancelButtonText: '取消', type: 'info' }
    )

    executing.value = true

    // 调用任务执行接口，只推送该设备的指定行
    const rowSelections: Record<string, number> = { [dev.mac]: row.id }
    const result: any = await taskApi.executeTask(currentTaskId.value, {
      macs: [dev.mac],
      rowSelections
    })

    // 响应拦截器已解包，result 直接就是 data 内容
    const data = result
    if (data && data.results && data.total > 0) {
      const { success, failed } = data
      if (failed === 0) {
        ElMessage.success(`已向「${name}」发送推送指令`)
        // 刷新任务详情并启动轮询
        if (currentTaskId.value) {
          await loadTaskDetail(currentTaskId.value)
          startProgressPolling()
        }
      } else {
        ElMessage.error(`「${name}」推送失败`)
      }
    } else if (data && data.total === 0) {
      ElMessage.warning('没有可推送的设备')
    } else {
      ElMessage.error(`「${name}」推送失败: 未知错误`)
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('推送指定行失败:', e)
      ElMessage.error(`推送「${name}」失败`)
    }
  } finally {
    executing.value = false
  }
}

/** 从任务移除设备 */
async function handleRemoveTableDevice(dev: any) {
  if (!currentTaskId.value) return
  const name = dev.name || dev.mac
  try {
    await ElMessageBox.confirm(
      `确定要将设备「${name}」从当前任务中移除吗？`,
      '移除确认',
      { confirmButtonText: '确定移除', cancelButtonText: '取消', type: 'info' }
    )
    await taskApi.removeTaskDevice(currentTaskId.value!, dev.mac)
    // 本地刷新
    await loadTaskDetail(currentTaskId.value!)
    ElMessage.success(`已将「${name}」从任务中移除`)
  } catch (e: any) {
    if (e !== 'cancel') {
      console.error('移除设备失败:', e)
      ElMessage.error(`移除失败: ${e.message || '未知错误'}`)
    }
  }
}

// ════════════ Excel导入导出功能 ════════════

/** 导出设备列表到Excel */
function exportToExcel() {
  if (!selectedTemplate.value || selectedMacs.value.length === 0) {
    ElMessage.warning('没有可导出的设备')
    return
  }

  // 确定要导出的设备：有勾选则导出勾选的，否则导出全部
  const macsToExport = checkedMacs.value.length > 0 ? checkedMacs.value : selectedMacs.value
  
  if (macsToExport.length === 0) {
    ElMessage.warning('没有可导出的设备')
    return
  }

  // 获取模板字段
  const fields = selectedTemplate.value.fields || []
  
  // 检查是否有设备存在多行数据（子表行）
  const hasMultiRowDevices = macsToExport.some(mac => {
    const taskDev = taskDetail.value?.devices?.find((d: any) => d.mac === mac)
    return taskDev && taskDev.rows && taskDev.rows.length > 0
  })
  
  // 构建表头（使用 label 作为显示名，key 作为数据键）
  const headers = ['MAC地址', '设备名称', '状态', ...(hasMultiRowDevices ? ['数据行号'] : []), ...fields.map((f: any) => f.label || f.key)]
  
  // 构建数据行
  const rows: any[] = []
  
  macsToExport.forEach(mac => {
    const device = deviceStore.devices?.find((d: any) => d.mac === mac)
    const taskDev = taskDetail.value?.devices?.find((d: any) => d.mac === mac)
    const customData = customOverrides.value[mac] || {}
    const subRows = taskDev?.rows || []
    
    if (subRows.length > 0) {
      // 多行模式：每个子表行输出一条记录，附加行号
      subRows.forEach((row: any, idx: number) => {
        const rowData: any = {
          'MAC地址': mac,
          '设备名称': device?.name || '',
          '状态': taskDev?.update_status || 'pending',
        }
        if (hasMultiRowDevices) rowData['数据行号'] = `#${idx + 1}`
        
        let rowCustomData: Record<string, any> = {}
        try { rowCustomData = typeof row.custom_data === 'string' ? JSON.parse(row.custom_data) : (row.custom_data || {}) } catch {}
        
        fields.forEach((field: any) => {
          const key = field.key
          const label = field.label || key
          const value = rowCustomData[key] !== undefined ? rowCustomData[key]
            : (customData[key] !== undefined ? customData[key] : defaultData.value[key])
          rowData[label] = value !== undefined ? value : ''
        })
        rows.push(rowData)
      })
    } else {
      // 单行模式（原有逻辑）
      const rowData: any = {
        'MAC地址': mac,
        '设备名称': device?.name || '',
        '状态': taskDev?.update_status || 'pending',
      }
      
      fields.forEach((field: any) => {
        const key = field.key
        const label = field.label || key
        const value = customData[key] !== undefined ? customData[key] : defaultData.value[key]
        rowData[label] = value !== undefined ? value : ''
      })
      
      rows.push(rowData)
    }
  })

  import('xlsx').then(XLSX => {
    const worksheet = XLSX.utils.json_to_sheet(rows, { header: headers })
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, '设备列表')
    
    const taskName = taskDetail.value?.name || '任务'
    const templateName = selectedTemplate.value?.tname || selectedTemplate.value?.tid || '未知模板'
    const exportType = checkedMacs.value.length > 0 ? '已选' : '全部'
    const now = new Date()
    const timeStr = now.toLocaleString('zh-CN', { 
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    }).replace(/[/:]/g, '').replace(/\s/g, '_')
    
    const fileName = `${taskName}_${templateName}_${exportType}_${timeStr}.xlsx`
    XLSX.writeFile(workbook, fileName)
    ElMessage.success(`已导出 ${rows.length} 条记录`)
  }).catch((e) => {
    console.error('导出失败:', e)
    ElMessage.error('导出失败，请检查是否安装了xlsx库')
  })
}

/** 处理Excel导入 */
async function handleImport(file: any) {
  if (!file) return
  
  importing.value = true
  try {
    const XLSX = await import('xlsx')
    const data = await file.raw.arrayBuffer()
    const workbook = XLSX.read(data, { type: 'array' })
    const worksheet = workbook.Sheets[workbook.SheetNames[0]]
    const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 }) as any[][]
    
    if (jsonData.length < 2) {
      ElMessage.warning('Excel文件数据为空')
      return
    }
    
    // 解析表头
    const headers = jsonData[0] as string[]
    const macIndex = headers.findIndex(h => h.includes('MAC') || h.includes('mac'))
    
    if (macIndex === -1) {
      ElMessage.error('未找到MAC地址列，请检查Excel格式')
      return
    }
    
    // 获取模板字段映射
    const fields = selectedTemplate.value?.fields || []
    console.log('[Import] 模板字段:', fields.map((f: any) => ({ key: f.key, label: f.label })))
    console.log('[Import] Excel表头:', headers)
    const fieldKeyToIndex: Record<string, number> = {}
    fields.forEach((field: any) => {
      const label = field.label || field.key
      const index = headers.findIndex(h => h === label || h === field.key)
      console.log(`[Import] 查找字段 "${label}" (key: ${field.key}) -> 索引: ${index}`)
      if (index !== -1) {
        fieldKeyToIndex[field.key] = index
      }
    })
    console.log('[Import] 字段映射:', fieldKeyToIndex)
    
    // 解析数据行（按 MAC 分组，支持同一 MAC 多行导入）
    const macToRowsMap = new Map<string, Array<Record<string, any>>>()
    const importedMacs: string[] = []

    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/

    for (let i = 1; i < jsonData.length; i++) {
      const row = jsonData[i]
      const mac = row[macIndex] as string
      if (!mac || typeof mac !== 'string') continue

      const trimmedMac = mac.trim().toUpperCase()
      if (!macRegex.test(trimmedMac)) continue

      const normalizedMac = trimmedMac

      const customData: Record<string, any> = {}
      Object.entries(fieldKeyToIndex).forEach(([key, idx]) => {
        if (row[idx] !== undefined && row[idx] !== null && row[idx] !== '') {
          customData[key] = row[idx]
        }
      })

      if (!macToRowsMap.has(normalizedMac)) {
        macToRowsMap.set(normalizedMac, [])
        importedMacs.push(normalizedMac)
      }
      macToRowsMap.get(normalizedMac)!.push(customData)
    }

    // 检测同 MAC 多行 → 弹出策略选择
    const multiRowMacs = [...macToRowsMap.entries()].filter(([, rows]) => rows.length > 1)

    let importMode: 'overwrite' | 'append' | undefined
    if (multiRowMacs.length > 0 && currentTaskId.value) {
      try {
        await ElMessageBox.confirm(
          `检测到 ${multiRowMacs.length} 个设备有多行重复数据。\n\n选择处理方式：`,
          '导入策略',
          {
            confirmButtonText: '覆盖模式（替换所有旧行）',
            cancelButtonText: '追加模式（保留旧行）',
            type: 'warning',
            distinguishCancelAndClose: true,
          }
        ).then(() => { importMode = 'overwrite' }).catch((action: string) => {
          if (action === 'close') importMode = undefined
          else importMode = 'append'
        })
        if (!importMode) return
      } catch {
        showImportDialog.value = false
        importFileList.value = []
        return
      }
    }
    
    if (importedMacs.length === 0) {
      ElMessage.warning('未找到有效的设备MAC地址')
      return
    }
    
    // 合并到当前任务
    if (currentTaskId.value) {
      // 新设备
      const newMacs = importedMacs.filter(m => !selectedMacs.value.includes(m))
      if (newMacs.length > 0) {
        const newMacsCustomData: Record<string, Record<string, any>> = {}
        newMacs.forEach(mac => {
          const rows = macToRowsMap.get(mac)!
          if (rows.length > 0 && Object.keys(rows[0]).length > 0) {
            newMacsCustomData[mac] = rows[0]
          }
        })
        await taskApi.addTaskDevices(currentTaskId.value, newMacs, newMacsCustomData)
      }

      // 处理每个设备：多行→子表，单行→主表
      for (const mac of importedMacs) {
        const rows = macToRowsMap.get(mac)!
        const isExisting = selectedMacs.value.includes(mac)

        if (isExisting && rows.length > 1 && importMode) {
          // 多行数据：写入子表
          // rows[0] 作为主表 custom_data（覆盖/追加均需更新主表）
          const dataRows = rows.map(r => ({ ...r }))
          try {
            await taskApi.batchAddDeviceRows(currentTaskId.value!, mac, dataRows, importMode)
          } catch (rowErr) {
            console.warn(`[Import] 子表写入失败(${mac}):`, rowErr)
            await taskApi.updateTaskDeviceData(currentTaskId.value!, mac, rows[0])
          }
          // 更新主表 custom_data 为第一行数据
          if (rows[0] && Object.keys(rows[0]).length > 0) {
            await taskApi.updateTaskDeviceData(currentTaskId.value!, mac, rows[0])
          }
        } else if (isExisting && rows.length >= 1) {
          // 单行数据：只更新主表
          if (rows[0] && Object.keys(rows[0]).length > 0) {
            try { await taskApi.updateTaskDeviceData(currentTaskId.value!, mac, rows[0]) } catch {}
          }
        } else if (!isExisting && rows.length > 1) {
          // 新设备且有多行数据：子表行也已通过 addTaskDevices 中的 newMacsCustomData 写入了主表
          // 还需要把所有行写入子表
          const dataRows = rows.map(r => ({ ...r }))
          try {
            await taskApi.batchAddDeviceRows(currentTaskId.value!, mac, dataRows, 'append')
          } catch (rowErr) {
            console.warn(`[Import] 新设备子表写入失败(${mac}):`, rowErr)
          }
        }
      }

      await loadTaskDetail(currentTaskId.value)

      if (selectedTemplate.value?.tid) {
        _saveTemplateCache()
      }
    } else {
      // 无任务模式：本地更新（单行兼容）
      const updatedOverrides: Record<string, Record<string, any>> = {}
      for (const [mac, data] of Object.entries(customOverrides.value)) {
        updatedOverrides[mac] = { ...data }
      }
      importedMacs.forEach(mac => {
        const rows = macToRowsMap.get(mac)!
        if (rows.length > 0 && rows[0] && Object.keys(rows[0]).length > 0) {
          updatedOverrides[mac] = { ...updatedOverrides[mac], ...rows[0] }
        }
      })
      customOverrides.value = updatedOverrides
      ElMessage.info(`已导入 ${importedMacs.length} 台设备数据，请创建任务后添加设备`)
    }

    ElMessage.success(`成功导入 ${importedMacs.length} 台设备${multiRowMacs.length > 0 ? `（含 ${multiRowMacs.length} 个多行设备）` : ''}`)
    showImportDialog.value = false
    importFileList.value = []
    
    // 强制刷新表格显示
    tableRefreshKey.value++
    await nextTick()
  } catch (e: any) {
    console.error('导入失败:', e)
    ElMessage.error(`导入失败: ${e.message || '未知错误'}`)
  } finally {
    importing.value = false
  }
}

/** 下载导入模板 */
function downloadImportTemplate() {
  if (!selectedTemplate.value) {
    ElMessage.warning('请先选择模板')
    return
  }
  
  const fields = selectedTemplate.value.fields || []
  const headers = ['MAC地址', '设备名称', '状态', ...fields.map((f: any) => f.label || f.key)]
  
  // 示例数据
  const exampleData = [{
    'MAC地址': 'D4:3D:39:XX:XX:XX',
    '设备名称': '示例设备',
    '状态': 'pending',
    ...fields.reduce((acc: any, f: any) => {
      acc[f.label || f.key] = ''
      return acc
    }, {})
  }]
  
  import('xlsx').then(XLSX => {
    const worksheet = XLSX.utils.json_to_sheet(exampleData, { header: headers })
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, '导入模板')
    XLSX.writeFile(workbook, `设备导入模板_${selectedTemplate.value?.tname || '模板'}.xlsx`)
  })
}

/** 全选/反切所有设备勾选 */
function updateAllChecked() {
  checkedMacs.value = [...selectedMacs.value]
}

// ════════════ 草稿持久化（保留兼容旧逻辑）════════════

// ════════════ 行选择持久化辅助 ═════════════

/** 初始化 selectedRowIds：优先从后端 DB 数据恢复 → localStorage 草稿 → 模板缓存 → 默认第1行 */
function _initSelectedRowIds(devices: any[], taskId?: number) {
  // 0. 最优先：从后端返回的 selected_row_id 恢复（跨设备同步的权威来源）
  const fromDb: Record<string, number> = {}
  let hasDbData = false
  for (const d of devices) {
    if (d.rows && d.rows.length > 0) {
      if (d.selected_row_id) {
        const exists = d.rows.find((r: any) => r.id === d.selected_row_id)
        if (exists) {
          fromDb[d.mac] = d.selected_row_id
          hasDbData = true
          continue
        }
      }
      // fallback 到第1行
      fromDb[d.mac] = d.rows[0].id
    }
  }
  if (hasDbData) {
    selectedRowIds.value = fromDb
    console.log('从后端DB恢复选中行:', fromDb)
    return
  }

  // 1. 尝试从 localStorage 草稿恢复（页面刷新后内存缓存丢失，草稿是备用来源）
  if (taskId) {
    const draft = readDraftRaw()
    if (draft?.selectedRowIds && draft.taskId === taskId) {
      const valid: Record<string, number> = {}
      for (const d of devices) {
        if (d.rows && d.rows.length > 0) {
          const cachedId = draft.selectedRowIds[d.mac]
          const exists = d.rows.find((r: any) => r.id === cachedId)
          valid[d.mac] = exists ? cachedId : d.rows[0].id
        }
      }
      selectedRowIds.value = valid
      console.log('从 localStorage 草稿恢复选中行:', valid)
      return
    }
  }

  // 2. 尝试从模板缓存恢复
  const cached = selectedTemplate.value?.tid ? templateDataCache.value[selectedTemplate.value.tid] : null
  if (cached?.selectedRowIds) {
    const valid: Record<string, number> = {}
    for (const d of devices) {
      if (d.rows && d.rows.length > 0) {
        const cachedId = cached.selectedRowIds[d.mac]
        const exists = d.rows.find((r: any) => r.id === cachedId)
        valid[d.mac] = exists ? cachedId : d.rows[0].id
      }
    }
    selectedRowIds.value = valid
    console.log('从模板缓存恢复选中行:', valid)
    return
  }

  // 3. 无缓存：默认选第1行
  const defaults: Record<string, number> = {}
  for (const d of devices) {
    if (d.rows && d.rows.length > 0) {
      defaults[d.mac] = d.rows[0].id
    }
  }
  selectedRowIds.value = defaults
}

/** 将当前数据（含行选择）保存到模板缓存 */
function _saveTemplateCache() {
  if (!selectedTemplate.value?.tid) return
  templateDataCache.value[selectedTemplate.value.tid] = {
    defaultData: { ...defaultData.value },
    customOverrides: { ...customOverrides.value },
    selectedRowIds: { ...selectedRowIds.value }
  }
}

let autoSaveTimer: ReturnType<typeof setInterval> | null = null

function saveDraft() {
  try {
    const draft = {
      tid: selectedTid.value,
      taskId: currentTaskId.value,
      macs: selectedMacs.value,
      checkedMacs: checkedMacs.value,
      defaultData: defaultData.value,
      customOverrides: customOverrides.value,
      selectedRowIds: { ...selectedRowIds.value },
      savedAt: Date.now(),
    }
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
  } catch (e) {
    console.warn('草稿保存失败:', e)
  }
}

function readDraftRaw(): any {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return null
}

function autoSave() {
  if ((currentTaskId.value || selectedTemplate.value) && selectedMacs.value.length > 0) saveDraft()
}

function restoreDraft() {
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const draft = JSON.parse(raw)
    // 只恢复非任务的草稿数据（兼容降级）
    if (!currentTaskId.value && draft.macs) {
      selectedTid.value = draft.tid ?? ''
      checkedMacs.value = draft.checkedMacs ?? draft.macs ?? []
      defaultData.value = draft.defaultData ?? {}
      customOverrides.value = draft.customOverrides ?? {}
      selectedRowIds.value = draft.selectedRowIds ?? {}
      if (draft.tid) {
        const tpl = availableTemplates.value.find(t => t.tid === draft.tid)
        if (tpl) selectedTemplate.value = tpl
      }
    }
  } catch (e) {
    console.warn('恢复草稿失败:', e)
  }
}

// ════════════ 生命周期 ═════════════

/** WS display_reply 监听器：收到设备回执后就地更新任务状态 */
function onDisplayReply(data: any) {
  const mac = data?.mac
  const result = data?.result ?? data?.code
  if (!mac || !taskDetail.value) return

  // 在本地 taskDetail.devices 中找到对应设备，就地修改（立即响应）
  const dev = taskDetail.value.devices.find((d: any) => d.mac === mac)
  if (!dev) return

  if (result === 200) {
    dev.update_status = 'success'
    dev.error_msg = ''
    dev.finished_at = new Date().toLocaleString('zh-CN', { hour12: false })
  } else {
    dev.update_status = 'failed'
    dev.error_msg = `result=${result}`
    dev.finished_at = new Date().toLocaleString('zh-CN', { hour12: false })
  }

  // 从服务端刷新最新数据（轻量级，不覆盖自定义数据）
  _refreshTaskFromServer().catch(() => {})
}

onMounted(async () => {
  await templateStore.fetchTemplates()
  await deviceStore.fetchDevices()
  await fetchTaskList()

  // 注册 WS display_reply 监听
  onWsMessage('display_reply', onDisplayReply)

  // 优先恢复上次编辑的任务
  const lastTaskIdStr = localStorage.getItem(LAST_TASK_KEY)
  if (lastTaskIdStr) {
    const lastId = parseInt(lastTaskIdStr, 10)
    if (!isNaN(lastId)) {
      const exists = taskList.value.find((t: TaskSummary) => t.id === lastId)
      if (exists) {
        currentTaskId.value = lastId
        await loadTaskDetail(lastId)
        console.log(`恢复上次编辑的任务: ${lastId}`)
        // 恢复成功，设置自动保存并返回
        autoSaveTimer = setInterval(autoSave, 30000)
        return
      }
    }
  }

  // 如果没有上次编辑的任务，则自动选择一个任务
  if (taskList.value.length > 0) {
    autoSelectTask()
  } else {
    // 没有任务时，使用模板选择和草稿恢复逻辑
    // URL 参数预选
    if (preSelectedMacs.value.length > 0) {
      // 有URL参数，尝试兼容处理
      // selectedMacs是计算属性，无法直接赋值，需要在任务中处理
      console.log(`URL参数包含设备: ${preSelectedMacs.value.join(', ')}`)
    }
    
    // 降级：恢复 localStorage 草稿
    restoreDraft()
    
    // 自动选模板（如果还没选）
    if (!selectedTemplate.value && availableTemplates.value.length > 0) {
      autoSelectTemplate()
    }
  }

  // 自动保存（30秒）
  autoSaveTimer = setInterval(autoSave, 30000)
})

/** 当模板切换时，如果已有任务则不自动拉取旧绑定（由任务管理设备） */
watch(() => selectedTemplate.value?.tid, async (tid) => {
  if (!tid || currentTaskId.value) return // 有任务时不走旧的绑定逻辑
  try {
    const res: any = await deviceApi.getTemplateBoundMacs(tid)
    const boundMacs = res?.macs
    if (boundMacs && boundMacs.length > 0) {
      // 仅设置内存变量（不覆盖任务系统）
      checkedMacs.value = [...boundMacs]
    }
  } catch (e) {
    console.warn('从数据库恢复设备列表失败:', e)
  }
}, { immediate: true })

// ── 数据变化时自动保存到DB（防抖） ──
let dbAutoSaveTimer: ReturnType<typeof setTimeout> | null = null

watch([defaultData, customOverrides, selectedRowIds], () => {
  // 1. 更新当前模板的数据缓存（含行选择）
  if (selectedTemplate.value?.tid) {
    _saveTemplateCache()
    console.log(`数据变化: 更新模板 ${selectedTemplate.value.tid} 的缓存`)
  }
  
  // 1.5 立即保存草稿到 localStorage（确保 selectedRowIds 刷新后可恢复）
  saveDraft()
  
  // 2. 如果有任务，自动保存到数据库
  if (!currentTaskId.value) return
  // 防抖：数据变化后 2 秒自动保存到 DB
  if (dbAutoSaveTimer) clearTimeout(dbAutoSaveTimer)
  dbAutoSaveTimer = setTimeout(async () => {
    try {
      await taskApi.updateTask(currentTaskId.value!, { default_data: defaultData.value })
      // 保存所有设备的自定义覆盖数据
      for (const mac of Object.keys(customOverrides.value)) {
        if (customOverrides.value[mac]) {
          await taskApi.updateTaskDeviceData(currentTaskId.value!, mac, customOverrides.value[mac])
        }
      }
      console.log('[Task] 数据已自动保存到 DB')
    } catch (e) {
      console.warn('[Task] 自动保存失败:', e)
    }
  }, 2000)
}, { deep: true })

// ── selectedRowIds 单独同步到后端（快速防抖 500ms，确保跨设备同步） ──
let selectedRowSyncTimer: ReturnType<typeof setTimeout> | null = null
watch(selectedRowIds, (newVal) => {
  if (!currentTaskId.value) return
  if (selectedRowSyncTimer) clearTimeout(selectedRowSyncTimer)
  selectedRowSyncTimer = setTimeout(async () => {
    try {
      for (const [mac, rowId] of Object.entries(newVal)) {
        if (rowId) {
          await taskApi.updateSelectedRow(currentTaskId.value!, mac, rowId as number)
        }
      }
    } catch (e) {
      console.warn('[Task] 选中行同步失败:', e)
    }
  }, 500)
}, { deep: true })

onUnmounted(() => {
  if (autoSaveTimer) clearInterval(autoSaveTimer)
  if (dbAutoSaveTimer) clearTimeout(dbAutoSaveTimer)
  if (selectedRowSyncTimer) clearTimeout(selectedRowSyncTimer)
  stopProgressPolling()
  offWsMessage('display_reply', onDisplayReply)
})
</script>

<style scoped lang="scss">
.simple-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 1100px;
  margin: 0 auto;
  padding-bottom: 80px; // 为底部bar留空间
}

/* ═══ 顶栏工具条 ═══ */
.top-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 14px;
  padding: 12px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
/* 选择器标签样式 */
.selector-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 600;
  
  .label-text {
    color: #1e293b;
    white-space: nowrap;
  }
  
  .el-icon {
    color: #94a3b8;
    cursor: help;
    font-size: 12px;
    
    &:hover {
      color: #6366f1;
    }
  }
}

/* 任务选择器 */
.task-switcher {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6366f1;

  .el-select { width: 200px; }
}
.tpl-switcher {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #475569;

  .el-select { width: 180px; }
}
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ═══ 卡片通用 ═══ */
.card {
  background: white;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h3 {
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 6px;
  }
}
.card-hint {
  font-size: 12.5px;
  color: #94a3b8;
}

/* ═══ 通用数据折叠面板 ═══ */
.generic-data-collapse {
  background: white;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
  overflow: hidden;

  :deep(.el-collapse-item__header) {
    height: auto;
    min-height: 48px;
    padding: 10px 20px;
    border-bottom: none;
    font-size: unset;
    color: unset;
    cursor: pointer;
    transition: background-color 0.2s;
    &:hover { background: #f8fafc; }
  }

  :deep(.el-collapse-item__arrow) {
    margin-right: 4px;
  }
  :deep(.el-collapse-item__wrap) {
    border-bottom: none;
  }
  :deep(.el-collapse-item__content) {
    padding: 0 20px 20px;
  }
}
.collapse-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.collapse-title-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.collapse-title-text {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}
.field-summary {
  font-size: 12.5px;
  font-weight: 500;
  color: #6366f1;
  background: rgba(99,102,241,0.08);
  padding: 2px 10px;
  border-radius: 10px;
}
.collapse-hint {
  flex-shrink: 0;
  margin-right: 8px;
}
.collapse-content-wrap {
  padding-top: 8px;
}

/* ═══ 空态 ═══ */
.empty-state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 40px;
  background: white;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  text-align: center;

  h2 {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin: 20px 0 8px;
  }
  p {
    font-size: 14px;
    color: #64748b;
    margin: 0 0 24px;
    max-width: 360px;
  }
}
.empty-icon-wrap {
  width: 88px;
  height: 88px;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
  color: #6366f1;
}

/* ═══ 默认值表单卡片 ═══ */
.form-footer-tip {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 14px;
  padding: 9px 13px;
  background: rgba(99,102,241,0.04);
  border-radius: 8px;
  color: #6366f1;
  font-size: 12.5px;
}

/* ═══ 设备表卡片 ═══ */
.device-table-card {
  min-height: 120px;
  overflow: visible;
}

/* 移动端设备表卡片 */
@media (max-width: 768px) {
  .device-table-card {
    padding: 12px;
    overflow: visible;
  }
}
.empty-devices {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
  color: #94a3b8;

  p {
    font-size: 14px;
    margin: 10px 0 6px;
  }
}
.device-count-badge {
  font-size: 12.5px;
  font-weight: 600;
  color: #6366f1;
  background: rgba(99,102,241,0.08);
  padding: 2px 10px;
  border-radius: 10px;
}

/* ═══ 任务进度徽章 ═══ */
.header-right-badges {
  display: flex;
  align-items: center;
  gap: 6px;
}
.badge-pending, .badge-sent, .badge-success, .badge-failed {
  font-size: 11.5px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
}
.badge-pending { color: #6b7280; background: rgba(107,114,128,0.08); }
.badge-sent { color: #d97706; background: rgba(217,119,6,0.08); }
.badge-success { color: #059669; background: rgba(5,150,105,0.08); }
.badge-failed { color: #dc2626; background: rgba(220,38,38,0.08); }

/* ═══ 表格操作行（已选数量 + 推送按钮）═══ */
.table-action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;

  .check-info {
    font-size: 13.5px;
    color: #64748b;
    font-weight: 500;
  }
}
.push-btn {
  padding: 10px 28px;
  font-size: 14.5px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  box-shadow: 0 4px 14px rgba(99,102,241,0.35);

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99,102,241,0.45);
  }
  &:disabled {
    opacity: 0.55;
  }
}

/* ═══ 设备选择弹窗移动端 ═══ */
.device-picker-dialog {
  :deep(.el-dialog) { border-radius: 16px; }

  :deep(.el-dialog__body) {
    padding: 12px 16px 20px;
    max-height: 70vh;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
}

// 手机端：纯CSS全屏
@media (max-width: 768px) {
  .device-picker-dialog {
    :deep(.el-overlay-dialog) {
      display: flex;
      justify-content: stretch;
      align-items: stretch;
    }
    :deep(.el-dialog) {
      width: 100% !important;
      margin: 0 !important;
      max-width: 100vw !important;
      max-height: 100vh !important;
      height: 100vh !important;
      border-radius: 0;

      .el-dialog__header {
        position: sticky;
        top: 0;
        z-index: 10;
        background: white;
        border-bottom: 1px solid var(--el-border-color-lighter);
        margin-right: 0 !important;
        padding: 14px 18px;
      }

      .el-dialog__title {
        font-size: 17px !important;
      }

      .el-dialog__body {
        flex: 1;
        overflow-y: auto;
        padding: 10px 8px;
        -webkit-overflow-scrolling: touch;
      }
    }
  }
}

@media (max-width: 768px) {
  .simple-workspace {
    gap: 10px;
    max-width: 100%;
  }

  .top-toolbar {
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 12px;
  }

  .toolbar-left {
    width: 100%;
    flex-wrap: wrap;

    .task-switcher { width: 100%; margin-bottom: 4px; }
    .task-switcher .el-select { width: calc(100% - 80px); flex: 1; }
    .tpl-switcher { width: 100%; border-left: none !important; padding-left: 0 !important; border-top: 1px solid #e2e8f0; padding-top: 8px; margin-top: 4px; }
    .tpl-switcher .el-select { width: 100%; flex: 1; }
  }

  .card {
    padding: 14px;
    border-radius: 12px;
    overflow: visible;
  }

  .collapse-title-text { font-size: 14px; }
  .field-summary { font-size: 11px; }
  .collapse-hint { display: none; }

  .table-action-row {
    padding: 10px 0;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .push-btn {
    padding: 9px 18px;
    font-size: 13.5px;
  }

  /* 顶栏badge移动端适配 */
  .header-right-badges {
    gap: 4px;
    flex-wrap: wrap;
  }
  .device-count-badge, .badge-sent, .badge-success, .badge-failed {
    font-size: 11px;
    padding: 2px 6px;
  }

  /* 表格区域（仅桌面端需要横向滚动） */
  .desktop-table { overflow-x: auto; -webkit-overflow-scrolling: touch; }
}

/* 设备筛选工具栏 */
.device-filter-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
  
  .filter-result-info {
    font-size: 13px;
    color: #6b7280;
    font-weight: 500;
  }
}

/* 移动端筛选工具栏适配 */
@media (max-width: 768px) {
  .device-filter-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
    
    .el-input {
      width: 100% !important;
    }
    
    .filter-result-info {
      text-align: center;
      font-size: 12px;
    }
  }
}
</style>
