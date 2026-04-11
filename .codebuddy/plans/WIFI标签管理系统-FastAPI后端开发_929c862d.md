---
name: WIFI标签管理系统-FastAPI后端开发
overview: 开发Python FastAPI后端服务，作为前端(Vue3)与真实WIFI标签系统(http://192.168.1.172:4000)之间的中间层/代理网关。实现认证代理、设备管理API代理、MQTT实时状态转发(WebSocket)、模板管理、批量操作等核心功能。支持可配置的连接参数(BaseURL/MQTT/APIKey)。
design:
  architecture:
    framework: react
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
  - id: fix-frontend-bugs
    content: 修复前端残留 bug(template.ts import错误)并创建 .env/.env.example 配置文件
    status: completed
  - id: backend-core
    content: "创建 backend/ 骨架: main.py + config.py + models.py + requirements.txt"
    status: completed
    dependencies:
      - fix-frontend-bugs
  - id: service-layer
    content: "实现 services 层: wifi_client(HTTP代理) + mqtt_service(MQTT桥接) + ws_manager + auth_service"
    status: completed
    dependencies:
      - backend-core
  - id: api-routes
    content: "实现 API 路由: auth(登录代理) + devices(CRUD代理) + control(设备控制) + template + batch + websocket"
    status: completed
    dependencies:
      - service-layer
  - id: integration-test
    content: 启动后端服务 + 全流程前后端联调测试(登录/设备列表/控制/监控)
    status: completed
    dependencies:
      - api-routes
---

## 产品概述

开发 WIFI 标签管理系统的 FastAPI 后端服务，作为前端 (Vue3, localhost:3000) 与真实 WIFI 标签系统 (http://192.168.1.172:4000) 之间的**代理网关 + 实时消息中转站**。后端负责：认证代理、设备 API 代理、MQTT 实时状态桥接至 WebSocket、模板管理、批量操作。

## 核心功能

### 1. 认证代理模块

- 前端发送用户名密码 → 后端用 test/123456 调用真实系统 `POST /user/api/login` → 获取 token 和 apiKey → 返回给前端
- 后端维护 session/token 映射，后续请求携带的 Bearer Token 对应到真实系统的 apiKey

### 2. 设备 API 代理（全部转发到真实 WIFI 系统）

| 前端调用 | 后端代理目标 |
| --- | --- |
| `GET /api/v1/devices` | `GET http://192.168.1.172:4000/user/api/rest/devices` |
| `GET /api/v1/devices/:id` | `GET .../devices/:id` |
| `GET /api/v1/devices/mac/:mac` | `GET .../devices/mac/:mac` |
| `POST /api/v1/mqtt/publish/:mac/led` | `POST .../mqtt/publish/:mac/led` |
| `POST /api/v1/mqtt/publish/:mac/battery` | `POST .../mqtt/publish/:mac/battery` |
| `POST /api/v1/mqtt/publish/:mac/display` | `POST .../mqtt/publish/:mac/display` |
| `POST /api/v1/mqtt/publish/:mac/reboot` | `POST .../mqtt/publish/:mac/reboot` |
| `POST /api/v1/mqtt/publish/:mac/template/:tid` | `POST .../mqtt/publish/:mac/template/:tid` |


### 3. 模板管理

- `GET /api/v1/templates` — 返回可用模板列表（含字段定义）
- `GET /api/v1/templates/:id` — 模板详情
- 模板数据可从真实系统获取或本地配置

### 4. MQTT-WebSocket 桥接

- 后端连接 MQTT Broker (`192.168.1.172:8883`, TLS)
- 订阅 `/client/${ApiKey}/action/{online,offline,battery_reply,...}` 等 Topic
- 通过 `WS /ws/device-status` 将实时设备状态推送到前端
- 前端 WebSocket 连接通过 Vite 代理转发

### 5. 批量操作

- `POST /api/v1/batch/template` — 批量应用模板
- 设备数据导入导出

### 可配置项（全部通过 .env 文件）

- `WIFI_BASE_URL` — 真实系统地址 (默认 http://192.168.1.172:4000)
- `WIFI_USERNAME` / `WIFI_PASSWORD` — 真实系统账号
- `WIFI_APIKEY` — 真实系统 API Key
- `MQTT_BROKER_HOST` / `MQTT_BROKER_PORT` — MQTT Broker 地址端口
- 后端监听端口 (默认 8000)

### 联调测试

后端开发完成后启动，与前端 localhost:3000 进行全流程联调：

- 登录流程测试
- 设备列表加载和展示
- 设备控制操作（LED/重启/电量）
- 模板更新向导流程
- 批量编辑功能
- 监控看板实时数据推送

## Tech Stack

### 核心框架

- **Python 3.11+** + **FastAPI** (Uvicorn ASGI服务器) — 高性能异步Web框架
- **httpx** — 异步HTTP客户端（用于代理转发请求到真实WIFI系统，替代requests支持async）
- **paho-mqtt** — MQTT客户端（连接Broker订阅设备状态Topic）
- **websockets** (FastAPI内置WebSocket) — 向前端推送实时数据
- **Pydantic v2** — 数据校验和序列化
- **python-dotenv** — .env 环境变量管理
- **SQLite (aiosqlite)** — 轻量本地数据库（存储session/缓存数据）

### 项目依赖

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
httpx>=0.26.0
paho-mqtt>=1.6.1
pydantic>=2.5.0
python-dotenv>=1.0.0
aiosqlite>=0.19.0
```

## Implementation Approach

### 架构模式：反向代理 + MQTT Bridge

采用 **BFF (Backend for Frontend) 代理模式**：

```
前端(Vue3:3000)  ←→  后端(FastAPI:8000)  ←→  WiFi标签系统(192.168.1.172:4000)
                        │
                   MQTT Broker(8883)
                   订阅设备状态 → WS推送给前端
```

**关键设计决策**：

1. **认证代理**: 后端持有真实系统凭据，前端只拿到后端颁发的 JWT。避免暴露真实系统的 apiKey 给浏览器。
2. **异步架构**: 使用 FastAPI async endpoints + httpx 异步请求，避免阻塞事件循环
3. **MQTT桥接**: 后端作为单一 MQTT 客户端连接 Broker，多路复用到所有前端的 WebSocket 连接（N:1:M 模式），而非每个前端直连 MQTT
4. **环境隔离**: 所有外部连接参数通过 .env 配置，零硬编码

### API 路径映射策略

前端 baseURL = `/api/v1`, Vite proxy → `localhost:8000/api/v1`
后端路由前缀 = `/api/v1`，内部转发时去掉此前缀拼接真实路径

### 认证流程设计

1. 前端 POST `{username, password}` 到 `/api/v1/auth/login`
2. 后端验证通过后，用 WIFI 凭据调真实系统登录获取 apiKey
3. 后端生成 JWT token（包含 userId + wifiApiKey 加密在内），返回前端
4. 后续前端请求带 Bearer token，后端解码获得 wifiApiKey 用于转发
5. JWT 有效期 24h，存内存字典（生产可换 Redis）

### WebSocket 推送协议

```
{"type": "device_online", "data": {"mac": "xx:xx", "timestamp": "..."}}
{"type": "device_offline", "data": {"mac": "xx:xx"}}
{"type": "battery_reply", "data": {"mac": "xx:xx", "voltage": 3500}}
{"type": "control_reply", "data": {"mac": "xx:xx", "action": "led", "result": 200}}
```

## Architecture Design

### 系统组件关系图

```mermaid
graph TB
    subgraph Frontend["前端 Vue3 :3000"]
        Login[登录页]
        Dashboard[仪表盘]
        Devices[设备管理]
        Template[模板向导]
        Batch[批量编辑]
        Monitor[监控看板]
    end

    subgraph Backend["FastAPI 后端 :8000"]
        Router[API Router /api/v1]
        AuthSvc[认证代理服务]
        DeviceProxy[设备API代理]
        ControlProxy[控制指令代理]
        TemplateSvc[模板服务]
        BatchSvc[批量操作服务]
        MqttBridge[MQTT桥接服务]
        WsMgr[WebSocket管理器]
        SessionMgr[Session管理-JWT+apiKey映射]
    end

    subgraph WifiSystem["WIFI标签系统 :4000"]
        WifiAuth[/user/api/login]
        WifiDevices[/user/api/rest/devices]
        WifiControl[/user/api/mqtt/publish/*]
    end

    subgraph MQTT["MQTT Broker :8883 TLS"]
        Topics[设备状态Topics<br/>online/offline/battery_reply<br/>led_reply/reboot_reply]
    end

    Login -->|POST /auth/login| AuthSvc
    AuthSvc -->|代理登录| WifiAuth
    AuthSvc -->|返回JWT+用户信息| Login

    Devices -->|GET /devices| DeviceProxy
    DeviceProxy -->|转发+apiKey| WifiDevices
    WifiDevices -->|返回设备列表| DeviceProxy

    Template -->|GET /templates| TemplateSvc
    Monitor -->|WS /ws/device-status| WsMgr

    MqttBridge -->|订阅| Topics
    Topics -->|推送设备状态| MqttBridge
    MqttBridge -->|广播| WsMgr
    WsMgr -->|实时JSON| Monitor

    Devices -->|POST /mqtt/publish/*| ControlProxy
    ControlProxy -->|转发+apiKey| WifiControl
```

## Directory Structure Summary

```
f:\pick\AI项目\CodeBuddy\WifiEsl\
├── backend/                              # [NEW] FastAPI后端项目根目录
│   ├── __init__.py                       # [NEW] 包标记文件
│   ├── main.py                           # [NEW] FastAPI应用入口 - CORS/Middleware/路由注册/Lifespan启动关闭
│   ├── config.py                         # [NEW] pydantic-settings 配置管理类 - 从.env加载所有可配项
│   ├── models.py                         # [NEW] Pydantic数据模型 - LoginRequest/Device/Template/ApiResponse等
│   │
│   ├── api/                              # [NEW] API路由层
│   │   ├── __init__.py                  # [NEW] api-router汇总注册
│   │   ├── auth.py                      # [NEW] POST /auth/login - 登录认证代理+JWT颁发
│   │   ├── devices.py                   # [NEW] GET/POST/PUT/DELETE /devices - 设备CRUD代理
│   │   ├── control.py                   # [NEW] POST /mqtt/publish/:mac/{led|reboot|battery|display} - 设备控制代理
│   │   ├── template.py                  # [NEW] GET /templates, GET /templates/:id - 模板管理
│   │   ├── batch.py                     # [NEW] POST /batch/template等 - 批量操作接口
│   │   └── websocket.py                 # [NEW] WS /ws/device-status - WebSocket实时推送端点
│   │
│   ├── services/                         # [NEW] 业务逻辑层
│   │   ├── __init__.py                 # [NEW]
│   │   ├── wifi_client.py              # [NEW] httpx AsyncClient 封装 - 代理转发到真实WIFI系统(自动注入apiKey)
│   │   ├── mqtt_service.py             # [NEW] paho-mqtt客户端封装 - 连接Broker/订阅Topic/消息回调处理
│   │   ├── auth_service.py             # [NEW] 登录代理逻辑 - 调真实系统登录/JWT生成校验/session管理
│   │   └── ws_manager.py              # [NEW] WebSocket连接管理 - 连接池/广播消息/心跳检测
│   │
│   └── requirements.txt                # [NEW] 后端Python依赖清单
│
├── .env                                 # [NEW] 环境变量配置文件(含真实系统地址/账号/MQTT参数)
├── .env.example                         # [NEW] 配置模板文件(提交到git的参考)
└── frontend/                            # [已有] Vue3前端(67个文件,少量bug需修复)
    └── src/api/template.ts              # [MODIFY] 修复 import 路径错误 './api/index' → './index'
```

## Implementation Notes

### 关键执行细节

1. **前端 bug 同步修复**: `frontend/src/api/template.ts` 第4行 `import from './api/index'` 应改为 `'./index'`，否则模板页面编译报错
2. **Vite 代理匹配**: vite.config.ts 已配置 `/api` → `localhost:8000` 和 `/ws` → `ws://localhost:8000`，后端路由需与此一致
3. **前端响应格式约定**: 前端拦截器期望 `{code: 20000, message: '', data: {...}}` 格式（见 api/index.ts 第37行），后端所有响应必须包裹此结构
4. **设备列表分页**: 前端 deviceStore 期望 `{total, page, pageSize, items: []}` 分页格式（PaginatedResponse），后端需包装真实系统返回的数据
5. **MQTT TLS**: 真实系统使用 8883 TLS 端口，paho-mqtt 需要配置 tls_set()，开发环境可能需要处理证书验证问题（可先设置 tls_insecure=True 测试）
6. **Session 存储**: 开发阶段使用内存 dict 存储token→{userId,apiKey}映射，无需额外数据库依赖
7. **JWT secret**: 写入 .env，用于签名和验证前端Bearer token
8. **CORS**: 必须允许 `http://localhost:3000` origin

本任务为纯后端 API 开发，不涉及新 UI 创建或现有 UI 大规模改造，因此不输出设计内容。