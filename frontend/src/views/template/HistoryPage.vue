<template>
  <div class="history-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <div>
        <h1><Clock :size="22" /> 更新历史</h1>
        <p>查看所有模板推送记录，可复用历史配置重新推送</p>
      </div>
      <el-button type="primary" @click="$router.push('/template')">
        <Send :size="15" /> 返回数据更新
      </el-button>
    </header>

    <!-- 历史内容（复用 HistoryPanel 逻辑） -->
    <div class="history-content">
      <!-- 加载中 -->
      <div v-if="loading" class="state-card">
        <el-skeleton :rows="6" animated />
      </div>

      <!-- 空态 -->
      <div v-else-if="items.length === 0" class="state-card empty-state">
        <div class="empty-icon-wrap">
          <Clock :size="40" />
        </div>
        <h3>暂无更新记录</h3>
        <p>执行批量推送后，记录会显示在这里</p>
      </div>

      <!-- 时间线列表 -->
      <div v-else class="timeline-list">
        <div
          v-for="item in items"
          :key="item.id"
          class="tl-item"
          @click="toggleDetail(item.id)"
        >
          <div class="tl-marker" :class="item.result" />
          <div class="tl-body">
            <div class="tl-header">
              <span class="tl-title">{{ item.template_name || '未知模板' }}</span>
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
              <span><Monitor :size="12" /> {{ deviceCount(item) }} 台设备</span>
              <span><Clock :size="12" /> {{ formatTime(item.created_at) }}</span>
            </div>

            <!-- 展开详情 -->
            <Transition name="detail-expand">
              <div v-if="expandedId === item.id" class="tl-detail">
                <div v-if="getDevices(item).length > 0" class="detail-devices">
                  <div
                    v-for="d in getDevices(item)"
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
                  <el-button type="primary" size="small" @click.stop="reuseConfig(item)">
                    <RotateCcw :size="13" /> 使用此配置重新推送
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Monitor, Send, RotateCcw } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import { getUpdateHistory } from '@/api/template'

const router = useRouter()

interface HistoryItem {
  id: number
  username?: string
  action: string
  detail?: any // 可能是字符串或对象
  result: string
  created_at: string
  template_name?: string
}

const loading = ref(false)
const items = ref<HistoryItem[]>([])
const page = ref(1)
const pageSize = 12
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
      for (const it of items.value) {
        if (typeof it.detail === 'string') {
          try { it.detail = JSON.parse(it.detail) } catch { /* ignore */ }
        }
        // 提取模板名
        const d = typeof it.detail === 'object' ? it.detail : {}
        it.template_name = d.templateName || d.tname || ''
      }
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

function getDevices(item: HistoryItem): Array<{ mac: string; success: boolean; message?: string }> {
  return item.detail?.devices ?? []
}

function deviceCount(item: HistoryItem): number {
  return item.detail?.deviceCount || getDevices(item).length || '?'
}

/** 复用配置：保存到 localStorage 并跳转回数据更新页 */
function reuseConfig(item: HistoryItem) {
  const d = typeof item.detail === 'object' ? item.detail : {}
  try {
    localStorage.setItem('wifi_esl_reuse_config', JSON.stringify({
      tid: d.tid || '',
      macs: d.macs || [],
      defaultData: d.defaultData || {},
      customOverrides: d.customOverrides || {},
    }))
    ElMessage.info('已加载配置，正在跳转...')
    router.push('/template')
  } catch (e) {
    ElMessage.error('复用配置失败')
  }
}

onMounted(() => fetchPage())
</script>

<style scoped>
.history-page {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 页面头部 */
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

/* 内容区 */
.history-content {
  min-height: 300px;
}
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
    width: 72px;
    height: 72px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
    color: #6366f1;
    margin: 0 auto 16px;
  }
  h3 {
    font-size: 16px;
    color: #334155;
    margin: 0 0 6px;
  }
  p {
    font-size: 13.5px;
    color: #94a3b8;
    margin: 0;
  }
}

/* 时间线 */
.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tl-item {
  display: flex;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
  border: 1px solid #e2e8f0;

  &:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-color: #cbd5e1;
  }
}
.tl-marker {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 7px;
  flex-shrink: 0;
  &.success { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.35); }
  &.failure, &.error, &.fail { background: #ef4444; box-shadow: 0 0 6px rgba(239,68,68,0.35); }
}
.tl-body { flex: 1; min-width: 0; }

.tl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tl-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}
.tl-meta {
  display: flex;
  gap: 16px;
  margin-top: 5px;
  font-size: 12px;
  color: #94a3b8;
  span { display: flex; align-items: center; gap: 3px; }
}

/* 详情展开 */
.tl-detail {
  margin-top: 12px;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}
.detail-devices {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 10px;
}
.dd-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 0;
  font-size: 12px;
  &.fail { .dd-status { color: #ef4444; } code { color: #ef4444; } }
  .dd-status { color: #22c55e; font-weight: 700; }
  code { font-family: ui-monospace, monospace; font-size: 11px; color: #475569; }
  .dd-msg { color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
.detail-actions { text-align: right; }

/* 分页 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 20px 0 10px;
}

/* 展开/收起动画 */
.detail-expand-enter-active { transition: all 0.25s ease; }
.detail-expand-leave-active { transition: all 0.18s ease; }
.detail-expand-enter-from, .detail-expand-leave-to { opacity: 0; max-height: 0; overflow: hidden; }
</style>
