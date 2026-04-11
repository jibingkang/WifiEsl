import service from './index'

export interface Device {
  id: string
  mac: string
  ip: string
  name?: string
  is_online: boolean
  voltage?: number
  rssi?: number
  usb_state?: number
  device_type?: string
  screen_type?: string
  sn?: string
  sw_version?: number
  hw_version?: number
  created_at: string
  updated_at: string
}

export interface DeviceListParams {
  page?: number
  page_size?: number
  status?: string
  search?: string
  group_id?: string
}

export const deviceApi = {
  /**
   * 获取设备列表 (GET /user/api/rest/devices)
   */
  getDeviceList(params: DeviceListParams = {}): Promise<any> {
    return service.get('/devices', { params })
  },
  
  /**
   * 获取单个设备详情 (GET /user/api/rest/devices/:id)
   */
  getDeviceById(id: string): Promise<any> {
    return service.get(`/devices/${id}`)
  },
  
  /**
   * 根据MAC获取设备 (GET /user/api/rest/devices/mac/:mac)
   */
  getDeviceByMac(mac: string): Promise<any> {
    return service.get(`/devices/mac/${mac}`)
  },
  
  /**
   * 添加设备 (POST /user/api/rest/devices)
   */
  createDevice(data: Partial<Device>): Promise<any> {
    return service.post('/devices', data)
  },
  
  /**
   * 更新设备 (PUT /user/api/rest/devices/:id)
   */
  updateDevice(id: string, data: Partial<Device>): Promise<any> {
    return service.put(`/devices/${id}`, data)
  },
  
  /**
   * 删除设备 (DELETE /user/api/rest/devices/:id)
   */
  deleteDevice(id: string): Promise<any> {
    return service.delete(`/devices/${id}`)
  },
  
  // ==================== 设备控制接口 ====================
  
  /**
   * 设置LED灯状态 (POST /user/api/mqtt/publish/:mac/led)
   */
  controlLED(mac: string, red: number, green: number, blue: number): Promise<any> {
    return service.post(`/mqtt/publish/${mac}/led`, { red, green, blue })
  },
  
  /**
   * 获取电池电量 (POST /user/api/mqtt/publish/:mac/battery)
   */
  queryBattery(mac: string): Promise<any> {
    return service.post(`/mqtt/publish/${mac}/battery`)
  },
  
  /**
   * 重启设备 (POST /user/api/mqtt/publish/:mac/reboot)
   */
  rebootDevice(mac: string): Promise<any> {
    return service.post(`/mqtt/publish/${mac}/reboot`)
  },
  
  /**
   * 更新屏幕图片 (POST /user/api/mqtt/publish/:mac/display)
   */
  updateDisplay(mac: string, imgsrc?: string, templateData?: any): Promise<any> {
    const payload = imgsrc 
      ? { algorithm: 'floyd-steinberg', imgsrc }
      : templateData
    return service.post(`/mqtt/publish/${mac}/display`, payload)
  },
  
  /**
   * 调用模板显示 (POST /user/api/mqtt/publish/{:mac}/template/{:templateId})
   */
  applyTemplate(mac: string, templateId: string, data: Record<string, any>): Promise<any> {
    return service.post(`/mqtt/publish/${mac}/template/${templateId}`, data)
  },

  // ==================== 模板-设备绑定接口（数据更新页面设备列表持久化）====================

  /**
   * 保存/批量保存模板-设备绑定 (POST /api/v1/devices/template-devices)
   */
  saveTemplateBindings(tid: string, macs: string[]): Promise<any> {
    return service.post('/devices/template-devices', { tid, macs })
  },

  /**
   * 查询模板绑定的设备MAC列表 (GET /api/v1/devices/template-devices?tid=xxx)
   */
  getTemplateBoundMacs(tid: string): Promise<any> {
    return service.get('/devices/template-devices', { params: { tid } })
  },

  /**
   * 移除单条模板-设备绑定 (DELETE /api/v1/devices/template-devices/:tid/:mac)
   */
  removeTemplateBinding(tid: string, mac: string): Promise<any> {
    return service.delete(`/devices/template-devices/${tid}/${mac}`)
  },
}
