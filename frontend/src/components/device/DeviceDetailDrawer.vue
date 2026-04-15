<template>
  <el-drawer
    :model-value="visible"
    title="设备详情"
    direction="rtl"
    size="420px"
    :loading="loading"
    @update:model-value="(val) => $emit('update:visible', val)"
  >
    <template v-if="currentDevice && !loading">
      <!-- 头部信息 -->
      <div class="detail-header">
        <StatusBadge :online="currentDevice.is_online" size="large" />
        <div class="header-info">
          <h3>{{ currentDevice.name || '未命名设备' }}</h3>
          <code>{{ formatMac(currentDevice.mac) }}</code>
        </div>
      </div>

      <!-- 详细属性列表 -->
      <el-descriptions :column="1" border size="small" class="detail-desc">
        <el-descriptions-item label="MAC地址">
          <code>{{ currentDevice.mac }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentDevice.ip || '--' }}</el-descriptions-item>
        <el-descriptions-item label="自定义名称">{{ currentDevice.name || '--' }}</el-descriptions-item>
        <el-descriptions-item label="在线状态">
          <StatusBadge :online="currentDevice.is_online" />
        </el-descriptions-item>
        <el-descriptions-item label="电池电压">
          {{ currentDevice.voltage != null ? formatVoltage(currentDevice.voltage) : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="信号强度">
          {{ currentDevice.rssi != null ? `${currentDevice.rssi} dBm` : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="USB状态">
          {{ currentDevice.usb_state != null ? (currentDevice.usb_state ? '供电中' : '未连接') : '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="设备类型">
          {{ DEVICE_TYPES[currentDevice.device_type ?? ''] ?? currentDevice.device_type ?? '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="屏幕类型">
          {{ SCREEN_TYPES[currentDevice.screen_type ?? ''] ?? currentDevice.screen_type ?? '--' }}
        </el-descriptions-item>
        <el-descriptions-item label="序列号">{{ currentDevice.sn ?? '--' }}</el-descriptions-item>
        <el-descriptions-item label="固件版本">{{ currentDevice.sw_version ?? '--' }}</el-descriptions-item>
        <el-descriptions-item label="硬件版本">{{ currentDevice.hw_version ?? '--' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentDevice.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(currentDevice.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- LED灯控制 -->
      <div class="led-section">
        <div class="section-header">
          <h5><el-icon><Sunny /></el-icon> LED灯控制</h5>
          <el-switch
            v-model="ledOn"
            active-text="开"
            inactive-text="关"
            inline-prompt
            :disabled="controlLoading[`${currentDevice.mac}-led`]"
            @change="onLedSwitchChange"
          />
        </div>

        <template v-if="ledOn">
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
          <div class="led-actions">
            <div class="custom-color-row">
              <label class="color-label">自定义</label>
              <input type="color" v-model="hexColor" class="native-picker" @input="onHexColorChange" />
              <code class="hex-display">{{ hexColor.toUpperCase() }}</code>
            </div>
            <el-button
              type="primary"
              size="default"
              :loading="controlLoading[`${currentDevice.mac}-led`]"
              :icon="Promotion"
              @click="sendLedCommand"
            >发送亮灯指令</el-button>
          </div>
        </template>
        <div v-else class="led-off-tip">
          <p>LED 已关闭，点击上方开关开启</p>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="detail-actions" v-if="currentDevice.mac">
        <el-button type="primary" @click="$emit('control', { action: 'control', device: currentDevice! })">控制设备</el-button>
        <el-button @click="doQueryBattery" :loading="batteryLoading">刷新电量</el-button>
      </div>
    </template>
    <div v-else-if="loading" style="text-align:center;padding:60px 0;">
      <p style="color:var(--el-text-color-secondary)">正在加载设备详情...</p>
    </div>
    <div v-else style="text-align:center;padding:60px 0;">
      <p style="color:var(--el-text-color-secondary)">暂无设备数据</p>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Sunny, Promotion } from '@element-plus/icons-vue'
import type { Device } from '@/types'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatMac, formatDateTime, formatVoltage } from '@/utils/format'
import { DEVICE_TYPES, SCREEN_TYPES } from '@/utils/constants'
import { deviceApi } from '@/api/device'
import { useDevice } from '@/composables/useDevice'

const props = defineProps<{
  visible: boolean
  device: Device | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'control': [payload: { action: string; device: Device }]
}>()

const loading = ref(false)
const batteryLoading = ref(false)
const detailData = ref<Device | null>(null)

// LED 控制
const { controlLoading, setLed } = useDevice({ onSuccess: () => {} })
const ledOn = ref(true)
const hexColor = ref('#FF0000')
const currentLedColor = ref<{ name: string; r: number; g: number; b: number }>({ name: '红色', r: 255, g: 0, b: 0 })

const ledColors = [
  { name: '红色', r: 255, g: 0, b: 0 },
  { name: '绿色', r: 0, g: 255, b: 0 },
  { name: '蓝色', r: 0, g: 0, b: 255 },
  { name: '黄色', r: 255, g: 255, b: 0 },
  { name: '紫色', r: 255, g: 0, b: 255 },
  { name: '青色', r: 0, g: 255, b: 255 },
  { name: '白色', r: 255, g: 255, b: 255 },
]

/** 暴露给模板的设备数据（优先用拉取到的详情，回退到传入的 device） */
const currentDevice = computed<Device | null>(() => detailData.value || props.device)

/** 当抽屉打开且有 MAC 时自动拉取完整数据 */
watch(
  () => ({ visible: props.visible, device: props.device }),
  async ({ visible, device }) => {
    console.log('[DeviceDetail] watch触发:', { visible, deviceMac: device?.mac })
    if (visible && device?.mac) {
      await fetchFullDetail(device)
    } else if (!visible) {
      detailData.value = null
    }
  },
  { immediate: true },
)

/** 拉取完整设备详情（通过 MAC 地址查询） */
async function fetchFullDetail(device: Device | null) {
  if (!device?.mac) {
    console.warn('[DeviceDetail] 设备或MAC为空')
    return
  }
  console.log('[DeviceDetail] 开始获取详情，MAC:', device.mac, '传入设备:', device)
  loading.value = true
  try {
    const res = await deviceApi.getDeviceByMac(device.mac)
    console.log('[DeviceDetail] API响应:', res)
    // 后端返回格式: { code, data: {...} } 或直接是数据对象（已被拦截器解包）
    const data = res?.data ?? res
    console.log('[DeviceDetail] 提取的数据:', data)
    if (data && typeof data === 'object' && data.mac) {
      // 合并：API 数据为主 + 列表中的实时字段（如 is_online）为辅
      detailData.value = {
        ...data,
        is_online: data.is_online ?? device.is_online,
        voltage: data.voltage ?? device.voltage,
        rssi: data.rssi ?? device.rssi,
      } as Device
      console.log('[DeviceDetail] 设置详情数据:', detailData.value)
    } else {
      // API返回空数据，使用列表数据作为基础，避免显示空
      console.warn('[DeviceDetail] API返回数据无效，使用列表数据:', data)
      detailData.value = { ...device } as Device
    }
  } catch (e) {
    console.error('[DeviceDetail] 获取详情失败，使用列表数据:', e)
    detailData.value = { ...device } as Device // 回退到 props.device
  } finally {
    loading.value = false
    console.log('[DeviceDetail] 加载完成，最终数据:', detailData.value)
  }
}

/** 在详情页内刷新电量 */
async function doQueryBattery() {
  const mac = currentDevice.value?.mac || detailData.value?.mac
  if (!mac) return
  batteryLoading.value = true
  try {
    const res = await deviceApi.queryBattery(mac)
    const voltage = res.voltage ?? res.data?.voltage
    if (voltage != null && detailData.value) {
      detailData.value = { ...detailData.value, voltage }
    }
  } finally {
    batteryLoading.value = false
  }
}

// ── LED 灯控制 ──
function selectColor(color: typeof ledColors[0]) {
  currentLedColor.value = color
  hexColor.value = rgbToHex(color.r, color.g, color.b)
}

function onHexColorChange(e: Event) {
  const hex = (e.target as HTMLInputElement).value
  hexColor.value = hex
  const rgb = hexToRgb(hex)
  if (rgb) currentLedColor.value = { name: '自定义', ...rgb }
}

async function onLedSwitchChange(val: boolean) {
  if (!currentDevice.value?.mac) return
  if (!val) {
    await setLed(currentDevice.value.mac, { r: 0, g: 0, b: 0 })
  }
}

async function sendLedCommand() {
  if (!currentDevice.value?.mac || !currentLedColor.value) return
  await setLed(currentDevice.value.mac, {
    r: currentLedColor.value.r,
    g: currentLedColor.value.g,
    b: currentLedColor.value.b,
  })
}

function rgbToHex(r: number, g: number, b: number): string {
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0').toUpperCase()).join('')
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const m = hex.replace('#', '').match(/.{2}/g)
  if (!m) return null
  return { r: parseInt(m[0], 16), g: parseInt(m[1], 16), b: parseInt(m[2], 16) }
}
</script>

<style lang="scss" scoped>
.detail-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 14px;
  background: var(--el-fill-color-extra-light);
  margin-bottom: 20px;

  h3 { font-size: 17px; margin: 0 0 4px; color: var(--el-text-color-primary); }
  code { font-size: 12px; color: var(--el-text-color-secondary); }
}

.detail-desc {
  :deep(.el-descriptions__label) {
    width: 110px;
    font-weight: 500;
    color: var(--el-text-color-secondary);
  }
  code { font-family: monospace; font-size: 13px; background: var(--el-fill-color-light); padding: 1px 6px; border-radius: 4px; }
}

.detail-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.led-section {
  padding: 4px 0;
  margin-bottom: 16px;
}

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
  width: 36px;
  height: 36px;
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
    font-size: 14px;
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
    font-family: monospace;
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
</style>
