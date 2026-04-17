---
name: display-reply-status-update
overview: 改造更新状态机制：后端在收到 display_reply(result=200) 时自动将 task_devices 标记为 success，前端 WS 实时监听并局部刷新状态。涉及 mqtt_service.py、db_service.py、useBackendWs.ts、TemplateUpdateView.vue 四个文件。
design:
  architecture:
    framework: vue
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 32px
      weight: 600
    subheading:
      size: 18px
      weight: 500
    body:
      size: 16px
      weight: 400
todos:
  - id: add-db-func
    content: db_service.py 新增 update_device_status_by_mac 函数，按MAC批量更新sent/pending设备为success/failed
    status: pending
  - id: modify-mqtt-callback
    content: mqtt_service.py display_reply回调中解析result，调用新函数写入DB
    status: pending
    dependencies:
      - add-db-func
  - id: fix-execute-task
    content: tasks.py executeTask移除batch_update_device_statuses调用，改为仅标记sent状态
    status: pending
  - id: ws-event-listener
    content: TemplateUpdateView注册onWsMessage('display_reply')监听，就地更新taskDetail.devices实现实时刷新
    status: pending
  - id: verify-and-test
    content: lint验证零错误，确认数据流完整性
    status: pending
    dependencies:
      - add-db-func
      - modify-mqtt-callback
      - fix-execute-task
      - ws-event-listener
---

## 产品概述

将设备"在线状态"与"更新状态"彻底分离为两个独立字段，并实现基于 MQTT `display_reply` 回执的真实更新状态流转。

## 核心功能需求

### 1. 在线状态与更新状态分离显示（UI层）

- **在线状态**：绿色圆点=在线，灰色圆点=离线，数据来源为 `deviceStore.is_online`
- **更新状态**：el-tag 标签展示（待发送/发送中/成功/失败），数据来源为 `task_devices.update_status`
- 两个状态在表格同一列中并排展示，视觉上清晰区分
- **现状评估**: 前端 `DeviceDataTable.vue` 已基本完成此分离，仅需微调确认

### 2. 更新状态由 display_reply 回执驱动（核心改造）

- 推送执行后，设备状态保持为 `sent`（发送中），不立即标记 success/failed
- 当 MQTT 收到 `display_reply` 消息时：
- `result === 200` → 更新状态变为 `success`（更新完成）
- `result !== 200` → 更新状态变为 `failed`（更新失败）
- 后端：MQTT 回调中写入 DB（`task_devices.update_status`）
- 前端：WS 实时推送 + 本地 reactive 更新，表格即时刷新

### 3. 数据流闭环

```
点击推送 → 后端标记 sent → MQTT发布 → 设备执行
→ 设备回复 display_reply(result=200) → MQTT接收
→ _persist_to_db 写入 task_devices 表(success/failed)
→ WS 广播给前端 → useBackendWs 事件总线通知
→ TemplateUpdateView 就地修改 taskDetail.devices → 表格自动刷新
```

### 4. 边界情况

- 设备离线时推送按钮禁用（已有逻辑，不变）
- 同一 MAC 可能存在于多个任务中，需批量更新所有匹配的 sent 状态记录
- result 为 0 也视为成功（兼容部分固件）

## 技术栈

- **后端**: Python 3.11 + FastAPI + aiosqlite + paho-mqtt
- **前端**: Vue 3 Composition API + TypeScript + Element Plus + Pinia
- **实时通信**: MQTT Broker ←→ 后端桥接 ←→ WebSocket ←→ 前端

## 实现方案

### 策略概述

采用"推送后等待回执"模式替代当前的"推送即判定结果"模式。核心改动集中在后端 MQTT 回调和前端 WS 事件监听两处。

### 关键技术决策

**决策1: executeTask 不再立即标记 success/failed**

- 当前 `tasks.py:241` 调用 `batch_update_device_statuses()` 立即标记结果，这是错误的
- 因为 `wifi_proxy.apply_template()` 只是 MQTT publish 的返回值，不是设备的真正回执
- 改造后：executeTask 仅将设备标记为 `sent`，返回推送已发出的信息
- 最终状态由后续到达的 `display_reply` 决定

**决策2: 新增按 MAC 查找并更新的 DB 函数**

- `display_reply` 消息只包含 mac 和 result，不知道属于哪个任务
- 需要新函数 `update_device_status_by_mac(mac, status, error_msg)`
- SQL: `UPDATE task_devices SET ... WHERE mac=? AND update_status='sent'`
- 同时级联更新父任务的 progress 统计和 status 字段

**决策3: 前端复用已有事件总线机制**

- `useBackendWs.ts:32-43` 已有完整的 `_listeners/onWsMessage/offWsMessage` 事件总线
- `handleMessage:96` 行已在分发消息给监听者
- `TemplateUpdateView` 只需注册一个 `onWsMessage('display_reply', callback)` 监听器
- callback 内就地修改 `taskDetail.value.devices[]`，computed 自动派生表格数据

## 架构设计

### 改造前后对比

```
改造前 (错误流程):
executeTask → mark "sent" → MQTT publish → [apply_template 返回值当结果]
            → batch_update_device_statuses(success/failed) ← 这里判断不准!
→ (later) display_reply 到达 → 只写 last_seen_at ← 浪费了回执信息

改造后 (正确流程):
executeTask → mark "sent" → MQTT publish → return (设备全部处于 sent 状态)
→ (稍后) display_reply 到达(result=200) 
  → _persist_to_db 调用 update_device_status_by_mac → task_DEVICES 标记 success
  → ws_manager.broadcast → useBackendWs 事件分发
  → TemplateUpdateView onWsMessage callback → 就地改 taskDetail → 表格实时刷新
```

## 目录结构

```
项目根目录/
├── backend/services/db_service.py          # [MODIFY] 新增 update_device_status_by_mac 函数
├── backend/services/mqtt_service.py        # [MODIFY] display_reply 时调用新函数更新任务设备状态
├── backend/api/tasks.py                    # [MODIFY] executeTask 移除 batch_update_device_statuses 调用
└── frontend/src/
    ├── composables/useBackendWs.ts        # [MODIFY] display_reply case 中触发事件总线(已有逻辑，微调确认)
    └── views/template/TemplateUpdateView.vue # [MODIFY] 注册 display_reply 监听器，本地 reactive 更新
```

## 实施细节

### 1. db_service.py — 新增函数

```python
async def update_device_status_by_mac(mac: str, status: str, error_msg: str = "") -> dict:
    """
    根据 MAC 地址更新所有匹配任务中的设备状态
    用于 display_reply 回调：收到设备回复后，将该 mac 在所有任务中的 sent 状态更新为 success/failed
    Returns: {updated_count: int, affected_tasks: list[int]}
    """
    # SQL: UPDATE task_devices SET update_status=?, error_msg=?, finished_at=...
    #      WHERE mac=? AND update_status IN ('sent','pending')
    # 级联: 对每个受影响的任务重新统计 progress 并更新 tasks.status
```

关键点：

- 匹配条件：`mac=? AND update_status IN ('sent', 'pending')` （防止重复处理已完成的记录）
- 批量更新后遍历 `affected_tasks` 重新统计每个任务的 pending/sent/success/failed 数量
- 如果某任务所有设备都已完成（success+failed == total），则标记任务 status 为 `'completed'`

### 2. mqtt_service.py — 修改 _persist_to_db

```python
# 在 elif event_type in ("led_reply", "reboot_reply", "display_reply"): 分支内
if event_type == "display_reply":
    result_code = data.get("result") or data.get("code")
    if result_code is not None:
        ok = result_code in (200, 0, "200", "0", "success")
        new_status = "success" if ok else "failed"
        err = "" if ok else f"result={result_code}"
        try:
            from services.db_service import update_device_status_by_mac
            await update_device_status_by_mac(mac, new_status, err)
        except Exception as e:
            logger.error(f"[DB] display_reply 状态更新失败 {mac}: {e}")
```

### 3. tasks.py — 修改 executeTask

移除第 241 行的 `summary = await batch_update_device_statuses(task_id, results)` 调用。
改为仅更新任务主表状态为 `"sent"`（表示已发出推送）：

```python
# 推送完成后不再逐个标记 success/failed
# 所有设备保持 sent 状态，等待 display_reply 回调来最终确认
from services.db_service import update_task as _ut
await _ut(task_id, status="sent", total_devices=len(push_devices))
```

返回值的 data 结构调整为：

```python
"data": {
    "total": len(push_devices),
    "sent": len(push_devices),  # 全部标记为 sent
    "message": "推送已发出，等待设备回复",
    "results": results,
}
```

### 4. useBackendWs.ts — 微调 display_reply 分支

当前代码在第 96 行已经调用 `_listeners.get(type).forEach(h => h(data))` 进行事件分发，所以 `display_reply` 事件会自动通知外部监听者。无需大改动，只需确保 data 中包含完整信息（已有）。

可选优化：在 display_reply case 中增加日志便于调试。

### 5. TemplateUpdateView.vue — 注册 display_reply 监听

新增 import 和 setup 逻辑：

```typescript
import { onWsMessage, offWsMessage } from '@/composables/useBackendWs'

// display_reply 回调处理函数
function handleDisplayReply(data: any) {
  const mac = data?.mac
  const result = data?.result ?? data?.code
  if (!mac || !taskDetail.value) return
  
  // 在 taskDetail.devices 中找到对应设备，就地修改
  const dev = taskDetail.value.devices.find((d: any) => d.mac === mac)
  if (!dev || dev.update_status === 'success') return // 已成功的跳过
  
  const ok = result === 200 || result === 0 || result === 'success'
  dev.update_status = ok ? 'success' : 'failed'
  dev.error_msg = ok ? '' : `result=${result}`
  
  console.log(`[Task] 设备 ${mac} 更新${ok ? '成功' : '失败'} (result=${result})`)
}

// 注册/注销监听器
onMounted(() => {
  // ...现有逻辑...
  onWsMessage('display_reply', handleDisplayReply)
})

onUnmounted(() => {
  // ...现有逻辑...
  offWsMessage('display_reply', handleDisplayReply)
})
```

由于 `deviceTableData` 是 computed 属性，从 `taskDetail.value.devices` 派生，就地修改 devices 数组中的对象属性会自动触发 computed 重算，表格 UI 即时刷新。

## 注意事项

1. **数据库迁移**: 上次修复已补上 `updated_at` 列到建表语句。如果用户尚未删库重建，需手动 ALTER TABLE 或删除 `backend/data/wifi_esl.db`
2. **向后兼容**: 对于已经在执行中的旧任务（status 已经是 completed），display_reply 不再产生影响因为 WHERE 条件排除了非 sent 记录
3. **竞态条件**: 如果 display_reply 在 executeTask 的 "mark sent" 之前到达，该记录仍为 pending 状态，也会被匹配更新（SQL 用 IN ('sent','pending') 兼容此场景）
4. **性能**: `update_device_status_by_mac` 使用单次批量 UPDATE + 按需级联更新父任务，避免 N+1 问题
5. **错误处理**: MQTT 回调中的 DB 操作失败不应影响主流程，用 try/except 包裹并打日志
6. **前端响应式**: Vue 3 的 reactive 对象深层次修改能被追踪，但需确保不替换整个 devices 数组引用（用 find+就地修改而非 filter+map）

本次改造主要涉及后端逻辑变更，前端 UI 无重大调整。DeviceDataTable.vue 的状态列已实现在线圆点 + 更新标签的双元素布局，无需修改。唯一需要关注的是确保前端能通过 WS 事件总线实时接收 display_reply 并更新本地状态，让用户看到即时的状态变化反馈。

页面结构保持不变，仅在 TemplateUpdateView.vue 内部增加 WS 事件订阅逻辑。

## Agent Extensions

- **code-explorer**
- Purpose: 用于探索代码库中多个文件的相关代码段，确认修改目标和依赖关系
- Expected outcome: 已完成全部分析，确认了 5 个待修改文件的精确行号和上下文