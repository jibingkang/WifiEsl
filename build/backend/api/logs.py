"""
操作记录 API - 统一查询操作日志、推送日志、设备事件
GET /api/v1/operation-logs      - 操作日志（登录/推送/配置变更/上下线等）
GET /api/v1/push-logs           - 设备推送日志（每台设备每次推送的详细记录）
GET /api/v1/device-events-logs  - 设备事件（在线/离线/按键/回执等原始事件）
"""
import json
import logging
from fastapi import APIRouter, Request, HTTPException, Query

from services.db_service import get_logs, get_push_logs, get_device_events, get_db as _get_db
from services.auth_service import get_current_user_id_from_token
from services.db_service_extended import get_user_by_id

router = APIRouter(prefix="", tags=["操作记录"])
logger = logging.getLogger(__name__)

# action 类型中文映射
ACTION_LABELS = {
    "task_push": "数据推送",
    "batch_update_template": "批量推送",
    "device_online": "设备上线",
    "device_offline": "设备离线",
    "LOGIN": "用户登录",
    "LOGIN_FAILED": "登录失败",
    "CREATE_USER": "创建用户",
    "UPDATE_CONFIG": "修改配置",
}


async def _get_user_info(request: Request) -> tuple[int, str, str]:
    """从请求中获取当前用户ID、角色和用户名"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header:
        raise HTTPException(status_code=401, detail="未授权")

    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
    user_id = get_current_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的token")

    user_info = await get_user_by_id(user_id)
    if not user_info:
        raise HTTPException(status_code=401, detail="用户不存在")

    role = user_info.get("role", "user")
    username = user_info.get("username", "unknown")
    return user_id, role, username


async def get_family_tree_ids(db, user_id: int) -> list[int]:
    """
    BFS获取 user_id 所在家族树的全部非admin用户ID。
    普通用户的家族树以 admin 的直接下级为根，绝不包含 admin/super_admin。
    """
    # Step 1: 向上找根，遇到 admin/super_admin 立即停止
    root = user_id
    visited = set()
    while True:
        if root in visited:
            break  # 防环
        visited.add(root)

        # 查当前用户的角色和 parent_user_id
        cur = await db.execute(
            "SELECT id, role, parent_user_id FROM users WHERE id=?", (root,)
        )
        row = await cur.fetchone()
        if not row:
            break

        pid = row["parent_user_id"] or 0
        if pid and pid > 0:
            # 检查父用户是否是 admin/super_admin
            pcur = await db.execute("SELECT role FROM users WHERE id=?", (pid,))
            prow = await pcur.fetchone()
            if prow and prow["role"] in ("admin", "super_admin"):
                # 父用户是管理员 → 停在这里，root 就是当前用户
                break
            root = pid
        else:
            break

    # Step 2: 从 root 向下 BFS 收集所有后代（排除 admin/super_admin）
    ids = set()
    queue = [root]
    while queue:
        cid = queue.pop(0)
        if cid in ids:
            continue
        ids.add(cid)

        # 只收集 role 不是 admin/super_admin 的子用户
        children = await db.execute(
            "SELECT id FROM users WHERE parent_user_id=? AND status='active' AND role NOT IN ('admin','super_admin')",
            (cid,),
        )
        for r in await children.fetchall():
            if r["id"] not in ids:
                queue.append(r["id"])

    return list(ids)


async def _build_allowed_user_ids(db, user_id: int, role: str) -> list[int] | None:
    """
    根据角色构建可见的 user_id 列表。
    - admin / super_admin: None (不过滤，看全部)
    - user: 整棵家族树 BFS（祖先 + 所有后代）→ 子管理员可监管全树
    - operator: 仅自己
    """
    if role in ("admin", "super_admin"):
        return None  # 不过滤

    if role == "user":
        return await get_family_tree_ids(db, user_id)

    if role == "operator":
        return [user_id]  # 仅自己

    return [user_id]


# 兼容旧调用签名（db 参数位置不同时自动适配）
async def _build_allowed_user_ids_legacy(user_id: int, role: str) -> list[int] | None:
    """兼容旧版调用签名的包装"""
    _db = await _get_db()
    return await _build_allowed_user_ids(_db, user_id, role)


async def _build_allowed_macs(db, user_id: int, role: str) -> list[str] | None:
    """
    根据角色构建可见的 MAC 列表（用于设备事件过滤）
    - admin: None (不过滤)
    - user: 通过家族树内 devices 表查 MAC
    - operator: 仅自己的设备
    """
    if role == "admin":
        return None

    allowed_uids = await _build_allowed_user_ids(db, user_id, role)
    if allowed_uids is None:
        return None

    placeholders = ",".join("?" * len(allowed_uids))
    cur = await db.execute(
        f"SELECT DISTINCT mac FROM devices WHERE user_id IN ({placeholders})",
        allowed_uids,
    )
    rows = await cur.fetchall()
    return [r["mac"] for r in rows] if rows else []


def _get_allowed_actions(role: str) -> list[str]:
    """根据角色返回可查看的操作类型"""
    common = ["task_push", "batch_update_template", "device_online", "device_offline"]
    admin_extra = ["LOGIN", "LOGIN_FAILED", "CREATE_USER", "UPDATE_CONFIG"]

    if role == "admin":
        return common + admin_extra
    elif role == "user":
        return common + ["CREATE_USER", "UPDATE_CONFIG"]
    else:  # operator
        return common


@router.get("/operation-logs")
async def get_operation_logs_api(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str = Query("", description="操作类型筛选"),
    mac: str = Query("", description="设备MAC筛选"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """查询操作日志（支持角色权限过滤）"""
    user_id, role, username = await _get_user_info(request)

    # operator 只能看部分操作类型
    allowed_actions = _get_allowed_actions(role)
    if action and action not in allowed_actions:
        return {"code": 20000, "data": {"items": [], "total": 0, "page": page, "pageSize": page_size}}

    # 构建权限过滤
    _db = await _get_db()
    allowed_user_ids = await _build_allowed_user_ids(_db, user_id, role)

    items, total = await get_logs(
        page=page,
        page_size=page_size,
        action=action,
        user_id=None,  # 通过 allowed_user_ids 控制权限；admin 时为 None 表示不过滤
        allowed_user_ids=allowed_user_ids,
        start_time=start_time,
        end_time=end_time,
        mac=mac,
    )

    # 解析 detail JSON + 添加 action_label
    for item in items:
        if isinstance(item.get("detail"), str):
            try:
                item["detail"] = json.loads(item["detail"])
            except Exception:
                pass
        item["action_label"] = ACTION_LABELS.get(item.get("action", ""), item.get("action", ""))

    return {
        "code": 20000,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    }


@router.get("/push-logs")
async def get_push_logs_api(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_id: int = Query(0, description="任务ID筛选"),
    mac: str = Query("", description="设备MAC筛选"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    result: str = Query("", description="结果筛选: pending/sent/success/failed"),
):
    """查询设备推送日志（支持角色权限过滤）"""
    user_id, role, username = await _get_user_info(request)

    _db = await _get_db()
    allowed_user_ids = await _build_allowed_user_ids(_db, user_id, role)

    items, total = await get_push_logs(
        page=page,
        page_size=page_size,
        task_id=task_id if task_id > 0 else None,
        mac=mac,
        user_id=None,  # 通过 allowed_user_ids 控制权限
        allowed_user_ids=allowed_user_ids,
        start_time=start_time,
        end_time=end_time,
        result=result,
    )

    # 解析 push_data JSON + 映射模板名 fallback
    for item in items:
        if isinstance(item.get("push_data"), str):
            try:
                item["push_data"] = json.loads(item["push_data"])
            except Exception:
                pass
        # 模板名 fallback: 如果 device_push_logs 中没有，用 update_tasks 的
        if "template_name_final" in item and item["template_name_final"] and not item.get("template_name"):
            item["template_name"] = item["template_name_final"]
        # 确保设备名称不为 None
        if item.get("device_name") is None:
            item["device_name"] = ""

    return {
        "code": 20000,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    }


@router.get("/device-events-logs")
async def get_device_events_logs_api(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    mac: str = Query("", description="设备MAC筛选"),
    event_type: str = Query("", description="事件类型: online/offline/button/display_reply/battery_reply/led_reply"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """查询设备事件日志（不按MAC权限过滤，事件由当前用户的MQTT连接产生）"""
    items, total = await get_device_events(
        mac=mac if mac else None,
        event_type=event_type if event_type else None,
        page=page,
        page_size=page_size,
        allowed_macs=None,  # 事件日志不过滤MAC，与操作记录逻辑统一
        start_time=start_time,
        end_time=end_time,
    )

    # 解析 payload JSON
    for item in items:
        if isinstance(item.get("payload"), str):
            try:
                item["payload"] = json.loads(item["payload"])
            except Exception:
                pass

    return {
        "code": 20000,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    }
