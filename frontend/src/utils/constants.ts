/**
 * 应用常量定义
 */

// API基础地址 (由Vite代理转发到后端8080)
export const API_BASE_URL = '/api/v1'

// MQTT连接配置 (开发环境)
export const MQTT_CONFIG = {
  host: window.location.hostname,
  port: 8883,
  protocol: 'wss' as const,   // WebSocket Secure
  clientIdPrefix: 'esl_mgr_',
  reconnectPeriod: 5000,
  connectTimeout: 10000,
  keepalive: 60,
}

// MQTT主题
export const MQTT_TOPICS = {
  // 设备状态推送
  ONLINE: 'online',
  OFFLINE: 'offline',
  USB_STATE: 'usb_state',
  BUTTON: 'button',
  // 控制反馈
  DISPLAY_REPLY: 'display_reply',
  BATTERY_REPLY: 'battery_reply',
  LED_REPLY: 'led_reply',
  REBOOT_REPLY: 'reboot_reply',
} as const

// 设备类型映射
export const DEVICE_TYPES: Record<string, string> = {
  esl_29: '2.9寸标签',
  esl_43: '4.3寸标签',
  esl_7: '7.5寸标签',
  tag: '标签设备',
}

// 屏幕类型映射
export const SCREEN_TYPES: Record<string, string> = {
  bw: '黑白屏',
  bwr: '黑白红三色屏',
  color: '彩色屏',
}

// 设备在线状态
export const DEVICE_STATUS = {
  ONLINE: { label: '在线', value: true, type: 'success' },
  OFFLINE: { label: '离线', value: false, type: 'danger' },
} as const

// 分页默认配置
export const PAGINATION = {
  PAGE: 1,
  PAGE_SIZE: 20,
  PAGE_SIZES: [10, 20, 50, 100],
}

// 刷新间隔 (毫秒)
export const REFRESH_INTERVALS = {
  DASHBOARD: 30_000,     // 仪表盘 30秒
  MONITOR: 5_000,        // 监控看板 5秒
  STATUS: 10_000,        // 设备状态 10秒
} as const

// 主题配置
export const THEME_CONFIG = {
  LIGHT: 'light',
  DARK: 'dark',
  AUTO: 'auto',
} as const

// 动画时长 (ms)
export const ANIMATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const
