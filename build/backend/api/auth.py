"""
认证API - 登录认证代理
POST /api/v1/auth/login → 代理到真实WIFI系统登录，返回JWT
"""
from fastapi import APIRouter, Request
from services.auth_service import proxy_login, verify_token

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
async def login(request: Request, body: dict):
    """
    用户登录 (认证代理)
    前端提交 {username, password}
    后端代理到真实WIFI系统获取apiKey, 颁发JWT返回给前端
    """
    username = body.get("username", "")
    password = body.get("password", "")

    if not username or not password:
        return {"code": 40000, "message": "用户名和密码不能为空", "data": None}

    try:
        result = await proxy_login(username, password)
        return {
            "code": 20000,
            "message": "登录成功",
            "data": result,
        }
    except Exception as e:
        return {
            "code": 40001,
            "message": f"登录失败: {str(e)}",
            "data": None,
        }


@router.get("/userinfo")
async def get_userinfo(request: Request):
    """获取当前用户信息"""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    if not token:
        return {"code": 40100, "message": "未登录", "data": None}

    is_valid, _ = verify_token(token)
    if not is_valid:
        return {"code": 40101, "message": "Token已过期或无效", "data": None}

    # 从JWT payload中解析真实角色和用户名
    try:
        import jwt as pyjwt
        from config import settings
        payload = pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        role = payload.get("role", "operator")
        username = payload.get("sub", "")
        user_id = payload.get("user_id")
    except Exception:
        role = "operator"
        username = ""
        user_id = None

    return {
        "code": 20000,
        "message": "",
        "data": {"role": role, "username": username, "id": user_id},
    }


@router.post("/logout")
async def logout(request: Request):
    """登出（清理session）"""
    from services.auth_service import _sessions

    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    if token and token in _sessions:
        del _sessions[token]

    return {"code": 20000, "message": "已退出登录", "data": None}


@router.get("/profile")
async def get_profile(request: Request):
    """获取当前用户完整信息（含WIFI配置摘要）"""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    if not token:
        return {"code": 40100, "message": "未登录", "data": None}

    is_valid, _ = verify_token(token)
    if not is_valid:
        return {"code": 40101, "message": "Token已过期或无效", "data": None}

    # 从JWT payload中获取用户ID
    try:
        import jwt as pyjwt
        from config import settings
        payload = pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except Exception:
        user_id = None

    if not user_id:
        return {"code": 40100, "message": "无效的用户信息", "data": None}

    # 从数据库获取完整用户信息
    from services.db_service_extended import get_user_with_details
    user = await get_user_with_details(user_id)
    if not user:
        return {"code": 40400, "message": "用户不存在", "data": None}

    # 安全：移除敏感信息
    if "password" in user:
        user["password"] = "***"
    if "wifi_password" in user:
        user["wifi_password"] = "***"

    return {
        "code": 20000,
        "message": "",
        "data": user,
    }
