/**
 * 操作记录相关API
 */
import request from './index'

/** 操作日志列表 */
export function getOperationLogs(params: {
  page?: number
  page_size?: number
  action?: string
  mac?: string
  start_time?: string
  end_time?: string
}) {
  return request.get('/operation-logs', { params })
}

/** 设备推送日志列表 */
export function getPushLogs(params: {
  page?: number
  page_size?: number
  task_id?: number
  mac?: string
  start_time?: string
  end_time?: string
  result?: string
}) {
  return request.get('/push-logs', { params })
}

/** 设备事件日志列表 */
export function getDeviceEventLogs(params: {
  page?: number
  page_size?: number
  mac?: string
  event_type?: string
  start_time?: string
  end_time?: string
}) {
  return request.get('/device-events-logs', { params })
}
