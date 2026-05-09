---
name: user-create-user-with-data-inheritance
overview: 实现普通用户(user)可创建普通用户(user)和操作员(operator)，子用户与父用户完全共享数据（设备、任务、模板、WIFI配置），支持无限层级树形结构。
design:
  architecture:
    framework: vue
  styleKeywords:
    - 企业级管理后台风格
    - 清晰的层级可视化
    - 最小化UI变更
    - Element Plus设计规范
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 18px
      weight: 600
    subheading:
      size: 14px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#409EFF"
      - "#337ECC"
    background:
      - "#F5F7FA"
      - "#FFFFFF"
    text:
      - "#303133"
      - "#606266"
      - "#909399"
    functional:
      - "#67C23A"
      - "#E6A23C"
      - "#F56C6C"
todos:
  - id: add-family-tree-func
    content: 在 db_service_extended.py 新增 get_family_tree_user_ids() 家族树查询函数
    status: completed
  - id: modify-create-permission
    content: 修改 users.py check_create_permission() 允许user创建user角色
    status: completed
  - id: modify-task-sharing
    content: 修改 tasks.py _get_allowed_user_ids() 使用家族树实现数据完全共享
    status: completed
    dependencies:
      - add-family-tree-func
  - id: extend-wifi-inheritance
    content: 修改 users.py 创建用户逻辑，使user角色也继承WIFI/MQTT配置
    status: completed
  - id: expand-user-list
    content: 修改 users.py 用户列表接口，user角色可查看整棵家族树成员
    status: completed
    dependencies:
      - add-family-tree-func
  - id: expand-update-delete-perms
    content: 修改 users.py 更新/删除权限，允许管理树内非admin用户
    status: completed
    dependencies:
      - add-family-tree-func
  - id: update-frontend-role-options
    content: 修改 UserFormDialog.vue currentRoleOptions 允许user角色选择创建user
    status: completed
  - id: add-parent-column-ui
    content: UserListView用户新增上级用户列，展示层级关系
    status: completed
---

## 产品概述

实现用户层级体系的**完全共享模式（方案B）**：允许普通用户(user)创建其他普通用户(user)和操作员(operator)，子用户与父用户完全共享数据（设备、任务、WIFI配置、模板），且子用户可以修改父用户的数据，不限制层级深度。

## 核心功能

### 1. 创建权限扩展

- 普通用户(user)可创建的角色从仅 `operator` 扩展为 `user` + `operator`
- 任何角色均不可创建 `admin`

### 2. 数据完全共享（家族树模式）

同一棵用户树内的所有成员共享全部业务数据：

- **任务数据**：树内任何人创建的任务，树内所有人可见、可修改、可删除、可执行推送
- **设备列表**：通过继承相同的WIFI/MQTT配置，子用户自动看到父用户的设备；且可修改父用户的设备关联数据
- **WIFI/MQTT配置**：创建子用户时自动继承父用户的完整配置（当前仅operator继承，需扩展到user角色）
- **模板数据**：模板本身全局无过滤，无需改动

### 3. 用户管理权限扩展

- 用户列表展示：普通用户可查看整棵家族树的所有成员（递归所有后代+自身+祖先信息）
- 编辑权限：可编辑自己创建的所有非admin子用户（包括user角色）
- 删除权限：可删除自己创建的所有非admin子用户（包括user角色）
- 禁止操作：不可删除/修改admin、不可删除自己

### 4. 前端适配

- 创建用户表单中，当登录用户为 `user` 角色时，角色选择器同时显示"普通用户"和"操作员"两个选项

## 技术栈

- 后端：Python + FastAPI + SQLite (aiosqlite)
- 前端：Vue 3 + TypeScript + Element Plus + Pinia
- 数据库：SQLite（users表已有 parent_user_id / created_by 字段）

## 实现策略

### 核心思路：家族树(Family Tree)数据共享模型

方案B的关键是引入"家族树"概念——以 `parent_user_id` 为链，将所有有血缘关系的用户组成一棵树。树内所有成员对业务数据拥有同等权限（可见+可修改）。

```
          admin(根)
           │
         user_A ──────── user_B
        /    \              \
   user_A1  operator_A1   user_B1
      │
   user_A1_1
```

user_A1_1 可以看到并修改 admin、user_A、user_A1、operator_A1、user_A1_1 的全部数据。

### 架构改动点

#### 改动点1：新增家族树查询函数 — `db_service_extended.py`

新增 `get_family_tree_user_ids(user_id)` 函数：

1. 向上递归：沿 `parent_user_id` 链找到根用户，收集所有祖先ID
2. 向下递归：从当前用户出发，找到所有后代ID（BFS/DFS遍历 parent_user_id=当前 的记录）
3. 返回合并去重后的完整ID列表

这是整个方案的核心基础设施，被后续所有数据查询依赖。

```python
async def get_family_tree_user_ids(user_id: int) -> list[int]:
    """获取用户所在家族树的所有用户ID（含自身、祖先、后代）"""
    db = await get_db()
    tree_ids = set()
    
    # 1. 向上找所有祖先
    current = user_id
    while current > 0:
        tree_ids.add(current)
        cur = await db.execute("SELECT parent_user_id FROM users WHERE id=?", (current,))
        row = await cur.fetchone()
        if not row or not row["parent_user_id"] or row["parent_user_id"] == 0:
            break
        current = row["parent_user_id"]
    
    # 2. 向下找所有后代 (BFS)
    queue = [user_id]
    while queue:
        pid = queue.pop(0)
        cur = await db.execute("SELECT id FROM users WHERE parent_user_id=? AND status='active'", (pid,))
        children = [r["id"] for r in await cur.fetchall()]
        for cid in children:
            if cid not in tree_ids:
                tree_ids.add(cid)
                queue.append(cid)
    
    return list(tree_ids)
```

#### 改动点2：创建权限矩阵 — `backend/api/users.py:139-152`

修改 `check_create_permission()` 函数：

| 创建者 | 可创建 | 变更 |
| --- | --- | --- |
| admin | user, operator | 不变 |
| **user** | **user + operator** | **从仅operator扩展为两者** |
| operator | 无 | 不变 |


仅改一行：第150行 `return target_role == "operator"` → `return target_role in ("user", "operator")`

#### 改动点3：任务数据共享 — `backend/api/tasks.py:181-201`

修改 `_get_allowed_user_ids()` 函数：

**当前逻辑**：

- operator → `[self, parent_user_id]`（只看一层）
- admin/user → `None`（只看自己的）

**新逻辑**：

- 非admin → 调用 `get_family_tree_user_ids(user_id)` 获取整棵树的ID列表
- admin → 保持 `None`（admin看所有人的，由现有逻辑处理）

这样树内任何人的任务对所有树成员可见且可修改。

#### 改动点4：创建用户时的WIFI继承 — `backend/api/users.py:333-361`

**当前逻辑**：仅在 `user_data.role == "operator"` 时触发继承

**新逻辑**：在 `role != "admin"` 时都触发继承（即 `user` 和 `operator` 都继承父用户WIFI配置）。因为新创建的 `user` 也需要立即能访问父用户的设备。

具体改动：第333行 `if user_data.role == "operator":` → `if user_data.role in ("operator", "user"):`

#### 改动点5：用户列表展示 — `backend/api/users.py:183-192`

**当前逻辑**：user角色只能看到「自己 + 直接子operator」

**新逻辑**：user角色可以看到「整棵家族树的所有成员」

- 使用新的 `get_family_tree_user_ids()` 获取树内所有ID
- 查询这些ID的用户信息返回
- 同时保留搜索/分页/状态过滤功能

#### 改动点6：更新权限 — `backend/api/users.py:416-429`

**当前逻辑**：user 只能编辑 `created_by == self and role == "operator"` 的用户

**新逻辑**：user 可以编辑树内任何非admin的非自己的用户（即 `target_user.id in family_tree_ids and target_user.role != "admin"`）

- 不能修改admin
- 不能修改自己的角色（保持不变）
- 可以修改树内其他user/operator的信息和角色

#### 改动点7：删除权限 — `backend/api/users.py:506-515`

**当前逻辑**：user 只能删除 `created_by == self and role == "operator"` 的用户

**新逻辑**：与更新权限一致 —— 可以删除树内任何非admin的非自身的用户

#### 改动点8：前端角色选项 — `frontend/src/views/user/components/UserFormDialog.vue:324-329`

修改 `currentRoleOptions` 计算属性：

```typescript
// 修改前
if (myRole === 'user') return ['operator']

// 修改后
if (myRole === 'user') return ['user', 'operator']
```

同时确保模板中第46行的 `v-if` 条件正确渲染两个选项（已有 `v-if="currentRoleOptions.includes('user')"` 控制 user 选项显示，无需改模板）。

## 目录结构

```
WifiEsl/
├── backend/
│   ├── api/
│   │   ├── users.py                    # [MODIFY] 权限矩阵、用户列表、创建/编辑/删除权限
│   │   ├── tasks.py                    # [MODIFY] _get_allowed_user_ids() 使用家族树
│   │   └── template.py                 # [NO CHANGE] 模板已全局无过滤
│   └── services/
│       └── db_service_extended.py      # [MODIFY] 新增 get_family_tree_user_ids() 函数
└── frontend/
    └── src/views/user/
        └── components/
            └── UserFormDialog.vue     # [MODIFY] currentRoleOptions 允许user创建user
```

## 关键注意事项

1. **性能考量**：`get_family_tree_user_ids()` 每次请求可能执行多次DB查询（递归祖先+后代）。对于层级深度不大的场景（通常<10层），性能影响可忽略。如后续需要优化可加缓存或单条CTE SQL。
2. **设备数据天然共享**：设备的可见性取决于WIFI系统token。由于子用户继承了父用户的WIFI配置（username/password/apikey/base_url），调用WIFI系统API获取的设备列表自然相同。无需额外改动 devices.py。
3. **循环引用防护**：在 `get_family_tree_user_ids()` 的向下遍历中用 `set()` 去重已访问节点，防止因数据异常导致的无限循环。
4. **向后兼容**：admin的行为完全不改变；现有operator的权限也不改变（operator原本就能看到parent的任务，现在看到范围不变或更大）；唯一行为变化的是 `user` 角色。
5. **删除级联风险**：删除一个中间层的user会导致其下所有子用户的 `parent_user_id` 指向一个不存在的用户。建议删除时将子用户的 `parent_user_id` 提升为被删除用户的父用户，或在文档中说明此限制。

## 设计概述

本需求主要涉及后端权限逻辑和前端表单选项调整，不需要新建页面或大幅重构UI。仅需微调现有的用户管理模块：

### 页面1：用户管理页 (UserListView.vue) - 微调

- 在用户列表表格中新增"上级用户"列，显示每个用户的父用户名，帮助管理员和用户直观理解层级关系
- 表格行支持缩进或树形展示以体现层级结构（可选优化）

### 页面2：用户创建/编辑对话框 (UserFormDialog.vue) - 微调

- 角色选择器在当前登录用户为 `user` 角色时，同时展示"普通用户"和"操作员"两个选项
- 当选择创建"user"角色时，提示文字说明该子用户将与您共享全部数据和权限

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 深度分析用户权限体系和数据查询代码，确认所有需要改动的函数签名、参数、返回值
- Expected outcome: 精确定位每个需要修改的函数位置和上下文，确保实施方案与现有架构完全兼容