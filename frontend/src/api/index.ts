import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'

// 创建实例
const service: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 注入Token
    const token = localStorage.getItem('wifi_esl_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    const url = response.config.url || ''

    console.log('API响应:', { url, data: res })

    // 特殊处理：登录接口不进行拦截器处理，直接返回原始响应
    if (url.includes('/auth/login')) {
      console.log('登录接口，返回原始响应')
      return res
    }

    // 统一错误处理
    if (res.code && res.code !== 20000) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }

    // 返回 data 字段给调用方 (前端 store 期望 {items, total} 格式)
    return res.data ?? res
  },
  (error) => {
    const status = error.response?.status
    
    switch (status) {
      case 401:
        ElMessageBox.confirm('登录已过期，请重新登录', '提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning',
        }).then(() => {
          localStorage.removeItem('wifi_esl_token')
          router.push('/login')
        })
        break
        
      case 403:
        ElMessage.error('没有权限访问该资源')
        break
        
      case 404:
        ElMessage.error('请求的资源不存在')
        break
        
      case 500:
        ElMessage.error('服务器内部错误，请稍后重试')
        break
        
      default:
        if (!error.response) {
          ElMessage.error('网络连接异常，请检查网络')
        }
    }
    
    return Promise.reject(error)
  }
)

export default service
