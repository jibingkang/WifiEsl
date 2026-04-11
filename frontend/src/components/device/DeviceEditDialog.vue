<template>
  <el-dialog
    :model-value="visible"
    title="编辑设备"
    width="560px"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-form v-if="deviceInfo" :model="editForm" label-width="80px" label-position="right">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="MAC地址">
          <code>{{ deviceInfo.mac || '--' }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ deviceInfo.ip || '--' }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">
          <el-input v-model="editForm.name" placeholder="请输入设备名称" size="small" style="width: 100%;" />
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="deviceInfo.is_online ? 'success' : 'danger'" size="small">
            {{ deviceInfo.is_online ? '在线' : '离线' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="电量">{{ deviceInfo.voltage ? formatVoltage(deviceInfo.voltage) : '--' }}</el-descriptions-item>
        <el-descriptions-item label="信号强度">{{ deviceInfo.rssi ? deviceInfo.rssi + 'dBm' : '--' }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ deviceInfo.device_type || '--' }}</el-descriptions-item>
        <el-descriptions-item label="屏幕类型">{{ deviceInfo.screen_type || '--' }}</el-descriptions-item>
        <el-descriptions-item label="软件版本">{{ deviceInfo.sw_version || '--' }}<span :colspan="1"></span></el-descriptions-item>
        <el-descriptions-item label="硬件版本">{{ deviceInfo.hw_version || '--' }}</el-descriptions-item>
      </el-descriptions>
    </el-form>

    <div v-else style="padding: 20px; text-align: center;">
      <p style="color: var(--el-text-color-secondary);">未选择设备</p>
    </div>

    <template #footer v-if="deviceInfo">
      <div class="dialog-footer">
        <span class="save-tip">仅可修改设备名称</span>
        <el-button @click="$emit('update:visible', false)">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useDeviceStore } from '@/stores/device'
import { formatVoltage } from '@/utils/format'
import { deviceApi } from '@/api/device'

const props = defineProps<{
  visible: boolean
  deviceId?: string | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const deviceStore = useDeviceStore()
const saving = ref(false)

const deviceInfo = computed(() => {
  if (props.deviceId) {
    return deviceStore.devices.find(d => d.id === props.deviceId || d.mac === props.deviceId) ?? null
  }
  return null
})

const editForm = ref<{ name: string }>({ name: '' })

watch(() => props.visible, (val) => {
  if (val && deviceInfo.value) {
    editForm.value.name = deviceInfo.value.name ?? ''
  }
}, { immediate: true })

async function handleSave() {
  if (!deviceInfo.value?.id) return

  saving.value = true
  try {
    await deviceApi.updateDevice(deviceInfo.value.id, { name: editForm.value.name })
    // 同步更新 store 中的数据
    const idx = deviceStore.devices.findIndex(d => d.id === deviceInfo.value!.id)
    if (idx !== -1) {
      deviceStore.devices[idx] = { ...deviceStore.devices[idx], name: editForm.value.name }
    }
    ElMessage.success('设备名称已更新')
    emit('saved')
    emit('update:visible', false)
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  .save-tip {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
  }
}
</style>
