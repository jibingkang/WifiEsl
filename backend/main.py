"""
WIFI标签管理系统 - FastAPI 应用入口
"""
import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 确保项目根目录在路径中（用于加载 .env）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置全局日志级别（DEBUG级别显示所有日志）
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('wifi_esl_debug.log', encoding='utf-8')
    ]
)

# 设置httpx的日志级别为DEBUG
logging.getLogger("httpx").setLevel(logging.DEBUG)
logging.getLogger("httpcore").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info("WIFI标签管理系统启动，日志级别: DEBUG")

from config import settings

from api.auth import router as auth_router
from api.devices import router as devices_router
from api.control import router as control_router
from api.template import router as template_router, history_router as update_history_router
from api.batch import router as batch_router
from api.tasks import router as tasks_router
from api.settings import router as settings_router
from api.websocket import ws_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理: 初始化数据库 → 启动MQTT → 关闭时清理"""
    from services.db_service import init_db, close_db
    from services.mqtt_service import mqtt_manager, set_main_loop
    from services.ws_manager import ws_manager
    import asyncio

    # 0. 绑定当前事件循环供MQTT线程使用 (修复跨线程WS广播)
    set_main_loop(asyncio.get_running_loop())

    # 1. 初始化数据库 (建表+种子数据)
    print("[Startup] 正在初始化数据库...")
    await init_db()

    # 2. 启动 MQTT 连接
    print("[Startup] 正在连接 MQTT Broker...")
    await mqtt_manager.start()

    yield

    # 关闭所有连接
    print("[Shutdown] 正在关闭服务...")
    await mqtt_manager.stop()
    await ws_manager.close()
    await close_db()


# 创建FastAPI应用实例
app = FastAPI(
    title="WIFI标签管理系统",
    description="智能电子价签控制平台 - 后端API服务",
    version="1.0.0",
    lifespan=lifespan,
)

# ========== CORS 跨域配置 (开发环境暂时禁用) ==========
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# ========== 全局异常处理 ==========
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": f"服务器内部错误: {str(exc)}", "data": None},
    )


# ========== 原生ASGI WebSocket端点 (绕过中间件) ==========
from starlette.websockets import WebSocketDisconnect

async def ws_device_status_handler(ws):
    """Starlette WebSocketRoute 直接接收 WebSocket 对象"""
    from services.ws_manager import ws_manager
    from services.mqtt_service import mqtt_manager
    import time, json

    cid = None
    
    try:
        await ws.accept()
        cid = await ws_manager.connect(ws)
        print(f"[WS] ✅ 连接成功: {cid}")

        await ws.send_json({
            "type": "connected",
            "data": {"connection_id": cid, "mqtt_connected": mqtt_manager.connected},
            "timestamp": time.time(),
        })

        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await ws.send_json({"type": "pong", "timestamp": time.time()})

    except Exception as e:
        print(f"[WS] 异常: {e}")
    finally:
        if cid:
            await ws_manager.disconnect(cid)


# 将WS端点注册到路由表最前面（不经过中间件）
from starlette.routing import WebSocketRoute
app.router.routes.insert(0, WebSocketRoute("/ws/device-status", ws_device_status_handler))


# ========== 注册路由 ==========
app.include_router(auth_router, prefix="/api/v1", tags=["认证"])
app.include_router(devices_router, prefix="/api/v1", tags=["设备管理"])
app.include_router(control_router, prefix="/api/v1", tags=["设备控制"])
app.include_router(template_router, prefix="/api/v1", tags=["模板管理"])
app.include_router(batch_router, prefix="/api/v1", tags=["批量操作"])
app.include_router(tasks_router, prefix="/api/v1", tags=["更新任务"])
app.include_router(update_history_router, prefix="/api/v1", tags=["更新历史"])
app.include_router(settings_router, prefix="/api/v1", tags=["系统设置"])

# WebSocket 端点 (已通过 add_websocket_route 注册在上方)


# ========== 健康检查 ==========
@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "service": "wifi-esl-manager"}


@app.get("/", tags=["系统"])
async def root():
    return {"message": "WIFI标签管理系统后端服务运行中", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
