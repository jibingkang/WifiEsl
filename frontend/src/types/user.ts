/**
 * 用户角色类型
 */
export type UserRole = 'admin' | 'operator' | 'user'

/**
 * 用户状态类型
 */
export type UserStatus = 'active' | 'disabled' | 'deleted'

/**
 * 用户基础信息
 */
export interface User {
  id: number
  username: string
  role: UserRole
  avatar?: string
  status: UserStatus
  
  // WIFI系统配置
  wifi_username?: string
  wifi_apikey?: string
  wifi_base_url?: string
  wifi_mqtt_broker?: string  // MQTT broker地址
  mqtt_username?: string     // MQTT用户名
  mqtt_password?: string     // MQTT密码
  
  // 用户关系
  parent_user_id?: number
  created_by?: number
  
  // 时间戳
  created_at: string
  updated_at: string
}

/**
 * WIFI配置信息
 */
export interface WifiConfig {
  wifi_username: string
  wifi_password?: string // 注意：密码字段可能为空，解密后显示
  wifi_apikey: string
  wifi_base_url: string
  wifi_mqtt_broker?: string  // MQTT broker地址
  mqtt_username?: string     // MQTT用户名
  mqtt_password?: string     // MQTT密码
  // 用于显示的字段（后端返回时生成）
  wifi_apikey_display?: string
}

/**
 * 用户列表查询参数
 */
export interface UserListQuery {
  page?: number
  page_size?: number
  keyword?: string
  role?: UserRole
  status?: UserStatus
  parent_user_id?: number
}

/**
 * 创建用户请求参数
 */
export interface UserCreateRequest {
  username: string
  password: string
  role: UserRole
  avatar?: string
  status?: UserStatus
  
  // WIFI系统配置（可选）
  wifi_username?: string
  wifi_password?: string
  wifi_apikey?: string
  wifi_base_url?: string
  wifi_mqtt_broker?: string  // MQTT broker地址
  mqtt_username?: string     // MQTT用户名
  mqtt_password?: string     // MQTT密码
  
  // 用户关系
  parent_user_id?: number
}

/**
 * 更新用户请求参数
 */
export interface UserUpdateRequest {
  username?: string
  password?: string
  role?: UserRole
  avatar?: string
  status?: UserStatus
  
  // WIFI系统配置
  wifi_username?: string
  wifi_password?: string
  wifi_apikey?: string
  wifi_base_url?: string
  wifi_mqtt_broker?: string  // MQTT broker地址
  mqtt_username?: string     // MQTT用户名
  mqtt_password?: string     // MQTT密码
}

/**
 * 用户表单数据（用于创建/编辑）
 */
export interface UserFormData {
  username: string
  password: string
  confirmPassword?: string
  role: UserRole
  avatar?: string
  status: UserStatus
  
  // WIFI配置
  wifi_username?: string
  wifi_password?: string
  wifi_apikey?: string
  wifi_base_url?: string
  wifi_mqtt_broker?: string  // MQTT broker地址
  mqtt_username?: string     // MQTT用户名
  mqtt_password?: string     // MQTT密码
  
  // 用户关系
  parent_user_id?: number
}

/**
 * 用户统计信息
 */
export interface UserStats {
  total: number
  admin_count: number
  operator_count: number
  user_count: number
  active_count: number
  disabled_count: number
}