---
name: operator-role-full-impl
overview: 完整实现三级用户权限体系(admin/user/operator)：admin可创建user和operator，user只能创建operator，operator不能创建用户；WIFI配置支持"用户→父用户→settings"三级继承；前端路由守卫+菜单过滤+页面按钮限制。
design:
  architecture:
    framework: vue
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 14px
      weight: 600
    subheading:
      size: 12px
      weight: 500
    body:
      size: 13px
      weight: 400
  colorSystem:
    primary:
      - "#6366F1"
      - "#8B5CF6"
      - "#7C3AED"
    background:
      - "#FFFFFF"
      - "#F9FAFB"
    text:
      - "#1F2937"
      - "#6B7280"
    functional:
      - "#10B981"
      - "#EF4444"
      - "#F59E0B"
todos:
  - id: backend-auth-fixes
    content: 修复后端认证层：auth.py userinfo返回真实角色 + auth_service.py增加WIFI配置父用户三级继承 + 新增get_user_by_id辅助函数
    status: pending
  - id: backend-user-permissions
    content: 细化后端用户创建权限：users.py按角色区分创建规则(admin可建user+operator, user只可建operator, operator禁止) + parent_user_id智能默认
    status: pending
    dependencies:
      - backend-auth-fixes
  - id: frontend-route-menu
    content: 前端路由权限+菜单过滤：routes.ts添加meta.roles白名单+守卫角色检查跳转 + DefaultLayout.vue menuItems改为computed按角色过滤
    status: pending
  - id: frontend-form-adaptation
    content: 用户创建表单角色适配：UserFormDialog.vue根据当前角色动态显隐(角色选择/上级用户/WIFI配置) + auth.ts修复角色层级顺序bug
    status: pending
    dependencies:
      - frontend-route-menu
  - id: frontend-operator-ui
    content: 数据更新页operator限制：TemplateUpdateView.vue按角色隐藏非推送按钮(模板切换/添加设备/新建任务/导入导出/清空)
    status: pending
    dependencies:
      - frontend-route-menu
---

## 产品概述

实现三级用户权限体系（admin / 普通用户 user / 操作员 operator），使操作员能继承父用户配置、仅访问数据更新和监控页面、只能执行推送操作。

## 核心功能

### 角色定义与权限矩阵

| 维度 | admin | user（普通用户） | operator（操作员） |
| --- | --- | --- | --- |
| **可创建的用户** | user + operator | 仅 operator | 不能创建 |
| **可见页面** | 全部9个页面 | 除"用户管理"外8个页面 | 4个：仪表盘/数据更新/更新历史/实时监控 |
| **数据更新页操作** | 全部操作 | 全部操作 | 仅：编辑字段 + 推送数据 |
| **隐藏的操作** | 无 | 无 | 添加设备、切换模板、新建任务、导入导出、清空数据 |


### 创建规则

1. **admin -> 创建 user**：parent_user_id = admin自身ID，user 继承 settings 配置，可修改自己的 WIFI 配置
2. **admin -> 创建 operator**：parent_user_id 默认=admin 自身；可选指定其他普通用户为父；operator 继承指定父用户的配置
3. **user -> 创建 operator**：parent_user_id 强制 = user 自身ID（不可选他人），operator 继承该 user 的配置
4. **operator**：无创建用户入口，登录后看不到用户管理菜单

### 配置继承链路（三级优先级）

```
登录时WIFI配置解析:
  1. 用户自身的 wifi_* 字段（如果配了独立配置）
  2. 父用户的 wifi_* 字段（通过 parent_user_id 查库获取）  ← 新增
  3. settings 全局配置（.env / config.py 兜底）
```

### 前端权限控制

- 路由守卫增加角色白名单校验，无权访问时重定向到仪表盘
- 侧边栏菜单按角色动态过滤
- 数据更新页面按角色隐藏非推送相关按钮
- 用户创建表单根据当前角色动态调整可选项

## 技术栈

- 后端: Python FastAPI + SQLite
- 前端: Vue 3 Composition API + TypeScript + Element Plus + Pinia
- 认证: JWT (PyJWT) + 内存 Session

## 实现方案

### 架构策略：分层权限控制

采用"后端最小改动 + 前端主要控制"的策略。后端负责数据正确性（创建权限、配置继承、角色返回），前端负责体验隔离（路由、菜单、按钮）。这是因为系统是内部工具，前端拦截足够防止误操作。

### 改动分三层

#### Layer 1: 后端数据层（3个文件）

**1. auth_service.py — WIFI配置继承增强（第44-48行区域）**

将当前的两级回退改为三级优先级：

```python
# 当前（只有两级）
wifi_username = user.get("wifi_username") or settings.wifi_username

# 改为（三级：自身 → 父用户 → settings）
wifi_username = user.get("wifi_username")
if not wifi_username and user.get("parent_user_id"):
    parent = await get_user_by_id(user["parent_user_id"])
    if parent:
        wifi_username = parent.get("wifi_username") or settings.wifi_username
    else:
        wifi_username = settings.wifi_username
else:
    wifi_username = wifi_username or settings.wifi_username
```

需要新增 `get_user_by_id()` 函数到 db_service 或使用现有的。对 wifi_password/wifi_apikey/wifi_base_url 四个字段都做同样处理。

**2. auth.py:55 — userinfo 返回真实角色**

```python
# 当前
"data": {"role": "admin"},

# 改为：从JWT payload解析真实角色
payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
"data": {"role": payload.get("role", "admin"), "username": payload.get("sub")},
```

**3. users.py — 创建用户权限细化（第273-308行区域）**

- `create_user` 接口：
- admin: 可创建 role=user 或 role=operator
- user: 只能创建 role=operator（且 parent_user_id 强制设为自己）
- operator: 返回 403 "无权创建用户"
- parent_user_id 逻辑：
- 当创建 role=operator 时，如果前端传了 parent_user_id 且该父用户存在，使用前端的值
- 如果前端没传（undefined/0），默认设为 current_user_id
- 当创建 role=user 时，parent_user_id 始终 = current_user_id

#### Layer 2: 前端路由与导航（2个文件）

**4. routes.ts — 路由 meta.roles + 守卫角色检查**

每个路由添加 meta.roles 白名单：

```typescript
{ path: 'users', name: 'UserList', meta: { title: '用户管理', roles: ['admin'] } },
{ path: 'devices', name: 'DeviceList', meta: { title: '设备管理', roles: ['admin', 'user'] } },
{ path: 'template/update', name: 'DataUpdateMain', meta: { roles: ['admin', 'user', 'operator'] } },
{ path: 'template/manage', name: 'TemplateManage', meta: { roles: ['admin', 'user'] } },
{ path: 'batch', name: 'BatchEdit', meta: { roles: ['admin', 'user'] } },
{ path: 'monitor/view', name: 'MonitorView', meta: { roles: ['admin', 'user', 'operator'] } },
// dashboard 和 template/history 对所有角色开放
```

守卫中增加（在 isAuthenticated 检查之后）：

```typescript
if (to.meta?.roles?.length) {
  const store = await authStore()
  const role = store.getUserRole()
  if (!to.meta.roles.includes(role)) {
    next({ name: 'Dashboard' })
    return
  }
}
```

**5. DefaultLayout.vue:183 — menuItems 改为计算属性**

从硬编码数组改为 computed，按角色过滤：

```typescript
const menuItems = computed(() => {
  const role = authStore.getUserRole()
  const allMenus = [
    { path: '/dashboard', title: '仪表盘', icon: Odomer, roles: ['admin','user','operator'] },
    { path: '/users', title: '用户管理', icon: User, roles: ['admin'] },
    { path: '/devices', title: '设备管理', icon: Monitor, roles: ['admin','user'] },
    { path: '/template/update', title: '数据更新', icon: Document, roles: ['admin','user','operator'] },
    { path: '/template/history', title: '更新历史', icon: Clock, roles: ['admin','user','operator'] },
    { path: '/template/manage', title: '模板管理', icon: FolderOpened, roles: ['admin','user'] },
    { path: '/batch', title: '批量操作', icon: TrendCharts, roles: ['admin','user'] },
    { path: '/monitor', title: '实时监控', icon: Monitor, roles: ['admin','user','operator'] },
  ]
  return allMenus.filter(m => !m.roles || m.roles.includes(role))
})
```

#### Layer 3: 页面内控制（2个文件）

**6. UserFormDialog.vue — 根据当前角色动态表单**

- 当当前角色 = `user` 时：
- 隐藏角色选择器（强制 operator）或锁定为 operator
- 隐藏上级用户下拉（强制自己为父）
- 隐藏所有 WIFI 配置字段（operator 继承父用户，不需填）
- 当当前角色 = `admin` 且正在创建 operator 时：
- 上级用户下拉列出所有 `role IN ('admin', 'user')` 的用户供选（不只是 admin）
- 默认选中当前 admin 自己
- WIFI 配置留空即可提示"留空则继承父用户"

**7. TemplateUpdateView.vue — operator 按钮限制**

用 `v-if="authStore.getUserRole() !== 'operator'"` 隐藏以下元素：

- "+ 新建" 任务按钮（toolbar-left）
- "添加设备" 按钮（toolbar-right）
- 模板切换整个 tpl-switcher 区域
- 导入/导出/清空等操作按钮
- operator 只看到：任务选择器（只读/默认第一个）、设备表格（编辑+推送）

**8. auth.ts:133 — 修复角色层级顺序（Bug修复）**

```typescript
// 当前（错误！operator 排在了 user 前面）
const roleHierarchy = ['admin', 'operator', 'user']

// 修正（admin > user > operator）
const roleHierarchy = ['admin', 'user', 'operator']
```

## 目录结构

```
WifiEsl/
├── backend/
│   ├── api/
│   │   ├── auth.py                          # [MODIFY] userinfo返回真实角色
│   │   └── users.py                         # [MODIFY] 创建权限细化+parent逻辑
│   └── services/
│       ├── auth_service.py                  # [MODIFY] WIFI配置三级继承
│       └── db_service.py                    # [MODIFY] 可能需新增get_user_by_id()
├── frontend/src/
│   ├── router/
│   │   └── routes.ts                        # [MODIFY] 路由meta.roles+守卫角色检查
│   ├── layouts/
│   │   └── DefaultLayout.vue                # [MODIFY] 菜单按角色过滤
│   ├── stores/
│   │   └── auth.ts                          # [MODIFY] 修复角色层级顺序
│   └── views/
│       ├── template/
│       │   └── TemplateUpdateView.vue       # [MODIF] operator按钮限制
│       └── user/components/
│           └── UserFormDialog.vue           # [MODIFY] 按角色动态表单
```

## 关键注意事项

- **性能**：auth_service.py 中父用户查询是异步 DB 操作（每次登录执行一次，可接受）。避免在每次API调用时重复查询——登录时解析好存入 session/JWT 即可。
- **兼容性**：现有 admin 和 user 用户无 parent_user_id 或 parent_user_id=0 的，走原有 settings 回退逻辑，行为不变。
- **向后兼容**：路由守卫中未标注 roles 的路由对所有已登录角色开放（dashboard、login、history）。
- **边界情况**：parent_user_id 指向不存在的用户时，静默降级到 settings 配置并记录 warning 日志。

## 设计概述

本方案主要是功能性改造，不涉及全新UI设计。但需要对用户管理和数据更新页面进行角色适配的界面微调。

### 设计理念

- 保持现有视觉风格一致（紫色渐变主题、Element Plus 组件体系）
- 权限限制通过**优雅降级**方式呈现（隐藏而非置灰禁用，减少认知负担）
- 操作员界面追求极简：只保留核心推送工作流，移除一切干扰元素

### 页面设计变更

#### Page 1: 用户管理页面（UserListView + UserFormDialog）

**变更点**：创建用户对话框根据当前角色动态变化

- **admin 创建时**：
- 角色下拉：显示 admin/operator/user 三选项
- 上级用户：当选择 operator 时显示，列出所有 admin+user 角色用户
- WIFI配置区：始终显示

- **user 创建时**：
- 角色选择：隐藏或锁定为 operator（不可见/不可改）
- 上级用户：隐藏（强制自己为父）
- WIFI配置区：隐藏整块，显示提示文字"操作员将继承您的WIFI配置"

#### Page 2: 数据更新页面（TemplateUpdateView）

**变更点**：operator 角色下的工具栏和表格区域精简

- **顶栏左侧**：隐藏模板切换器，任务选择器保留但只读（自动选中第一个可用任务）
- **顶栏右侧**：只保留"历史记录"链接，隐藏"添加设备"按钮
- **设备表格**：完整保留编辑和推送功能，radio 和 input 正常工作
- **底部操作栏**：只保留"推送数据"按钮，隐藏导入/导出/清空等

### 交互反馈

- operator 登录后侧边栏自动收缩至4个菜单项，视觉上更简洁
- 如果 operator 直接输入了无权访问的URL，路由守卫重定向到 Dashboard 并可考虑加一条轻量 ElMessage 提示

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 确认 `get_user_by_id()` 函数是否已在 db_service/db_service_extended 中存在，以及 TemplateUpdateView.vue 中需要隐藏的按钮的完整列表（导入导出、清空、新建任务等的精确位置和 v-if 条件写法）
- Expected outcome: 确认是否需要新增数据库函数，以及页面限制的精确代码位置