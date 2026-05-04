/**
 * 登录告警检查 - 每次登录会话仅弹出一次
 *
 * 使用 sessionStorage 存储标志，确保：
 * - 每次登录进入系统后弹出一次
 * - 页面刷新后不再重复弹出（同一会话）
 * - 重新登录后（新会话）再次弹出
 */
import { ref, type Ref } from 'vue'
import { deviceApi } from '@/api/device'

export interface AlertDevice {
  mac: string
  name?: string | null
  is_online?: number | null
  voltage?: number | null
  last_seen_at?: string | null
}

export interface DeviceAlertData {
  offline_count: number
  offline_devices: AlertDevice[]
  low_battery_count: number
  low_battery_devices: AlertDevice[]
}

const STORAGE_KEY = 'wifi_esl_alert_checked'

// 组件间共享的响应式状态
const alertVisible = ref(false)
const alertData: Ref<DeviceAlertData | null> = ref(null)
const allNormal = ref(false)

export function useLoginAlert() {
  /**
   * 检查设备告警
   * 同一浏览器会话（sessionStorage）内只弹出一次
   */
  async function checkAlerts() {
    // 已检查过则跳过
    if (sessionStorage.getItem(STORAGE_KEY)) return
    sessionStorage.setItem(STORAGE_KEY, '1')

    try {
      const res: any = await deviceApi.getDeviceAlerts()
      // 响应拦截器已剥壳，res 直接就是 data 内的告警对象
      const data: DeviceAlertData | undefined = res?.offline_count != null
        ? res
        : res?.data  // 兼容万一拦截器没剥壳

      if (data) {
        alertData.value = data
        const hasAlert = data.offline_count > 0 || data.low_battery_count > 0
        allNormal.value = !hasAlert
        alertVisible.value = true
      }
    } catch (e) {
      console.warn('[useLoginAlert] 检查告警失败:', e)
    }
  }

  /** 关闭告警弹窗 */
  function dismissAlert() {
    alertVisible.value = false
  }

  /** 重置状态（登出时调用，确保下次登录重新弹窗） */
  function resetCheck() {
    sessionStorage.removeItem(STORAGE_KEY)
    alertData.value = null
    alertVisible.value = false
    allNormal.value = false
  }

  return {
    alertVisible,
    alertData,
    allNormal,
    checkAlerts,
    dismissAlert,
    resetCheck,
  }
}
