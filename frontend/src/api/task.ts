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

// ── 子表行数据 ──

export interface TaskDeviceRow {
  id: number
  task_device_id: number
  sort_order: number
  custom_data: string | Record<string, any>
  created_at: string
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
  rows?: TaskDeviceRow[] // [NEW] 子表行列表
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
  tid?: string
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
   * @param rowSelections 可选，指定每个设备要推送的行ID，格式 {mac: row_id}，不传则默认推送第一行
   */
  executeTask(taskId: number, body?: { macs?: string[]; rowSelections?: Record<string, number> }): Promise<any> {
    // 转换驼峰为下划线以匹配后端API
    const apiBody: any = {}
    if (body?.macs) apiBody.macs = body.macs
    if (body?.rowSelections) apiBody.row_selections = body.rowSelections
    return service.post(`/tasks/${taskId}/execute`, apiBody)
  },

  /**
   * 获取推送进度轮询
   */
  getTaskProgress(taskId: number): Promise<any> {
    return service.get(`/tasks/${taskId}/progress`)
  },

  // ==================== 子表数据管理 (task_device_rows) ====================

  /**
   * 获取某设备在任务中的所有子表行数据
   */
  getDeviceRows(taskId: number, mac: string): Promise<any> {
    return service.get(`/tasks/${taskId}/devices/${mac}/rows`)
  },

  /**
   * 为某设备添加一条子表行数据
   */
  addDeviceRow(taskId: number, mac: string, customData: Record<string, any>, sortOrder?: number): Promise<any> {
    return service.post(`/tasks/${taskId}/devices/${mac}/rows`, { custom_data: customData, sort_order: sortOrder })
  },

  /**
   * 更新单条子表行的自定义数据
   */
  updateDeviceRow(rowId: number, customData: Record<string, any>): Promise<any> {
    return service.put(`/tasks/device-rows/${rowId}`, { custom_data: customData })
  },

  /**
   * 删除单条子表行
   */
  deleteDeviceRow(rowId: number): Promise<any> {
    return service.delete(`/tasks/device-rows/${rowId}`)
  },

  /**
   * 批量添加子表行数据（导入时使用）
   * @param mode 'overwrite' 先清空再插入 | 'append' 追加到现有行之后
   */
  batchAddDeviceRows(taskId: number, mac: string, rows: Record<string, any>[], mode: 'overwrite' | 'append' = 'overwrite'): Promise<any> {
    return service.post(`/tasks/${taskId}/devices/${mac}/rows/batch`, { rows, mode })
  },

  /**
   * 清空某设备的所有子表行数据
   */
  clearDeviceRows(taskId: number, mac: string): Promise<any> {
    return service.delete(`/tasks/${taskId}/devices/${mac}/rows`)
  },
}
