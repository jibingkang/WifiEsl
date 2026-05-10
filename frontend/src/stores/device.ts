/**
 * 设备数据状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { Device, PaginatedResponse } from '@/types'
import { deviceApi } from '@/api/device'

// localStorage 持久化 key
const PAGE_SIZE_KEY = 'wifi_esl_device_page_size'

function loadPageSize(): number {
  try {
    const v = localStorage.getItem(PAGE_SIZE_KEY)
    return v ? parseInt(v) || 20 : 20
  } catch { return 20 }
}

function savePageSize(v: number) {
  try { localStorage.setItem(PAGE_SIZE_KEY, String(v)) } catch {}
}

export const useDeviceStore = defineStore('device', () => {
  // 状态
  const devices = ref<Device[]>([])
  const allDevices = ref<Device[]>([])   // 全量设备缓存（不分页，用于MAC查找）
  const loading = ref(false)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(loadPageSize())

  // 持久化 pageSize
  watch(pageSize, (v) => savePageSize(v))
  /** 已选中的设备MAC列表 */
  const selectedMacs = ref<string[]>([])

  // 计算属性
  /** 在线设备数 */
  const onlineCount = computed(() => allDeviceList.value.filter(d => d.is_online).length)

  /** 离线设备数 */
  const offlineCount = computed(() => allDeviceList.value.filter(d => !d.is_online).length)

  /** 在线率 */
  const onlineRate = computed(() =>
    allDeviceList.value.length > 0 ? ((onlineCount.value / allDeviceList.value.length) * 100).toFixed(1) : '0.0'
  )

  /** 低电量设备 (<350, 对应3.50V以下) */
  const lowBatteryDevices = computed(() =>
    allDeviceList.value.filter(d => d.voltage && d.voltage < 350 && d.is_online)
  )

  /** 弱信号设备 (< -70 dBm) */
  const weakSignalDevices = computed(() =>
    allDeviceList.value.filter(d => d.rssi && d.rssi < -70 && d.is_online)
  )

  /** 全量设备列表（优先 allDevices，兜底 devices；仪表盘/监控等依赖完整数据的视图应使用此属性） */
  const allDeviceList = computed(() => allDevices.value.length > 0 ? allDevices.value : devices.value)

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
   * 全量加载所有设备（单次请求，后端参数 all=true 跳过切片）
   * 同时写入 devices 确保仪表盘/监控读到完整数据
   */
  async function fetchAllDevices() {
    loading.value = true
    try {
      const res: any = await deviceApi.getDeviceList({ page: 1, pageSize: 1, all: true } as any)
      const items: Device[] = res.items ?? []
      allDevices.value = items
      devices.value = items
      total.value = res.total ?? items.length
      console.log(`[DeviceStore] 全量加载 ${items.length} 台设备`)
    } catch (e) {
      console.error('[DeviceStore] Failed to fetch all devices:', e)
    } finally {
      loading.value = false
    }
  }

  /**
   * 根据MAC获取单个设备信息（优先从全量缓存查找）
   */
  function getDeviceByMac(mac: string): Device | undefined {
    return allDevices.value.find(d => d.mac === mac) ?? devices.value.find(d => d.mac === mac)
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
    allDevices,
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
    allDeviceList,
    fetchDevices,
    fetchAllDevices,
    getDeviceByMac,
    updateDeviceStatus,
    deviceOnline,
    deviceOffline,
    clearSelection,
  }
})
