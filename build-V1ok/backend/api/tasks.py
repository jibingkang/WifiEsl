"""
更新任务 API - 任务 CRUD + 设备管理 + 执行推送
POST/GET /tasks, GET/PUT/DELETE /tasks/{id}, 
POST /tasks/{id}/devices, DELETE /tasks/{id}/devices/{mac},
POST /tasks/{id}/execute, GET /tasks/{id}/progress
"""
import asyncio
import json
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

from services.db_service import (
    create_update_task,
    get_task_list,
    get_task_detail,
    update_task,
    delete_task,
    add_task_devices,
    remove_task_device,
    get_task_device_list,
    update_task_device_custom_data,
    update_task_device_status,
    batch_update_device_statuses,
    get_task_progress,
    _refresh_task_summary as _refresh_task_summary_db_raw,
    # 子表 CRUD
    get_task_device_rows,
    get_first_task_device_row,
    add_task_device_row,
    update_task_device_row,
    delete_task_device_row,
    delete_all_task_device_rows,
    batch_add_task_device_rows,
    # 操作日志
    add_log,
    add_push_log,
    # 模板查询
    get_template_by_tid,
    # DB 连接
    get_db,
)
from services.wifi_client import wifi_proxy
from services.auth_service import get_current_user_id_from_token
from services.wifi_connection_manager import wifi_connection_manager

router = APIRouter(prefix="/tasks", tags=["更新任务"])
logger = logging.getLogger(__name__)


async def _refresh_task_summary_db(task_id: int):
    """刷新任务汇总状态（包装 db_service 的函数）"""
    db = await get_db()
    await _refresh_task_summary_db_raw(db, task_id)


# ── Pydantic 请求模型 ──

class TaskCreate(BaseModel):
    name: str = ""
    tid: str = ""

class TaskUpdate(BaseModel):
    name: str | None = None
    tid: str | None = None
    default_data: dict | None = None
    status: str | None = None

class DevicesAdd(BaseModel):
    macs: list[str]
    custom_data_map: dict | None = None

class DeviceCustomData(BaseModel):
    custom_data: dict


class TaskDeviceRowCreate(BaseModel):
    custom_data: dict
    sort_order: int | None = None


class TaskDeviceRowUpdate(BaseModel):
    custom_data: dict


class TaskDeviceRowsBatchCreate(BaseModel):
    rows: list[dict]  # [custom_data_dict, ...]
    mode: str = 'overwrite'  # overwrite: 先清空再插入 | append: 追加到现有行之后


# ── 辅助函数 ─

async def _get_wifi_token(request: Request) -> str | None:
    """从请求中获取用户的WIFI系统token"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header:
        return None
    
    # 提取token（去掉Bearer前缀）
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
    if not token:
        return None
    
    # 从token获取用户ID
    user_id = get_current_user_id_from_token(token)
    if not user_id:
        return None
    
    # 获取用户的WIFI系统token
    conn = await wifi_connection_manager.get_connection(user_id)
    if conn and conn.token:
        return conn.token
    
    return None


async def _get_wifi_config(request: Request) -> tuple[str | None, str | None]:
    """从请求中获取用户的WIFI系统token和base_url
    
    Returns:
        tuple: (wifi_token, wifi_base_url) 如果获取失败则返回 (None, None)
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header:
        return None, None
    
    # 提取token（去掉Bearer前缀）
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
    if not token:
        return None, None
    
    # 从token获取用户ID
    user_id = get_current_user_id_from_token(token)
    if not user_id:
        return None, None
    
    # 获取用户的WIFI连接配置
    conn = await wifi_connection_manager.get_connection(user_id)
    if conn and conn.token:
        return conn.token, conn.wifi_base_url
    
    return None, None


# ══════════  子表行直接操作（必须在 /{task_id} 路由之前定义）  ══════════

@router.put("/device-rows/{row_id}")
async def update_device_row(request: Request, row_id: int, body: TaskDeviceRowUpdate):
    """更新单条子表行的自定义数据"""
    ok = await update_task_device_row(row_id, body.custom_data)
    if not ok:
        raise HTTPException(status_code=404, detail="子表行不存在")
    return {"code": 20000, "message": "已更新"}


@router.delete("/device-rows/{row_id}")
async def delete_device_row(request: Request, row_id: int):
    """删除单条子表行"""
    await _reject_operator(request)
    ok = await delete_task_device_row(row_id)
    if not ok:
        raise HTTPException(status_code=404, detail="子表行不存在")
    return {"code": 20000, "message": "已删除"}


# ══════════  任务 CRUD  ══════════

async def _get_current_user_id(request: Request) -> int:
    """从请求token中获取当前用户ID"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header:
        raise HTTPException(status_code=401, detail="未授权")
    
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
    user_id = get_current_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的token")
    
    return user_id


async def _get_allowed_user_ids(request: Request) -> tuple[int, list[int] | None]:
    """
    获取当前用户ID和该用户可见任务的所有用户ID列表。
    
    - admin/super_admin: 看全部 → (user_id, None)
    - user: 整棵家族树 BFS（祖先+所有后代）→ 子管理员可监管全树
    - operator: 自己 + parent_user 的任务 → (user_id, [operator_id, parent_user_id])
    
    Returns: (current_user_id, allowed_user_ids_or_None)
    """
    user_id = await _get_current_user_id(request)
    
    from services.db_service_extended import get_user_by_id
    user_info = await get_user_by_id(user_id)
    role = user_info.get("role", "user") if user_info else "user"
    
    if role == "admin" or role == "super_admin":
        return user_id, None
    
    if role == "user":
        # user 角色：使用家族树 BFS
        from api.logs import get_family_tree_ids as _get_tree_ids
        from services.db_service import get_db as _get_db_for_tree
        _db = await _get_db_for_tree()
        tree_ids = await _get_tree_ids(_db, user_id)
        return user_id, tree_ids
    
    # operator: 自己 + parent
    if user_info:
        parent_id = user_info.get("parent_user_id", 0)
        if parent_id and parent_id > 0:
            return user_id, [user_id, parent_id]
    
    return user_id, [user_id]


async def _reject_operator(request: Request):
    """如果当前用户是 operator，拒绝操作（operator 只能推送，不能增删改）"""
    from services.db_service_extended import get_user_by_id
    user_id = await _get_current_user_id(request)
    user_info = await get_user_by_id(user_id)
    role = user_info.get("role", "user") if user_info else "user"
    if role == "operator":
        raise HTTPException(status_code=403, detail="操作员无此权限")


@router.post("")
async def create_task(request: Request, body: TaskCreate):
    """创建新的更新任务"""
    user_id = await _get_current_user_id(request)
    
    name = body.name or f"更新任务"
    tid = body.tid
    if not tid:
        raise HTTPException(status_code=400, detail="tid 不能为空")

    # 查询模板名称
    tname = ""
    try:
        tpl = await get_template_by_tid(tid)
        if tpl:
            tname = tpl.get("tname", "")
    except Exception as e:
        logger.warning(f"创建任务时查询模板名称失败 tid={tid}: {e}")

    task_id = await create_update_task(name=name, tid=tid, tname=tname, user_id=user_id)
    # 获取完整详情返回
    detail = await get_task_detail(task_id, user_id=user_id)
    return {"code": 20000, "message": "创建成功", "data": detail}


@router.get("")
async def list_tasks(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(""),
):
    """获取任务列表（分页，返回当前用户可见的任务）"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    items, total = await get_task_list(page, page_size, status, user_id=user_id, allowed_user_ids=allowed_ids)
    return {
        "code": 20000,
        "data": {"items": items, "total": total},
        "message": "ok",
    }


@router.get("/{task_id}")
async def get_task(request: Request, task_id: int):
    """获取任务详情（含设备列表和状态统计）"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    return {"code": 20000, "message": "ok", "data": detail}


@router.put("/{task_id}")
async def update_task_info(request: Request, task_id: int, body: TaskUpdate):
    """更新任务信息"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    kwargs = {}
    if body.name is not None:
        kwargs["name"] = body.name
    if body.tid is not None:
        kwargs["tid"] = body.tid
    if body.default_data is not None:
        kwargs["default_data"] = json.dumps(body.default_data, ensure_ascii=False)
    if body.status is not None:
        kwargs["status"] = body.status

    if kwargs:
        await update_task(task_id, **kwargs)

    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    return {"code": 20000, "message": "更新成功", "data": detail}


@router.delete("/{task_id}")
async def delete_one_task(request: Request, task_id: int):
    """删除任务（级联删除所有设备明细）"""
    await _reject_operator(request)
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    ok = await delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"code": 20000, "message": "删除成功"}


# ══════════  设备管理  ══════════

@router.post("/{task_id}/devices")
async def add_devices_to_task(request: Request, task_id: int, body: DevicesAdd):
    """批量添加设备到任务中"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    macs = body.macs
    if not macs:
        raise HTTPException(status_code=400, detail="macs 列表不能为空")

    added = await add_task_devices(
        task_id, macs,
        custom_data_map=body.custom_data_map,
    )
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    return {"code": 20000, "message": f"已添加 {added} 台设备", "data": detail}


@router.delete("/{task_id}/devices/{mac}")
async def remove_device_from_task(request: Request, task_id: int, mac: str):
    """从任务中移除单台设备"""
    await _reject_operator(request)
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    ok = await remove_task_device(task_id, mac)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不在任务中或任务不存在")
    return {"code": 20000, "message": "已移除设备"}


@router.put("/{task_id}/devices/{mac}")
async def update_single_device_data(request: Request, task_id: int, mac: str, body: DeviceCustomData):
    """更新单台设备的自定义数据"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    await update_task_device_custom_data(task_id, mac, body.custom_data)
    return {"code": 20000, "message": "已保存自定义数据"}


@router.put("/{task_id}/devices/{mac}/status")
async def update_single_device_status(request: Request, task_id: int, mac: str, body: dict):
    """更新单台设备的推送状态（前端单推时标记 sent/failed）"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    status = body.get("update_status", "")
    error_msg = body.get("error_msg", "") if status in ("failed",) else ""
    ok = await update_task_device_status(task_id, mac, status, error_msg)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不在任务中或任务不存在")
    # 刷新任务汇总
    await _refresh_task_summary_db(task_id)
    return {"code": 20000, "message": f"设备 {mac} 状态已更新为 {status}"}


@router.put("/{task_id}/devices/{mac}/selected-row")
async def update_selected_row(request: Request, task_id: int, mac: str, body: dict):
    """更新设备当前选中的子表行ID（跨设备同步用）"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    row_id = body.get("selected_row_id")
    db = await get_db()
    await db.execute(
        "UPDATE task_devices SET selected_row_id=? WHERE task_id=? AND mac=?",
        (row_id, task_id, mac),
    )
    await db.commit()
    return {"code": 20000, "message": "已更新选中行"}


@router.get("/{task_id}/devices")
async def list_task_devices(request: Request, task_id: int):
    """获取任务的设备列表"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    devices = await get_task_device_list(task_id)
    return {"code": 20000, "data": devices}


# ══════════  执行推送（核心接口） ══════════

@router.post("/{task_id}/execute")
async def execute_task_push(request: Request, task_id: int, body: dict = None):
    """
    执行任务推送：
    1. 加载任务信息 (tid, default_data) + 所有 pending 状态的设备
    2. 并发调用 wifi_proxy.apply_template() 推送
    3. 根据结果逐条更新 task_devices.update_status
    4. 汇总结果并返回
    
    可选参数：
    - macs: 指定要推送的设备MAC列表，如果不传则推送所有符合条件的设备
    - row_selections: 指定每个设备要推送的行ID，格式 {mac: row_id}，不传则默认推送第一行
    """
    # 获取当前用户ID并进行多租户验证
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    
    # 加载任务详情
    task = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")

    wifi_token, wifi_base_url = await _get_wifi_config(request)
    if not wifi_token:
        raise HTTPException(status_code=401, detail="未授权")

    # 解析 default_data
    try:
        default_data = json.loads(task.get("default_data") or "{}")
    except Exception:
        default_data = {}

    # 获取需要推送的设备列表
    devices = task.get("devices", [])
    
    # 解析行选择参数 {mac: row_id}
    row_selections = (body or {}).get("row_selections", {}) or {}
    
    # 如果指定了设备列表，只推送指定的设备
    if body and "macs" in body and body["macs"]:
        target_macs = set(body["macs"])
        push_devices_all = [d for d in devices if d["mac"] in target_macs and d["update_status"] in ("pending", "failed", "sent", "success")]
    else:
        # 默认推送所有符合条件的设备
        push_devices_all = [d for d in devices if d["update_status"] in ("pending", "failed", "sent", "success")]

    # 去重：同一MAC只推送一次，优先取 row_selections 匹配的行
    push_devices = []
    seen_macs = set()
    for d in push_devices_all:
        mac = d["mac"]
        if mac in seen_macs:
            continue
        seen_macs.add(mac)
        # 该MAC有指定的行选择时，找该子行所属的 task_device 记录
        best = d
        selected_rid = row_selections.get(mac)
        if selected_rid:
            for candidate in push_devices_all:
                if candidate["mac"] == mac:
                    candidate_rows = await get_task_device_rows(candidate["id"])
                    if any(r["id"] == selected_rid for r in candidate_rows):
                        best = candidate
                        break
        push_devices.append(best)

    if not push_devices:
        return {
            "code": 20000,
            "message": "没有待推送的设备",
            "data": {"total": 0, "success": 0, "failed": 0, "results": []},
        }

    tid = task["tid"]
    tname = task.get("tname", "")

    # ⭐ 如果任务自身 tname 为空，从模板表补全并持久化
    if not tname:
        try:
            tpl = await get_template_by_tid(tid)
            if tpl:
                tname = tpl.get("tname", "")
                if tname:
                    # 回写 update_tasks，避免下次执行时再查
                    from services.db_service import get_db as _get_exec_db
                    _exec_db = await _get_exec_db()
                    await _exec_db.execute("UPDATE update_tasks SET tname=? WHERE id=?", (tname, task_id))
                    await _exec_db.commit()
                    logger.info(f"[Task-{task_id}] 补全模板名称: {tname}")
        except Exception as e:
            logger.warning(f"[Task-{task_id}] 补全模板名称失败: {e}")

    logger.info(f"[Task-{task_id}] 开始执行推送，目标 {len(push_devices)} 台设备")
    print(f"\n========== [TASK] 任务 {task_id} 开始推送 ==========")
    print(f"   模板: {tid} ({tname}), 设备数: {len(push_devices)}")
    print(f"   设备MAC列表: {[d['mac'] for d in push_devices]}")
    print(f"   行选择参数: {row_selections}")
    # 打印每台设备的推送参数
    for d in push_devices[:5]:  # 最多打印5台设备参数
        cd = d.get("custom_data", "{}")
        print(f"   设备 {d['mac']} (dev_id={d['id']}): custom_data={cd}")

    # 将所有设备状态先置为 sent，同时设置 pending_reply_row_id（仅记录推送行，不改 selected_row_id）
    # selected_row_id 只在回执成功时更新，推送中不改变当前显示行
    from services.db_service import get_db as _get_db
    _push_db = await _get_db()
    for d in push_devices:
        mac = d["mac"]
        selected_rid = row_selections.get(mac)
        if selected_rid:
            # pending_reply_row_id: 正在等待回执的行（回执成功后才写入 selected_row_id）
            await _push_db.execute(
                "UPDATE task_devices SET pending_reply_row_id=? WHERE task_id=? AND mac=?",
                (selected_rid, task_id, mac),
            )
            await _push_db.commit()
        from services.db_service import update_task_device_status as _uds
        await _uds(task_id, mac, "sent")
    await _push_db.commit()

    results = []
    semaphore = asyncio.Semaphore(5)

    async def _push_one(dev: dict) -> dict:
        mac = dev["mac"]
        async with semaphore:
            try:
                # 合并默认数据和设备自定义数据
                data = {**default_data}

                # 1. 主表 custom_data 作为基底
                custom = dev.get("custom_data")
                if custom and isinstance(custom, str) and custom.strip():
                    try:
                        custom_obj = json.loads(custom)
                        data.update(custom_obj)
                    except Exception:
                        pass
                elif isinstance(custom, dict):
                    data.update(custom)

                # 2. 子表数据覆盖主表
                # 检查是否有指定行选择
                selected_row_id = row_selections.get(mac)
                target_row = None
                target_row_idx = 0  # 1-based 行号
                
                if selected_row_id:
                    # 获取指定行
                    rows = await get_task_device_rows(dev["id"])
                    print(f"   [{mac}] dev_id={dev['id']}, 期望行ID={selected_row_id}, 子行数量={len(rows)}")
                    print(f"   [{mac}] 子行ID列表: {[(r['id'], r.get('sort_order')) for r in rows]}")
                    for idx, r in enumerate(rows):
                        if r["id"] == selected_row_id:
                            target_row = r
                            target_row_idx = idx + 1
                            break
                    
                    if not target_row:
                        print(f"   [警告] {mac}: 未找到 row_id={selected_row_id}，将使用第一行")
                        print(f"   [警告] 前端选中行ID {selected_row_id} 不在 dev_id={dev['id']} 的子行列表中")
                
                # 如果没有指定行或指定行不存在，使用第一行
                if not target_row:
                    target_row = await get_first_task_device_row(dev["id"])
                    target_row_idx = 1
                
                if target_row:
                    row_custom = target_row.get("custom_data")
                    print(f"   [{mac}] 推送行: row_id={target_row.get('id')} (第{target_row_idx}行), custom_data={row_custom}")
                    if row_custom:
                        if isinstance(row_custom, str) and row_custom.strip():
                            try:
                                data.update(json.loads(row_custom))
                            except Exception:
                                pass
                        elif isinstance(row_custom, dict):
                            data.update(row_custom)

                result = await wifi_proxy.apply_template(mac, tid, data, wifi_token, template_name=tname, base_url=wifi_base_url)
                return {"mac": mac, "success": True, "result": result, "push_data": data}
            except Exception as e:
                logger.warning(f"[Task-{task_id}] 设备 {mac} 推送失败: {e}")
                return {"mac": mac, "success": False, "error": str(e)}

    coros = [_push_one(d) for d in push_devices]
    results = await asyncio.gather(*coros)

    # 统计 MQTT 发送成功/失败数（注意：这只是发送结果，不是设备回执）
    # 设备最终 success/failed 由 display_reply 回调驱动
    sent_ok = sum(1 for r in results if r.get("success"))
    sent_fail = len(results) - sent_ok

    # 对发送失败的设备标记为 failed（MQTT 层面就失败了，不会收到 reply）
    from services.db_service import update_task_device_status as _uds_fail
    for r in results:
        if not r.get("success"):
            await _uds_fail(task_id, r["mac"], "failed", r.get("error", "MQTT发送失败"))

    # 刷新任务汇总状态
    await _refresh_task_summary_db(task_id)

    # ═══ 记录推送日志 ═══
    import datetime as dt
    now_iso = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 查询操作人信息
    from services.db_service_extended import get_user_by_id
    operator_info = await get_user_by_id(user_id)
    operator_name = operator_info.get("username", "unknown") if operator_info else "unknown"

    # 1. 每台设备写一条 device_push_logs（逐条 try，一条失败不影响其他）
    for r in results:
        mac = r.get("mac", "")
        try:
            # 直接使用 _push_one 返回的合并后推送数据（default_data + device_custom + row_custom）
            merged_data = r.get("push_data", {})
            push_data_json = json.dumps(merged_data, ensure_ascii=False) if merged_data else "{}"

            p_result = "sent" if r.get("success") else "failed"
            p_error = r.get("error", "") if not r.get("success") else ""
            await add_push_log(
                task_id=task_id,
                mac=mac,
                user_id=user_id,
                username=operator_name,
                template_id=tid,
                template_name=tname,
                push_data=push_data_json,
                result=p_result,
                error_msg=p_error,
                sent_at=now_iso,
            )
            # 从WIFI系统同步设备别名到本地DB
            if r.get("success"):
                try:
                    from services.db_service import upsert_device as _upsert
                    dev_info = await wifi_proxy.get_device_by_mac(mac, wifi_token, base_url=wifi_base_url)
                    dev_data = dev_info.get("data", dev_info) if isinstance(dev_info, dict) else {}
                    alias = dev_data.get("alias", "") if isinstance(dev_data, dict) else ""
                    if alias:
                        await _upsert(mac=mac, user_id=user_id, name=alias)
                except Exception:
                    pass
        except Exception as push_log_err:
            logger.warning(f"[Task-{task_id}] 设备 {mac} 推送明细写入失败: {push_log_err}")

    # 2. 汇总写一条 operation_logs（确保必然执行，不受 above 异常影响）
    try:
        detail_data = {
            "taskId": task_id,
            "templateId": tid,
            "templateName": tname,
            "deviceCount": len(push_devices),
            "sentOk": sent_ok,
            "sentFail": sent_fail,
        }
        await add_log(
            username=operator_name,
            action="task_push",
            target_type="task",
            target_id=str(task_id),
            detail=json.dumps(detail_data, ensure_ascii=False),
            result="success" if sent_fail == 0 else "partial",
            user_id=user_id,
            task_id=task_id,
        )
    except Exception as log_err:
        logger.warning(f"[Task-{task_id}] 写入操作汇总日志失败: {log_err}")

    return {
        "code": 20000,
        "message": f"推送已发出: 成功{sent_ok}, 发送失败{sent_fail} (等待设备回执)",
        "data": {
            "total": len(push_devices),
            "success": sent_ok,
            "failed": sent_fail,
            "results": results,
        },
    }


# ══════════  进度查询  ══════════

@router.get("/{task_id}/progress")
async def get_progress(request: Request, task_id: int):
    """获取任务推送进度"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    progress = await get_task_progress(task_id)
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    return {
        "code": 20000,
        "data": {
            "status": detail.get("status"),
            "total_devices": detail.get("total_devices"),
            "success_count": detail.get("success_count"),
            "failed_count": detail.get("failed_count"),
            **progress,
        },
    }


# ══════════  子表数据管理 (task_device_rows)  ══════════

@router.get("/{task_id}/devices/{mac}/rows")
async def list_device_rows(request: Request, task_id: int, mac: str):
    """获取某设备在任务中的所有子表行数据"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 验证任务权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    # 先找到 task_device id
    from services.db_service import get_db
    db = await get_db()
    cur = await db.execute(
        "SELECT id FROM task_devices WHERE task_id=? AND mac=?", (task_id, mac)
    )
    dev = await cur.fetchone()
    if not dev:
        raise HTTPException(status_code=404, detail="设备不在任务中")
    rows = await get_task_device_rows(dev["id"])
    return {"code": 20000, "data": rows}


@router.post("/{task_id}/devices/{mac}/rows")
async def add_device_row(request: Request, task_id: int, mac: str, body: TaskDeviceRowCreate):
    """为某设备添加一条子表行数据"""
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 验证任务权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    from services.db_service import get_db
    db = await get_db()
    cur = await db.execute(
        "SELECT id FROM task_devices WHERE task_id=? AND mac=?", (task_id, mac)
    )
    dev = await cur.fetchone()
    if not dev:
        raise HTTPException(status_code=404, detail="设备不在任务中")
    row_id = await add_task_device_row(dev["id"], body.custom_data, body.sort_order)
    return {"code": 20000, "message": "已添加子表行", "data": {"row_id": row_id}}


@router.post("/{task_id}/devices/{mac}/rows/batch")
async def batch_add_device_rows(
    request: Request, task_id: int, mac: str, body: TaskDeviceRowsBatchCreate
):
    """
    批量添加子表行数据（导入时使用）
    会先清空该设备的所有旧行，再批量插入新数据
    mode='overwrite': 先清空再插入
    mode='append': 追加到现有行之后
    """
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 验证任务权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    from services.db_service import get_db
    db = await get_db()
    cur = await db.execute(
        "SELECT id FROM task_devices WHERE task_id=? AND mac=?", (task_id, mac)
    )
    dev = await cur.fetchone()
    if not dev:
        raise HTTPException(status_code=404, detail="设备不在任务中")

    mode = body.mode  # overwrite or append（从 Pydantic 模型获取）
    task_dev_id = dev["id"]

    if mode == "overwrite":
        await delete_all_task_device_rows(task_dev_id)

    added = await batch_add_task_device_rows(task_dev_id, body.rows)
    return {
        "code": 20000,
        "message": f"已批量添加 {added} 条子表行 (模式={mode})",
        "data": {"added": added},
    }


@router.delete("/{task_id}/devices/{mac}/rows")
async def clear_device_rows(request: Request, task_id: int, mac: str):
    """清空某设备的所有子表行数据"""
    await _reject_operator(request)
    user_id, allowed_ids = await _get_allowed_user_ids(request)
    # 验证任务权限
    detail = await get_task_detail(task_id, user_id=user_id, allowed_user_ids=allowed_ids)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    from services.db_service import get_db
    db = await get_db()
    cur = await db.execute(
        "SELECT id FROM task_devices WHERE task_id=? AND mac=?", (task_id, mac)
    )
    dev = await cur.fetchone()
    if not dev:
        raise HTTPException(status_code=404, detail="设备不在任务中")
    deleted = await delete_all_task_device_rows(dev["id"])
    return {"code": 20000, "message": f"已清空 {deleted} 条子表行"}
