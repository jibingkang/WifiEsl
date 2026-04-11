"""
WebSocket连接管理器
维护所有前端WebSocket连接池，支持广播消息、心跳检测
"""
import time
import json
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接池管理"""

    def __init__(self):
        # 活跃连接: {connection_id: websocket}
        self._connections: Dict[str, any] = {}
        # 按类型分组: Set[connection_id]
        self._groups: Dict[str, Set[str]] = defaultdict(set)
        self._counter = 0
        self._lock = asyncio.Lock()

    async def connect(self, websocket) -> str:
        """注册新的WS连接，返回连接ID"""
        async with self._lock:
            cid = f"ws-{self._counter}"
            self._counter += 1
            self._connections[cid] = websocket
            self._groups["all"].add(cid)
            logger.info(f"[WS] 新连接: {cid}, 总数: {len(self._connections)}")
            return cid

    async def disconnect(self, connection_id: str):
        """移除WS连接"""
        async with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]
                for g in list(self._groups.values()):
                    g.discard(connection_id)
                logger.info(f"[WS] 断开: {connection_id}, 总数: {len(self._connections)}")

    async def send_to(self, connection_id: str, message: dict):
        """向指定连接发消息"""
        ws = self._connections.get(connection_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"[WS] 发送失败({connection_id}): {e}")
                await self.disconnect(connection_id)

    async def broadcast(self, message: dict, group: str = "all"):
        """向指定组或所有连接广播消息"""
        cids = self._groups.get(group, set()).copy()
        disconnected = []

        for cid in cids:
            ws = self._connections.get(cid)
            if ws:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.debug(f"[WS] 广播失败({cid}): {e}")
                    disconnected.append(cid)

        # 清理失效连接
        for cid in disconnected:
            await self.disconnect(cid)

    def count(self) -> int:
        """当前活跃连接数"""
        return len(self._connections)

    async def close(self):
        """关闭所有连接，清理资源"""
        async with self._lock:
            for cid, ws in list(self._connections.items()):
                try:
                    await ws.close()
                except Exception:
                    pass
            self._connections.clear()
            self._groups.clear()
            logger.info("[WS] 所有连接已清理")


# 全局单例
ws_manager = WebSocketManager()


async def ws_endpoint(websocket):
    """
    WebSocket端点处理函数
    路径: /ws/device-status
    """
    from services.mqtt_service import mqtt_manager

    cid = await ws_manager.connect(websocket)
    logger.info(f"[WS] 前端连接建立: {cid}")

    # 发送欢迎消息+MQTT状态
    await websocket.send_json({
        "type": "connected",
        "data": {
            "connection_id": cid,
            "mqtt_connected": mqtt_manager.connected,
        },
        "timestamp": time.time(),
    })

    try:
        # 保持连接，持续接收前端消息
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                # 处理前端发来的消息（如心跳ping）
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time(),
                    })
                elif data.get("type") == "subscribe_mqtt":
                    # 可扩展: 指定订阅特定设备的MQTT topic
                    mac = data.get("data", {}).get("mac")
                    if mac:
                        await websocket.send_json({
                            "type": "subscribed",
                            "data": {"mac": mac},
                            "timestamp": time.time(),
                        })
            except json.JSONDecodeError:
                pass  # 忽略非JSON消息

    except Exception as e:
        logger.debug(f"[WS] 连接关闭/异常 ({cid}): {e}")
    finally:
        await ws_manager.disconnect(cid)
