<template>
  <div class="history-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div>
        <h1><Clock :size="22" /> 更新历史</h1>
        <p>查看每台设备的推送记录：谁、什么时候、更新了什么内容、是否成功</p>
      </div>
      <div class="header-actions">
        <el-button size="default" @click="$router.push('/logs/operations')">
          <ClipboardList :size="15" /> 查看全部操作记录
        </el-button>
        <el-button type="primary" @click="$router.push('/template')">
          <Send :size="15" /> 返回数据更新
        </el-button>
      </div>
    </header>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="filterMac"
        placeholder="设备 MAC"
        clearable
        size="default"
        style="width: 200px"
        @clear="search"
        @keyup.enter="search"
      />
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        size="default"
        value-format="YYYY-MM-DD"
        @change="search"
      />
      <el-select v-model="filterResult" placeholder="推送结果" clearable size="default" style="width: 120px" @change="search">
        <el-option label="全部" value="" />
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failed" />
        <el-option label="已发送" value="sent" />
      </el-select>
      <el-button type="primary" size="default" @click="search">
        <Search :size="14" /> 查询
      </el-button>
      <span class="filter-summary" v-if="total > 0">共 {{ total }} 条记录</span>
    </div>

    <!-- 表格 -->
    <div class="table-wrap">
      <div v-if="loading" class="state-card">
        <el-skeleton :rows="8" animated />
      </div>

      <div v-else-if="items.length === 0" class="state-card empty-state">
        <div class="empty-icon-wrap"><Send :size="40" /></div>
        <h3>暂无推送记录</h3>
        <p>执行数据推送后，每台设备的记录会显示在这里</p>
      </div>

      <el-table
        v-else
        :data="items"
        size="default"
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: 600, fontSize: '13px' }"
        row-class-name="push-row"
      >
        <!-- 设备MAC -->
        <el-table-column prop="mac" label="设备 MAC" width="175">
          <template #default="{ row }">
            <code class="mac-code">{{ row.mac }}</code>
          </template>
        </el-table-column>

        <!-- 设备名称（从 WIFI 系统设备列表获取，与数据更新页面一致） -->
        <el-table-column label="名称" width="110" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="device-name-cell">{{ getDeviceName(row.mac) || '-' }}</span>
          </template>
        </el-table-column>

        <!-- 操作者 (operator 隐藏) -->
        <el-table-column v-if="role !== 'operator'" prop="username" label="操作者" width="90" align="center">
          <template #default="{ row }">
            <span class="op-user">{{ row.username }}</span>
          </template>
        </el-table-column>

        <!-- 模板 -->
        <el-table-column prop="template_name" label="模板" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="template-name">{{ row.template_name || '-' }}</span>
          </template>
        </el-table-column>

        <!-- 更新内容 -->
        <el-table-column label="更新内容" min-width="180">
          <template #default="{ row }">
            <span v-if="row.push_data && Object.keys(row.push_data).length > 0" class="push-data-tags">
              <span
                v-for="(v, k) in row.push_data"
                :key="k"
                class="data-tag"
                :title="`${k}: ${v}`"
              >{{ k }}: {{ v }}</span>
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <!-- 发送时间 -->
        <el-table-column label="发送时间" width="145" align="center">
          <template #default="{ row }">
            <span class="time-cell">{{ formatTime(row.sent_at) }}</span>
          </template>
        </el-table-column>

        <!-- 完成时间 -->
        <el-table-column label="完成时间" width="145" align="center">
          <template #default="{ row }">
            <span v-if="row.replied_at" class="time-cell done">{{ formatTime(row.replied_at) }}</span>
            <span v-else class="time-cell waiting">等待回执</span>
          </template>
        </el-table-column>

        <!-- 结果 -->
        <el-table-column label="结果" width="85" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.result === 'success' ? 'success' : row.result === 'failed' ? 'danger' : 'warning'"
              size="small"
              effect="plain"
            >
              {{ resultLabel(row.result) }}
            </el-tag>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Clock, Send, Search, ClipboardList } from 'lucide-vue-next'
import { getPushLogs } from '@/api/logs'
import { useAuthStore } from '@/stores/auth'
import { useDeviceStore } from '@/stores/device'

const authStore = useAuthStore()
const deviceStore = useDeviceStore()
const role = computed(() => authStore.getUserRole())

interface PushRecord {
  id: number
  mac: string
  task_id: number
  template_name: string
  template_id: string
  username: string
  user_id: number
  push_data: Record<string, any> | null
  result: string
  sent_at: string
  replied_at: string | null
}

/** 从设备店获取设备名称（与数据更新页面一致） */
function getDeviceName(mac: string): string {
  const d = deviceStore.devices.find((d: any) => d.mac === mac)
  return d?.name || ''
}

const loading = ref(false)
const items = ref<PushRecord[]>([])
const page = ref(1)
const pageSize = 15
const total = ref(0)

// 筛选
const filterMac = ref('')
const dateRange = ref<string[] | null>(null)
const filterResult = ref('')

function resultLabel(r: string): string {
  const map: Record<string, string> = { sent: '已发送', success: '成功', failed: '失败', pending: '等待' }
  return map[r] || r
}

function formatTime(t: string | null): string {
  if (!t) return '-'
  try {
    const d = new Date(t)
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    const s = String(d.getSeconds()).padStart(2, '0')
    return `${m}-${day} ${h}:${min}:${s}`
  } catch {
    return t
  }
}

async function search() {
  page.value = 1
  await fetchData()
}

async function fetchData() {
  loading.value = true
  const params: any = {
    page: page.value,
    page_size: pageSize,
  }
  if (filterMac.value) params.mac = filterMac.value
  if (filterResult.value) params.result = filterResult.value
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_time = dateRange.value[0] + ' 00:00:00'
    params.end_time = dateRange.value[1] + ' 23:59:59'
  }

  const res: any = await getPushLogs(params).catch((e: Error) => {
    console.error('加载推送历史失败:', e)
    return null
  })

  if (res?.items) {
    items.value = res.items ?? []
    total.value = res.total ?? 0
  } else {
    items.value = []
    total.value = 0
  }
  loading.value = false
}

async function fetchPage(p: number) {
  page.value = p
  await fetchData()
}

onMounted(async () => {
  // 确保设备列表已加载（用于获取设备名称）
  if (deviceStore.devices.length === 0) {
    await deviceStore.fetchDevices().catch(() => {})
  }
  fetchData()
})
</script>

<style scoped>
.history-page {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}
.page-header h1 {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.page-header p {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 8px;
}

/* 筛选栏 */
.filter-bar {
  background: white;
  border-radius: 12px;
  padding: 12px 18px;
  border: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.filter-summary {
  margin-left: auto;
  font-size: 13px;
  color: #64748b;
}

/* 表格容器 */
.table-wrap {
  background: white;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}
.push-row {
  cursor: default;
}

/* MAC 样式 */
.mac-code {
  font-family: 'SF Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 12.5px;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 5px;
  color: #334155;
  letter-spacing: 0.3px;
}

/* 设备名称 */
.device-name-cell {
  font-size: 13px;
  color: #334155;
}

/* 操作者 */
.op-user {
  font-size: 13px;
  color: #475569;
  font-weight: 500;
}

/* 模板名 */
.template-name {
  font-size: 13px;
  color: #334155;
}

/* 推送内容 tags */
.push-data-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
}
.data-tag {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #eef2ff;
  color: #4338ca;
  border: 1px solid #c7d2fe;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 时间 */
.time-cell {
  font-family: ui-monospace, 'SF Mono', monospace;
  font-size: 12.5px;
  color: #475569;
  white-space: nowrap;
}
.time-cell.waiting {
  color: #94a3b8;
  font-style: italic;
  font-family: inherit;
  font-size: 12px;
}
.time-cell.done {
  color: #065f46;
}

.text-muted {
  color: #94a3b8;
  font-size: 12px;
}

/* 空状态 & 加载 */
.state-card {
  padding: 24px;
}
.empty-state {
  text-align: center;
  padding: 60px 20px;
}
.empty-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.06));
  color: #6366f1;
  margin: 0 auto 16px;
}
.empty-state h3 {
  font-size: 16px;
  color: #334155;
  margin: 0 0 6px;
}
.empty-state p {
  font-size: 13.5px;
  color: #94a3b8;
  margin: 0;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 18px 0 12px;
}
</style>
