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

    return {
        "code": 20000,
        "message": "",
        "data": {"role": "admin"},
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
