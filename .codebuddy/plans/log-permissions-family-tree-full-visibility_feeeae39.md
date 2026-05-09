---
name: log-permissions-family-tree-full-visibility
overview: 操作日志/推送日志/设备事件/update-history 的权限模型改造：admin看全部、user看整棵家族树、operator只看自己。同时修复 update-history 接口的权限漏洞。
todos:
  - id: rewrite-allowed-user-ids
    content: 重写 logs.py 中 _build_allowed_user_ids() 函数：user 角色走 BFS 家族树遍历，operator 仅返回自己，新增 super_admin 分支
    status: completed
  - id: fix-update-history-perms
    content: 修复 template.py 中 get_update_history_api() 接口：添加 request 参数、获取用户身份信息、传入 allowed_user_ids 过滤
    status: completed
  - id: verify-and-test
    content: 验证修改后4个接口的权限逻辑正确性，检查 lint 错误
    status: completed
    dependencies:
      - rewrite-allowed-user-ids
      - fix-update-history-perms
---

## 产品概述

重构操作日志/推送日志/设备事件/更新历史 4个接口的权限模型，实现**按角色分层**的日志可见性控制。

## 核心需求

- **admin / super_admin**：看到全量日志（不过滤）
- **user（普通用户）**：看到**整棵家族树**所有成员的日志记录——用于监管下级用户操作。包括向上找到祖先 + 向下递归所有后代
- **operator（操作员）**：只能看到**自己的**操作记录

### 用户树示例与预期效果

```
admin
 └── user_A                    ← user_A 登录能看到全部6人的日志
      ├── op_A                 ← op_A 只能看自己
      ├── user_A1 (监管者)     ← user_A1 登录也能看到全部6人(同树)
      │   └── op_A1_1          ← op_A1_1 只能看自己
      └── user_A2              ← user_A2 同样看到全部6人
           └── op_A2_1         ← op_A2_1 只能看自己
```

### 附带修复

- `template.py` 的 `/update-history` 接口当前**完全无权限过滤**，任何登录用户都能看到全量数据，需补上鉴权

### 涉及接口清单

| 接口 | 路由 | 文件 | 当前问题 |
| --- | --- | --- | --- |
| 操作日志 | `GET /operation-logs` | `logs.py:118` | user 只查一层子用户 |
| 推送日志 | `GET /push-logs` | `logs.py:170` | 同上 |
| 设备事件 | `GET /device-events-logs` | `logs.py:223` | MAC 过滤依赖上述逻辑 |
| 更新历史 | `GET /update-history` | `template.py:150` | 无任何权限过滤 |


## 技术栈

- 后端框架：Python FastAPI + aiosqlite（异步 SQLite）
- 权限函数位于：`backend/api/logs.py`
- 漏洞接口位于：`backend/api/template.py`
- 数据库服务层：`backend/services/db_service.py`（已支持 `allowed_user_ids` 参数）

## 实现方案

### 核心策略：BFS 家族树遍历

重写 `_build_allowed_user_ids()` 函数，将权限逻辑从"单层查询"改为"家族树完整遍历"：

```python
# logs.py — 新的 _build_allowed_user_ids() 逻辑伪码
async def _build_allowed_user_ids(user_id, role):
    if role in ("admin", "super_admin"):
        return None          # 不过滤，看全部
    
    if role == "operator":
        return [user_id]     # 仅自己
    
    # === role == "user": 整棵家族树 ===
    # Step 1: 向上找根祖先（沿 parent_user_id 链直到根）
    root_id = user_id
    while True:
        parent = await get_user_by_id(root_id)
        pid = parent.get("parent_user_id", 0) if parent else 0
        if pid and pid > 0:
            root_id = pid
        else:
            break
    
    # Step 2: 从根向下 BFS 收集所有后代 ID
    ids = set()
    queue = [root_id]
    while queue:
        cur_id = queue.pop(0)
        ids.add(cur_id)
        # 查所有以 cur_id 为 parent 的活跃用户
        children = await db.execute(
            "SELECT id FROM users WHERE parent_user_id=? AND status='active'", (cur_id,)
        )
        for row in children:
            if row["id"] not in ids:
                queue.append(row["id"])
    
    return list(ids)
```

### 改动点详情

#### 改动 1：`backend/api/logs.py` — 重写 `_build_allowed_user_ids()` (L51-79)

| 角色 | 旧行为 | 新行为 |
| --- | --- | --- |
| admin | None（不过滤） | None（不变） |
| super_admin | 走到 default 返回 `[user_id]` | **None（修复：不过滤）** |
| user | `[self, 直属子]` | **整棵 BFS 树（祖先+所有后代）** |
| operator | `[self, parent]` | **`[self]` 仅自己** |


同时新增内部辅助函数 `_find_family_tree_root()` 用于沿 `parent_user_id` 链向上查找树根。

#### 改动 2：`backend/api/logs.py` — `_build_allowed_macs()` (L82-102)

无需修改代码逻辑，该函数依赖 `_build_allowed_user_ids()` 的返回值，改动 1 自动生效。

#### 改动 3：`backend/api/template.py` — `get_update_history_api()` (L150-170)

- 新增导入：`get_current_user_id_from_token`, `get_user_by_id`
- 新增参数：`request: Request`
- 调用 `_get_user_info()` 或内联获取用户信息（由于 template.py 没有 logs.py 的辅助函数，可选择复制一个简化版或直接内联）
- 将 `allowed_user_ids` 传给 `get_logs()`

### 性能分析

- **BFS 查询次数**：最坏情况 O(N) 次数据库查询，N 为树节点数。实际场景中每棵树通常 < 50 个用户，每次查询为简单的索引主键查找（`idx_users_parent` 已建索引），延迟可忽略。
- **优化空间**：如果未来用户量增大，可改为一次性的 CTE 递归 SQL 查询（SQLite 3.35+ 支持 WITH RECURSIVE），当前阶段无必要。

## 架构设计

```
请求进入 → _get_user_info() 获取角色
         → _build_allowed_user_ids() 计算 ID 列表
            ├─ admin/super_admin → None (不过滤)
            ├─ operator → [自身]
            └─ user → BFS 整棵树 → [root, ...所有后代]
         → get_logs(get_push_logs/get_device_events) 带过滤查询
         → 返回结果
```

## 目录结构

```
backend/
├── api/
│   ├── logs.py              # [MODIFY] 重写 _build_allowed_user_ids() 为家族树 BFS；新增 super_admin 分支
│   └── template.py          # [MODIFY] 修复 get_update_history_api() 补充权限过滤
```

## Agent Extensions

- **code-explorer**
- Purpose: 确认 `get_user_by_id` 在 template.py 中是否可直接导入、以及 `db_service.py` 中 `get_logs` 的 `allowed_user_ids` SQL 实现细节
- Expected outcome: 验证方案中 import 和参数传递的可行性