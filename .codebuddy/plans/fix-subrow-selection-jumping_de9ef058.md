---
name: fix-subrow-selection-jumping
overview: 修复轮询期间子行选择自动跳回的问题：移除 `_refreshTaskFromServer` 中过于激进的 condition 2，只在状态转换时同步 `selected_row_id`。
todos:
  - id: fix-needs-main-sync
    content: 移除 `_refreshTaskFromServer` 中 needsMainSync 的 condition 2（无条件 selected_row_id 对比），只保留 condition 1 的 sent→success/failed 状态转换检测
    status: completed
---

## 用户需求

修复在数据更新页面选择其他子行后，选择框自动跳回当前显示子行的问题。根因是 `_refreshTaskFromServer()` 中 `needsMainSync` 的 condition 2（无条件 selected_row_id 对比）过于激进，在轮询期间会强制将所有设备的行选择覆盖为 DB 中记录的 selected_row_id。

## 核心改动

移除 condition 2，只保留 condition 1（sent→success/failed 状态转换检测）。修改后，轮询和 WS 回调只在设备状态发生 sent→success/failed 转换时才同步 selectedRowIds，其他情况不覆盖用户的手动选择。

## 技术方案

修改文件：`frontend/src/views/template/TemplateUpdateView.vue` 第 736-754 行

### 修改前

```javascript
const needsMainSync =
  (oldStatus === 'sent' && dev.update_status !== 'sent' && dev.selected_row_id) ||
  (dev.update_status !== 'sent' && dev.selected_row_id && dev.selected_row_id !== selectedRowIds.value[dev.mac])

if (needsMainSync) {
  exactLocal.selected_row_id = dev.selected_row_id
  selectedRowIds.value = { ...selectedRowIds.value, [dev.mac]: dev.selected_row_id }
  _restoreOverridesFromMainData(dev.mac, dev.custom_data)
  _saveTemplateCache()
  console.log(...)
}
else if (dev.custom_data && oldStatus === 'sent' && dev.update_status === 'success') {
  exactLocal.selected_row_id = dev.selected_row_id
  _restoreOverridesFromMainData(dev.mac, dev.custom_data)
}
```

### 修改后

只保留 condition 1 的状态转换检测：

```javascript
const needsMainSync =
  (oldStatus === 'sent' && dev.update_status !== 'sent' && dev.selected_row_id)

if (needsMainSync) {
  exactLocal.selected_row_id = dev.selected_row_id
  selectedRowIds.value = { ...selectedRowIds.value, [dev.mac]: dev.selected_row_id }
  _restoreOverridesFromMainData(dev.mac, dev.custom_data)
  _saveTemplateCache()
  console.log(...)
}
else if (dev.custom_data && oldStatus === 'sent' && dev.update_status === 'success') {
  exactLocal.selected_row_id = dev.selected_row_id
  _restoreOverridesFromMainData(dev.mac, dev.custom_data)
}
```

### 逻辑说明

| 场景 | 修改前 | 修改后 |
| --- | --- | --- |
| 用户推送后状态转换 sent→success | 同步 selectedRowIds | 同步 selectedRowIds（不变） |
| 轮询期间用户手动切换到其他行 | 强制跳回 DB 的 selected_row_id | 不覆盖，尊重用户选择 |
| WS display_reply 回调触发刷新 | 可能强制跳回 | 仅在 sent→success 时同步 |