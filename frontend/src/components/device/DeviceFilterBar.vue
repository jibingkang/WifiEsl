<template>
  <div class="filter-bar">
    <el-form :model="localFilters" inline class="filter-form">
      <!-- 关键词搜索 -->
      <el-form-item>
        <el-input
          v-model="localFilters.keyword"
          placeholder="搜索MAC地址 / 名称..."
          clearable
          :prefix-icon="Search"
          style="width: 220px;"
          @keyup.enter="$emit('search')"
          @clear="$emit('search')"
        />
      </el-form-item>

      <!-- 状态筛选 -->
      <el-form-item>
        <el-select v-model="localFilters.status" placeholder="在线状态" clearable style="width: 130px;">
          <el-option label="全部状态" value="" />
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
        </el-select>
      </el-form-item>

      <!-- 设备类型 -->
      <el-form-item>
        <el-select v-model="localFilters.deviceType" placeholder="设备类型" clearable style="width: 140px;">
          <el-option label="全部类型" value="" />
          <el-option v-for="(label, key) in DEVICE_TYPES" :key="key" :label="label" :value="key" />
        </el-select>
      </el-form-item>

      <!-- 屏幕类型 -->
      <el-form-item>
        <el-select v-model="localFilters.screenType" placeholder="屏幕类型" clearable style="width: 130px;">
          <el-option label="全部屏幕" value="" />
          <el-option v-for="(label, key) in SCREEN_TYPES" :key="key" :label="label" :value="key" />
        </el-select>
      </el-form-item>

      <!-- 按钮 -->
      <el-form-item>
        <el-button type="primary" :icon="Search" @click="$emit('search')">搜索</el-button>
        <el-button :icon="RefreshRight" @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Search, RefreshRight } from '@element-plus/icons-vue'
import { DEVICE_TYPES, SCREEN_TYPES } from '@/utils/constants'

const props = withDefaults(defineProps<{
  filters?: Record<string, string>
  // Selector mode (used in template wizard)
  selectedMacs?: string[]
  preSelected?: string[]
}>(), {
  filters: () => ({ keyword: '', status: '', deviceType: '', screenType: '' }),
  selectedMacs: () => [],
  preSelected: () => [],
})

// Filter bar mode
const emit = defineEmits<{
  'update:filters': [value: Record<string, string>]
  'update:selectedMacs': [value: string[]]
  search: []
  reset: []
}>()

const localFilters = reactive({ ...props.filters })

watch(() => props.filters, () => Object.assign(localFilters, props.filters), { deep: true })

function handleReset() {
  Object.assign(localFilters, { keyword: '', status: '', deviceType: '', screenType: '' })
  emit('update:filters', localFilters)
  emit('reset')
}
</script>

<style lang="scss" scoped>
.filter-bar {
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 14px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

:deep(.el-form-item) { margin-bottom: 0 !important; margin-right: 0; }

@media (max-width: 768px) {
  .filter-form { flex-direction: column; }
  :deep(.el-input),
  :deep(.el-select) { width: 100% !important; }
}
</style>
