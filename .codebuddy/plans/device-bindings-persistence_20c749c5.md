---
name: device-bindings-persistence
overview: 新增 template_device_bindings 表持久化模板-设备关联，后端提供保存/查询/移除API；前端"删除"改"移除"（仅从列表移除不删设备），设备选择后持久化到DB实现多端同步。
todos:
  - id: add-bindings-table-and-crud
    content: 在 db_service.py 新增 template_device_bindings 表(含init_db)、save_template_bindings/get_template_bound_macs/remove_template_binding 函数
    status: completed
  - id: add-binding-api-routes
    content: "在 devices.py 新增3个API端点: POST/GET/DELETE /api/v1/template-devices"
    status: completed
    dependencies:
      - add-bindings-table-and-crud
  - id: add-frontend-api-methods
    content: 在 frontend/src/api/device.ts 新增 saveTemplateBindings/getTemplateBoundMacs/removeTemplateBinding 三个方法
    status: completed
    dependencies:
      - add-binding-api-routes
  - id: refactor-remove-to-unbind
    content: "改造前端: DeviceDataTable\"删除\"→\"移除\"+TemplateUpdateView删除逻辑改为移除绑定(调removeTemplateBinding+本地移除)"
    status: completed
    dependencies:
      - add-frontend-api-methods
  - id: wire-persistence-on-select-load
    content: "改造前端: handleDeviceConfirm调saveTemplateBindings持久化+onMounted拉取getTemplateBoundMacs恢复列表实现多端同步"
    status: completed
    dependencies:
      - add-frontend-api-methods
---

## 产品概述

数据更新页面的设备列表目前仅保存在浏览器内存/localStorage中，无法跨端同步。需要将用户选择的模板-设备关联关系持久化到数据库，实现多终端同步；同时修正操作列中"删除"按钮的语义，改为从当前列表移除而非物理删除设备。

## 核心功能

### 需求1：设备关联数据持久化与多端同步

- 新增 `template_device_bindings` 数据库表，存储「哪个模板绑定了哪些设备」的关联关系
- 后端提供保存/查询/移除绑定的 REST API 接口
- 前端在确认选择设备后调用保存接口写入数据库
- 前端页面加载时拉取该模板已绑定设备列表（替代 localStorage 草稿）
- 手机端和电脑端访问同一后端服务，看到的已选设备一致

### 需求2："删除"改为"移除"

- 操作列中的"删除"按钮文字改为"移除"
- 点击"移除"后弹出确认框，确认后：
- 调用后端接口**移除绑定关系**（DELETE template_device_binding）
- 从前端当前列表/选中列表中移除
- **不调用** `deviceApi.deleteDevice()`，不删除设备本身
- 不影响设备在其他地方的显示

## Tech Stack

- **后端**: Python + FastAPI + aiosqlite (SQLite)
- **前端**: Vue 3 + TypeScript + Element Plus + Pinia
- **数据库**: SQLite (`backend/data/wifi_esl.db`)

## 实现方案

### 整体架构：新增模板-设备绑定表

核心思路是新增一张中间表 `template_device_bindings`，记录「某个模板下用户选择了哪些设备」。这样：

- 设备本体仍在 WIFI 系统或本地 devices 表中（不变）
- 绑定关系独立存储，支持 CRUD
- 多端共享同一份数据源

```
templates ──< template_device_bindings >── devices
   (tid)          tid + mac               (mac)
```

### 数据库设计

新表结构（追加到 `db_service.py` 的 `init_db()` 中）：

```sql
CREATE TABLE IF NOT EXISTS template_device_bindings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tid         TEXT    NOT NULL,          -- 模板ID
    mac         TEXT    NOT NULL,          -- 设备MAC地址
    created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
    updated_at  TEXT    DEFAULT (datetime('now', 'localtime')),
    UNIQUE(tid, mac)                          -- 同一模板下同一设备唯一
);

CREATE INDEX IF NOT EXISTS idx_bind_tid ON template_device_bindings(tid);
CREATE INDEX IF NOT EXISTS idx_bind_mac ON template_device_bindings(mac);
```

### 后端API设计

在 `backend/api/devices.py` 或新建 `template_devices.py` 中添加3个接口：

| 方法 | 路径 | 功能 |
| --- | --- | --- |
| POST | `/api/v1/template-devices` | 保存/批量保存绑定 `{tid, macs:[]}` |
| GET | `/api/v1/template-devices?tid=xxx` | 查询某模板的已绑定设备MAC列表 |
| DELETE | `/api/v1/template-devices/{tid}/{mac}` | 移除单个绑定 |


### db_service 新增函数

```python
# 保存/批量保存绑定（UPSERT）
async def save_template_bindings(tid: str, macs: list[str]) -> int

# 查询模板绑定的MAC列表
async def get_template_bound_macs(tid: str) -> list[str]

# 删除单条绑定
async def remove_template_binding(tid: str, mac: str) -> bool
```

### 前端改造

**DeviceDataTable.vue**:

- 操作列"删除" → "移除"，emit 名保持兼容或重命名为 `removeBinding`
- 样式颜色可微调为中性色（非红色），强调"移除"语义

**TemplateUpdateView.vue**:

- `handleDeviceConfirm()`: 确认选择后调 `saveTemplateBindings()` API 持久化
- `handleDeleteTableDevice()` → 重命名为 `handleRemoveTableDevice()`:
- 不再调用 `deviceApi.deleteDevice()`
- 改为调用 `removeTemplateBinding()` API 移除绑定
- 本地从 selectedMacs / checkedMacs 中过滤掉
- 确认提示文案改为"确定要将此设备从更新列表中移除吗？"
- `onMounted()`: 增加拉取已绑定设备的逻辑，优先使用 DB 数据恢复 selectedMacs
- 如果DB有数据则用DB数据，否则降级到 localStorage 草稿

**frontend/src/api/device.ts**:

- 新增三个 API 方法: `saveTemplateBindings`, `getTemplateBoundMacs`, `removeTemplateBinding`

### 性能与可靠性考量

- 批量保存使用事务确保原子性
- 绑定查询走索引（tid + mac 联合索引）
- 前端先本地 UI 更新（乐观更新），后端异步持久化失败时回滚提示
- 页面加载时并行请求：模板列表 + 已绑定设备列表

## 架构设计

```
前端 TemplateUpdateView.vue
  ├─ onMounted: 并行 fetchTemplates() + getTemplateBoundMacs(tid)
  ├─ handleDeviceConfirm(macs): → POST /api/v1/template-devices {tid, macs}
  ├─ handleRemoveTableDevice(dev): → DELETE /api/v1/template-devices/{tid}/{mac} + 本地移除
  └─ DeviceDataTable (操作列: 推送 | 移除)

后端 FastAPI
  ├─ POST   /api/v1/template-devices      → db_service.save_template_bindings()
  ├─ GET    /api/v1/template-devices?tid=x → db_service.get_template_bound_macs()
  └─ DELETE /api/v1/template-devices/{t}/{m}→ db_service.remove_template_binding()

SQLite
  ├─ templates (已有)
  ├─ devices (已有)
  └─ template_device_bindings (新增)
```

## 目录结构

```
project-root/
├── backend/
│   ├── services/
│   │   └── db_service.py              # [MODIFY] 新增 template_device_bindings 表定义 + 4个CRUD函数 + init_db建表
│   ├── api/
│   │   └── devices.py                 # [MODIFY] 新增3个模板-设备绑定API路由(POST/GET/DELETE)
│   └── main.py                        # [无需修改] 复用已有devices_router
└── frontend/
├── src/
│   ├── api/
│   │   └── device.ts              # [MODIFY] 新增3个API方法(save/get/remove bindings)
│   ├── views/template/
│   │   ├── TemplateUpdateView.vue # [MODIFY] 改造设备加载/保存/移除逻辑; 删除→移除
│   │   └── DeviceDataTable.vue    # [MODIFY] 操作列文字"删除"→"移除"; emit rename
│   └── stores/
│       └── device.ts              # [无需修改]