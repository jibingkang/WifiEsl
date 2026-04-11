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
from typing import Optional

from config import settings
from services.wifi_client import wifi_proxy
from services.db_service import get_user_by_name, add_log, verify_password

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

    # Step 2: 调用真实WIFI系统登录获取 apiKey
    try:
        wifi_result = await wifi_proxy.login(
            username=settings.wifi_username,
            password=settings.wifi_password,
        )
        wifi_data = wifi_result.get("data", wifi_result) if isinstance(wifi_result, dict) else {}
        api_key = (
            wifi_data.get("token")
            or wifi_data.get("apikey")
            or wifi_data.get("apiKey")
            or wifi_data.get("api_key")
            or settings.wifi_apikey
        )
    except Exception as e:
        logger.error(f"WIFI系统登录失败(不影响本地认证): {e}")
        api_key = settings.wifi_apikey

    # Step 3: 生成JWT token
    token = _create_jwt_token(username, api_key)

    # Step 4: 存储内存 session
    _sessions[token] = {
        "username": username,
        "api_key": api_key,
        "role": user.get("role", "operator"),
        "created_at": time.time(),
        "expires_at": time.time() + settings.jwt_expire_hours * 3600,
    }

    # Step 5: 记录日志
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
            "role": user.get("role", "admin"),
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
                _sessions[token] = {
                    "username": payload.get("sub", "unknown"),
                    "api_key": api_key_from_jwt,
                    "role": payload.get("role", "operator"),
                    "created_at": time.time(),
                    "expires_at": payload["exp"],
                }
                logger.info(f"自动重建session: {payload.get('sub')}")
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


def _create_jwt_token(username: str, api_key: str) -> str:
    """生成JWT token"""
    payload = {
        "sub": username,
        "api_key": api_key,
        "iat": int(time.time()),
        "exp": int(time.time()) + settings.jwt_expire_hours * 3600,
        "role": "admin",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def cleanup_expired_sessions():
    """清理过期session"""
    now = time.time()
    expired_tokens = [t for t, s in _sessions.items() if now > s.get("expires_at", 0)]
    for t in expired_tokens:
        del _sessions[t]
    if expired_tokens:
        logger.info(f"清理了 {len(expired_tokens)} 个过期session")
