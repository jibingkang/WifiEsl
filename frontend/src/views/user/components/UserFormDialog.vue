<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @closed="handleClosed"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      label-position="right"
      class="user-form"
    >
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="formData.username"
          placeholder="请输入用户名"
          :disabled="dialogType === 'edit'"
        />
      </el-form-item>
      
      <el-form-item label="密码" prop="password" v-if="dialogType === 'create'">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="请输入密码"
          show-password
        />
      </el-form-item>
      
      <el-form-item label="确认密码" prop="confirmPassword" v-if="dialogType === 'create'">
        <el-input
          v-model="formData.confirmPassword"
          type="password"
          placeholder="请再次输入密码"
          show-password
        />
      </el-form-item>
      
      <el-form-item label="用户角色" prop="role">
        <el-select v-model="formData.role" placeholder="请选择用户角色">
          <el-option label="管理员" value="admin" />
          <el-option label="操作员" value="operator" />
          <el-option label="普通用户" value="user" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="用户状态" prop="status">
        <el-radio-group v-model="formData.status">
          <el-radio value="active">活跃</el-radio>
          <el-radio value="disabled">禁用</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="头像URL">
        <el-input
          v-model="formData.avatar"
          placeholder="请输入头像URL（可选）"
        />
      </el-form-item>
      
      <el-divider content-position="left">WIFI系统配置</el-divider>
      
      <el-form-item label="WIFI用户名">
        <el-input
          v-model="formData.wifi_username"
          placeholder="请输入WIFI系统用户名"
        />
      </el-form-item>
      
      <el-form-item label="WIFI密码">
        <el-input
          v-model="formData.wifi_password"
          :type="showWifiPassword ? 'text' : 'password'"
          :placeholder="dialogType === 'edit' ? '留空表示不修改原密码' : '请输入WIFI系统密码'"
          :show-password="!showWifiPassword"
        >
          <template v-if="dialogType === 'edit' && props.userData?.wifi_password" #append>
            <el-button 
              type="text" 
              size="small" 
              @click="showWifiPassword = !showWifiPassword"
              style="padding: 0 8px;"
            >
              {{ showWifiPassword ? '隐藏' : '查看' }}
            </el-button>
          </template>
        </el-input>
        <div v-if="dialogType === 'edit' && props.userData?.wifi_password" class="form-tips">
          原密码: {{ showWifiPassword ? props.userData.wifi_password_display || props.userData.wifi_password : '●●●●●●●●' }}
          <el-button 
            v-if="!showWifiPassword"
            type="text" 
            size="small" 
            @click="showWifiPassword = true"
            style="margin-left: 8px;"
          >
            查看
          </el-button>
          <el-button 
            v-if="showWifiPassword"
            type="text" 
            size="small" 
            @click="showWifiPassword = false"
            style="margin-left: 8px;"
          >
            隐藏
          </el-button>
        </div>
        <div v-else-if="dialogType === 'edit'" class="form-tips">
          当前未设置WIFI密码
        </div>
        <div v-else class="form-tips">
          请输入WIFI系统密码
        </div>
      </el-form-item>
      
      <el-form-item label="API Key">
        <el-input
          v-model="formData.wifi_apikey"
          placeholder="请输入API Key"
        />
        <div class="form-tips">
          用于MQTT订阅的API Key（与WIFI账号关联）
        </div>
      </el-form-item>
      
      <el-form-item label="WIFI Token" v-if="dialogType === 'edit'">
        <el-input
          v-model="formData.wifi_token"
          :placeholder="props.userData?.wifi_token ? '当前WIFI系统token' : '暂无WIFI token'"
          readonly
          :show-password="false"
        >
          <template #append>
            <el-button 
              type="text" 
              size="small" 
              @click="copyToken"
              style="padding: 0 8px;"
            >
              复制
            </el-button>
          </template>
        </el-input>
        <div class="form-tips">
          WIFI系统登录后获取的token，用于调用WIFI系统API
          <span v-if="!props.userData?.wifi_token" style="color: #f56c6c; margin-left: 8px;">
            （暂无token，请登录WIFI系统后自动获取）
          </span>
          <span v-else style="color: #67c23a; margin-left: 8px;">
            （已保存，长度: {{ props.userData?.wifi_token?.length || 0 }}）
          </span>
        </div>
      </el-form-item>
      
      <el-form-item label="API地址">
        <el-input
          v-model="formData.wifi_base_url"
          placeholder="请输入WIFI系统API地址"
        />
      </el-form-item>
      
      <el-form-item label="MQTT Broker">
        <el-input
          v-model="formData.wifi_mqtt_broker"
          placeholder="请输入MQTT broker地址（例如：192.168.1.100:1883）"
        />
        <div class="form-tips">
          用于设备状态实时订阅的MQTT broker地址（直接使用配置的地址）
        </div>
      </el-form-item>
      
      <el-form-item label="MQTT用户名">
        <el-input
          v-model="formData.mqtt_username"
          placeholder="请输入MQTT用户名（默认：test）"
        />
        <div class="form-tips">
          MQTT连接用户名，不填则使用默认值 test
        </div>
      </el-form-item>
      
      <el-form-item label="MQTT密码">
        <el-input
          v-model="formData.mqtt_password"
          type="password"
          placeholder="请输入MQTT密码（默认：123456）"
          show-password
        />
        <div class="form-tips">
          MQTT连接密码，不填则使用默认值 123456
        </div>
      </el-form-item>
      
      <el-form-item label="上级用户" v-if="dialogType === 'create'">
        <el-select
          v-model="formData.parent_user_id"
          placeholder="请选择上级用户（可选）"
          clearable
          filterable
        >
          <el-option
            v-for="user in adminUsers"
            :key="user.id"
            :label="user.username"
            :value="user.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ dialogType === 'create' ? '创建' : '保存' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import type { User, UserFormData } from '@/types/user'

const props = defineProps<{
  modelValue: boolean
  dialogType: 'create' | 'edit'
  userData: User | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const userStore = useUserStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const showWifiPassword = ref(false)

// 对话框显示状态
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

// 表单数据
const formData = ref<UserFormData>({
  username: '',
  password: '',
  confirmPassword: '',
  role: 'user',
  status: 'active',
  avatar: '',
  wifi_username: '',
  wifi_password: '',
  wifi_apikey: '',
  wifi_token: '',
  wifi_base_url: '',
  wifi_mqtt_broker: '',
  mqtt_username: '',
  mqtt_password: '',
  parent_user_id: undefined,
})

// 表单验证规则
const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== formData.value.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  role: [
    { required: true, message: '请选择用户角色', trigger: 'change' },
  ],
  status: [
    { required: true, message: '请选择用户状态', trigger: 'change' },
  ],
}

// 对话框标题
const dialogTitle = computed(() => {
  return props.dialogType === 'create' ? '创建用户' : '编辑用户'
})

// 管理员用户列表（用于选择上级用户）
const adminUsers = computed(() => {
  return userStore.userList.filter(user => user.role === 'admin')
})

// 重置表单
const resetForm = () => {
  formData.value = {
    username: '',
    password: '',
    confirmPassword: '',
    role: 'user',
    status: 'active',
    avatar: '',
    wifi_username: '',
    wifi_password: '',
    wifi_apikey: '',
    wifi_token: '',
    wifi_base_url: '',
    wifi_mqtt_broker: '',
    mqtt_username: '',
    mqtt_password: '',
    parent_user_id: undefined,
  }
}

// 监听用户数据变化，填充表单
watch(() => props.userData, (user) => {
  if (user) {
    formData.value = {
      username: user.username,
      password: '', // 编辑时不显示原密码
      confirmPassword: '',
      role: user.role,
      status: user.status,
      avatar: user.avatar || '',
      wifi_username: user.wifi_username || '',
      wifi_password: '', // 编辑时不显示原WIFI密码
      wifi_apikey: user.wifi_apikey || '',
      wifi_token: user.wifi_token || '',
      wifi_base_url: user.wifi_base_url || '',
      wifi_mqtt_broker: user.wifi_mqtt_broker || '',
      mqtt_username: user.mqtt_username || '',
      mqtt_password: user.mqtt_password || '',
      parent_user_id: user.parent_user_id,
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// 对话框打开时重置表单验证
watch(visible, (value) => {
  if (value) {
    nextTick(() => {
      formRef.value?.clearValidate()
    })
  }
})

// 对话框关闭时重置
const handleClosed = () => {
  resetForm()
  formRef.value?.clearValidate()
  showWifiPassword.value = false
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    // 验证表单
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    // 准备提交数据
    const submitData: any = {
      username: formData.value.username,
      role: formData.value.role,
      status: formData.value.status,
      avatar: formData.value.avatar || undefined,
    }
    
    // 只在创建时添加密码
    if (props.dialogType === 'create') {
      submitData.password = formData.value.password
      submitData.parent_user_id = formData.value.parent_user_id || undefined
    } else if (formData.value.password) {
      // 编辑时如果有新密码才更新
      submitData.password = formData.value.password
    }
    
    // 添加WIFI配置
    if (formData.value.wifi_username) {
      submitData.wifi_username = formData.value.wifi_username
    }
    if (formData.value.wifi_password) {
      submitData.wifi_password = formData.value.wifi_password
    }
    if (formData.value.wifi_apikey) {
      submitData.wifi_apikey = formData.value.wifi_apikey
    }
    if (formData.value.wifi_token) {
      submitData.wifi_token = formData.value.wifi_token
    }
    if (formData.value.wifi_base_url) {
      submitData.wifi_base_url = formData.value.wifi_base_url
    }
    if (formData.value.wifi_mqtt_broker) {
      submitData.wifi_mqtt_broker = formData.value.wifi_mqtt_broker
    }
    
    // 调用API
    if (props.dialogType === 'create') {
      await userStore.createUser(submitData)
      ElMessage.success('用户创建成功')
    } else if (props.userData) {
      await userStore.updateUser(props.userData.id, submitData)
      ElMessage.success('用户更新成功')
    }
    
    // 触发成功事件
    emit('success')
    visible.value = false
    
  } catch (error) {
    console.error('保存用户失败:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.user-form {
  .el-divider {
    margin: 20px 0;
  }
  
  .el-form-item {
    margin-bottom: 20px;
  }
  
  .form-tips {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
    line-height: 1.4;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>