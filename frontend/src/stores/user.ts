import { defineStore } from 'pinia'
import { ref } from 'vue'
import userApi from '@/api/user'
import type { User, UserListQuery, UserFormData, UserStats } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  // 状态
  const userList = ref<User[]>([])
  const total = ref(0)
  const currentUser = ref<User | null>(null)
  const loading = ref(false)
  const queryParams = ref<UserListQuery>({
    page: 1,
    page_size: 10,
  })

  // 获取用户列表
  const fetchUsers = async (params?: UserListQuery) => {
    try {
      loading.value = true
      if (params) {
        queryParams.value = { ...queryParams.value, ...params }
      }
      
      const response = await userApi.list(queryParams.value)
      userList.value = response.items || []
      total.value = response.total || 0
      return response
    } finally {
      loading.value = false
    }
  }

  // 获取用户详情
  const fetchUserDetail = async (id: number) => {
    try {
      loading.value = true
      const user = await userApi.detail(id)
      return user
    } finally {
      loading.value = false
    }
  }

  // 创建用户
  const createUser = async (data: UserFormData) => {
    try {
      loading.value = true
      const user = await userApi.create(data)
      
      // 将新用户添加到列表中（如果不在当前页面，会在刷新时获取）
      if (user && user.id) {
        // 检查是否已存在
        const existingIndex = userList.value.findIndex(u => u.id === user.id)
        if (existingIndex === -1) {
          userList.value.push(user as User)
          total.value += 1
        }
      }
      
      return user
    } finally {
      loading.value = false
    }
  }

  // 更新用户
  const updateUser = async (id: number, data: UserFormData) => {
    try {
      loading.value = true
      const user = await userApi.update(id, data)
      return user
    } finally {
      loading.value = false
    }
  }

  // 删除用户
  const deleteUser = async (id: number) => {
    try {
      loading.value = true
      await userApi.delete(id)
      // 从列表中移除
      const index = userList.value.findIndex(user => user.id === id)
      if (index !== -1) {
        userList.value.splice(index, 1)
        total.value -= 1
      }
    } finally {
      loading.value = false
    }
  }

  // 获取用户WIFI配置
  const fetchUserWifiConfig = async (id: number) => {
    try {
      loading.value = true
      const config = await userApi.getWifiConfig(id)
      return config
    } finally {
      loading.value = false
    }
  }

  // 更新用户WIFI配置
  const updateUserWifiConfig = async (id: number, data: { wifi_username?: string; wifi_password?: string; wifi_apikey?: string; wifi_base_url?: string }) => {
    try {
      loading.value = true
      const config = await userApi.updateWifiConfig(id, data)
      return config
    } finally {
      loading.value = false
    }
  }

  // 重置查询参数
  const resetQuery = () => {
    queryParams.value = {
      page: 1,
      page_size: 10,
    }
  }

  // 获取用户统计信息（模拟，实际应从后端获取）
  const getUserStats = (): UserStats => {
    const stats: UserStats = {
      total: userList.value.length,
      admin_count: userList.value.filter(user => user.role === 'admin').length,
      operator_count: userList.value.filter(user => user.role === 'operator').length,
      user_count: userList.value.filter(user => user.role === 'user').length,
      active_count: userList.value.filter(user => user.status === 'active').length,
      disabled_count: userList.value.filter(user => user.status === 'disabled').length,
    }
    return stats
  }

  return {
    // 状态
    userList,
    total,
    currentUser,
    loading,
    queryParams,
    
    // 方法
    fetchUsers,
    fetchUserDetail,
    createUser,
    updateUser,
    deleteUser,
    fetchUserWifiConfig,
    updateUserWifiConfig,
    resetQuery,
    getUserStats,
  }
})

export default useUserStore