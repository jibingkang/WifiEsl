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
)
from services.wifi_client import wifi_proxy
from services.auth_service import get_api_key_from_request

router = APIRouter(prefix="/tasks", tags=["更新任务"])
logger = logging.getLogger(__name__)


async def _refresh_task_summary_db(task_id: int):
    """刷新任务汇总状态（包装 db_service 的函数）"""
    from services.db_service import get_db
    db = await get_db()
    await _refresh_task_summary_db_raw(db, task_id)


# ── Pydantic 请求模型 ──

class TaskCreate(BaseModel):
    name: str = ""
    tid: str = ""

class TaskUpdate(BaseModel):
    name: str | None = None
    default_data: dict | None = None
    status: str | None = None

class DevicesAdd(BaseModel):
    macs: list[str]
    custom_data_map: dict | None = None

class DeviceCustomData(BaseModel):
    custom_data: dict


# ── 辅助函数 ─

def _get_api_key(request: Request) -> str | None:
    return get_api_key_from_request(dict(request.headers))


# ══════════  任务 CRUD  ══════════

@router.post("")
async def create_task(body: TaskCreate):
    """创建新的更新任务"""
    name = body.name or f"更新任务"
    tid = body.tid
    if not tid:
        raise HTTPException(status_code=400, detail="tid 不能为空")

    task_id = await create_update_task(name=name, tid=tid)
    # 获取完整详情返回
    detail = await get_task_detail(task_id)
    return {"code": 20000, "message": "创建成功", "data": detail}


@router.get("")
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(""),
):
    """获取任务列表（分页）"""
    items, total = await get_task_list(page, page_size, status)
    return {
        "code": 20000,
        "data": {"items": items, "total": total},
        "message": "ok",
    }


@router.get("/{task_id}")
async def get_task(task_id: int):
    """获取任务详情（含设备列表和状态统计）"""
    detail = await get_task_detail(task_id)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"code": 20000, "message": "ok", "data": detail}


@router.put("/{task_id}")
async def update_task_info(task_id: int, body: TaskUpdate):
    """更新任务信息"""
    kwargs = {}
    if body.name is not None:
        kwargs["name"] = body.name
    if body.default_data is not None:
        kwargs["default_data"] = json.dumps(body.default_data, ensure_ascii=False)
    if body.status is not None:
        kwargs["status"] = body.status

    if kwargs:
        await update_task(task_id, **kwargs)

    detail = await get_task_detail(task_id)
    return {"code": 20000, "message": "更新成功", "data": detail}


@router.delete("/{task_id}")
async def delete_one_task(task_id: int):
    """删除任务（级联删除所有设备明细）"""
    ok = await delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"code": 20000, "message": "删除成功"}


# ══════════  设备管理  ══════════

@router.post("/{task_id}/devices")
async def add_devices_to_task(task_id: int, body: DevicesAdd):
    """批量添加设备到任务中"""
    macs = body.macs
    if not macs:
        raise HTTPException(status_code=400, detail="macs 列表不能为空")

    added = await add_task_devices(
        task_id, macs,
        custom_data_map=body.custom_data_map,
    )
    detail = await get_task_detail(task_id)
    return {"code": 20000, "message": f"已添加 {added} 台设备", "data": detail}


@router.delete("/{task_id}/devices/{mac}")
async def remove_device_from_task(task_id: int, mac: str):
    """从任务中移除单台设备"""
    ok = await remove_task_device(task_id, mac)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不在任务中或任务不存在")
    return {"code": 20000, "message": "已移除设备"}


@router.put("/{task_id}/devices/{mac}")
async def update_single_device_data(task_id: int, mac: str, body: DeviceCustomData):
    """更新单台设备的自定义数据"""
    await update_task_device_custom_data(task_id, mac, body.custom_data)
    return {"code": 20000, "message": "已保存自定义数据"}


@router.put("/{task_id}/devices/{mac}/status")
async def update_single_device_status(task_id: int, mac: str, body: dict):
    """更新单台设备的推送状态（前端单推时标记 sent/failed）"""
    status = body.get("update_status", "")
    error_msg = body.get("error_msg", "") if status in ("failed",) else ""
    ok = await update_task_device_status(task_id, mac, status, error_msg)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不在任务中或任务不存在")
    # 刷新任务汇总
    await _refresh_task_summary_db(task_id)
    return {"code": 20000, "message": f"设备 {mac} 状态已更新为 {status}"}


@router.get("/{task_id}/devices")
async def list_task_devices(task_id: int):
    """获取任务的设备列表"""
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
    """
    # 加载任务详情
    task = await get_task_detail(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    api_key = _get_api_key(request)

    # 解析 default_data
    try:
        default_data = json.loads(task.get("default_data") or "{}")
    except Exception:
        default_data = {}

    # 获取需要推送的设备列表
    devices = task.get("devices", [])
    
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
                custom = dev.get("custom_data")
                if custom and isinstance(custom, str) and custom.strip():
                    try:
                        custom_obj = json.loads(custom)
                        data.update(custom_obj)
                    except Exception:
                        pass
                elif isinstance(custom, dict):
                    data.update(custom)

                result = await wifi_proxy.apply_template(mac, tid, data, api_key, template_name=tname)
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
async def get_progress(task_id: int):
    """获取任务推送进度"""
    progress = await get_task_progress(task_id)
    detail = await get_task_detail(task_id)
    if not detail:
        raise HTTPException(status_code=404, detail="任务不存在")
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
