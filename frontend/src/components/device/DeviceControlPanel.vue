<template>
  <el-drawer
    :model-value="visible"
    title="设备控制面板"
    direction="rtl"
    size="380px"
    :close-on-click-modal="true"
    @update:model-value="(val) => $emit('update:visible', val)"
  >
    <template v-if="device">
      <!-- 设备基本信息 -->
      <div class="device-summary">
        <StatusBadge :online="device.is_online" size="large" />
        <div class="summary-info">
          <h4>{{ device.name || '未命名设备' }}</h4>
          <code>{{ formatMac(device.mac) }}</code>
          <p class="ip">{{ device.ip || 'IP未知' }}</p>
        </div>
      </div>

      <el-divider />

      <!-- LED灯控制 -->
      <div class="control-section">
        <div class="section-header">
          <h5><el-icon><Sunny /></el-icon> LED灯控制</h5>
          <el-switch
            v-model="ledOn"
            active-text="开"
            inactive-text="关"
            inline-prompt
            :disabled="controlLoading[`${device.mac}-led`]"
            @change="onLedSwitchChange"
          />
        </div>

        <template v-if="ledOn">
          <!-- 预设颜色选择 -->
          <div class="color-presets">
            <button
              v-for="color in ledColors"
              :key="color.name"
              class="color-btn"
              :class="{ active: currentLedColor?.name === color.name }"
              :style="{ background: `rgb(${color.r},${color.g},${color.b})` }"
              :title="color.name"
              @click="selectColor(color)"
            >
              <span v-if="currentLedColor?.name === color.name" class="check-icon">&#10003;</span>
            </button>
          </div>

          <!-- 自定义颜色 + 发送按钮 -->
          <div class="led-actions">
            <div class="custom-color-row">
              <label class="color-label">自定义</label>
              <input
                ref="colorPickerRef"
                type="color"
                v-model="hexColor"
                class="native-picker"
                @input="onHexColorChange"
              />
              <code class="hex-display">{{ hexColor.toUpperCase() }}</code>
            </div>
            <el-button
              type="primary"
              size="default"
              :loading="controlLoading[`${device.mac}-led`]"
              :icon="Promotion"
              @click="sendLedCommand"
            >发送亮灯指令</el-button>
          </div>
        </template>
        <div v-else class="led-off-tip">
          <p>LED 已关闭，点击上方开关开启</p>
        </div>
      </div>

      <el-divider />

      <!-- 快捷操作 -->
      <div class="control-section">
        <h5><el-icon><Operation /></el-icon> 快捷操作</h5>
        <div class="quick-btns">
          <el-button
            :loading="controlLoading[`${device.mac}-battery`]"
            @click="doQueryBattery"
          >
            <el-icon><Lightning /></el-icon> 查询电量
          </el-button>
          <el-button
            type="warning"
            :loading="controlLoading[`${device.mac}-reboot`]"
            @click="doReboot"
          >
            <el-icon><RefreshRight /></el-icon> 重启设备
          </el-button>
        </div>
      </div>

      <el-divider />

      <!-- 实时状态 -->
      <div class="control-section">
        <h5><el-icon><DataLine /></el-icon> 实时状态</h5>
        <div class="status-grid">
          <div class="status-item">
            <span class="label">电压</span>
            <span class="val">{{ device.voltage ? formatVolt(device.voltage) : '--' }}</span>
          </div>
          <div class="status-item">
            <span class="label">信号强度</span>
            <span class="val">{{ device.rssi != null ? `${device.rssi} dBm` : '--' }}</span>
          </div>
          <div class="status-item">
            <span class="label">USB状态</span>
            <span class="val">{{ device.usb_state != null ? (device.usb_state ? '供电中' : '未连接') : '--' }}</span>
          </div>
          <div class="status-item">
            <span class="label">软件版本</span>
            <span class="val">{{ device.sw_version ?? '--' }}</span>
          </div>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Sunny, Operation, Lightning, RefreshRight, DataLine, Promotion } from '@element-plus/icons-vue'
import type { Device } from '@/types'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useDevice } from '@/composables/useDevice'
import { formatMac, formatVolt } from '@/utils/format'

const props = defineProps<{
  visible: boolean
  device: Device | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const { controlLoading, setLed, reboot, queryBattery } = useDevice({
  onSuccess: () => {},
})

// ── LED 灯控制 ──
interface LedColor {
  name: string
  r: number
  g: number
  b: number
}

/** 预设颜色（不含"关闭"，关闭由开关统一处理） */
const ledColors: LedColor[] = [
  { name: '红色', r: 255, g: 0, b: 0 },
  { name: '绿色', r: 0, g: 255, b: 0 },
  { name: '蓝色', r: 0, g: 0, b: 255 },
  { name: '黄色', r: 255, g: 255, b: 0 },
  { name: '紫色', r: 255, g: 0, b: 255 }, // 改为(255,0,255) #FF00FF
  { name: '青色', r: 0, g: 255, b: 255 },
  { name: '白色', r: 255, g: 255, b: 255 },
]

const ledOn = ref(true)
const currentLedColor = ref<LedColor>(ledColors[0]) // 默认红色
const hexColor = ref('#FF0000')
const colorPickerRef = ref<HTMLInputElement | null>(null)

/** 从预设颜色中选中 */
function selectColor(color: LedColor) {
  currentLedColor.value = color
  hexColor.value = rgbToHex(color.r, color.g, color.b)
}

/** 原生颜色选择器变化 → 更新当前颜色 */
function onHexColorChange(e: Event) {
  const hex = (e.target as HTMLInputElement).value
  hexColor.value = hex
  currentLedColor.value = hexToRgb(hex) || currentLedColor.value
}

/** 开关切换：关 → 直接发(0,0,0)；开 → 不自动发送，让用户选色 */
async function onLedSwitchChange(val: boolean) {
  if (!props.device) return
  if (!val) {
    // 关灯：直接发送黑色
    await setLed(props.device.mac, { r: 0, g: 0, b: 0 })
  }
  // 开灯不自动发送，等用户选色后点按钮
}

/** 发送亮灯指令 */
async function sendLedCommand() {
  if (!props.device || !currentLedColor.value) return
  await setLed(props.device.mac, {
    r: currentLedColor.value.r,
    g: currentLedColor.value.g,
    b: currentLedColor.value.b,
  })
}

// ── 颜色工具函数 ──
function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0').toUpperCase()).join('')
}

function hexToRgb(hex: string): LedColor | null {
  const m = hex.replace('#', '').match(/.{2}/g)
  if (!m) return null
  return { name: '自定义', r: parseInt(m[0], 16), g: parseInt(m[1], 16), b: parseInt(m[2], 16) }
}

// ── 快捷操作 ──
async function doReboot() {
  if (!props.device) return
  await reboot(props.device.mac)
}

async function doQueryBattery() {
  if (!props.device) return
  await queryBattery(props.device.mac)
}
</script>

<style lang="scss" scoped>
.device-summary {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 14px;
  border-radius: 12px;
  background: var(--el-fill-color-extra-light);

  h4 { font-size: 15px; margin: 0 0 4px; color: var(--el-text-color-primary); }
  code { font-size: 12px; color: var(--el-text-color-secondary); }
  .ip { font-size: 12px; color: var(--el-text-color-placeholder); margin: 4px 0 0; }
}

.control-section { padding: 4px 0; }

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  h5 {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0;
  }
}

.color-presets {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin-top: 10px;
}

.color-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2.5px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.15);

  &:hover { transform: scale(1.15); }

  &.active {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 3px var(--el-color-primary-light-7), inset 0 1px 3px rgba(0, 0, 0, 0.15);
  }

  .check-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #fff;
    font-size: 16px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  }
}

.led-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 14px;
}

.custom-color-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--el-fill-color-extra-light);

  .color-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    white-space: nowrap;
  }

  .native-picker {
    -webkit-appearance: none;
    appearance: none;
    border: none;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    padding: 0;
    background: transparent;
    overflow: hidden;

    &::-webkit-color-swatch-wrapper { padding: 2px; }
    &::-webkit-color-swatch { border-radius: 4px; border: 1px solid rgba(128, 128, 128, 0.3); }
  }

  .hex-display {
    font-size: 13px;
    color: var(--el-text-color-regular);
    letter-spacing: 0.5px;
  }
}

.led-off-tip {
  margin-top: 10px;
  p {
    font-size: 13px;
    color: var(--el-text-color-placeholder);
    text-align: center;
    padding: 16px;
    background: var(--el-fill-color-extra-light);
    border-radius: 8px;
    margin: 0;
  }
}

.quick-btns { display: flex; gap: 10px; flex-wrap: wrap; }
.quick-btns .el-button { flex: 1; min-width: 120px; }

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.status-item {
  padding: 10px;
  border-radius: 9px;
  background: var(--el-fill-color-extra-light);
  display: flex;
  flex-direction: column;
  gap: 4px;
  .label { font-size: 12px; color: var(--el-text-color-secondary); }
  .val { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); }
}
</style>
