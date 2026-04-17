"""
MQTT桥接服务 - 连接Broker订阅设备状态Topic并转发给WebSocket管理器
使用 paho-mqtt 客户端库 (同步线程模式 + 异步事件循环桥接)
"""
import threading
import time
import json
import base64
import logging
import asyncio

import paho.mqtt.client as mqtt

from config import settings
from services.ws_manager import ws_manager
from services.db_service import upsert_device, add_device_event, update_device_status_by_mac

logger = logging.getLogger(__name__)

# 全局主事件循环引用 (由main.py在lifespan中通过set_main_loop()绑定)
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop):
    """保存主事件循环引用，供MQTT回调线程安全调度协程"""
    global _main_loop
    _main_loop = loop
    print(f"[MQTT] 已绑定主事件循环 (id={id(loop)})")


class MQTTManager:
    """MQTT Broker连接和消息处理管理器"""

    def __init__(self):
        self.client: mqtt.Client | None = None
        self.connected = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    async def start(self):
        """启动MQTT连接 (在后台线程中运行)"""
        self._stop_event.clear()

        client_id = f"wifi-esl-manager-{int(time.time())}"
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            transport="tcp",
            protocol=mqtt.MQTTv311,
        )

        if settings.mqtt_tls_enable:
            self.client.tls_set()
            if settings.mqtt_tls_insecure:
                self.client.tls_insecure_set(True)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        mqtt_user = settings.mqtt_username or settings.wifi_apikey
        mqtt_pass = settings.mqtt_password or ""
        self.client.username_pw_set(mqtt_user, mqtt_pass)

        print(f"[MQTT] 配置: host={settings.mqtt_broker_host}, port={settings.mqtt_broker_port}, "
              f"TLS={settings.mqtt_tls_enable}, user={mqtt_user}, protocol=3.1.1")

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        for _ in range(50):
            if self.connected:
                print("[MQTT] Broker 连接成功!")
                return True
            time.sleep(0.1)

        print("[WARNING] MQTT 连接超时，后台继续尝试...")
        return False

    async def stop(self):
        """停止MQTT连接"""
        self._stop_event.set()
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
        print("[MQTT] 已断开")

    def _loop(self):
        """后台线程: 连接Broker并保持消息循环"""
        try:
            host = settings.mqtt_broker_host
            port = settings.mqtt_broker_port
            print(f"[MQTT] 尝试连接 tcp://{host}:{port} ...")
            self.client.connect(host, port, keepalive=60)
            self.client.loop_start()
            print(f"[MQTT] TCP连接已发起，等待CONNACK确认...")

            while not self._stop_event.is_set():
                time.sleep(0.5)

        except Exception as e:
            print(f"[MQTT] 连接异常: {type(e).__name__}: {e}")
            logger.error(f"MQTT 连接错误: {e}")

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """MQTT连接成功回调 - 订阅所有需要的Topic"""
        print(f"[MQTT] _on_connect 回调触发, reason_code={reason_code}")
        if reason_code == 0:
            self.connected = True
            api_key = settings.wifi_apikey

            topics = [
                f"/client/{api_key}/action/online",
                f"/client/{api_key}/action/offline",
                f"/client/{api_key}/action/usb_state",
                f"/client/{api_key}/action/button",
                f"/client/{api_key}/action/battery_reply",
                f"/client/{api_key}/action/led_reply",
                f"/client/{api_key}/action/reboot_reply",
                f"/client/{api_key}/action/display_reply",
            ]

            for topic in topics:
                client.subscribe(topic, qos=1)
                print(f"[MQTT] 已订阅: {topic}")
        else:
            print(f"[MQTT] 认证失败或被拒绝, code={reason_code}")

    def _on_message(self, client, userdata, msg):
        """
        MQTT消息到达回调 - 解析后:
          1) 通过WS广播给前端 (实时)
          2) 持久化到数据库 (设备状态 + 事件记录)
        此方法在paho-mqtt后台线程中被调用，所有async操作通过主事件循环调度
        """
        topic: str = msg.topic
        payload: bytes = msg.payload
        api_key = settings.wifi_apikey

        prefix = f"/client/{api_key}/action/"
        if not topic.startswith(prefix):
            return

        action_type = topic[len(prefix):]

        try:
            decoded = base64.b64decode(payload).decode("utf-8")
            data = json.loads(decoded) if decoded else {}
        except Exception:
            try:
                data = json.loads(payload.decode("utf-8"))
            except Exception:
                data = {"raw_payload": payload.hex()}

        ws_msg = {
            "type": action_type,
            "data": data,
            "timestamp": time.time(),
        }

        print(f"[MQTT] 收到 [{action_type}] data={data} -> 广播给 WS + 写入DB")

        global _main_loop
        if _main_loop and not _main_loop.is_closed():
            # 1) WS实时广播
            future = asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(ws_msg), _main_loop
            )
            future.add_done_callback(lambda f: f.exception() if f else None)

            # 2) 数据库持久化
            mac = data.get("mac") if isinstance(data, dict) else None
            if mac:
                asyncio.run_coroutine_threadsafe(
                    self._persist_to_db(mac, action_type, data), _main_loop
                )
        else:
            logger.warning(f"[MQTT] 无法广播 [{action_type}]: 主事件循环不可用")

    async def _persist_to_db(self, mac: str, event_type: str, data: dict):
        """
        异步持久化: 更新devices表最新状态 + 插入event事件记录
        在主事件循环中执行，安全访问aiosqlite
        """
        import datetime as dt

        now_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        update_fields: dict = {}

        if event_type == "online":
            update_fields = {"is_online": 1, "last_seen_at": now_iso}
        elif event_type == "offline":
            update_fields = {"is_online": 0}
        elif event_type == "battery_reply":
            voltage = data.get("voltage") or data.get("voltage_mv")
            if voltage is not None:
                update_fields = {"voltage": int(voltage), "last_seen_at": now_iso}
        elif event_type in ("led_reply", "reboot_reply", "display_reply"):
            update_fields = {"last_seen_at": now_iso}

        try:
            await upsert_device(mac, **update_fields)
        except Exception as e:
            logger.error(f"[DB] upsert device {mac} 失败: {e}")

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
                await update_device_status_by_mac(mac, new_status, err_msg)
                print(f"[MQTT] display_reply: {mac} -> {new_status}")
            except Exception as e:
                logger.error(f"[DB] 更新任务设备状态失败 {mac}: {e}")

        try:
            await add_device_event(mac, event_type, data)
        except Exception as e:
            logger.error(f"[DB] add event [{event_type}] for {mac} 失败: {e}")

    def _on_disconnect(self, client, userdata, reason_code, properties=None, packet_from_broker=None):
        """MQTT断连回调 (paho-mqtt v2: 5个参数 + self)"""
        self.connected = False
        if reason_code != 0:
            logger.warning(f"[MQTT] 意外断开, code={reason_code}")
        else:
            print("[MQTT] 正常断开")


# 全局单例
mqtt_manager = MQTTManager()
