"""
WIFI系统HTTP客户端 - 代理转发到真实WIFI标签系统
使用 httpx 异步客户端封装所有对真实系统的HTTP请求
"""
import httpx
import json
import logging

from config import settings

logger = logging.getLogger(__name__)

# 全局异步HTTP客户端 (单例复用连接池)
_client: httpx.AsyncClient | None = None


def get_wifi_client() -> httpx.AsyncClient:
    """获取或创建全局httpx客户端"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.wifi_base_url,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=30.0),
            headers={"Content-Type": "application/json"},
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
        )
    return _client


async def close_wifi_client():
    """关闭HTTP客户端"""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


class WifiSystemProxy:
    """
    WIFI标签系统代理类
    封装所有与真实WIFI系统的HTTP交互
    """

    @staticmethod
    async def login(username: str, password: str) -> dict:
        """
        代理登录请求
        POST /user/api/login → 返回 {token, apiKey, user}
        """
        client = get_wifi_client()
        try:
            resp = await client.post(
                "/user/api/login",
                json={"username": username, "password": password},
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"登录成功, 用户: {username}")
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"登录失败: {e.response.status_code} - {e.response.text}")
            raise Exception(f"WIFI系统登录失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"登录异常: {e}")
            raise Exception(f"无法连接WIFI系统: {e}")

    @staticmethod
    async def get_devices(
        api_key: str,
        page: int = 1,
        page_size: int = 20,
        query: str = "",
    ) -> dict:
        """
        获取设备列表
        GET /user/api/rest/devices
        """
        client = get_wifi_client()
        params = {"page": page, "page_size": page_size}
        if query:
            params["query"] = query
        try:
            resp = await client.get(
                "/user/api/rest/devices",
                headers=_headers(api_key),
                params=params,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code}: {e.response.text}")
            raise Exception(f"获取设备列表失败: {e.response.status_code} - {e.response.text[:200]}")
        except Exception as e:
            import traceback
            logger.error(f"设备列表请求异常: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            raise Exception(f"设备列表请求异常: {type(e).__name__}: {e}")

    @staticmethod
    async def get_device_by_id(device_id: str, api_key: str) -> dict:
        """GET /user/api/rest/devices/:id"""
        client = get_wifi_client()
        try:
            resp = await client.get(
                f"/user/api/rest/devices/{device_id}",
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"获取设备详情失败: {e.response.status_code}")

    @staticmethod
    async def get_device_by_mac(mac: str, api_key: str) -> dict:
        """GET /user/api/rest/devices/mac/:mac"""
        client = get_wifi_client()
        try:
            resp = await client.get(
                f"/user/api/rest/devices/mac/{mac}",
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"MAC查询设备失败: {e.response.status_code}")

    @staticmethod
    async def control_led(
        mac: str, red: int, green: int, blue: int, api_key: str
    ) -> dict:
        """POST /user/api/mqtt/publish/:mac/led"""
        client = get_wifi_client()
        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/led",
                json={"red": red, "green": green, "blue": blue},
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"LED控制失败: {e.response.status_code} - {e.response.text}")

    @staticmethod
    async def query_battery(mac: str, api_key: str) -> dict:
        """POST /user/api/mqtt/publish/:mac/battery"""
        client = get_wifi_client()
        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/battery",
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"电量查询失败: {e.response.status_code}")

    @staticmethod
    async def reboot_device(mac: str, api_key: str) -> dict:
        """POST /user/api/mqtt/publish/:mac/reboot"""
        client = get_wifi_client()
        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/reboot",
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"重启指令发送失败: {e.response.status_code}")

    @staticmethod
    async def update_display(
        mac: str,
        api_key: str,
        algorithm: str = "floyd-steinberg",
        imgsrc: str | None = None,
        template_data: dict | None = None,
    ) -> dict:
        """POST /user/api/mqtt/publish/:mac/display"""
        client = get_wifi_client()
        payload: dict = {}
        if imgsrc:
            payload["algorithm"] = algorithm
            payload["imgsrc"] = imgsrc
        elif template_data:
            payload = template_data
        else:
            payload["algorithm"] = algorithm

        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/display",
                json=payload,
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"屏幕更新失败: {e.response.status_code}")

    @staticmethod
    async def apply_template(
        mac: str, template_id: str, data: dict, api_key: str,
        template_name: str = "",
    ) -> dict:
        """
        POST /user/api/mqtt/publish/{mac}/template/{templateId}

        请求体格式(按API文档):
        {
            "tid": "模板ID",
            "tname": "模板名称",
            "data": { ...模板变量数据 }
        }
        """
        client = get_wifi_client()
        url = f"/user/api/mqtt/publish/{mac}/template/{template_id}"

        # 按API文档构造请求体: tid + tname + data
        payload = {
            "tid": template_id,
            "tname": template_name,
            "data": data,
        }

        print(f"\n  >>> 推送设备 {mac} 模板 {template_id}")
        print(f"  >>> URL: {url}")
        print(f"  >>> 数据: {json.dumps(payload, ensure_ascii=False)[:500]}")

        logger.info(f"=== 推送模板到设备 ===")
        logger.info(f"  MAC: {mac}")
        logger.info(f"  模板ID: {template_id}")
        logger.info(f"  模板名称: {template_name}")
        logger.info(f"  请求URL: {url}")
        logger.info(f"  请求数据: {json.dumps(payload, ensure_ascii=False)}")
        try:
            resp = await client.post(
                url,
                json=payload,
                headers=_headers(api_key),
            )
            logger.info(f"  响应状态码: {resp.status_code}")
            resp_text = resp.text
            logger.info(f"  响应内容: {resp_text[:1000]}")
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"  设备 {mac} 模板推送成功")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"  设备 {mac} 模板推送HTTP错误: {e.response.status_code} - {e.response.text[:500]}")
            raise Exception(f"模板调用失败: {e.response.status_code}")
        except httpx.ReadTimeout:
            logger.error(f"  设备 {mac} 模板推送读取超时 (ReadTimeout)")
            raise Exception(f"模板调用失败: 设备响应超时(30s)，请检查设备是否在线")
        except httpx.ConnectError as e:
            logger.error(f"  设备 {mac} 模板推送连接错误: {e}")
            raise Exception(f"模板调用失败: 无法连接WIFI系统 - {e}")
        except Exception as e:
            import traceback
            logger.error(f"  设备 {mac} 模板推送异常: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            raise Exception(f"模板调用失败: {type(e).__name__}: {e}")


def _headers(api_key: str) -> dict:
    """构建带认证的请求头 (使用Bearer Token)"""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


# 全局代理实例
wifi_proxy = WifiSystemProxy()
