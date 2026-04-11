<template>
  <div class="workspace-form">
    <!-- 表单头部 -->
    <div class="form-header">
      <h3 class="form-title">
        <Pencil /> {{ templateInfo.tname }} — 数据填写
      </h3>
      <p class="form-tip">以下数据为所有设备的默认值，可在下方"设备自定义数据"中为单台设备单独覆盖</p>
    </div>

    <el-form :model="localData" label-position="top" size="default">
      <el-row :gutter="16">
        <el-col
          v-for="field in templateInfo.fields"
          :key="field.key"
          :xs="24" :sm="isWideField(field) ? 24 : 12"
        >
          <el-form-item :label="field.label + (field.required ? ' *' : '')" :required="field.required">
            <!-- 文本 -->
            <input
              v-if="field.type === 'text'"
              type="text"
              v-model="localData[field.key]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              class="form-input"
            />

            <!-- 多行文本 -->
            <textarea
              v-else-if="field.type === 'textarea'"
              v-model="localData[field.key]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              rows="3"
              class="form-input form-textarea"
            ></textarea>

            <!-- 数字 -->
            <input
              v-else-if="field.type === 'number'"
              type="number"
              v-model.number="localData[field.key]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              class="form-input"
            />

            <!-- 下拉选择 -->
            <select
              v-else-if="field.type === 'select'"
              v-model="localData[field.key]"
              class="form-select"
            >
              <option value="" disabled>{{ field.placeholder || `请选择${field.label}` }}</option>
              <option v-for="opt in (field.options ?? [])" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>

            <!-- 颜色 -->
            <input
              v-else-if="field.type === 'color'"
              type="color"
              v-model="localData[field.key]"
              class="form-color"
            />

            <!-- 日期 -->
            <input
              v-else-if="field.type === 'date'"
              type="date"
              v-model="localData[field.key]"
              class="form-input"
            />

            <!-- 其他（二维码/图片） -->
            <input
              v-else
              type="text"
              v-model="localData[field.key]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              class="form-input"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- 快速填充提示 -->
    <div class="form-footer-hint">
      <Info size="14" />
      <span>填写完默认值后，下方表格可为每台设备单独设置不同数据</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { Pencil, Info } from 'lucide-vue-next'
import type { TemplateInfo } from '@/types'

const props = defineProps<{
  templateInfo: TemplateInfo
  defaultData: Record<string, any>
}>()

const emit = defineEmits<{
  'update:defaultData': [val: Record<string, any>]
}>()

var _updatingFromProp = false

// 本地数据初始化为 props 的快照
var localData = ref<Record<string, any>>({})

// 从 prop 同步到本地（仅当 prop 引用变化时，避免回写死循环）
watch(() => props.defaultData, (v) => {
  _updatingFromProp = true
  var copy: Record<string, any> = {}
  if (v) {
    var keys = Object.keys(v)
    for (var i = 0; i < keys.length; i++) { copy[keys[i]] = v[keys[i]] }
  }
  localData.value = copy
  // 延迟重置标志，确保当前 tick 内不再响应 localData 的变化
  nextTick(function() { _updatingFromProp = false })
}, { immediate: true })

// 本地变化向上通知父组件（仅当非从 prop 同步时）
watch(localData, function(v) {
  if (_updatingFromProp) return
  emit('update:defaultData', v)
}, { deep: true })

function isWideField(f: TemplateInfo['fields'][number]): boolean {
  return ['textarea', 'qrcode', 'image'].includes(f.type)
}
</script>

<style scoped>
.workspace-form {
  background: white;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}

.form-header {
  margin-bottom: 18px;
}
.form-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 4px;
}
.form-tip {
  font-size: 12.5px;
  color: #64748b;
  margin: 0;
}

/* 原生输入控件统一样式 */
.form-input,
.form-select,
.form-textarea,
.form-color {
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  font-size: 13.5px;
  color: #1e293b;
  transition: all 0.2s ease;
  outline: none;
  box-sizing: border-box;

  &:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
    background: white;
  }

  &::placeholder { color: #94a3b8; }
}

.form-textarea {
  resize: vertical;
  min-height: 72px;
}

.form-color {
  height: 38px;
  cursor: pointer;
  padding: 4px 8px;
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2394a3b8'%3E%3Cpath d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.form-footer-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 10px 14px;
  background: rgba(99,102,241,0.05);
  border-radius: 8px;
  color: #6366f1;
  font-size: 12.5px;
}
</style>
