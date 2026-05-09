---
name: allow-chinese-username
overview: 修改前端用户表单的正则验证规则，允许用户名包含中文字符。
todos:
  - id: allow-chinese-username
    content: 修改 UserFormDialog.vue 第286行正则，允许用户名包含中文、字母、数字和下划线
    status: pending
---

## 用户需求

支持用户名设置为中文。

## 核心功能

- 用户创建/编辑表单允许输入中文用户名
- 中文用户名可通过前端验证和后端存储

## 技术方案

### 修改范围

仅需修改一个文件的一行代码：`frontend/src/views/user/components/UserFormDialog.vue` 第286行。

### 修改内容

将用户名验证正则从仅允许 ASCII 字符改为同时允许中文字符：

```typescript
// 修改前
{ pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' },

// 修改后
{ pattern: /^[\u4e00-\u9fa5a-zA-Z0-9_]+$/, message: '用户名只能包含中文、字母、数字和下划线', trigger: 'blur' },
```

### 兼容性说明

- SQLite `TEXT` 类型原生支持 UTF-8，无需数据库变更
- 后端 Pydantic 模型仅校验长度，无字符集限制
- JWT `sub` 字段支持 Unicode
- 登录页验证同样无正则限制