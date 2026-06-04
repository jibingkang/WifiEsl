<template>
  <div class="device-events-page">
    <!-- 头部 -->
    <header class="page-header">
      <div>
        <h1><Activity :size="22" /> 设备事件</h1>
        <p>设备在线/离线、按键、回执等状态变化记录</p>
      </div>
    </header>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select v-model="filterEventType" placeholder="事件类型" clearable size="default" style="width: 150px" @change="fetchData">
          <el-option v-for="opt in eventTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
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
    <div class="events-content">
      <div v-if="loading" class="state-card">
        <el-skeleton :rows="6" animated />
      </div>

      <div v-else-if="items.length === 0" class="state-card empty-state">
        <div class="empty-icon-wrap"><Activity :size="40" /></div>
        <h3>暂无事件记录</h3>
        <p>设备状态变化后，记录会显示在这里</p>
      </div>

      <!-- 时间线 -->
      <div v-else class="timeline-list">
        <div v-for="item in items" :key="item.id" class="ev-item" @click="toggleDetail(item)">
          <div class="ev-marker" :class="markerClass(item.event_type)" />
          <div class="ev-body">
            <div class="ev-header">
              <span class="ev-mac"><code>{{ item.mac }}</code></span>
              <el-tag :type="tagType(item.event_type)" size="small" effect="dark" round>
                {{ eventLabel(item.event_type) }}
              </el-tag>
              <span class="ev-time">{{ formatTime(item.created_at) }}</span>
            </div>
            <!-- 展开详情 -->
            <Transition name="detail-expand">
              <div v-if="expandedId === item.id && item.payload" class="ev-detail">
                <div class="detail-fields">
                  <template v-for="(v, k) in displayPayload(item)" :key="k">
                    <div class="df-item">
                      <span class="df-key">{{ k }}</span>
                      <span class="df-val">{{ v }}</span>
                    </div>
                  </template>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>

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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Activity, Search } from 'lucide-vue-next'
import { getDeviceEventLogs } from '@/api/logs'

interface EventItem {
  id: number
  mac: string
  event_type: string
  payload?: any
  created_at: string
}

const loading = ref(false)
const items = ref<EventItem[]>([])
const page = ref(1)
const pageSize = 30
const total = ref(0)
const expandedId = ref<number | null>(null)
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null

const filterEventType = ref('')
const filterMac = ref('')
const dateRange = ref<string[] | null>(null)

const eventTypeOptions = [
  { value: '', label: '全部' },
  { value: 'online', label: '上线' },
  { value: 'offline', label: '离线' },
  { value: 'button', label: '按键' },
  { value: 'display_reply', label: '屏幕回执' },
  { value: 'battery_reply', label: '电量回复' },
  { value: 'led_reply', label: 'LED回执' },
]

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filterEventType.value) params.event_type = filterEventType.value
    if (filterMac.value) params.mac = filterMac.value
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_time = dateRange.value[0] + ' 00:00:00'
      params.end_time = dateRange.value[1] + ' 23:59:59'
    }
    const res: any = await getDeviceEventLogs(params)
    if (res?.items) {
      items.value = res.items ?? []
      total.value = res.total ?? 0
    }
  } catch (e) {
    console.error('加载设备事件失败:', e)
  } finally {
    loading.value = false
  }
}

async function fetchPage(p: number) {
  page.value = p
  expandedId.value = null
  await fetchData()
}

function toggleDetail(item: EventItem) {
  expandedId.value = expandedId.value === item.id ? null : item.id
}

function markerClass(type: string): string {
  if (type === 'online') return 'online'
  if (type === 'offline') return 'offline'
  if (type === 'button') return 'button'
  if (type === 'battery_reply') return 'battery'
  return 'default'
}

function tagType(type: string): string {
  const map: Record<string, string> = {
    online: 'success', offline: 'danger', button: 'warning',
    display_reply: '', battery_reply: 'info', led_reply: 'info',
  }
  return map[type] || 'info'
}

function eventLabel(type: string): string {
  const map: Record<string, string> = {
    online: '上线', offline: '离线', button: '按键',
    display_reply: '屏幕回执', battery_reply: '电量回复',
    led_reply: 'LED回执', reboot_reply: '重启回执',
  }
  return map[type] || type
}

function displayPayload(item: EventItem): Record<string, any> {
  if (!item.payload || typeof item.payload !== 'object') return {}
  const p = { ...item.payload }
  // 隐藏冗余字段
  delete p.mac
  delete p.msgId
  return p
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

onMounted(() => {
  fetchData()
  // 每10秒自动刷新设备事件，回到第1页显示最新
  autoRefreshTimer = setInterval(() => {
    page.value = 1
    fetchData()
  }, 10000)
})

onBeforeUnmount(() => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
})
</script>

<style scoped>
.device-events-page {
  max-width: 900px;
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
    font-size: 18px; font-weight: 700; color: #1e293b; margin: 0 0 4px;
    display: flex; align-items: center; gap: 8px;
  }
  p { font-size: 13px; color: #64748b; margin: 0; }
}

.filter-bar {
  background: white;
  border-radius: 12px;
  padding: 14px 18px;
  border: 1px solid #e2e8f0;
  .filter-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
}

.events-content { min-height: 300px; }
.state-card { background: white; border-radius: 14px; padding: 24px; border: 1px solid #e2e8f0; }
.empty-state {
  text-align: center; padding: 50px 20px;
  .empty-icon-wrap {
    width: 72px; height: 72px; border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
    color: #6366f1; margin: 0 auto 16px;
  }
  h3 { font-size: 16px; color: #334155; margin: 0 0 6px; }
  p { font-size: 13.5px; color: #94a3b8; margin: 0; }
}

.timeline-list { display: flex; flex-direction: column; gap: 4px; }
.ev-item {
  display: flex; gap: 10px; padding: 10px 14px; border-radius: 10px;
  cursor: pointer; transition: all 0.15s ease;
  background: white; border: 1px solid #e2e8f0;
  &:hover { box-shadow: 0 2px 6px rgba(0,0,0,0.05); border-color: #cbd5e1; }
}
.ev-marker {
  width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0;
  &.online { background: #22c55e; box-shadow: 0 0 5px rgba(34,197,94,0.3); }
  &.offline { background: #ef4444; box-shadow: 0 0 5px rgba(239,68,68,0.3); }
  &.button { background: #f59e0b; box-shadow: 0 0 5px rgba(245,158,11,0.3); }
  &.battery { background: #3b82f6; box-shadow: 0 0 5px rgba(59,130,246,0.3); }
  &.default { background: #94a3b8; }
}
.ev-body { flex: 1; min-width: 0; }
.ev-header {
  display: flex; align-items: center; gap: 8px;
  .ev-mac code {
    font-family: ui-monospace, monospace; font-size: 12px;
    background: #f1f5f9; padding: 1px 6px; border-radius: 4px; color: #475569;
  }
  .ev-time {
    margin-left: auto; font-size: 12px; color: #94a3b8;
    font-family: ui-monospace, monospace;
  }
}

.ev-detail {
  margin-top: 8px; padding: 10px 12px; background: #f8fafc;
  border-radius: 8px; border: 1px solid #e2e8f0;
}
.detail-fields { display: flex; flex-wrap: wrap; gap: 6px 16px; }
.df-item {
  .df-key { font-size: 11px; color: #94a3b8; margin-right: 4px; }
  .df-val { font-size: 12px; color: #475569; }
}

.pagination-wrap { display: flex; justify-content: center; padding: 16px 0 8px; }

.detail-expand-enter-active { transition: all 0.2s ease; }
.detail-expand-leave-active { transition: all 0.15s ease; }
.detail-expand-enter-from, .detail-expand-leave-to { opacity: 0; max-height: 0; overflow: hidden; }
</style>
