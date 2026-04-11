<template>
  <div class="history-panel">
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="items.length === 0" class="empty-state">
      <el-empty description="暂无更新历史记录" :image-size="80" />
      <p class="empty-tip">执行批量推送后，记录会显示在这里</p>
    </div>

    <div v-else class="timeline">
      <div
        v-for="item in items"
        :key="item.id"
        class="tl-item"
        @click="toggleDetail(item.id)"
      >
        <div class="tl-marker" :class="item.result" />
        <div class="tl-body">
          <div class="tl-header">
            <span class="tl-title">{{ item.template_name || item.detail?.templateName || '未知模板' }}</span>
            <el-tag
              :type="item.result === 'success' ? 'success' : 'danger'"
              size="small"
              effect="dark"
              round
            >
              {{ item.result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </div>
          <div class="tl-meta">
            <span><Monitor :size="12" /> {{ item.detail?.deviceCount || '?' }} 台设备</span>
            <span><Clock :size="12" /> {{ formatTime(item.created_at) }}</span>
          </div>

          <!-- 展开详情 -->
          <Transition name="detail-expand">
            <div v-if="expandedId === item.id" class="tl-detail">
              <div v-if="item.detail?.devices" class="detail-devices">
                <div
                  v-for="d in item.detail.devices"
                  :key="d.mac"
                  class="dd-item"
                  :class="{ fail: !d.success }"
                >
                  <span class="dd-status">{{ d.success ? '✓' : '✗' }}</span>
                  <code>{{ d.mac }}</code>
                  <span class="dd-msg">{{ d.message || '' }}</span>
                </div>
              </div>
              <div class="detail-actions">
                <el-button type="primary" size="small" @click.stop="emitReuse(item)">
                  使用此配置重新推送
                </el-button>
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
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Monitor, Clock } from 'lucide-vue-next'
import { getUpdateHistory } from '@/api/template'

export interface HistoryItem {
  id: number
  username?: string
  action: string
  target_type?: string
  target_id?: string
  detail?: string
  result: string
  created_at: string
  // 解析后的
  template_name?: string
}

const emit = defineEmits<{
  reuse: [data: { tid: string; macs: string[]; defaultData: Record<string, any>; customOverrides: Record<string, Record<string, any>> }]
}>()

const loading = ref(false)
const items = ref<HistoryItem[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const expandedId = ref<number | null>(null)

async function fetchPage(p?: number) {
  if (p) page.value = p
  loading.value = true
  try {
    const res: any = await getUpdateHistory(page.value, pageSize)
    if (res?.data) {
      items.value = res.data.items ?? res.data ?? []
      total.value = res.data.total ?? items.value.length
      // 解析 detail JSON
      items.value.forEach((it: HistoryItem) => {
        if (typeof it.detail === 'string') {
          try { it.detail = JSON.parse(it.detail) } catch { /* ignore */ }
        }
      })
    }
  } catch (e) {
    console.error('加载历史失败:', e)
  } finally {
    loading.value = false
  }
}

function toggleDetail(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

function formatTime(t: string): string {
  try {
    const d = new Date(t)
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${m}-${day} ${h}:${min}`
  } catch { return t }
}

function emitReuse(item: HistoryItem) {
  const d = typeof item.detail === 'object' ? item.detail : {}
  emit('reuse', {
    tid: d.tid || '',
    macs: d.macs || [],
    defaultData: d.defaultData || {},
    customOverrides: d.customOverrides || {},
  })
}

onMounted(() => fetchPage())
</script>

<style scoped>
.history-panel { padding: 0 4px; }
.loading-state { padding: 40px 0; }

.empty-state { text-align: center; padding: 40px 0; }
.empty-tip { font-size: 13px; color: #94a3b8; margin: 8px 0 0; }

/* 时间线 */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.tl-item {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  &:hover {
    background: #f8fafc;
  }
}
.tl-marker {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 7px;
  flex-shrink: 0;
  &.success { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.3); }
  &.failure, &.error, &.fail { background: #ef4444; box-shadow: 0 0 6px rgba(239,68,68,0.3); }
}
.tl-body { flex: 1; min-width: 0; }

.tl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tl-title {
  font-size: 13.5px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}
.tl-meta {
  display: flex;
  gap: 12px;
  margin-top: 4px;
  font-size: 11.5px;
  color: #94a3b8;
  span { display: flex; align-items: center; gap: 3px; }
}

/* 详情展开 */
.tl-detail {
  margin-top: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.detail-devices {
  max-height: 180px;
  overflow-y: auto;
  margin-bottom: 10px;
}
.dd-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
  font-size: 11.5px;
  &.fail { .dd-status { color: #ef4444; } code { color: #ef4444; } }
  .dd-status { color: #22c55e; font-weight: 700; }
  code { font-family: ui-monospace, monospace; font-size: 11px; color: #475569; }
  .dd-msg { color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
.detail-actions { text-align: right; }

.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

/* 展开/收起动画 */
.detail-expand-enter-active { transition: all 0.25s ease; }
.detail-expand-leave-active { transition: all 0.18s ease; }
.detail-expand-enter-from, .detail-expand-leave-to { opacity: 0; max-height: 0; overflow: hidden; }
</style>
