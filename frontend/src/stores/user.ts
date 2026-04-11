import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LoginParams, UserInfo, TokenInfo } from '@/types'
import { authApi } from '@/api/auth'

const TOKEN_KEY = 'wifi_esl_token'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const userInfo = ref<UserInfo | null>(null)
  const apiKey = ref<string | null>(null)
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username ?? '')
  const role = computed(() => userInfo.value?.role ?? 'viewer')

  /**
   * 登录 - 调用后端真实接口
   */
  async function login(params: LoginParams): Promise<TokenInfo> {
    loading.value = true
    try {
      // 调用后端登录代理
      const res: any = await authApi.login(params)

      // 响应拦截器已解包 {code, data} → res 直接就是 { token, expiresIn, user }
      const tokenInfo: TokenInfo = {
        token: res.token,
        expiresIn: res.expiresIn ?? 86400,
        user: res.user || {
          id: '1',
          username: params.username,
          role: 'admin',
          avatar: '',
          apiKey: res.apiKey || '',
        },
      }

      // 存储Token
      setToken(tokenInfo.token)
      userInfo.value = tokenInfo.user
      apiKey.value = tokenInfo.user.apiKey

      return tokenInfo
    } finally {
      loading.value = false
    }
  }

  /**
   * 设置Token
   */
  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem(TOKEN_KEY, newToken)
  }

  /**
   * 登出
   */
  async function logout() {
    token.value = null
    userInfo.value = null
    apiKey.value = null
    localStorage.removeItem(TOKEN_KEY)

    // 跳转到登录页（在组件中调用）
    window.location.href = '/login'
  }

  /**
   * 检查Token有效性
   */
  function checkAuth(): boolean {
    if (!token.value) return false

    // TODO: 实际项目中应检查Token是否过期
    return true
  }

  return {
    token,
    userInfo,
    apiKey,
    loading,
    isLoggedIn,
    username,
    role,
    login,
    logout,
    checkAuth,
  }
})
