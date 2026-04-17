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
async def delete_device_row(row_id: int):
    """删除单条子表行"""
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


@router.post("")
async def create_task(request: Request, body: TaskCreate):
    """创建新的更新任务"""
    user_id = await _get_current_user_id(request)
    
    name = body.name or f"更新任务"
    tid = body.tid
    if not tid:
        raise HTTPException(status_code=400, detail="tid 不能为空")

    task_id = await create_update_task(name=name, tid=tid, user_id=user_id)
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
    """获取任务列表（分页，只返回当前用户的任务）"""
    user_id = await _get_current_user_id(request)
    items, total = await get_task_list(page, page_size, status, user_id=user_id)
    return {
        "code": 20000,
        "data": {"items": items, "total": total},
        "message": "ok",
    }


@router.get("/{task_id}")
async def get_task(request: Request, task_id: int):
    """获取任务详情（含设备列表和状态统计）"""
    user_id = await _get_current_user_id(request)
    detail = await get_task_detail(task_id, user_id=user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    return {"code": 20000, "message": "ok", "data": detail}


@router.put("/{task_id}")
async def update_task_info(request: Request, task_id: int, body: TaskUpdate):
    """更新任务信息"""
    user_id = await _get_current_user_id(request)
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

    detail = await get_task_detail(task_id, user_id=user_id)
    return {"code": 20000, "message": "更新成功", "data": detail}


@router.delete("/{task_id}")
async def delete_one_task(request: Request, task_id: int):
    """删除任务（级联删除所有设备明细）"""
    user_id = await _get_current_user_id(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id)
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
    user_id = await _get_current_user_id(request)
    macs = body.macs
    if not macs:
        raise HTTPException(status_code=400, detail="macs 列表不能为空")

    added = await add_task_devices(
        task_id, macs,
        custom_data_map=body.custom_data_map,
    )
    detail = await get_task_detail(task_id, user_id=user_id)
    return {"code": 20000, "message": f"已添加 {added} 台设备", "data": detail}


@router.delete("/{task_id}/devices/{mac}")
async def remove_device_from_task(request: Request, task_id: int, mac: str):
    """从任务中移除单台设备"""
    user_id = await _get_current_user_id(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    ok = await remove_task_device(task_id, mac)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不在任务中或任务不存在")
    return {"code": 20000, "message": "已移除设备"}


@router.put("/{task_id}/devices/{mac}")
async def update_single_device_data(request: Request, task_id: int, mac: str, body: DeviceCustomData):
    """更新单台设备的自定义数据"""
    user_id = await _get_current_user_id(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在或无权限访问")
    await update_task_device_custom_data(task_id, mac, body.custom_data)
    return {"code": 20000, "message": "已保存自定义数据"}


@router.put("/{task_id}/devices/{mac}/status")
async def update_single_device_status(request: Request, task_id: int, mac: str, body: dict):
    """更新单台设备的推送状态（前端单推时标记 sent/failed）"""
    user_id = await _get_current_user_id(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id)
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
    user_id = await _get_current_user_id(request)
    detail = await get_task_detail(task_id, user_id=user_id)
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
    user_id = await _get_current_user_id(request)
    # 先验证任务存在且有权限
    detail = await get_task_detail(task_id, user_id=user_id)
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
    user_id = await _get_current_user_id(request)
    
    # 加载任务详情
    task = await get_task_detail(task_id, user_id=user_id)
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
        push_devices = [d for d in devices if d["mac"] in target_macs and d["update_status"] in ("pending", "failed", "sent", "success")]
    else:
        # 默认推送所有符合条件的设备
        push_devices = [d for d in devices if d["update_status"] in ("pending", "failed", "sent", "success")]

    if not push_devices:
        return {
            "code": 20000,
            "message": "没有待推送的设备",
            "data": {"total": 0, "success": 0, "failed": 0, "results": []},
        }

    tid = task["tid"]
    tname = task.get("tname", "")

    logger.info(f"[Task-{task_id}] 开始执行推送，目标 {len(push_devices)} 台设备")
    print(f"\n========== [TASK] 任务 {task_id} 开始推送 ==========")
    print(f"   模板: {tid} ({tname}), 设备数: {len(push_devices)}")

    # 将所有设备状态先置为 sent
    for d in push_devices:
        from services.db_service import update_task_device_status as _uds
        await _uds(task_id, d["mac"], "sent")

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
                
                if selected_row_id:
                    # 获取指定行
                    rows = await get_task_device_rows(dev["id"])
                    for r in rows:
                        if r["id"] == selected_row_id:
                            target_row = r
                            break
                
                # 如果没有指定行或指定行不存在，使用第一行
                if not target_row:
                    target_row = await get_first_task_device_row(dev["id"])
                
                if target_row:
                    row_custom = target_row.get("custom_data")
                    if row_custom:
                        if isinstance(row_custom, str) and row_custom.strip():
                            try:
                                data.update(json.loads(row_custom))
                            except Exception:
                                pass
                        elif isinstance(row_custom, dict):
                            data.update(row_custom)

                result = await wifi_proxy.apply_template(mac, tid, data, wifi_token, template_name=tname, base_url=wifi_base_url)
                return {"mac": mac, "success": True, "result": result}
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
    user_id = await _get_current_user_id(request)
    progress = await get_task_progress(task_id)
    detail = await get_task_detail(task_id, user_id=user_id)
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
    user_id = await _get_current_user_id(request)
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
    user_id = await _get_current_user_id(request)
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
    user_id = await _get_current_user_id(request)
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
    user_id = await _get_current_user_id(request)
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
