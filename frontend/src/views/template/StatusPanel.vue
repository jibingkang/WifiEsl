<template>
  <div class="status-panel">
    <!-- 准备状态 -->
    <div v-if="!executing && results.length === 0" class="state-ready">
      <div class="ready-icon">
        <Send :size="32" />
      </div>
      <h3>准备就绪</h3>
      <p>模板「{{ templateName || '未选择' }}」</p>
      <p class="ready-devices">
        <Smartphone /> {{ deviceMacs.length }} 台设备待推送
      </p>

      <el-button
        v-if="deviceMacs.length > 0"
        type="primary"
        size="large"
        round
        class="start-btn"
        @click="$emit('start')"
      >
        开始推送
      </el-button>
    </div>

    <!-- 执行中 -->
    <div v-else-if="executing" class="state-running">
      <div class="running-header">
        <Loader2 class="spin-icon" :size="20" />
        <span>正在推送...</span>
      </div>

      <div class="progress-bar-wrap">
        <el-progress
          :percentage="progress"
          :stroke-width="16"
          :show-text="true"
          :format="(p: number) => `${p}%`"
          color="#6366f1"
        />
      </div>

      <div class="result-summary-mini">
        <span class="s-ok">✓ {{ succCount }}</span>
        <span class="s-fail">✗ {{ failCount }}</span>
        <span class="s-total">/ {{ total }}</span>
      </div>

      <!-- 实时结果流 -->
      <div class="live-results">
        <TransitionGroup name="slide-in" tag="div" class="results-list">
          <div
            v-for="r in results.slice(-20).reverse()"
            :key="r.mac + r.status + results.indexOf(r)"
            class="lr-item"
            :class="{ ok: r.status === 'success', err: r.status === 'error' }"
          >
            <span class="lr-dot" />
            <code class="lr-mac">{{ r.mac }}</code>
            <span class="lr-msg">{{ r.message }}</span>
          </div>
        </TransitionGroup>
      </div>
    </div>

    <!-- 完成状态 -->
    <div v-else class="state-done">
      <div class="done-icon" :class="{ allOk: failCount === 0 }">
        <CheckCircle v-if="failCount === 0" :size="36" />
        <AlertTriangle v-else :size="36" />
      </div>
      <h3>{{ failCount === 0 ? '全部成功' : '部分失败' }}</h3>

      <div class="done-stats">
        <div class="ds-item total">
          <span class="ds-num">{{ total }}</span>
          <span class="ds-lbl">总计</span>
        </div>
        <div class="ds-item ok">
          <span class="ds-num">{{ succCount }}</span>
          <span class="ds-lbl">成功</span>
        </div>
        <div class="ds-item fail">
          <span class="ds-num">{{ failCount }}</span>
          <span class="ds-lbl">失败</span>
        </div>
      </div>

      <div v-if="failCount > 0" class="fail-list">
        <p class="fail-title">失败设备:</p>
        <div v-for="r in results.filter(r => r.status === 'error')" :key="r.mac" class="fail-item">
          <code>{{ r.mac }}</code>: {{ r.message }}
        </div>
      </div>

      <div class="done-actions">
        <el-button
          v-if="failCount > 0"
          type="warning"
          size="small"
          plain
          @click="$emit('retry')"
        >
          重试失败的
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Send, Smartphone, Loader2, CheckCircle, AlertTriangle } from 'lucide-vue-next'

const props = defineProps<{
  templateName: string
  deviceMacs: string[]
  executing: boolean
  progress: number
  results: Array<{ mac: string; status: 'success' | 'error'; message?: string }>
}>()

defineEmits<{
  start: []
  retry: []
}>()

const total = computed(() => props.deviceMacs.length)
const succCount = computed(() => props.results.filter(r => r.status === 'success').length)
const failCount = computed(() => props.results.filter(r => r.status === 'error').length)
</script>

<style scoped>
.status-panel {
  background: white;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
  height: fit-content;
  position: sticky;
  top: 0;
}

/* 准备状态 */
.state-ready {
  text-align: center;
  padding: 16px 0;
}
.ready-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.08));
  color: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
}
.state-ready h3 {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}
.state-ready p {
  font-size: 13px;
  color: #64748b;
  margin: 2px 0;
}
.ready-devices {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 14px !important;
  color: #475569 !important;
  margin-top: 10px !important;
}
.start-btn {
  margin-top: 18px;
  width: 80%;
  border-radius: 10px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  font-weight: 600;
}

/* 执行中 */
.state-running {
  padding: 4px 0;
}
.running-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 14px;
}
.spin-icon {
  animation: spin 1s linear infinite;
  color: #6366f1;
}
@keyframes spin { to { transform: rotate(360deg); } }

.progress-bar-wrap { margin-bottom: 12px; }

.result-summary-mini {
  display: flex;
  gap: 12px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 14px;
  .s-ok { color: #22c55e; }
  .s-fail { color: #ef4444; }
  .s-total { color: #94a3b8; }
}

.live-results {
  max-height: 280px;
  overflow-y: auto;
}
.results-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.lr-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 12px;
  &.ok { background: rgba(34,197,94,0.06); border-left: 3px solid #22c55e; }
  &.err { background: rgba(239,68,68,0.06); border-left: 3px solid #ef4444; }
}
.lr-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  .ok & { background: #22c55e; }
  .err & { background: #ef4444; }
}
.lr-mac {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 11px;
  color: #475569;
}
.lr-msg {
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 完成状态 */
.state-done {
  text-align: center;
  padding: 12px 0;
}
.done-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
  background: rgba(239,68,68,0.08);
  color: #ef4444;
  &.allOk { background: rgba(34,197,94,0.08); color: #22c55e; }
}
.state-done h3 {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 14px;
}

.done-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 16px;
}
.ds-item { text-align: center; }
.ds-num { display: block; font-size: 26px; font-weight: 700; }
.ds-lbl { font-size: 12px; color: #94a3b8; }
.ds-item.ok .ds-num { color: #22c55e; }
.ds-item.fail .ds-num { color: #ef4444; }
.ds-item.total .ds-num { color: #6366f1; }

.fail-list {
  text-align: left;
  background: #fef2f2;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 14px;
  max-height: 150px;
  overflow-y: auto;
}
.fail-title {
  font-size: 12px;
  font-weight: 600;
  color: #dc2626;
  margin: 0 0 8px;
}
.fail-item {
  font-size: 11.5px;
  color: #7f1d1d;
  padding: 3px 0;
  code { color: #dc2626; }
}

.done-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
}

/* 动画 */
.slide-in-enter-active { transition: all 0.35s ease; }
.slide-in-enter-from { opacity: 0; transform: translateX(-16px); }
</style>
