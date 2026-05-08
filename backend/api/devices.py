"""
设备管理API - 设备CRUD代理到真实WIFI系统
GET/POST/PUT/DELETE /api/v1/devices
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Query, Request

from services.wifi_connection_manager import wifi_connection_manager
from services.auth_service import get_api_key_from_request as get_auth_api_key, get_current_user_id_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["设备管理"])


async def _get_user_wifi_token(request: Request) -> str | None:
    """获取用户的WIFI系统token"""
    try:
        # 从请求中获取当前用户ID
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
        return await wifi_connection_manager.get_token_for_user(user_id)
    except Exception as e:
        logger.error(f"获取用户WIFI token失败: {e}")
        return None


def _extract_timestamp(item: dict) -> tuple[str, str]:
    """从原始设备数据中提取创建/更新时间，返回 (created_at, updated_at)"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    search: str = Query(default=""),
    status: str = Query(default=None),
):
    """获取设备列表"""
    logger.info(f"[API /devices] ========== 获取设备列表请求开始 ==========")
    logger.info(f"[API /devices] 请求参数: page={page}, page_size={page_size}, search={search}, status={status}")
    logger.info(f"[API /devices] 全部query参数: {dict(request.query_params)}")
    logger.debug(f"[API /devices] 请求头: {dict(request.headers)}")
    
    # 从请求头提取Authorization
    auth_header = request.headers.get("authorization", "")
    logger.info(f"[API /devices] Authorization头: {auth_header[:50]}...")
    
    # 获取用户的WIFI系统token
    from services.auth_service import get_current_user_id_from_token
    
    # 提取token（去掉Bearer前缀）
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
    if not token:
        logger.warning(f"[API /devices] ❌ 未找到有效的token，返回401未授权")
        return {"code": 40100, "message": "未授权，请先登录", "data": None}
    
    # 从token获取用户ID
    user_id = get_current_user_id_from_token(token)
    if not user_id:
        logger.warning(f"[API /devices] ❌ 无法从token获取用户ID")
        return {"code": 40100, "message": "无效的token", "data": None}
    
    logger.info(f"[API /devices] ✅ 用户ID: {user_id}")
    
    # 获取用户的WIFI连接
    conn = await wifi_connection_manager.get_connection(user_id)
    if not conn or not conn.token:
        logger.error(f"[API /devices] ❌ 用户 {user_id} 的WIFI连接或token无效")
        return {"code": 50000, "message": "WIFI系统连接失败，请检查WIFI配置", "data": None}
    
    api_key = conn.token
    base_url = conn.wifi_base_url
    
    logger.info(f"[API /devices] ✅ 使用用户 {user_id} 的WIFI配置: base_url={base_url}")
    logger.info(f"[API /devices] ✅ WIFI系统token: {api_key[:8]}... (长度: {len(api_key)})")
    
    try:
        # 不传 query 给 WIFI，拿全量数据后在本地做模糊筛选
        logger.info(f"[API /devices] 构造的查询参数: search={search}, status={status}")
        logger.info(f"[API /devices] 开始调用WIFI系统获取设备列表(全量)...")

        from services.wifi_client import wifi_proxy
        raw_data = await wifi_proxy.get_devices(
                api_key=api_key,
                base_url=base_url,
                page=1,
                page_size=20,  # WIFI标准分页大小
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
            wf_total = inner_data.get("total", len(items))
        elif isinstance(inner_data, list):
            items = inner_data
            wf_total = len(inner_data)
        else:
            items = []
            wf_total = 0

        # 如果WIFI系统返回的total>当前items数量，翻页获取全部数据
        if isinstance(items, list) and wf_total > len(items) and isinstance(inner_data, dict):
            import math
            remaining = wf_total - len(items)
            logger.info(f"[API /devices] WIFI系统返回 total={wf_total}, items={len(items)}, 还需获取 {remaining} 条")
            for wp in range(2, math.ceil(wf_total / len(items)) + 1):
                try:
                    next_raw = await wifi_proxy.get_devices(
                        api_key=api_key,
                        base_url=base_url,
                        page=wp,
                        page_size=20,
                    )
                    n_inner = next_raw.get("data", next_raw) if isinstance(next_raw, dict) else next_raw
                    n_items = n_inner.get("items", []) if isinstance(n_inner, dict) else (n_inner if isinstance(n_inner, list) else [])
                    items.extend(n_items)
                    logger.info(f"[API /devices]  第{wp}页获取 {len(n_items)} 条，累计 {len(items)} 条")
                except Exception as e:
                    logger.warning(f"[API /devices] 获取第{wp}页失败: {e}")
                    break
        total = wf_total

        # 统一设备数据格式 (真实系统返回小写字段)
        normalized_items = []
        status_samples = []  # 调试：收集status值
        for item in (items if isinstance(items, list) else []):
            if isinstance(item, dict):
                raw_status = item.get("status")
                if len(status_samples) < 5:
                    status_samples.append(f"{item.get('mac','?')}: status={raw_status}({type(raw_status).__name__})")
                # 提取嵌套的子对象字段
                station = item.get("station") or {}
                screentype = item.get("screentype") or item.get("screen_type") or {}
                devtype = item.get("devtype") or item.get("device_type") or {}
                created_at, updated_at = _extract_timestamp(item)
                
                # 归一化 is_online：WIFI可能返回 bool/int/str
                if raw_status is True or raw_status == 1 or (isinstance(raw_status, str) and raw_status.lower() in ("online", "true", "1")):
                    is_online = True
                elif raw_status is False or raw_status == 0 or (isinstance(raw_status, str) and raw_status.lower() in ("offline", "false", "0")):
                    is_online = False
                else:
                    is_online = False  # 默认离线
                
                normalized_items.append({
                    "id": item.get("_id", item.get("id", "")),
                    "mac": item.get("mac", ""),
                    "ip": item.get("ip", ""),
                    "name": item.get("alias", item.get("name")),
                    "is_online": is_online,
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

        # 调试日志：打印status采样值，检查在线/离线状态来源
        if status_samples:
            logger.info(f"[API /devices] status采样: {status_samples}")

        # 本地过滤：模糊搜索（MAC + 名称）
        if search:
            kw = search.lower()
            normalized_items = [
                d for d in normalized_items
                if kw in d.get("mac", "").lower() or kw in d.get("name", "").lower()
            ]
            logger.info(f"[API /devices] 搜索过滤后: {len(normalized_items)} 台设备 (search={search})")

        # 本地过滤：在线状态筛选
        if status:
            if status == "online":
                normalized_items = [d for d in normalized_items if d.get("is_online")]
            elif status == "offline":
                normalized_items = [d for d in normalized_items if not d.get("is_online")]
            logger.info(f"[API /devices] 状态过滤后: {len(normalized_items)} 台设备 (status={status})")

        total = len(normalized_items)

        # 分页切片
        start = (page - 1) * page_size
        paged_items = normalized_items[start:start + page_size]

        return {
            "code": 20000,
            "message": "",
            "data": {
                "total": total,
                "page": page,
                "pageSize": page_size,
                "items": paged_items,
            },
        }
    except Exception as e:
        return {"code": 50000, "message": f"获取设备列表失败: {e}", "data": None}


@router.get("/mac/{mac}")
async def get_device_by_mac(mac: str, request: Request):
    """根据MAC地址查询设备"""
    # 获取用户的WIFI系统token
    token = await _get_user_wifi_token(request)
    if not token:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        # 获取用户ID和连接信息
        from services.auth_service import get_current_user_id_from_token
        auth_header = request.headers.get("authorization", "")
        user_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
        user_id = get_current_user_id_from_token(user_token)
        
        if not user_id:
            return {"code": 40100, "message": "无效的token", "data": None}
        
        # 获取用户的WIFI连接
        conn = await wifi_connection_manager.get_connection(user_id)
        if not conn:
            return {"code": 50000, "message": "WIFI系统连接失败", "data": None}
        
        from services.wifi_client import wifi_proxy
        raw_data = await wifi_proxy.get_device_by_mac(mac, token, conn.wifi_base_url)
        logger.info(f"[MAC查询设备] WIFI系统原始响应: {raw_data}")
        # 归一化字段（与列表接口保持一致）
        data = _normalize_single_device(raw_data)
        logger.info(f"[MAC查询设备] 归一化后数据: {data}")
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


@router.get("/alerts")
async def get_device_alerts():
    """
    登录后即时告警摘要 - 返回需要关注的异常设备
    返回: {
      offline_count, offline_devices(最近10台),
      low_battery_count, low_battery_devices(最近10台)
    }
    """
    from services.db_service import get_db

    try:
        db = await get_db()

        # 离线设备：is_online=0，按最后在线时间降序，取最近10台
        offline_cur = await db.execute(
            "SELECT COUNT(*) as cnt FROM devices WHERE is_online=0"
        )
        offline_count = (await offline_cur.fetchone())["cnt"]

        offline_rows_cur = await db.execute(
            "SELECT mac, COALESCE(NULLIF(name, ''), mac) AS name, is_online, voltage, last_seen_at "
            "FROM devices WHERE is_online=0 ORDER BY last_seen_at DESC LIMIT 10"
        )
        offline_devices = [dict(r) for r in await offline_rows_cur.fetchall()]

        # 低电量设备：在线且 voltage < 350（即 <3.50V），按电压升序，取最近10台
        low_battery_cur = await db.execute(
            "SELECT COUNT(*) as cnt FROM devices WHERE is_online=1 AND voltage < 350 AND voltage IS NOT NULL"
        )
        low_battery_count = (await low_battery_cur.fetchone())["cnt"]

        low_battery_rows_cur = await db.execute(
            "SELECT mac, COALESCE(NULLIF(name, ''), mac) AS name, is_online, voltage, last_seen_at FROM devices "
            "WHERE is_online=1 AND voltage < 350 AND voltage IS NOT NULL "
            "ORDER BY voltage ASC LIMIT 10"
        )
        low_battery_devices = [dict(r) for r in await low_battery_rows_cur.fetchall()]

        return {
            "code": 20000,
            "message": "",
            "data": {
                "offline_count": offline_count,
                "offline_devices": offline_devices,
                "low_battery_count": low_battery_count,
                "low_battery_devices": low_battery_devices,
            },
        }
    except Exception as e:
        logger.error(f"获取设备告警失败: {e}")
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
    # 获取用户的WIFI系统token
    token = await _get_user_wifi_token(request)
    if not token:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        # 获取用户ID和连接信息
        from services.auth_service import get_current_user_id_from_token
        auth_header = request.headers.get("authorization", "")
        user_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
        user_id = get_current_user_id_from_token(user_token)
        
        if not user_id:
            return {"code": 40100, "message": "无效的token", "data": None}
        
        # 获取用户的WIFI连接
        conn = await wifi_connection_manager.get_connection(user_id)
        if not conn:
            return {"code": 50000, "message": "WIFI系统连接失败", "data": None}
        
        from services.wifi_client import wifi_proxy
        raw_data = await wifi_proxy.get_device_by_id(device_id, token)
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
