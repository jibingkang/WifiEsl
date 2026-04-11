/**
 * 设备操作 composable
 */
import { reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deviceApi } from '@/api/device'
import { formatVoltage } from '@/utils/format'

interface UseDeviceOptions {
  onSuccess?: () => void
  onError?: (err: any) => void
}

export function useDevice(options?: UseDeviceOptions) {
  const controlLoading = reactive<Record<string, boolean>>({})

  /**
   * 设置LED灯状态
   */
  async function setLed(mac: string, params: { r: number; g: number; b: number }) {
    const key = `${mac}-led`
    controlLoading[key] = true
    try {
      await deviceApi.controlLED(mac, params.r, params.g, params.b)
      ElMessage.success(`已发送LED控制指令 → ${mac}`)
      options?.onSuccess?.()
    } catch (e: any) {
      ElMessage.error(`LED控制失败: ${e.message}`)
      options?.onError?.(e)
    } finally {
      controlLoading[key] = false
    }
  }

  /**
   * 重启设备
   */
  async function reboot(mac: string) {
    await ElMessageBox.confirm(`确定要重启设备 ${mac} 吗？`, '重启确认', { type: 'warning' })
    const key = `${mac}-reboot`
    controlLoading[key] = true
    try {
      await deviceApi.rebootDevice(mac)
      ElMessage.success(`已发送重启指令 → ${mac}`)
      options?.onSuccess?.()
    } catch (e: any) {
      ElMessage.error(`重启失败: ${e.message}`)
      options?.onError?.(e)
    } finally {
      controlLoading[key] = false
    }
  }

  /**
   * 查询电池电量
   */
  async function queryBattery(mac: string) {
    const key = `${mac}-battery`
    controlLoading[key] = true
    try {
      const res = await deviceApi.queryBattery(mac)
      ElMessage.success(`${mac} 电量: ${formatVoltage(res.voltage)}`)
      options?.onSuccess?.()
      return res
    } catch (e: any) {
      ElMessage.error(`电量查询失败: ${e.message}`)
      options?.onError?.(e)
    } finally {
      controlLoading[key] = false
    }
  }

  return {
    controlLoading,
    setLed,
    reboot,
    queryBattery,
  }
}
