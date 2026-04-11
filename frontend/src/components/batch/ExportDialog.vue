<template>
  <el-dialog
    :model-value="visible"
    title="导出数据"
    width="420px"
    append-to-body
    @update:model-value="(val) => $emit('update:visible', val)"
  >
    <div class="export-body">
      <el-form label-position="top" size="large">
        <el-form-item label="导出格式">
          <el-radio-group v-model="format" class="format-options">
            <el-radio value="excel">
              <div class="fmt-item">
                <el-icon :size="22"><Document /></el-icon>
                <div>
                  <strong>Excel</strong>
                  <span>.xlsx 文件</span>
                </div>
              </div>
            </el-radio>
            <el-radio value="csv">
              <div class="fmt-item">
                <el-icon :size="22"><Tickets /></el-icon>
                <div>
                  <strong>CSV</strong>
                  <span>逗号分隔文件</span>
                </div>
              </div>
            </el-radio>
            <el-radio value="json">
              <div class="fmt-item">
                <el-icon :size="22"><Coin /></el-icon>
                <div>
                  <strong>JSON</strong>
                  <span>结构化数据</span>
                </div>
              </div>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="导出范围">
          <el-select v-model="range" style="width: 100%;">
            <el-option label="全部数据" value="all" />
            <el-option label="仅已修改的数据" value="changed" />
            <el-option label="仅选中的行" value="selected" />
          </el-select>
        </el-form-item>

        <el-form-item label="文件名">
          <el-input v-model="fileName" placeholder="wifi_devices_export" prefix-icon="Folder" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleConfirm">开始下载</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Document, Tickets, Coin } from '@element-plus/icons-vue'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  'update:visible': [value: bool]
  confirm: [format: string]
}>()

const format = ref('excel')
const range = ref('all')
const fileName = ref('wifi_devices_export')

function handleConfirm() {
  emit('confirm', format.value)
}
</script>

<style lang="scss" scoped>
.export-body { padding: 8px 0; }

.format-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;

  :deep(.el-radio__input) { display: none; }
  :deep(.el-radio.is-bordered) {
    border-radius: 11px;
    border: 1px solid var(--el-border-color);
    padding: 12px 16px;
    transition: all 0.2s;
    &.is-checked { border-color: #6366f1; background: rgba(99,102,241,0.04); }
    &:hover:not(.is-checked) { border-color: rgba(99,102,241,0.3); }
  }
}

.fmt-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--el-text-color-regular);

  div { display: flex; flex-direction: column; line-height: 1.3; }
  strong { font-size: 14px; font-weight: 600; }
  span { font-size: 12px; color: var(--el-text-color-secondary); }
}
</style>
