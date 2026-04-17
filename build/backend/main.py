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
# 确保日志目录存在（使用相对路径，兼容 Windows 和 Docker）
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'wifi_esl_debug.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)

# 设置httpx的日志级别为DEBUG
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("WIFI标签管理系统启动，日志级别: INFO")

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
    from services.multi_user_mqtt_manager import multi_user_mqtt_manager
    from services.mqtt_service import set_main_loop
    from services.ws_manager import ws_manager
    import asyncio

    print("[Startup] lifespan 开始执行...")
    
    # 0. 绑定当前事件循环供MQTT线程使用 (修复跨线程WS广播)
    print("[Startup] 设置主事件循环...")
    set_main_loop(asyncio.get_running_loop())
    print("[Startup] 主事件循环设置完成")
    
    # 设置多用户MQTT管理器的主事件循环
    print("[Startup] 设置MQTT管理器事件循环...")
    multi_user_mqtt_manager.set_main_loop(asyncio.get_running_loop())
    print("[Startup] MQTT管理器事件循环设置完成")

    # 1. 初始化数据库 (建表+种子数据)
    print("[Startup] 正在初始化数据库...")
    import time
    start = time.time()
    await init_db()
    print(f"[Startup] 数据库初始化完成，耗时: {time.time() - start:.2f}s")

    yield

    # 关闭所有连接
    print("[Shutdown] 正在关闭服务...")
    await multi_user_mqtt_manager.stop_all()
    await ws_manager.close()
    await close_db()


# 创建FastAPI应用实例
app = FastAPI(
    title="WIFI标签管理系统",
    description="智能电子价签控制平台 - 后端API服务",
    version="1.0.0",
    lifespan=lifespan,
)

# ========== CORS 跨域配置 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 注意：CORS中间件对WebSocket不生效，WebSocket需要单独处理跨域

# ========== WebSocket 连接日志 ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    # WebSocket 请求不经过此中间件处理，直接放行
    if "/ws/" in str(request.url):
        logger.info(f"[WS] 收到WebSocket请求: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"[WS] WebSocket响应: {response.status_code}")
        return response
    response = await call_next(request)
    return response

# ========== 全局异常处理 ==========
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": f"服务器内部错误: {str(exc)}", "data": None},
    )


# ========== WebSocket端点 ==========
from fastapi import WebSocket
from services.ws_manager import ws_endpoint

@app.websocket("/ws/device-status")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点 - 实时设备状态推送
    
    注意：FastAPI默认会检查Origin头，如果前端运行在3001端口，
    WebSocket连接8001端口，会被认为是跨域请求。
    我们在CORS中间件中允许了所有来源，但WebSocket需要单独处理。
    """
    # 手动接受WebSocket连接，不检查Origin
    try:
        # 先接受连接
        await websocket.accept()
        logger.info(f"[WS] WebSocket连接已接受 from {websocket.client}")
        # 然后处理业务逻辑
        await ws_endpoint(websocket)
    except Exception as e:
        logger.error(f"[WS] WebSocket处理异常: {e}")
        raise


# ========== 注册路由 ==========
app.include_router(auth_router, prefix="/api/v1", tags=["认证"])
app.include_router(devices_router, prefix="/api/v1", tags=["设备管理"])
app.include_router(control_router, prefix="/api/v1", tags=["设备控制"])
app.include_router(template_router, prefix="/api/v1", tags=["模板管理"])
app.include_router(batch_router, prefix="/api/v1", tags=["批量操作"])
app.include_router(tasks_router, prefix="/api/v1", tags=["更新任务"])
app.include_router(update_history_router, prefix="/api/v1", tags=["更新历史"])
app.include_router(settings_router, prefix="/api/v1", tags=["系统设置"])

# 导入并注册用户管理API
try:
    from api.users import router as users_router
    app.include_router(users_router, prefix="/api/v1", tags=["用户管理"])
    logger.info("用户管理API已注册")
except Exception as e:
    logger.error(f"用户管理API注册失败: {e}")

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
