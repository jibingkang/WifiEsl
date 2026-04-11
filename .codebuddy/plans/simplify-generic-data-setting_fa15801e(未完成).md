---
name: simplify-generic-data-setting
overview: 将 TemplateUpdateView 中的「通用数据设置」从固定展示的完整表单卡片改为可折叠面板（el-collapse），默认收起，点击展开编辑；同时优化移动端体验。
design:
  styleKeywords:
    - Minimalism
    - Clean
    - Collapsible
  fontSystem:
    fontFamily: PingFang-SC
    heading:
      size: 15px
      weight: 600
    subheading:
      size: 13px
      weight: 500
    body:
      size: 12.5px
      weight: 400
  colorSystem:
    primary:
      - "#6366F1"
      - "#8B5CF6"
    background:
      - "#FFFFFF"
      - "#F8FAFC"
    text:
      - "#1E293B"
      - "#475569"
      - "#94A3B8"
    functional:
      - "#22C55E"
      - "#F59E0B"
      - "#EF4444"
todos:
  - id: collapse-form-area
    content: 将通用数据设置区改为el-collapse折叠面板：默认收起、自定义title插槽显示字段摘要、展开时渲染WorkspaceForm
    status: pending
  - id: add-summary-computed
    content: 新增 formSummaryText 和 formFieldStats 计算属性，用于折叠面板标题显示已填字段概览
    status: pending
  - id: update-collapse-styles
    content: 调整样式：移除旧的 .default-form-card/.form-footer-tip 样式，优化折叠面板视觉效果与页面一致性
    status: pending
    dependencies:
      - collapse-form-area
---

## 产品概述

简化数据更新页面中"通用数据设置"区域，当前该区域以完整卡片+表单形式占据大量页面空间，影响用户操作体验。

## 核心功能

- 将"通用数据设置"从**固定展开的卡片**改为**可收起/展开的折叠面板**
- **默认收起状态**：仅显示一行标题栏，展示已填字段数量和关键值摘要
- 点击标题栏或箭头可**展开查看/编辑完整表单**
- 展开后显示完整的 WorkspaceForm 组件（逻辑不变）
- 收起时通过字段摘要让用户快速了解当前默认值状态
- 设备列表区域因此获得更多可视空间

## 技术栈

- Vue 3 + TypeScript + Element Plus + UnoCSS

## 实现方案

采用 **Element Plus `el-collapse` 折叠面板** 方案，理由如下：

1. 比弹窗方案更轻量——无需遮罩层、关闭按钮、额外点击操作
2. 比"按钮+下拉列表"更适合多字段表单场景（下拉不适合放多个输入框）
3. 折叠面板是 Element Plus 内置组件，项目已有使用基础，零新增依赖
4. 用户可在同一页面上下文内完成编辑，认知负担最低

### 交互设计

```
┌─ 默认收起态 ───────────────────────────────────────┐
│ ▶ 通用数据设置          已填 5/6 字段  门号:201 店号:1005 │
├─ 点击展开 ──────────────────────────────────────────┤
│ ▼ 通用数据设置              [修改后所有设备自动继承]    │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│   │ 门号*201  │ │ 店号*1005│ │ 条码*123 │            │
│   └──────────┘ └──────────┘ └──────────┘            │
│   💡 下方表格可为每台设备单独修改不同数据               │
└─────────────────────────────────────────────────────┘
```

### 代码改动范围

| 文件 | 改动 | 说明 |
| --- | --- | --- |
| `TemplateUpdateView.vue` | 修改模板第49-64行 | 用 `<el-collapse>` + `<el-collapse-item>` 包裹通用数据设置区域，添加字段摘要计算属性 |
| `TemplateUpdateView.vue` | 修改样式部分 | 移除 `.default-form-card` / `.form-footer-tip` 等旧样式，添加折叠面板相关样式 |
| 无需改动 `WorkspaceForm.vue` | 不变 | 继续作为子组件复用 |


### 关键实现细节

1. **默认收起**：`el-collapse-item` 设置 `v-model="formExpanded"` 初始值为 `false`
2. **字段摘要计算**：新增 computed `formSummaryText`，遍历 defaultData 提取非空字段，格式为 `"门号:201  店号:1005"`
3. **字段统计**：新增 computed `formFieldStats` 返回 `"已填 N/M 个字段"`
4. **自定义折叠头**：用 `#title` 插槽替换默认标题，左侧图标+文字，右侧显示摘要信息
5. **首次自动展开**：如果 defaultData 全为空（首次进入），可以默认展开引导用户填写；有数据则收起

## 设计风格

延续页面现有的简洁卡片风格，折叠面板与设备列表卡片的圆角、边框、阴影保持一致。收起态高度控制在约48px，紧凑而不拥挤。展开态与原有表单卡片视觉一致。

## 页面结构变化

- 顶栏工具条不变
- "通用数据设置"从独立卡片变为 el-collapse 面板项，默认收起
- "设备列表"卡片上移，获得更多可视空间
- 底部操作栏不变

## 折叠面板设计细节

- 标题行左侧：铅笔图标 + "通用数据设置" 文字
- 标题行右侧：字段统计徽章 + 已填值预览标签（最多显示3个关键值）
- 展开/收起动画使用 Element Plus 内置过渡
- 收起时标题行 hover 效果提示可交互