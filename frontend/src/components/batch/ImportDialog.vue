<template>
  <el-dialog
    :model-value="visible"
    title="导入数据"
    width="520px"
    append-to-body
    @update:model-value="(val) => $emit('update:visible', val)"
  >
    <div class="import-body">
      <!-- 上传区域 -->
      <el-upload
        ref="uploadRef"
        drag
        accept=".csv,.xlsx,.xls,.json"
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        :on-remove="() => { file.value = null }"
        class="upload-area"
      >
        <div class="upload-icon"><el-icon :size="40"><UploadFilled /></el-icon></div>
        <p class="upload-text">拖拽文件到此处，或 <em>点击上传</em></p>
        <p class="upload-tip">支持 CSV / Excel (.xlsx/.xls) / JSON 格式</p>
      </el-upload>

      <!-- 预览 -->
      <div v-if="previewData.length > 0" class="preview-section">
        <h4>预览（前5条）</h4>
        <el-table :data="previewData.slice(0, 5)" size="small" max-height="200" border>
          <el-table-column
            v-for="(key, i) in previewColumns"
            :key="i"
            :prop="key"
            :label="key"
            show-overflow-tooltip
          />
        </el-table>
        <p class="preview-count">共 {{ previewData.length }} 条数据</p>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :disabled="!file || previewData.length === 0" :loading="importing" @click="handleImport">
        确认导入
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  'update:visible': [value: boolean]
  imported: [count: number]
}>()

const file = ref<File | null>(null)
const importing = ref(false)
const previewData = ref<any[]>([])
const previewColumns = ref<string[]>([])

// 获取文件格式
function getFileFormat(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  if (ext === 'csv') return 'csv'
  if (ext === 'xlsx' || ext === 'xls') return 'excel'
  if (ext === 'json') return 'json'
  return 'unknown'
}

function handleFileChange(uploadFile: any) {
  file.value = uploadFile.raw

  // 简单读取CSV预览（实际项目应使用xlsx/papaparse等库）
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const text = e.target?.result as string
      if (text.startsWith('[') || text.startsWith('{')) {
        // JSON
        const json = JSON.parse(text)
        const arr = Array.isArray(json) ? json : [json]
        previewData.value = arr
        previewColumns.value = Object.keys(arr[0] || {})
      } else {
        // CSV (简单处理)
        const lines = text.split('\n').filter(l => l.trim())
        if (lines.length >= 2) {
          previewColumns.value = lines[0].split(',').map(s => s.trim().replace(/"/g, ''))
          for (let i = 1; i < Math.min(lines.length, 51); i++) {
            const vals = lines[i].split(',').map(s => s.trim().replace(/"/g, ''))
            const obj: any = {}
            previewColumns.value.forEach((k, j) => obj[k] = vals[j])
            previewData.value.push(obj)
          }
        }
      }
    } catch (err) {
      ElMessage.error('文件解析失败，请检查格式')
      previewData.value = []
    }
  }
  reader.readAsText(file.value as File)
}

async function handleImport() {
  importing.value = true
  try {
    // 调用后端导入API
    const formData = new FormData()
    formData.append('file', file.value!.raw!)
    formData.append('format', getFileFormat(file.value!.name))
    
    // 这里应该调用实际的导入API
    // const response = await importBatchData(formData)
    
    // 模拟API调用
    await new Promise(r => setTimeout(r, 800))
    emit('imported', previewData.value.length)
    emit('update:visible', false)
  } finally {
    importing.value = false
  }
}
</script>

<style lang="scss" scoped>
.import-body { padding: 8px 0; }

.upload-area {
  :deep(.el-upload) {
    width: 100%;
    .el-upload-dragger {
      width: 100%;
      height: auto;
      padding: 32px 20px;
      border-radius: 14px;
      transition: all 0.25s;
      &:hover { border-color: #6366f1; }
    }
  }
}

.upload-icon { color: #c0c4cc; margin-bottom: 12px; }
.upload-text { color: var(--el-text-color-regular); margin: 0 0 6px; em { color: #6366f1; font-style: normal; } }
.upload-tip { font-size: 12px; color: var(--el-text-color-placeholder); margin: 0; }

.preview-section {
  margin-top: 18px;
  h4 { font-size: 14px; font-weight: 600; margin: 0 0 10px; }
}
.preview-count { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 8px; text-align: right; }
</style>
