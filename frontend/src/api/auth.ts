import service from './index'

export interface LoginParams {
  username: string
  password: string
}

export interface TokenInfo {
  token: string
  expiresIn: number
  user: {
    id: string
    username: string
    role: string
    avatar?: string
    apiKey: string
  }
}

export const authApi = {
  /**
   * 用户登录
   */
  login(params: LoginParams): Promise<any> {
    // 对接WIFI系统API: POST /user/api/login
    return service.post('/auth/login', params)
  },
  
  /**
   * 登出
   */
  logout(): Promise<any> {
    return service.post('/auth/logout')
  },
  
  /**
   * 获取当前用户信息
   */
  getUserInfo(): Promise<any> {
    return service.get('/auth/userinfo')
  },

  /**
   * 获取当前用户完整信息（含WIFI配置摘要）
   */
  getProfile(): Promise<any> {
    return service.get('/auth/profile')
  },
}
