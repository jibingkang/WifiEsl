"""
认证服务 - 基于数据库的用户登录 + JWT Token管理
- 用户账号密码存储在 SQLite users 表中
- 登录后用配置的WIFI系统凭据代理获取 apiKey
- 生成JWT token给前端
- Session映射仍保留在内存中(可后续迁移到Redis)
"""
import jwt
import time
import logging
import json
from typing import Optional

from config import settings
from services.wifi_client import wifi_proxy
from services.db_service import get_user_by_name, add_log, verify_password
from services.wifi_connection_manager import wifi_connection_manager

logger = logging.getLogger(__name__)

# 内存session存储: {jwt_token_str: session_info_dict}
_sessions: dict[str, dict] = {}


async def proxy_login(username: str, password: str, ip: str = "") -> dict:
    """
    登录流程:
    1. 从数据库验证用户名密码 (SHA-256哈希比对)
    2. 用配置的WIFI系统凭据调用真实API获取 apiKey
    3. 生成JWT token
    4. 记录操作日志
    5. 返回前端期望的格式
    """
    # Step 1: 验证本地用户
    user = await get_user_by_name(username)
    if not user or not verify_password(password, user["password"]):
        await add_log(username, "LOGIN_FAILED", detail="用户名或密码错误", result="failed", ip_address=ip)
        raise ValueError("用户名或密码错误")

    # Step 2: 获取用户的WIFI配置并调用真实WIFI系统登录
    logger.info(f"[AUTH] ========== 开始登录WIFI系统获取JWT token ==========")
    logger.info(f"[AUTH] 本地用户名: {username}")
    
    # 获取用户的WIFI配置（三级继承：自身 → 父用户 → settings全局默认）
    wifi_username = user.get("wifi_username")
    wifi_password = user.get("wifi_password")
    wifi_apikey = user.get("wifi_apikey")
    wifi_base_url = user.get("wifi_base_url")

    # 如果用户自身没有配置，尝试从父用户继承
    if not wifi_username and user.get("parent_user_id"):
        try:
            from services.db_service_extended import get_user_by_id
            parent = await get_user_by_id(user["parent_user_id"])
            if parent:
                wifi_username = parent.get("wifi_username")
                wifi_password = parent.get("wifi_password")
                wifi_apikey = parent.get("wifi_apikey")
                wifi_base_url = parent.get("wifi_base_url")
                if wifi_username:
                    logger.info(f"[AUTH] 从父用户(ID={user['parent_user_id']})继承WIFI配置")
        except Exception as e:
            logger.warning(f"[AUTH] 查询父用户WIFI配置失败: {e}")

    # 最终回退到 settings 全局默认
    wifi_username = wifi_username or settings.wifi_username
    wifi_password = wifi_password or settings.wifi_password
    wifi_apikey = wifi_apikey or settings.wifi_apikey
    wifi_base_url = wifi_base_url or settings.wifi_base_url
    
    # 检查是否使用独立配置
    using_custom_config = bool(user.get("wifi_username"))
    
    if using_custom_config:
        logger.info(f"[AUTH] ✅ 使用用户独立的WIFI配置:")
    else:
        logger.info(f"[AUTH] ⚠️  用户无独立WIFI配置，使用系统默认配置:")
    
    logger.info(f"[AUTH]   WIFI用户名: {wifi_username}")
    logger.info(f"[AUTH]   WIFI密码长度: {len(wifi_password)} 字符")
    logger.info(f"[AUTH]   API Key: {wifi_apikey[:8]}... (长度: {len(wifi_apikey)})")
    logger.info(f"[AUTH]   WIFI地址: {wifi_base_url}")
    
    # 解密WIFI密码（如果是加密存储的）
    decrypted_password = wifi_password
    try:
        # 尝试从db_service导入解密函数
        from services.db_service import decrypt_wifi_password as decrypt_func
        decrypted_password = decrypt_func(wifi_password)
        logger.debug(f"[AUTH]   WIFI密码解密长度: {len(decrypted_password)} 字符")
    except Exception as e:
        logger.debug(f"[AUTH]   WIFI密码解密失败，可能已经是明文: {e}")
        decrypted_password = wifi_password
    
    # 检查是否真的会调用WIFI系统登录
    logger.info(f"[AUTH] 即将调用 wifi_proxy.login()...")
    
    api_key = None
    try:
        wifi_result = await wifi_proxy.login(
            username=wifi_username,
            password=decrypted_password,
            base_url=wifi_base_url,
        )
        
        logger.info(f"[AUTH] ✅ WIFI系统登录调用成功!")
        logger.info(f"[AUTH]   响应类型: {type(wifi_result).__name__}")
        logger.info(f"[AUTH]   响应是否字典: {isinstance(wifi_result, dict)}")
        if isinstance(wifi_result, dict):
            logger.info(f"[AUTH]   响应键: {list(wifi_result.keys())}")
            logger.info(f"[AUTH]   响应数据 (前200字符): {json.dumps(wifi_result, ensure_ascii=False)[:200]}")
        
        wifi_data = wifi_result.get("data", wifi_result) if isinstance(wifi_result, dict) else {}
        
        # 尝试从不同字段获取token
        api_key = (
            wifi_data.get("token")
            or wifi_data.get("apikey")
            or wifi_data.get("apiKey")
            or wifi_data.get("api_key")
        )
        
        if api_key:
            logger.info(f"[AUTH] ✅ 成功获取JWT token")
            logger.info(f"[AUTH]    token开头: {api_key[:8]}...")
            logger.info(f"[AUTH]    token长度: {len(api_key)} 字符")
            logger.info(f"[AUTH]    JWT格式: {'✅ 标准JWT (eyJ开头)' if api_key.startswith('eyJ') else '⚠️  非标准格式'}")
            logger.debug(f"[AUTH]    完整token: {api_key}")
        else:
            logger.warning(f"[AUTH] ❌ 登录响应中没有找到token，无法调用WIFI系统API")
            raise Exception(f"WIFI系统登录失败：未获取到token")
            
        # 注意：这里返回的api_key实际上是WIFI系统登录后返回的token
        # 而用户的wifi_apikey字段只用于MQTT订阅，不用于API调用
            
    except Exception as e:
        import traceback
        logger.error(f"[AUTH] ❌ WIFI系统登录失败: {type(e).__name__}: {e}")
        logger.error(f"[AUTH] 异常堆栈: {traceback.format_exc()}")
        
        # 尝试使用用户配置的 wifi_apikey
        api_key = user.get("wifi_apikey") or settings.wifi_apikey
        if api_key:
            logger.warning(f"[AUTH] 使用配置的 API Key 作为后备继续登录本系统")
        else:
            logger.critical(f"[AUTH] 🚨 严重: 无法获取任何API Key")
            raise ValueError("WIFI系统连接失败，请检查WIFI配置")

    # Step 3: 生成JWT token（包含用户配置信息）
    token = _create_jwt_token(username, api_key, user)

    # Step 4: 存储内存 session（包含WIFI配置）
    _sessions[token] = {
        "username": username,
        "api_key": api_key,
        "role": user.get("role", "operator"),
        "user_id": user.get("id"),
        "wifi_config": {
            "username": wifi_username,
            "apikey": wifi_apikey,
            "base_url": wifi_base_url
        },
        "created_at": time.time(),
        "expires_at": time.time() + settings.jwt_expire_hours * 3600,
    }

    # Step 5: 异步初始化用户的WIFI连接和MQTT（不阻塞登录）
    user_id = user.get("id")
    if user_id:
        # 使用后台任务异步初始化，避免阻塞登录响应
        import asyncio
        asyncio.create_task(
            _init_user_wifi_async(user_id, username, api_key, wifi_username, wifi_password, wifi_apikey, wifi_base_url)
        )
        logger.info(f"[AUTH] 🔄 用户 {username} 的WIFI连接初始化已放入后台任务")

    # Step 6: 记录日志
    await add_log(
        username=username,
        action="LOGIN",
        target_type="auth",
        detail=f"用户 {username} 登录成功",
        ip_address=ip,
    )

    logger.info(f"用户登录成功: {username}")

    return {
        "token": token,
        "expiresIn": settings.jwt_expire_hours * 3600,
        "user": {
            "id": str(user["id"]),
            "username": username,
            "role": user.get("role", "operator"),
            "avatar": user.get("avatar", ""),
            "apiKey": api_key,
        },
    }


def verify_token(token: str) -> tuple[bool, Optional[str]]:
    """验证JWT token有效性 → Returns (is_valid, api_key_or_none)"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])

        session = _sessions.get(token)
        if not session:
            # Session不存在(如重启)，但JWT未过期 → 自动重建session
            api_key_from_jwt = payload.get("api_key")
            if api_key_from_jwt and payload.get("exp", 0) > time.time():
                # 从payload中提取WIFI配置信息

                wifi_config = {
                    "username": payload.get("wifi_username"),
                    "apikey": payload.get("wifi_apikey"),
                    "base_url": payload.get("wifi_base_url", settings.wifi_base_url),
                    "user_id": payload.get("user_id"),
                    "parent_user_id": payload.get("parent_user_id", 0)
                }
                
                _sessions[token] = {
                    "username": payload.get("sub", "unknown"),
                    "api_key": api_key_from_jwt,
                    "role": payload.get("role", "operator"),
                    "created_at": time.time(),
                    "expires_at": payload["exp"],
                    "wifi_config": wifi_config
                }
                logger.info(f"自动重建session: {payload.get('sub')}")
                logger.info(f"   WIFI配置: {wifi_config}")
                return True, api_key_from_jwt
            return False, None

        if time.time() > session["expires_at"]:
            del _sessions[token]
            return False, None

        return True, session["api_key"]

    except jwt.ExpiredSignatureError:
        if token in _sessions:
            del _sessions[token]
        return False, None
    except jwt.InvalidTokenError:
        return False, None


def get_api_key_from_request(request_headers: dict) -> Optional[str]:
    """从请求头提取Bearer token并验证，返回对应的apiKey"""
    auth_header = request_headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    is_valid, api_key = verify_token(token)
    return api_key if is_valid else None


def get_username_from_token(token: str) -> Optional[str]:
    """从token获取用户名(用于审计)"""
    session = _sessions.get(token)
    return session["username"] if session else None


def get_wifi_config_from_token(token: str) -> Optional[dict]:
    """从token获取用户的WIFI配置"""
    session = _sessions.get(token)
    if not session:
        return None
    return session.get("wifi_config")


def get_wifi_config_from_request(request_headers: dict) -> Optional[dict]:
    """从请求头获取用户的WIFI配置"""
    auth_header = request_headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    return get_wifi_config_from_token(token)


def get_current_user_id_from_token(token: str) -> Optional[int]:
    """从token获取当前用户ID"""
    # 首先尝试从session获取
    session = _sessions.get(token)
    if session and session.get("user_id"):
        return session.get("user_id")
    
    # 如果session中没有，尝试从JWT token的payload中获取
    try:
        import jwt
        from config import settings
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id:
            # 尝试将字符串转换为整数
            return int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        
        # 如果token中没有user_id，尝试通过用户名查找
        username = payload.get("sub")
        if username:
            from services.db_service import get_user_by_name
            import asyncio
            
            # 注意：这里需要异步调用，但函数是同步的
            # 创建一个新的事件循环来运行异步函数
            try:
                user = asyncio.run(get_user_by_name(username))
                if user:
                    return user.get("id")
            except:
                # 如果异步调用失败，返回None
                pass
        
        return None
    except Exception as e:
        logger.error(f"从token解析用户ID失败: {e}")
        return None


def _create_jwt_token(username: str, api_key: str, user_info: dict = None) -> str:
    """生成JWT token"""
    payload = {
        "sub": username,
        "api_key": api_key,
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.jwt_expire_hours * 3600,
        "role": user_info.get("role", "admin") if user_info else "admin",
    }
    
    # 如果提供了用户信息，添加更多字段
    if user_info:
        # 添加WIFI配置信息
        if user_info.get("wifi_username"):
            payload["wifi_username"] = user_info.get("wifi_username")
            payload["wifi_apikey"] = user_info.get("wifi_apikey", "")
            payload["wifi_base_url"] = user_info.get("wifi_base_url", settings.wifi_base_url)
        
        # 添加用户ID
        if user_info.get("id"):
            payload["user_id"] = str(user_info["id"])
        
        # 添加父用户ID（用于权限管理）
        if user_info.get("parent_user_id"):
            payload["parent_user_id"] = user_info.get("parent_user_id")
    
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def cleanup_expired_sessions():
    """清理过期session"""
    now = time.time()
    expired_tokens = [t for t, s in _sessions.items() if now > s.get("expires_at", 0)]
    for t in expired_tokens:
        del _sessions[t]
    if expired_tokens:
        logger.info(f"清理了 {len(expired_tokens)} 个过期session")


async def _init_user_wifi_async(
    user_id: int,
    username: str,
    api_key: str,
    wifi_username: str,
    wifi_password: str,
    wifi_apikey: str,
    wifi_base_url: str
):
    """
    后台异步初始化用户的WIFI连接和MQTT
    不阻塞登录流程，失败时记录日志但不影响用户登录
    """
    try:
        logger.info(f"[AUTH] 🔄 [后台] 开始初始化用户 {username} 的WIFI连接...")
        
        # 设置较短的超时时间，避免长时间阻塞
        import asyncio
        
        # 尝试获取WIFI连接（带超时）
        try:
            conn = await asyncio.wait_for(
                wifi_connection_manager.get_connection(user_id),
                timeout=10.0  # 10秒超时
            )
            if conn and conn.token:
                logger.info(f"[AUTH] ✅ [后台] 用户 {username} 的WIFI连接已初始化")
            else:
                logger.warning(f"[AUTH] ⚠️  [后台] 用户 {username} 的WIFI连接初始化失败，token为空")
                return
        except asyncio.TimeoutError:
            logger.warning(f"[AUTH] ⏱️  [后台] 用户 {username} 的WIFI连接初始化超时，将在后续操作重试")
            return
        
        # 启动MQTT连接（带超时）
        try:
            from services.multi_user_mqtt_manager import multi_user_mqtt_manager
            mqtt_started = await asyncio.wait_for(
                multi_user_mqtt_manager.start_user_connection(user_id),
                timeout=10.0
            )
            if mqtt_started:
                logger.info(f"[AUTH] ✅ [后台] 用户 {username} 的MQTT连接已启动")
            else:
                logger.warning(f"[AUTH] ⚠️  [后台] 用户 {username} 的MQTT连接启动失败")
        except asyncio.TimeoutError:
            logger.warning(f"[AUTH] ⏱️  [后台] 用户 {username} 的MQTT连接启动超时")
        except Exception as e:
            logger.error(f"[AUTH] ❌ [后台] 用户 {username} 的MQTT连接启动异常: {e}")
            
    except Exception as e:
        logger.error(f"[AUTH] ❌ [后台] 初始化用户 {username} 的WIFI连接失败: {e}")
