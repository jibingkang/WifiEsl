/**
 * 本地存储封装 (统一管理localStorage/sessionStorage)
 */

const PREFIX = 'wifi_esl_'

function getKey(key: string): string {
  return `${PREFIX}${key}`
}

/**
 * 存储数据到 localStorage
 */
export function setStorage<T>(key: string, value: T): void {
  try {
    localStorage.setItem(getKey(key), JSON.stringify(value))
  } catch (e) {
    console.warn('[Storage] set failed:', key, e)
  }
}

/**
 * 从 localStorage 读取数据
 */
export function getStorage<T>(key: string, defaultValue?: T): T | undefined {
  try {
    const raw = localStorage.getItem(getKey(key))
    return raw ? JSON.parse(raw) : defaultValue
  } catch {
    return defaultValue
  }
}

/** 删除 localStorage 数据 */
export function removeStorage(key: string): void {
  localStorage.removeItem(getKey(key))
}

// ==================== 常用存储键 ====================
export const StorageKeys = {
  TOKEN: 'token',
  USER_INFO: 'user_info',
  THEME: 'theme',           // light / dark / auto
  SIDEBAR_STATUS: 'sidebar_collapsed',
  DEVICE_FILTERS: 'device_filters',
  LAST_VISITED_ROUTE: 'last_route',
} as const
