<template>
  <el-dialog
    v-model="visible"
    title="WIFI系统配置"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      label-position="right"
      class="wifi-form"
      v-loading="loading"
    >
      <el-form-item label="WIFI用户名" prop="wifi_username">
        <el-input
          v-model="formData.wifi_username"
          placeholder="请输入WIFI系统用户名"
        />
      </el-form-item>
      
      <el-form-item label="WIFI密码" prop="wifi_password">
        <el-input
          v-model="formData.wifi_password"
          type="password"
          placeholder="请输入WIFI系统密码"
          show-password
        />
        <div class="form-tips">留空表示不修改原密码</div>
      </el-form-item>
      
      <el-form-item label="API Key" prop="wifi_apikey">
        <el-input
          v-model="formData.wifi_apikey"
          placeholder="请输入API Key"
        />
      </el-form-item>
      
      <el-form-item label="API地址" prop="wifi_base_url">
        <el-input
          v-model="formData.wifi_base_url"
          placeholder="请输入WIFI系统API地址"
        />
        <div class="form-tips">例如：http://192.168.1.100:4000</div>
      </el-form-item>
      
      <el-form-item label="MQTT Broker地址" prop="wifi_mqtt_broker">
        <el-input
          v-model="formData.wifi_mqtt_broker"
          placeholder="请输入MQTT Broker地址"
        />
        <div class="form-tips">例如：mqtt://192.168.1.100:1883</div>
      </el-form-item>
      
      <el-alert
        v-if="currentWifiConfig"
        title="当前配置信息"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <template #default>
          <div class="config-info">
            <div><strong>WIFI用户名:</strong> {{ currentWifiConfig.wifi_username }}</div>
            <div>
              <strong>API Key:</strong> 
              <span v-if="showRealApikey">{{ currentWifiConfig.wifi_apikey }}</span>
              <span v-else>{{ currentWifiConfig.wifi_apikey_display || '未设置' }}</span>
              <el-button 
                v-if="currentWifiConfig.wifi_apikey"
                type="text" 
                size="small" 
                @click="showRealApikey = !showRealApikey"
                style="margin-left: 8px;"
              >
                {{ showRealApikey ? '隐藏' : '查看' }}
              </el-button>
            </div>
            <div><strong>API地址:</strong> {{ currentWifiConfig.wifi_base_url }}</div>
            <div v-if="currentWifiConfig.wifi_mqtt_broker">
              <strong>MQTT Broker:</strong> {{ currentWifiConfig.wifi_mqtt_broker }}
            </div>
            <div v-if="currentWifiConfig.wifi_password">
              <strong>WIFI密码:</strong> 
              <span v-if="showRealPassword">{{ currentWifiConfig.wifi_password }}</span>
              <span v-else>●●●●●●●●</span>
              <el-button 
                v-if="currentWifiConfig.wifi_password"
                type="text" 
                size="small" 
                @click="showRealPassword = !showRealPassword"
                style="margin-left: 8px;"
              >
                {{ showRealPassword ? '隐藏' : '查看' }}
              </el-button>
            </div>
          </div>
        </template>
      </el-alert>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          保存配置
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import type { WifiConfig } from '@/types/user'

const props = defineProps<{
  modelValue: boolean
  userId: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const currentWifiConfig = ref<WifiConfig | null>(null)
const showRealApikey = ref(false)
const showRealPassword = ref(false)

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 表单数据
const formData = ref({
  wifi_username: '',
  wifi_password: '',
  wifi_apikey: '',
  wifi_base_url: '',
  wifi_mqtt_broker: '',
})

// 表单验证规则
const formRules: FormRules = {
  wifi_username: [
    { required: true, message: '请输入WIFI用户名', trigger: 'blur' },
  ],
  wifi_base_url: [
    { required: true, message: '请输入API地址', trigger: 'blur' },
    {
      pattern: /^https?:\/\/.+$/,
      message: '请输入有效的URL地址（以http://或https://开头）',
      trigger: 'blur',
    },
  ],
  wifi_apikey: [
    { required: true, message: '请输入API Key', trigger: 'blur' },
  ],
  wifi_mqtt_broker: [
    {
      pattern: /^(mqtt:\/\/|tcp:\/\/|ws:\/\/|wss:\/\/).+$/,
      message: '请输入有效的MQTT地址（以mqtt://, tcp://, ws://或wss://开头）',
      trigger: 'blur',
    },
  ],
}

// 重置表单
const resetForm = () => {
  formData.value = {
    wifi_username: '',
    wifi_password: '',
    wifi_apikey: '',
    wifi_base_url: '',
    wifi_mqtt_broker: '',
  }
}

// 加载WIFI配置
const loadWifiConfig = async (userId: number) => {
  try {
    loading.value = true
    const config = await userStore.fetchUserWifiConfig(userId)
    currentWifiConfig.value = config
    
    // 填充表单（不填充密码）
    formData.value = {
      wifi_username: config.wifi_username || '',
      wifi_password: '',
      wifi_apikey: config.wifi_apikey || '',
      wifi_base_url: config.wifi_base_url || '',
      wifi_mqtt_broker: config.wifi_mqtt_broker || '',
    }
  } catch (error) {
    console.error('加载WIFI配置失败:', error)
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 监听userId变化，加载WIFI配置
watch(() => props.userId, async (userId) => {
  if (userId) {
    await loadWifiConfig(userId)
  } else {
    resetForm()
    currentWifiConfig.value = null
  }
}, { immediate: true })

// 对话框打开时重置表单验证和显示状态
watch(visible, (value) => {
  if (value) {
    nextTick(() => {
      formRef.value?.clearValidate()
    })
  } else {
    // 关闭对话框时重置查看状态
    showRealApikey.value = false
    showRealPassword.value = false
  }
})

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value || !props.userId) return
  
  try {
    // 验证表单
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    // 准备提交数据，过滤空密码
    const submitData: any = {
      wifi_username: formData.value.wifi_username,
      wifi_apikey: formData.value.wifi_apikey,
      wifi_base_url: formData.value.wifi_base_url,
      wifi_mqtt_broker: formData.value.wifi_mqtt_broker,
    }
    
    // 只有在密码不为空时才更新密码
    if (formData.value.wifi_password.trim()) {
      submitData.wifi_password = formData.value.wifi_password
    }
    
    // 调用API更新配置
    await userStore.updateUserWifiConfig(props.userId, submitData)
    
    ElMessage.success('WIFI配置更新成功')
    
    // 触发成功事件
    emit('success')
    visible.value = false
    
    // 重新加载配置
    await loadWifiConfig(props.userId)
    
  } catch (error) {
    console.error('更新WIFI配置失败:', error)
    ElMessage.error('更新配置失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.wifi-form {
  .form-tips {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
    line-height: 1.4;
  }
  
  .config-info {
    font-size: 14px;
    line-height: 1.6;
    
    div {
      margin-bottom: 4px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    strong {
      display: inline-block;
      width: 100px;
      color: #606266;
    }
  }
  
  .el-form-item {
    margin-bottom: 20px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>