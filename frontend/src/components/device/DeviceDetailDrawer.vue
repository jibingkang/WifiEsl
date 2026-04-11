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
import type { Device } from '@/types'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatMac, formatDateTime, formatVoltage } from '@/utils/format'
import { DEVICE_TYPES, SCREEN_TYPES } from '@/utils/constants'
import { deviceApi } from '@/api/device'

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

/** 暴露给模板的设备数据（优先用拉取到的详情，回退到传入的 device） */
const currentDevice = computed<Device | null>(() => detailData.value || props.device)

/** 当抽屉打开且有 MAC 时自动拉取完整数据 */
watch(
  () => ({ visible: props.visible, device: props.device }),
  async ({ visible, device }) => {
    if (visible && device?.mac) {
      await fetchFullDetail(device)
    } else {
      detailData.value = null
    }
  },
)

/** 拉取完整设备详情（通过 MAC 地址查询） */
async function fetchFullDetail(device: Device | null) {
  if (!device?.mac) return
  loading.value = true
  try {
    const res = await deviceApi.getDeviceByMac(device.mac)
    // 后端返回格式: { code, data: {...} } 或直接是数据对象
    const data = res.data ?? res
    if (data && typeof data === 'object') {
      // 合并：API 数据为主 + 列表中的实时字段（如 is_online）为辅
      detailData.value = {
        ...data,
        is_online: data.is_online ?? device.is_online,
        voltage: data.voltage ?? device.voltage,
        rssi: data.rssi ?? device.rssi,
      } as Device
    }
  } catch (e) {
    console.error('[DeviceDetail] 获取详情失败，使用列表数据:', e)
    detailData.value = null // 回退到 props.device
  } finally {
    loading.value = false
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
</style>
