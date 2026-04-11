<template>
  <div class="template-manage">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">模板管理</h2>
        <p class="page-desc">新增、编辑、删除模板，支持JSON文件导入或手动输入</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>新增模板
        </el-button>
        <el-upload
          class="upload-btn"
          :show-file-list="false"
          :on-change="handleJsonUpload"
          accept=".json"
          :before-upload="() => false"
        >
          <el-button type="success">
            <el-icon><Upload /></el-icon>导入JSON文件
          </el-button>
        </el-upload>
        <el-button type="info" @click="showJsonInputDialog">
          <el-icon><EditPen /></el-icon>手动输入JSON
        </el-button>
      </div>
    </div>

    <!-- 模板列表 -->
    <div class="template-list">
      <div v-if="loading" class="loading-wrap">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="templates.length === 0" class="empty-wrap">
        <el-empty description="暂无模板">
          <el-button type="primary" @click="showCreateDialog">创建第一个模板</el-button>
        </el-empty>
      </div>
      <div v-else class="grid">
        <el-card
          v-for="tpl in templates"
          :key="tpl.tid"
          class="template-card"
          shadow="hover"
        >
          <template #header>
            <div class="card-header">
              <div class="title-section">
                <h3>{{ tpl.tname }}</h3>
                <el-tag v-if="tpl.screen_type" size="small">{{ tpl.screen_type }}</el-tag>
              </div>
              <div class="actions">
                <el-button type="primary" text size="small" @click="showEditDialog(tpl)">
                  编辑
                </el-button>
                <el-button type="danger" text size="small" @click="handleDelete(tpl)">
                  删除
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="card-content">
            <p class="desc" v-if="tpl.description">{{ tpl.description }}</p>
            <p class="desc" v-else style="color: #999;">无描述</p>
            
            <div class="fields-info">
              <el-tag size="small" type="info">
                <el-icon><Document /></el-icon>
                字段: {{ tpl.fields?.length || 0 }}个
              </el-tag>
              <div class="template-id">
                <el-text type="info" size="small">ID: {{ tpl.tid }}</el-text>
              </div>
            </div>
            
            <div v-if="tpl.fields && tpl.fields.length > 0" class="fields-preview">
              <div class="field-list">
                <div v-for="field in tpl.fields" :key="field.key" class="field-item">
                  <div class="field-key">{{ field.key }}</div>
                  <div class="field-details">
                    <span class="field-label">{{ field.label }}</span>
                    <span class="field-type">{{ field.type }}</span>
                    <el-tag v-if="field.required" size="small" type="danger">必填</el-tag>
                    <el-tag v-if="field.default_value !== undefined" size="small" type="success">
                      默认: {{ field.default_value }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 创建/编辑模板弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="template-form"
      >
        <el-form-item label="模板ID" prop="tid">
          <el-input
            v-model="formData.tid"
            placeholder="如: test-template-001"
            :disabled="isEditing"
          />
        </el-form-item>
        
        <el-form-item label="模板名称" prop="tname">
          <el-input v-model="formData.tname" placeholder="请输入模板名称" />
        </el-form-item>
        
        <el-form-item label="描述信息" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        
        <el-form-item label="屏幕类型" prop="screen_type">
          <el-select v-model="formData.screen_type" placeholder="请选择屏幕类型" clearable>
            <el-option label="单色屏" value="monochrome" />
            <el-option label="彩色屏" value="color" />
            <el-option label="黑白屏" value="bw" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        
        <!-- 字段管理 -->
        <div class="fields-section">
          <div class="section-header">
            <h4>字段定义</h4>
            <el-button type="primary" size="small" @click="addField">
              <el-icon><Plus /></el-icon>添加字段
            </el-button>
          </div>
          
          <div v-if="formData.fields.length === 0" class="fields-empty">
            <el-empty description="暂无字段定义" :image-size="60" />
          </div>
          
          <div v-else class="field-items">
            <div
              v-for="(field, index) in formData.fields"
              :key="index"
              class="field-item-draggable"
            >
              <div class="field-header">
                <div class="field-title">
                  <el-icon><Grid /></el-icon>
                  <span>字段 {{ index + 1 }}: {{ field.label || '未命名' }}</span>
                </div>
                <div class="field-actions">
                  <el-button type="danger" text size="small" @click="removeField(index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              
              <div class="field-form">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="字段Key" :prop="`fields[${index}].key`" :rules="fieldRules.key">
                      <el-input v-model="field.key" placeholder="如: text-0" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="显示名称" :prop="`fields[${index}].label`" :rules="fieldRules.label">
                      <el-input v-model="field.label" placeholder="如: 商品名称" />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row :gutter="16">
                  <el-col :span="8">
                    <el-form-item label="字段类型" :prop="`fields[${index}].type`" :rules="fieldRules.type">
                      <el-select v-model="field.type" placeholder="请选择">
                        <el-option label="文本" value="text" />
                        <el-option label="数字" value="number" />
                        <el-option label="日期" value="date" />
                        <el-option label="图片" value="image" />
                        <el-option label="选项" value="select" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="是否必填">
                      <el-switch v-model="field.required" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="排序">
                      <el-input-number v-model="field.order" :min="0" />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-form-item label="默认值">
                      <el-input v-model="field.default_value" placeholder="默认值" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="占位符">
                      <el-input v-model="field.placeholder" placeholder="占位符" />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-row v-if="field.type === 'select'" :gutter="16">
                  <el-col :span="24">
                    <el-form-item label="选项">
                      <el-input
                        v-model="field.options"
                        type="textarea"
                        :rows="2"
                        placeholder="每行一个选项，如: 选项1\n选项2"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>
              </div>
            </div>
          </div>
        </div>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 手动输入JSON数据弹窗 -->
    <el-dialog
      v-model="jsonDialogVisible"
      title="手动输入JSON数据"
      width="600px"
    >
      <div class="json-input-section">
        <el-alert
          title="JSON格式示例"
          type="info"
          :closable="false"
          description='{"tid":"template-id","tname":"模板名称","description":"描述","screen_type":"monochrome","fields":[{"key":"text-0","label":"文本","type":"text","required":true}]}'
          show-icon
          style="margin-bottom: 16px;"
        />
        
        <el-input
          v-model="jsonInput"
          type="textarea"
          :rows="12"
          placeholder="请输入JSON格式的模板数据..."
          resize="none"
          class="json-textarea"
        />
        
        <div style="margin-top: 16px;">
          <el-text type="info" size="small">
            提示: 也可以直接粘贴从 template.json 文件复制的内容
          </el-text>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="jsonDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="parseJsonInput" :loading="jsonProcessing">
          解析并添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type UploadFile } from 'element-plus'
import {
  Plus,
  Upload,
  EditPen,
  Document,
  Grid,
  Delete,
} from '@element-plus/icons-vue'
import {
  getTemplateList,
  createTemplate,
  updateTemplate,
  deleteTemplate,
} from '@/api/template'

// 辅助函数：处理模板API响应（因为拦截器会提取data字段）
async function handleTemplateApiCall<T>(apiCall: Promise<any>): Promise<{ success: boolean; data?: T; message?: string }> {
  try {
    const res = await apiCall
    // 如果res是数组，说明是列表数据
    if (Array.isArray(res)) {
      return { success: true, data: res as T }
    }
    // 如果res有code字段（旧格式或错误格式）
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 20000) {
        return { success: true, data: res.data as T, message: res.message }
      } else {
        return { success: false, message: res.message || '操作失败' }
      }
    }
    // 其他情况（可能是成功但没有code字段）
    return { success: true, data: res as T }
  } catch (error: any) {
    return { success: false, message: error.message || '请求失败' }
  }
}

interface TemplateField {
  key: string
  label: string
  type: 'text' | 'number' | 'date' | 'image' | 'select'
  required?: boolean
  default_value?: string
  placeholder?: string
  options?: string
  order?: number
}

interface TemplateInfo {
  tid: string
  tname: string
  description?: string
  screen_type?: string
  fields?: TemplateField[]
}

// 响应式数据
const loading = ref(true)
const templates = ref<TemplateInfo[]>([])
const dialogVisible = ref(false)
const jsonDialogVisible = ref(false)
const submitting = ref(false)
const jsonProcessing = ref(false)
const formRef = ref<FormInstance>()
const jsonInput = ref('')
const isEditing = ref(false)
const editingTemplateId = ref('')

const formData = reactive({
  tid: '',
  tname: '',
  description: '',
  screen_type: '',
  fields: [] as TemplateField[]
})

// 表单验证规则
const formRules = {
  tid: [
    { required: true, message: '请输入模板ID', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  tname: [
    { required: true, message: '请输入模板名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

const fieldRules = {
  key: [
    { required: true, message: '请输入字段Key', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  label: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择字段类型', trigger: 'change' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEditing.value ? '编辑模板' : '新增模板')

// 方法
const fetchTemplates = async () => {
  loading.value = true
  try {
    const result = await handleTemplateApiCall<Array<any>>(getTemplateList())
    if (result.success) {
      templates.value = result.data || []
    } else {
      ElMessage.error(result.message || '获取模板列表失败')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取模板列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  isEditing.value = false
  editingTemplateId.value = ''
  resetForm()
  dialogVisible.value = true
}

const showEditDialog = (tpl: TemplateInfo) => {
  isEditing.value = true
  editingTemplateId.value = tpl.tid
  formData.tid = tpl.tid
  formData.tname = tpl.tname
  formData.description = tpl.description || ''
  formData.screen_type = tpl.screen_type || ''
  formData.fields = JSON.parse(JSON.stringify(tpl.fields || []))
  dialogVisible.value = true
}

const resetForm = () => {
  formData.tid = ''
  formData.tname = ''
  formData.description = ''
  formData.screen_type = ''
  formData.fields = []
}

const addField = () => {
  formData.fields.push({
    key: '',
    label: '',
    type: 'text',
    required: false,
    order: formData.fields.length
  })
}

const removeField = (index: number) => {
  formData.fields.splice(index, 1)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      // 格式化数据以匹配后端格式
      const submitData = {
        tid: formData.tid,
        tname: formData.tname,
        description: formData.description,
        screen_type: formData.screen_type,
        fields: formData.fields.map(field => ({
          key: field.key,
          label: field.label,
          type: field.type,
          required: !!field.required,
          default_value: field.default_value,
          placeholder: field.placeholder,
          options: field.options,
          order: field.order || 0
        }))
      }
      
      if (isEditing.value) {
        // 更新模板
        const result = await handleTemplateApiCall(updateTemplate(editingTemplateId.value, submitData))
        if (result.success) {
          ElMessage.success(result.message || '模板更新成功')
          await fetchTemplates()
          dialogVisible.value = false
        } else {
          ElMessage.error(result.message || '模板更新失败')
        }
      } else {
        // 创建模板
        const result = await handleTemplateApiCall(createTemplate(submitData))
        if (result.success) {
          ElMessage.success(result.message || '模板创建成功')
          await fetchTemplates()
          dialogVisible.value = false
        } else {
          ElMessage.error(result.message || '模板创建失败')
        }
      }
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = (tpl: TemplateInfo) => {
  ElMessageBox.confirm(
    `确定要删除模板 "${tpl.tname}" 吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const result = await handleTemplateApiCall(deleteTemplate(tpl.tid))
      if (result.success) {
        ElMessage.success(result.message || '模板删除成功')
        await fetchTemplates()
      } else {
        ElMessage.error(result.message || '删除失败')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '删除失败')
    }
  }).catch(() => {})
}

const handleJsonUpload = (file: UploadFile) => {
  if (!file.raw) return
  
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const content = e.target?.result as string
      const data = JSON.parse(content)
      await processJsonData(data)
    } catch (error) {
      ElMessage.error('JSON文件解析失败，请检查格式')
    }
  }
  reader.readAsText(file.raw)
}

const showJsonInputDialog = () => {
  jsonInput.value = ''
  jsonDialogVisible.value = true
}

const parseJsonInput = async () => {
  if (!jsonInput.value.trim()) {
    ElMessage.warning('请输入JSON数据')
    return
  }
  
  jsonProcessing.value = true
  try {
    const data = JSON.parse(jsonInput.value)
    await processJsonData(data)
    jsonDialogVisible.value = false
  } catch (error) {
    ElMessage.error('JSON解析失败，请检查格式是否正确')
  } finally {
    jsonProcessing.value = false
  }
}

const processJsonData = async (data: any) => {
  try {
    // 处理 template.json 示例格式: {"tid":"...","tname":"...","data":{...}}
    if (data.tid && data.tname && data.data) {
      // 从data对象中提取字段
      const fields: TemplateField[] = []
      for (const [key, value] of Object.entries(data.data)) {
        const field: TemplateField = {
          key,
          label: key.replace(/-/g, ' ').toUpperCase(),
          type: typeof value === 'number' ? 'number' : 'text',
          required: true,
          default_value: String(value),
          order: fields.length
        }
        fields.push(field)
      }
      
      const templateData = {
        tid: data.tid,
        tname: data.tname,
        description: data.description || '通过JSON导入的模板',
        fields
      }
      
      const result = await handleTemplateApiCall(createTemplate(templateData))
      if (result.success) {
        ElMessage.success(result.message || '模板导入成功')
        await fetchTemplates()
      } else {
        ElMessage.error(result.message || '导入失败')
      }
    } else if (data.tid && data.tname && data.fields) {
      // 直接使用完整格式
      const result = await handleTemplateApiCall(createTemplate(data))
      if (result.success) {
        ElMessage.success(result.message || '模板导入成功')
        await fetchTemplates()
      } else {
        ElMessage.error(result.message || '导入失败')
      }
    } else {
      ElMessage.error('JSON格式不正确，请参考示例')
    }
  } catch (error: any) {
    ElMessage.error('处理JSON数据失败: ' + error.message)
  }
}

// 生命周期
onMounted(() => {
  fetchTemplates()
})
</script>

<style lang="scss" scoped>
.template-manage {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  
  .page-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    margin: 0 0 8px;
  }
  
  .page-desc {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
    
    .upload-btn {
      display: inline-block;
    }
  }
}

.template-list {
  .loading-wrap, .empty-wrap {
    padding: 80px 0;
    text-align: center;
  }
  
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 20px;
  }
}

.template-card {
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12) !important;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    
    .title-section {
      display: flex;
      align-items: center;
      gap: 8px;
      
      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }
    
    .actions {
      display: flex;
      gap: 4px;
    }
  }
  
  .card-content {
    .desc {
      font-size: 14px;
      line-height: 1.6;
      margin: 0 0 16px;
      color: var(--el-text-color-primary);
    }
    
    .fields-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    
    .fields-preview {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid var(--el-border-color-lighter);
      border-radius: 6px;
      padding: 12px;
      background: var(--el-fill-color-lighter);
      
      .field-list {
        .field-item {
          padding: 8px 0;
          border-bottom: 1px dashed var(--el-border-color);
          
          &:last-child {
            border-bottom: none;
          }
          
          .field-key {
            font-weight: 600;
            color: var(--el-text-color-primary);
            font-size: 13px;
            margin-bottom: 4px;
          }
          
          .field-details {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
            
            .field-label {
              font-size: 12px;
              color: var(--el-text-color-regular);
            }
            
            .field-type {
              font-size: 11px;
              color: var(--el-color-primary);
              background: var(--el-color-primary-light-9);
              padding: 1px 6px;
              border-radius: 3px;
            }
          }
        }
      }
    }
  }
}

.template-form {
  .fields-section {
    margin-top: 24px;
    
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      h4 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
      }
    }
    
    .fields-empty {
      padding: 40px 0;
      border: 1px dashed var(--el-border-color);
      border-radius: 6px;
    }
    
    .field-items {
      .field-item-draggable {
        margin-bottom: 16px;
        padding: 16px;
        border: 1px solid var(--el-border-color);
        border-radius: 6px;
        background: var(--el-fill-color-lighter);
        
        .field-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px dashed var(--el-border-color);
          
          .field-title {
            display: flex;
            align-items: center;
            gap: 6px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            
            svg {
              color: var(--el-color-primary);
            }
          }
        }
        
        .field-form {
          :deep(.el-form-item) {
            margin-bottom: 16px;
          }
          
          :deep(.el-form-item__label) {
            font-size: 13px;
          }
        }
      }
    }
  }
}

.json-input-section {
  .json-textarea {
    font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
    font-size: 13px;
    
    :deep(textarea) {
      line-height: 1.5;
    }
  }
}
</style>