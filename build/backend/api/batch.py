"""
批量操作API - 批量模板应用等
POST /api/v1/batch/template 等
"""
import asyncio
import json
import logging
from fastapi import APIRouter, Request
from services.wifi_client import wifi_proxy
from services.auth_service import get_current_user_id_from_token
from services.wifi_connection_manager import wifi_connection_manager
from services.db_service import add_log

router = APIRouter(prefix="/batch", tags=["批量操作"])
logger = logging.getLogger(__name__)


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


@router.post("/template")
async def batch_apply_template(request: Request, body: dict):
    """
    批量应用模板到多个设备
    POST { macs: ["AA:BB:CC...", ...], templateId: "xxx", dataList: [{...}, ...] }
    """
    print("\n========== 【BATCH】收到批量推送请求 ==========")
    print(f"  请求体: {json.dumps(body, ensure_ascii=False)[:500]}")
    
    logger.info(f"========== 收到批量推送请求 ==========")
    logger.info(f"  请求体原始内容: {json.dumps(body, ensure_ascii=False)}")
    
    wifi_token, wifi_base_url = await _get_wifi_config(request)
    print(f"  WIFI Token: {'有' if wifi_token else '无'}")
    print(f"  WIFI Base URL: {wifi_base_url}")
    logger.info(f"  WIFI Token: {'有' if wifi_token else '无'} ({str(wifi_token)[:20]}...)")
    logger.info(f"  WIFI Base URL: {wifi_base_url}")
    
    if not wifi_token:
        print("  >>> 拒绝: 未授权")
        logger.warning("  >>> 拒绝: 未授权 (无WIFI Token)")
        return {"code": 40100, "message": "未授权", "data": None}

    macs = body.get("macs", [])
    template_id = body.get("templateId") or body.get("template_id")
    template_name = body.get("templateName") or body.get("template_name") or ""
    data_list = body.get("dataList") or body.get("data_list") or [{}] * len(macs)

    print(f"  MACs={macs}, tid={template_id}, tname={template_name}, data_count={len(data_list)}")
    logger.info(f"  MAC列表: {macs}")
    logger.info(f"  模板ID: {template_id}")
    logger.info(f"  模板名称: {template_name}")
    logger.info(f"  数据条数: {len(data_list)}")

    if not macs:
        print("  >>> 拒绝: MAC列表为空")
        logger.warning("  >>> 拒请: MAC列表为空")
        return {"code": 40000, "message": "请选择至少一个设备", "data": None}
    
    if not wifi_token:
        logger.warning("  >>> 拒绝: 未授权 (无WIFI Token)")
        return {"code": 40100, "message": "未授权", "data": None}

    if not template_id:
        return {"code": 40000, "message": "请选择模板", "data": None}

    results = []
    success_count = 0
    failed_count = 0

    # 并发发送模板调用请求 (限制并发数避免压垮系统)
    semaphore = asyncio.Semaphore(5)

    async def _apply_one(mac: str, data: dict) -> dict:
        nonlocal success_count, failed_count
        async with semaphore:
            try:
                result = await wifi_proxy.apply_template(mac, template_id, data, wifi_token, template_name=template_name, base_url=wifi_base_url)
                success_count += 1
                return {"mac": mac, "success": True, "result": result}
            except Exception as e:
                failed_count += 1
                logger.warning(f"设备 {mac} 推送失败: {e}")
                return {"mac": mac, "success": False, "error": str(e)}

    tasks = [_apply_one(mac, data) for mac, data in zip(macs, data_list)]
    results = list(await asyncio.gather(*tasks))

    # 写入操作日志
    try:
        detail = json.dumps({
            "templateId": template_id,
            "deviceCount": len(macs),
            "successCount": success_count,
            "failedCount": failed_count,
            "results": [
                {"mac": r["mac"], "success": r.get("success", False), "error": r.get("error")}
                for r in results
            ],
        }, ensure_ascii=False)
        await add_log(
            username="",
            action="batch_update_template",
            target_type="template",
            target_id=template_id,
            detail=detail,
            result="success" if failed_count == 0 else "partial_failure",
        )
    except Exception as log_err:
        logger.warning(f"写入操作日志失败: {log_err}")

    return {
        "code": 20000,
        "message": f"批量操作完成: 成功{success_count}个, 失败{failed_count}个",
        "data": {
            "total": len(macs),
            "success": success_count,
            "failed": failed_count,
            "results": results,
        },
    }


@router.post("/control/led")
async def batch_control_led(request: Request, body: dict):
    """批量设置LED颜色"""
    wifi_token, wifi_base_url = await _get_wifi_config(request)
    if not wifi_token:
        return {"code": 40100, "message": "未授权", "data": None}

    macs = body.get("macs", [])
    red = body.get("red", 0)
    green = body.get("green", 0)
    blue = body.get("blue", 0)

    results = []
    for mac in macs:
        try:
            r = await wifi_proxy.control_led(mac, red, green, blue, wifi_token, base_url=wifi_base_url)
            results.append({"mac": mac, "success": True, "result": r})
        except Exception as e:
            results.append({"mac": mac, "success": False, "error": str(e)})

    return {
        "code": 20000,
        "message": "批量LED控制完成",
        "data": {"total": len(macs), "results": results},
    }


@router.post("/control/reboot")
async def batch_reboot(request: Request, body: dict):
    """批量重启设备"""
    wifi_token, wifi_base_url = await _get_wifi_config(request)
    if not wifi_token:
        return {"code": 40100, "message": "未授权", "data": None}

    macs = body.get("macs", [])
    results = []
    for mac in macs:
        try:
            r = await wifi_proxy.reboot_device(mac, wifi_token, base_url=wifi_base_url)
            results.append({"mac": mac, "success": True, "result": r})
        except Exception as e:
            results.append({"mac": mac, "success": False, "error": str(e)})

    return {
        "code": 20000,
        "message": "批量重启指令已发送",
        "data": {"total": len(macs), "results": results},
    }
