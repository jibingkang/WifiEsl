"""
WIFI系统HTTP客户端 - 代理转发到真实WIFI标签系统
使用 httpx 异步客户端封装所有对真实系统的HTTP请求
"""
import httpx
import json
import logging

from config import settings

logger = logging.getLogger(__name__)

# 全局异步HTTP客户端缓存，按base_url存储
_clients: dict[str, httpx.AsyncClient] = {}


def get_wifi_client(base_url: str | None = None) -> httpx.AsyncClient:
    """获取或创建httpx客户端，支持不同base_url"""
    global _clients
    
    # 如果没有指定base_url，使用默认配置
    if base_url is None:
        from config import settings
        base_url = settings.wifi_base_url
    
    # 检查是否已有对应base_url的客户端
    if base_url in _clients:
        client = _clients[base_url]
        if not client.is_closed:
            return client
        else:
            # 客户端已关闭，从缓存中移除
            del _clients[base_url]
    
    # 创建新的客户端
    client = httpx.AsyncClient(
        base_url=base_url,
        timeout=httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=30.0),  # 统一30秒超时
        headers={"Content-Type": "application/json"},
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),  # 增加连接池限制以支持批量推送
        follow_redirects=True,  # 启用重定向跟随
    )
    _clients[base_url] = client
    logger.info(f"创建新的WIFI客户端: {base_url}")
    return client


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
    async def login(username: str, password: str, base_url: str | None = None) -> dict:
        """
        代理登录请求
        POST /user/api/login → 返回 {token, apiKey, user}
        """
        client = get_wifi_client(base_url)
        
        # 详细的日志记录
        logger.info(f"[登录WIFI系统] ========== 开始登录 ==========")
        logger.info(f"[登录WIFI系统] 目标地址: {client.base_url}/user/api/login")
        logger.info(f"[登录WIFI系统] 传入的用户名: {username}")
        logger.info(f"[登录WIFI系统] 传入的密码长度: {len(password)} 字符")
        logger.info(f"[登录WIFI系统] 密码哈希表示: {'*' * min(10, len(password))}")
        
        # 打印完整的请求体
        request_body = {"username": username, "password": password}
        logger.info(f"[登录WIFI系统] 完整请求体: {json.dumps(request_body, ensure_ascii=False)}")
        
        try:
            logger.debug(f"[登录WIFI系统] 发送POST请求...")
            resp = await client.post(
                "/user/api/login",
                json={"username": username, "password": password},
            )
            
            logger.info(f"[登录WIFI系统] 响应状态码: {resp.status_code}")
            logger.debug(f"[登录WIFI系统] 响应头: {dict(resp.headers)}")
            logger.debug(f"[登录WIFI系统] 响应内容: {resp.text[:200]}")
            
            resp.raise_for_status()
            data = resp.json()
            
            logger.info(f"[登录WIFI系统] 登录成功, 用户: {username}")
            logger.debug(f"[登录WIFI系统] 返回数据: apiKey={data.get('apiKey', '')[:8]}..., token={data.get('token', '')[:8]}...")
            
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"[登录WIFI系统] HTTP错误 {e.response.status_code}: {e.response.text}")
            logger.error(f"[登录WIFI系统] 请求URL: {e.request.url}")
            raise Exception(f"WIFI系统登录失败: {e.response.status_code}")
        except Exception as e:
            import traceback
            logger.error(f"[登录WIFI系统] 异常: {type(e).__name__}: {e}")
            logger.error(f"[登录WIFI系统] 异常堆栈: {traceback.format_exc()}")
            raise Exception(f"无法连接WIFI系统: {e}")

    @staticmethod
    async def get_devices(
        api_key: str,
        base_url: str | None = None,
        page: int = 1,
        page_size: int = 20,
        query: str = "",
    ) -> dict:
        """
        获取设备列表
        GET /user/api/rest/devices
        """
        client = get_wifi_client(base_url)
        params = {"page": page, "page_size": page_size}
        if query:
            params["query"] = query
        
        # 详细的日志记录
        logger.info(f"[获取设备列表] ========== 开始调用WIFI系统接口 ==========")
        logger.info(f"[获取设备列表] 目标地址: {client.base_url}/user/api/rest/devices")
        logger.info(f"[获取设备列表] Token: {api_key[:20]}... (长度: {len(api_key)})")
        logger.info(f"[获取设备列表] 请求参数: page={page}, page_size={page_size}, query={query}")
        logger.info(f"[获取设备列表] Token详细信息:")
        logger.info(f"[获取设备列表]   - Token前20字符: {api_key[:20]}")
        logger.info(f"[获取设备列表]   - Token完整内容: {api_key}")
        logger.info(f"[获取设备列表]   - Token长度: {len(api_key)} 字符")
        logger.info(f"[获取设备列表]   - Token是否JWT格式: {'是' if api_key.startswith('eyJ') else '否'}")
        
        try:
            logger.debug(f"[获取设备列表] 发送GET请求...")
            resp = await client.get(
                "/user/api/rest/devices",
                headers=_headers(api_key),
                params=params,
            )
            
            logger.info(f"[获取设备列表] 响应状态码: {resp.status_code}")
            logger.debug(f"[获取设备列表] 响应头: {dict(resp.headers)}")
            
            # 记录响应内容（前200字符）
            response_text = resp.text
            logger.debug(f"[获取设备列表] 响应内容 (前500字符): {response_text[:500]}")
            
            resp.raise_for_status()
            
            result = resp.json()
            # 正确计算设备数量：从data.items数组长度获取
            device_count = 0
            if isinstance(result, dict):
                data = result.get('data', {})
                if isinstance(data, dict):
                    items = data.get('items', [])
                    if isinstance(items, list):
                        device_count = len(items)
                elif isinstance(data, list):
                    device_count = len(data)
            
            logger.info(f"[获取设备列表] 成功获取设备列表，设备数量: {device_count}")
            logger.debug(f"[获取设备列表] 完整响应: {json.dumps(result, ensure_ascii=False)[:300]}")
            
            return result
        except httpx.HTTPError as e:
            logger.error(f"[获取设备列表] HTTP错误: {e}")
            raise Exception(f"获取设备列表失败: {str(e)}")
        except Exception as e:
            import traceback
            logger.error(f"[获取设备列表] 异常: {type(e).__name__}: {e}")
            logger.error(f"[获取设备列表] 异常堆栈: {traceback.format_exc()}")
            raise Exception(f"设备列表请求异常: {type(e).__name__}: {e}")

    @staticmethod
    async def get_device_by_id(device_id: str, api_key: str, base_url: str | None = None) -> dict:
        """GET /user/api/rest/devices/:id"""
        client = get_wifi_client(base_url)
        
        # 打印API调用信息和token
        logger.info(f"[获取设备详情] 开始调用WIFI系统接口")
        logger.info(f"[获取设备详情] 目标地址: {client.base_url}/user/api/rest/devices/{device_id}")
        logger.info(f"[获取设备详情] Token: {api_key[:20]}... (长度: {len(api_key)})")
        logger.info(f"[获取设备详情] Token完整内容: {api_key}")
        
        try:
            resp = await client.get(
                f"/user/api/rest/devices/{device_id}",
                headers=_headers(api_key),
            )
            
            logger.info(f"[获取设备详情] 响应状态码: {resp.status_code}")
            logger.debug(f"[获取设备详情] 响应内容: {resp.text[:200]}")
            
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"[获取设备详情] 成功获取设备 {device_id} 的详情")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[获取设备详情] HTTP错误 {e.response.status_code}: {e.response.text}")
            raise Exception(f"获取设备详情失败: {e.response.status_code}")

    @staticmethod
    async def get_device_by_mac(mac: str, api_key: str, base_url: str | None = None) -> dict:
        """GET /user/api/rest/devices/mac/:mac"""
        client = get_wifi_client(base_url)
        
        # 打印API调用信息和token
        logger.info(f"[MAC查询设备] 开始调用WIFI系统接口")
        logger.info(f"[MAC查询设备] 目标地址: {client.base_url}/user/api/rest/devices/mac/{mac}")
        logger.info(f"[MAC查询设备] Token: {api_key[:20]}... (长度: {len(api_key)})")
        logger.info(f"[MAC查询设备] Token完整内容: {api_key}")
        logger.info(f"[MAC查询设备] Token完整内容: {api_key}")
        
        try:
            resp = await client.get(
                f"/user/api/rest/devices/mac/{mac}",
                headers=_headers(api_key),
            )
            
            logger.info(f"[MAC查询设备] 响应状态码: {resp.status_code}")
            logger.debug(f"[MAC查询设备] 响应内容: {resp.text[:200]}")
            
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"[MAC查询设备] 成功通过MAC地址 {mac} 查询设备")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[MAC查询设备] HTTP错误 {e.response.status_code}: {e.response.text}")
            raise Exception(f"MAC查询设备失败: {e.response.status_code}")

    @staticmethod
    async def control_led(
        mac: str, red: int, green: int, blue: int, api_key: str, base_url: str | None = None
    ) -> dict:
        """POST /user/api/mqtt/publish/:mac/led"""
        client = get_wifi_client(base_url)
        
        # 打印API调用信息和token
        logger.info(f"[LED控制] 开始调用WIFI系统接口")
        logger.info(f"[LED控制] 目标地址: {client.base_url}/user/api/mqtt/publish/{mac}/led")
        logger.info(f"[LED控制] Token: {api_key[:20]}... (长度: {len(api_key)})")
        logger.info(f"[LED控制] Token完整内容: {api_key}")
        logger.info(f"[LED控制] LED参数: R={red}, G={green}, B={blue}")
        
        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/led",
                json={"red": red, "green": green, "blue": blue},
                headers=_headers(api_key),
            )
            
            logger.info(f"[LED控制] 响应状态码: {resp.status_code}")
            logger.debug(f"[LED控制] 响应内容: {resp.text[:200]}")
            
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"[LED控制] 成功控制设备 {mac} 的LED灯")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[LED控制] HTTP错误 {e.response.status_code}: {e.response.text}")
            raise Exception(f"LED控制失败: {e.response.status_code} - {e.response.text}")

    @staticmethod
    async def query_battery(mac: str, api_key: str, base_url: str | None = None) -> dict:
        """POST /user/api/mqtt/publish/:mac/battery"""
        client = get_wifi_client(base_url)
        
        # 打印API调用信息和token
        logger.info(f"[电量查询] 开始调用WIFI系统接口")
        logger.info(f"[电量查询] 目标地址: {client.base_url}/user/api/mqtt/publish/{mac}/battery")
        logger.info(f"[电量查询] Token: {api_key[:20]}... (长度: {len(api_key)})")
        logger.info(f"[电量查询] Token完整内容: {api_key}")
        
        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/battery",
                headers=_headers(api_key),
            )
            
            logger.info(f"[电量查询] 响应状态码: {resp.status_code}")
            logger.debug(f"[电量查询] 响应内容: {resp.text[:200]}")
            
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"[电量查询] 成功查询设备 {mac} 的电量信息")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[电量查询] HTTP错误 {e.response.status_code}: {e.response.text}")
            raise Exception(f"电量查询失败: {e.response.status_code}")

    @staticmethod
    async def reboot_device(mac: str, api_key: str, base_url: str | None = None) -> dict:
        """POST /user/api/mqtt/publish/:mac/reboot"""
        client = get_wifi_client(base_url)
        
        # 打印API调用信息和token
        logger.info(f"[重启设备] 开始调用WIFI系统接口")
        logger.info(f"[重启设备] 目标地址: {client.base_url}/user/api/mqtt/publish/{mac}/reboot")
        logger.info(f"[重启设备] Token: {api_key[:20]}... (长度: {len(api_key)})")
        logger.info(f"[重启设备] Token完整内容: {api_key}")
        
        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/reboot",
                headers=_headers(api_key),
            )
            
            logger.info(f"[重启设备] 响应状态码: {resp.status_code}")
            logger.debug(f"[重启设备] 响应内容: {resp.text[:200]}")
            
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"[重启设备] 成功发送重启指令到设备 {mac}")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[重启设备] HTTP错误 {e.response.status_code}: {e.response.text}")
            raise Exception(f"重启指令发送失败: {e.response.status_code}")

    @staticmethod
    async def update_display(
        mac: str,
        api_key: str,
        algorithm: str = "floyd-steinberg",
        imgsrc: str | None = None,
        template_data: dict | None = None,
        base_url: str | None = None,
    ) -> dict:
        """POST /user/api/mqtt/publish/:mac/display"""
        client = get_wifi_client(base_url)
        payload: dict = {}
        if imgsrc:
            payload["algorithm"] = algorithm
            payload["imgsrc"] = imgsrc
        elif template_data:
            payload = template_data
        else:
            payload["algorithm"] = algorithm

        # 打印API调用信息和token
        logger.info(f"[屏幕更新] 开始调用WIFI系统接口")
        logger.info(f"[屏幕更新] 目标地址: {client.base_url}/user/api/mqtt/publish/{mac}/display")
        logger.info(f"[屏幕更新] Token: {api_key[:20]}... (长度: {len(api_key)})")
        logger.info(f"[屏幕更新] Token完整内容: {api_key}")
        logger.info(f"[屏幕更新] 请求数据: {json.dumps(payload, ensure_ascii=False)[:500]}")
        
        try:
            resp = await client.post(
                f"/user/api/mqtt/publish/{mac}/display",
                json=payload,
                headers=_headers(api_key),
            )
            
            logger.info(f"[屏幕更新] 响应状态码: {resp.status_code}")
            logger.debug(f"[屏幕更新] 响应内容: {resp.text[:200]}")
            
            resp.raise_for_status()
            result = resp.json()
            logger.info(f"[屏幕更新] 成功更新设备 {mac} 的屏幕显示")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[屏幕更新] HTTP错误 {e.response.status_code}: {e.response.text}")
            raise Exception(f"屏幕更新失败: {e.response.status_code}")

    @staticmethod
    async def apply_template(
        mac: str, template_id: str, data: dict, api_key: str,
        template_name: str = "",
        base_url: str | None = None,
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
        client = get_wifi_client(base_url)
        url = f"/user/api/mqtt/publish/{mac}/template/{template_id}"

        # 按API文档构造请求体: tid + tname + data
        payload = {
            "tid": template_id,
            "tname": template_name,
            "data": data,
        }

        logger.info(f"=== 推送模板到设备 ===")
        logger.info(f"  目标地址: {client.base_url}{url}")
        logger.info(f"  MAC: {mac}, 模板ID: {template_id}, 模板名称: {template_name}")
        logger.debug(f"  请求Token: {api_key[:20]}...")
        logger.debug(f"  请求数据: {json.dumps(payload, ensure_ascii=False)}")
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
    # 检查api_key是否已经是Bearer格式
    if api_key.startswith("Bearer "):
        return {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
    else:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }


# 全局代理实例
wifi_proxy = WifiSystemProxy()
