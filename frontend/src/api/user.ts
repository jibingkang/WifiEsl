import service from './index'
import type { User, UserListQuery, UserCreateRequest, UserUpdateRequest, WifiConfig } from '@/types/user'

export const userApi = {
  /**
   * 获取用户列表
   */
  list(query?: UserListQuery) {
    return service.get<{ items: User[]; total: number }>('/users', {
      params: query,
    })
  },

  /**
   * 获取用户详情
   */
  detail(id: number) {
    return service.get<User>(`/users/${id}`)
  },

  /**
   * 创建用户
   */
  create(data: UserCreateRequest) {
    return service.post<User>('/users', data)
  },

  /**
   * 更新用户
   */
  update(id: number, data: UserUpdateRequest) {
    return service.put<User>(`/users/${id}`, data)
  },

  /**
   * 删除用户
   */
  delete(id: number) {
    return service.delete(`/users/${id}`)
  },

  /**
   * 获取用户WIFI配置
   */
  getWifiConfig(id: number) {
    return service.get<WifiConfig>(`/users/${id}/wifi-config`)
  },

  /**
   * 更新用户WIFI配置
   */
  updateWifiConfig(id: number, data: { wifi_username?: string; wifi_password?: string; wifi_apikey?: string; wifi_base_url?: string; wifi_mqtt_broker?: string }) {
    return service.put<WifiConfig>(`/users/${id}/wifi-config`, data)
  },
}

export default userApi