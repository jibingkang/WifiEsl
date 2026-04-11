---
name: data-update-module-optimization
overview: 重构数据更新模块：将5步向导简化为单页面三区域布局（左模板+中设备+右表单），增加更新历史记录和操作状态持久化，实现快速重复推送和状态追踪。
design:
  architecture:
    framework: vue
  styleKeywords:
    - Enterprise Dashboard
    - Three-Column Layout
    - Real-time Status
    - Glassmorphism Cards
    - Clean Information Hierarchy
  fontSystem:
    fontFamily: Inter, system-ui, -apple-system, sans-serif
    heading:
      size: 22px
      weight: 600
    subheading:
      size: 16px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#6366F1"
      - "#818CF8"
      - "#4F46E5"
    background:
      - "#F8FAFC"
      - "#FFFFFF"
      - "#F1F5F9"
      - "#0F172A"
    text:
      - "#1E293B"
      - "#64748B"
      - "#94A3B8"
    functional:
      - "#22C55E"
      - "#EF4444"
      - "#F59E0B"
      - "#06B6D4"
todos:
  - id: rewrite-template-update-view
    content: 重写 TemplateUpdateView.vue 为三栏一体式工作台布局，集成模板选择器、数据表单、设备状态、推送控制到单一视图
    status: completed
  - id: simplify-template-form
    content: 简化 TemplateForm.vue，移除 editMode 切换逻辑，统一为默认值表单 + 设备覆盖行内编辑模式
    status: completed
    dependencies:
      - rewrite-template-update-view
  - id: adapt-other-components
    content: 适配 TemplateSelector/DeviceSelector/TemplatePreview/UpdateProgress 组件至新布局（Selector简化为下拉+预览，Preview缩为内嵌面板，Progress移入状态区）
    status: completed
    dependencies:
      - rewrite-template-update-view
      - simplify-template-form
  - id: add-draft-persistence
    content: 实现 localStorage 草稿自动保存/恢复机制，防止数据意外丢失；添加手动保存/清除草稿按钮
    status: completed
    dependencies:
      - simplify-template-form
  - id: add-backend-history-api
    content: 后端 batch.py 推送完成后写入 operation_logs；新增 GET /api/v1/update-history 分页查询接口及 service 层方法
    status: completed
  - id: create-history-page
    content: 新建 UpdateHistory.vue 历史记录页（侧边抽屉），展示任务时间线及设备级详情
    status: completed
    dependencies:
      - add-backend-history-api
---

## Product Overview

优化 WIFI 电子标签系统的数据更新模块，将现有5步向导流程重构为高效的一体化操作界面。用户核心操作路径为：选择模板 -> 添加设备 -> 填写/修改数据 -> 一键推送 -> 查看更新状态。

## Core Features

- **一体化操作界面**: 将模板选择、设备选择、数据编辑整合为单页面多区域布局，消除冗余步骤切换
- **数据草稿持久化**: 使用 localStorage + 可选的数据库保存，支持保存/恢复填写中的数据，避免意外丢失
- **一键快速推送**: 填写完数据后可直接执行推送，无需额外预览确认步骤（预览改为可折叠面板内嵌）
- **实时状态追踪**: 利用已有 WebSocket/MQTT 能力，展示设备 display_reply 实时反馈和最终结果
- **更新历史记录**: 后端 operation_logs 表记录每次批量更新任务，前端提供历史列表查看详情
- **快速重复操作**: 支持基于上次任务的"再次编辑并推送"功能，无需重新选模板和设备

## Tech Stack

- **前端**: Vue 3 + TypeScript + Element Plus + Pinia + Vite（与现有项目完全一致）
- **后端**: Python FastAPI + SQLite（aiosqlite）（利用已有 db_service）
- **通信**: WebSocket（已有 ws_manager）+ MQTT（已有 mqtt_service）
- **持久化**: 前端 localStorage（快速草稿）+ 后端 operation_logs 表（正式历史）

## Tech Architecture

### 架构策略：重构主视图 + 新增历史模块

将 `TemplateUpdateView.vue` 从**步进式向导**重构为**单页面三栏布局**:

```
+---------------------------------------------------------------+
|  [左侧] 配置区              | [中间] 数据编辑区         | [右侧] 状态区        |
|  - 模板选择(下拉)          |  - 动态表单(默认值)       |  - 已选设备摘要      |
|  - 设备选择(弹窗/侧边)     |  - 设备自定义覆盖列表    |  - 推送进度           |
|  - 快速操作按钮组          |  - 内嵌迷你预览          |  - 结果明细           |
|  - 草稿保存/恢复          |                        |  - 历史记录入口       |
+---------------------------------------------------------------+
```

### 核心改动点

1. **TemplateUpdateView.vue 重构**: 从 step-based 切换改为三栏/上下分区布局，所有核心操作在一个视图中可见
2. **TemplateForm.vue 适配**: 移除 editMode 切换逻辑（不再需要 single/default 双模式），统一使用 inline 编辑方式
3. **DeviceSelector.vue 保留**: 作为独立弹窗或侧边抽屉调用，支持随时增减设备
4. **TemplateSelector.vue 简化**: 从卡片网格改为 el-select 下拉 + 卡片预览，节省空间
5. **UpdateProgress.vue 集成**: 从独立步骤变为右侧状态面板的一部分或底部区域
6. **新增 UpdateHistory.vue**: 新页面（或侧边抽屉），展示历史更新记录列表
7. **后端 batch.py 增强**: 每次推送自动写入 operation_logs 表
8. **新增 API**: `GET /api/v1/update-history` 分页查询更新历史

### 数据流

```
用户操作 → 填写表单(v-model双向绑定)
         ↓ 点击"推送"
前端组装 dataList(defaultData + customOverrides合并)
         ↓ POST /batch/template
后端: Semaphore并发控制 → wifi_proxy.apply_template逐个推送
     → 写入 operation_logs 记录任务
     → 返回 results[]
前端: 展示结果(成功/失败) → 失败设备支持一键重试
```

## Implementation Details

### 关键文件变更清单

```
frontend/src/views/template/
├── TemplateUpdateView.vue      # [REWRITE] 主视图：向导→一体式布局
├── TemplateManageView.vue      # [MODIFY]   添加"历史记录"入口
└── UpdateHistory.vue           # [NEW]      更新历史列表页

frontend/src/components/template/
├── TemplateSelector.vue        # [MODIFY]   简化为下拉+预览
├── DeviceSelector.vue          # [KEEP]     基本不变
├── TemplateForm.vue            # [MODIFY]   统一编辑模式,移除editMode切换
├── TemplatePreview.vue         # [MODIFY]   缩减为内嵌面板组件
└── UpdateProgress.vue         # [MODIFY]   适配新布局(作为子区域)

backend/
├── api/batch.py               # [MODIFY]   推送后写入operation_log
└── api/template.py            # [NEW]      GET /update-history 接口
```

### 性能与可靠性考虑

- **localStorage 草稿容量**: 单条草稿约 2-5KB，localStorage 5MB 限制足够存储数百条
- **防重复提交**: 执行中禁用按钮，loading 状态锁死
- **WebSocket 断连**: 更新过程中 WS 断开不影响推送（服务端异步），仅影响实时展示
- **大数量设备(100+)**: 分批加载表格，虚拟滚动或分页; 推送已有限制 Semaphore=5

### 向后兼容性

- URL 参数 `?macs=xxx` 保持有效（从设备管理页跳转时携带）
- 原5步向导逻辑不删除，可通过 feature flag 或路由参数 `/template?mode=wizard` 切换
- 所有子组件 props/emits 接口保持兼容扩展

## 设计风格：现代企业级管理系统

采用**三栏响应式布局**设计，将传统的线性向导转变为信息密度更高的一体化工作台界面。整体风格参考现代 SaaS 管理后台（如 Vercel Dashboard、Linear）的简洁高效美学。

### 页面规划（3个核心页面）

#### 页面1: 数据更新工作台（主页面 `/template`）

这是用户停留时间最长的核心操作页面，采用左右分栏 + 底部状态区的布局。

**Block 1 - 左侧配置栏（280px固定宽度）**
包含模板快捷选择器、设备管理入口、草稿操作、历史记录入口等全局配置项。采用垂直排列的紧凑卡片组，每个功能区块有清晰的图标和标题。

**Block 2 - 中央数据编辑区（自适应宽度）**
上半部分为动态表单区域（根据模板字段渲染输入控件），下半部分为设备自定义覆盖表格。表单与设备表格之间用内嵌预览面板分隔，实时显示当前数据的汇总效果。

**Block 3 - 右侧状态面板（320px固定宽度）**
显示已选设备摘要、最近推送状态、实时进度条、结果统计。推送完成后展示成功/失败分布。

**Block 4 - 底部操作栏**
横跨全宽的粘性工具栏，包含"保存草稿"、"推送到设备"、"重置"等主要操作按钮。

#### 页面2: 更新历史记录 (`/template/history`)

以时间线形式展示所有历史更新任务，每条记录显示：模板名、设备数、成功率、执行时间、操作人。点击展开查看详细设备级结果。

#### 页面3: 模板管理（已有页面 `/template/manage`）

在原有功能基础上增加"使用此模板"快捷按钮，跳转到数据更新页并预选该模板。