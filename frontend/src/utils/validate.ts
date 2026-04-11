/**
 * 校验规则工具集
 */

/**
 * MAC地址校验 (XX:XX:XX:XX:XX:XX 或 连续12位十六进制)
 */
export function isValidMac(mac: string): boolean {
  if (!mac) return false
  const pattern = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$|^[0-9A-Fa-f]{12}$/
  return pattern.test(mac.trim())
}

/**
 * IP地址校验 (IPv4)
 */
export function isValidIp(ip: string): boolean {
  if (!ip) return true // 可选字段
  const pattern = /^(\d{1,3}\.){3}\d{1,3}$/
  if (!pattern.test(ip)) return false
  return ip.split('.').every(octet => parseInt(octet) >= 0 && parseInt(octet) <= 255)
}

/**
 * 端口号校验 (1-65535)
 */
export function isValidPort(port: number | string): boolean {
  const num = Number(port)
  return Number.isInteger(num) && num >= 1 && num <= 65535
}

/**
 * 设备名称校验
 */
export function isValidDeviceName(name: string): boolean {
  if (!name || name.length === 0) return true // 可选
  return name.length <= 50 && /^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$/.test(name)
}

/**
 * JSON字符串校验
 */
export function isJsonString(str: string): boolean {
  try {
    JSON.parse(str)
    return true
  } catch {
    return false
  }
}

/**
 * 常用Element Plus表单校验规则
 */
export const rules = {
  required(message = '此项为必填项'): any {
    required: true,
    message,
    trigger: 'blur',
  },

  mac(): any {
    return {
      validator: (_rule: any, value: string, callback: Function) => {
        if (!value) callback()
        else if (!isValidMac(value)) callback(new Error('MAC地址格式不正确，如 AA:BB:CC:DD:EE:FF'))
        else callback()
      },
      trigger: 'blur',
    }
  },

  ip(required = false): any {
    return {
      validator: (_rule: any, value: string, callback: Function) => {
        if (!value && !required) callback()
        else if (!isValidIp(value)) callback(new Error('IP地址格式不正确'))
        else callback()
      },
      trigger: 'blur',
    }
  },

  port(): any {
    return {
      validator: (_rule: any, value: number, callback: Function) => {
        if (!value) callback()
        else if (!isValidPort(value)) callback(new Error('端口号范围: 1-65535'))
        else callback()
      },
      trigger: 'blur',
    }
  },
}
