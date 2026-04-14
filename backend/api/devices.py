"""
设备管理API - 设备CRUD代理到真实WIFI系统
GET/POST/PUT/DELETE /api/v1/devices
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Query, Request

from services.wifi_client import wifi_proxy
from services.auth_service import get_api_key_from_request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["设备管理"])


def _get_api_key(request: Request) -> str | None:
    return get_api_key_from_request(dict(request.headers))


def _extract_timestamp(item: dict) -> tuple[str, str]:
    """从原始设备数据中提取创建/更新时间，返回 (created_at, updated_at)"""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    created = (
        item.get("created_at") or item.get("createdAt")
        or item.get("created") or item.get("registerTime") or now
    )
    updated = (
        item.get("updated_at") or item.get("updatedAt")
        or item.get("updated") or item.get("last_seen")
        or item.get("lastSeen") or item.get("lastSeenAt")
        or created or now
    )
    return str(created), str(updated)


def _normalize_single_device(raw_data: dict) -> dict | None:
    """
    将真实WIFI系统返回的单个设备原始数据归一化为前端统一格式。
    真实系统可能返回 { code:20000, data:{...} } 或直接对象
    """
    if not isinstance(raw_data, dict):
        return None

    # 如果外层有 code/data 结构，取 data 部分
    item = raw_data.get("data", raw_data) if "code" in raw_data else raw_data
    if not isinstance(item, dict):
        return None

    station = item.get("station") or {}
    screentype = item.get("screentype") or item.get("screen_type") or {}
    devtype = item.get("devtype") or item.get("device_type") or {}
    created_at, updated_at = _extract_timestamp(item)

    return {
        "id": item.get("_id", item.get("id", "")),
        "mac": item.get("mac", ""),
        "ip": item.get("ip", ""),
        "name": item.get("alias", item.get("name")),
        "is_online": item.get("status", False),
        "voltage": item.get("voltage"),
        "rssi": station.get("rssi"),
        "usb_state": item.get("usbState", item.get("usb_state")),
        "device_type": devtype.get("name", str(devtype.get("type", ""))),
        "screen_type": screentype.get("name", f"{screentype.get('width','')}x{screentype.get('height','')}"),
        "sn": item.get("sn"),
        "sw_version": item.get("sw"),
        "hw_version": item.get("hw"),
        "created_at": created_at,
        "updated_at": updated_at,
    }


@router.get("")
async def get_device_list(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default=""),
    status: str = Query(default=None),
):
    """获取设备列表"""
    logger.info(f"[API /devices] ========== 获取设备列表请求开始 ==========")
    logger.info(f"[API /devices] 请求参数: page={page}, page_size={page_size}, search={search}, status={status}")
    logger.debug(f"[API /devices] 请求头: {dict(request.headers)}")
    
    # 从请求头提取Authorization
    auth_header = request.headers.get("authorization", "")
    logger.info(f"[API /devices] Authorization头: {auth_header[:50]}...")
    
    api_key = _get_api_key(request)
    if not api_key:
        logger.warning(f"[API /devices] ❌ 未找到有效的API Key，返回401未授权")
        logger.warning(f"[API /devices] Auth头格式: {'Bearer ' if auth_header.startswith('Bearer ') else '不正确'}")
        return {"code": 40100, "message": "未授权，请先登录", "data": None}

    logger.info(f"[API /devices] ✅ 提取到的API Key: {api_key[:8]}... (长度: {len(api_key)})")
    logger.info(f"[API /devices] API Key格式检查:")
    logger.info(f"[API /devices]   - 是JWT格式 (eyJ开头): {api_key.startswith('eyJ')}")
    logger.info(f"[API /devices]   - 长度: {len(api_key)} 字符")
    logger.info(f"[API /devices]   - 是WIFI_APIKEY格式 (24字符): {len(api_key) == 24}")
    
    try:
        query_parts = []
        if status:
            query_parts.append(status)
        if search:
            query_parts.append(search)
        
        query_str = ",".join(query_parts)
        logger.info(f"[API /devices] 构造的查询参数: {query_str}")

        logger.info(f"[API /devices] 开始调用wifi_proxy.get_devices...")
        raw_data = await wifi_proxy.get_devices(
            api_key=api_key,
            page=page,
            page_size=page_size,
            query=query_str,
        )

        # DEBUG: 打印原始数据用于调试
        import json as _json
        logger.info(f"[API /devices] RAW device data type={type(raw_data).__name__}")
        if isinstance(raw_data, dict):
            logger.info(f"[API /devices] RAW device data keys={list(raw_data.keys())}")
            logger.info(f"[API /devices] RAW device data (first 800 chars): {_json.dumps(raw_data, ensure_ascii=False, indent=2)[:800]}")
        else:
            logger.info(f"[API /devices] RAW device data (type): {type(raw_data)}")

        # 真实系统返回格式: { code:20000, data:{ items:[...], total:N } }
        inner_data = raw_data.get("data", raw_data) if isinstance(raw_data, dict) else raw_data

        # inner_data 可能是 { items:[], total:N } 或直接是列表
        if isinstance(inner_data, dict):
            items = inner_data.get("items", [])
            total = inner_data.get("total", len(items))
        elif isinstance(inner_data, list):
            items = inner_data
            total = len(inner_data)
        else:
            items = []
            total = 0

        # 统一设备数据格式 (真实系统返回小写字段)
        normalized_items = []
        for item in (items if isinstance(items, list) else []):
            if isinstance(item, dict):
                # 提取嵌套的子对象字段
                station = item.get("station") or {}
                screentype = item.get("screentype") or item.get("screen_type") or {}
                devtype = item.get("devtype") or item.get("device_type") or {}
                created_at, updated_at = _extract_timestamp(item)
                
                normalized_items.append({
                    "id": item.get("_id", item.get("id", "")),
                    "mac": item.get("mac", ""),
                    "ip": item.get("ip", ""),
                    "name": item.get("alias", item.get("name")),
                    "is_online": item.get("status", False),
                    "voltage": item.get("voltage"),
                    "rssi": station.get("rssi"),
                    "usb_state": item.get("usbState", item.get("usb_state")),
                    "device_type": devtype.get("name", str(devtype.get("type", ""))),
                    "screen_type": screentype.get("name", f"{screentype.get('width','')}x{screentype.get('height','')}"),
                    "sn": item.get("sn"),
                    "sw_version": item.get("sw"),
                    "hw_version": item.get("hw"),
                    "created_at": created_at,
                    "updated_at": updated_at,
                })

        return {
            "code": 20000,
            "message": "",
            "data": {
                "total": total,
                "page": page,
                "pageSize": page_size,
                "items": normalized_items,
            },
        }
    except Exception as e:
        return {"code": 50000, "message": f"获取设备列表失败: {e}", "data": None}


@router.get("/mac/{mac}")
async def get_device_by_mac(mac: str, request: Request):
    """根据MAC地址查询设备"""
    api_key = _get_api_key(request)
    if not api_key:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        raw_data = await wifi_proxy.get_device_by_mac(mac, api_key)
        # 归一化字段（与列表接口保持一致）
        data = _normalize_single_device(raw_data)
        return {"code": 20000, "message": "", "data": data}
    except Exception as e:
        logger.error(f"按MAC查询设备失败: {e}")
        return {"code": 50000, "message": str(e), "data": None}



@router.post("")
async def create_device(request: Request, body: dict):
    """添加设备 (暂不支持，转发给真实系统)"""
    return {"code": 50100, "message": "设备需通过WIFI标签系统注册，此接口暂不可用", "data": None}


# ============================================================
# 本地数据库查询接口 (MQTT事件持久化数据)
# ============================================================

@router.get("/events")
async def get_device_events(
    mac: str = Query(default=None, description="按MAC过滤"),
    event_type: str = Query(default=None, description="事件类型: online/offline/button/battery_reply等"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """
    查询本地存储的设备事件记录 (来自MQTT消息持久化)
    
    示例:
      GET /api/v1/devices/events              → 最近50条所有事件
      GET /api/v1/devices/events?mac=D4:3D:39 → 指定设备的最近事件
      GET /api/v1/devices/events?event_type=online → 所有上线事件
      GET /api/v1/devices/events?mac=D4:3D:39&event_type=button&page=1&page_size=20
    """
    from services.db_service import get_device_events as _get_events

    try:
        items, total = await _get_events(
            mac=mac,
            event_type=event_type,
            page=page,
            page_size=page_size,
        )
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
    except Exception as e:
        logger.error(f"查询设备事件失败: {e}")
        return {"code": 50000, "message": f"查询失败: {e}", "data": None}


@router.get("/stats")
async def get_device_stats():
    """
    设备统计摘要 - 从本地DB获取实时统计
    
    返回: { total, online, offline, low_battery, online_rate }
    """
    from services.db_service import get_device_stats as _get_stats, get_all_devices as _get_all

    try:
        stats = await _get_stats()
        
        # 额外返回最近上线的10台设备
        recent_online = await _get_all_devices(online_only=True)
        stats["recent_online"] = recent_online[:10]

        return {
            "code": 20000,
            "message": "",
            "data": stats,
        }
    except Exception as e:
        logger.error(f"获取设备统计失败: {e}")
        return {"code": 50000, "message": f"查询失败: {e}", "data": None}


# ============================================================
# 模板-设备绑定接口（数据更新页面的设备列表持久化）
# 注意：必须放在 /{device_id} 动态路由之前，否则 template-devices 会被 device_id 匹配
# ============================================================

@router.post("/template-devices")
async def save_template_devices(request: Request, body: dict):
    """
    保存/批量保存模板-设备绑定关系
    Body: { tid: "tpl_001", macs: ["AA:BB:CC", "DD:EE:FF"] }
    """
    from services.db_service import save_template_bindings

    try:
        tid = body.get("tid", "")
        macs = body.get("macs", [])
        if not tid or not isinstance(macs, list):
            return {"code": 40000, "message": "参数错误: 需要tid和macs数组", "data": None}

        count = await save_template_bindings(tid, macs)
        return {
            "code": 20000,
            "message": f"已保存 {count} 台设备",
            "data": {"tid": tid, "count": count},
        }
    except Exception as e:
        logger.error(f"保存模板设备绑定失败: {e}")
        return {"code": 50000, "message": f"保存失败: {e}", "data": None}


@router.get("/template-devices")
async def get_template_devices(tid: str = Query(..., description="模板ID")):
    """查询某模板绑定的所有设备MAC地址"""
    from services.db_service import get_template_bound_macs

    try:
        macs = await get_template_bound_macs(tid)
        return {
            "code": 20000,
            "message": "",
            "data": {"tid": tid, "macs": macs, "total": len(macs)},
        }
    except Exception as e:
        logger.error(f"查询模板设备绑定失败: {e}")
        return {"code": 50000, "message": f"查询失败: {e}", "data": None}


@router.delete("/template-devices/{tid}/{mac}")
async def remove_template_device_binding(tid: str, mac: str):
    """
    移除单条模板-设备绑定
    仅从当前模板的更新列表中移除该设备，不删除设备本身
    """
    from services.db_service import remove_template_binding

    try:
        ok = await remove_template_binding(tid, mac)
        if ok:
            return {
                "code": 20000,
                "message": "已从更新列表移除",
                "data": {"tid": tid, "mac": mac},
            }
        else:
            return {"code": 40400, "message": "绑定记录不存在", "data": None}
    except Exception as e:
        logger.error(f"移除模板设备绑定失败: {e}")
        return {"code": 50000, "message": f"操作失败: {e}", "data": None}


# ============================================================
# 动态路由（必须放在所有固定路径之后）
# ============================================================

@router.get("/{device_id}")
async def get_device(device_id: str, request: Request):
    """获取单个设备详情"""
    api_key = _get_api_key(request)
    if not api_key:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        raw_data = await wifi_proxy.get_device_by_id(device_id, api_key)
        # 归一化字段
        data = _normalize_single_device(raw_data)
        return {"code": 20000, "message": "", "data": data}
    except Exception as e:
        return {"code": 50000, "message": str(e), "data": None}


@router.put("/{device_id}")
async def update_device(device_id: str, request: Request, body: dict):
    """更新设备信息"""
    return {"code": 50100, "message": "暂不支持直接修改设备信息", "data": None}


@router.delete("/{device_id}")
async def delete_device(device_id: str, request: Request):
    """删除设备"""
    return {"code": 50100, "message": "暂不支持删除设备", "data": None}
