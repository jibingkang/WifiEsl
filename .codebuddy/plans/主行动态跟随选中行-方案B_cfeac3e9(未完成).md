---
name: 主行动态跟随选中行-方案B
overview: 修改 DeviceDataTable.vue，使主行字段显示/编辑跟随当前选中的子表行（radio选择），实现"所见即所得"。切换radio时自动flush缓存到后端并加载新行数据。
design:
  styleKeywords:
    - Functional Clarity
    - Minimal Indicator
    - Purple Accent
    - Smooth Transition
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
  - id: modify-geteffective
    content: 重构 getEffective() 函数：新增 getActiveRow() 辅助函数，将硬编码 rows[0] 改为按 selectedRowIds[mac] 动态取行
    status: pending
  - id: modify-edit-write-target
    content: 修改 onBlur() 和 clearField() 的写入目标：从固定 firstRow.id 改为当前选中行的 row.id
    status: pending
    dependencies:
      - modify-geteffective
  - id: modify-selectrow-flush
    content: 增强 selectRow() 函数：切换行前调用 flushMainEditsToRow() 将旧行编辑持久化到后端
    status: pending
    dependencies:
      - modify-edit-write-target
  - id: add-ui-indicators
    content: 添加UI行号指示器：桌面端主行radio旁显示当前选中行号标签(#N)，移动端卡片头同步增加标记
    status: pending
    dependencies:
      - modify-selectrow-flush
  - id: verify-and-test
    content: 验证全流程：单行/多行设备、行切换时编辑不丢失、推送数据正确性、删除子行后回退正常
    status: pending
    dependencies:
      - add-ui-indicators
---

## 产品概述

解决用户在设备数据表格中"不知道主行显示的是哪行数据"的困惑。当前主行始终固定显示子表第1行的数据，但radio可以选择不同行进行推送，两者脱节导致混淆。

## 核心功能需求

- **主行动态跟随选中行**：切换radio选择不同子行时，主行字段自动切换为对应行数据显示和编辑
- **编辑联动**：在主行编辑的字段值，自动写入当前选中的子行（而非固定写入第1行）
- **行切换时数据持久化**：从第N行切到第M行时，将第N行的未保存编辑flush到后端，再加载第M行数据
- **视觉反馈**：桌面端主行radio旁显示当前选中行编号（如"#1"），让用户明确知道正在操作哪行

## 不涉及的改动

- 子行（sub-row）的独立编辑逻辑不变（已有 `rowEdits` + `getRowEffective` 独立体系）
- 移动端卡片布局同步改造
- 推送逻辑不变（推送仍基于 `selectedRowIds` 决定用哪行数据）

## 技术栈

- Vue 3 Composition API + TypeScript
- Element Plus 组件库
- 单文件修改：`frontend/src/views/template/DeviceDataTable.vue`

## 实现方案

### 核心策略：将主行从"固定展示第1行"变为"当前选中行的编辑镜像"

**关键设计决策**：

1. **`getEffective(mac, key)` 改为动态读取** — 根据 `selectedRowIds[mac]` 找到当前选中行，读取该行 `custom_data`，不再硬编码 `rows[0]`
2. **`onBlur()` / `clearField()` 写入目标动态化** — 将 `taskApi.updateDeviceRow()` 的目标从 `firstRow.id` 改为当前选中行的 `row.id`
3. **`selectRow()` 增加flush逻辑** — 切换行前，将当前 `customOverrides[mac]` 的待保存内容通过API写入旧选中行，避免编辑丢失
4. **`customOverrides` 结构保持不变** — 仍然按 `mac` 键存储，因为它代表"主行编辑区的临时缓存"，始终对应当前激活行

### 数据流变化

```
切换前:  Radio选#1 → 主行显示rows[0] → 编辑→写rows[0]
切换后:  Radio选#N → 主行显示rows[N-1] → 编辑→写rows[N-1]
         切换到#M → 先flush mac的overrides到rows[N-1] → 更新selectedRowIds → 主行刷新为rows[M-1]
```

### 涉及修改的5个函数

| 函数 | 当前行为 | 修改后行为 |
| --- | --- | --- |
| `getEffective(mac,key)` | 固定读 `rows[0]` | 按 `selectedRowIds[mac]` 取对应行 |
| `onBlur(mac,key,event)` | 写入 `firstRow.id` | 写入选中行的 `row.id` |
| `clearField(mac,key)` | 清除 `firstRow.id` 对应字段 | 清除选中行对应字段 |
| `selectRow(mac,rowId)` | 只更新 `selectedRowIds` | 先flush旧行编辑，再更新 |
| `hasAnyValue(mac)` / `isOverridden(mac,key)` | 基于检查 `customOverrides[mac]` | 保持不变（仍表示主行是否有编辑） |


### 实施细节

#### 1. 新增辅助函数 `getActiveRow(mac)`

```typescript
function getActiveRow(mac: string): { row: any; index: number } | null {
  const dev = props.devices.find(d => d.mac === mac)
  if (!dev?.rows?.length) return null
  const activeRowId = selectedRowIds.value[mac]
  const idx = dev.rows.findIndex((r: any) => r.id === activeRowId)
  return idx >= 0 ? { row: dev.rows[idx], index: idx } : { row: dev.rows[0], index: 0 }
}
```

#### 2. 修改 `getEffective()` — 第501行

- 第509行：`const firstRow = dev.rows[0]` → 改为调用 `getActiveRow(mac)` 获取当前行
- 其余优先级链路不变

#### 3. 修改 `onBlur()` — 第574行

- 第602行：`const firstRow = dev.rows[0]` → 用 `getActiveRow(mac).row` 替代
- 第610行：`taskApi.updateDeviceRow(firstRow.id, ...)` → 用 `activeRow.id`

#### 4. 修改 `clearField()` — 第618行

- 同上模式，将 `firstRow` 替换为活跃行

#### 5. 修改 `selectRow()` — 第433行，增加flush逻辑

```typescript
async function selectRow(mac: string, rowId: number) {
  // 如果该设备有未保存的主行编辑，先flush到旧选中行
  if (props.customOverrides[mac] && Object.keys(props.customOverrides[mac]).length > 0) {
    const oldRowId = selectedRowIds.value[mac]
    if (oldRowId && oldRowId !== rowId) {
      await flushMainEditsToRow(mac, oldRowId)
    }
  }
  selectedRowIds.value = { ...selectedRowIds.value, [mac]: rowId }
  _syncToParent()
}
```

#### 6. 新增 `flushMainEditsToRow(mac, rowId)` 函数

- 将 `customOverrides[mac]` 的所有字段合并写入指定 `rowId` 的 `custom_data`
- 调用 `taskApi.updateDeviceRow(rowId, mergedData)`
- 成功后清除 `customOverrides[mac]`（通过 emit 通知父组件清空）

#### 7. UI微调 — 桌面端主行radio区域增加行号提示

- 在第53~61行的radio按钮旁边，加一个小标签 `#{{ getActiveRowIndex(dev.mac) + 1 }}` 显示当前选中行号
- 移动端卡片头部也加类似标记

### 性能与边界考虑

- **flush防抖**：`selectRow` 中的flush是await串行的，确保数据一致性。如果用户快速连续切换radio，前一次flush完成后才执行切换
- **无子行设备不受影响**：`getActiveRow` 对无rows的设备返回null，走默认值分支
- **单行设备不受影响**：只有1行时选中行就是第1行，行为与之前完全一致

## 设计方案：方案B — 主行动态跟随选中行

### 设计理念

将主行重新定位为"当前选中行的快捷编辑区"，而非固定的第1行展示区。Radio不仅是推送选择器，同时也是"主行显示哪行数据"的切换器。

### 页面结构变更

**桌面端主行变更点（仅3处）**：

1. **Radio区域（col-check td）**：在现有radio按钮右侧增加一个紧凑的行号标签 `#1`/`#2`/`#3`，使用小字号、紫色系、圆角标签样式。当用户切换子行radio时，此标签同步更新。
2. **字段列（col-field td）**：无需视觉改动，input的value已由 `getEffective()` 动态返回正确行的数据。
3. **行高亮反馈**：当某设备有多行数据时，主行增加微弱的左侧彩色边框指示（如淡紫色 3px 左边框），暗示"这是当前激活行的编辑区"。

**移动端卡片变更点（2处）**：

1. **卡片头部**：在设备名/MAC旁增加当前行号标签 `#编辑行 N`。
2. **字段输入区**：无需改动，value动态绑定。

### 交互流程

1. 用户看到设备有3行数据 → 主行radio旁显示 "#1"
2. 用户点击子行 #3 的radio → 主行立即切换为 #3 的数据，标签变为 "#3"
3. 如果主行 #1 有未保存的编辑 → 自动后台保存到第1行后完成切换
4. 用户在主行编辑字段 → blur后写入第3行

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 验证 `customOverrides` 在父组件 TemplateUpdateView 中的完整使用链路，确认改为动态行写入后不会影响推送/导出/保存等下游功能
- Expected outcome: 确认所有消费 `customOverrides[mac]` 的场景兼容新行为