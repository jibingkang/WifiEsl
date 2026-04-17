# WIFI标签管理系统 - 多用户架构设计方案

## 1. 目标需求
- 支持多个用户账号登录系统
- 管理员可以添加、修改、删除子账号
- 每个子账号有独立的WIFI系统配置（用户名、密码、API Key）
- 子账号登录后只能访问和管理自己WIFI账号下的设备
- 管理员可以查看所有用户和设备

## 2. 系统架构设计

### 2.1 用户角色定义
```
┌─────────────────────────────────┐
│        用户角色体系             │
├─────────────────────────────────┤
│ 1. 超级管理员 (super_admin)     │
│    - 管理所有用户账号           │
│    - 查看所有设备               │
│    - 系统全局配置               │
├─────────────────────────────────┤
│ 2. 管理员 (admin)              │
│    - 管理自己创建的子账号       │
│    - 查看自己账号的设备         │
│    - 设备控制权限               │
├─────────────────────────────────┤
│ 3. 操作员 (operator)           │
│    - 查看设备状态               │
│    - 受限设备控制权限           │
│    - 无法管理用户               │
└─────────────────────────────────┘
```

### 2.2 数据结构扩展

#### 2.2.1 扩展users表
```sql
-- 添加WIFI系统配置字段到users表
ALTER TABLE users ADD COLUMN wifi_username TEXT;
ALTER TABLE users ADD COLUMN wifi_password TEXT; -- 加密存储
ALTER TABLE users ADD COLUMN wifi_apikey TEXT;   -- 用于MQTT订阅
ALTER TABLE users ADD COLUMN wifi_base_url TEXT;
ALTER TABLE users ADD COLUMN parent_user_id INTEGER DEFAULT 0;

-- 索引优化
CREATE INDEX idx_users_parent ON users(parent_user_id);
CREATE INDEX idx_users_role ON users(role);
```

#### 2.2.2 用户配置存储格式
```json
{
  "id": 2,
  "username": "operator1",
  "role": "operator",
  "wifi_username": "W123456_customer1",
  "wifi_password": "***加密***", 
  "wifi_apikey": "customer1_api_key",
  "wifi_base_url": "http://192.144.234.153:4000",
  "parent_user_id": 1,
  "created_by": 1
}
```

### 2.3 Session增强设计

#### 2.3.1 Session数据结构
```python
{
    "username": "operator1",
    "role": "operator",
    "wifi_config": {
        "username": "W123456_customer1",
        "apikey": "customer1_api_key",
        "base_url": "http://192.144.234.153:4000"
    },
    "created_at": 1776149208,
    "expires_at": 1776156408
}
```

#### 2.3.2 JWT Payload增强
```json
{
  "sub": "operator1",
  "role": "operator",
  "wifi_user": "W123456_customer1",
  "wifi_apikey": "customer1_api_key",
  "parent_id": 1,
  "iat": 1776149208,
  "exp": 1776156408
}
```

## 3. 核心功能实现方案

### 3.1 用户登录流程增强
```python
async def enhanced_proxy_login(username: str, password: str, ip: str = "") -> dict:
    """
    增强版登录流程：
    1. 验证本地用户账号密码
    2. 根据用户角色和配置调用不同的WIFI系统登录
    3. 生成包含配置信息的JWT token
    """
    # 1. 验证本地用户
    user = await get_user_by_name(username)
    if not user or not verify_password(password, user["password"]):
        await add_log(username, "LOGIN_FAILED", detail="用户名或密码错误", result="failed", ip_address=ip)
        raise ValueError("用户名或密码错误")
    
    # 2. 获取用户的WIFI配置
    wifi_config = {
        "username": user.get("wifi_username"),
        "password": decrypt_wifi_password(user.get("wifi_password")),
        "apikey": user.get("wifi_apikey"),
        "base_url": user.get("wifi_base_url")
    }
    
    # 3. 调用WIFI系统登录
    try:
        wifi_result = await wifi_proxy.login(
            username=wifi_config["username"],
            password=wifi_config["password"],
        )
        # 处理响应...
        
    except Exception as e:
        logger.error(f"用户 {username} WIFI系统登录失败: {e}")
        # 根据角色决定是否允许登录...
```

### 3.2 用户管理API设计

#### 3.2.1 用户列表API
```
GET /api/v1/users
权限：超级管理员查看所有用户，管理员查看自己创建的用户
```

#### 3.2.2 添加用户API
```
POST /api/v1/users
请求体：
{
  "username": "operator1",
  "password": "user_password",
  "role": "operator",
  "wifi_username": "W123456_customer1",
  "wifi_password": "wifi_password",
  "wifi_apikey": "customer1_api_key",
  "wifi_base_url": "http://192.144.234.153:4000"
}
```

#### 3.2.3 修改用户API
```
PUT /api/v1/users/{user_id}
权限：只能修改自己创建的子账号
```

#### 3.2.4 删除用户API
```
DELETE /api/v1/users/{user_id}
权限：只能删除自己创建的子账号
```

### 3.3 设备隔离方案

#### 3.3.1 设备获取权限控制
```python
async def get_user_devices(user_config: dict, page: int = 1, page_size: int = 20):
    """
    根据用户配置获取设备列表
    """
    # 使用用户的WIFI配置获取设备
    api_key = user_config.get("wifi_apikey")
    
    # 调用WIFI系统API，使用用户的配置
    raw_data = await wifi_proxy.get_devices(
        api_key=api_key,
        page=page,
        page_size=page_size
    )
    
    # 设备数据解析...
```

#### 3.3.2 设备控制权限验证
```python
async def verify_device_access(mac: str, user_config: dict) -> bool:
    """
    验证用户是否有权限访问指定设备
    """
    # 根据用户配置获取设备列表
```

## 4. 前端界面设计

### 4.1 用户管理界面
```
┌─────────────────────────────────────────────────┐
│           用户管理                              │
├─────────────────────────────────────────────────┤
│ [添加用户] [批量操作] [搜索:___________]        │
├─────┬──────────┬──────┬─────────┬──────────────┤
│ ID  │ 用户名   │ 角色 │ 创建时间│ 操作          │
├─────┼──────────┼──────┼─────────┼──────────────┤
│ 2   │ operator1│操作员│ 2026-04-│ [编辑][删除]  │
│     │          │      │ 14 17:30│              │
├─────┼──────────┼──────┼─────────┼──────────────┤
│ 3   │ operator2│操作员│ 2026-04-│ [编辑][删除]  │
│     │          │      │ 14 17:32│              │
└─────┴──────────┴──────┴─────────┴──────────────┘
```

### 4.2 用户添加/编辑表单
```
┌─────────────────────────────────────────────────┐
│           用户信息                              │
├─────────────────────────────────────────────────┤
│ 用户名: _______________                         │
│ 密码:   _______________                         │
│ 确认密码: _______________                       │
│                                                   
│           WIFI系统配置                           │
├─────────────────────────────────────────────────┤
│ WIFI用户名: _______________                     │
│ WIFI密码:   _______________                     │
│ API Key:   _______________                      │
│ WIFI地址: http://192.144.234.153:4000           │
│                                                   
│          权限设置                                │
├─────────────────────────────────────────────────┤
│ 角色: ● 操作员 ○ 管理员 ○ 超级管理员            │
└─────────────────────────────────────────────────┘
```

## 5. 安全考虑

### 5.1 密码安全
1. **本地用户密码**：SHA256哈希存储
2. **WIFI密码**：AES加密存储
3. **API Key**：明文存储，但只用于MQTT订阅

### 5.2 权限控制
1. **垂直权限**：角色分级
2. **水平权限**：用户只能访问自己创建的设备和用户
3. **数据隔离**：不同用户的设备数据完全隔离

### 5.3 审计日志
1. **用户操作**：记录所有用户管理操作
2. **设备访问**：记录设备访问日志
3. **登录记录**：详细登录审计

## 6. 实施步骤

### 阶段1：数据库扩展（1天）
1. 扩展users表，添加WIFI配置字段
2. 更新数据库初始化脚本
3. 创建数据库迁移脚本

### 阶段2：后端增强（2天）
1. 修改auth_service.py，支持用户独立配置
2. 创建用户管理API
3. 增强设备API权限控制

### 阶段3：前端界面（1天）
1. 创建用户管理页面
2. 添加用户表单
3. 用户列表展示

### 阶段4：测试验证（1天）
1. 单元测试
2. 集成测试
3. 安全测试

### 阶段5：部署上线（1天）
1. 数据迁移
2. 系统部署
3. 用户培训

## 7. 风险与应对

### 7.1 技术风险
1. **WIFI系统API兼容性**：确保不同用户的API调用正常
2. **数据库性能**：用户增多可能影响性能，添加索引优化

### 7.2 业务风险
1. **用户配置错误**：提供配置验证和测试功能
2. **权限混乱**：严格的权限验证和审计

### 7.3 安全风险
1. **敏感数据泄露**：加密存储，访问控制
2. **权限提升攻击**：输入验证，权限边界检查

## 8. 扩展性考虑

### 8.1 未来功能扩展
1. **用户组管理**：支持用户分组
2. **设备共享**：跨用户设备共享
3. **权限模板**：可配置的权限模板

### 8.2 性能扩展
1. **数据库分表**：用户数据量增大时考虑分表
2. **缓存策略**：用户配置和设备数据缓存
3. **负载均衡**：支持多实例部署

---

**下一步建议**：先实施阶段1的数据库扩展，然后逐步完成后续阶段。需要我开始编写数据库扩展代码吗？