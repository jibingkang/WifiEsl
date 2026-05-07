---
name: device-operation-log-audit
overview: 设计并实现设备操作记录（审计日志）方案：记录每个标签被谁、何时、更新了什么内容，同时扩展设备事件日志覆盖在线/离线等操作。包含后端表结构、API、推送日志补录和前端展示改造。
design:
  architecture:
    framework: vue
  styleKeywords:
    - Enterprise Audit Log Dashboard
    - Data-Dense Table Layout
    - Color-Coded Action Types
    - Expandable Detail Panel
    - Filter Bar with Time Range
    - Clean Information Hierarchy
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 18px
      weight: 600
    subheading:
      size: 14px
      weight: 500
    body:
      size: 13px
      weight: 400
  colorSystem:
    primary:
      - "#6366F1"
      - "#8B5CF6"
    background:
      - "#FFFFFF"
      - "#F9FAFB"
      - "#F3F4F6"
    text:
      - "#111827"
      - "#374151"
      - "#9CA3AF"
    functional:
      - "#10B981"
      - "#EF4444"
      - "#F59E0B"
      - "#3B82F6"
---

## 产品概述

为 WiFi 电子价签系统设计一套完整的**操作记录与审计日志**功能，让客户能够追溯"哪个标签什么时候被谁更新了什么内容"，同时将设备的在线/离线等状态变化也纳入日志记录体系。

## 核心需求

### 需求 1：标签级推送记录（核心）

客户需要看到**每台设备（标签）的完整操作轨迹**：

- 谁（用户名）在什么时间，对哪台设备（MAC）执行了什么操作（数据推送）
- 推送了**什么具体内容**（模板字段值，如商品名、价格等），而不只是"成功/失败"
- 推送结果（成功/失败/超时）

### 需求 2：设备状态变化日志

设备的在线/离线、电量变化、按键触发等事件也需要在日志中可查：

- 设备上线/下线时间
- 电量告警事件
- 按钮按下事件（如有人按了价签上的按键）

### 需求 3：统一的操作记录页面

一个集中的页面查看所有类型的操作记录，支持筛选和搜索。

---

## 现状痛点分析（已通过代码验证）

| 问题点 | 现状 | 影响 |
| --- | --- | --- |
| **新任务推送不记日志** | `tasks.py:execute_task_push` 完全不写 `operation_logs` 表 | 客户用任务推送后，历史页看不到任何记录 |
| **旧 batch 推送的日志无内容** | `batch.py:150` 写了 `operation_logs` 但只记 MAC+成功失败，不记推了什么数据 | 不知道推了什么内容 |
| **HistoryPage 只查一种类型** | `template.py:156` 查询过滤 `action='batch_update_template'`，新任务推送的 action 不匹配 | 新推送记录完全不可见 |
| **device_events 与用户脱节** | `device_events` 只有 mac+event_type，不知道是哪个用户的设备，也没有"谁操作的" | 无法做审计追踪 |
| **operation_logs 缺少 user_id** | 没有 user_id 字段，多租户无法按用户过滤 | 操作员角色下无法隔离查看 |
| **实际数据为空** | 数据库中 operation_logs 最新 15 条全是 LOGIN，没有任何推送记录 | 说明当前系统对客户来说等于没有操作记录 |


## 技术栈

- 后端: Python FastAPI + SQLite (aiosqlite)
- 前端: Vue 3 Composition API + TypeScript + Element Plus + Pinia
- 现有数据库表: `operation_logs`、`device_events`、`update_tasks`、`task_devices`

## 实现方案：增强式审计日志（最小改动 + 最大收益）

### 架构策略：三层分离 + 统一视图

```
┌─────────────────────────────────────────────┐
│              统一操作记录 API                 │
│    GET /api/v1/operation-logs               │
│    (支持 action/mac/user_id/time 筛选)      │
└──────────┬──────────────────┬───────────────┘
           │                  │
    ┌──────▼──────┐   ┌──────▼──────────┐
    │ operation_logs│   │ device_events   │
    │ (用户操作类)  │   │ (设备事件类)     │
    │              │   │                  │
    │ TASK_PUSH    │   │ online/offline   │
    │ DEVICE_ONLINE│   │ battery_reply    │
    │ TASK_CREATE  │   │ button           │
    │ LOGIN/LOGOUT │   │ display_reply    │
    └──────────────┘   └──────────────────┘
```

**核心思路**: 复用现有 `operation_logs` 表，扩展 action 类型；`device_events` 保持原样作为原始数据源，在查询时做联合展示。

### Layer 1: 数据库层 — operation_logs 表增强

#### 1.1 增加字段（ALTER TABLE 迁移）

```sql
ALTER TABLE operation_logs ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0;
-- 用于多租户过滤和关联用户信息
```

#### 1.2 扩展 action 类型枚举

| action 值 | 来源 | target_type | target_id | detail 内容示例 |
| --- | --- | --- | --- | --- |
| **TASK_PUSH** | tasks.py execute_task_push | task | 任务ID | `{taskName, tid, tname, deviceCount, devices:[{mac, custom_data摘要, status}]}` |
| **TASK_CREATE** | tasks.py POST /tasks | task | 任务ID | `{name, tid, tname, deviceCount}` |
| **DEVICE_ONLINE** | mqtt_service _persist_to_db (online事件) | device | MAC | `{name, voltage, rssi}` |
| **DEVICE_OFFLINE** | mqtt_service _persist_to_db (offline事件) | device | MAC | `{name, lastSeenAt, durationOnline}` |
| **DEVICE_LOW_BATTERY** | multi_user_mqtt_manager (battery_reply) | device | MAC | `{voltage, percent}` |
| **LOGIN** | 已有 | auth | - | 用户名+IP |
| **LOGIN_FAILED** | 已有 | auth | - | 用户名+IP |
| **CREATE_USER** | 已有 | user | 用户ID | 创建的用户名/角色 |
| **UPDATE_CONFIG** | 已有 | config | key | 配置变更 |
| batch_update_template | 已有(保留兼容) | template | templateId | 旧格式保持不变 |


#### 1.3 get_logs 函数增强

- 支持 `action` 精确匹配（当前是 LIKE 模糊匹配）
- 支持 `user_id` 过滤
- 支持 `mac` 过滤（针对设备相关操作）
- 支持 `start_time/end_time` 时间范围
- 联合查询 device_events（可选，用于展示在线离线）

### Layer 2: 后端写入点 — 在关键路径补写日志

#### 2.1 任务推送时（最关键！）

**文件**: `backend/api/tasks.py` 的 `execute_task_push` 函数（第371行附近）

在推送完成后、返回前，写入一条 `TASK_PUSH` 日志：

```python
# 在 execute_task_push 末尾（约第516行后）
from services.db_service import add_log
from services.db_service_extended import get_user_by_id

user_info = await get_user_by_id(user_id)
username = user_info.get("username", f"user_{user_id}") if user_info else f"user_{user_id}"

await add_log(
    username=username,
    action="TASK_PUSH",
    target_type="task",
    target_id=str(task_id),
    detail=json.dumps({
        "task_name": task["name"],
        "tid": tid,
        "tname": tname,
        "device_count": len(push_devices),
        "success_count": sent_ok,
        "failed_count": sent_fail,
        "devices": [
            {
                "mac": d["mac"],
                "custom_data": d.get("custom_data"),  # 记录每台设备推送的具体数据
                "status": r.get("success") and "sent" or "failed",
            }
            for d, r in zip(push_devices, results)
        ],
    }, ensure_ascii=False),
    result="success" if sent_fail == 0 else ("partial_failure" if sent_ok > 0 else "failure"),
    user_id=user_id,
)
```

**关键决策**: custom_data 是否完整记录？

- **推荐**: 记录摘要版（去掉冗余字段，只保留有值的业务字段）。因为 custom_data 可能很大（含模板所有字段），完整存储会导致 detail 字段膨胀。
- **实现方式**: 在写入日志时遍历 default_data 和 custom_data 的合并结果，过滤掉空值/null值，只保留实际有内容的字段。

#### 2.2 设备状态变化时

**文件**:

- `backend/services/mqtt_service.py` 的 `_persist_to_db` 方法
- `backend/services/multi_user_mqtt_manager.py` 的 `_persist_to_db` 方法

在 `online` / `offline` / `battery_reply` 事件处理中，同步写入 operation_logs：

```python
if event_type == "online":
    # 写入 DEVICE_ONLINE 日志
    await add_log(
        username="system",
        action="DEVICE_ONLINE",
        target_type="device", target_id=mac,
        detail=json.dumps({"voltage": voltage_val}, ensure_ascii=False),
        user_id=self.user_id,
    )
elif event_type == "offline":
    await add_log(
        username="system",
        action="DEVICE_OFFLINE",
        target_type="device", target_id=mac,
        detail=json.dumps({"last_seen_at": last_seen}, ensure_ascii=False),
        user_id=self.user_id,
    )
```

**注意**: 设备事件来自 MQTT，不是用户主动操作，所以 username 设为 `"system"`。

#### 2.3 其他已有日志补 user_id

- `auth_service.py` 登录日志 → 补充 user_id
- `settings.py` 配置修改日志 → 补充 user_id
- `users.py` 创建用户日志 → 补充 user_id

### Layer 3: API 层 — 统一操作记录接口

#### 3.1 增强 /api/v1/update-history 或新建 /api/v1/operation-logs

**推荐**: 新建 `/api/v1/operation-logs` 作为统一接口，保留旧的 `/api/v1/update-history` 不动（向后兼容）。

**接口定义**:

```python
@router.get("/api/v1/operation-logs")
async def get_operation_logs(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    action: str = "",          # 筛选: TASK_PUSH, DEVICE_ONLINE, ...
    mac: str = "",             # 筛选: 设备MAC
    start_time: str = "",      # 开始时间
    end_time: str = "",        # 结束时间
):
```

**返回结构**:

```
{
    "code": 20000,
    "data": {
        "total": 150,
        "items": [
            {
                "id": 200,
                "username": "admin",
                "user_id": 1,
                "action": "TASK_PUSH",
                "action_label": "数据推送",
                "target_type": "task",
                "target_id": "42",
                "detail": { ... },
                "result": "success",
                "created_at": "2026-05-04 18:30:00"
            }
        ]
    }
}
```

#### 3.2 action 类型中文映射

后端或前端维护映射表：

```python
ACTION_LABELS = {
    "TASK_PUSH": "数据推送",
    "TASK_CREATE": "创建任务",
    "DEVICE_ONLINE": "设备上线",
    "DEVICE_OFFLINE": "设备离线",
    "DEVICE_LOW_BATTERY": "低电量告警",
    "LOGIN": "用户登录",
    "LOGIN_FAILED": "登录失败",
    "CREATE_USER": "创建用户",
    "UPDATE_CONFIG": "修改配置",
}
```

### Layer 4: 前端 — 操作记录页面重新设计

#### 页面规划（2屏）

**Screen 1: 操作记录主页面** (`OperationLogPage.vue`)

**Block 1: 页面头部**

- 标题"操作记录"+ 副标题说明
- 导出按钮（可选，后续迭代）

**Block 2: 筛选工具栏**

- 左侧：时间范围选择器（今天/最近7天/最近30天/自定义）
- 右侧：操作类型下拉筛选（全部/数据推送/设备上线/设备离线/登录...）
- 可选：设备 MAC 输入框搜索

**Block 3: 记录列表（表格模式，替代原来的时间线）**

- 列：时间 | 操作类型(彩色tag) | 操作者 | 目标对象 | 结果 | 详情(展开)
- 行点击展开详情面板：
- **TASK_PUSH 展开内容**:

```
任务: 价格更新任务 #42
模板: 商品价格模板 (price_tpl_001)
设备列表:
├─ D4:3D:39:66:B8:4C  [成功]  商品名: 可乐  价格: ¥3.50
├─ D4:3D:39:83:D5:64  [成功]  商品名: 雪碧  价格: ¥3.00
└─ D4:3D:39:66:A0:92  [失败]  错误: 超时无响应
```

- **DEVICE_ONLINE/OFFLINE 展开内容**:

```
设备: D4:3D:39:66:B8:4C
电量: 4.11V (100%)
上次离线时长: 2小时15分
```

**Block 4: 分页**

**Screen 2: 更新历史页（保留但降级）**

现有的 `HistoryPage.vue` 保留不变，侧边栏菜单改为指向新的操作记录页。或者将 HistoryPage 重构为操作记录页的一个 Tab 视图。

### 数据流总览

```
[用户点击"推送数据"]
    ↓
[tasks.py:execute_task_push]
    ↓ 并发推送 MQTT
    ↓ 同时写入 operation_logs(action=TASK_PUSH, detail={devices:[{mac, custom_data}]})
    ↓
[设备收到 MQTT]
    ↓ 回复 display_reply
    [multi_user_mqtt_manager:_persist_to_db]
    ↓ 更新 task_devices.update_status
    ↓
[前端轮询 progress / WebSocket 实时更新]

[设备上下线]
    ↓ MQTT 消息到达
    [mqtt_service:_persist_to_db] 或 [multi_user_mqtt_manager:_persist_to_db]
    ↓ 更新 devices.is_online
    ↓ 同时写入 operation_logs(action=DEVICE_ONLINE/OFFLINE)

[用户访问"操作记录"页]
    ↓ GET /api/v1/operation-logs?action=&start_time=&end_time=
    [db_service:get_logs 增强]
    ↓ SELECT FROM operation_logs WHERE ... ORDER BY created_at DESC
    ↓
[前端 OperationLogPage 渲染表格 + 展开]
```

## 关键实现注意事项

### 性能考虑

- **custom_data 存储策略**: 只存非空字段的摘要，不存完整 default_data（避免单条日志过大）。建议限制 detail JSON 大小不超过 4KB。
- **索引优化**: 确保 `idx_logs_action`、`idx_logs_time`、新增的 `idx_logs_user_id` 都存在。
- **设备事件频率**: online/offline 事件可能很频繁（每次重连都会触发），考虑：
- 方案A: 全部记录（简单，但数据量大）
- 方案B: 只记录状态**变化**（连续 online 忽略，offline→online 才记）— 推荐
- 方案C: 不写入 operation_logs，只在查询时从 device_events 联合读取
- **推荐方案B**: 用内存缓存每个设备最新状态，只有状态切换时才写日志

### 向后兼容

- 旧的 `batch_update_template` 类型的日志仍然可以正常显示
- `user_id` 列默认值为 0，旧数据的 user_id=0 显示为"未知用户"
- 旧 HistoryPage API 保持不变

### 多租户

- operation_logs 增加 user_id 后，API 查询时根据当前用户角色过滤：
- admin: 可以看所有 user_id 的日志
- user/operator: 只能看自己和下属的日志

## 设计概述

操作记录页面需要从原有的简单时间线升级为一个专业的**审计日志仪表板**。采用表格+展开详情的模式，配合丰富的筛选能力，让客户能够快速定位到任何一次操作的具体内容。

### 设计风格

采用**企业级审计日志**风格：清晰的信息层级、紧凑的数据密度、高效的筛选交互。配色上延续项目紫色主题，同时用不同颜色区分操作类型（绿色=成功/上线，红色=失败/离线，蓝色=推送，灰色=系统）。

### 应用类型

Web（桌面端管理后台）

### 框架组件

Vue 3 + Element Plus（el-table、el-tag、el-select、el-date-picker、el-pagination）