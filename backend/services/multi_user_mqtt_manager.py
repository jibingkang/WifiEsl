#!/usr/bin/env python3
"""
多用户MQTT管理器 - 为每个用户管理独立的MQTT连接
每个用户使用自己的WIFI配置和API Key连接
"""
import asyncio
import logging
import time
import json
import base64
import threading
from typing import Optional, Dict, Any, Set
import paho.mqtt.client as mqtt

from .wifi_connection_manager import wifi_connection_manager
from .ws_manager import ws_manager
from .db_service import upsert_device, add_device_event, update_device_status_by_mac

logger = logging.getLogger(__name__)


class UserMQTTConnection:
    """单个用户的MQTT连接管理"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.subscribed_topics: Set[str] = set()
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.api_key: Optional[str] = None
        self.broker_host: Optional[str] = None
        self.broker_port: int = 1883
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """设置主事件循环引用"""
        self._main_loop = loop
    
    async def start(self) -> bool:
        """启动用户的MQTT连接"""
        try:
            # 获取用户的WIFI配置
            conn = await wifi_connection_manager.get_connection(self.user_id)
            if not conn:
                logger.error(f"用户 {self.user_id} 的WIFI连接不可用")
                return False
            
            # MQTT订阅使用用户的wifi_apikey（专门用于MQTT订阅）
            self.api_key = conn.wifi_apikey if conn.wifi_apikey else conn.token
            broker_url = conn.wifi_mqtt_broker
            
            # MQTT认证信息：优先使用用户配置的，否则使用默认
            mqtt_username = getattr(conn, 'mqtt_username', None) or "test"
            mqtt_password = getattr(conn, 'mqtt_password', None) or "123456"
            
            # 打印详细的MQTT连接信息
            logger.info(f"=" * 60)
            logger.info(f"[MQTT连接信息] 用户 {self.user_id}")
            logger.info(f"[MQTT连接信息]   - MQTT订阅API Key: {self.api_key[:20]}..." if self.api_key else "[MQTT连接信息]   - MQTT订阅API Key: None")
            logger.info(f"[MQTT连接信息]   - API Key长度: {len(self.api_key) if self.api_key else 0}")
            logger.info(f"[MQTT连接信息]   - 配置的Broker: {broker_url}")
            logger.info(f"[MQTT连接信息]   - MQTT用户名: {mqtt_username}")
            logger.info(f"[MQTT连接信息]   - MQTT密码: {'*' * len(mqtt_password)}")
            logger.info(f"=" * 60)
            
            if not self.api_key:
                logger.error(f"用户 {self.user_id} 的API Key不可用（用于MQTT订阅）")
                return False
            
            if not broker_url:
                logger.warning(f"用户 {self.user_id} 未配置MQTT broker，使用默认broker")
                from config import settings
                broker_url = settings.mqtt_broker_host
                self.broker_port = settings.mqtt_broker_port
                logger.info(f"[MQTT连接信息] 使用默认Broker: {broker_url}:{self.broker_port}")
            
            # 解析broker地址 - 直接使用配置的地址，不强制添加端口
            if broker_url.startswith("mqtt://"):
                broker_url = broker_url[7:]
            elif broker_url.startswith("tcp://"):
                broker_url = broker_url[6:]
            elif broker_url.startswith("ws://"):
                broker_url = broker_url[5:]
            elif broker_url.startswith("wss://"):
                broker_url = broker_url[6:]
            
            # 检查是否包含端口
            if ":" in broker_url:
                parts = broker_url.rsplit(":", 1)
                broker_host = parts[0]
                try:
                    self.broker_port = int(parts[1])
                except ValueError:
                    broker_host = broker_url
            else:
                broker_host = broker_url
                # 如果没有端口，使用默认1883
                if self.broker_port is None:
                    self.broker_port = 1883
            
            self.broker_host = broker_host
            
            # 打印解析后的连接信息
            logger.info(f"[MQTT连接信息] 解析后的Broker地址: {self.broker_host}:{self.broker_port}")
            
            # 创建MQTT客户端
            client_id = f"wifi-esl-user-{self.user_id}-{int(time.time())}"
            logger.info(f"[MQTT连接信息] Client ID: {client_id}")
            
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=client_id,
                transport="tcp",
                protocol=mqtt.MQTTv311,
            )

            # 设置回调
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            self.client.on_subscribe = self._on_subscribe

            # 设置用户名密码（使用配置的MQTT用户名密码，不是API Key）
            self.client.username_pw_set(mqtt_username, mqtt_password)
            logger.info(f"[MQTT连接信息] MQTT用户名密码已设置 (用户名: {mqtt_username})")

            # 启动连接线程
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._connection_loop, daemon=True)
            self.thread.start()

            # 等待连接建立
            for _ in range(30):
                if self.connected:
                    logger.info(f"用户 {self.user_id} MQTT连接成功")
                    return True
                await asyncio.sleep(0.1)
            
            logger.warning(f"用户 {self.user_id} MQTT连接超时，继续尝试...")
            return False
            
        except Exception as e:
            import traceback
            logger.error(f"[MQTT连接信息] 启动用户 {self.user_id} MQTT连接失败: {e}")
            logger.error(f"[MQTT连接信息] 异常堆栈: {traceback.format_exc()}")
            return False
    
    def _connection_loop(self):
        """后台连接线程"""
        try:
            logger.info(f"[MQTT连接信息] 用户 {self.user_id} 开始连接 {self.broker_host}:{self.broker_port}")
            result = self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            logger.info(f"[MQTT连接信息] connect() 返回结果: {result}")
            self.client.loop_start()
            logger.info(f"[MQTT连接信息] 用户 {self.user_id} MQTT loop已启动")

            while not self.stop_event.is_set():
                time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"用户 {self.user_id} MQTT连接异常: {e}")
    
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """连接成功回调"""
        logger.info(f"[MQTT连接信息] 用户 {self.user_id} _on_connect 被调用, reason_code: {reason_code}")
        if reason_code == 0:
            self.connected = True
            logger.info(f"[MQTT连接信息] 用户 {self.user_id} MQTT连接成功")
            
            # 通知前端MQTT已连接（延迟一点确保WebSocket已准备好）
            if self._main_loop and not self._main_loop.is_closed():
                def notify_mqtt_connected():
                    import time
                    time.sleep(0.5)  # 延迟500ms确保WebSocket组已建立
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.broadcast_to_user(self.user_id, {
                            "type": "mqtt_status",
                            "data": {"connected": True},
                            "timestamp": time.time()
                        }),
                        self._main_loop
                    )
                threading.Thread(target=notify_mqtt_connected, daemon=True).start()
            
            # 订阅用户特定主题
            topics = [
                f"/client/{self.api_key}/action/online",
                f"/client/{self.api_key}/action/offline",
                f"/client/{self.api_key}/action/usb_state",
                f"/client/{self.api_key}/action/button",
                f"/client/{self.api_key}/action/battery_reply",
                f"/client/{self.api_key}/action/led_reply",
                f"/client/{self.api_key}/action/reboot_reply",
                f"/client/{self.api_key}/action/display_reply",
            ]
            
            for topic in topics:
                result = client.subscribe(topic, qos=1)
                self.subscribed_topics.add(topic)
                # 提取动作类型用于打印
                action_type = topic.split('/')[-1] if '/' in topic else topic
                logger.info(f"[MQTT订阅] 用户 {self.user_id} 订阅成功: {action_type} -> {topic}, mid={result[1] if isinstance(result, tuple) else result}")
            
            logger.info(f"[MQTT订阅] 用户 {self.user_id} 共订阅了 {len(topics)} 个主题: online, offline, usb_state, button, battery_reply, led_reply, reboot_reply, display_reply")
                
        else:
            logger.error(f"[MQTT连接信息] 用户 {self.user_id} MQTT连接失败，错误码: {reason_code}")
    
    def _on_message(self, client, userdata, msg):
        """消息到达回调"""
        topic: str = msg.topic
        payload: bytes = msg.payload
        
        # 解析主题，提取操作类型
        prefix = f"/client/{self.api_key}/action/"
        if not topic.startswith(prefix):
            return
        
        action_type = topic[len(prefix):]
        
        # 解析消息内容
        try:
            decoded = base64.b64decode(payload).decode("utf-8")
            data = json.loads(decoded) if decoded else {}
        except Exception:
            try:
                data = json.loads(payload.decode("utf-8"))
            except Exception:
                data = {"raw_payload": payload.hex()}
        
        # 构建WebSocket消息
        ws_msg = {
            "type": action_type,
            "data": data,
            "user_id": self.user_id,
            "timestamp": time.time(),
        }
        
        # 打印完整消息内容
        data_str = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
        logger.info(f"[MQTT消息] 用户 {self.user_id} 收到 [{action_type}]: {data_str[:500]}")

        # 通过主事件循环广播给WebSocket
        if self._main_loop and not self._main_loop.is_closed():
            # 1) WebSocket广播
            try:
                future = asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast_to_user(self.user_id, ws_msg),
                    self._main_loop
                )
                def on_broadcast_done(f):
                    try:
                        f.result()
                        logger.info(f"[MQTT消息] 用户 {self.user_id} [{action_type}] WebSocket广播成功")
                    except Exception as e:
                        logger.error(f"[MQTT消息] 用户 {self.user_id} [{action_type}] WebSocket广播失败: {e}")
                future.add_done_callback(on_broadcast_done)
            except Exception as e:
                logger.error(f"[MQTT消息] 用户 {self.user_id} [{action_type}] 启动广播失败: {e}")

            # 2) 数据库持久化
            mac = data.get("mac") if isinstance(data, dict) else None
            logger.info(f"[MQTT消息] 准备持久化: mac={mac}, action_type={action_type}")
            if mac:
                future = asyncio.run_coroutine_threadsafe(
                    self._persist_to_db(mac, action_type, data),
                    self._main_loop
                )
                def on_persist_done(f):
                    try:
                        f.result()
                        logger.info(f"[MQTT消息] 持久化完成: mac={mac}, action_type={action_type}")
                    except Exception as e:
                        logger.error(f"[MQTT消息] 持久化失败: mac={mac}, action_type={action_type}, error={e}")
                future.add_done_callback(on_persist_done)
            else:
                logger.warning(f"[MQTT消息] 无法持久化: 消息中没有mac字段, data={data}")
        else:
            logger.warning(f"用户 {self.user_id} 无法广播MQTT消息：主事件循环不可用")
    
    async def _persist_to_db(self, mac: str, event_type: str, data: dict):
        """异步持久化到数据库"""
        import datetime as dt
        from services.db_service import update_device_status_by_mac
        
        now_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        update_fields: dict = {}
        
        if event_type == "online":
            update_fields = {"is_online": 1, "last_seen_at": now_iso}
        elif event_type == "offline":
            update_fields = {"is_online": 0}
        elif event_type == "battery_reply":
            voltage = data.get("voltage") or data.get("voltage_mv")
            if voltage is not None:
                voltage_int = int(voltage)
                update_fields = {"voltage": voltage_int, "last_seen_at": now_iso}
                
                # 低电量告警检查（阈值：350 = 3.5V）
                LOW_BATTERY_THRESHOLD = 350
                if voltage_int < LOW_BATTERY_THRESHOLD:
                    # 查询设备别名
                    device_name = mac  # 默认使用MAC地址
                    try:
                        from services.db_service import get_device_by_mac
                        device = await get_device_by_mac(mac)
                        if device and device.get("name"):
                            device_name = device["name"]
                    except Exception as e:
                        logger.warning(f"[MQTT] 获取设备 {mac} 别名失败: {e}")
                    
                    # 计算电量百分比（与前端保持一致）
                    # 前端规则: <335 (3.35V) = 0%, >390 (3.90V) = 100%, 中间线性插值
                    # voltage_int 单位是 0.01V，如 334 表示 3.34V
                    if voltage_int >= 390:
                        battery_percent = 100.0
                    elif voltage_int <= 335:
                        battery_percent = 0.0
                    else:
                        battery_percent = ((voltage_int - 335) / (390 - 335)) * 100
                    
                    voltage_v = voltage_int / 100.0  # 转换为伏特
                    
                    # 发送低电量告警WebSocket消息
                    alert_msg = {
                        "type": "low_battery_alert",
                        "data": {
                            "mac": mac,
                            "name": device_name,
                            "voltage": voltage_int,
                            "voltage_v": round(voltage_v, 2),
                            "battery_percent": round(battery_percent, 1),
                            "threshold": LOW_BATTERY_THRESHOLD,
                            "message": f"设备 {device_name} 电量过低 ({voltage_v:.2f}V, 剩余{battery_percent:.1f}%)，请及时更换电池"
                        },
                        "user_id": self.user_id,
                        "timestamp": time.time(),
                    }
                    
                    if self._main_loop and not self._main_loop.is_closed():
                        asyncio.run_coroutine_threadsafe(
                            ws_manager.broadcast_to_user(self.user_id, alert_msg),
                            self._main_loop
                        )
                        logger.warning(f"[MQTT] 低电量告警: {mac} ({device_name}) - {voltage_v:.2f}V ({battery_percent:.1f}%)")
        elif event_type == "usb_state":
            usb_state = data.get("state")
            if usb_state is not None:
                update_fields = {"usb_state": int(usb_state)}
        elif event_type in ("led_reply", "reboot_reply", "display_reply"):
            update_fields = {"last_seen_at": now_iso}
        
        # 更新设备状态
        if update_fields:
            await upsert_device(
                mac=mac,
                user_id=self.user_id,
                **update_fields
            )
        
        # 添加事件记录
        await add_device_event(
            mac=mac,
            event_type=event_type,
            payload=data
        )
        
        # display_reply: 联动更新任务设备状态（result=200 → success, 否则 failed）
        if event_type == "display_reply" and mac:
            result = data.get("result") if isinstance(data, dict) else None
            if result == 200:
                new_status = "success"
                err_msg = ""
            else:
                new_status = "failed"
                err_msg = f"display_reply result={result}"
            try:
                updated_rows = await update_device_status_by_mac(mac, new_status, err_msg)
                logger.info(f"[MQTT] display_reply: {mac} -> {new_status}, 更新行数: {updated_rows}")
                if updated_rows == 0:
                    logger.warning(f"[MQTT] display_reply: {mac} 没有更新任何行，检查task_devices表中是否存在该设备且状态为sent")
            except Exception as e:
                logger.error(f"[DB] 更新任务设备状态失败 {mac}: {e}")
        
        logger.debug(f"用户 {self.user_id} 设备 {mac} 事件 {event_type} 已持久化")
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        """断开连接回调"""
        self.connected = False
        logger.info(f"用户 {self.user_id} MQTT断开连接，原因码: {reason_code}")
        
        # 通知前端MQTT已断开
        if self._main_loop and not self._main_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_to_user(self.user_id, {
                    "type": "mqtt_status",
                    "data": {"connected": False},
                    "timestamp": time.time()
                }),
                self._main_loop
            )
    
    def _on_subscribe(self, client, userdata, mid, reason_codes, properties=None):
        """订阅成功回调"""
        logger.info(f"[MQTT订阅确认] 用户 {self.user_id} 订阅请求 mid={mid} 已确认, reason_codes={reason_codes}")
    
    async def stop(self):
        """停止用户的MQTT连接"""
        self.stop_event.set()
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
        
        # 等待线程结束
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info(f"用户 {self.user_id} MQTT连接已停止")


class MultiUserMQTTManager:
    """多用户MQTT管理器"""
    
    _instance = None
    _lock = None  # 将在__new__中初始化为asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: Dict[int, UserMQTTConnection] = {}
            cls._instance._main_loop: Optional[asyncio.AbstractEventLoop] = None
            cls._instance._lock = asyncio.Lock()  # 使用asyncio.Lock支持异步上下文
        return cls._instance
    
    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """设置主事件循环"""
        self._main_loop = loop
        # 为所有现有连接设置主循环
        for conn in self._connections.values():
            conn.set_main_loop(loop)
    
    async def start_user_connection(self, user_id: int) -> bool:
        """启动用户的MQTT连接"""
        async with self._lock:
            # 检查是否已有连接
            if user_id in self._connections:
                conn = self._connections[user_id]
                if conn.connected:
                    logger.info(f"用户 {user_id} MQTT连接已存在且已连接")
                    return True
                # 连接存在但未连接，尝试重启
                logger.info(f"用户 {user_id} MQTT连接已存在但未连接，重新启动...")
                await conn.stop()
                del self._connections[user_id]
            
            # 创建新连接
            conn = UserMQTTConnection(user_id)
            if self._main_loop:
                conn.set_main_loop(self._main_loop)
            
            # 启动连接（放入连接池，让后台线程去连接）
            self._connections[user_id] = conn
            success = await conn.start()
            
            # 返回实际的连接状态（如果已连接）或True（如果后台正在连接）
            actual_status = conn.connected
            if actual_status:
                logger.info(f"用户 {user_id} MQTT连接已成功建立")
                return True
            else:
                # 即使还没连上，也返回True表示正在连接中
                logger.info(f"用户 {user_id} MQTT连接正在后台建立中...")
                return True
    
    async def stop_user_connection(self, user_id: int):
        """停止用户的MQTT连接"""
        async with self._lock:
            if user_id in self._connections:
                conn = self._connections[user_id]
                await conn.stop()
                del self._connections[user_id]
                logger.info(f"用户 {user_id} MQTT连接已停止")
    
    async def get_user_connection(self, user_id: int) -> Optional[UserMQTTConnection]:
        """获取用户的MQTT连接"""
        return self._connections.get(user_id)
    
    async def is_user_connected(self, user_id: int) -> bool:
        """检查用户MQTT是否已连接"""
        if user_id in self._connections:
            return self._connections[user_id].connected
        return False
    
    async def stop_all(self):
        """停止所有用户的MQTT连接"""
        async with self._lock:
            tasks = []
            for user_id in list(self._connections.keys()):
                tasks.append(self.stop_user_connection(user_id))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("所有用户MQTT连接已停止")
    
    def get_all_connections(self) -> Dict[int, UserMQTTConnection]:
        """获取所有连接"""
        return self._connections.copy()


# 全局管理器实例
multi_user_mqtt_manager = MultiUserMQTTManager()