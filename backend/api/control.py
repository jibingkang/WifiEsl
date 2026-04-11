"""
设备控制API - LED/重启/电量查询/屏幕更新/模板调用
POST /api/v1/mqtt/publish/:mac/{led|reboot|battery|display|template/:tid}
"""
from fastapi import APIRouter, Request

from services.wifi_client import wifi_proxy
from services.auth_service import get_api_key_from_request

router = APIRouter(prefix="/mqtt/publish", tags=["设备控制"])


def _get_api_key(request: Request) -> str | None:
    return get_api_key_from_request(dict(request.headers))


@router.post("/{mac}/led")
async def control_led(mac: str, request: Request, body: dict):
    """设置LED灯颜色 {red, green, blue}"""
    api_key = _get_api_key(request)
    if not api_key:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        red = int(body.get("red", 0))
        green = int(body.get("green", 0))
        blue = int(body.get("blue", 0))

        result = await wifi_proxy.control_led(mac, red, green, blue, api_key)
        return {"code": 20000, "message": "LED指令已发送", "data": result}
    except Exception as e:
        return {"code": 50000, "message": str(e), "data": None}


@router.post("/{mac}/battery")
async def query_battery(mac: str, request: Request):
    """查询设备电池电量 (同时同步到本地数据库)"""
    api_key = _get_api_key(request)
    if not api_key:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        result = await wifi_proxy.query_battery(mac, api_key)

        # 提取电压值，立即写入本地数据库
        if isinstance(result, dict):
            raw_voltage = (
                result.get("voltage")
                or result.get("voltage_mv")
            )
            if raw_voltage is not None:
                try:
                    from services.db_service import upsert_device
                    import datetime as _dt
                    now_iso = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    await upsert_device(mac, voltage=int(raw_voltage), last_seen_at=now_iso)
                    print(f"[Control] 电量查询结果已同步DB: mac={mac}, voltage={raw_voltage}")
                except Exception as db_err:
                    print(f"[Control] DB写入失败(不影响响应): {db_err}")

        return {"code": 20000, "message": "电量查询指令已发送", "data": result}
    except Exception as e:
        return {"code": 50000, "message": str(e), "data": None}


@router.post("/{mac}/reboot")
async def reboot_device(mac: str, request: Request):
    """重启指定设备"""
    api_key = _get_api_key(request)
    if not api_key:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        result = await wifi_proxy.reboot_device(mac, api_key)
        return {"code": 20000, "message": "重启指令已发送", "data": result}
    except Exception as e:
        return {"code": 50000, "message": str(e), "data": None}


@router.post("/{mac}/display")
async def update_display(mac: str, request: Request, body: dict):
    """更新设备屏幕内容 (图片或模板数据)"""
    api_key = _get_api_key(request)
    if not api_key:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        algorithm = body.get("algorithm", "floyd-steinberg")
        imgsrc = body.get("imgsrc")
        template_data = body.get("templateData") or body.get("template_data")

        result = await wifi_proxy.update_display(
            mac=mac,
            api_key=api_key,
            algorithm=algorithm,
            imgsrc=imgsrc,
            template_data=template_data,
        )
        return {"code": 20000, "message": "屏幕更新指令已发送", "data": result}
    except Exception as e:
        return {"code": 50000, "message": str(e), "data": None}


@router.post("/{mac}/template/{template_id}")
async def apply_template(mac: str, template_id: str, request: Request, body: dict):
    """调用模板显示到指定设备"""
    api_key = _get_api_key(request)
    if not api_key:
        return {"code": 40100, "message": "未授权", "data": None}

    try:
        data = body.get("data") or body
        result = await wifi_proxy.apply_template(mac, template_id, data, api_key)
        return {"code": 20000, "message": "模板调用指令已发送", "data": result}
    except Exception as e:
        return {"code": 50000, "message": str(e), "data": None}
