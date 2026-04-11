import service from './index'

// ── 类型定义 ──

export interface TaskSummary {
  id: number
  name: string
  tid: string
  tname: string
  status: string // draft / sent / completed / cancelled
  total_devices: number
  success_count: number
  failed_count: number
  created_at: string
  updated_at: string
}

export interface TaskDeviceInfo {
  id: number
  task_id: number
  mac: string
  custom_data: string | Record<string, any>
  update_status: string // pending / sent / success / failed
  error_msg: string
  retry_count: number
  sent_at?: string       // 推送开始时间
  finished_at?: string   // 完成时间 (success/failed 时有值)
}

export interface TaskDetail extends TaskSummary {
  devices: TaskDeviceInfo[]
  progress: {
    pending: number
    sent: number
    success: number
    failed: number
  }
}

export interface CreateTaskData {
  name?: string
  tid: string
}

export interface UpdateTaskData {
  name?: string
  default_data?: Record<string, any>
  status?: string
}

// ── API 封装 ──

export const taskApi = {
  /**
   * 创建更新任务
   */
  createTask(data: CreateTaskData): Promise<any> {
    return service.post('/tasks', data)
  },

  /**
   * 获取任务列表 (分页)
   */
  getTaskList(params?: { page?: number; pageSize?: number; status?: string }): Promise<any> {
    return service.get('/tasks', { params })
  },

  /**
   * 获取任务详情（含设备列表+状态统计）
   */
  getTaskDetail(taskId: number): Promise<any> {
    return service.get(`/tasks/${taskId}`)
  },

  /**
   * 更新任务信息
   */
  updateTask(taskId: number, data: UpdateTaskData): Promise<any> {
    return service.put(`/tasks/${taskId}`, data)
  },

  /**
   * 删除任务
   */
  deleteTask(taskId: number): Promise<any> {
    return service.delete(`/tasks/${taskId}`)
  },

  // ==================== 设备管理 ====================

  /**
   * 批量添加设备到任务
   */
  addTaskDevices(taskId: number, macs: string[], customDataMap?: Record<string, any>): Promise<any> {
    return service.post(`/tasks/${taskId}/devices`, {
      macs,
      custom_data_map: customDataMap || {},
    })
  },

  /**
   * 从任务中移除单台设备
   */
  removeTaskDevice(taskId: number, mac: string): Promise<any> {
    return service.delete(`/tasks/${taskId}/devices/${mac}`)
  },

  /**
   * 更新单台设备的自定义数据
   */
  updateTaskDeviceData(taskId: number, mac: string, customData: Record<string, any>): Promise<any> {
    return service.put(`/tasks/${taskId}/devices/${mac}`, { custom_data: customData })
  },

  /**
   * 更新单台设备的推送状态（前端单推时标记sent/failed）
   */
  updateTaskDeviceStatus(taskId: number, mac: string, status: string, errorMsg?: string): Promise<any> {
    return service.put(`/tasks/${taskId}/devices/${mac}/status`, { update_status: status, error_msg: errorMsg || '' })
  },

  /**
   * 获取任务的设备列表
   */
  getTaskDevices(taskId: number): Promise<any> {
    return service.get(`/tasks/${taskId}/devices`)
  },

  // ==================== 执行与进度 ====================

  /**
   * ⭐ 执行任务推送（核心接口）
   * @param macs 可选，指定要推送的设备MAC列表
   */
  executeTask(taskId: number, body?: { macs?: string[] }): Promise<any> {
    return service.post(`/tasks/${taskId}/execute`, body || {})
  },

  /**
   * 获取推送进度轮询
   */
  getTaskProgress(taskId: number): Promise<any> {
    return service.get(`/tasks/${taskId}/progress`)
  },
}
