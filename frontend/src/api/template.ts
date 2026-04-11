/**
 * 模板相关API
 */
import request from './index'

/** 模板列表 */
export function getTemplateList() {
  return request.get('/templates')
}

/** 获取单个模板详情 */
export function getTemplateDetail(tid: string) {
  return request.get(`/templates/${tid}`)
}

/** 调用模板显示到指定设备 */
export function applyTemplateToDevice(mac: string, templateId: string, data: Record<string, any>) {
  return request.post(`/mqtt/publish/${mac}/template/${templateId}`, { data })
}

/** 批量应用模板 */
export function batchApplyTemplate(
  macs: string[],
  templateId: string,
  dataList: Record<string, any>[],
  templateName?: string,
) {
  return request.post('/batch/template', {
    macs,
    templateId,
    templateName: templateName || '',
    dataList,
  })
}

/** 创建模板 */
export function createTemplate(data: Record<string, any>) {
  return request.post('/templates', data)
}

/** 更新模板 */
export function updateTemplate(tid: string, data: Record<string, any>) {
  return request.put(`/templates/${tid}`, data)
}

/** 删除模板 */
export function deleteTemplate(tid: string) {
  return request.delete(`/templates/${tid}`)
}

/** 获取更新历史记录（分页） */
export function getUpdateHistory(page = 1, pageSize = 20) {
  return request.get('/update-history', { params: { page, pageSize } })
}
