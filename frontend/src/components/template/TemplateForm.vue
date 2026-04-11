<template>
  <div v-if="templateInfo" class="template-form">
    <div class="form-header">
      <div class="header-info">
        <el-icon :size="22" style="color:#6366f1;"><Document /></el-icon>
        <div>
          <h3>{{ templateInfo.tname }}</h3>
          <p class="desc">{{ templateInfo.description }}</p>
        </div>
      </div>
      <el-tag type="success" size="large">共 {{ deviceCount }} 台设备</el-tag>
    </div>

    <el-divider />

    <!-- 操作工具栏 -->
    <div class="action-toolbar" v-if="editMode === 'default'">
      <el-button-group>
        <el-button 
          type="primary" 
          size="default" 
          @click="saveCurrentEdit"
          :disabled="!templateInfo"
        >
          <el-icon><Check /></el-icon> 保存当前数据
        </el-button>
        <el-button 
          type="info" 
          size="default" 
          @click="resetAllData"
          :disabled="!templateInfo"
        >
          <el-icon><Refresh /></el-icon> 重置所有数据
        </el-button>
      </el-button-group>
      
      <div class="edit-mode-info" v-if="editMode === 'single'">
        <el-tag type="warning">
          <el-icon><Edit /></el-icon> 单设备编辑模式: {{ getDeviceName(currentEditingDevice) }}
        </el-tag>
        <el-button 
          size="small" 
          @click="exitSingleEditMode"
          style="margin-left: 8px;"
        >
          返回默认编辑
        </el-button>
      </div>
    </div>

    <!-- 默认值表单 -->
    <div class="section" :class="{ 'single-edit-mode': editMode === 'single' }">
      <h4 class="section-title">
        <el-icon><EditPen /></el-icon>
        {{ editMode === 'single' ? `单设备编辑: ${getDeviceName(currentEditingDevice)}` : '默认内容（所有设备共用）' }}
      </h4>
      <p class="section-tip">
        {{ editMode === 'single' 
          ? '以下内容仅应用于当前设备，其他设备使用默认值' 
          : '填写以下内容将应用到所有已选设备，可在下方为单台设备单独修改' }}
      </p>

      <el-form 
        :model="currentFormData" 
        label-position="top" 
        size="large" 
        class="dynamic-form"
      >
        <el-row :gutter="20">
          <el-col
            v-for="field in templateInfo.fields"
            :key="field.key"
            :xs="24" :sm="isWideField(field) ? 24 : 12"
          >
            <el-form-item :label="field.label + (field.required ? ' *' : '')" :required="field.required">
              <!-- 文本 -->
              <el-input
                v-if="field.type === 'text'"
                v-model="currentFormData[field.key]"
                :placeholder="getFieldPlaceholder(field)"
                clearable
              />

              <!-- 多行文本 -->
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="currentFormData[field.key]"
                type="textarea"
                :rows="3"
                :placeholder="getFieldPlaceholder(field)"
              />

              <!-- 数字 -->
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="currentFormData[field.key]"
                controls-position="right"
                :placeholder="getFieldPlaceholder(field)"
                style="width: 100%;"
              />

              <!-- 下拉选择 -->
              <el-select
                v-else-if="field.type === 'select'"
                v-model="currentFormData[field.key]"
                :placeholder="getFieldPlaceholder(field)"
                style="width: 100%;"
              >
                <el-option
                  v-for="opt in (field.options ?? [])"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>

              <!-- 颜色选择 -->
              <el-color-picker
                v-else-if="field.type === 'color'"
                v-model="currentFormData[field.key]"
                show-alpha
              />

              <!-- 二维码/图片占位 -->
              <div v-else class="special-field">
                <el-input
                  v-model="currentFormData[field.key]"
                  :placeholder="getFieldPlaceholder(field)"
                  clearable
                >
                  <template #prefix><el-icon><Picture /></el-icon></template>
                </el-input>
              </div>
              
              <div v-if="editMode === 'single'" class="field-hint">
                默认值: {{ localDefaultData[field.key] ?? '(空)' }}
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <el-divider />

    <!-- 设备列表 + 自定义覆盖 -->
    <div v-if="deviceCount > 0" class="section custom-section">
      <h4 class="section-title">
        <el-icon><UserFilled /></el-icon>
        单设备数据编辑
      </h4>
      <p class="section-tip">点击编辑按钮可为单台设备设置不同的数据</p>

      <el-table :data="deviceList" stripe max-height="300" size="default">
        <el-table-column prop="mac" label="设备MAC" width="180">
          <template #default="{ row }">
            <code>{{ row.mac }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" width="140">
          <template #default="{ row }">{{ row.name || '--' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'info'" size="small">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="自定义内容" width="120" align="center">
          <template #default="{ row }">
            <el-tag 
              v-if="row.hasCustom"
              type="warning" 
              size="small"
              effect="plain"
            >
              已设置
            </el-tag>
            <span v-else style="color: var(--el-text-color-placeholder);">--</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              plain
              @click="enterSingleEditMode(row.mac)"
              :disabled="editMode === 'single'"
            >
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 自定义表单展开区域 -->
      <el-collapse v-model="activeCustomMacs">
        <el-collapse-item
          v-for="mac in Object.keys(customOverrides)"
          :key="mac"
          :name="mac"
        >
          <template #title>
            <code style="font-size:12px;">{{ mac }}</code>
          </template>
          <div class="custom-form-inner">
            <el-form :model="customOverrides[mac]" label-position="top" size="default">
              <el-row :gutter="16">
                <el-col v-for="field in templateInfo.fields" :key="field.key" :xs="24" :sm="12">
                  <el-form-item :label="field.label">
                    <el-input
                      v-model="customOverrides[mac][field.key]"
                      :placeholder="'默认: ' + (localDefaultData[field.key] ?? '(空)')"
                      size="default"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Document, EditPen, UserFilled, Picture, Check, Edit, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { TemplateInfo } from '@/types'
import { useDeviceStore } from '@/stores/device'

const props = withDefaults(defineProps<{
  templateInfo?: TemplateInfo | null
  deviceCount: number
  defaultData: Record<string, any>
  customOverrides: Record<string, Record<string, any>>
  selectedMacs?: string[]
}>(), {
  templateInfo: () => ({ tid: '', tname: '', description: '', fields: [] }),
  selectedMacs: () => [],
})

const emit = defineEmits<{
  'update:defaultData': [val: Record<string, any>]
  'update:customOverrides': [val: Record<string, Record<string, any>>]
  save: [data: { defaultData: Record<string, any>; customOverrides: Record<string, Record<string, any>> }]
  reset: []
}>()

const deviceStore = useDeviceStore()
const localDefaultData = ref<Record<string, any>>({ ...props.defaultData })
const activeCustomMacs = ref<string[]>([])
const editMode = ref<'default' | 'single'>('default')
const currentEditingDevice = ref<string>('')

/** 当前表单绑定的数据对象（根据编辑模式动态切换） */
const currentFormData = computed(() => {
  if (editMode.value === 'single' && currentEditingDevice.value) {
    // 确保自定义覆盖对象存在
    if (!props.customOverrides[currentEditingDevice.value]) {
      const overrides = { ...props.customOverrides }
      overrides[currentEditingDevice.value] = {}
      emit('update:customOverrides', overrides)
    }
    return props.customOverrides[currentEditingDevice.value] ?? {}
  }
  return localDefaultData.value
})

watch(localDefaultData, (v) => emit('update:defaultData', v), { deep: true })

/** 判断是否是宽字段 */
function isWideField(f: TemplateInfo['fields'][number]): boolean {
  return ['textarea', 'qrcode', 'image'].includes(f.type)
}

/** 切换自定义覆盖 */
function toggleCustom(mac: string, enabled: boolean) {
  const overrides = { ...props.customOverrides }
  if (enabled) {
    overrides[mac] = {}
    activeCustomMacs.value.push(mac)
  } else {
    delete overrides[mac]
    activeCustomMacs.value = activeCustomMacs.value.filter(m => m !== mac)
  }
  emit('update:customOverrides', overrides)
}

// 真实设备列表
const deviceList = computed(() => {
  if (props.selectedMacs.length > 0) {
    return props.selectedMacs.map(mac => {
      const device = deviceStore.devices.find((d: any) => d.mac === mac)
      return {
        mac,
        name: device?.name || mac,
        status: device?.status || 'offline',
        hasCustom: !!props.customOverrides[mac]
      }
    })
  }
  // 如果没有选择设备，显示模拟数据
  return Array.from({ length: Math.min(props.deviceCount, 50) }, (_, i) => ({
    mac: `A4:CE:CC:XX:XX:${String(i).padStart(2, '0')}`,
    name: `设备-${i + 1}`,
    status: 'online',
    hasCustom: false
  }))
})

/** 获取设备名称 */
function getDeviceName(mac: string): string {
  const device = deviceStore.devices.find((d: any) => d.mac === mac)
  return device?.name || mac
}

/** 进入单设备编辑模式 */
function enterSingleEditMode(mac: string) {
  editMode.value = 'single'
  currentEditingDevice.value = mac
  activeCustomMacs.value = [mac]
  
  // 确保该设备有自定义覆盖
  if (!props.customOverrides[mac]) {
    const overrides = { ...props.customOverrides }
    overrides[mac] = {}
    emit('update:customOverrides', overrides)
  }
  
  ElMessage.info(`正在编辑设备: ${getDeviceName(mac)}`)
}

/** 退出单设备编辑模式 */
function exitSingleEditMode() {
  editMode.value = 'default'
  currentEditingDevice.value = ''
}

/** 保存当前编辑 */
function saveCurrentEdit() {
  emit('save', {
    defaultData: localDefaultData.value,
    customOverrides: props.customOverrides
  })
  ElMessage.success('数据已保存')
}

/** 重置所有数据 */
function resetAllData() {
  localDefaultData.value = {}
  const overrides = { ...props.customOverrides }
  for (const mac in overrides) {
    overrides[mac] = {}
  }
  emit('update:customOverrides', overrides)
  activeCustomMacs.value = []
  editMode.value = 'default'
  currentEditingDevice.value = ''
  
  // 重新设置默认值
  if (props.templateInfo?.fields) {
    for (const f of props.templateInfo.fields) {
      if (f.default_value != null) localDefaultData.value[f.key] = f.default_value
    }
  }
  
  ElMessage.info('已重置所有数据')
}

/** 获取字段占位符 */
function getFieldPlaceholder(field: TemplateInfo['fields'][number]): string {
  if (editMode.value === 'single') {
    return `自定义值 (默认: ${localDefaultData.value[field.key] ?? '空'})`
  }
  return field.placeholder ?? `请输入${field.label}`
}

onMounted(() => {
  // 初始化默认值
  if (props.templateInfo?.fields) {
    for (const f of props.templateInfo.fields) {
      if (f.default_value != null && !localDefaultData.value[f.key]) {
        localDefaultData.value[f.key] = f.default_value
      }
    }
  }
})
</script>

<style lang="scss" scoped>
.template-form { padding: 4px; }

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .header-info { display: flex; gap: 12px; align-items: center; }
  h3 { font-size: 17px; font-weight: 600; margin: 0; }
  .desc { font-size: 13px; color: var(--el-text-color-secondary); margin: 4px 0 0; }
}

.action-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-radius: 10px;
  
  .edit-mode-info {
    display: flex;
    align-items: center;
  }
}

.section { padding: 4px 0; }

.single-edit-mode {
  background: rgba(255, 243, 222, 0.3);
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid #f59e0b;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 6px;
}
.section-tip { font-size: 13px; color: var(--el-text-color-placeholder); margin: 0 0 16px; }

.dynamic-form { max-width: 720px; }

.special-field {
  :deep(.el-input__inner) { font-family: monospace; }
}

.field-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
}

.custom-section {
  background: var(--el-fill-color-extra-light);
  border-radius: 12px;
  padding: 18px;
}

.custom-form-inner {
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-radius: 10px;
}

code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  background: var(--el-fill-color-light);
  padding: 2px 8px;
  border-radius: 5px;
}
</style>
