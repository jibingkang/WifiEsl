/**
 * 设备数据状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Device, PaginatedResponse } from '@/types'
import { deviceApi } from '@/api/device'

export const useDeviceStore = defineStore('device', () => {
  // 状态
  const devices = ref<Device[]>([])
  const loading = ref(false)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  /** 已选中的设备MAC列表 */
  const selectedMacs = ref<string[]>([])

  // 计算属性
  /** 在线设备数 */
  const onlineCount = computed(() => (devices.value ?? []).filter(d => d.is_online).length)

  /** 离线设备数 */
  const offlineCount = computed(() => (devices.value ?? []).filter(d => !d.is_online).length)

  /** 在线率 */
  const onlineRate = computed(() =>
    (devices.value ?? []).length > 0 ? ((onlineCount.value / (devices.value ?? []).length) * 100).toFixed(1) : '0.0'
  )

  /** 低电量设备 (<350, 对应3.50V以下) */
  const lowBatteryDevices = computed(() =>
    (devices.value ?? []).filter(d => d.voltage && d.voltage < 350 && d.is_online)
  )

  /** 弱信号设备 (< -70 dBm) */
  const weakSignalDevices = computed(() =>
    (devices.value ?? []).filter(d => d.rssi && d.rssi < -70 && d.is_online)
  )

  /**
   * 加载设备列表
   */
  async function fetchDevices(params?: Record<string, any>) {
    loading.value = true
    try {
      const res: PaginatedResponse<Device> = await deviceApi.getDeviceList({
        page: currentPage.value,
        pageSize: pageSize.value,
        ...params,
      })
      devices.value = res.items ?? []
      total.value = res.total ?? 0
    } catch (e) {
      console.error('[DeviceStore] Failed to fetch devices:', e)
    } finally {
      loading.value = false
    }
  }

  /**
   * 根据MAC获取单个设备信息
   */
  function getDeviceByMac(mac: string): Device | undefined {
    return devices.value.find(d => d.mac === mac)
  }

  /**
   * 更新单个设备的实时状态 (来自MQTT推送)
   */
  function updateDeviceStatus(mac: string, data: Partial<Device>) {
    const idx = devices.value.findIndex(d => d.mac === mac)
    if (idx !== -1) {
      devices.value[idx] = { ...devices.value[idx], ...data, updated_at: new Date().toISOString() }
    }
  }

  /**
   * 设备上线
   */
  function deviceOnline(mac: string) {
    updateDeviceStatus(mac, { is_online: true, last_seen: new Date().toISOString() })
  }

  /**
   * 设备离线
   */
  function deviceOffline(mac: string) {
    updateDeviceStatus(mac, { is_online: false })
  }

  /**
   * 清除选中
   */
  function clearSelection() {
    selectedMacs.value = []
  }

  return {
    devices,
    loading,
    total,
    currentPage,
    pageSize,
    selectedMacs,
    onlineCount,
    offlineCount,
    onlineRate,
    lowBatteryDevices,
    weakSignalDevices,
    fetchDevices,
    getDeviceByMac,
    updateDeviceStatus,
    deviceOnline,
    deviceOffline,
    clearSelection,
  }
})
