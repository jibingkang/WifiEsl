<template>
  <div class="oplog-page">
    <!-- 头部 -->
    <header class="page-header">
      <div>
        <h1><ClipboardList :size="22" /> 操作记录</h1>
        <p>查看所有操作日志，包括数据推送、设备上下线等记录</p>
      </div>
    </header>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="filterAction" placeholder="操作类型" clearable size="default" style="width: 140px" @change="fetchData">
          <el-option v-for="opt in actionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
        <el-input v-model="filterMac" placeholder="设备 MAC" clearable size="default" style="width: 200px" @clear="fetchData" @keyup.enter="fetchData" />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="default"
          value-format="YYYY-MM-DD"
          @change="fetchData"
        />
        <el-button type="primary" size="default" @click="fetchData">
          <Search :size="14" /> 查询
        </el-button>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="log-content">
      <div v-if="loading" class="state-card">
        <el-skeleton :rows="6" animated />
      </div>

      <div v-else-if="items.length === 0" class="state-card empty-state">
        <div class="empty-icon-wrap"><ClipboardList :size="40" /></div>
        <h3>暂无操作记录</h3>
        <p>执行推送操作后，记录会显示在这里</p>
      </div>

      <!-- 表格模式 -->
      <div v-else class="log-table-wrap">
        <el-table :data="items" stripe size="default" @row-click="toggleExpand" row-key="id" :row-class-name="rowClassName">
          <el-table-column label="时间" width="160">
            <template #default="{ row }">
              <span class="time-cell">{{ formatTime(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作类型" width="130">
            <template #default="{ row }">
              <el-tag :type="actionTagType(row.action)" size="small" effect="dark" round>
                {{ row.action_label || row.action }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作者" width="100" v-if="role !== 'operator'">
            <template #default="{ row }">
              <span class="user-cell">{{ row.username || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="目标" min-width="200">
            <template #default="{ row }">
              <span class="target-cell">
                <template v-if="row.action === 'task_push' || row.action === 'batch_update_template'">
                  {{ row.detail?.templateName || row.detail?.tname || `任务 #${row.target_id}` }}
                  <span class="target-sub">({{ row.detail?.deviceCount || 0 }} 台设备)</span>
                </template>
                <template v-else-if="row.action === 'device_online' || row.action === 'device_offline'">
                  <code>{{ row.target_id }}</code>
                </template>
                <template v-else>
                  {{ row.target_type }} {{ row.target_id }}
                </template>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="结果" width="80" align="center">
            <template #default="{ row }">
              <span :class="['result-dot', row.result === 'success' ? 'success' : 'fail']" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click.stop="toggleExpand(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          small
          layout="prev, pager, next"
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          @current-change="fetchPage"
        />
      </div>
    </div>

    </div>

    <!-- 操作详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="操作详情"
      width="640px"
      :close-on-click-modal="true"
      destroy-on-close
      class="detail-dialog"
    >
      <template v-if="expandedItem">
        <!-- 推送详情 -->
        <template v-if="expandedItem.action === 'task_push'">
          <div class="detail-grid">
            <div class="detail-field"><label>任务 ID</label><span>{{ expandedItem.target_id }}</span></div>
            <div class="detail-field"><label>模板</label><span>{{ expandedItem.detail?.templateName || '-' }}</span></div>
            <div class="detail-field"><label>设备数</label><span>{{ expandedItem.detail?.deviceCount || 0 }}</span></div>
            <div class="detail-field"><label>发送成功</label><span class="text-success">{{ expandedItem.detail?.sentOk || 0 }}</span></div>
            <div class="detail-field"><label>发送失败</label><span class="text-danger">{{ expandedItem.detail?.sentFail || 0 }}</span></div>
            <div class="detail-field"><label>操作者</label><span>{{ expandedItem.username || '-' }}</span></div>
          </div>
          <div v-if="pushDetailDevices.length > 0" class="push-device-list">
            <h4>设备推送明细</h4>
            <el-table :data="pushDetailDevices" size="small" max-height="280">
              <el-table-column prop="mac" label="MAC" width="180">
                <template #default="{ row }"><code>{{ row.mac }}</code></template>
              </el-table-column>
              <el-table-column label="推送时间" width="150">
                <template #default="{ row }">
                  <span class="time-cell">{{ formatTime(row.sent_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="推送内容" min-width="200">
                <template #default="{ row }">
                  <span v-if="row.push_data && Object.keys(row.push_data).length > 0" class="push-data-preview">
                    <template v-for="(v, k) in row.push_data" :key="k">
                      <el-tag size="small" type="info" class="data-tag">{{ k }}: {{ v }}</el-tag>
                    </template>
                  </span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column label="结果" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.result === 'success' ? 'success' : row.result === 'failed' ? 'danger' : 'warning'" size="small">
                    {{ resultLabel(row.result) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="error_msg" label="错误信息" min-width="150">
                <template #default="{ row }">
                  <span class="text-muted">{{ row.error_msg || '-' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>

        <!-- 设备上下线详情 -->
        <template v-else-if="expandedItem.action === 'device_online' || expandedItem.action === 'device_offline'">
          <div class="detail-grid">
            <div class="detail-field"><label>设备 MAC</label><span><code>{{ expandedItem.target_id }}</code></span></div>
            <div class="detail-field"><label>事件</label><span>{{ expandedItem.action === 'device_online' ? '上线' : '离线' }}</span></div>
          </div>
        </template>

        <!-- 通用详情 -->
        <template v-else>
          <div class="detail-raw">
            <pre>{{ JSON.stringify(expandedItem.detail, null, 2) }}</pre>
          </div>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ClipboardList, Search, X } from 'lucide-vue-next'
import { getOperationLogs, getPushLogs } from '@/api/logs'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const role = computed(() => authStore.getUserRole())

interface LogItem {
  id: number
  username?: string
  action: string
  action_label?: string
  target_type?: string
  target_id?: string
  detail?: any
  result: string
  created_at: string
  user_id?: number
  task_id?: number
}

interface PushLogItem {
  id: number
  mac: string
  push_data?: any
  result: string
  error_msg: string
  template_name?: string
  username?: string
  sent_at?: string
  replied_at?: string
}

const loading = ref(false)
const items = ref<LogItem[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const detailDialogVisible = ref(false)
const pushDetailDevices = ref<PushLogItem[]>([])

// 筛选
const filterAction = ref('')
const filterMac = ref('')
const dateRange = ref<string[] | null>(null)

// 操作类型选项（按角色）
const actionOptions = computed(() => {
  const common = [
    { value: '', label: '全部' },
    { value: 'task_push', label: '数据推送' },
    { value: 'device_online', label: '设备上线' },
    { value: 'device_offline', label: '设备离线' },
  ]
  if (role.value === 'admin') {
    common.push(
      { value: 'LOGIN', label: '用户登录' },
      { value: 'CREATE_USER', label: '创建用户' },
      { value: 'UPDATE_CONFIG', label: '修改配置' },
    )
  } else if (role.value === 'user') {
    common.push(
      { value: 'CREATE_USER', label: '创建操作员' },
      { value: 'UPDATE_CONFIG', label: '修改配置' },
    )
  }
  return common
})

const expandedId = ref<number | null>(null)
const expandedItem = computed(() => items.value.find(i => i.id === expandedId.value))

async function fetchData() {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize,
    }
    if (filterAction.value) params.action = filterAction.value
    if (filterMac.value) params.mac = filterMac.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0] + ' 00:00:00'
      params.end_time = dateRange.value[1] + ' 23:59:59'
    }
    const res: any = await getOperationLogs(params)
    if (res?.items) {
      items.value = res.items ?? []
      total.value = res.total ?? 0
    }
  } catch (e) {
    console.error('加载操作记录失败:', e)
  } finally {
    loading.value = false
  }
}

async function fetchPage(p: number) {
  page.value = p
  expandedId.value = null
  await fetchData()
}

async function toggleExpand(row: LogItem) {
  expandedId.value = row.id
  pushDetailDevices.value = []
  detailDialogVisible.value = true

  // 推送类型：加载推送明细
  if (row.action === 'task_push' && row.target_id) {
    try {
      const res: any = await getPushLogs({
        task_id: Number(row.target_id),
        page_size: 100,
      })
      if (res?.items) {
        pushDetailDevices.value = res.items ?? []
      }
    } catch (e) {
      console.error('加载推送明细失败:', e)
    }
  }
}

function actionTagType(action: string): string {
  const map: Record<string, string> = {
    task_push: 'primary',
    batch_update_template: 'primary',
    device_online: 'success',
    device_offline: 'danger',
    LOGIN: '',
    LOGIN_FAILED: 'warning',
    CREATE_USER: 'info',
    UPDATE_CONFIG: 'info',
  }
  return map[action] || 'info'
}

function resultLabel(r: string): string {
  const map: Record<string, string> = { pending: '等待', sent: '已发', success: '成功', failed: '失败' }
  return map[r] || r
}

function rowClassName({ row }: { row: LogItem }): string {
  return row.id === expandedId.value ? 'expanded-row' : ''
}

function formatTime(t: string): string {
  try {
    const d = new Date(t)
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    const s = String(d.getSeconds()).padStart(2, '0')
    return `${m}-${day} ${h}:${min}:${s}`
  } catch { return t }
}

onMounted(() => fetchData())
</script>

<style scoped>
.oplog-page {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;

  h1 {
    font-size: 18px;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 4px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  p {
    font-size: 13px;
    color: #64748b;
    margin: 0;
  }
}

.filter-bar {
  background: white;
  border-radius: 12px;
  padding: 14px 18px;
  border: 1px solid #e2e8f0;
  .filter-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
}

.log-content { min-height: 300px; }

.state-card {
  background: white;
  border-radius: 14px;
  padding: 24px;
  border: 1px solid #e2e8f0;
}
.empty-state {
  text-align: center;
  padding: 50px 20px;
  .empty-icon-wrap {
    width: 72px; height: 72px; border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
    color: #6366f1; margin: 0 auto 16px;
  }
  h3 { font-size: 16px; color: #334155; margin: 0 0 6px; }
  p { font-size: 13.5px; color: #94a3b8; margin: 0; }
}

.log-table-wrap {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.time-cell {
  font-size: 13px;
  color: #64748b;
  font-family: ui-monospace, monospace;
}

.user-cell {
  font-size: 13px;
  color: #374151;
}

.target-cell {
  font-size: 13px;
  color: #1e293b;
  .target-sub {
    color: #94a3b8;
    font-size: 12px;
    margin-left: 4px;
  }
  code {
    font-family: ui-monospace, monospace;
    font-size: 12px;
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 4px;
    color: #475569;
  }
}

.result-dot {
  display: inline-block;
  width: 8px; height: 8px; border-radius: 50%;
  &.success { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.35); }
  &.fail { background: #ef4444; box-shadow: 0 0 6px rgba(239,68,68,0.35); }
}

.text-success { color: #22c55e; }
.text-danger { color: #ef4444; }
.text-muted { color: #94a3b8; }

/* 展开详情 */
.expand-panel {
  margin: 12px 16px 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  .expand-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    .expand-title {
      font-weight: 600;
      font-size: 14px;
      color: #1e293b;
    }
  }
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.detail-field {
  label {
    display: block;
    font-size: 11px;
    color: #94a3b8;
    margin-bottom: 2px;
  }
  span {
    font-size: 13px;
    color: #1e293b;
  }
  code {
    font-family: ui-monospace, monospace;
    font-size: 12px;
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 4px;
  }
}

.push-device-list {
  margin-top: 14px;
  h4 {
    font-size: 13px;
    font-weight: 600;
    color: #475569;
    margin: 0 0 8px;
  }
}

.push-data-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  .data-tag {
    font-size: 11px;
  }
}

.detail-raw {
  pre {
    font-size: 12px;
    color: #475569;
    background: #f1f5f9;
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 0;
  }
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

/* 弹窗响应式 */
@media (max-width: 768px) {
  .detail-dialog {
    :deep(.el-dialog) {
      width: 92% !important;
      margin-top: 10vh !important;
    }
    :deep(.el-dialog__body) {
      padding: 12px 16px;
    }
    .detail-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

:deep(.expanded-row) {
  background: rgba(99, 102, 241, 0.04) !important;
  cursor: pointer;
}
:deep(.el-table__row) {
  cursor: pointer;
}
</style>
