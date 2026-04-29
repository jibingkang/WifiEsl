<template>
  <div class="monitor-view">
    <!-- 第一行：核心指标 + 在线率 -->
    <div class="row row-top">
      <div class="panel panel-stats">
        <div class="stat-grid">
          <div v-for="(item, idx) in topStats" :key="idx" class="stat-card-m">
            <div class="sc-label">{{ item.label }}</div>
            <div class="sc-value" :class="item.colorClass">{{ animatedValues[idx] ?? item.value }}</div>
          </div>
        </div>
      </div>

      <div class="panel panel-rate">
        <div class="panel-title">在线率</div>
        <div class="rate-circle-wrap">
          <svg viewBox="0 0 120 120" class="rate-svg">
            <circle cx="60" cy="60" r="52" fill="none" class="rate-bg-circle" stroke-width="10" />
            <circle
              cx="60" cy="60" r="52"
              fill="none"
              stroke="url(#rateGrad)"
              stroke-width="10"
              stroke-linecap="round"
              :stroke-dasharray="`${onlineRate * 3.27} 327`"
              transform="rotate(-90 60 60)"
            />
            <defs>
              <linearGradient id="rateGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#22c55e" />
                <stop offset="100%" stop-color="#4ade80" />
              </linearGradient>
            </defs>
          </svg>
          <div class="rate-text">{{ onlineRate }}%</div>
        </div>
      </div>
    </div>

    <!-- 第二行：设备状态列表 + 实时事件流 -->
    <div class="row row-middle">
      <div class="panel panel-devices">
        <div class="panel-header">
          <span class="panel-title">设备实时状态</span>
          <span class="live-badge"><span class="blink" /> LIVE</span>
        </div>
        <div class="device-grid">
          <TransitionGroup name="device-list" tag="div" class="device-list-inner">
            <div
              v-for="dev in deviceList"
              :key="dev.mac"
              class="device-chip"
              :class="{ online: dev.online, offline: !dev.online }"
            >
              <span class="chip-dot" />
              <span class="chip-name">{{ dev.name }}</span>
              <code class="chip-mac">{{ dev.mac }}</code>
              <span class="chip-volt">{{ dev.voltage != null ? formatVoltage(dev.voltage) : '--' }}</span>
            </div>
          </TransitionGroup>
        </div>
      </div>

      <div class="panel panel-events">
        <div class="panel-header">
          <span class="panel-title">实时事件流</span>
          <span class="live-badge"><span class="blink" /> LIVE</span>
        </div>
        <div class="event-stream">
          <TransitionGroup name="event-slide" tag="div">
            <div
              v-for="event in eventStream"
              :key="event.id"
              class="event-item"
              :class="`type-${event.type}`"
            >
              <span class="ev-time">{{ event.time }}</span>
              <span class="ev-msg">{{ event.message }}</span>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </div>

    <!-- 第三行：信号分布 + 告警信息 -->
    <div class="row row-bottom">
      <div class="panel panel-signal">
        <div class="panel-title">信号强度分布</div>
        <div class="signal-bars" v-if="signalData.length > 0">
          <div
            v-for="(sig, i) in signalData"
            :key="i"
            class="bar-item"
          >
            <div class="bar-fill" :style="{ height: sig.height, background: sig.color }">
              <span class="bar-val">{{ sig.count }}台</span>
            </div>
            <span class="bar-label">{{ sig.label }}</span>
          </div>
        </div>
      </div>

      <div class="panel panel-alerts">
        <div class="panel-header">
          <span class="panel-title">告警信息</span>
          <el-tag size="small" type="danger" effect="dark">{{ alertCount }} 条</el-tag>
        </div>
        <div class="alert-list" v-if="alertCount > 0">
          <div
            v-for="alert in alerts"
            :key="alert.id"
            class="alert-item"
          >
            <el-icon :size="14" color="#ef4444"><WarningFilled /></el-icon>
            <span class="al-text">{{ alert.message }}</span>
            <span class="al-time">{{ alert.time }}</span>
          </div>
        </div>
        <div v-else class="no-alert">暂无告警</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'
import { useDeviceStore } from '@/stores/device'
import { formatVolt, formatVoltage } from '@/utils/format'

const deviceStore = useDeviceStore()

// 核心统计
const topStats = computed(() => [
  { label: '总设备数', value: String((deviceStore.devices ?? []).length || 0), colorClass: 'text-blue' },
  { label: '在线数', value: String(deviceStore.onlineCount || 0), colorClass: 'text-green' },
  { label: '离线数', value: String(deviceStore.offlineCount || 0), colorClass: 'text-red' },
  { label: '低电量', value: String(deviceStore.lowBatteryDevices?.length || 0), colorClass: 'text-yellow' },
  { label: '弱信号', value: String(deviceStore.weakSignalDevices?.length || 0), colorClass: 'text-orange' },
])

const animatedValues = ref<string[]>([])

const onlineRate = computed(() => {
  const devs = deviceStore.devices ?? []
  if (!devs.length) return 0
  return ((deviceStore.onlineCount / devs.length) * 100).toFixed(1)
})

// 设备网格数据 (模拟)
const deviceList = ref<Array<{ mac: string; name: string; online: boolean; voltage?: number }>>([])

// 事件流
interface EventItem { id: number; time: string; message: string; type: string }
let eventIdCounter = 0
const eventStream = ref<EventItem[]>([])
const maxEvents = 30

function pushEvent(message: string, type: string) {
  const now = new Date().toLocaleTimeString('zh-CN')
  eventStream.value.unshift({ id: ++eventIdCounter, time: now, message, type })
  if (eventStream.value.length > maxEvents) eventStream.value.pop()
}

// 信号分布
const signalData = computed(() => {
  const devs = deviceStore.devices ?? []
  return [
    { label: '优秀\n>-50dBm', count: devs.filter(d => d.rssi != null && d.rssi >= -50).length, height: '40%', color: '#22c55e' },
    { label: '良好\n-60dBm', count: devs.filter(d => d.rssi != null && d.rssi >= -60 && d.rssi < -50).length, height: '65%', color: '#4ade80' },
    { label: '一般\n-70dBm', count: devs.filter(d => d.rssi != null && d.rssi >= -70 && d.rssi < -60).length, height: '45%', color: '#f59e0b' },
    { label: '弱\n<-70dBm', count: devs.filter(d => d.rssi != null && d.rssi < -70).length, height: '22%', color: '#ef4444' },
  ]
})

// 告警
const alerts = ref<Array<{ id: number; message: string; time: string }>>([])
const alertCount = computed(() => alerts.value.length)

// 定时刷新
let refreshTimer: ReturnType<typeof setInterval> | null = null

async function refresh() {
  await deviceStore.fetchDevices()

  // 更新动画值
  animatedValues.value = topStats.value.map(s => s.value)

  // 构建设备网格
  const devs = deviceStore.devices ?? []
  deviceList.value = devs.slice(0, 30).map(d => ({
    mac: d.mac,
    name: d.name || d.mac,
    online: d.is_online,
    voltage: d.voltage,
  }))

  // 模拟事件推送 (实际由MQTT触发)
  if (Math.random() > 0.7) {
    const onlineDev = devs.find(d => d.is_online)
    if (onlineDev) {
      const events = [`设备 ${onlineDev.mac} 状态正常`, `心跳: ${onlineDev.mac}`, `电量查询: ${onlineDev.mac} → ${formatVolt(onlineDev.voltage)}`]
      pushEvent(events[Math.floor(Math.random() * events.length)], 'info')
    }
  }

  // 更新告警
  const lowBat = deviceStore.lowBatteryDevices.slice(0, 5)
  alerts.value = lowBat.map((d, i) => ({
    id: i,
    message: `${d.mac}${d.name ? ` (${d.name})` : ''} 电量过低 (${formatVoltage(d.voltage)})`,
    time: new Date().toLocaleTimeString('zh-CN'),
  }))
}

onMounted(async () => {
  await refresh()
  refreshTimer = setInterval(refresh, 5000) // 每5秒刷新
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style lang="scss" scoped>
/* ========== 监控看板整体布局 ========== */
.monitor-view {
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: calc(100vh - 52px);
}

.row {
  display: flex;
  gap: 14px;

  &-top { height: 160px; }
  &-middle { flex: 1; min-height: 300px; }
  &-bottom { height: 220px; }
}

/* ========== 面板基础样式 ========== */
.panel {
  background: var(--monitor-panel-bg, linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95)));
  border: 1px solid var(--monitor-panel-border, rgba(99,102,241,0.12));
  border-radius: 14px;
  padding: 16px 18px;
  backdrop-filter: blur(8px);
  transition: background 0.3s ease, border-color 0.3s ease;

  .panel-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--monitor-text-secondary, #94a3b8);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

/* 浅色模式面板 */
html:not(.dark) .panel {
  --monitor-panel-bg: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(248,250,252,0.98));
  --monitor-panel-border: rgba(99,102,241,0.1);
  --monitor-panel-shadow: 0 1px 3px rgba(0,0,0,0.06);

  .panel-title {
    --monitor-text-secondary: #64748b;
  }
}

html.dark .panel {
  --monitor-panel-bg: linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));
  --monitor-panel-border: rgba(99,102,241,0.12);

  .panel-title {
    --monitor-text-secondary: #94a3b8;
  }
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .panel-title { margin-bottom: 0; }
}

.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 700;
  color: #ef4444;
  background: rgba(239,68,68,0.1);
  padding: 2px 10px;
  border-radius: 10px;
  letter-spacing: 1px;

  .blink {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #ef4444;
    animation: blink 1.2s infinite;
  }
}

html:not(.dark) .live-badge {
  background: rgba(239,68,68,0.06);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.15; }
}

/* ========== 顶部统计面板 ========== */
.panel-stats {
  flex: 1;
  display: flex;
  align-items: center;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  width: 100%;
}

.stat-card-m {
  text-align: center;
  .sc-label { font-size: 13px; color: var(--monitor-text-muted, #64748b); margin-bottom: 6px; }
  .sc-value {
    font-size: 32px;
    font-weight: 800;
    font-family: 'DIN Alternate', sans-serif;
    &.text-blue { color: var(--monitor-blue, #60a5fa); }
    &.text-green { color: var(--monitor-green, #4ade80); }
    &.text-red { color: var(--monitor-red, #f87171); }
    &.text-yellow { color: var(--monitor-yellow, #fbbf24); }
    &.text-orange { color: var(--monitor-orange, #fb923c); }
  }
}

html:not(.dark) .stat-card-m {
  --monitor-text-muted: #64748b;
  --monitor-blue: #3b82f6;
  --monitor-green: #16a34a;
  --monitor-red: #dc2626;
  --monitor-yellow: #ca8a04;
  --monitor-orange: #ea580c;
}

html.dark .stat-card-m {
  --monitor-text-muted: #64748b;
  --monitor-blue: #60a5fa;
  --monitor-green: #4ade80;
  --monitor-red: #f87171;
  --monitor-yellow: #fbbf24;
  --monitor-orange: #fb923c;
}

.panel-rate {
  width: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  .rate-circle-wrap {
    position: relative;
    width: 110px;
    height: 110px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .rate-svg { width: 110px; height: 110px; }
  .rate-bg-circle { stroke: var(--monitor-rate-bg, #1e293b); }
  .rate-text {
    position: absolute;
    font-size: 26px;
    font-weight: 800;
    color: var(--monitor-green, #4ade80);
    font-family: 'DIN Alternate', sans-serif;
  }
}

html:not(.dark) .panel-rate .rate-text {
  --monitor-green: #16a34a;
}

html.dark .panel-rate .rate-text {
  --monitor-green: #4ade80;
}

html:not(.dark) .rate-bg-circle {
  --monitor-rate-bg: #e2e8f0;
}

html.dark .rate-bg-circle {
  --monitor-rate-bg: #1e293b;
}

/* ========== 设备网格 ========== */
.panel-devices { flex: 1.5; display: flex; flex-direction: column; overflow: hidden; }
.device-grid {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.device-list-inner {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.device-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 9px;
  background: var(--monitor-chip-bg, rgba(255,255,255,0.03));
  border: 1px solid transparent;
  transition: all 0.2s;

  &.online { border-color: rgba(34,197,94,0.2); }
  &.offline { opacity: 0.5; }

  .chip-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
    background: #4ade80;
  }
  .offline .chip-dot { background: #64748b; }

  .chip-name { font-size: 12px; color: var(--monitor-chip-name, #cbd5e1); max-width: 60px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .chip-mac { font-size: 11px; font-family: monospace; color: var(--monitor-chip-mac, #64748b); }
  .chip-volt { font-size: 11px; margin-left: auto; color: var(--monitor-text-secondary, #94a3b8); }
}

html:not(.dark) .device-chip {
  --monitor-chip-bg: rgba(0,0,0,0.02);
  --monitor-chip-name: #334155;
  --monitor-chip-mac: #94a3b8;
}

html.dark .device-chip {
  --monitor-chip-bg: rgba(255,255,255,0.03);
  --monitor-chip-name: #cbd5e1;
  --monitor-chip-mac: #64748b;
}

/* ========== 事件流 ========== */
.panel-events { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.event-stream { flex: 1; overflow-y: auto; padding-right: 4px; }

.event-item {
  display: flex;
  gap: 10px;
  padding: 7px 0;
  border-bottom: 1px solid var(--monitor-divider, rgba(255,255,255,0.04));
  font-size: 12.5px;
  animation: slideIn 0.3s ease both;

  .ev-time { color: var(--monitor-time-color, #475569); font-family: monospace; white-space: nowrap; min-width: 72px; }
  .ev-msg { color: var(--monitor-ev-msg, #cbd5e1); }
}

html:not(.dark) .event-item {
  --monitor-divider: rgba(0,0,0,0.06);
  --monitor-time-color: #94a3b8;
  --monitor-ev-msg: #475569;
}

html.dark .event-item {
  --monitor-divider: rgba(255,255,255,0.04);
  --monitor-time-color: #475569;
  --monitor-ev-msg: #cbd5e1;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

/* ========== 信号分布 ========== */
.panel-signal { flex: 1; display: flex; flex-direction: column; }

.signal-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: 16px;
  height: 140px;
  padding-top: 10px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  max-width: 80px;

  .bar-fill {
    width: 100%;
    max-width: 56px;
    border-radius: 6px 6px 2px 2px;
    transition: height 0.5s ease;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 4px;

    .bar-val { font-size: 11px; color: white; font-weight: 600; }
  }

  .bar-label {
    font-size: 11px;
    color: var(--monitor-text-muted, #64748b);
    text-align: center;
    line-height: 1.3;
    white-space: pre-line;
  }
}

/* ========== 告警面板 ========== */
.panel-alerts { flex: 1; display: flex; flex-direction: column; }

.alert-list {
  flex: 1;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--monitor-alert-bg, rgba(239,68,68,0.06));
  border-left: 3px solid #ef4444;
  margin-bottom: 6px;
  font-size: 12.5px;

  .al-text { color: var(--monitor-alert-text, #fca5a5); flex: 1; }
  .al-time { color: var(--monitor-time-color, #64748b); font-size: 11px; font-family: monospace; }
}

html:not(.dark) .alert-item {
  --monitor-alert-bg: rgba(239,68,68,0.04);
  --monitor-alert-text: #dc2626;
}

html.dark .alert-item {
  --monitor-alert-bg: rgba(239,68,68,0.06);
  --monitor-alert-text: #fca5a5;
}

.no-alert {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--monitor-text-muted, #475569);
  font-size: 13px;
}

html:not(.dark) .no-alert {
  --monitor-text-muted: #94a3b8;
}

html.dark .no-alert {
  --monitor-text-muted: #475569;
}

/* ========== 动画过渡 ========== */
.device-list-enter-active { transition: all 0.3s ease; }
.device-list-enter-from { opacity: 0; transform: translateY(8px); }

.event-slide-enter-active { transition: all 0.3s ease; }
.event-slide-enter-from { opacity: 0; transform: translateX(-16px); }
.event-slide-leave-active { transition: all 0.2s ease; }
.event-slide-leave-to { opacity: 0; transform: translateX(16px); }

/* ========== 响应式 ========== */
@media (max-width: 900px) {
  .row { flex-direction: column; }
  .row-top { height: auto; }
  .stat-grid { grid-template-columns: repeat(3, 1fr); }
  .panel-rate { width: 100%; margin-top: 12px; }
}
</style>
