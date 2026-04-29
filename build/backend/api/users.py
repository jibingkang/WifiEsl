"""
用户管理API - 多用户支持
管理员可以创建、修改、删除子账号
"""
import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from services.db_service_extended import (
    create_user_with_wifi_config,
    update_user_wifi_config,
    get_user_wifi_config,
    get_users_by_parent,
    list_all_users,
    get_user_with_details
)
from services.auth_service import get_api_key_from_request, verify_token
from services.db_service import get_user_by_name, update_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["用户管理"])

# ============================================================
# 数据模型
# ============================================================

class CreateUserRequest(BaseModel):
    """创建用户请求体"""
    username: str
    password: str
    role: str = "operator"
    wifi_username: Optional[str] = None
    wifi_password: Optional[str] = None
    wifi_apikey: Optional[str] = None
    wifi_base_url: Optional[str] = None
    wifi_mqtt_broker: Optional[str] = None  # MQTT broker地址
    mqtt_username: Optional[str] = None     # MQTT用户名
    mqtt_password: Optional[str] = None     # MQTT密码

class UpdateUserRequest(BaseModel):
    """更新用户请求体"""
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    wifi_username: Optional[str] = None
    wifi_password: Optional[str] = None
    wifi_apikey: Optional[str] = None
    wifi_base_url: Optional[str] = None
    wifi_mqtt_broker: Optional[str] = None  # MQTT broker地址
    mqtt_username: Optional[str] = None     # MQTT用户名
    mqtt_password: Optional[str] = None     # MQTT密码

class UserResponse(BaseModel):
    """用户响应体"""
    id: int
    username: str
    role: str
    avatar: Optional[str] = None
    status: str
    wifi_username: Optional[str] = None
    wifi_base_url: Optional[str] = None
    parent_user_id: int
    created_by: int
    created_at: str
    updated_at: str

# ============================================================
# 权限验证辅助函数
# ============================================================

async def get_current_user_id(request: Request) -> int:
    """获取当前用户ID"""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    
    is_valid, api_key = verify_token(token)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Token已过期或无效")
    
    # 从token的payload中获取用户ID
    try:
        import jwt
        from config import settings
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            # 如果token中没有user_id，尝试通过用户名查找
            username = payload.get("sub")
            if username:
                user = await get_user_by_name(username)
                if user:
                    return user.get("id", 0)
            return 0
        return int(user_id)
    except Exception as e:
        logger.error(f"解析用户ID失败: {e}")
        return 0

async def get_current_user_role(request: Request) -> str:
    """获取当前用户角色"""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    
    if not token:
        return ""
    
    try:
        import jwt
        from config import settings
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        role = payload.get("role", "")
        
        # 如果token中没有role，尝试从数据库获取
        if not role:
            username = payload.get("sub")
            if username:
                user = await get_user_by_name(username)
                if user:
                    role = user.get("role", "")
        
        return role
    except Exception as e:
        logger.error(f"获取用户角色失败: {e}")
        return ""

def check_admin_permission(role: str) -> bool:
    """检查是否是管理员权限"""
    return role in ["admin", "super_admin"]

# ============================================================
# 用户管理API
# ============================================================

@router.get("")
async def get_user_list(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    keyword: str = "",  # 兼容前端参数名
    role: str = "",
    status: str = "",
    parent_user_id: int = 0
):
    """获取用户列表"""
    current_user_id = await get_current_user_id(request)
    current_user_role = await get_current_user_role(request)
    
    if not current_user_id:
        return {"code": 40100, "message": "未登录", "data": None}
    
    try:
        # 根据角色决定返回哪些用户
        if check_admin_permission(current_user_role):
            # 管理员：可以查看所有用户
            all_users = await list_all_users()
            users = all_users
            logger.info(f"管理员 {current_user_id} ({current_user_role}) 查看所有用户: {len(users)} 个")
        else:
            # 普通用户：只能查看自己创建的子用户
            users = await get_users_by_parent(current_user_id)
            logger.info(f"普通用户 {current_user_id} ({current_user_role}) 查看子用户: {len(users)} 个")
            # 普通用户也应该能看到自己
            try:
                from services.db_service_extended import get_user_with_details
                current_user_info = await get_user_with_details(current_user_id)
                if current_user_info:
                    # 安全：移除敏感信息
                    if "password" in current_user_info:
                        current_user_info["password"] = "***"
                    if "wifi_password" in current_user_info:
                        current_user_info["wifi_password"] = "***"
                    users.append(current_user_info)
            except Exception as e:
                logger.error(f"获取当前用户信息失败: {e}")
        
        # 应用搜索过滤（兼容search和keyword）
        search_term = search or keyword
        if search_term:
            search_lower = search_term.lower()
            users = [
                u for u in users
                if search_lower in u.get("username", "").lower()
                or search_lower in u.get("wifi_username", "").lower()
            ]
        
        # 应用角色过滤
        if role:
            users = [u for u in users if u.get("role") == role]
        
        # 应用状态过滤
        if status:
            users = [u for u in users if u.get("status") == status]
        
        # 应用父用户ID过滤（如果提供）
        if parent_user_id > 0:
            users = [u for u in users if u.get("parent_user_id") == parent_user_id]
        
        # 分页处理
        total = len(users)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_users = users[start_idx:end_idx]
        
        # 安全：移除敏感信息
        for user in paginated_users:
            if "password" in user:
                del user["password"]
            if "wifi_password" in user:
                del user["wifi_password"]
        
        return {
            "code": 20000,
            "message": "",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": paginated_users
            }
        }
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        return {"code": 50000, "message": f"获取用户列表失败: {str(e)}", "data": None}

@router.get("/{user_id}")
async def get_user_detail(
    request: Request,
    user_id: int
):
    """获取用户详情"""
    current_user_id = await get_current_user_id(request)
    current_user_role = await get_current_user_role(request)
    
    if not current_user_id:
        return {"code": 40100, "message": "未登录", "data": None}
    
    try:
        # 获取目标用户信息
        target_user = await get_user_with_details(user_id)
        if not target_user:
            return {"code": 40400, "message": "用户不存在", "data": None}
        
        # 权限检查
        if not check_admin_permission(current_user_role):
            # 普通用户只能查看自己创建的子用户
            if target_user.get("created_by") != current_user_id:
                return {"code": 40300, "message": "无权查看该用户信息", "data": None}
        
        # 安全：移除敏感信息
        if "password" in target_user:
            target_user["password"] = "***"
        if "wifi_password" in target_user:
            target_user["wifi_password"] = "***"
        
        return {
            "code": 20000,
            "message": "",
            "data": target_user
        }
        
    except Exception as e:
        logger.error(f"获取用户详情失败: {e}")
        return {"code": 50000, "message": f"获取用户详情失败: {str(e)}", "data": None}

@router.post("")
async def create_user(
    request: Request,
    user_data: CreateUserRequest
):
    """创建新用户"""
    current_user_id = await get_current_user_id(request)
    current_user_role = await get_current_user_role(request)
    
    if not current_user_id:
        return {"code": 40100, "message": "未登录", "data": None}
    
    if not check_admin_permission(current_user_role):
        return {"code": 40300, "message": "无权创建用户", "data": None}
    
    try:
        # 检查用户名是否已存在
        existing_user = await get_user_by_name(user_data.username)
        if existing_user:
            return {"code": 40001, "message": "用户名已存在", "data": None}
        
        # 创建用户
        new_user_id = await create_user_with_wifi_config(
            username=user_data.username,
            password=user_data.password,
            role=user_data.role,
            wifi_username=user_data.wifi_username,
            wifi_password=user_data.wifi_password,
            wifi_apikey=user_data.wifi_apikey,
            wifi_base_url=user_data.wifi_base_url,
            wifi_mqtt_broker=user_data.wifi_mqtt_broker,
            mqtt_username=user_data.mqtt_username,
            mqtt_password=user_data.mqtt_password,
            parent_user_id=current_user_id,
            created_by=current_user_id
        )
        
        # 获取新用户的完整信息
        new_user = await get_user_with_details(new_user_id)
        
        # 记录操作日志
        logger.info(f"用户 {current_user_id} 创建了新用户: {user_data.username} (ID: {new_user_id})")
        
        return {
            "code": 20000,
            "message": "创建用户成功",
            "data": new_user
        }
        
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        return {"code": 50000, "message": f"创建用户失败: {str(e)}", "data": None}

@router.put("/{user_id}")
async def update_user_info(
    request: Request,
    user_id: int,
    user_data: UpdateUserRequest
):
    """更新用户信息"""
    current_user_id = await get_current_user_id(request)
    current_user_role = await get_current_user_role(request)
    
    if not current_user_id:
        return {"code": 40100, "message": "未登录", "data": None}
    
    try:
        # 获取目标用户信息
        target_user = await get_user_with_details(user_id)
        if not target_user:
            return {"code": 40400, "message": "用户不存在", "data": None}
        
        # 权限检查
        if not check_admin_permission(current_user_role):
            # 普通用户只能修改自己创建的子用户
            if target_user.get("created_by") != current_user_id:
                return {"code": 40300, "message": "无权修改该用户信息", "data": None}
        
        # 如果需要更新本地用户信息
        update_fields = {}
        if user_data.username is not None:
            update_fields["username"] = user_data.username
        if user_data.password is not None:
            update_fields["password"] = user_data.password
        if user_data.role is not None:
            update_fields["role"] = user_data.role
        
        if update_fields:
            await update_user(user_id, **update_fields)
        
        # 如果需要更新WIFI配置
        wifi_updated = False
        if any([
            user_data.wifi_username is not None,
            user_data.wifi_password is not None,
            user_data.wifi_apikey is not None,
            user_data.wifi_base_url is not None,
            user_data.wifi_mqtt_broker is not None,
            user_data.mqtt_username is not None,
            user_data.mqtt_password is not None
        ]):
            wifi_updated = await update_user_wifi_config(
                user_id=user_id,
                wifi_username=user_data.wifi_username,
                wifi_password=user_data.wifi_password,
                wifi_apikey=user_data.wifi_apikey,
                wifi_base_url=user_data.wifi_base_url,
                wifi_mqtt_broker=user_data.wifi_mqtt_broker,
                mqtt_username=user_data.mqtt_username,
                mqtt_password=user_data.mqtt_password,
                updated_by=current_user_id
            )
        
        # 记录操作日志
        logger.info(f"用户 {current_user_id} 更新了用户 {user_id} 的信息")
        
        return {
            "code": 20000,
            "message": "更新用户信息成功",
            "data": {
                "user_id": user_id,
                "basic_info_updated": bool(update_fields),
                "wifi_config_updated": wifi_updated
            }
        }
        
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        return {"code": 50000, "message": f"更新用户信息失败: {str(e)}", "data": None}

@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: int
):
    """删除用户（硬删除）"""
    current_user_id = await get_current_user_id(request)
    current_user_role = await get_current_user_role(request)
    
    if not current_user_id:
        return {"code": 40100, "message": "未登录", "data": None}
    
    try:
        # 获取目标用户信息
        target_user = await get_user_with_details(user_id)
        if not target_user:
            return {"code": 40400, "message": "用户不存在", "data": None}
        
        # 权限检查
        if not check_admin_permission(current_user_role):
            # 普通用户只能删除自己创建的子用户
            if target_user.get("created_by") != current_user_id:
                return {"code": 40300, "message": "无权删除该用户", "data": None}
        
        # 不能删除自己
        if user_id == current_user_id:
            return {"code": 40002, "message": "不能删除自己", "data": None}
        
        # 硬删除：从数据库中删除用户及其关联数据
        from services.db_service import hard_delete_user
        deleted = await hard_delete_user(user_id)
        
        if not deleted:
            return {"code": 50000, "message": "删除用户失败", "data": None}
        
        # 记录操作日志
        logger.info(f"用户 {current_user_id} 删除了用户 {user_id}")
        
        return {
            "code": 20000,
            "message": "用户已删除",
            "data": {"user_id": user_id}
        }
        
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        return {"code": 50000, "message": f"删除用户失败: {str(e)}", "data": None}

@router.get("/{user_id}/wifi-config")
async def get_user_wifi_config_api(
    request: Request,
    user_id: int
):
    """获取用户的WIFI配置（用户只能查看自己和自己创建的子用户的配置）"""
    current_user_id = await get_current_user_id(request)
    current_user_role = await get_current_user_role(request)
    
    if not current_user_id:
        return {"code": 40100, "message": "未登录", "data": None}
    
    try:
        # 获取目标用户信息
        target_user = await get_user_with_details(user_id)
        if not target_user:
            return {"code": 40400, "message": "用户不存在", "data": None}
        
        # 权限检查：用户可以查看自己，或者自己创建的子用户
        # 管理员可以查看所有用户
        is_admin = check_admin_permission(current_user_role)
        is_self = current_user_id == user_id
        is_created_by_me = target_user.get("created_by") == current_user_id
        
        if not (is_admin or is_self or is_created_by_me):
            return {"code": 40300, "message": "无权查看该用户的WIFI配置", "data": None}
        
        # 获取WIFI配置
        wifi_config = await get_user_wifi_config(user_id)
        
        # 安全：处理密码字段
        if "wifi_password_decrypted" in wifi_config:
            # 保留wifi_password字段，但设置为星号
            wifi_config["wifi_password"] = "***"
            del wifi_config["wifi_password_decrypted"]
        elif "wifi_password" in wifi_config and wifi_config["wifi_password"]:
            # 如果只有加密的密码，也设置为星号
            wifi_config["wifi_password"] = "***"
        
        # 返回真实的API Key给授权用户查看
        # 但为了安全，也提供一个星号版本用于显示
        if "wifi_apikey" in wifi_config and wifi_config["wifi_apikey"]:
            real_apikey = wifi_config["wifi_apikey"]
            # 显示前4个字符和星号
            wifi_config["wifi_apikey_display"] = real_apikey[:4] + "****" if len(real_apikey) > 4 else "****"
        else:
            wifi_config["wifi_apikey_display"] = ""
        
        return {
            "code": 20000,
            "message": "",
            "data": wifi_config
        }
        
    except Exception as e:
        logger.error(f"获取用户WIFI配置失败: {e}")
        return {"code": 50000, "message": f"获取用户WIFI配置失败: {str(e)}", "data": None}


@router.put("/{user_id}/wifi-config")
async def update_user_wifi_config_api(
    request: Request,
    user_id: int,
    user_data: UpdateUserRequest
):
    """更新用户的WIFI配置"""
    current_user_id = await get_current_user_id(request)
    current_user_role = await get_current_user_role(request)
    
    if not current_user_id:
        return {"code": 40100, "message": "未登录", "data": None}
    
    try:
        # 获取目标用户信息
        target_user = await get_user_with_details(user_id)
        if not target_user:
            return {"code": 40400, "message": "用户不存在", "data": None}
        
        # 权限检查：用户可以修改自己，或者自己创建的子用户
        # 管理员可以修改所有用户
        is_admin = check_admin_permission(current_user_role)
        is_self = current_user_id == user_id
        is_created_by_me = target_user.get("created_by") == current_user_id
        
        if not (is_admin or is_self or is_created_by_me):
            return {"code": 40300, "message": "无权修改该用户的WIFI配置", "data": None}
        
        # 更新WIFI配置
        wifi_updated = await update_user_wifi_config(
            user_id=user_id,
            wifi_username=user_data.wifi_username,
            wifi_password=user_data.wifi_password,
            wifi_apikey=user_data.wifi_apikey,
            wifi_base_url=user_data.wifi_base_url,
            wifi_mqtt_broker=user_data.wifi_mqtt_broker,
            updated_by=current_user_id
        )
        
        if not wifi_updated:
            return {"code": 50000, "message": "更新WIFI配置失败", "data": None}
        
        # 获取更新后的WIFI配置
        wifi_config = await get_user_wifi_config(user_id)
        
        # 安全：处理密码字段
        if "wifi_password_decrypted" in wifi_config:
            # 保留wifi_password字段，但设置为星号
            wifi_config["wifi_password"] = "***"
            del wifi_config["wifi_password_decrypted"]
        elif "wifi_password" in wifi_config and wifi_config["wifi_password"]:
            # 如果只有加密的密码，也设置为星号
            wifi_config["wifi_password"] = "***"
        
        # 返回真实的API Key给授权用户查看
        # 但为了安全，也提供一个星号版本用于显示
        if "wifi_apikey" in wifi_config and wifi_config["wifi_apikey"]:
            real_apikey = wifi_config["wifi_apikey"]
            # 显示前4个字符和星号
            wifi_config["wifi_apikey_display"] = real_apikey[:4] + "****" if len(real_apikey) > 4 else "****"
        else:
            wifi_config["wifi_apikey_display"] = ""
        
        # 记录操作日志
        logger.info(f"用户 {current_user_id} 更新了用户 {user_id} 的WIFI配置")
        
        return {
            "code": 20000,
            "message": "WIFI配置更新成功",
            "data": wifi_config
        }
        
    except Exception as e:
        logger.error(f"更新用户WIFI配置失败: {e}")
        return {"code": 50000, "message": f"更新用户WIFI配置失败: {str(e)}", "data": None}