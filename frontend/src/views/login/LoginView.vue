<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="login-bg">
      <div class="bg-gradient" />
      <div class="bg-shapes">
        <span class="shape shape-1" />
        <span class="shape shape-2" />
        <span class="shape shape-3" />
      </div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card-wrapper">
      <el-card class="login-card" shadow="always">
        <!-- Logo区域 -->
        <div class="login-header">
          <div class="logo-icon">
            <el-icon :size="32"><Connection /></el-icon>
          </div>
          <h1 class="login-title">WIFI标签管理系统</h1>
          <p class="login-subtitle">智能电子价签控制平台</p>
        </div>

        <!-- 登录表单 -->
        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          size="large"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item>
            <div class="login-options">
              <el-checkbox v-model="rememberMe">记住登录状态</el-checkbox>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 底部信息 -->
        <div class="login-footer">
          <span class="version">v1.0.0</span>
          <ThemeToggle />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Connection } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单引用
const formRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(true)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
})

// 校验规则
const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度为2-20个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度为6-30个字符', trigger: 'blur' },
  ],
}

/**
 * 处理登录
 */
async function handleLogin() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      console.log('开始登录，用户名:', loginForm.username)
      const res = await authStore.login(loginForm.username, loginForm.password)
      console.log('登录结果:', res)

      ElMessage.success(`欢迎回来，${authStore.userInfo?.username || loginForm.username}！`)

      // 跳转到目标页面或首页
      const redirect = (route.query.redirect as string) || '/dashboard'
      console.log('跳转到:', redirect)
      router.push(redirect)
    } catch (error: any) {
      console.error('登录捕获的错误:', error)
      const errorMsg = error.message || '登录失败，请检查用户名和密码'
      console.error('显示错误消息:', errorMsg)
      ElMessage.error(errorMsg)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

// ========== 背景装饰 ==========
.login-bg {
  position: absolute;
  inset: 0;
  z-index: 0;

  .bg-gradient {
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg,
      #0f172a 0%,
      #1e1b4b 25%,
      #312e81 50%,
      #4338ca 75%,
      #6366f1 100%
    );
  }

  .bg-shapes {
    position: absolute;
    inset: 0;

    .shape {
      position: absolute;
      border-radius: 50%;
      opacity: 0.08;
      background: white;
    }

    .shape-1 {
      width: 600px;
      height: 600px;
      top: -200px;
      right: -100px;
      animation: float 20s ease-in-out infinite;
    }

    .shape-2 {
      width: 400px;
      height: 400px;
      bottom: -150px;
      left: -100px;
      animation: float 15s ease-in-out infinite reverse;
    }

    .shape-3 {
      width: 200px;
      height: 200px;
      top: 40%;
      left: 10%;
      animation: float 12s ease-in-out infinite 3s;
    }
  }
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(30px, -30px); }
  66% { transform: translate(-20px, 20px); }
}

// ========== 登录卡片 ==========
.login-card-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  padding: 16px;
}

.login-card {
  border-radius: 20px !important;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(99, 102, 241, 0.1) !important;

  :deep(.el-card__body) {
    padding: 40px 36px 24px;
  }
}

// 暗色模式适配
html.dark {
  .login-card {
    background: rgba(30, 27, 75, 0.9) !important;
    border-color: rgba(99, 102, 241, 0.2) !important;
  }
}

// ========== 头部 ==========
.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  margin-bottom: 18px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
}

.login-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.5px;
  margin: 0 0 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

html.dark {
  .login-title { color: #f1f5f9; }
  .login-subtitle { color: #64748b; }
}

// ========== 表单 ==========
:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-input__wrapper) {
  border-radius: 11px;
  padding: 5px 12px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: all 0.25s;

  &:hover { box-shadow: 0 0 0 1px #cbd5e1 inset; }
  &.is-focus { box-shadow: 0 0 0 1.5px #6366f1 inset, 0 0 0 3px rgba(99, 102, 241, 0.1) !important; }
}

html.dark {
  :deep(.el-input__wrapper) {
    box-shadow: 0 0 0 1px #334155 inset;
    &:hover { box-shadow: 0 0 0 1px #475569 inset; }
  }
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

// ========== 登录按钮 ==========
.login-btn {
  width: 100%;
  height: 46px;
  border-radius: 11px !important;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
  }

  &:active { transform: translateY(0); }
}

// ========== 底部 ==========
.login-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.version {
  font-size: 12px;
  color: #cbd5e1;
}

html.dark {
  .login-footer { border-top-color: #334155; }
  .version { color: #475569; }
}

// ========== 响应式 ==========
@media (max-width: 480px) {
  .login-card-wrapper {
    padding: 12px;
  }
  .login-card :deep(.el-card__body) {
    padding: 28px 24px 20px;
  }
  .logo-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
  }
  .login-title { font-size: 19px; }
}
</style>
