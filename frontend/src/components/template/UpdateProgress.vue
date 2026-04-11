<template>
  <div class="update-progress">
    <!-- 未执行状态 -->
    <div v-if="!executing && results.length === 0" class="pre-execution">
      <div class="exec-icon ready">
        <el-icon :size="48"><Upload /></el-icon>
      </div>
      <h3>准备就绪</h3>
      <p>即将对 <strong>{{ deviceMacs.length }}</strong> 台设备应用模板「{{ templateName }}」</p>
      <p class="tip">点击下方按钮开始批量推送，推送过程中请勿关闭页面。</p>

      <el-button type="primary" size="large" round icon="VideoPlay" @click="$emit('start')" style="margin-top: 16px;">
        开始执行
      </el-button>
    </div>

      <!-- 执行中状态 -->
      <div v-else-if="executing" class="executing-state">
        <div class="execution-header">
          <h3><el-icon class="spin"><Loading /></el-icon> 正在推送更新...</h3>
          <el-tag type="info" size="small" style="margin-left: 8px;">
            <el-icon><Clock /></el-icon> 实时处理
          </el-tag>
        </div>

        <!-- 总进度条 -->
        <div class="progress-main">
          <el-progress
            :percentage="progress"
            :stroke-width="18"
            status="success"
            :format="(pct) => `${pct}% (${completed}/${total})`"
          />
        </div>

        <!-- 实时结果列表 -->
        <div class="result-list">
          <div class="result-header">
            <span>实时更新状态</span>
            <span class="result-stats">
              成功: <span class="success-count">{{ succCount }}</span>
              失败: <span class="fail-count">{{ failCount }}</span>
            </span>
          </div>
          
          <TransitionGroup name="list" tag="div" class="results-grid">
            <div
              v-for="(r, idx) in results"
              :key="r.mac"
              class="result-item"
              :class="{ success: r.status === 'success', error: r.status === 'error' }"
            >
              <div class="ri-status">
                <el-icon v-if="r.status === 'success'" color="#22c55e"><CircleCheckFilled /></el-icon>
                <el-icon v-else color="#ef4444"><CircleCloseFilled /></el-icon>
              </div>
              <div class="ri-info">
                <code>{{ r.mac }}</code>
                <span class="msg">{{ r.message }}</span>
                <span class="result-time">{{ getResultTime(idx) }}</span>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>

      <!-- 执行完成状态 -->
      <div v-else class="done-state">
        <div class="exec-icon" :class="{ success: failCount === 0 }">
          <el-icon :size="48"><CircleCheckFilled v-if="failCount === 0" /><WarningFilled v-else /></el-icon>
        </div>

        <h3>{{ failCount === 0 ? '全部完成！' : `已完成（部分失败）` }}</h3>
        
        <p v-if="failCount === 0" class="success-summary">
          所有 {{ total }} 台设备的数据更新成功！
        </p>
        <p v-else class="warning-summary">
          {{ succCount }}台成功，{{ failCount }}台失败
        </p>

        <div class="summary-stats">
          <div class="stat">
            <span class="num total">{{ total }}</span>
            <span class="lbl">总计</span>
          </div>
          <div class="stat ok">
            <span class="num">{{ succCount }}</span>
            <span class="lbl">成功</span>
          </div>
          <div class="stat err">
            <span class="num">{{ failCount }}</span>
            <span class="lbl">失败</span>
          </div>
        </div>

        <!-- 失败详情 -->
        <div v-if="failCount > 0" class="failure-detail">
          <el-collapse>
            <el-collapse-item title="查看失败设备明细" name="failures">
              <div v-for="r in results.filter(r => r.status === 'error')" :key="r.mac" class="fail-item">
                <code>{{ r.mac }}</code>: {{ r.message }}
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div class="done-actions">
          <el-button 
            type="info" 
            size="large" 
            plain
            @click="handleRetryFailed"
            :disabled="failCount === 0"
            style="margin-right: 12px;"
          >
            重试失败设备
          </el-button>
          <el-button type="primary" size="large" round @click="$emit('done')">
            完成并返回
          </el-button>
        </div>
      </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Upload, Loading, VideoPlay, CircleCheckFilled, CircleCloseFilled, WarningFilled, Clock } from '@element-plus/icons-vue'

const props = defineProps<{
  templateName: string
  deviceMacs: string[]
  executing: boolean
  progress: number
  results: Array<{ mac: string; status: 'success' | 'error'; message?: string }>
}>()

const emit = defineEmits<{
  start: []
  done: []
  retry: []
}>()

const total = computed(() => props.deviceMacs.length)
const completed = computed(() => props.results.length)
const succCount = computed(() => props.results.filter(r => r.status === 'success').length)
const failCount = computed(() => props.results.filter(r => r.status === 'error').length)
const resultTimes = ref<string[]>([])

watch(() => props.results.length, (newCount, oldCount) => {
  if (newCount > oldCount) {
    const now = new Date()
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' + 
                   now.getMinutes().toString().padStart(2, '0') + ':' +
                   now.getSeconds().toString().padStart(2, '0')
    resultTimes.value.push(timeStr)
  }
})

function getResultTime(index: number): string {
  if (index < resultTimes.value.length) {
    return resultTimes.value[index]
  }
  return '刚刚'
}

function handleRetryFailed() {
  emit('retry')
}
</script>

<style lang="scss" scoped>
.update-progress { text-align: center; padding: 30px 20px; }

.pre-execution, .done-state { animation: fadeIn 0.4s ease both; }
.executing-state { animation: fadeIn 0.3s ease both; }

.execution-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.exec-icon {
  width: 88px;
  height: 88px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1));
  color: #6366f1;
  &.success { background: linear-gradient(135deg, rgba(34,197,94,0.1), rgba(74,222,128,0.1)); color: #22c55e; }
}

h3 { font-size: 20px; font-weight: 700; color: var(--el-text-color-primary); margin: 0 0 10px; display: flex; align-items: center; justify-content: center; gap: 8px; }
p { color: var(--el-text-color-secondary); margin: 4px 0; }
.tip { font-size: 13px; color: var(--el-text-color-placeholder); }

.progress-main { max-width: 520px; margin: 24px auto 16px; }

.result-list { max-height: 320px; overflow-y: auto; margin-top: 16px; }

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  
  .result-stats {
    .success-count { color: #22c55e; font-weight: 600; margin-right: 8px; }
    .fail-count { color: #ef4444; font-weight: 600; }
  }
}

.results-grid { display: flex; flex-direction: column; gap: 6px; }

.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 9px;
  background: var(--el-bg-color);
  &.success { border-left: 3px solid #22c55e; }
  &.error { border-left: 3px solid #ef4444; }

  code { font-family: monospace; font-size: 12px; }
  .msg { font-size: 12px; color: var(--el-text-color-secondary); margin-left: 8px; }
  .result-time {
    font-size: 11px;
    color: var(--el-text-color-placeholder);
    margin-left: 12px;
    font-family: monospace;
  }
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin: 24px 0;
  .stat { text-align: center; }
  .num { display: block; font-size: 32px; font-weight: 700; }
  .lbl { font-size: 13px; color: var(--el-text-color-secondary); }
  .ok .num { color: #22c55e; }
  .err .num { color: #ef4444; }
  .total .num { color: #6366f1; }
}

.failure-detail { max-width: 480px; margin: 0 auto; }
.fail-item { padding: 4px 0; font-size: 13px; color: var(--el-text-color-secondary); code { color: #ef4444; } }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.list-enter-active,
.list-leave-active { transition: all 0.3s ease; }
.list-enter-from { opacity: 0; transform: translateX(-12px); }
</style>
