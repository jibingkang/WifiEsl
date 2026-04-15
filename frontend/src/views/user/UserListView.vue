<template>
  <div class="user-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <div class="page-actions">
        <el-button type="primary" @click="handleCreate" :icon="Plus">
          新增用户
        </el-button>
        <el-button @click="refresh" :icon="Refresh" :loading="loading">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon total">
                <el-icon><User /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-label">用户总数</div>
                <div class="stats-value">{{ stats.total }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon admin">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-label">管理员</div>
                <div class="stats-value">{{ stats.admin_count }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon operator">
                <el-icon><User /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-label">操作员</div>
                <div class="stats-value">{{ stats.operator_count }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-content">
              <div class="stats-icon active">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stats-info">
                <div class="stats-label">活跃用户</div>
                <div class="stats-value">{{ stats.active_count }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :model="queryParams" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="请输入用户名"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </el-form-item>
        
        <el-form-item label="用户角色">
          <el-select
            v-model="queryParams.role"
            placeholder="全部角色"
            clearable
            @change="handleSearch"
          >
            <el-option label="管理员" value="admin" />
            <el-option label="操作员" value="operator" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="用户状态">
          <el-select
            v-model="queryParams.status"
            placeholder="全部状态"
            clearable
            @change="handleSearch"
          >
            <el-option label="活跃" value="active" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :icon="Search">
            搜索
          </el-button>
          <el-button @click="handleReset" :icon="Refresh">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table
        :data="userList"
        v-loading="loading"
        style="width: 100%"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        
        <el-table-column prop="username" label="用户名" min-width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="32" :src="row.avatar" class="user-avatar">
                {{ row.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="user-info">
                <div class="username">{{ row.username }}</div>
                <div class="user-role">
                  <el-tag :type="getRoleType(row.role)" size="small">
                    {{ getRoleLabel(row.role) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" effect="plain">
              {{ row.status === 'active' ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="wifi_username" label="WIFI用户名" min-width="120" />
        <el-table-column prop="wifi_base_url" label="API地址" min-width="150" show-overflow-tooltip />
        
        <el-table-column prop="wifi_apikey" label="API Key" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.wifi_apikey">
              {{ row.wifi_apikey.slice(0, 4) }}****
            </span>
            <span v-else class="text-gray-400">未设置</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="wifi_mqtt_broker" label="MQTT Broker" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.wifi_mqtt_broker">
              {{ row.wifi_mqtt_broker }}
            </span>
            <span v-else class="text-gray-400">未设置</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="updated_at" label="更新时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleEdit(row)"
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button
              type="info"
              link
              size="small"
              @click="handleViewWifiConfig(row)"
              :icon="Connection"
            >
              WIFI配置
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
              :icon="Delete"
              :disabled="row.role === 'admin'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 用户表单对话框 -->
    <user-form-dialog
      v-model="dialogVisible"
      :dialog-type="dialogType"
      :user-data="currentUser"
      @success="handleDialogSuccess"
    />
    
    <!-- WIFI配置对话框 -->
    <wifi-config-dialog
      v-model="wifiDialogVisible"
      :user-id="currentUserId"
      @success="handleWifiConfigSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Refresh,
  Search,
  Edit,
  Delete,
  User,
  UserFilled,
  CircleCheck,
  Connection,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import type { User as UserType, UserListQuery } from '@/types/user'
import UserFormDialog from './components/UserFormDialog.vue'
import WifiConfigDialog from './components/WifiConfigDialog.vue'

const userStore = useUserStore()

// 响应式数据
const userList = computed(() => userStore.userList)
const total = computed(() => userStore.total)
const loading = computed(() => userStore.loading)
const queryParams = computed({
  get: () => userStore.queryParams,
  set: (value) => {
    userStore.queryParams = value
  },
})

// 对话框状态
const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const currentUser = ref<UserType | null>(null)

// WIFI配置对话框状态
const wifiDialogVisible = ref(false)
const currentUserId = ref<number | null>(null)

// 统计信息
const stats = computed(() => userStore.getUserStats())

// 生命周期
onMounted(() => {
  fetchUsers()
})

// 获取用户列表
const fetchUsers = async () => {
  try {
    await userStore.fetchUsers()
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 刷新
const refresh = () => {
  fetchUsers()
}

// 搜索
const handleSearch = () => {
  queryParams.value.page = 1
  fetchUsers()
}

// 重置搜索
const handleReset = () => {
  userStore.resetQuery()
  fetchUsers()
}

// 分页大小改变
const handleSizeChange = (size: number) => {
  queryParams.value.page_size = size
  queryParams.value.page = 1
  fetchUsers()
}

// 当前页改变
const handleCurrentChange = (page: number) => {
  queryParams.value.page = page
  fetchUsers()
}

// 创建用户
const handleCreate = () => {
  dialogType.value = 'create'
  currentUser.value = null
  dialogVisible.value = true
}

// 编辑用户
const handleEdit = (user: UserType) => {
  dialogType.value = 'edit'
  currentUser.value = { ...user }
  dialogVisible.value = true
}

// 查看WIFI配置
const handleViewWifiConfig = (user: UserType) => {
  currentUserId.value = user.id
  wifiDialogVisible.value = true
}

// 删除用户
const handleDelete = async (user: UserType) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await userStore.deleteUser(user.id)
    ElMessage.success('删除成功')
  } catch (error) {
    // 用户取消删除
  }
}

// 对话框成功回调
const handleDialogSuccess = () => {
  dialogVisible.value = false
  fetchUsers()
}

// WIFI配置成功回调
const handleWifiConfigSuccess = () => {
  wifiDialogVisible.value = false
  fetchUsers()
}

// 工具函数
const getRoleLabel = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    operator: '操作员',
    user: '普通用户',
  }
  return roleMap[role] || role
}

const getRoleType = (role: string) => {
  const roleTypeMap: Record<string, string> = {
    admin: 'danger',
    operator: 'warning',
    user: 'info',
  }
  return roleTypeMap[role] || ''
}

const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
</script>

<style scoped lang="scss">
.user-management {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #333;
      margin: 0;
    }
    
    .page-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .stats-cards {
    margin-bottom: 24px;
    
    .stats-card {
      :deep(.el-card__body) {
        padding: 20px;
      }
      
      .stats-content {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .stats-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          
          &.total {
            background-color: #e8f4ff;
            color: #409eff;
          }
          
          &.admin {
            background-color: #fef0f0;
            color: #f56c6c;
          }
          
          &.operator {
            background-color: #fdf6ec;
            color: #e6a23c;
          }
          
          &.active {
            background-color: #f0f9eb;
            color: #67c23a;
          }
        }
        
        .stats-info {
          .stats-label {
            font-size: 14px;
            color: #909399;
            margin-bottom: 4px;
          }
          
          .stats-value {
            font-size: 24px;
            font-weight: 600;
            color: #303133;
          }
        }
      }
    }
  }
  
  .filter-card {
    margin-bottom: 16px;
    
    :deep(.el-card__body) {
      padding: 20px;
    }
  }
  
  .table-card {
    :deep(.el-card__body) {
      padding: 20px;
    }
    
    .user-cell {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .user-avatar {
        flex-shrink: 0;
      }
      
      .user-info {
        .username {
          font-weight: 500;
          color: #303133;
          margin-bottom: 4px;
        }
        
        .user-role {
          display: flex;
          gap: 4px;
        }
      }
    }
    
    .pagination {
      display: flex;
      justify-content: flex-end;
      margin-top: 24px;
    }
  }
}
</style>