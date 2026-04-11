// ============================================
// 全局类型定义
// ============================================

// 用户相关
export interface LoginParams {
  username: string
  password: string
}

export interface UserInfo {
  id: string
  username: string
  role: 'admin' | 'operator' | 'viewer'
  avatar?: string
  apiKey: string
}

export interface TokenInfo {
  token: string
  expiresIn: number
  user: UserInfo
}

// 设备相关
export interface Device {
  id: string
  mac: string
  ip: string
  name?: string
  is_online: boolean
  voltage?: number
  rssi?: number
  usb_state?: number
  device_type?: string
  screen_type?: string
  sn?: string
  sw_version?: number
  hw_version?: number
  created_at: string
  updated_at: string
}

// 模板相关
export interface TemplateFieldDef {
  key: string
  label: string
  type: 'text' | 'textarea' | 'number' | 'select' | 'color' | 'date' | 'image' | 'qrcode'
  required?: boolean
  default_value?: string | null
  placeholder?: string
  options?: Array<{ label: string; value: any }>
  order: number
}

export interface TemplateInfo {
  tid: string
  tname: string
  description?: string
  preview_image?: string
  fields: TemplateFieldDef[]
  screen_type?: string
}

// MQTT消息类型
export interface MqttMessage<T = any> {
  topic: string
  payload: T
  timestamp: number
}

export interface DeviceStatusMessage {
  mac: string
  msgId: string
  online?: boolean
  voltage?: number
  rssi?: number
  state?: number // USB状态
  result?: number // 操作结果 200/400/401
}

// API响应
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页
export interface PaginationParams {
  page: number
  pageSize: number
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  pageSize: number
  items: T[]
}
