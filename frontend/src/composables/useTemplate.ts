/**
 * 模板操作 composable
 */
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import * as templateApi from '@/api/template'
import type { TemplateInfo } from '@/types'

interface UseTemplateOptions {
  onSuccess?: () => void
  onError?: (err: any) => void
}

export function useTemplate(options?: UseTemplateOptions) {
  const loading = ref(false)
  const templates = ref<TemplateInfo[]>([])
  const selectedTemplate = ref<TemplateInfo | null>(null)

  /** 加载模板列表 (从后端API获取) */
  async function fetchTemplates() {
    loading.value = true
    try {
      const res: any = await templateApi.getTemplateList()
      // 后端返回格式: { code:20000, data: [...] }
      const data = res?.data ?? res
      templates.value = Array.isArray(data) ? data.map((t: any) => ({
        tid: t.tid,
        tname: t.tname,
        description: t.description ?? '',
        fields: (t.fields ?? []).map((f: any) => ({
          key: f.key,
          label: f.label,
          type: f.type,
          required: !!f.required,
          default_value: f.default_value ?? null,
          placeholder: f.placeholder ?? '',
          options: f.options ?? [],
          order: f.order ?? 0,
        })),
      })) : []
    } catch (e) {
      console.error('[useTemplate] Failed:', e)
      options?.onError?.(e)
    } finally {
      loading.value = false
    }
  }

  /**
   * 选择模板
   */
  function selectTemplate(template: TemplateInfo) {
    selectedTemplate.value = template
  }

  return {
    loading,
    templates,
    selectedTemplate,
    fetchTemplates,
    selectTemplate,
  }
}
