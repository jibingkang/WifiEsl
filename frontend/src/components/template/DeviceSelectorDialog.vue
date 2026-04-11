<template>
  <DeviceSelector
    :selected-macs="internalMacs"
    :pre-selected="[...preSelected]"
    @update:selected-macs="internalMacs = $event"
    @confirm="handleConfirm"
    @push-device="handlePushDevice"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DeviceSelector from './DeviceSelector.vue'
import { ElMessage } from 'element-plus'

const props = withDefaults(defineProps<{
  preSelected?: string[]
}>(), {
  preSelected: () => [],
})

const emit = defineEmits<{
  confirm: [macs: string[]]
  'push-device': [device: any]
}>()

const internalMacs = ref<string[]>([...props.preSelected])

function handleConfirm(macs: string[]) {
  emit('confirm', macs)
  ElMessage.success(`已确认选择 ${macs.length} 台设备`)
}

function handlePushDevice(device: any) {
  emit('push-device', device)
}
</script>
