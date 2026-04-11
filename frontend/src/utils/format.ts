/**
 * 格式化工具函数集
 */

/**
 * 格式化MAC地址 (添加冒号分隔)
 */
export function formatMac(mac: string): string {
  if (!mac) return '--'
  const cleaned = mac.replace(/[^a-fA-F0-9]/g, '')
  if (cleaned.length !== 12) return mac
  return cleaned.match(/.{2}/g)?.join(':')?.toUpperCase() ?? mac
}

/**
 * 格式化电压值 → "X.XX V (XX.X%)"
 * 原始单位为 0.01V (如设备返回413 → 4.13V)
 * 电量百分比基准: <3350=0.0%, >3900=100.0%, 中间线性插值
 */
export function formatVoltage(voltage?: number | null): string {
  if (voltage == null || voltage === 0) return '--'
  const voltV = voltage / 100           // 0.01V 单位 → V (如 413→4.13)
  const pct = calcBatteryPercent(voltage)
  return `${voltV.toFixed(2)} V (${pct}%)`
}

/**
 * 格式化电压值 → 仅显示 "X.XX V"（用于控制面板等紧凑场景）
 */
export function formatVolt(voltage?: number | null): string {
  if (voltage == null || voltage === 0) return '--'
  return `${(voltage / 100).toFixed(2)} V`
}

/**
 * 计算电量百分比（基于基准电压公式）
 * <335(3.35V) → 0.0%, >390(3.90V) → 100.0%, 中间线性插值
 */
function calcBatteryPercent(voltageRaw: number): string {
  if (voltageRaw >= 390) return '100.0'
  if (voltageRaw <= 335) return '0.0'
  return (((voltageRaw - 335) / (390 - 335)) * 100).toFixed(1)
}

/**
 * 格式化信号强度 RSSI
 */
export function formatRssi(rssi?: number | null): string {
  if (rssi == null) return '-- dBm'
  if (rssi >= -50) return `${rssi} dBm (优秀)`
  if (rssi >= -60) return `${rssi} dBm (良好)`
  if (rssi >= -70) return `${rssi} dBm (一般)`
  return `${rssi} dBm (弱)`
}

/**
 * 格式化日期时间
 */
export function formatDateTime(dateStr: string | Date, fmt = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!dateStr) return '--'
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr

  const map: Record<string, () => number> = {
    YYYY: () => date.getFullYear(),
    MM: () => String(date.getMonth() + 1).padStart(2, '0'),
    DD: () => String(date.getDate()).padStart(2, '0'),
    HH: () => String(date.getHours()).padStart(2, '0'),
    mm: () => String(date.getMinutes()).padStart(2, '0'),
    ss: () => String(date.getSeconds()).padStart(2, '0'),
  }

  let result = fmt
  for (const [key, fn] of Object.entries(map)) {
    result = result.replace(key, String(fn()))
  }
  return result
}

/**
 * 相对时间 (xx前)
 */
export function formatRelativeTime(dateStr: string): string {
  if (!dateStr) return ''
  const now = Date.now()
  const target = new Date(dateStr).getTime()
  const diff = now - target

  if (diff < 60_000) return '刚刚'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)}分钟前`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)}小时前`
  return `${Math.floor(diff / 86400_000)}天前`
}

/**
 * 文件大小格式化
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

/**
 * 数字千分位分隔
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('zh-CN')
}

/**
 * 百分比显示
 */
export function formatPercent(value: number, total: number): string {
  if (total === 0) return '0%'
  return `${((value / total) * 100).toFixed(1)}%`
}

/**
 * 截断文本 + 省略号
 */
export function truncate(text: string, maxLength: number): string {
  if (!text || text.length <= maxLength) return text ?? ''
  return text.slice(0, maxLength) + '...'
}
