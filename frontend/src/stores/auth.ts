import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import type { TokenInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>('')
  const userInfo = ref<any>(null)
  const isAuthenticated = ref(false)

  // 登录
  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login({ username, password })
      
      console.log('登录API响应:', response)
      
      // 处理不同的响应格式
      let tokenData = ''
      let userData: any = null
      
      // 情况1: axios拦截器返回了data字段 (后端返回 {code, message, data})
      if (response && response.token) {
        // 直接有token字段
        tokenData = response.token
        userData = response.user || { username, role: response.role || 'user' }
      } 
      // 情况2: 响应有code和data字段 (后端原始响应)
      else if (response && response.code === 20000 && response.data) {
        const data = response.data
        tokenData = data.token || data.access_token || data.apiKey || data.apikey || ''
        userData = data.user || { username, role: data.role || 'user' }
      }
      // 情况3: 其他格式
      else if (response && response.data && response.data.token) {
        tokenData = response.data.token
        userData = response.data.user || { username, role: response.data.role || 'user' }
      }
      // 情况4: 失败响应
      else {
        const errorMsg = response?.message || response?.data?.message || '登录失败'
        console.error('登录失败响应:', response)
        throw new Error(errorMsg)
      }
      
      // 验证获取到的数据
      if (!tokenData) {
        console.error('未获取到token:', response)
        throw new Error('登录失败: 未获取到认证令牌')
      }
      
      // 保存状态
      token.value = tokenData
      userInfo.value = userData
      isAuthenticated.value = true
      
      // 保存到localStorage
      localStorage.setItem('wifi_esl_token', tokenData)
      localStorage.setItem('wifi_esl_user', JSON.stringify(userData))
      
      console.log('登录成功，用户信息:', userData)
      return { success: true, data: { token: tokenData, user: userData } }
      
    } catch (error: any) {
      console.error('登录捕获的错误:', error)
      throw new Error(error.message || '登录失败，请检查用户名和密码')
    }
  }

  // 登出
  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      // 清除本地状态
      token.value = ''
      userInfo.value = null
      isAuthenticated.value = false
      localStorage.removeItem('wifi_esl_token')
      localStorage.removeItem('wifi_esl_user')
      sessionStorage.clear()
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const response = await authApi.getUserInfo()
      if (response.code === 20000) {
        userInfo.value = response.data
        isAuthenticated.value = true
        return userInfo.value
      } else {
        throw new Error(response.message || '获取用户信息失败')
      }
    } catch (error: any) {
      isAuthenticated.value = false
      throw error
    }
  }

  // 检查登录状态
  const checkAuth = () => {
    const savedToken = localStorage.getItem('wifi_esl_token')
    const savedUser = localStorage.getItem('wifi_esl_user')
    
    if (savedToken && savedUser) {
      try {
        token.value = savedToken
        userInfo.value = JSON.parse(savedUser)
        isAuthenticated.value = true
        return true
      } catch (error) {
        console.error('解析保存的用户信息失败:', error)
        return false
      }
    }
    
    return false
  }

  // 获取当前用户角色
  const getUserRole = () => {
    return userInfo.value?.role || 'user'
  }

  // 检查是否有权限
  const hasPermission = (requiredRole: string) => {
    const userRole = getUserRole()
    const roleHierarchy = ['admin', 'user', 'operator']
    
    const userIndex = roleHierarchy.indexOf(userRole)
    const requiredIndex = roleHierarchy.indexOf(requiredRole)
    
    return userIndex <= requiredIndex // 角色等级越高，权限越大
  }

  return {
    // 状态
    token,
    userInfo,
    isAuthenticated,
    
    // 方法
    login,
    logout,
    fetchUserInfo,
    checkAuth,
    getUserRole,
    hasPermission,
  }
})

export default useAuthStore