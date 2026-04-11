<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <div class="user-dropdown">
      <div class="avatar">
        <img v-if="userInfo?.avatar" :src="userInfo.avatar" alt="avatar" />
        <span v-else class="avatar-text">{{ avatarText }}</span>
      </div>
      <span class="username" v-show="!isMobile">{{ username }}</span>
      <el-icon class="arrow"><ArrowDown /></el-icon>
    </div>
    <template #dropdown>
      <el-dropdown-menu>
        <div class="dropdown-header">
          <div class="avatar-lg">
            <img v-if="userInfo?.avatar" :src="userInfo.avatar" />
            <span v-else>{{ avatarText }}</span>
          </div>
          <p class="name">{{ username }}</p>
          <p class="role-tag">
            <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
          </p>
        </div>
        <el-divider style="margin: 4px 0;" />
        <el-dropdown-item command="profile">
          <el-icon><User /></el-icon> 个人中心
        </el-dropdown-item>
        <el-dropdown-item command="settings">
          <el-icon><Setting /></el-icon> 系统设置
        </el-dropdown-item>
        <el-divider style="margin: 4px 0;" />
        <el-dropdown-item command="logout" divided>
          <el-icon><SwitchButton /></el-icon>
          <span style="color: #ef4444;">退出登录</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { ArrowDown, User, Setting, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useResponsive } from '@/composables/useResponsive'

const router = useRouter()
const userStore = useUserStore()
const { isMobile } = useResponsive()

const userInfo = computed(() => userStore.userInfo)
const username = computed(() => userStore.username)
const roleLabel = computed(() => {
  const map: Record<string, string> = { admin: '管理员', operator: '操作员', viewer: '观察者' }
  return map[userStore.role] ?? userStore.role
})
const roleTagType = computed(() => {
  const map: Record<string, any> = { admin: '', operator: 'warning', viewer: 'info' }
  return map[userStore.role] ?? 'info'
})
const avatarText = computed(() => username.value?.charAt(0).toUpperCase() ?? 'U')

async function handleCommand(command: string) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
    await userStore.logout()
    ElMessage.success('已退出登录')
  }
}
</script>

<style lang="scss" scoped>
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 10px;
  transition: background 0.2s;

  &:hover { background: var(--el-fill-color-light); }

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;

    img { width: 100%; height: 100%; object-fit: cover; }
    .avatar-text { color: white; font-size: 13px; font-weight: 600; }
  }

  .username {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .arrow { color: var(--el-text-color-secondary); font-size: 12px; }
}

.dropdown-header {
  text-align: center;
  padding: 12px 16px 8px;

  .avatar-lg {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    margin: 0 auto 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 18px;
    font-weight: 600;
    img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
  }
  .name { font-size: 14px; font-weight: 600; margin: 2px 0; }
}
</style>
