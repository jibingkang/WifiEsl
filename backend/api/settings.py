"""
系统设置 API - 管理员增删改查系统配置项
提供 WIFI/MQTT/JWT 等配置的持久化管理接口
"""
import logging
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field

from services.auth_service import get_api_key_from_request
from services.db_service import (
    get_config, get_config_category, set_config, set_configs,
    get_all_users, create_user, update_user, delete_user, get_logs,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# 请求/响应模型
# ============================================================

class ConfigItem(BaseModel):
    key: str
    value: str
    description: str = ""


class BatchConfigUpdate(BaseModel):
    configs: dict[str, str]


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=6, max_length=30)
    role: str = "operator"


class UpdateUserRequest(BaseModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None


# ============================================================
# 辅助: 从请求提取用户信息
# ============================================================

def _get_current_user(request: Request) -> str:
    """从请求头获取当前用户名"""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return "unknown"
    token = auth[7:]
    from services.auth_service import get_username_from_token
    return get_username_from_token(token) or "unknown"


# ────────────────────────────────────────
# 配置管理接口
# ────────────────────────────────────────

@router.get("/settings")
async def list_all_settings():
    """获取所有系统配置 (按分类分组)"""
    data = await get_config()
    return {"code": 20000, "message": "", "data": data}


@router.get("/settings/category/{category}")
async def get_settings_by_category(category: str):
    """获取指定分类的配置"""
    data = await get_config_category(category)
    return {"code": 20000, "message": "", "data": data}


@router.put("/settings/{key}")
async def update_single_setting(key: str, item: ConfigItem, request: Request):
    """修改单个配置项"""
    user = _get_current_user(request)
    await set_config(key, item.value, updated_by=user)
    await add_log(user, "UPDATE_CONFIG", target_id=key, detail=f"修改配置 {key}", ip_address=request.client.host if request.client else "")
    return {"code": 20000, "message": f"配置 {key} 已更新", "data": None}


@router.put("/settings")
async def batch_update_settings(body: BatchConfigUpdate, request: Request):
    """批量修改配置项"""
    user = _get_current_user(request)
    await set_configs(body.configs, updated_by=user)
    keys = ", ".join(body.configs.keys())
    await add_log(user, "UPDATE_CONFIG", detail=f"批量修改配置: {keys}", ip_address=request.client.host if request.client else "")
    return {"code": 20000, "message": f"已更新 {len(body.configs)} 项配置", "data": None}


# ────────────────────────────────────────
# 用户管理接口
# ────────────────────────────────────────

@router.get("/users")
async def list_users():
    """获取用户列表(不含密码)"""
    users = await get_all_users()
    return {"code": 20000, "message": "", "data": users}


@router.post("/users")
async def create_new_user(req: CreateUserRequest, request: Request):
    """创建新用户"""
    user = _get_current_user(request)
    try:
        uid = await create_user(req.username, req.password, req.role)
        await add_log(user, "CREATE_USER", target_type="user", target_id=str(uid), detail=f"创建用户 {req.username}({req.role})", ip_address=request.client.host if request.client else "")
        return {"code": 20000, "message": "用户创建成功", "data": {"id": uid}}
    except Exception as e:
        return {"code": 50000, "message": str(e), "data": None}


@router.put("/users/{user_id}")
async def update_existing_user(user_id: int, req: UpdateUserRequest, request: Request):
    """更新用户信息"""
    user = _get_current_user(request)
    kwargs = {}
    if req.username is not None:
        kwargs["username"] = req.username
    if req.password is not None:
        kwargs["password"] = req.password
    if req.role is not None:
        kwargs["role"] = req.role
    if kwargs:
        await update_user(user_id, **kwargs)
        await add_log(user, "UPDATE_USER", target_type="user", target_id=str(user_id), detail=f"修改用户信息", ip_address=request.client.host if request.client else "")
    return {"code": 20000, "message": "用户信息已更新", "data": None}


@router.delete("/users/{user_id}")
async def remove_user(user_id: int, request: Request):
    """删除/禁用用户"""
    user = _get_current_user(request)
    await delete_user(user_id)
    await add_log(user, "DELETE_USER", target_type="user", target_id=str(user_id), detail=f"禁用用户 ID={user_id}", ip_address=request.client.host if request.client else "")
    return {"code": 20000, "message": "用户已禁用", "data": None}


# ────────────────────────────────────────
# 操作日志接口
# ────────────────────────────────────────

@router.get("/logs")
async def query_logs(page: int = 1, page_size: int = 20, action: str = ""):
    """分页查询操作日志"""
    items, total = await get_logs(page=page, page_size=page_size, action=action)
    return {
        "code": 20000,
        "message": "",
        "data": {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "items": items,
        },
    }
