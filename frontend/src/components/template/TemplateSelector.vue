<template>
  <div class="template-selector">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
      <el-skeleton :rows="3" animated style="margin-top: 16px;" />
    </div>

    <!-- 模板网格 -->
    <div v-else-if="templates.length > 0" class="template-grid-container">
      <div class="selector-header">
        <h3>选择模板</h3>
        <p class="header-tip">请选择一个模板，点击卡片选择，然后点击确认按钮继续</p>
      </div>
      
      <TransitionGroup name="grid" tag="div" class="template-grid">
        <div
          v-for="tpl in templates"
          :key="tpl.tid"
          class="template-card"
          :class="{ selected: selectedId === tpl.tid }"
          @click="handleSelectTemplate(tpl)"
        >
          <div class="card-header">
            <el-icon :size="28" class="card-icon"><Document /></el-icon>
            <span class="badge" v-if="selectedId === tpl.tid">
              <el-icon><Select /></el-icon> 已选择
            </span>
          </div>
          <h3 class="card-title">{{ tpl.tname }}</h3>
          <p class="card-desc">{{ tpl.description }}</p>
          <div class="card-fields">
            <el-tag
              v-for="field in (tpl.fields || []).slice(0, 4)"
              :key="field.key"
              size="small"
              effect="plain"
            >{{ field.label }}</el-tag>
            <el-tag v-if="(tpl.fields || []).length > 4" size="small" type="info" effect="plain">
              +{{ (tpl.fields || []).length - 4 }}
            </el-tag>
          </div>
        </div>
      </TransitionGroup>

      <!-- 操作按钮 -->
      <div class="selector-footer">
        <el-button 
          type="primary" 
          size="large" 
          :disabled="!selectedTemplate"
          @click="handleConfirm"
          class="confirm-btn"
        >
          <el-icon><Check /></el-icon> 确认选择并继续
        </el-button>
        <el-button 
          v-if="selectedTemplate"
          type="info" 
          size="large" 
          plain
          @click="handleCancelSelection"
        >
          取消选择
        </el-button>
      </div>
    </div>

    <div v-else class="empty-state">
      <el-empty description="暂无可用模板">
        <el-button type="primary" @click="$router.push('/template/manage')">
          前往创建模板
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Document, Select, Check } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import type { TemplateInfo } from '@/types'

const router = useRouter()

const selectedTemplate = ref<TemplateInfo | null>(null)

defineProps<{
  templates: TemplateInfo[]
  loading: boolean
  selectedId?: string | null
}>()

const emit = defineEmits<{
  select: [template: TemplateInfo]
  confirm: [template: TemplateInfo]
  cancel: []
}>()

function handleSelectTemplate(tpl: TemplateInfo) {
  selectedTemplate.value = tpl
  emit('select', tpl)
}

function handleConfirm() {
  if (selectedTemplate.value) {
    emit('confirm', selectedTemplate.value)
  }
}

function handleCancelSelection() {
  selectedTemplate.value = null
  emit('cancel')
}
</script>

<style lang="scss" scoped>
.template-selector { padding: 8px; }

.loading-state { max-width: 560px; margin: 0 auto; }

.selector-header {
  margin-bottom: 24px;
  
  h3 {
    font-size: 18px;
    font-weight: 700;
    color: var(--el-text-color-primary);
    margin: 0 0 6px;
  }
  
  .header-tip {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.template-grid-container {
  max-width: 900px;
  margin: 0 auto;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.template-card {
  position: relative;
  padding: 22px;
  border-radius: 16px;
  background: var(--el-bg-color);
  border: 2px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.25s ease;

  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(99,102,241,0.08);
    border-color: rgba(99,102,241,0.25);
  }

  &.selected {
    border-color: #6366f1;
    background: linear-gradient(135deg, rgba(99,102,241,0.04), rgba(139,92,246,0.06));
    box-shadow: 0 4px 20px rgba(99,102,241,0.12);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;

  .card-icon {
    color: #6366f1;
    opacity: 0.7;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 11px;
    color: #6366f1;
    font-weight: 600;
    background: rgba(99,102,241,0.1);
    padding: 3px 10px;
    border-radius: 20px;
  }
}

.card-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 6px;
}
.card-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin: 0 0 14px;
  line-height: 1.5;
}

.card-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.selector-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);
  margin-top: 24px;
  
  .confirm-btn {
    min-width: 200px;
  }
}

.empty-state {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.grid-enter-active,
.grid-leave-active { transition: all 0.35s ease; }
.grid-enter-from { opacity: 0; transform: scale(0.9); }
.grid-leave-to { opacity: 0; transform: scale(0.95); }
</style>
