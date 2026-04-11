<template>
  <div class="fullscreen-layout">
    <!-- 全屏顶栏 -->
    <header class="monitor-header">
      <div class="header-left">
        <h1 class="system-title">
          <el-icon :size="22"><Connection /></el-icon>
          WIFI标签实时监控系统
        </h1>
      </div>
      <div class="header-center">
        <span class="clock">{{ currentTime }}</span>
      </div>
      <div class="header-right">
        <div class="mqtt-indicator" :class="{ connected: mqttConnected }">
          <span class="dot" />
          MQTT {{ mqttConnected ? '已连接' : '断开' }}
        </div>
        <ThemeToggle size="small" />
        <button class="exit-btn" @click="$router.push('/dashboard')">
          <el-icon><Close /></el-icon> 退出大屏
        </button>
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="monitor-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Connection, Close } from '@element-plus/icons-vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import { useBackendWs } from '@/composables/useBackendWs'

const currentTime = ref('')
const { mqttConnected } = useBackendWs()

let timer: ReturnType<typeof setInterval>

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  })
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style lang="scss" scoped>
.fullscreen-layout {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #0a0e1a;
  color: #e2e8f0;
  z-index: 100;
  overflow: hidden;
}

.monitor-header {
  height: 52px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: linear-gradient(180deg, rgba(15,23,42,1), rgba(15,23,42,0.85));
  border-bottom: 1px solid rgba(99,102,241,0.2);
  backdrop-filter: blur(10px);
}

.system-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #818cf8, #c4b5fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-center .clock {
  font-size: 20px;
  font-weight: 600;
  font-family: 'SF Mono', monospace;
  color: #94a3b8;
  letter-spacing: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mqtt-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  background: rgba(239,68,68,0.15);
  color: #f87171;

  &.connected { background: rgba(34,197,94,0.15); color: #4ade80; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; animation: pulse 2s infinite; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.exit-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: 1px solid rgba(148,163,184,0.25);
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  &:hover { color: #f87171; border-color: rgba(248,113,113,0.4); }
}

.monitor-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
