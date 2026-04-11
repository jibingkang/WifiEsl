---
name: frontend-simple-update-ui
overview: 将数据更新工作台从三栏复杂布局重构为单栏流式布局：自动加载模板、合并双层编辑为单表、移除右侧状态面板改为内联通知、设备表格增加勾选批量推送、历史记录改为子页面路由、保留草稿自动保存功能。
design:
  architecture:
    framework: vue
  styleKeywords:
    - Minimalism
    - Clean
    - Single-column Flow
    - Card-based Layout
    - Soft Gradient Accents
    - Micro-interactions
    - Glassmorphism Footer
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
      - "#6366F1"
      - "#8B5CF6"
      - "#7C6EFB"
    background:
      - "#F8FAFC"
      - "#FFFFFF"
      - "#F1F5F9"
    text:
      - "#1E293B"
      - "#64748B"
      - "#94A3B8"
    functional:
      - "#22C55E"
      - "#EF4444"
      - "#F59E0B"
      - "#3B82F6"
todos:
  - id: rewrite-main-view
    content: 重写 TemplateUpdateView.vue 为单栏流式布局：顶栏工具条+默认值表单+设备表格(含checkbox)+底部操作栏+Notification结果反馈，保留草稿逻辑
    status: completed
  - id: enhance-device-table
    content: 增强 DeviceDataTable.vue：新增 checkbox 选择列、全选/反选底部工具条、优化内联编辑交互
    status: completed
  - id: create-history-page
    content: 新建 HistoryPage.vue 历史记录子页面，复用 HistoryPanel 逻辑改造为全屏页面，支持复用配置跳转回数据更新页
    status: completed
  - id: update-routes-sidebar
    content: 更新 routes.ts 添加 /template/history 路由，DefaultLayout.vue 侧边栏 menuItems 增加更新历史入口
    status: completed
    dependencies:
      - create-history-page
  - id: polish-and-test
    content: 联调测试：验证自动加载模板、设备勾选推送、草稿恢复、历史页面跳转等完整链路
    status: completed
    dependencies:
      - rewrite-main-view
      - enhance-device-table
      - create-history-page
      - update-routes-sidebar
---

## Product Overview

将当前"数据更新工作台"页面从**三栏复杂工作台**简化为**单栏流式操作页面**，核心目标是：进入即用、操作简单、一目了然。同时将历史记录从抽屉弹窗升级为独立子页面。

## Core Features

### 页面重构（TemplateUpdateView.vue 主页面）

1. **自动加载默认模板**：进入页面后自动选中第一个模板（或恢复上次草稿中的模板），无需手动选择；无模板时显示空态引导去模板管理页创建
2. **顶部工具栏**：左侧为模板切换器（小型 el-select），右侧醒目的"添加设备"按钮和"历史记录"链接
3. **统一数据表单区（合并原 WorkspaceForm + DeviceDataTable）**：

- 上方：默认值编辑区（所有设备共享的字段值，修改=批量改所有设备）
- 下方：设备数据表格，每行显示一台设备，包含：
    - **Checkbox 列**：支持勾选单台/批量推送
    - **设备名/MAC 列**
    - **在线状态列**（绿点/灰点）
    - **动态字段列**（继承默认值可内联修改，自定义值橙色高亮）
    - **操作列**（编辑/删除该台设备）

4. **底部固定操作栏**：显示已选设备数 + 推送按钮 + 重置按钮
5. **推送结果反馈**：移除右侧 StatusPanel 面板，改用 ElNotification 展示成功/失败摘要
6. **保留草稿自动保存**：localStorage 30秒间隔自动保存，进入页面时恢复

### 历史记录子页面（新增 /template/history）

1. 独立路由 `/template/history`，侧边栏增加入口（在"数据更新"下作为子菜单或兄弟菜单项）
2. 复用现有 HistoryPanel.vue 组件逻辑，改造为全屏页面展示
3. 支持查看历史推送记录、展开详情、一键复用配置重新推送

## Tech Stack

- **前端框架**: Vue 3 + TypeScript（现有项目技术栈）
- **UI 组件库**: Element Plus（已使用）
- **图标**: lucide-vue-next（已使用）+ @element-plus/icons-vue
- **状态管理**: Pinia store（useDeviceStore、useTemplate composable）
- **样式**: SCSS scoped + CSS 变量
- **路由**: Vue Router 4（已有 routes.ts）

## Implementation Approach

### 核心策略：三栏→单栏流式布局，合并双层编辑为一张表

**改动前架构**：

```
TemplateUpdateView (三栏 flex)
├── panel-left (280px): 模板select + 设备chips + 草稿操作
├── panel-center (flex): WorkspaceForm(默认) + DeviceDataTable(覆盖) + MiniPreview
└── panel-right (320px): StatusPanel(三态)
+ 弹窗: DeviceSelectorDialog, Drawer: HistoryPanel
```

**改动后架构**：

```
TemplateUpdateView (单栏流式)
├── toolbar: [模板切换器 ▾] ... [+ 添加设备] [历史记录]
├── empty-state (无模板时): 引导去创建模板
├── default-form-card: 默认值编辑区 (WorkspaceForm 精简版)
├── device-table-card: 设备数据表格 (增强版 DeviceDataTable, 含 checkbox)
│   ├── col-checkbox | 设备名/MAC | 状态 | 动态字段... | 操作
│   └── 底部: 全选/反选 + 已选 N 台
├── bottom-bar (sticky): [重置] ... [▶ 推送到 N 台]
├── notification: 推送结果 (ElNotification 替代 StatusPanel)
+ 弹窗: DeviceSelectorDialog (不变)

/template/history (新子页面):
├── HistoryPage.vue (基于 HistoryPanel 逻辑的全屏页面)
```

### 关键设计决策

1. **模板自动选中策略**：优先级 = 草稿中保存的 tid > 模板列表第一个 > 显示空态
2. **数据模型不变**：defaultData（共享默认值）+ customOverrides（每台覆盖），但 UI 上不再分两个区域，而是表格中直接展示"默认值背景 + 覆盖值高亮"
3. **checkbox 选择与推送绑定**：executePush() 只推送 checkedMacs 中的设备，不再全量推送
4. **StatusPanel 降级**：执行中显示全局 loading + 进度条（ElLoading.directive 或顶部进度条），完成后 ElNotification 弹出结果摘要
5. **历史记录页面化**：新建 HistoryPage.vue，routes.ts 加子路由，侧边栏加菜单项

## Architecture Design

```mermaid
graph TB
    subgraph 新页面结构
        A[Toolbar<br/>模板切换 + 添加设备 + 历史] --> B{有模版?}
        B -->|否| C[EmptyState<br/>引导去创建]
        B -->|是| D[DefaultFormCard<br/>默认值编辑区]
        D --> E[DeviceTableCard<br/>含checkbox的设备数据表]
        E --> F[BottomBar<br/>推送/重置]
    end
    
    subgraph 推送流程
        F --> G[只推checkedMacs]
        G --> H[ElNotification结果]
    end
    
    subgraph 子页面
        I[/template/history] --> J[HistoryPage<br/>时间线列表]
        J --> K[复用配置重推]
    end
```

## Directory Structure

```
frontend/src/
├── views/template/
│   ├── TemplateUpdateView.vue    # [REWRITE] 三栏→单栏流式，核心改动文件
│   ├── WorkspaceForm.vue         # [MODIFY] 轻微调整：去除标题区的模板名重复
│   ├── DeviceDataTable.vue       # [MODIFY] 增加 checkbox 列、优化操作列
│   ├── StatusPanel.vue           # [KEEP but UNUSED] 保留不删，后续可能复用
│   ├── HistoryPanel.vue          # [KEEP] 作为组件被 HistoryPage 引用
│   ├── HistoryPage.vue           # [NEW] 历史记录独立子页面
│   └── MiniPreview.vue           # [UNUSED in new layout] 保留不删
├── components/template/
│   └── DeviceSelectorDialog.vue  # [UNCHANGED] 保持现有弹窗交互
├── router/
│   └── routes.ts                 # [MODIFY] 添加 /template/history 路由
├── layouts/
│   └── DefaultLayout.vue         # [MODIFY] menuItems 增加历史记录入口
└── api/
    └── template.ts               # [UNCHANGED]
```

## Implementation Notes

1. **TemplateUpdateView.vue 重写要点**：

- 移除 `.workspace-body` 的三栏 flex 布局，改为 `flex-direction: column` 单栏
- onMounted 中自动调用 `handleTemplateChange(firstTemplateId)` 
- 新增 `checkedMacs: ref<Set<string>>(new Set())` 追踪勾选状态
- executePush 中过滤 `Array.from(checkedMacs)` 而非 `selectedMacs`
- 推送完成用 `ElNotification({ title, message, type })` 替代 StatusPanel
- 草稿逻辑完整保留（DRAFT_KEY、autoSave、restoreDraft）

2. **DeviceDataTable.vue 增强**：

- props 新增 `modelValue: string[]`（勾选的 mac 列表）
- emit 新增 `update:modelValue`
- 表格 `<thead>` 最左增加 `<th class="col-check"><el-checkbox .../></th>`
- `<tbody>` 每行最左增加 `<td class="col-check"><el-checkbox v-model="rowChecked"/></td>`
- 底部增加"全选/反选"工具条

3. **HistoryPage.vue 新建**：

- 基于 HistoryPanel.vue 的 script 逻辑（fetchPage、items、toggleDetail 等）
- 加上页面级 header/breadcrumb
- "使用此配置重新推送"按钮改为 `router.push('/template')` 并通过 pinia/event bus 传递复用数据

4. **路由和侧边栏**：

- routes.ts 在 `path: 'template'` 下增加子路由 `path: 'history'`
- DefaultLayout.vue menuItems 在 `{ path: '/template', title: '数据更新' }` 后追加 `{ path: '/template/history', title: '更新历史' }`

5. **兼容性注意**：

- 不删除任何现有文件（StatusPanel.vue、MiniPreview.vue 仅是不再 import）
- deviceStore 和 useTemplate composable 完全复用，不改接口
- batchApplyTemplate API 调用方式不变

## 设计风格：简洁高效的工作台

采用现代简约的**单栏流式布局**，以清晰的信息层级和直观的操作路径为核心设计理念。

### 整体布局描述

页面采用从上到下的线性信息流，分为 5 个功能区块：

**区块 1 — 顶栏工具条（Toolbar）**
白色卡片式顶栏，左侧放置精简的模板下拉切换器（紧凑尺寸），右侧放置主操作按钮组："添加设备"（Primary 实心按钮，醒目紫色）和"历史记录"（文字链接）。整个工具条使用 sticky 定位，滚动时始终可见。

**区块 2 — 无模板空态引导（条件渲染）**
当无模板时，页面中央展示空态插图 + "暂无可用模板"提示文字 + "去创建模板" Primary 按钮，点击跳转至 /template/manage。

**区块 3 — 默认值编辑区（Default Form Card）**
圆角白色卡片，标题为"通用数据设置"，副标题说明"以下数据将作为所有设备的默认填充值"。内部根据模板字段动态渲染表单控件（text/number/select 等），采用两列栅格布局（el-row/el-col）。字段标签使用较小字号，输入框使用浅色背景聚焦高亮的设计语言。卡片底部有一条淡色分隔线和提示文字"下方表格可为每台设备单独修改不同数据"。

**区块 4 — 设备数据表格（Device Table Card）**
圆角白色卡片，这是页面的核心区域。表格包含：最左侧 checkbox 列（支持全选/单选）、设备标识列（名称 + MAC 双行）、在线状态列（绿色/灰色圆点带脉冲动画）、各动态字段列（可内联编辑的 input 单元格，自定义值使用淡琥珀色背景高亮区分于默认灰色背景）、操作列（移除按钮）。表格底部固定工具条显示"已选 N 台设备"统计信息和快捷全选/清除按钮。

**区块 5 — 底部操作栏（Bottom Action Bar）**
页面底部 sticky 固定的操作栏，左右分布：左侧"重置"文字按钮，右侧大号 Primary 渐变按钮"推送到 N 台设备"。操作栏使用毛玻璃效果（backdrop-filter: blur）增加层次感。

### 交互细节

- 表单输入框 focus 时边框变为主题色并带有柔和光晕
- 设备行 hover 时整行微亮，checkbox 出现过渡动画
- 推送按钮 disabled 态降低透明度而非置灰
- 推送成功/失败使用 Element Plus Notification 从右上角滑入，停留 5 秒自动关闭
- 表格单元格编辑时自动保存（blur 触发），无需确认按钮

## Agent Extensions

### SubAgent

- **code-explorer**
- Purpose: 确认 DeviceStore 的 devices 数组的 status 字段来源（是 is_online 还是 status），以及 DefaultLayout.vue 中 menuItems 的精确格式，确保路由添加和历史入口不会破坏现有导航
- Expected outcome: 确认设备状态字段映射正确、menuItems 格式无误、新路由 path 不冲突